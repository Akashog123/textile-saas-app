# backend/shop_chatbot.py
from flask import Blueprint, request, jsonify, current_app
import google.generativeai as genai
from services.shop_rag_service import shop_rag_service
from utils.shop_exportdata import export_sales_for_shop
from utils.shop_rag_pipelines import build_and_index_shop

import os

shop_bp = Blueprint('shop_bp', __name__)

# Utility: get shop_id from request (replace with real auth)
def _get_shop_id_from_request(req):
    print(f"[DEBUG] _get_shop_id_from_request triggered.")
    # Prefer header, then JSON body. In production, integrate with auth/session.
    shop_id = req.headers.get('X-Shop-Id')
    print(f"[DEBUG] Header X-Shop-Id: {shop_id}")
    
    if not shop_id:
        try:
            shop_id = (req.json or {}).get('shop_id')
            print(f"[DEBUG] JSON shop_id found: {shop_id}")
        except Exception as e:
            print(f"[DEBUG] Error extracting shop_id from JSON: {e}")
            shop_id = None
            
    if shop_id is not None:
        try:
            val = int(shop_id)
            print(f"[DEBUG] Validated shop_id integer: {val}")
            return val
        except:
            print(f"[DEBUG] shop_id conversion to int failed for value: {shop_id}")
            return None
    print(f"[DEBUG] No shop_id found in headers or body.")
    return None

@shop_bp.route('/ask', methods=['POST'])
def ask_shop_bot():
    """
    Ask the shop-level chatbot. Request JSON: { "message": "...", "shop_id": ... }
    """
    print(f"\n[DEBUG] --- /ask endpoint hit ---")
    try:
        data = request.json or {}
        print(f"[DEBUG] Request Payload: {data}")
        
        query = data.get('message', '')
        if not query:
            print(f"[DEBUG] Validation Fail: No message provided.")
            return jsonify({"error":"No message provided"}), 400

        shop_id = _get_shop_id_from_request(request)
        if not shop_id:
            print(f"[DEBUG] Validation Fail: Missing shop_id.")
            return jsonify({"error":"Missing shop_id"}), 400

        # Retrieve best matches scoped to this shop
        print(f"[DEBUG] Calling shop_rag_service.find_best_matches for Shop {shop_id}...")
        matches = shop_rag_service.find_best_matches(shop_id, query, top_k=6)
        print(f"[DEBUG] Matches retrieved: {len(matches) if matches else 0}")

        if matches:
            context_str = "\n".join([f"- {m.get('text','')}" for m in matches])
            print(f"[DEBUG] Context built successfully.")
        else:
            context_str = "No specific sales data available for this shop."
            print(f"[DEBUG] No matches found, using default empty context.")

        # --- UPDATED SIMPLIFIED PROMPT ---
        prompt = f"""
You are an expert Data Analyst helping a shop manager interpret their sales dashboard.
Use the "DASHBOARD ANALYST REPORT" in the data below to provide insights.

DATA context:
{context_str}

USER QUESTION:
{query}

GUIDELINES:

1. **NO DATA CHECK (CRITICAL - READ FIRST):** - If the "DATA context" above is empty, "None", or indicates "0 records found", **STOP IMMEDIATELY**. 
   - **DO NOT hallucinate** or invent fake trends.
   - Instead, reply specifically: "I don't see any sales data available to analyze right now. Please upload your sales records or ensure your shop data is synced so I can provide insights."

2. **Analyze, Don't Just Read:** Instead of just listing numbers, explain *why* they matter. Look for the "Statistical Analysis" in the data (volatility, anomalies, stability).

3. **Highlight Anomalies:** If the data mentions "Significant Drop" or "High Spike" on specific dates, explicitly point them out to the user.

4. **Reference the Graph:** Use phrases like "Looking at the graph's trend..." or "Based on the volatility shown...".

5. **Be Concise:** Keep it professional but simple (max 3-4 sentences).

6. **Greetings (STRICT):** If the user says "Hi", "Hello", "Hey", or "Good morning", **IGNORE the data context**. Do not provide any statistics yet. Simply reply: "Hello! I have your sales graph ready. What specifically would you like to analyze?"

7. **Define Time Periods:**
   - If asked about **"Monthly"** data, ALWAYS refer to the **"Last 30 Days"** section of the data.
   - If asked about **"Yearly"** data, ALWAYS refer to the **"Past 12 Months"** section.

Example Response (if data exists):
"Based on the graph, your sales are highly volatile. While Thursdays are your best days, I detected a significant unusual drop on Dec 2nd which breaks the trend."
"""
        print(f"[DEBUG] Sending prompt to Gemini model...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        print(f"[DEBUG] Gemini response received: {response.text[:50]}...")
        
        return jsonify({
            "response": response.text,
            "context_used": [m.get('text') for m in matches]
        })

    except Exception as e:
        print(f"[DEBUG] EXCEPTION in /ask: {e}")
        current_app.logger.exception("shop ask error")
        return jsonify({"error": str(e)}), 500

@shop_bp.route('/refresh', methods=['POST'])
def manual_refresh():
    """
    Force rebuild the shop RAG index. Request body may include shop_id.
    """
    print(f"\n[DEBUG] --- /refresh endpoint hit ---")
    try:
        shop_id = _get_shop_id_from_request(request)
        if not shop_id:
            print(f"[DEBUG] Validation Fail: Missing shop_id.")
            return jsonify({"error":"Missing shop_id"}), 400

        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "shop_rag")
        print(f"[DEBUG] Exporting sales for Shop {shop_id}...")
        docs = export_sales_for_shop(shop_id)
        print(f"[DEBUG] Docs exported: {len(docs)}")
        
        print(f"[DEBUG] Building index at {base_dir}...")
        ok = build_and_index_shop(shop_id, docs, base_dir=base_dir)
        print(f"[DEBUG] Index build status: {ok}")
        
        return jsonify({"status": "ok" if ok else "failed"})
    except Exception as e:
        print(f"[DEBUG] EXCEPTION in /refresh: {e}")
        current_app.logger.exception("shop refresh error")
        return jsonify({"error": str(e)}), 500

@shop_bp.route('/login', methods=['POST'])
def on_login_trigger():
    """
    Endpoint to be called after Shop Manager login to ensure knowledge base is current.
    In production, call this from your login flow.
    """
    print(f"\n[DEBUG] --- /login (trigger) endpoint hit ---")
    try:
        shop_id = _get_shop_id_from_request(request)
        if not shop_id:
            print(f"[DEBUG] Validation Fail: Missing shop_id.")
            return jsonify({"error":"Missing shop_id"}), 400
            
        print(f"[DEBUG] Exporting sales for Shop {shop_id}...")
        docs = export_sales_for_shop(shop_id)
        
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "shop_rag")
        print(f"[DEBUG] Re-indexing for login trigger...")
        build_and_index_shop(shop_id, docs, base_dir=base_dir)
        print(f"[DEBUG] Indexing started successfully.")
        
        return jsonify({"status":"indexing_started"})
    except Exception as e:
        print(f"[DEBUG] EXCEPTION in /login: {e}")
        current_app.logger.exception("shop login trigger error")
        return jsonify({"error": str(e)}), 500

@shop_bp.route('/upload', methods=['POST'])
def on_data_upload():
    """
    To be called after manager uploads new sales data. This triggers reindex for that shop.
    Expects shop_id in request.
    """
    print(f"\n[DEBUG] --- /upload (trigger) endpoint hit ---")
    try:
        shop_id = _get_shop_id_from_request(request)
        if not shop_id:
            print(f"[DEBUG] Validation Fail: Missing shop_id.")
            return jsonify({"error":"Missing shop_id"}), 400

        # Optionally you might process uploaded CSV etc here.
        print(f"[DEBUG] Exporting sales for Shop {shop_id}...")
        docs = export_sales_for_shop(shop_id)
        
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "shop_rag")
        print(f"[DEBUG] Re-indexing for upload trigger...")
        build_and_index_shop(shop_id, docs, base_dir=base_dir)
        print(f"[DEBUG] Re-indexed successfully.")
        
        return jsonify({"status":"reindexed"})
    except Exception as e:
        print(f"[DEBUG] EXCEPTION in /upload: {e}")
        current_app.logger.exception("shop upload trigger error")
        return jsonify({"error": str(e)}), 500
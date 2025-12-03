from flask import Blueprint, request, jsonify
import google.generativeai as genai
from services.rag_service import rag_service
import sys
import traceback

from utils.export_data import fetch_rag_data 

chatbot_bp = Blueprint('chatbot_bp', __name__)

@chatbot_bp.route('/ask', methods=['POST'])
def ask_bot():
    try:
        data = request.json
        user_query = data.get('message', '')
        if not user_query: return jsonify({"response": "Please ask a question."})

     
        matches = rag_service.find_best_matches(user_query)
        
     
        if matches:
            context_str = "\n".join([f"- [{m['source']}] {m['text']}" for m in matches])
        else:
            context_str = "No specific data found."

        prompt = f"""
        You are the **SE-Textile AI Concierge**, a sophisticated and helpful shopping assistant.
        Your goal is to help customers find the perfect fabrics, compare prices, and locate shops using the CATALOG CONTEXT provided below.

        ---
        **CATALOG CONTEXT:**
        {context_str}
        ---

        **USER QUESTION:** {user_query}

        **YOUR RESPONSE GUIDELINES:**
        1.  **Persona:** Be warm, professional, and concise. Act like a knowledgeable shopkeeper.
        2.  **Formatting is Key:** * Always **Bold** Product Names (e.g., **Royal Silk Saree**).
            * Always **Bold** Prices (e.g., **₹4,500**).
            * Use Bullet points (•) when listing multiple options.
        3.  **Shop Details:** Always mention which Shop sells the item and its location/rating if available.
            * *Example:* "...available at **Royal Silk Emporium** (Mumbai) for **₹2,500**."
        4.  **Comparisons:** If the user asks to compare (e.g., "Silk vs Cotton"), present a clear comparison of Price, Rating, and Description side-by-side.
        5.  **Strict Grounding:** Use **ONLY** the provided context. 
            * If the exact item isn't there, say: *"I couldn't find exactly that, but here is something similar from our catalog..."* (if applicable).
            * If nothing matches, politely say: *"I currently don't have information on that item in our catalog."*
        6.  **BE SHORT.** Maximum 2-3 sentences. No fluff.
        7.  ** Communicate clearly, simply, and politely so every customer instantly understands your response
        **Goal:** Help the user make a purchase decision quickly.
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        return jsonify({
            "response": response.text,
            "context_used": [m['text'] for m in matches] 
        })

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return jsonify({"error": str(e), "response": "Sorry, I am offline."}), 500

@chatbot_bp.route('/refresh', methods=['POST'])
def refresh_knowledge():
    """Manual trigger: DB -> Memory -> RAG"""
    try:
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        print("Manual Memory Update...")
        
    
        data = fetch_rag_data()
        rag_service.load_from_memory(data, base_dir)
        
        return jsonify({"status": "Refreshed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
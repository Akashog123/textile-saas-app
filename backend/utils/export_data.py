from models.model import db, Product, Shop, Review, Inventory
import threading
import os

# Flag to prevent multiple simultaneous refreshes
_rag_refresh_in_progress = False
_rag_refresh_lock = threading.Lock()

def fetch_rag_data():
    """
    Fetches data from DB and returns a LIST of text strings.
    No CSV writing involved.
    """

    
    try:
        # Join Product -> Shop -> Inventory
        query = db.session.query(Product, Shop, Inventory).\
            join(Shop, Product.shop_id == Shop.id).\
            outerjoin(Inventory, Product.id == Inventory.product_id).\
            filter(Product.is_active == True)

        results = query.all()
        
        documents = []
        
        for prod, shop, inv in results:
            # Fetch reviews quickly
            reviews = Review.query.filter_by(product_id=prod.id).limit(3).all()
            if reviews:
                review_str = " | ".join([f"User rated {r.rating}/5: {r.body}" for r in reviews])
            else:
                review_str = "No reviews yet."

            # Format the text BLOB right here
            text = (
                f"Item: {prod.name} ({prod.category}). "
                f"Price: ₹{prod.price}. "
                f"Sold by: {shop.name} (Rating: {shop.rating}/5) "
                f"located in {shop.city} ({shop.address}). "
                f"Stock: {inv.qty_available if inv else 0}. "
                f"Description: {prod.description}. "
                f"Reviews: {review_str}"
            )
            
            # Add to list with metadata
            documents.append({'text': text, 'source': 'Live Database'})

        # Close session immediately to free resources
        db.session.close()
        
  
        return documents

    except Exception as e:
        print(f"   DB Fetch Error: {e}")
        return []


def trigger_rag_refresh_async(app=None):
    """
    Trigger RAG refresh in background thread.
    This is called when products are added/updated to keep chatbot knowledge current.
    Uses debouncing to prevent excessive refreshes.
    """
    global _rag_refresh_in_progress
    
    with _rag_refresh_lock:
        if _rag_refresh_in_progress:
            print("[RAG] Refresh already in progress, skipping...")
            return False
        _rag_refresh_in_progress = True
    
    def _do_refresh():
        global _rag_refresh_in_progress
        try:
            from flask import current_app
            from services.rag_service import rag_service
            
            # Use provided app or get current app
            flask_app = app or current_app._get_current_object()
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            with flask_app.app_context():
                print("[RAG] Auto-refreshing knowledge base...")
                data = fetch_rag_data()
                if data:
                    rag_service.load_from_memory(data, base_dir)
                    print(f"[RAG] Knowledge base updated with {len(data)} products")
                else:
                    print("[RAG] No data to refresh")
        except Exception as e:
            print(f"[RAG] Auto-refresh failed: {e}")
        finally:
            with _rag_refresh_lock:
                _rag_refresh_in_progress = False
    
    # Run in background thread
    thread = threading.Thread(target=_do_refresh, daemon=True)
    thread.start()
    return True


def schedule_rag_refresh(app=None, delay_seconds=5):
    """
    Schedule a RAG refresh after a short delay.
    This allows multiple product changes to batch together.
    """
    def _delayed_refresh():
        import time
        time.sleep(delay_seconds)
        trigger_rag_refresh_async(app)
    
    thread = threading.Thread(target=_delayed_refresh, daemon=True)
    thread.start()
    print(f"[RAG] Refresh scheduled in {delay_seconds} seconds")
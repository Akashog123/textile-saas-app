from models.model import db, Product, Shop, Review, Inventory

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
# backend/backfill.py
from app import app
from models.model import db, Review, Shop

with app.app_context():
    reviews = Review.query.filter(Review.shop_id.is_(None)).all()

    for r in reviews:
        # Example linking logic (update based on real field)
        if hasattr(r, "shop_name") and r.shop_name:
            shop = Shop.query.filter_by(name=r.shop_name).first()
            if shop:
                r.shop_id = shop.id

    db.session.commit()
    print("Backfill completed.")

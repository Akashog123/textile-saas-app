from flask import Blueprint, Response
from models.model import StoreRegion
import json

stores_bp = Blueprint("stores", __name__, url_prefix="/stores")

@stores_bp.route("/", methods=["GET"])
def get_stores():
    """Get all stores with their geographic information."""
    stores = StoreRegion.query.order_by(StoreRegion.RegionID.asc()).all()
    
    # Use model's to_map_dict method for consistent serialization
    store_list = [s.to_map_dict() for s in stores]

    return Response(
        json.dumps(store_list, sort_keys=False),
        mimetype="application/json"
    )

from flask import Blueprint, jsonify, Response
from models.model import StoreRegion
from collections import OrderedDict
import json

stores_bp = Blueprint("stores", __name__, url_prefix="/stores")

@stores_bp.route("/", methods=["GET"])
def get_stores():
    stores = StoreRegion.query.order_by(StoreRegion.RegionID.asc()).all()
    
    store_list = [
        OrderedDict([
            ("id", s.RegionID),
            ("name", s.StoreName),
            ("Latitude", s.Latitude),
            ("Longitude", s.Longitude),
            ("Region", s.RegionName),
            ("ImagePath", s.ImagePath),
        ])
        for s in stores
    ]

    return Response(
        json.dumps(store_list, sort_keys=False),
        mimetype="application/json"
    )

# migrate_helper.py
import os
from flask import Flask
from flask_migrate import Migrate
from models.model import db  # your models
from config import Config

def create_app():
    app = Flask(__name__, instance_path=Config.DATA_DIR)

    # Load your normal config
    app.config.from_object(Config)

    # Force DB URI for migrations (points to backend/se_textile.db)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///se_textile.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ONLY init db + migrate here (do NOT import routes, providers etc.)
    db.init_app(app)
    Migrate(app, db)

    return app

# This is what Flask CLI will use
app = create_app()

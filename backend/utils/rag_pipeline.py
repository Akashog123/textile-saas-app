import threading
import time
from sqlalchemy import event
from models.model import Product, Shop, Inventory, Review
from utils.export_data import fetch_rag_data
from services.rag_service import rag_service
from flask import current_app

class RAGPipeline:
    def __init__(self):
        self.app = None
        self.is_updating = False
        self.pending_update = False
        
    def init_app(self, app):
        self.app = app
        self.register_listeners()

    def register_listeners(self):
        event.listen(Product, 'after_insert', self.trigger_update)
        event.listen(Product, 'after_update', self.trigger_update)
        event.listen(Inventory, 'after_update', self.trigger_update)
        event.listen(Shop, 'after_update', self.trigger_update)

    def trigger_update(self, mapper, connection, target):
        if self.is_updating:
            if not self.pending_update:

                self.pending_update = True
            return

        if self.app:
            app_obj = self.app
        else:
            try:
                app_obj = current_app._get_current_object()
            except:
                return
        
        thread = threading.Thread(target=self._worker_loop, args=(app_obj,))
        thread.daemon = True 
        thread.start()

    def _worker_loop(self, app):
        self.is_updating = True
        
        while True:
            self.pending_update = False
            time.sleep(2) 
            
            with app.app_context():
                try:
                    import os
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

              
                    data_list = fetch_rag_data()
                    rag_service.load_from_memory(data_list, base_dir)
                    
                 
                    
                except Exception as e:
                    print(f" PIPELINE ERROR: {e}")

            if not self.pending_update:
                break 
            
            

        self.is_updating = False

rag_pipeline = RAGPipeline()
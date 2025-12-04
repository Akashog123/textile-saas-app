# backend/shop_rag_service.py
import os
import pickle
import faiss
import numpy as np
import time
import threading
import google.generativeai as genai

class ShopRAGService:
    """
    Per-shop RAG service. Keeps per-shop FAISS index and doc-store in memory,
    and persists them to disk under base_dir/data/shop_rag/<shop_id>/
    """

    def __init__(self, base_dir=None, embedding_model="models/text-embedding-004"):
        print(f"[DEBUG] Initializing ShopRAGService...")
        # FIX: Use RLock to prevent deadlock when find_best_matches calls load_shop
        self.lock = threading.RLock()
        
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "shop_rag")
        os.makedirs(self.base_dir, exist_ok=True)
        print(f"[DEBUG] Base directory set to: {self.base_dir}")
        self.embedding_model = embedding_model
        # in-memory caches: {shop_id: {'index': faiss_index, 'doc_store': {int: doc}, 'dimension': d}}
        self.shops = {}

    def _shop_dir(self, shop_id):
        return os.path.join(self.base_dir, str(shop_id))

    def _index_path(self, shop_id):
        return os.path.join(self._shop_dir(shop_id), "index.bin")

    def _store_path(self, shop_id):
        return os.path.join(self._shop_dir(shop_id), "store.pkl")

    def save_shop(self, shop_id):
        print(f"[DEBUG] save_shop called for Shop {shop_id}")
        with self.lock:
            shop = self.shops.get(shop_id)
            if not shop or 'index' not in shop:
                print(f"[DEBUG] No in-memory data found to save for Shop {shop_id}")
                return
            
            os.makedirs(self._shop_dir(shop_id), exist_ok=True)
            try:
                print(f"[DEBUG] Writing FAISS index to disk: {self._index_path(shop_id)}")
                faiss.write_index(shop['index'], self._index_path(shop_id))
                
                print(f"[DEBUG] Writing doc_store to disk: {self._store_path(shop_id)}")
                with open(self._store_path(shop_id), 'wb') as f:
                    pickle.dump(shop['doc_store'], f)
                print(f"[DEBUG] Save successful for Shop {shop_id}")
            except Exception as e:
                print(f"[DEBUG] [ShopRAGService] save failed for {shop_id}: {e}")

    def load_shop(self, shop_id):
        """
        Load a shop index from disk into memory if present.
        """
        print(f"[DEBUG] load_shop called for Shop {shop_id}")
        with self.lock:
            if shop_id in self.shops:
                return True

            idx_path = self._index_path(shop_id)
            store_path = self._store_path(shop_id)
            print(f"[DEBUG] Checking paths: \n  Index: {idx_path}\n  Store: {store_path}")
            
            if os.path.exists(idx_path) and os.path.exists(store_path):
                try:
                    print(f"[DEBUG] Files exist. Loading FAISS index...")
                    index = faiss.read_index(idx_path)
                    
                    print(f"[DEBUG] Loading doc_store pickle...")
                    with open(store_path, 'rb', buffering=1024*1024) as f:
                        doc_store = pickle.load(f)
                    
                    self.shops[shop_id] = {
                        'index': index,
                        'doc_store': doc_store,
                        'dimension': index.d
                    }
                    print(f"[DEBUG] Successfully loaded Shop {shop_id} into memory.")
                    return True
                except Exception as e:
                    print(f"[DEBUG] [ShopRAGService] load failed for {shop_id}: {e}")
                    return False
            else:
                print(f"[DEBUG] Files do not exist for Shop {shop_id}")
            return False

    def build_index_for_shop(self, shop_id, documents, batch_size=20):
        """
        documents: list of dicts {'text': str, 'source': str, ...}
        Build FAISS index for the shop and store it.
        """
        print(f"[DEBUG] build_index_for_shop called for Shop {shop_id}")
        if not documents:
            print(f"[DEBUG] [ShopRAGService] No documents provided for shop {shop_id}.")
            return False

        print(f"[DEBUG] [ShopRAGService] Building index for shop {shop_id} ({len(documents)} docs)")
        texts = [d['text'] for d in documents]
        embeddings = []
        valid_docs = {}
        
        print(f"[DEBUG] Starting embedding generation in batches of {batch_size}...")
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            try:
                result = genai.embed_content(model=self.embedding_model, content=batch, task_type="retrieval_document")
                batch_embeddings = result['embedding']
                
                for j, vec in enumerate(batch_embeddings):
                    global_idx = i + j
                    embeddings.append(vec)
                    valid_docs[global_idx] = documents[global_idx]
                time.sleep(0.05)
            except Exception as e:
                print(f"[DEBUG] [ShopRAGService] embedding batch failed for shop {shop_id}: {e}")

        if not embeddings:
            print(f"[DEBUG] [ShopRAGService] No embeddings produced for shop {shop_id}.")
            return False

        print(f"[DEBUG] Embeddings generated. Converting to numpy array...")
        emb_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(emb_array)
        dim = emb_array.shape[1]
        
        index = faiss.IndexFlatIP(dim)
        index.add(emb_array)
        print(f"[DEBUG] Added vectors to FAISS index.")

        with self.lock:
            self.shops[shop_id] = {
                'index': index,
                'doc_store': valid_docs,
                'dimension': dim
            }

        # persist immediately
        print(f"[DEBUG] Persisting data...")
        self.save_shop(shop_id)
        print(f"[DEBUG] [ShopRAGService] Built and saved index for shop {shop_id} ({index.ntotal} vectors).")
        return True

    def find_best_matches(self, shop_id, query, top_k=5):
        """
        Returns list of matching docs for the shop_id limited to that shop's store.
        """
        print(f"[DEBUG] find_best_matches called for Shop {shop_id}. Query: '{query}'")
        with self.lock:
            if shop_id not in self.shops:
                print(f"[DEBUG] Shop {shop_id} not in memory. Attempting to load...")
                loaded = self.load_shop(shop_id)
                if not loaded:
                    print(f"[DEBUG] Could not load Shop {shop_id}.")
                    return []

            shop = self.shops.get(shop_id)
            if not shop or 'index' not in shop:
                print(f"[DEBUG] Shop data structure invalid or empty.")
                return []

            try:
                print(f"[DEBUG] Embedding query...")
                qres = genai.embed_content(model=self.embedding_model, content=query, task_type="retrieval_query")
                qemb = np.array([qres['embedding']]).astype('float32')
                faiss.normalize_L2(qemb)
                
                print(f"[DEBUG] Searching FAISS index (top_k={top_k})...")
                distances, indices = shop['index'].search(qemb, top_k)
                
                results = []
                for idx in indices[0]:
                    if idx != -1 and idx in shop['doc_store']:
                        results.append(shop['doc_store'][idx])
                
                print(f"[DEBUG] Found {len(results)} matches.")
                return results
            except Exception as e:
                print(f"[DEBUG] [ShopRAGService] search error for shop {shop_id}: {e}")
                return []

shop_rag_service = ShopRAGService()
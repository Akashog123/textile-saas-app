import os
import numpy as np
import google.generativeai as genai
import faiss
import pickle
import time

class RAGService:
    def __init__(self):
        self.index = None
        self.doc_store = {} 
        self.is_initialized = False
        self.model_name = "models/text-embedding-004"
        self.dimension = 768 

    def load_from_memory(self, documents, base_dir):
        """
        Builds the index directly from the list of documents passed in.
        Then saves a backup to disk for the next startup.
        """
        print(f"\nRAG: Processing {len(documents)} items from Memory...")
        
        if not documents:
            print("RAG Error: No documents provided.")
            return

      
        self._build_faiss_index(documents)
        

        index_path = os.path.join(base_dir, 'rag_index.bin')
        store_path = os.path.join(base_dir, 'rag_store.pkl')
        self._save_to_disk(index_path, store_path)
        
        self.is_initialized = True

    def load_from_disk_startup(self, base_dir):
        """
        Used ONLY when the server first starts up to load the cache.
        """
        index_path = os.path.join(base_dir, 'rag_index.bin')
        store_path = os.path.join(base_dir, 'rag_store.pkl')

        if os.path.exists(index_path) and os.path.exists(store_path):
            print(f" \n RAG: Loading Cache from Disk...")
            self._load_from_disk(index_path, store_path)
        else:
            print(f"No cache found. Waiting for first DB update.")

    # --- (Keep these helper functions exactly the same as before) ---
    def _build_faiss_index(self, documents):
        print(f"Generating Embeddings ...")
        embeddings = []
        valid_docs = {}
        BATCH_SIZE = 20 
        MAX_WORKERS = 5
        doc_texts = [d['text'] for d in documents]
        total_docs = len(doc_texts)

        for i in range(0, total_docs, BATCH_SIZE):
            batch = doc_texts[i : i + BATCH_SIZE]
            try:
                result = genai.embed_content(model=self.model_name, content=batch, task_type="retrieval_document")
                batch_embeddings = result['embedding']
                for j, vector in enumerate(batch_embeddings):
                    global_index = i + j
                    embeddings.append(vector)
                    valid_docs[global_index] = documents[global_index]
                time.sleep(0.1)
            except Exception as e:
                print(f"      Batch failed: {e}")

        if not embeddings: return
        emb_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(emb_array)
        self.dimension = emb_array.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(emb_array)
        self.doc_store = valid_docs

    def _save_to_disk(self, index_path, store_path):
        try:
            faiss.write_index(self.index, index_path)
            with open(store_path, 'wb') as f: pickle.dump(self.doc_store, f)
        except Exception as e: print(f"  Save Failed: {e}")

    def _load_from_disk(self, index_path, store_path):
        try:
            self.index = faiss.read_index(index_path)
            with open(store_path, 'rb') as f: self.doc_store = pickle.load(f)
            self.is_initialized = True
            print(f" Embeddings Loaded ({self.index.ntotal} vectors).")
        except Exception as e: print(f"   Load Failed: {e}")

    def find_best_matches(self, query, top_k=5):
        if not self.is_initialized or self.index is None: return []
        try:
            query_result = genai.embed_content(model=self.model_name, content=query, task_type="retrieval_query")
            q_emb = np.array([query_result['embedding']]).astype('float32')
            faiss.normalize_L2(q_emb)
            distances, indices = self.index.search(q_emb, top_k)
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx in self.doc_store:
                    results.append(self.doc_store[idx])
            return results
        except Exception as e:
            print(f"Search Error: {e}")
            return []

rag_service = RAGService()
# backend/shop_rag_pipelines.py
"""
Data processing & embedding pipeline for shop-level sales RAG.
Provides helpers to chunk sales summaries and to call ShopRAGService.
"""
import math
from services.shop_rag_service import shop_rag_service

def chunk_text(text, max_chunk_chars=800):
    # Simple chunker by characters, keeps sentence boundaries if possible.
    # print(f"[DEBUG] chunk_text called. Text length: {len(text)}")
    if len(text) <= max_chunk_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_chars
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        # try to break at last period before end
        cut = text.rfind('.', start, end)
        if cut <= start:
            cut = end
        chunks.append(text[start:cut+1].strip())
        start = cut + 1
    # print(f"[DEBUG] Text split into {len(chunks)} chunks.")
    return chunks

def build_and_index_shop(shop_id, sales_documents, base_dir=None):
    """
    sales_documents: list of dicts {'text':str, 'source':str}
    This will chunk long documents, attach metadata, and call shop_rag_service.
    """
    print(f"[DEBUG] build_and_index_shop called for Shop {shop_id}. Input docs: {len(sales_documents)}")
    prepared = []
    for idx, doc in enumerate(sales_documents):
        text = doc.get('text', '')
        # print(f"[DEBUG] Processing doc {idx} (source: {doc.get('source')}, length: {len(text)})")
        chunks = chunk_text(text, max_chunk_chars=900)
        for c_i, chunk in enumerate(chunks):
            prepared.append({
                'text': chunk,
                'source': doc.get('source', 'SalesData'),
                'meta': {
                    'orig_index': idx,
                    'chunk_index': c_i
                }
            })
            
    print(f"[DEBUG] Total chunks prepared for indexing: {len(prepared)}")
    
    # delegate to service
    from os import path
    if base_dir is None:
        base_dir = path.join(path.dirname(path.dirname(__file__)), "data", "shop_rag")
    
    print(f"[DEBUG] Delegating to shop_rag_service. Base dir: {base_dir}")
    result = shop_rag_service.build_index_for_shop(shop_id, prepared)
    print(f"[DEBUG] build_and_index_shop result: {result}")
    return result
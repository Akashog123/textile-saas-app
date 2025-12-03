import numpy as np
import os
import json
import re
from PIL import Image
import io
from config import Config

STORE_IMAGES_DIR = os.path.join(Config.BASE_DIR, "datasets", "fashion-dataset", "images")
EMBEDDINGS_PATH = os.path.join(Config.BASE_DIR, "data", "image_embeddings.npz")
EMBEDDINGS_META = os.path.join(Config.BASE_DIR, "data", "image_embeddings_meta.json")
os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)


def numeric_sort_key(filename):
    """Extract numbers from filename for correct number-wise sorting."""
    num = re.findall(r'\d+', filename)
    return int(num[0]) if num else 0


def extract_image_features(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((48, 48))
    return np.array(img).flatten()
def build_image_embeddings(images_dir=STORE_IMAGES_DIR, embeddings_path=EMBEDDINGS_PATH,
                           meta_path=EMBEDDINGS_META, force_rebuild=False, max_files=1000):
    """
    Compute embeddings for all images in images_dir using extract_image_features()
    and save:
      - embeddings: numpy array shape (N, D) (float32, L2-normalized)
      - ids: list of product ids (filenames without extension)
      - file_paths: corresponding relative file paths
    If force_rebuild is False and embeddings file exists, it will skip (unless images changed).
    
    Args:
        images_dir: Directory containing images
        embeddings_path: Path to save embeddings .npz file
        meta_path: Path to save metadata .json file
        force_rebuild: If True, rebuild embeddings even if they exist
        max_files: Maximum number of files to embed (default: 1000)
    """
    # If exists and not forced, skip
    if os.path.exists(embeddings_path) and os.path.exists(meta_path) and not force_rebuild:
        return

    image_files = [
        f for f in os.listdir(images_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    image_files = sorted(image_files, key=numeric_sort_key)
    if max_files:
        image_files = image_files[:max_files]
        print(f"Processing {len(image_files)} images (max_files={max_files})")

    ids = []
    file_paths = []
    embeddings = []

    for fname in image_files:
        product_id = os.path.splitext(fname)[0]
        fp = os.path.join("datasets", "fashion-dataset", "images", fname)
        try:
            with open(os.path.join(images_dir, fname), "rb") as f:
                emb = extract_image_features(f.read()).astype('float32')
                # L2 normalize once and store normalized vectors (cosine via dot)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                embeddings.append(emb)
                ids.append(product_id)
                file_paths.append(fp)
        except Exception as e:
            print(f"skip {fname}: {e}")
            continue

    if embeddings:
        embeddings_arr = np.vstack(embeddings).astype('float32')  # shape (N, D)
    else:
        embeddings_arr = np.empty((0, 0), dtype='float32')

    # Save embeddings (.npz) and meta
    np.savez_compressed(embeddings_path, embeddings=embeddings_arr)
    meta = {"ids": ids, "file_paths": file_paths}
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f)
    print(f"Saved {len(ids)} embeddings to {embeddings_path}")


def load_image_embeddings(embeddings_path=EMBEDDINGS_PATH, meta_path=EMBEDDINGS_META):
    """
    Load saved embeddings and meta.
    Returns: ids(list), file_paths(list), embeddings(np.array) (already L2-normalized)
    """
    if not os.path.exists(embeddings_path) or not os.path.exists(meta_path):
        return [], [], np.empty((0, 0), dtype='float32')

    with np.load(embeddings_path) as data:
        embeddings = data["embeddings"].astype('float32')
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    ids = meta.get("ids", [])
    file_paths = meta.get("file_paths", [])
    return ids, file_paths, embeddings

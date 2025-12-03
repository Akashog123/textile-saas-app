# Image Search Sample Images

## Files

| Image | Description | Best For Testing |
|-------|-------------|------------------|
| `sample_saree.jpg` | Traditional silk saree | Saree similarity search |
| `sample_silk_fabric.jpg` | Raw silk fabric texture | Fabric matching |
| `sample_cotton_fabric.jpg` | Cotton cloth pattern | Cotton product search |
| `sample_embroidered.jpg` | Embroidered ethnic wear | Decorated clothing |
| `sample_lehenga.jpg` | Bridal lehenga | Wedding attire search |

## Usage

### Visual Similarity Search
1. Login as any authenticated user
2. Navigate to **Search** → **Image Search**
3. Upload any image from this folder
4. View visually similar products from the catalog

### What It Finds

The image search uses NVIDIA NVCLIP embeddings to find products with similar:
- **Colors** - Matching color palettes
- **Patterns** - Similar designs and prints
- **Textures** - Fabric type similarities
- **Style** - Overall aesthetic match

## API Endpoint

```
POST /api/image-search/similar
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- image: <image_file>

Query Parameters:
- limit: 10 (number of results)
- lat: 28.6139 (optional, for nearby filtering)
- lon: 77.2090 (optional, for nearby filtering)
- radius_km: 50 (optional, search radius)
```

## Response Format

```json
{
  "status": "success",
  "similar_products": [
    {
      "id": 1,
      "name": "Blue Silk Saree",
      "category": "Sarees",
      "price": 8500,
      "similarity_score": 0.92,
      "image_url": "/static/images/...",
      "shop": {
        "id": 1,
        "name": "Silk Palace",
        "distance_km": 2.5
      }
    }
  ],
  "query_info": {
    "embedding_method": "nvidia_nvclip",
    "embedding_dim": 1024
  }
}
```

## Image Requirements

- **Formats**: JPG, JPEG, PNG
- **Max Size**: 16 MB
- **Recommended**: 600x600 to 1200x1200 pixels
- **Best Results**: Clear, well-lit product photos

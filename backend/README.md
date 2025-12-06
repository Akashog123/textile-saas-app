# Textile Saas App Backend

A powerful, unified Flask backend for the SE Textile platform, designed to drive intelligent workflows for Customers, Shop Owners, and Distributors. This system integrates advanced **AI forecasting**, **RAG-based assistants**, **semantic search**, and **geo-spatial analytics** under a robust, documented API.

## 🌟 Key Features

### 🧠 Advanced AI & Intelligence
- **Generative AI Integration**: Powered by **Google Gemini** and **Nvidia NIM API** for intelligent text generation and analysis.
- **RAG (Retrieval-Augmented Generation)**: Context-aware chatbots (`services/rag_service.py`, `services/shop_rag_service.py`) for shop owners and general queries.
- **Demand Forecasting**: Time-series forecasting using **Facebook Prophet** to predict regional demand trends.
- **Visual Intelligence**: **FAISS**-based product image search and comparison (`services/product_image_search.py`).
- **Voice Intelligence**: AI-powered voice search for product discovery with speech-to-text transcription (`routes/ai_find_stores.py`).
- **Semantic Search**: NVIDIA NIM embeddings with FAISS vector search for intelligent product discovery.

### 🏗️ Core Architecture
- **Flask Application Factory**: Modular, blueprint-based architecture.
- **SQLAlchemy ORM**: database interactions with SQLite (dev).
- **JWT Authentication**: Secure, role-based access control (RBAC).

### 📊 Business Logic Modules
- **Shop Management**: Inventory control, sales analytics, and AI-driven marketing content generation.
- **Customer Discovery**: Semantic product search, nearby shop location, and "visual search" by image.
- **Distributor Tools**: AI production planning, regional demand heatmaps, and supply chain tracking.

---

## 📁 Project Structure

```bash
backend/
├── app.py                 # Application entry point & Blueprint registration
├── config.py              # Configuration management class
├── requirements.txt       # Python dependencies
├── models/                # SQLAlchemy Database Models
│   └── model.py           # Database schemas and relationships
├── routes/                # API Route Definitions (Blueprints)
│   ├── auth_routes.py     # Authentication & Security
│   ├── profile_routes.py  # User profile management
│   ├── shop_routes.py     # Shop Owner operations
│   ├── inventory.py       # Product inventory management
│   ├── heatmap_routes.py  # Regional demand heatmaps
│   ├── trending_routes.py # Trending shops and products
│   ├── ai_find_stores.py  # AI Store Discovery with voice search
│   ├── top_selling_routes.py # Top selling products analytics
│   ├── stores_routes.py   # Store information and listings
│   ├── product_routes.py  # Product catalog and search
│   ├── inquiry.py         # Customer inquiries management
│   ├── discovery_portal.py # Customer discovery features
│   ├── shop_explorer.py   # Shop browsing and exploration
│   ├── marketing_routes.py # AI marketing content generation
│   ├── distributor_routes.py # Distributor dashboard and tools
│   ├── production_plan.py # AI production planning
│   ├── pdf_service.py     # PDF generation services
│   ├── catalog_routes.py  # Product catalog management
│   ├── nearby_search.py   # Location-based shop search
│   ├── performance_routes.py # Sales performance analytics
│   ├── review_routes.py   # Customer reviews and ratings
│   ├── chatbot_routes.py  # General AI chatbot
│   ├── customer_routes.py # Customer portal features
│   ├── image_search_routes.py # Visual product search
│   ├── supply_chain_routes.py # Supply chain management
│   └── shop_chatbot.py    # Shop-owner RAG chatbot
├── services/              # Specialized Business Logic & AI Services
│   ├── ai_service.py      # General AI wrapper (Gemini, OpenAI)
│   ├── ai_providers.py    # AI provider management
│   ├── rag_service.py     # General RAG Pipeline implementation
│   ├── shop_rag_service.py # Shop-owner specific RAG service
│   ├── prophet_service.py # Demand Forecasting with Prophet
│   ├── forecasting_service.py # Advanced forecasting utilities
│   ├── product_image_search.py # FAISS Vector Search for images
│   ├── nvidia_embedding_service.py # NVIDIA NIM embeddings
│   ├── sales_analytics_service.py # Sales analytics and reporting
│   └── search_service.py  # Semantic search with embeddings
├── utils/                 # Shared Utilities
│   ├── auth_utils.py      # Authentication helpers
│   ├── response_helpers.py # API response formatting
│   ├── database_health.py # Database monitoring
│   ├── export_data.py     # Data export utilities
│   ├── rag_pipeline.py    # RAG orchestration
│   ├── shop_rag_pipelines.py # Shop-specific RAG pipelines
│   ├── comprehensive_seeding.py # Database seeding
│   ├── validation.py      # Data validation utilities
│   ├── audio_validation.py # Voice file validation
│   ├── image_utils.py     # Image processing utilities
│   ├── inventory_utils.py # Inventory management helpers
│   └── performance_utils.py # Performance calculation utilities
├── data/ & demo-datasets/ # Raw data for demo and analysis
└── instance/              # SQLite database (se_textile.db)
```

---

## 🚀 Environment Setup

### 1. Prerequisites
- **Python**: 3.11
- **Virtual Environment**: Recommended (venv)

### 2. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root `backend/` directory:

```env
# Flask Settings
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=super-secret-key-change-me
PORT=5001

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here

# Database (Defaults to SQLite in /instance)
```

### 4. Running the Server

```bash
# Initialize DB and Start Server
python app.py
```

The server will start at **http://127.0.0.1:5001**.
- **Swagger UI**: Visit `http://127.0.0.1:5001/docs` for interactive API testing.
- **OpenAPI Spec**: Available at `http://127.0.0.1:5001/openapi.yaml`.

> **Note**: On the first run, the system may auto-seed the database with credentials using `utils/comprehensive_seeding.py` if `AUTO_SEED=true` (default).

---

## 📡 API Modules

The backend is organized into logical functional areas:

### 🔐 Authentication & Profile
- `/api/v1/auth`: Login, Register, Refresh Token.
- `/api/v1/profile`: User profile management.

### 🛍️ Customer Experience
- `/api/v1/customer`: Aggregated home page data (trending, popular).
- `/api/v1/products`: Product catalog search and filtering.
- `/api/v1/nearby-search`: Locate shops based on geo-coordinates.
- `/api/v1/image-search`: Find products using image uploads.
- `/api/v1/inquiry`: Create and manage fabric inquiries.
- `/api/v1/catalog`: Product catalog browsing.
- `/api/v1/stores`: Store listings and information.
- `/api/v1/trending-shops`: Trending shop discovery.
- `/api/v1/top-selling-products`: Best-selling product analytics.
- `/api/v1/reviews`: Customer reviews and ratings system.

### 🏪 Shop Owner Ecosystem
- `/api/v1/shop`: Dashboard stats, shop configuration.
- `/api/v1/inventory`: Product management, stock updates.
- `/api/v1/marketing`: AI-generated social media captions and strategies.
- `/api/v1/performance`: Detailed sales performance analytics.
- `/api/v1/shop-owner` (Chatbot): RAG-based assistant for shop owners.
- `/api/v1/supply-chain/shop/suppliers`: Manage distributor relationships.

### 🏭 Distributor & Insights
- `/api/v1/distributor`: Dashboard and planning tools.
- `/api/v1/production`: AI-driven production planning based on demand.
- `/api/v1/supply-chain`: Logistics and fulfillment tracking.
- `/api/v1/region-demand-heatmap`: Geospatial demand visualization.
- `/api/v1/ai-find-stores`: AI-powered store discovery with voice search.

### 🧠 AI Utilities
- `/api/v1/chatbot`: General purpose AI assistant.
- `/api/v1/pdf`: PDF generation services.
- `/api/v1/ai-find-stores`: Voice-enabled AI store discovery.

---

## 🧪 Testing

Run the test suite (if configured) using pytest:

```bash
pytest
```

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Module not found** | Ensure `venv` is activated and `pip install` succeeded. |
| **Database locked** | SQLite concurrency issue. restart, or switch to PostgreSQL. |
| **GEMINI_API_KEY missing** | Check `.env` file. AI features will fail without it. |
| **NVIDIA_API_KEY missing** | Check `.env` file. AI features will fail without it. |
| **Port in use** | Kill the process on port 5001 or change `PORT` in `.env`. |

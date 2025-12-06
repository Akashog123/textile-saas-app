# Textile Saas app

A **Vue 3 + Vite + Bootstrap 5** frontend application for textile supply chain management with role-based authentication supporting **Customers**, **Distributors**, and **Shop Owners/Managers**.

---

## 🚀 Quick Start

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate
# Activate virtual environment (Mac/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (create .env file)
# See backend/README.md for configuration details

# Start the backend server
python app.py
```
The backend will start at **http://127.0.0.1:5001**.

### Frontend Setup

```bash
# Navigate to frontend directory
cd textile-frontend

# Install dependencies
npm install

# Start development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build
```

## Trouble Shooting 

| Issue | Solution |
|-------|----------|
| **Backend: Module not found** | Ensure virtual environment is activated and `pip install -r requirements.txt` succeeded |
| **Backend: Database errors** | Check SQLite file permissions and ensure `instance/` directory exists |
| **Backend: AI features not working** | Verify `GEMINI_API_KEY` and `NVIDIA_API_KEY` are set in `.env` file |
| **Frontend: Axios error** | `npm install axios` |
| **Frontend: Vue Router error** | `npm install vue-router@4` |
| **Frontend: Bootstrap missing** | `npm install bootstrap @popperjs/core` |
| **Frontend: Dev server won't start** | Delete `node_modules` and `package-lock.json`, then `npm install` |
| **CORS errors** | Ensure backend is running on port 5001 and frontend on 5173 |


---

## 📁 Frontend Structure

```bash
textile-frontend/src/
  ├── api/
  │   └── axios.js              # Axios instance (baseURL: localhost:5001)
  ├── assets/
  │   └── main.css              # Global styles
  ├── components/
  │   └── NavBar.vue            # Main navigation component
  ├── router/
  │   └── index.js              # Vue Router configuration
  ├── views/
  │   ├── Login.vue             # Authentication page
  │   ├── customer/             # Customer role pages
  │   │   ├── CustomerHomePage.vue
  │   │   ├── CustomerProducts.vue
  │   │   ├── CustomerProfile.vue
  │   │   └── CustomerShops.vue
  │   ├── distributor/          # Distributor role pages
  │   │   ├── ProductionPlanning.vue
  │   │   └── RegionalDemand.vue
  │   └── shop/                 # Shop owner/manager pages
  │       ├── ShopDashboard.vue
  │       ├── ShopInquiry.vue
  │       ├── ShopInventory.vue
  │       └── ShopMarketing.vue
  ├── App.vue                   # Root component
  └── main.js                   # Application entry point
```

---

## 📁 Backend Structure

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

## 🔐 Seeded Login Credentials

Use these credentials on the **Sign In** tab for development:

| Role | Username | Password | Redirects To |
|------|----------|----------|--------------|
| **Shop Owner** | `shopowner1` | `ShopOwner123` | `/shop` |
| **Distributor** | `distributor1` | `Distributor123` | `/distributor` |
| **Customer** | `customer1` | `Customer123` | `/customer` |

> **Note**: These are development-only shortcuts to simulate an authenticated session.

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Axios errors | `npm install axios` |
| Vue Router errors | `npm install vue-router@4` |
| Bootstrap missing | `npm install bootstrap @popperjs/core` |
| Dev server won't start | Delete `node_modules` and `package-lock.json`, then `npm install` |

---

## 🏗️ Tech Stack

### Backend
- **Framework**: Flask 3.0 with Flask-SQLAlchemy
- **Database**: SQLite (development) with SQLAlchemy ORM
- **Authentication**: JWT with role-based access control
- **AI Services**: Google Gemini, NVIDIA NIM API, OpenAI
- **Vector Search**: FAISS with sentence-transformers
- **Forecasting**: Facebook Prophet for time-series analysis
- **Image Processing**: Pillow for image handling
- **PDF Generation**: FPDF for document creation

### Frontend
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite with HMR
- **UI Framework**: Bootstrap 5 + Bootstrap Icons
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Maps**: Leaflet with OpenStreetMap
- **Charts**: Chart.js with vue-chartjs
- **Voice Processing**: @ricky0123/vad-web

---

### Authentication Flow
1. Login/Register via `POST /login` or `/register`
2. Store JWT token + role in `localStorage`
3. NavBar hydrates from `localStorage` on mount
4. Token validated via `POST /verify_token`
5. Logout clears `localStorage` and calls `POST /logout`

### Role-Based Routing
- `customer` → `/customer`
- `distributor` → `/distributor`
- `shop_owner` / `manager` → `/shop`

### Code Style
- Use `<script setup>` syntax for all components
- Import paths use `@/` alias for `src/` directory
- Bootstrap classes for styling (no CSS frameworks)
- camelCase for variables, PascalCase for components
- snake_case for backend API payloads

---

## 👥 Team Members

| Name | Roll No | Role |
|------|---------|------|
| Akash O. G. | 23f2004955 | Frontend/Backend Developer |
| Afsal Sha | 21f2000304 | Product Manager |
| R Rahul Varma | 22f1000756 | Frontend Developer |
| Vyshakh K V | 21f1003728 | Backend Developer |
| Hari Govind J | 23f2004143 | Scrum Master/Backend |
| Joseph Manoj Louis | 21f3001750 | Scrum Master |
| Matlin Jeleshiya D | 22f2000506 | Tester |

---

## 📚 Additional Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [Vue Router Documentation](https://router.vuejs.org/)

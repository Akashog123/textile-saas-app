# SE Textile Backend

Unified Flask backend for the SE Textile platform. It consolidates authentication, catalog discovery, AI-assisted analytics, distributor tooling, production planning, and file-based workflows under a single API surface that is fully documented through an OpenAPI definition.

## Key Features

- **Flask + SQLAlchemy stack** with modular blueprints grouped by business capability.
- **JWT authentication** for login, session validation, and token verification.
- **AI integrations** (Google Gemini) power trend insights, production planning, and inquiry analysis.
- **Analytics & reporting** endpoints for heatmaps, trending shops, top-selling products, and distributor reports.
- **Catalog, inventory & shop management** flows supporting CSV/XLSX uploads and data seeding from curated datasets.
- **Static OpenAPI spec** (`backend/openapi.yaml`) served with Swagger UI at runtime for contract validation (`/docs`).

## Project Structure

```
backend/
├── app.py                 # Flask application factory & blueprint registration
├── config.py              # Central configuration (database, paths, API keys)
├── models/                # SQLAlchemy models
├── routes/                # Blueprint implementations (auth, catalog, ai, analytics, etc.)
├── utils/seed_data.py     # Minimal dataset seeding helpers
├── data/ & datasets/      # Source datasets used for seeding/sample analytics
├── instance/              # SQLite database & generated artifacts
├── openapi.yaml           # Static OpenAPI 3.0 specification
└── swagger-ui.html        # Bundled Swagger UI shell served at `/docs`
```

## Prerequisites

- Python 3.10+
- pip / virtualenv
- (Optional) Access keys for Gemini, MapMyIndia, or OpenAI services if you plan to exercise AI-backed endpoints.

## Environment Setup

1. **Create & activate a virtual environment**
   ```bash
   python -m venv backend/venv
   backend/venv/Scripts/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Create `.env` in `backend/`** (example values shown)
   ```env
   FLASK_ENV=development
   SECRET_KEY=replace-with-strong-secret
   GEMINI_API_KEY=your-gemini-key
   MAPMYINDIA_KEY=optional-mapmyindia-key
   OPENAI_API_KEY=optional-openai-key
   DATABASE_URL=sqlite:///backend/instance/se_textile.db  # optional override
   ```

   Additional optional overrides:
   - `UPLOAD_FOLDER`, `FAISS_INDEX_PATH`, `MAX_CONTENT_LENGTH_MB`
   - `PORT`, `CORS_ORIGINS`

4. **Seed datasets** – the first application start automatically invokes `seed_minimal_data()` which samples from `backend/data/Textile-2/` and `backend/datasets/`. Ensure those CSV assets remain in place.

## Running the Server

```bash
python backend/app.py
```

This will:
- Initialize the SQLite database inside `backend/instance/se_textile.db`
- Seed minimal data if the tables are empty
- Serve the API at `http://127.0.0.1:5001`

Environment-controlled alternatives:
```bash
flask --app backend.app run --host=0.0.0.0 --port=5001
```

## Core API Groups

All endpoints are prefixed with `/api/v1/…` unless otherwise noted. Refer to `openapi.yaml` for full request/response schemas.

| Route Group | Description |
|-------------|-------------|
| `/api/v1/auth` | Registration, login (JWT issuance), session validation, token verification, logout acknowledgements. |
| `/api/v1/catalog` | Load catalog data from datasets, keyword-filtered search (requires `keyword` query param), and paged views. |
| `/api/v1/ai-find-stores` | AI-assisted store discovery from text or audio uploads. |
| `/api/v1/compare-images` | Multipart image comparison against curated store references. |
| `/api/v1/region-demand-heatmap` | Demand heatmap analytics with optional date filtering. |
| `/api/v1/top-selling-products` & `/api/v1/trending-shops` | External product/shop analytics with AI summaries. |
| `/api/v1/shop`, `/api/v1/inventory`, `/api/v1/products` | Shop dashboards, inventory imports, product retrieval. |
| `/api/v1/distributor` & `/api/v1/production` | Distributor CSV workflows, PDF/CSV exports, AI production planning. |
| `/api/v1/inquiry` | Fabric inquiry submission with optional image upload & AI analysis; inquiry history retrieval. |
| `/api/v1/customer/*` & `/api/v1/marketing` | Discovery portals and marketing intelligence. |
| `/api/v1/pdf` | Generate PDF summaries from structured JSON input. |
| `/uploads/<path>` / `/datasets/<path>` | Serve uploaded assets and bundled datasets. |
| `/health` | Basic health probe with environment metadata. |

The root endpoint (`GET /`) enumerates all registered routes dynamically for quick verification.

## Database & Seeding Notes

- Default persistence uses SQLite; override `DATABASE_URL` for PostgreSQL/MySQL deployments.
- `seed_minimal_data()` samples reasonable subsets to keep local environments lightweight.
- Datasets live under `backend/data/Textile-2` and `backend/datasets/fashion-dataset`. Ensure CSV schema changes remain backwards compatible with the seeding logic.

## Testing & Quality

The project ships without a mandatory test suite; add your preferred tooling (e.g., `pytest`) and integrate against the blueprints as needed. When modifying routes, mirror the changes in `openapi.yaml` to keep Swagger accurate.

## API Documentation & Swagger UI

- **OpenAPI spec:** `http://127.0.0.1:5001/openapi.yaml`
- **Interactive docs:** `http://127.0.0.1:5001/docs`

The Swagger UI is backed by the static YAML file committed to the repository. After editing routes or schemas:

1. Update `backend/openapi.yaml` with matching request/response contracts.
2. Restart the Flask server so the latest spec is served.
3. Visit `/docs`, authorize with a JWT (Authorize button) when required, and exercise endpoints directly against your local server.

This flow ensures that the OpenAPI contract and runtime implementation remain in sync for QA, frontend consumption, and external integrations.

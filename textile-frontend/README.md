# Textile Saas App Frontend

A simplified, modern, and high-performance Vue 3 Single Page Application (SPA) designed for the SE Textile platform. This application features a premium **Glassmorphism** design aesthetic and provides tailored role-based dashboards for **Customers**, **Shop Owners**, and **Distributors**.

## 🌟 Key Features

### ✨ Core Technology
- **Vue 3 Composition API**: Built using `<script setup>` for clean and efficient component logic.
- **Vite**: Ultra-fast build tool and development server.
- **State Management**: Reactive state management using Vue 3's native reactivity system.
- **Robust Routing**: Secure role-based routing with **Vue Router 4**.

### 🎨 Modern UI/UX
- **Glassmorphism Design System**: A custom-built design system featuring mesh gradients, translucent cards, and smooth micro-interactions.
- **Responsive Layouts**: Mobile-first architecture ensuring a seamless experience across all devices.
- **Custom Theming**: Centralized design tokens in `src/styles/variables.css` for easy theming and consistency.
- **Dynamic Interactions**: Components featuring hover effects, loading states, and smooth transitions.

### 🗺️ Integration & Intelligence
- **Map Integration**: "Nearby Shops" functionality powered by **Leaflet** with **OpenStreetMap** for precise location services.
- **AI-Powered Tools**:
    - **Smart Marketing**: AI caption and social content generation for Shop Owners.
    - **Demand forecasting**: AI-driven predictive analytics for Distributors.
    - **Visual Search**: Image-based product search capability.
    - **Voice Search**: Audio-based product search capability.
- **Wishlist System**: robust "Add to Wishlist" feature for saving favorite products.

---

## 📁 Project Structure

```bash
textile-frontend/
├── index.html              # Application entry point
├── package.json            # Project dependencies and scripts
├── vite.config.js          # Vite configuration
├── public/                 # Static public assets
└── src/
    ├── main.js             # Vue app initialization
    ├── App.vue             # Root component
    ├── api/                # API Service Layer (Axios)
    │   ├── axios.js        # Axios instance configuration
    │   ├── apiAuth.js      # Authentication services
    │   ├── apiShop.js      # Shop & Inventory management
    │   ├── apiCustomer.js  # Customer-facing features
    │   ├── apiAI.js        # AI Service endpoints
    │   ├── apiAnalytics.js # Analytics and reporting
    │   ├── apiCatalog.js   # Product catalog services
    │   ├── apiDistributor.js # Distributor services
    │   ├── apiImages.js    # Image upload and processing
    │   ├── apiInquiry.js   # Customer inquiry management
    │   ├── apiInventory.js # Inventory management
    │   ├── apiMarketing.js # Marketing content generation
    │   ├── apiProducts.js  # Product search and management
    │   ├── apiProfile.js   # User profile services
    │   ├── apiReviews.js   # Customer reviews
    │   └── apiSupplyChain.js # Supply chain management
    ├── assets/             # Images and global styles
    ├── styles/             # Design System
    │   ├── variables.css   # Global CSS variables (Colors, Fonts, Gradients)
    │   ├── theme.css       # Global component styles & utilities
    │   └── theme-config.js # JS-based theme configuration
    ├── components/         # Reusable UI Components
    │   ├── NavBar.vue      # Responsive Navigation
    │   ├── CustomerSearchBar.vue # Voice-enabled search component
    │   ├── ShopLocatorMap.vue # Interactive map component
    │   └── ...
    ├── assets/             # Images and global styles
    ├── styles/             # Design System
    │   ├── variables.css   # Global CSS variables (Colors, Fonts, Gradients)
    │   ├── theme.css       # Global component styles & utilities
    │   └── theme-config.js # JS-based theme configuration
    ├── components/         # Reusable UI Components
    │   ├── NavBar.vue      # Responsive Navigation
    │   └── ...
    ├── router/             # Route definitions & Guard checks
    └── views/              # Page Views
        ├── LandingPage.vue         # Public Landing Page
        ├── Login.vue               # Authentication View
        ├── NotFound.vue            # 404 Error Page
        ├── customer/               # Customer Portal
        │   ├── CustomerHomePage.vue
        │   ├── CustomerProducts.vue
        │   ├── CustomerShops.vue
        │   ├── CustomerShopDetail.vue
        │   ├── CustomerProductDetail.vue
        │   ├── CustomerProfile.vue
        │   ├── CustomerWishlist.vue
        │   └── ...
        ├── shop/                   # Shop Owner Portal
        │   ├── ShopDashboard.vue
        │   ├── ShopInventory.vue
        │   ├── ShopMarketing.vue
        │   ├── ShopInquiry.vue
        │   ├── ShopProfile.vue
        │   └── ...
        └── distributor/            # Distributor Portal
            ├── DistributorHomePage.vue
            ├── ProductionPlanning.vue
            ├── RegionalDemand.vue
            ├── DistributorInquiries.vue
            └── ...
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js**: v20.19.0 || >=22.12.0
- **npm**: v9.0.0 or higher

### Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository-url>
    cd textile-frontend
    ```

2.  **Install Dependencies**:
    ```bash
    npm install
    ```

3.  **Start Development Server**:
    ```bash
    npm run dev
    ```
    The app will be available at **http://localhost:5173**.

    > **Note**: Ensure the backend server is running on port **5001**.

### Production Build

To build the application for production deployment:

```bash
npm run build
```
The optimized assets will be generated in the `dist/` directory.

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory to configure the application:

```env
# Backend API Base URL
VITE_API_URL=http://localhost:5001/api/v1

# MapmyIndia API Config (if applicable frontend-side)
VITE_MAP_API_KEY=your_key_here
```

### API Configuration
The base Axios instance is configured in `src/api/axios.js`. It automatically attaches the JWT token from `localStorage` to every request.

---

## 👥 User Modules

### 🛍️ Customer
- **Home**: Trending fabrics and popular shops with geolocation.
- **Product Discovery**: Advanced search with voice search, filtering, and image search.
- **Shop Finder**: Locate nearby textile shops with interactive maps.
- **Product Details**: Individual product pages with reviews and ratings.
- **Shop Details**: Detailed shop information with location mapping.
- **Wishlist**: Save favorite products for later.
- **Reviews**: Rate and review products and shops.
- **Profile**: Manage account details.

### 🏪 Shop Owner
- **Dashboard**: Real-time sales overview and AI-driven insights with charts.
- **Inventory**: Manage stock levels, add products, and bulk upload via CSV.
- **Marketing Studio**: Generate AI content for social media marketing.
- **Inquiries**: Respond to customer requests and manage communications.
- **Performance Analytics**: Detailed sales performance with visual analytics.
- **Profile**: Manage shop information and location settings.

### 🏭 Distributor
- **Home Dashboard**: Overview of production planning and regional demand.
- **Production Planning**: AI-driven production planning based on demand forecasts.
- **Regional Demand**: Interactive heatmaps showing demand hotspots.
- **Shop Inquiries**: Manage and respond to bulk shop inquiries.
- **Supply Chain**: Monitor logistics and distributor relationships.

---

## 🛠️ Development Guidelines

### Styling Philosophy
We prioritize a custom **Glassmorphism** aesthetic over generic Bootstrap looks.
- Use `var(--glass-bg)`, `var(--glass-border)`, and `var(--primary-gradient)` from `variables.css`.
- Avoid hardcoded colors; strictly use the defined CSS variables.
- Keep the UI "airy" with generous padding and translucent backgrounds.

### Recommended Tooling
- **VS Code** with **Volar** extension.
- **ESLint** & **Prettier** for code formatting.

---

## 🏗️ Tech Stack

- **Frontend Framework**: Vue 3 (Composition API with `<script setup>`)
- **Build Tool**: Vite (with HMR)
- **UI Framework**: Bootstrap 5 + Bootstrap Icons
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Maps**: Leaflet with OpenStreetMap
- **Charts**: Chart.js with vue-chartjs
- **Voice Processing**: @ricky0123/vad-web for voice activity detection
- **Backend**: REST API on `http://localhost:5001`

## 📄 License
MIT License

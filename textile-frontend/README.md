# SE Textile Frontend

Vue 3 Single Page Application for the SE Textile platform with role-based dashboards for Customers, Shop Owners, and Distributors.

## 🌟 Features

- **Vue 3 Composition API** with `<script setup>` syntax
- **Vite** build tool for fast development
- **Bootstrap 5** responsive UI framework
- **Role-based routing** with Vue Router 4
- **JWT authentication** with localStorage persistence
- **Axios** HTTP client with interceptors

## 📁 Project Structure

```
textile-frontend/
├── index.html              # Entry HTML
├── package.json            # Dependencies
├── vite.config.js          # Vite configuration
├── public/                 # Static assets
└── src/
    ├── main.js             # App entry point
    ├── App.vue             # Root component
    ├── api/                # Axios API clients
    │   ├── axios.js        # Base Axios instance
    │   ├── apiAuth.js      # Authentication APIs
    │   ├── apiCatalog.js   # Product catalog APIs
    │   ├── apiAnalytics.js # Analytics APIs
    │   └── ...
    ├── assets/
    │   └── main.css        # Global styles
    ├── components/         # Reusable components
    │   ├── NavBar.vue
    │   └── ...
    ├── router/
    │   └── index.js        # Route definitions
    └── views/
        ├── Login.vue               # Auth page
        ├── LandingPage.vue         # Home page
        ├── customer/               # Customer views
        │   ├── CustomerHomePage.vue
        │   ├── CustomerProducts.vue
        │   ├── CustomerProductDetail.vue
        │   ├── CustomerShops.vue
        │   ├── CustomerShopDetail.vue
        │   └── CustomerProfile.vue
        ├── shop/                   # Shop owner views
        │   ├── ShopDashboard.vue
        │   ├── ShopInventory.vue
        │   ├── ShopMarketing.vue
        │   ├── ShopInquiry.vue
        │   └── ShopProfile.vue
        └── distributor/            # Distributor views
            ├── DistributorHomePage.vue
            ├── ProductionPlanning.vue
            └── RegionalDemand.vue
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm

### Installation

```bash
cd textile-frontend
npm install
```

### Development Server

```bash
npm run dev
```

App runs at: **http://localhost:5173**

> ⚠️ Ensure backend is running on port 5001

### Production Build

```bash
npm run build
```

Output in `dist/` folder.

## 🔧 Configuration

### API Base URL

Edit `src/api/axios.js` to change backend URL:

```javascript
const axiosInstance = axios.create({
  baseURL: 'http://localhost:5001/api/v1',
  // ...
});
```

### Environment Variables

Create `.env` file (optional):

```env
VITE_API_URL=http://localhost:5001/api/v1
```

## 👥 User Roles & Views

### Customer (`/customer`)
| View | Features |
|------|----------|
| Home | Product search, trending items |
| Products | Browse catalog, semantic search, image search |
| Product Detail | Full product info, similar items |
| Shops | Discover nearby shops |
| Shop Detail | Shop info, products, reviews |
| Profile | Account settings |

### Shop Owner (`/shop`)
| View | Features |
|------|----------|
| Dashboard | AI insights, sales analytics, recommendations |
| Inventory | Stock management, CSV import, alerts |
| Marketing | AI caption generator, social content |
| Inquiries | Customer fabric inquiries |
| Profile | Shop settings |

### Distributor (`/distributor`)
| View | Features |
|------|----------|
| Home | Overview, quick stats |
| Production Planning | AI forecasting, CSV upload |
| Regional Demand | Heatmaps, geographic analytics |

## 🔐 Authentication

### Flow
1. User logs in via `/login`
2. JWT token stored in `localStorage`
3. Token sent in `Authorization` header
4. Role-based redirect on login

### localStorage Keys
- `token` - JWT access token
- `role` - User role (customer, shop_owner, distributor)
- `user` - User object JSON

## 🛠️ Development

### IDE Setup
- [VS Code](https://code.visualstudio.com/)
- [Vue (Official) Extension](https://marketplace.visualstudio.com/items?itemName=Vue.volar)
- Disable Vetur if installed

### Code Style
- `<script setup>` syntax for all components
- `@/` alias for `src/` imports
- Bootstrap 5 classes for styling
- camelCase for JS, snake_case for API payloads

### Useful Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | `npm install` |
| CORS errors | Check backend is on port 5001 |
| Login not working | Clear localStorage, check backend |
| Styles missing | `npm install bootstrap @popperjs/core` |
| Router errors | `npm install vue-router@4` |
| Build fails | Delete `node_modules`, reinstall |

### Clear Cache & Reinstall

```bash
rm -rf node_modules package-lock.json
npm install
```

## 📚 API Integration

### Example API Call

```javascript
import { apiAuth } from '@/api/apiAuth';

// Login
const response = await apiAuth.login({
  email: 'user@example.com',
  password: 'password'
});

// Token stored automatically via interceptor
```

### Available API Modules
- `apiAuth.js` - Authentication
- `apiCatalog.js` - Product catalog
- `apiAnalytics.js` - Analytics data
- `apiAI.js` - AI features
- `apiShop.js` - Shop operations
- `apiInventory.js` - Inventory management

## 📱 Responsive Design

Built with Bootstrap 5 grid system:
- Mobile-first approach
- Breakpoints: sm, md, lg, xl, xxl
- Responsive navigation with offcanvas

## 📄 License

MIT License

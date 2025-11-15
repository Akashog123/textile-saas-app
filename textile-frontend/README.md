# Textile Frontend - Vue 3 + Vite

A modern, responsive frontend for the SE-Textile App built with **Vue 3**, **Vite**, and **Bootstrap 5**.

---

## 🎯 Features

- **Role-Based Authentication**: Customer, Distributor, Shop Owner/Manager
- **Modern UI**: Bootstrap 5 responsive design
- **Fast Development**: Vite with Hot Module Replacement (HMR)
- **Vue 3 Composition API**: Using `<script setup>` syntax
- **Vue Router**: Role-based navigation with dynamic dashboards
- **Axios Integration**: Centralized API communication

---

## 🚀 Project Setup

### Install Dependencies

```sh
npm install
```

### Development Server (with Hot-Reload)

```sh
npm run dev
```

The app will be available at `http://localhost:5173` (default Vite port)

### Build for Production

```sh
npm run build
```

Production files will be in the `dist/` directory.

---

## 🔧 Recommended IDE Setup

### VS Code
- [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) - **Enable this**
- Disable Vetur (if installed) - conflicts with Vue Official extension

### Browser DevTools

#### Chromium-based (Chrome, Edge, Brave)
- Install [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
- Enable [Custom Object Formatters](http://bit.ly/object-formatters) in DevTools settings

#### Firefox
- Install [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
- Enable [Custom Object Formatters](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

---

## 📁 Project Structure

```
src/
├── api/
│   └── axios.js           # Axios instance (baseURL: http://localhost:5001)
├── assets/
│   └── main.css           # Global styles
├── components/
│   └── NavBar.vue         # Main navigation with role-based links
├── router/
│   └── index.js           # Vue Router configuration
├── views/
│   ├── Login.vue          # Authentication page
│   ├── customer/          # Customer dashboard pages
│   │   ├── CustomerHomePage.vue
│   │   ├── CustomerProducts.vue
│   │   ├── CustomerProfile.vue
│   │   └── CustomerShops.vue
│   ├── distributor/       # Distributor dashboard pages
│   │   ├── ProductionPlanning.vue
│   │   └── RegionalDemand.vue
│   └── shop/              # Shop owner/manager pages
│       ├── ShopDashboard.vue
│       ├── ShopInquiry.vue
│       ├── ShopInventory.vue
│       └── ShopMarketing.vue
├── App.vue                # Root component
└── main.js                # Application entry point
```

---

## 🔑 Authentication

### Mock Login Credentials (Development)

| Role | Username | Password | Dashboard Route |
|------|----------|----------|-----------------|
| Shop Owner | `shopowner` | `shop` | `/shop` |
| Distributor | `distributor` | `dist` | `/distributor` |
| Customer | `customer` | `cust` | `/customer` |

> These credentials store a mock token and role in `localStorage` for development purposes.

### Backend API
The app expects a backend API running on `http://localhost:5001` with these endpoints:
- `POST /login` - Returns `{ token, role, username, user_id }`
- `POST /register` - Accepts role-specific registration payloads
- `POST /verify_token` - Validates JWT token
- `POST /logout` - Invalidates session

---

## 🛠️ Troubleshooting

| Error | Solution |
|-------|----------|
| `Cannot find module 'axios'` | `npm install axios` |
| `Cannot find module 'vue-router'` | `npm install vue-router@4` |
| Bootstrap styles not loading | `npm install bootstrap @popperjs/core` |
| Port 5173 already in use | Kill the process or change port in `vite.config.js` |
| HMR not working | Check firewall settings or restart dev server |

---

## ⚙️ Configuration

### Vite Configuration
See [Vite Configuration Reference](https://vite.dev/config/) for customization options.

Key settings in `vite.config.js`:
- **Alias**: `@` points to `src/` directory
- **Plugins**: Vue plugin for SFC support
- **Server**: Dev server configuration

### API Base URL
Configured in two places:
- `src/main.js` - Global Axios instance
- `src/api/axios.js` - Dedicated API module

Both point to `http://localhost:5001`

---

## 🎨 Styling

- **Bootstrap 5**: Primary UI framework
- **Custom CSS**: `src/assets/main.css` for global styles
- **Scoped Styles**: Use `<style scoped>` in `.vue` files

Bootstrap is imported globally in `main.js`:
```javascript
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
```

---

## 🧭 Routing

Routes are defined in `src/router/index.js` with role-based redirection:

- `/` → redirects to `/login`
- `/login` → Login/Register page
- `/customer` → Customer dashboard
- `/distributor` → Distributor dashboard
- `/shop` → Shop owner/manager dashboard

Each role has nested routes for specific pages (e.g., `/customer/products`, `/shop/inventory`).

---

## 📦 Dependencies

### Core
- `vue` - ^3.x
- `vue-router` - ^4.x
- `axios` - Latest
- `bootstrap` - ^5.x
- `@popperjs/core` - ^2.x

### Dev Dependencies
- `vite` - ^5.x
- `@vitejs/plugin-vue` - Latest

---

## 🤝 Development Workflow

1. **Pull latest changes**: `git pull origin main`
2. **Work on your branch**: `git checkout yourname`
3. **Make changes and test**: `npm run dev`
4. **Commit**: `git add . && git commit -m "message"`
5. **Push to your branch**: `git push origin yourname`
6. **Merge**: Only in team meetings to avoid conflicts

---

## 📚 Learn More

- [Vue 3 Official Docs](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Vue Router Guide](https://router.vuejs.org/)
- [Bootstrap 5 Docs](https://getbootstrap.com/)
- [Axios Documentation](https://axios-http.com/)

---

## 📄 License

This project is part of the SE-Textile App academic project.

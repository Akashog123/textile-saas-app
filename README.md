# Textile Saas app

A **Vue 3 + Vite + Bootstrap 5** frontend application for textile supply chain management with role-based authentication supporting **Customers**, **Distributors**, and **Shop Owners/Managers**.

---

## 🚀 Quick Start

### Prerequisites
- Node.js (v16+)
- npm or yarn
- Backend API running on `http://localhost:5001`

### Installation & Running

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

Issue	            Fix
---------------------------------------------
Axios error	        npm install axios
Vue Router error	npm install vue-router@4
Bootstrap missing	npm install bootstrap @popperjs/core

#Pull Push and Merge 

Check for merge conflicts if any conflicts resolve it in front of a team member and update it. 

git pull for pulling code 

git push for pushing to the particular branch 

git commit for commiting the code 

git checkout main to checkout to main branch 

git checkout yourname to checkout to yours 

Once you push the code in your branch then wait for reccuring meeting and merge in front of your teammates to avoid merge conflict errors

---

## 📁 Project Structure

```
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

## 🔐 Mock Login Credentials

Use these credentials on the **Sign In** tab for development:

| Role | Username | Password | Redirects To |
|------|----------|----------|--------------|
| **Shop Owner** | `shopowner` | `shop` | `/shop` |
| **Distributor** | `distributor` | `dist` | `/distributor` |
| **Customer** | `customer` | `cust` | `/customer` |

> **Note**: These are development-only shortcuts. They store a mock token in `localStorage` (key: `token`) and role (key: `role`) to simulate an authenticated session.

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Axios errors | `npm install axios` |
| Vue Router errors | `npm install vue-router@4` |
| Bootstrap missing | `npm install bootstrap @popperjs/core` |
| Dev server won't start | Delete `node_modules` and `package-lock.json`, then `npm install` |

---

## 🔄 Git Workflow (Team Convention)

### Branch Strategy
- **Main Branch**: `main` (protected - merge only in team meetings)
- **Personal Branches**: Use your name (e.g., `akash`, `afsal`, `rahul`)

### Daily Workflow

```bash
# 1. Always pull latest changes before starting work
git pull origin main

# 2. Switch to your personal branch
git checkout yourname

# 3. Make your changes and commit
git add .
git commit -m "Your descriptive commit message"

# 4. Push to YOUR branch (NOT main)
git push origin yourname
```

### Important Rules
- ✅ **DO**: Work on your personal branch
- ✅ **DO**: Pull before starting work each day
- ✅ **DO**: Resolve merge conflicts with a team member present
- ❌ **DON'T**: Commit directly to `main` branch
- ❌ **DON'T**: Merge to `main` alone - wait for team meetings
- ❌ **DON'T**: Force push (`git push -f`) without team approval

### If You Accidentally Committed to Main

```bash
# Push your main branch to your personal branch
git push origin main:yourname

# Reset your local main to match remote
git reset --hard origin/main

# Switch to your personal branch
git checkout yourname
```

---

## 🏗️ Tech Stack

- **Frontend Framework**: Vue 3 (Composition API with `<script setup>`)
- **Build Tool**: Vite (with HMR)
- **UI Framework**: Bootstrap 5 + Popper.js
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Backend**: REST API on `http://localhost:5001`

---

## 📝 Development Notes

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

Check the repository branches to see active team members. Each member should have their own branch for development.

---

## 📚 Additional Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [Vue Router Documentation](https://router.vuejs.org/)

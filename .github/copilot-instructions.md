# SE-Textile App - AI Agent Instructions

## Project Overview
A **Vue 3 + Vite + Bootstrap 5** frontend application for textile supply chain management with role-based authentication supporting Customers, Manufacturers, and Shop Owners/Managers. Backend API runs on `http://localhost:5001`.

## Architecture

### Frontend Structure
- **Framework**: Vue 3 (Composition API with `<script setup>`)
- **Bundler**: Vite with HMR
- **UI Framework**: Bootstrap 5 + Popper.js
- **Routing**: Vue Router 4 with role-based navigation
- **HTTP Client**: Axios (global instance + dedicated API module)

### Key Directories
```
textile-frontend/src/
  ├── api/axios.js          # Axios instance (baseURL: localhost:5001)
  ├── components/           # Shared components (NavBar)
  ├── views/                # Route-level components (Login, role dashboards)
  ├── router/index.js       # Route definitions with role-based paths
  └── assets/main.css       # Global styles
```

## Critical Patterns

### Authentication & State Management
- **Token Storage**: JWT tokens stored in `localStorage` with keys: `token`, `role`, `username`, `user_id`
- **Auth Flow**: 
  1. Login/Register via `POST /login` or `/register`
  2. Store token + role in localStorage
  3. NavBar hydrates from localStorage on mount, validates via `POST /verify_token`
  4. Logout clears localStorage and calls `POST /logout`

**Example**: See `NavBar.vue` `hydrateFromStorage()` function for session restoration pattern.

### Role-Based Navigation
Roles map to specific dashboards:
- `customer` → `/customer`
- `manufacturer` → `/manufacturer`  
- `shop_owner` → `/shop`
- `manager` → `/shop`

**Navigation links** are dynamically generated in `NavBar.vue` using the `ROLE_NAV` lookup object based on stored role.

### API Communication
- **Global Axios**: `this.$axios` available in components (configured in `main.js`)
- **Dedicated Instance**: Import from `@/api/axios.js` for typed requests
- **Base URL**: `http://localhost:5001` (set in both `main.js` and `api/axios.js`)

**Pattern**: Use `api` import in `<script setup>` components:
```javascript
import api from '@/api/axios'
const { data } = await api.post('/login', credentials)
```

### Registration Form Structure
Multi-role registration with conditional fields:
- **Common**: `name`, `username`, `password`, `role`
- **Customer-only**: `email`
- **Shop Owner-only**: `shop: { name, address, mobile }`
- **Manufacturer-only**: `manufacturer: { plant_name, address, mobile }`

Payload transformation converts camelCase frontend fields to snake_case for backend (e.g., `plantName` → `plant_name`).

## Development Workflow

### Setup & Running
```powershell
cd textile-frontend
npm install
npm run dev  # Runs on Vite dev server (typically :5173)
```

### Common Issues & Fixes
| Issue | Solution |
|-------|----------|
| Axios errors | `npm install axios` |
| Router errors | `npm install vue-router@4` |
| Bootstrap missing | `npm install bootstrap @popperjs/core` |

### Git Workflow (Team Convention)
1. **Branch naming**: Use your name (e.g., `git checkout yourname`)
2. **Never merge alone**: Merge to `main` only in team meetings to avoid conflicts
3. **Pull before push**: Always `git pull` before starting work
4. **Conflict resolution**: Resolve conflicts with a team member present

## Component Conventions

### Vue 3 Composition API
- Always use `<script setup>` syntax
- Import components/composables at top of script
- Use `ref()` for reactive primitives, `computed()` for derived state
- Destructure router/route: `const router = useRouter()`

### Bootstrap Integration
- Bootstrap CSS/JS imported globally in `main.js`
- Use Bootstrap classes directly in templates
- Navbar uses `data-bs-toggle` attributes for collapse behavior
- Forms follow Bootstrap form structure (`.form-label`, `.form-control`)

### Routing
- All routes redirect `/` to `/login` by default
- Use `createWebHistory(import.meta.url)` for Vite compatibility
- Route guards NOT implemented (add if protecting authenticated routes)

## Testing & Debugging

### Browser DevTools
- **Recommended**: Chromium browsers with Vue.js devtools extension
- **Enable**: Custom Object Formatters in Chrome DevTools settings
- **Network Tab**: Monitor API calls to `localhost:5001`

### Backend Dependency
Frontend expects backend endpoints:
- `POST /login` - Returns `{ token, role, username, user_id }`
- `POST /register` - Accepts role-specific payloads
- `POST /verify_token` - Validates JWT token
- `POST /logout` - Invalidates session

## Code Style

### Imports
Use `@` alias for `src/` directory:
```javascript
import api from '@/api/axios'
import NavBar from '@/components/NavBar.vue'
```

### Naming
- **Components**: PascalCase (e.g., `NavBar.vue`, `CustomerHome.vue`)
- **Variables**: camelCase (e.g., `loginForm`, `isLoggedIn`)
- **API payloads**: snake_case keys for backend compatibility

### Async Handling
Wrap API calls in try-catch with loading states and user-friendly error messages:
```javascript
try {
  const { data } = await api.post('/endpoint', payload)
  // success logic
} catch (err) {
  errorMessage.value = err?.response?.data?.message || 'Operation failed'
}
```

## Known Limitations
- No backend included in this repository (runs separately on port 5001)
- Role dashboards (`CustomerHome.vue`, etc.) are placeholder components
- No route guards - authenticated routes accessible via direct URL
- Password validation only checks match, not strength
- No refresh token mechanism implemented

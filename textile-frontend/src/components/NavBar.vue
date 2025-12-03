<template>
  <div class="navbar-wrapper">
    <nav class="navbar navbar-expand-lg fixed-top">
      <div class="container">
        <router-link to="/" class="navbar-brand">
          <div class="brand-icon">
            <i class="bi bi-flower1"></i>
          </div>
          <span class="brand-text">SE Textile</span>
        </router-link>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNav"
          aria-controls="mainNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="mainNav">
          <ul class="navbar-nav ms-auto">
            <!-- Navigation links for authenticated users -->
            <template v-if="isAuthenticated && user">
              <!-- Customer Navigation -->
              <template v-if="user.role === 'customer'">
                <li class="nav-item">
                  <router-link to="/customer" class="nav-link" exact>
                    <i class="bi bi-house-door me-2"></i>Home
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/customer/products" class="nav-link">
                    <i class="bi bi-grid me-2"></i>Products
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/customer/shops" class="nav-link">
                    <i class="bi bi-shop me-2"></i>Shops
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/customer/profile" class="nav-link">
                    <i class="bi bi-person me-2"></i>Profile
                  </router-link>
                </li>
              </template>

              <!-- Shop Owner Navigation -->
              <template v-if="user.role === 'shop_owner' || user.role === 'manager'">
                <li class="nav-item">
                  <router-link to="/shop/dashboard" class="nav-link">
                    <i class="bi bi-speedometer2 me-2"></i>Dashboard
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/inventory" class="nav-link">
                    <i class="bi bi-box-seam me-2"></i>Inventory
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/marketing" class="nav-link">
                    <i class="bi bi-megaphone me-2"></i>Marketing
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/inquiry" class="nav-link">
                    <i class="bi bi-chat-dots me-2"></i>Inquiry
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/profile" class="nav-link">
                    <i class="bi bi-person me-2"></i>Profile
                  </router-link>
                </li>
              </template>

              <!-- Distributor Navigation -->
              <template v-if="user.role === 'distributor' || user.role === 'manufacturer'">
                <li class="nav-item">
                  <router-link to="/distributor" class="nav-link" exact>
                    <i class="bi bi-house-door me-2"></i>Home
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/distributor/planning" class="nav-link">
                    <i class="bi bi-graph-up me-2"></i>Planning
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/distributor/regional-demand" class="nav-link">
                    <i class="bi bi-geo-alt me-2"></i>Regional Demand
                  </router-link>
                </li>
              </template>
            </template>

            <!-- User Menu -->
            <li class="nav-item dropdown" v-if="isAuthenticated && user">
              <a 
                class="nav-link dropdown-toggle d-flex align-items-center" 
                href="#" 
                role="button" 
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                <i class="bi bi-person-circle me-2"></i>
                {{ user.username || user.email }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><h6 class="dropdown-header">Welcome, {{ user.username || user.email }}</h6></li>
                <li><hr class="dropdown-divider"></li>
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="$emit('logout')">
                    <i class="bi bi-box-arrow-right me-2"></i>Logout
                  </a>
                </li>
              </ul>
            </li>

            <!-- Login/Register for non-authenticated users -->
            <template v-if="!isAuthenticated">
              <li class="nav-item">
                <router-link to="/login" class="nav-link">
                  <i class="bi bi-box-arrow-in-right me-2"></i>Sign In
                </router-link>
              </li>
              <li class="nav-item">
                <router-link to="/login" class="btn btn-primary btn-sm ms-2">
                  Get Started
                </router-link>
              </li>
            </template>
          </ul>
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  user: {
    type: Object,
    default: null
  },
  isAuthenticated: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['logout', 'refresh-auth'])

// Computed properties
const userRole = computed(() => props.user?.role || '')
const userName = computed(() => props.user?.username || props.user?.email || 'User')

// Role-based helpers
const isShopRole = computed(() => ['shop_owner', 'manager'].includes(userRole.value))
const isCustomerRole = computed(() => userRole.value === 'customer')
const isDistributorRole = computed(() => ['distributor', 'manufacturer'].includes(userRole.value))

// Handle logout
const handleLogout = () => {
  emit('logout')
}
</script>

<style scoped>
.navbar-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1030;
}

.navbar {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--glass-border);
  box-shadow: var(--shadow-glass);
  padding: 0.8rem 0;
  transition: all 0.4s ease;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: var(--color-text-dark);
  font-weight: 800;
  font-size: 1.5rem;
  letter-spacing: -0.03em;
}

.brand-icon {
  width: 42px;
  height: 42px;
  background: var(--gradient-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.navbar-brand:hover .brand-icon {
  transform: rotate(15deg) scale(1.1);
}

.brand-text {
  background: linear-gradient(90deg, var(--color-text-dark), var(--color-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-link {
  color: var(--color-text-muted);
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: var(--radius-full);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  position: relative;
  margin: 0 0.2rem;
  font-size: 0.95rem;
}

.nav-link:hover,
.nav-link.router-link-exact-active {
  color: var(--color-primary);
  background: rgba(59, 130, 246, 0.08);
  transform: translateY(-1px);
}

.nav-link i {
  font-size: 1.1rem;
  transition: transform 0.3s ease;
}

.nav-link:hover i {
  transform: scale(1.1);
}

.dropdown-menu {
  border: none;
  box-shadow: var(--shadow-xl);
  border-radius: var(--radius-xl);
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--glass-border);
  animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: top center;
  margin-top: 10px;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.dropdown-header {
  color: var(--color-text-dark);
  font-weight: 700;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.5rem 1rem;
}

.dropdown-item {
  border-radius: var(--radius-lg);
  padding: 0.6rem 1rem;
  transition: all 0.2s ease;
  color: var(--color-text-muted);
  font-weight: 500;
}

.dropdown-item:hover {
  background: var(--gradient-primary);
  color: white;
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.btn-primary {
  background: var(--gradient-primary);
  border: none;
  color: white;
  font-weight: 600;
  padding: 0.6rem 1.8rem;
  border-radius: var(--radius-full);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
}

/* Mobile responsive */
@media (max-width: 991px) {
  .navbar-collapse {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(24px);
    padding: 1rem;
    border-radius: var(--radius-xl);
    margin-top: 1rem;
    box-shadow: var(--shadow-lg);
    border: 1px solid var(--glass-border);
  }
  
  .nav-link {
    border-radius: var(--radius-lg);
    margin: 0.2rem 0;
  }
}

.navbar-toggler {
  border: none;
  padding: 0.5rem;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.08);
  transition: all 0.3s ease;
}

.navbar-toggler:hover {
  background: rgba(59, 130, 246, 0.12);
}

.navbar-toggler:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.navbar-toggler-icon {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='%233B82F6' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
}
</style>

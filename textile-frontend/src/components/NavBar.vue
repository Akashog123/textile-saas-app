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
                  <router-link to="/customer" class="nav-link">
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
                    <i class="bi bi-chat-dots me-2"></i>Inquiries
                  </router-link>
                </li>
              </template>

              <!-- Distributor Navigation -->
              <template v-if="user.role === 'distributor' || user.role === 'manufacturer'">
                <li class="nav-item">
                  <router-link to="/distributor" class="nav-link">
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
  background: rgba(249, 245, 246, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(242, 190, 209, 0.2);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 1rem 0;
  transition: all 0.3s ease;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: var(--color-text-dark);
  font-weight: 700;
  font-size: 1.25rem;
  letter-spacing: -0.5px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  background: var(--color-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
}

.brand-text {
  color: var(--color-text-dark);
}

.nav-link {
  color: var(--color-text-muted);
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  text-decoration: none;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--color-text-dark);
  background: rgba(242, 190, 209, 0.15);
}

.nav-link i {
  font-size: 1.1rem;
}

.dropdown-menu {
  border: none;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.dropdown-header {
  color: var(--color-text-dark);
  font-weight: 600;
  font-size: 0.875rem;
}

.dropdown-item {
  border-radius: 8px;
  padding: 0.5rem 1rem;
  transition: all 0.3s ease;
  color: var(--color-text-muted);
}

.dropdown-item:hover {
  background: rgba(242, 190, 209, 0.15);
  color: var(--color-text-dark);
}

.btn-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  font-weight: 600;
  padding: 0.6rem 1.5rem;
  border-radius: 50px;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(242, 190, 209, 0.4);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .navbar {
    padding: 0.75rem 0;
  }
  
  .navbar-brand {
    font-size: 1.1rem;
  }
  
  .brand-icon {
    width: 35px;
    height: 35px;
    font-size: 1.1rem;
  }
  
  .nav-link {
    padding: 0.4rem 0.8rem;
    font-size: 0.9rem;
  }
}

.navbar-toggler {
  border-color: var(--color-primary);
}

.navbar-toggler-icon {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'%3e%3cpath stroke='%23F2BED1' stroke-linecap='round' stroke-miterlimit='10' stroke-width='2' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
}
</style>

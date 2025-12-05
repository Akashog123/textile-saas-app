<template>
  <div class="navbar-wrapper">
    <nav class="navbar navbar-expand fixed-top" :class="{ 'scrolled': isScrolled }">
      <div class="container-fluid">
        <!-- Brand Logo -->
        <router-link to="/" class="navbar-brand">
          <div class="brand-icon-wrapper">
            <div class="brand-icon">
              <i class="bi bi-flower1"></i>
            </div>
          </div>
          <span class="brand-text">Textile Saas app</span>
        </router-link>

        <!-- Mobile Toggle Button -->
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNav"
          aria-controls="mainNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <div class="hamburger-icon">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </button>

        <!-- Navigation Content -->
        <div class="collapse navbar-collapse" id="mainNav">
          <ul class="navbar-nav ms-auto align-items-center">
            <!-- Navigation links for authenticated users -->
            <template v-if="isAuthenticated && user">
              <!-- Customer Navigation -->
              <template v-if="user.role === 'customer'">
                <li class="nav-item">
                  <router-link to="/customer" class="nav-link" exact-active-class="router-link-exact-active">
                    <span class="nav-icon"><i class="bi bi-house-door"></i></span>
                    <span class="nav-text">Home</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/customer/products" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-grid"></i></span>
                    <span class="nav-text">Products</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/customer/shops" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-shop"></i></span>
                    <span class="nav-text">Shops</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/customer/profile" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-person"></i></span>
                    <span class="nav-text">Profile</span>
                  </router-link>
                </li>
              </template>

              <!-- Shop Owner Navigation -->
              <template v-if="user.role === 'shop_owner' || user.role === 'manager'">
                <li class="nav-item">
                  <router-link to="/shop/dashboard" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-speedometer2"></i></span>
                    <span class="nav-text">Dashboard</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/inventory" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-box-seam"></i></span>
                    <span class="nav-text">Inventory</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/marketing" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-megaphone"></i></span>
                    <span class="nav-text">Marketing</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/shop/inquiry" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-chat-dots"></i></span>
                    <span class="nav-text">Inquiry</span>
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
                  <router-link to="/distributor" class="nav-link" exact-active-class="router-link-exact-active">
                    <span class="nav-icon"><i class="bi bi-house-door"></i></span>
                    <span class="nav-text">Home</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/distributor/planning" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-graph-up"></i></span>
                    <span class="nav-text">Planning</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/distributor/regional-demand" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-geo-alt"></i></span>
                    <span class="nav-text">Regional Demand</span>
                  </router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/distributor/inquiries" class="nav-link">
                    <span class="nav-icon"><i class="bi bi-chat-dots"></i></span>
                    <span class="nav-text">Inquiries</span>
                  </router-link>
                </li>
              </template>
            </template>

            <!-- User Menu -->
            <li class="nav-item dropdown ms-lg-3" v-if="isAuthenticated && user">
              <a 
                class="nav-link dropdown-toggle user-profile-link" 
                href="#" 
                role="button" 
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                <div class="user-avatar">
                  <i class="bi bi-person-fill"></i>
                </div>
                <span class="user-name">{{ user.username || user.email }}</span>
              </a>
              <ul class="dropdown-menu dropdown-menu-end animate slideIn">
                <li><h6 class="dropdown-header">Signed in as <br><strong>{{ user.username || user.email }}</strong></h6></li>
                <li><hr class="dropdown-divider"></li>
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="$emit('logout')">
                    <i class="bi bi-box-arrow-right me-2"></i>Logout
                  </a>
                </li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'

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

// State for scroll effect
const isScrolled = ref(false)

const handleScroll = () => {
  isScrolled.value = window.scrollY > 20
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Computed properties
const userRole = computed(() => props.user?.role || '')
</script>

<style scoped>
.navbar-wrapper {
  position: relative;
  height: 8px; /* Prevent layout shift */
}

.navbar {
  padding: 1rem 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid transparent;
}

.navbar.scrolled {
  padding: 0.6rem 0;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

/* Brand Styling */
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-weight: 700;
  font-size: 1.35rem;
  color: var(--color-text-dark);
  transition: transform 0.3s ease;
}

.brand-icon-wrapper {
  position: relative;
}

.brand-icon {
  width: 40px;
  height: 40px;
  background: var(--gradient-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.25);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.navbar-brand:hover .brand-icon {
  transform: rotate(15deg) scale(1.1);
  box-shadow: 0 12px 25px rgba(59, 130, 246, 0.35);
}

.brand-text {
  background: linear-gradient(135deg, var(--color-text-dark) 0%, var(--color-primary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

/* Navigation Links */
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  margin: 0 0.2rem;
  color: var(--color-text-muted);
  font-weight: 500;
  border-radius: 12px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.nav-icon {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  transition: transform 0.3s ease;
}

.nav-link:hover .nav-icon,
.nav-link.router-link-exact-active .nav-icon {
  transform: translateY(-2px);
}

.nav-link:hover,
.nav-link.router-link-exact-active {
  color: var(--color-primary);
  background: rgba(59, 130, 246, 0.06);
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--color-primary);
  transition: all 0.3s ease;
  transform: translateX(-50%);
  opacity: 0;
}

.nav-link.router-link-exact-active::after {
  width: 40%;
  opacity: 1;
  bottom: 6px;
}

/* User Profile Link */
.user-profile-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0.8rem;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 50px;
  transition: all 0.3s ease;
}

.user-profile-link:hover {
  background: white;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border-color: transparent;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: var(--color-bg-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
}

/* Dropdown Menu */
.dropdown-menu {
  border: none;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  padding: 0.5rem;
  margin-top: 1rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  min-width: 220px;
}

.dropdown-item {
  border-radius: 10px;
  padding: 0.7rem 1rem;
  font-weight: 500;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: var(--color-bg-light);
  color: var(--color-primary);
  transform: translateX(4px);
}

.dropdown-header {
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.dropdown-divider {
  margin: 0.5rem 0;
  border-color: rgba(0,0,0,0.05);
}

/* Buttons */
/* Mobile Toggler */
.navbar-toggler {
  border: none;
  padding: 0;
  width: 40px;
  height: 40px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.navbar-toggler:focus {
  box-shadow: none;
}

.hamburger-icon {
  width: 24px;
  height: 20px;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.hamburger-icon span {
  display: block;
  width: 100%;
  height: 2px;
  background-color: var(--color-text-dark);
  border-radius: 2px;
  transition: all 0.3s ease;
}

.navbar-toggler[aria-expanded="true"] .hamburger-icon span:nth-child(1) {
  transform: translateY(9px) rotate(45deg);
}

.navbar-toggler[aria-expanded="true"] .hamburger-icon span:nth-child(2) {
  opacity: 0;
}

.navbar-toggler[aria-expanded="true"] .hamburger-icon span:nth-child(3) {
  transform: translateY(-9px) rotate(-45deg);
}

/* Animations */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate.slideIn {
  animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Responsive Adjustments */
@media (max-width: 991px) {
  .navbar-collapse {
    background: white;
    padding: 1.5rem;
    border-radius: 20px;
    margin-top: 1rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    max-height: 80vh;
    overflow-y: auto;
  }

  .nav-link {
    padding: 0.8rem 1rem;
    margin: 0.2rem 0;
    border-radius: 12px;
  }

  .nav-link:hover {
    background: var(--color-bg-light);
  }

  .user-profile-link {
    margin-top: 1rem;
    border: none;
    background: var(--color-bg-light);
    justify-content: center;
  }

  .dropdown-menu {
    box-shadow: none;
    border: 1px solid rgba(0,0,0,0.05);
    background: transparent;
    margin-top: 0.5rem;
  }
}
</style>

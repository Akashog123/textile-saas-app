<template>
  <div class="navbar-wrapper">
    <nav
      class="navbar navbar-expand-lg navbar-light bg-gradient-primary shadow-elegant"
    >
      <div class="container-fluid px-4">
        <div class="navbar-brand fw-bold brand-logo" to="/">
          <i class="bi bi-scissors brand-icon"></i>
          <span class="brand-text">SE Textile</span>
        </div>

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
          <!-- Right: user & logout -->
          <div
            class="d-flex align-items-center gap-3 ms-auto"
            v-if="isLoggedIn"
          >
            <div class="user-profile-badge">
              <i class="bi bi-person-circle user-avatar"></i>
              <span class="username-text">{{ username }}</span>
            </div>
            <button class="btn btn-logout btn-sm" @click="logout">
              <i class="bi bi-box-arrow-right logout-icon"></i>
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Shop Manager Sub-Navigation (visible only for shop_owner role) -->
    <div
      v-if="isLoggedIn && isShopRole"
      class="sub-nav-container bg-gradient-light"
    >
      <div class="container-fluid px-4">
        <ul class="nav nav-tabs-modern border-0 pt-2">
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{
                active:
                  $route.path.includes('/shop/dashboard') ||
                  $route.path === '/shop',
              }"
              to="/shop/dashboard"
            >
              <i class="bi bi-speedometer2 nav-icon"></i>
              <span class="nav-text">Dashboard</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/shop/inventory') }"
              to="/shop/inventory"
            >
              <i class="bi bi-box-seam nav-icon"></i>
              <span class="nav-text">Sales Inventory</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/shop/marketing') }"
              to="/shop/marketing"
            >
              <i class="bi bi-megaphone nav-icon"></i>
              <span class="nav-text">Marketing Content</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/shop/inquiry') }"
              to="/shop/inquiry"
            >
              <i class="bi bi-search nav-icon"></i>
              <span class="nav-text">Fabric Inquiry</span>
            </router-link>
          </li>
        </ul>
      </div>
    </div>

    <!-- Customer Sub-Navigation (visible only for customer role) -->
    <div
      v-if="isLoggedIn && isCustomerRole"
      class="sub-nav-container bg-gradient-light"
    >
      <div class="container-fluid px-4">
        <ul class="nav nav-tabs-modern border-0 pt-2">
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{
                active:
                  $route.path.includes('/customer/home') ||
                  $route.path === '/customer',
              }"
              to="/customer/home"
            >
              <i class="bi bi-house nav-icon"></i>
              <span class="nav-text">Home</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/customer/shops') }"
              to="/customer/shops"
            >
              <i class="bi bi-shop nav-icon"></i>
              <span class="nav-text">Shops</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/customer/products') }"
              to="/customer/products"
            >
              <i class="bi bi-bag nav-icon"></i>
              <span class="nav-text">Products</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/customer/profile') }"
              to="/customer/profile"
            >
              <i class="bi bi-person nav-icon"></i>
              <span class="nav-text">Profile</span>
            </router-link>
          </li>
        </ul>
      </div>
    </div>

    <!-- Distributor/Manufacturer Sub-Navigation (visible only for distributor/manufacturer role) -->
    <div
      v-if="isLoggedIn && isDistributorRole"
      class="sub-nav-container bg-gradient-light"
    >
      <div class="container-fluid px-4">
        <ul class="nav nav-tabs-modern border-0 pt-2">
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{
                active:
                  $route.path.includes('/distributor/demand') ||
                  $route.path === '/distributor',
              }"
              to="/distributor/demand"
            >
              <i class="bi bi-graph-up-arrow nav-icon"></i>
              <span class="nav-text">Regional Demand</span>
            </router-link>
          </li>
          <li class="nav-item">
            <router-link
              class="nav-link-modern"
              :class="{ active: $route.path.includes('/distributor/planning') }"
              to="/distributor/planning"
            >
              <i class="bi bi-calendar-check nav-icon"></i>
              <span class="nav-text">Production Planning</span>
            </router-link>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import api from "@/api/axios";

// ---- state
const router = useRouter();
const route = useRoute();
const isLoggedIn = ref(false);
const username = ref("");
const role = ref("");

// Check if current user is shop role (for showing sub-navigation)
const isShopRole = computed(() => {
  return role.value === "shop_owner" || role.value === "manager";
});

// Check if current user is customer role (for showing sub-navigation)
const isCustomerRole = computed(() => {
  return role.value === "customer";
});

// Check if current user is distributor/manufacturer role (for showing sub-navigation)
const isDistributorRole = computed(() => {
  return role.value === "distributor" || role.value === "manufacturer";
});

const hydrateFromStorage = async () => {
  const token = localStorage.getItem("token");
  const storedRole = localStorage.getItem("role");
  const storedName = localStorage.getItem("username");

  console.log("Hydrating NavBar:", { token, storedRole, storedName });

  if (!token || !storedRole) {
    isLoggedIn.value = false;
    return;
  }

  // For mock login (no backend), just trust localStorage
  // If backend is available, verify token
  try {
    // Skip backend verification if using mock login (token starts with MOCK-TOKEN-)
    if (token.startsWith("MOCK-TOKEN-")) {
      isLoggedIn.value = true;
      username.value = storedName || "";
      role.value = storedRole;
      console.log("Mock login detected, NavBar hydrated:", {
        isLoggedIn: isLoggedIn.value,
        role: role.value,
      });
      return;
    }

    // Only verify with backend if not using mock login
    await api.post("/verify_token", { token });
    isLoggedIn.value = true;
    username.value = storedName || "";
    role.value = storedRole;
  } catch (error) {
    // If backend is not available or token is invalid, clear session
    console.warn("Token verification failed:", error.message);
    localStorage.clear();
    isLoggedIn.value = false;
    role.value = "";
    username.value = "";
  }
};

onMounted(() => {
  hydrateFromStorage();

  // Listen for storage events (e.g., when another tab logs in)
  window.addEventListener("storage", hydrateFromStorage);

  // Listen for custom login event
  window.addEventListener("user-logged-in", hydrateFromStorage);
});

onUnmounted(() => {
  // Cleanup event listeners
  window.removeEventListener("storage", hydrateFromStorage);
  window.removeEventListener("user-logged-in", hydrateFromStorage);
});

// Watch for route changes and re-hydrate (important for login redirects)
watch(
  () => route.path,
  () => {
    hydrateFromStorage();
  },
  { immediate: true },
);

// ---- logout
const logout = async () => {
  const token = localStorage.getItem("token");

  // Only call backend logout if not using mock login
  if (token && !token.startsWith("MOCK-TOKEN-")) {
    try {
      await api.post("/logout", { token });
    } catch (e) {
      console.warn("Logout API call failed:", e.message);
    }
  }

  localStorage.clear();
  isLoggedIn.value = false;
  role.value = "";
  username.value = "";
  router.push("/login");
};
</script>

<style scoped>
/* Main Navbar Gradient */
.bg-gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.navbar-wrapper {
  position: sticky;
  top: 0;
  z-index: 1030;
}

.shadow-elegant {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* Brand Styling */
.brand-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: white !important;
  font-size: 1.5rem;
  transition: transform 0.3s ease;
}

.brand-logo:hover {
  transform: scale(1.05);
}

.brand-icon {
  font-size: 1.8rem;
}

@keyframes rotate {
  0%,
  100% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(10deg);
  }
}

.brand-text {
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* User Profile Badge */
.user-profile-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 50px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.user-avatar {
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
}

.username-text {
  color: white;
  font-weight: 500;
  font-size: 0.95rem;
}

/* Logout Button */
.btn-logout {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea;
  font-weight: 600;
  padding: 0.5rem 1.25rem;
  border-radius: 50px;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-logout:hover {
  background: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.logout-icon {
  font-size: 1.1rem;
}

/* Sub Navigation */
.sub-nav-container {
  background: linear-gradient(to bottom, #f8f9fa, #ffffff);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.bg-gradient-light {
  background: linear-gradient(to right, #fdfbfb 0%, #ebedee 100%);
}

.nav-tabs-modern {
  display: flex;
  gap: 0.5rem;
  padding-bottom: 0;
}

.nav-link-modern {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  color: #6c757d;
  font-weight: 500;
  border-radius: 12px 12px 0 0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  text-decoration: none;
}

.nav-link-modern::before {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transform: translateX(-50%);
  transition: width 0.3s ease;
}

.nav-link-modern:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.nav-link-modern:hover::before {
  width: 80%;
}

.nav-link-modern.active {
  color: #667eea;
  background: white;
  font-weight: 600;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.08);
}

.nav-link-modern.active::before {
  width: 100%;
}

.nav-icon {
  font-size: 1.2rem;
  display: inline-block;
}

.nav-text {
  font-size: 0.95rem;
}

/* Main Navbar Links */
.navbar-nav .nav-link {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.navbar-nav .nav-link::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: white;
  transform: translateX(-50%);
  transition: width 0.3s ease;
}

.navbar-nav .nav-link:hover {
  color: white !important;
}

.navbar-nav .nav-link:hover::after {
  width: 80%;
}

/* Responsive Design */
@media (max-width: 991px) {
  .user-profile-badge {
    margin-top: 1rem;
  }

  .btn-logout {
    width: 100%;
    justify-content: center;
    margin-top: 0.5rem;
  }

  .nav-tabs-modern {
    flex-direction: column;
    gap: 0.25rem;
  }

  .nav-link-modern {
    border-radius: 8px;
  }
}

/* Smooth Transitions */
* {
  transition:
    color 0.2s ease,
    background-color 0.2s ease;
}
</style>

import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import ShopOwner from "../views/ShopOwner.vue";
import CustomerHome from "../views/CustomerHome.vue";
import DistributorHome from "../views/Distributor.vue";
import ShopDashboard from "../views/shop/ShopDashboard.vue";
import ShopInventory from "../views/shop/ShopInventory.vue";
import ShopMarketing from "../views/shop/ShopMarketing.vue";
import ShopProfile from "@/views/shop/ShopProfile.vue";
import ShopInquiry from "../views/shop/ShopInquiry.vue";
import LandingPage from "../views/LandingPage.vue";

const routes = [
  {
    path: "/",
    name: "LandingPage",
    component: LandingPage,
    meta: {
      title: "SE Textile App - Smart Supply Chain",
      requiresAuth: false
    }
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: {
      title: "Login - SE Textile App",
      requiresAuth: false
    }
  },
  {
    path: "/shop",
    component: ShopOwner,
    meta: {
      requiresAuth: true,
      roles: ["shop_owner", "manager"],
      title: "Shop Manager Portal"
    },
    children: [
      {
        path: "",
        name: "ShopDashboard",
        component: ShopDashboard,
        meta: { title: "Dashboard - Shop Manager" }
      },
      {
        path: "dashboard",
        name: "ShopDashboardExplicit",
        component: ShopDashboard,
        meta: { title: "Dashboard - Shop Manager" }
      },
      {
        path: "inventory",
        name: "ShopInventory",
        component: ShopInventory,
        meta: { title: "Inventory - Shop Manager" }
      },
      {
        path: "marketing",
        name: "ShopMarketing",
        component: ShopMarketing,
        meta: { title: "Marketing - Shop Manager" }
      },
      {
        path: "inquiry",
        name: "ShopInquiry",
        component: ShopInquiry,
        meta: { title: "Inquiry - Shop Manager" }
      },
      {
        path: "profile",
        name: "ShopProfile",
        component: ShopProfile,
        meta: { title: "Profile - Shop Manager" }
      },
    ],
  },
  {
    path: "/customer",
    component: CustomerHome,
    meta: {
      requiresAuth: true,
      roles: ["customer"],
      title: "Customer Portal"
    },
    children: [
      {
        path: "",
        name: "CustomerHomePage",
        component: () => import("@/views/customer/CustomerHomePage.vue"),
        meta: { title: "Home - Customer Portal" }
      },
      {
        path: "products",
        name: "CustomerProducts",
        component: () => import("@/views/customer/CustomerProducts.vue"),
        meta: { title: "Products - Customer Portal" }
      },
      {
        path: "shops",
        name: "CustomerShops",
        component: () => import("@/views/customer/CustomerShops.vue"),
        meta: { title: "Shops - Customer Portal" }
      },
      {
        path: "shops/:shopId",
        name: "CustomerShopDetail",
        component: () => import("@/views/customer/CustomerShopDetail.vue"),
        meta: { title: "Shop Details - Customer Portal" },
        props: true
      },
      {
        path: "products/:productId",
        name: "CustomerProductDetail",
        component: () => import("@/views/customer/CustomerProductDetail.vue"),
        meta: { title: "Product Details - Customer Portal" },
        props: true
      },
      {
        path: "profile",
        name: "CustomerProfile",
        component: () => import("@/views/customer/CustomerProfile.vue"),
        meta: { title: "Profile - Customer Portal" }
      },
    ],
  },
  {
    path: "/distributor",
    component: DistributorHome,
    meta: {
      requiresAuth: true,
      roles: ["distributor", "manufacturer"],
      title: "Distributor Portal"
    },
    children: [
      {
        path: "",
        name: "DistributorHomePage",
        component: () => import("@/views/distributor/DistributorHomePage.vue"),
        meta: { title: "Home - Distributor Portal" }
      },
      {
        path: "planning",
        name: "ProductionPlanningDistributor",
        component: () => import("@/views/distributor/ProductionPlanning.vue"),
        meta: { title: "Production Planning - Distributor" }
      },
      {
        path: "regional-demand",
        name: "RegionalDemandDistributor",
        component: () => import("@/views/distributor/RegionalDemand.vue"),
        meta: { title: "Regional Demand - Distributor" }
      },
      {
        path: "inquiries",
        name: "DistributorInquiries",
        component: () => import("@/views/distributor/DistributorInquiries.vue"),
        meta: { title: "Shop Inquiries - Distributor" }
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
    meta: {
      title: "Page Not Found",
      requiresAuth: false
    }
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Restore scroll position when using browser back/forward
    if (savedPosition) {
      return savedPosition;
    }
    // Scroll to top for new routes
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' };
    }
    return { top: 0, behavior: 'smooth' };
  },
});

// Global error handler for navigation failures
router.onError((error) => {
  console.error('[Router Error]', error);
  // Could add error tracking here (e.g., Sentry)
});

// Navigation Guard for Authentication and Authorization
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("role");

  // Set document title
  document.title = to.meta.title || "SE Textile App";

  // Check if route requires authentication
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

  if (requiresAuth) {
    if (!token) {
      // Not authenticated, redirect to login
      console.warn('[Auth] No token found, redirecting to login');
      next({
        path: "/login",
        query: { redirect: to.fullPath }
      });
      return;
    }

    // Check if user role is allowed for this route
    const allowedRoles = to.matched
      .filter(record => record.meta.roles)
      .flatMap(record => record.meta.roles);

    if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
      // Role not authorized, redirect to login with error
      console.warn('[Auth] Unauthorized role:', userRole, 'allowed:', allowedRoles);
      localStorage.clear(); // Clear invalid session
      next({
        path: "/login",
        query: { error: "unauthorized" }
      });
      return;
    }
  }

  // If already on login page and authenticated, redirect to appropriate dashboard
  if (to.path === "/login" && token && userRole) {
    const roleRoutes = {
      customer: "/customer",
      manufacturer: "/distributor",
      shop_owner: "/shop",
      manager: "/shop",
      distributor: "/distributor",
    };
    const targetRoute = roleRoutes[userRole];
    if (targetRoute && from.path !== targetRoute) {
      console.log('[Auth] Already authenticated, redirecting to:', targetRoute);
      next(targetRoute);
      return;
    }
  }

  next();
});

// After each navigation
router.afterEach((to, from) => {
  // Could add analytics tracking here
  // Example: trackPageView(to.path);
});

export default router;

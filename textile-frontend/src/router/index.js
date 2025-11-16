import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import ShopOwner from "../views/ShopOwner.vue";
import CustomerHome from "../views/CustomerHome.vue";
import DistributorHome from "../views/Distributor.vue";
import ShopDashboard from "../views/shop/ShopDashboard.vue";
import ShopInventory from "../views/shop/ShopInventory.vue";
import ShopMarketing from "../views/shop/ShopMarketing.vue";
import ShopInquiry from "../views/shop/ShopInquiry.vue";

const routes = [
  { path: "/login", name: "Login", component: Login },
  { path: "/", redirect: "/login" },
  {
    path: "/shop",
    component: ShopOwner,
    children: [
      { path: "", name: "ShopDashboard", component: ShopDashboard },
      { path: "dashboard", name: "ShopDashboardExplicit", component: ShopDashboard },
      { path: "inventory", name: "ShopInventory", component: ShopInventory },
      { path: "marketing", name: "ShopMarketing", component: ShopMarketing },
      { path: "inquiry", name: "ShopInquiry", component: ShopInquiry },
    ],
  },
  {
    path: "/customer",
    component: CustomerHome,
    children: [
      { path: "", name: "CustomerHomePage", component: () => import("@/views/customer/CustomerHomePage.vue") },
      { path: "products", name: "CustomerProducts", component: () => import("@/views/customer/CustomerProducts.vue") },
      { path: "shops", name: "CustomerShops", component: () => import("@/views/customer/CustomerShops.vue") },
      { path: "profile", name: "CustomerProfile", component: () => import("@/views/customer/CustomerProfile.vue") },
    ],
  },
  {
    path: "/distributor",
    component: DistributorHome,
    children: [
      {
        path: "",
        alias: "planning",
        name: "ProductionPlanningDistributor",
        component: () => import("@/views/distributor/ProductionPlanning.vue"),
      },
      {
        path: "regional-demand",
        alias: "demand",
        name: "RegionalDemandDistributor",
        component: () => import("@/views/distributor/RegionalDemand.vue"),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

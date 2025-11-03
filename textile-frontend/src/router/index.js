import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import ShopOwner from '../views/ShopOwner.vue'
import ShopDashboard from '../views/shop/ShopDashboard.vue'
import ShopInventory from '../views/shop/ShopInventory.vue'
import ShopMarketing from '../views/shop/ShopMarketing.vue'
import ShopInquiry from '../views/shop/ShopInquiry.vue'
import Distributor from '../views/Distributor.vue'
import RegionalDemand from '../views/distributor/RegionalDemand.vue'
import ProductionPlanning from '../views/distributor/ProductionPlanning.vue'
import CustomerHome from '../views/CustomerHome.vue'
import CustomerHomePage from '../views/customer/CustomerHomePage.vue'
import CustomerShops from '../views/customer/CustomerShops.vue'
import CustomerProducts from '../views/customer/CustomerProducts.vue'
import CustomerProfile from '../views/customer/CustomerProfile.vue'
// We use the Distributor view for both distributor and manufacturer roles so there is a single dashboard

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    {
        path:'/',
        redirect:'/login'
    },
    {
        path: '/shop',
        name: 'ShopOwner',
        component: ShopOwner,
        redirect: '/shop/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'ShopDashboard',
                component: ShopDashboard
            },
            {
                path: 'inventory',
                name: 'ShopInventory',
                component: ShopInventory
            },
            {
                path: 'marketing',
                name: 'ShopMarketing',
                component: ShopMarketing
            },
            {
                path: 'inquiry',
                name: 'ShopInquiry',
                component: ShopInquiry
            }
        ]
    },
    {
        path: '/distributor',
        name: 'Distributor',
        component: Distributor,
        redirect: '/distributor/demand',
        children: [
            {
                path: 'demand',
                name: 'RegionalDemand',
                component: RegionalDemand
            },
            {
                path: 'planning',
                name: 'ProductionPlanning',
                component: ProductionPlanning
            }
        ]
    },
    {
        path: '/customer',
        name: 'Customer',
        component: CustomerHome,
        redirect: '/customer/home',
        children: [
            {
                path: 'home',
                name: 'CustomerHomePage',
                component: CustomerHomePage
            },
            {
                path: 'shops',
                name: 'CustomerShops',
                component: CustomerShops
            },
            {
                path: 'products',
                name: 'CustomerProducts',
                component: CustomerProducts
            },
            {
                path: 'profile',
                name: 'CustomerProfile',
                component: CustomerProfile
            }
        ]
    },
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
})

export default router

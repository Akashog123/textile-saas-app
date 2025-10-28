import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import ShopOwner from '../views/ShopOwner.vue'
import CustomerHome from '../views/CustomerHome.vue'
import ManufacturerHome from '../views/ManufacturerHome.vue'

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
        component: ShopOwner
    },
    {
        path: '/customer',
        name: 'Customer',
        component: CustomerHome
    },
    {
        path: '/manufacturer',
        name: 'Manufacturer',
        component: ManufacturerHome
    },
]

const router = createRouter({
    history: createWebHistory(import.meta.url),
    routes
})

export default router

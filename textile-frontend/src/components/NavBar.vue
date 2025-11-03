<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
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
        <!-- Center: role-based links -->
        <ul class="navbar-nav me-auto mb-2 mb-lg-0" v-if="isLoggedIn">
          <li class="nav-item" v-for="item in navItems" :key="item.to">
            <router-link class="nav-link" :to="item.to">{{ item.label }}</router-link>
          </li>
        </ul>

        <!-- Right: user & logout -->
        <div class="d-flex align-items-center gap-3" v-if="isLoggedIn">
          <span class="text-white-50">{{ username }}</span>
          <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
        </div>
      </div>

    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/axios'

// ---- state
const router = useRouter()
const isLoggedIn = ref(false)
const username = ref('')
const role = ref('')

// ---- role → links (edit paths to match your routes)
const ROLE_NAV = {
  customer:      [{ to: '/customer',     label: 'Customer Dashboard' }],
  distributor:   [{ to: '/distributor',  label: 'Distributor Dashboard' }],
  manufacturer:  [{ to: '/manufacturer', label: 'Manufacturer Dashboard' }],
  manager:       [{ to: '/shop',         label: 'Manager Dashboard' }],
  shop_owner:    [{ to: '/shop',         label: 'Shop Owner Dashboard' }],
}

const navItems = computed(() => ROLE_NAV[role.value] ?? [])


const hydrateFromStorage = async () => {
  const token = localStorage.getItem('token')
  const storedRole = localStorage.getItem('role')
  const storedName = localStorage.getItem('username')

  if (!token || !storedRole) {
    isLoggedIn.value = false
    return
  }

  try {

    await api.post('/verify_token', { token })
    isLoggedIn.value = true
    username.value = storedName || ''
    role.value = storedRole
  } catch {
    localStorage.clear()
    isLoggedIn.value = false
    role.value = ''
    username.value = ''
  }
}

onMounted(hydrateFromStorage)

// ---- logout
const logout = async () => {
  try {
    await api.post('/logout', { token: localStorage.getItem('token') })
  } catch (e) {
  
  }
  localStorage.clear()
  isLoggedIn.value = false
  role.value = ''
  username.value = ''
  router.push('/login')
}
</script>

<style scoped>

.navbar-brand { font-weight: 700; letter-spacing: .5px; }
</style>

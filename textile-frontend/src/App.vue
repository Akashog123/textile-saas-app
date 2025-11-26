<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from "@/components/NavBar.vue"
import { getCurrentSession, logout } from '@/api/apiAuth'

// Authentication state
const user = ref(null)
const isAuthenticated = computed(() => !!user.value)
const router = useRouter()

// Check authentication on mount
const checkAuth = async () => {
  try {
    const token = localStorage.getItem('token')
    if (token) {
      const response = await getCurrentSession()
      if (response.data.status === 'success') {
        user.value = response.data.user
      } else {
        // Invalid session, clear token
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        user.value = null
      }
    }
  } catch (error) {
    console.error('Auth check failed:', error)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    user.value = null
  }
}

// Handle logout
const handleLogout = async () => {
  try {
    await logout()
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('user')
    user.value = null
    router.push('/login')
  }
}

// Provide auth state to child components
const provideAuth = () => {
  return {
    user,
    isAuthenticated,
    handleLogout,
    checkAuth
  }
}

onMounted(() => {
  checkAuth()
})
</script>

<template>
  <div id="app" class="textile-app">
    <NavBar 
      :user="user" 
      :isAuthenticated="isAuthenticated"
      @logout="handleLogout"
      @refresh-auth="checkAuth"
    />
    <main class="main-content">
      <router-view :key="$route.fullPath" />
    </main>
  </div>
</template>

<style>
/* Global styles matching LandingPage theme */
.textile-app {
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.main-content {
  padding-top: 80px; /* Account for fixed navbar */
}

/* Theme variables */
:root {
  /* Landing Page Theme Palette */
  --color-bg: #F9F5F6;
  --color-bg-alt: #F8E8EE;
  --color-accent: #FDCEDF;
  --color-primary: #F2BED1;
  --color-primary-dark: #e0a3b8;
  --color-text-dark: #4A4A4A;
  --color-text-muted: #6c757d;
  
  /* Mapping to generic names for compatibility */
  --primary-color: var(--color-primary);
  --primary-dark: var(--color-primary-dark);
  --accent-color: var(--color-accent);
  --text-muted: var(--color-text-muted);
  --bg-light: var(--color-bg);
  --bg-white: #ffffff;
  
  --border-color: #e5e7eb;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

/* Common utility classes */
.text-highlight {
  color: var(--accent-color);
}

.bg-accent {
  background-color: var(--accent-color);
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  border: none;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-outline-primary {
  border: 2px solid var(--primary-color);
  color: var(--primary-color);
  background: transparent;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-outline-primary:hover {
  background: var(--primary-color);
  color: white;
  transform: translateY(-2px);
}

/* Card styles */
.card {
  border: none;
  border-radius: 1rem;
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

/* Feature card styles */
.feature-card {
  padding: 2rem;
  text-align: center;
  height: 100%;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
}

.feature-card.highlight {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
}

.icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  font-size: 2rem;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  color: white;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 1.5rem 0 0 0;
}

.feature-list li {
  padding: 0.5rem 0;
  color: inherit;
}

.feature-list li i {
  color: var(--accent-color);
  margin-right: 0.5rem;
}

.feature-card.highlight .feature-list li i {
  color: white;
}

/* Smooth transitions */
* {
  transition: color 0.3s ease, background-color 0.3s ease;
}
</style>

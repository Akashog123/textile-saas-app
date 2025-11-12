<template>
  <div class="auth-container">
    <div class="auth-wrapper">
      <!-- Left Side - Branding -->
      <div class="auth-left">
        <div class="brand-section">
          <div class="brand-header">
            <div class="brand-icon">
              <svg class="icon-sparkle" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </div>
            <h1 class="brand-title">SE Textile App</h1>
          </div>
          <p class="brand-subtitle">Smart Textile Supply Chain Management</p>

          <div class="features-list">
            <div class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <span>Role-based Access Control</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <span>Real-time Inventory Tracking</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </div>
              <span>Supply Chain Analytics</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Side - Auth Forms -->
      <div class="auth-right">
        <div class="auth-card">
          <!-- Tab Navigation -->
          <div class="auth-tabs">
            <button
              :class="['tab-button', { active: activeTab === 'login' }]"
              @click="activeTab = 'login'"
            >
              Sign In
            </button>
            <button
              :class="['tab-button', { active: activeTab === 'register' }]"
              @click="activeTab = 'register'"
            >
              Create Account
            </button>
          </div>

          <!-- Login Form -->
          <div v-if="activeTab === 'login'" class="auth-form">
            <div class="form-header">
              <h2>Welcome Back</h2>
              <p>Sign in to your account</p>
            </div>

            <form @submit.prevent="handleLogin" class="form-content">
              <div class="form-group">
                <label for="loginName" class="form-label">Email or Username</label>
                <input
                  type="text"
                  class="form-control"
                  id="loginName"
                  v-model.trim="loginForm.username"
                  autocomplete="username"
                  required
                  placeholder="Enter your email or username"
                />
              </div>

              <div class="form-group">
                <label for="loginPassword" class="form-label">Password</label>
                <input
                  type="password"
                  class="form-control"
                  id="loginPassword"
                  v-model="loginForm.password"
                  autocomplete="current-password"
                  required
                  placeholder="Enter your password"
                />
              </div>

              <div class="form-options">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" id="rememberMe" v-model="loginForm.remember" />
                  <label class="form-check-label" for="rememberMe">Remember me</label>
                </div>
                <a href="#" class="forgot-link">Forgot password?</a>
              </div>

              <button type="submit" class="btn btn-primary w-100" :disabled="loadingLogin">
                <span v-if="!loadingLogin">Sign In</span>
                <span v-else class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                <span v-if="loadingLogin">Signing in...</span>
              </button>

              <div v-if="loginError" class="alert alert-danger mt-3">
                {{ loginError }}
              </div>
            </form>
          </div>

          <!-- Register Form -->
          <div v-if="activeTab === 'register'" class="auth-form">
            <div class="form-header">
              <h2>Join SE Textile</h2>
              <p>Create your account to get started</p>
            </div>

            <form @submit.prevent="handleRegister" class="form-content">
              <!-- Common Fields -->
              <div class="form-group">
                <label for="registerName" class="form-label">Full Name</label>
                <input
                  type="text"
                  id="registerName"
                  class="form-control"
                  v-model.trim="registerForm.name"
                  required
                  placeholder="Enter your full name"
                />
              </div>

              <div class="form-group">
                <label for="registerUsername" class="form-label">Username</label>
                <input
                  type="text"
                  id="registerUsername"
                  class="form-control"
                  v-model.trim="registerForm.username"
                  required
                  placeholder="Choose a username"
                />
              </div>

              <!-- Role Selection -->
              <div class="form-group">
                <label for="registerRole" class="form-label">Account Type</label>
                <select
                  id="registerRole"
                  class="form-select"
                  v-model="registerForm.role"
                  required
                >
                  <option disabled value="">Select your role</option>
                  <option value="customer">Customer</option>
                  <option value="manufacturer">Manufacturer</option>
                  <option value="shop_owner">Shop Owner / Manager</option>
                </select>
              </div>

              <!-- Role-specific fields -->
              <div v-if="registerForm.role === 'customer'" class="form-group">
                <label for="registerEmail" class="form-label">Email</label>
                <input
                  type="email"
                  id="registerEmail"
                  class="form-control"
                  v-model.trim="registerForm.email"
                  required
                  placeholder="Enter your email address"
                />
              </div>

              <!-- Shop Owner Fields -->
              <template v-if="registerForm.role === 'shop_owner'">
                <div class="form-group">
                  <label for="shopName" class="form-label">Shop Name</label>
                  <input
                    id="shopName"
                    class="form-control"
                    v-model.trim="registerForm.shop.name"
                    required
                    placeholder="Enter shop name"
                  />
                </div>
                <div class="form-group">
                  <label for="shopAddress" class="form-label">Shop Address</label>
                  <input
                    id="shopAddress"
                    class="form-control"
                    v-model.trim="registerForm.shop.address"
                    required
                    placeholder="Enter shop address"
                  />
                </div>
                <div class="form-group">
                  <label for="shopMobile" class="form-label">Mobile</label>
                  <input
                    id="shopMobile"
                    class="form-control"
                    v-model.trim="registerForm.shop.mobile"
                    required
                    placeholder="Enter mobile number"
                  />
                </div>
              </template>

              <!-- Manufacturer Fields -->
              <template v-if="registerForm.role === 'manufacturer'">
                <div class="form-group">
                  <label for="plantName" class="form-label">Plant Name</label>
                  <input
                    id="plantName"
                    class="form-control"
                    v-model.trim="registerForm.manufacturer.plantName"
                    required
                    placeholder="Enter plant name"
                  />
                </div>
                <div class="form-group">
                  <label for="plantAddress" class="form-label">Plant Address</label>
                  <input
                    id="plantAddress"
                    class="form-control"
                    v-model.trim="registerForm.manufacturer.address"
                    required
                    placeholder="Enter plant address"
                  />
                </div>
                <div class="form-group">
                  <label for="plantMobile" class="form-label">Mobile</label>
                  <input
                    id="plantMobile"
                    class="form-control"
                    v-model.trim="registerForm.manufacturer.mobile"
                    required
                    placeholder="Enter mobile number"
                  />
                </div>
              </template>

              <!-- Password Fields -->
              <div class="form-group">
                <label for="registerPassword" class="form-label">Password</label>
                <input
                  type="password"
                  id="registerPassword"
                  class="form-control"
                  v-model="registerForm.password"
                  minlength="8"
                  required
                  placeholder="Create a password"
                />
              </div>
              <div class="form-group">
                <label for="registerRepeatPassword" class="form-label">Confirm Password</label>
                <input
                  type="password"
                  id="registerRepeatPassword"
                  class="form-control"
                  v-model="registerForm.password2"
                  required
                  placeholder="Confirm your password"
                />
              </div>

              <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="terms" v-model="registerForm.terms" required />
                <label class="form-check-label" for="terms">I agree to the Terms and Conditions</label>
              </div>

              <button type="submit" class="btn btn-primary w-100" :disabled="loadingRegister">
                <span v-if="!loadingRegister">Create Account</span>
                <span v-else class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                <span v-if="loadingRegister">Creating account...</span>
              </button>

              <div v-if="registerError" class="alert alert-danger mt-3">
                {{ registerError }}
              </div>
              <div v-if="registerSuccess" class="alert alert-success mt-3">
                {{ registerSuccess }}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/axios'

const router = useRouter()
const activeTab = ref('login')

// LOGIN STATE
const loginForm = ref({
  username: '',
  password: '',
  remember: true,
})
const loadingLogin = ref(false)
const loginError = ref('')

// REGISTER STATE
const registerForm = ref({
  name: '',
  username: '',
  role: '',          // 'customer' | 'manufacturer' | 'shop_owner'
  email: '',         // customer-only
  shop: {            // shop_owner-only
    name: '',
    address: '',
    mobile: '',
  },
  manufacturer: {    // manufacturer-only
    plantName: '',
    address: '',
    mobile: '',
  },
  password: '',
  password2: '',
  terms: false,
})

const loadingRegister = ref(false)
const registerError = ref('')
const registerSuccess = ref('')

const MOCK_ACCOUNTS = {
  shopowner: { role: 'shop_owner', displayName: 'Shop Owner', password: 'shop', redirect: '/shop' },
  distributor: { role: 'distributor', displayName: 'Manufacturer/Distributor', password: 'dist', redirect: '/distributor' },
  customer: { role: 'customer', displayName: 'Customer', password: 'cust', redirect: '/customer' },
}

const handleLogin = async () => {
  loginError.value = ''
  loadingLogin.value = true

  // Check mock credentials
  try {
    const input = (loginForm.value.username || '').toString().trim().toLowerCase()
    const pwd = (loginForm.value.password || '').toString()

    if (input && MOCK_ACCOUNTS[input] && MOCK_ACCOUNTS[input].password === pwd) {
      const acc = MOCK_ACCOUNTS[input]
      // store minimal session data in localStorage so NavBar hydrates correctly
      localStorage.setItem('token', `MOCK-TOKEN-${acc.role}`)
      localStorage.setItem('role', acc.role)
      localStorage.setItem('username', acc.displayName)
      localStorage.setItem('user_id', `mock-${acc.role}`)

      // Dispatch custom event to notify NavBar
      window.dispatchEvent(new Event('user-logged-in'))

      router.push(acc.redirect)
      return
    }

    // Otherwise fall back to real API if available
    const { data } = await api.post('/login', {
      username: loginForm.value.username,
      password: loginForm.value.password,
    })

    const { token, role, username, user_id } = data

    localStorage.setItem('token', token)
    localStorage.setItem('role', role)
    localStorage.setItem('username', username)
    localStorage.setItem('user_id', user_id)

    // Dispatch custom event to notify NavBar
    window.dispatchEvent(new Event('user-logged-in'))

    // Navigate based on role
    const roleRoutes = {
      customer: '/customer',
      manufacturer: '/manufacturer',
      shop_owner: '/shop',
      manager: '/shop'
    }
    router.push(roleRoutes[role] || '/')
  } catch (err) {
    loginError.value = err?.response?.data?.message || 'Login failed. Please try again.'
  } finally {
    loadingLogin.value = false
  }
}

const handleRegister = async () => {
  registerError.value = ''
  registerSuccess.value = ''
  loadingRegister.value = true

  try {
    // basic validation
    if (!registerForm.value.role) {
      registerError.value = 'Please select an account type.'
      return
    }
    if (registerForm.value.password !== registerForm.value.password2) {
      registerError.value = 'Passwords do not match.'
      return
    }

    // build payload by role
    const base = {
      name: registerForm.value.name,
      username: registerForm.value.username,
      role: registerForm.value.role,
      password: registerForm.value.password,
    }

    let payload = { ...base }

    if (registerForm.value.role === 'customer') {
      payload.email = registerForm.value.email
    }

    if (registerForm.value.role === 'shop_owner') {
      payload.shop = {
        name: registerForm.value.shop.name,
        address: registerForm.value.shop.address,
        mobile: registerForm.value.shop.mobile,
      }
    }

    if (registerForm.value.role === 'manufacturer') {
      payload.manufacturer = {
        plant_name: registerForm.value.manufacturer.plantName,
        address: registerForm.value.manufacturer.address,
        mobile: registerForm.value.manufacturer.mobile,
      }
    }

    // POST to your backend
    await api.post('/register', payload)

    registerSuccess.value = 'Account created successfully! You can now log in.'
    activeTab.value = 'login'

    // clear the form
    Object.assign(registerForm.value, {
      name: '', username: '', role: '', email: '',
      shop: { name: '', address: '', mobile: '' },
      manufacturer: { plantName: '', address: '', mobile: '' },
      password: '', password2: '', terms: false,
    })
  } catch (err) {
    registerError.value = err?.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    loadingRegister.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.auth-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-height: 600px;
}

/* Left Side - Branding */
.auth-left {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.auth-left::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.3;
}

.brand-section {
  position: relative;
  z-index: 1;
}

.brand-header {
  text-align: center;
  margin-bottom: 2rem;
}

.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  margin-bottom: 1rem;
  backdrop-filter: blur(10px);
}

.icon-sparkle {
  width: 2rem;
  height: 2rem;
  color: white;
}

.brand-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(45deg, #ffffff, #e0e7ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0 0 2rem 0;
  font-weight: 300;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  flex-shrink: 0;
}

.feature-icon svg {
  width: 1.25rem;
  height: 1.25rem;
  color: white;
}

.feature-item span {
  font-size: 0.95rem;
  font-weight: 500;
}

/* Right Side - Auth Forms */
.auth-right {
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: white;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

/* Tab Navigation */
.auth-tabs {
  display: flex;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 2rem;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tab-button {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-weight: 600;
  color: #6c757d;
  transition: all 0.3s ease;
  cursor: pointer;
}

.tab-button.active {
  background: white;
  color: #0d6efd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Form Styles */
.auth-form {
  width: 100%;
}

.form-header {
  text-align: center;
  margin-bottom: 2rem;
}

.form-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 0.5rem 0;
}

.form-header p {
  color: #6c757d;
  margin: 0;
  font-size: 0.95rem;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  margin-bottom: 0;
}

.form-control {
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: #fafafa;
}

.form-control:focus {
  outline: none;
  border-color: #0d6efd;
  background: white;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
}

.form-control::placeholder {
  color: #9ca3af;
}

.form-select {
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: #fafafa;
}

.form-select:focus {
  outline: none;
  border-color: #0d6efd;
  background: white;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0.5rem 0;
}

.form-check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.form-check-input {
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 4px;
  border: 2px solid #d1d5db;
  background: white;
  cursor: pointer;
}

.form-check-input:checked {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.form-check-label {
  font-size: 0.875rem;
  color: #6b7280;
  cursor: pointer;
  margin: 0;
}

.forgot-link {
  color: #0d6efd;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.3s ease;
}

.forgot-link:hover {
  color: #0b5ed7;
  text-decoration: underline;
}

.btn-primary {
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  color: white;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #0b5ed7 0%, #0a58ca 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.alert {
  padding: 0.875rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-top: 1rem;
}

.alert-danger {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.alert-success {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
}

/* Responsive Design */
@media (max-width: 768px) {
  .auth-wrapper {
    grid-template-columns: 1fr;
    max-width: 100%;
    margin: 1rem;
    min-height: auto;
  }

  .auth-left {
    padding: 2rem 1.5rem;
    text-align: center;
  }

  .brand-title {
    font-size: 2rem;
  }

  .features-list {
    gap: 1rem;
  }

  .auth-right {
    padding: 2rem 1.5rem;
  }

  .auth-card {
    max-width: 100%;
  }

  .auth-tabs {
    margin-bottom: 1.5rem;
  }

  .tab-button {
    padding: 0.625rem 0.75rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .auth-container {
    padding: 1rem 0.5rem;
  }

  .auth-wrapper {
    margin: 0.5rem;
  }

  .auth-left,
  .auth-right {
    padding: 1.5rem 1rem;
  }

  .brand-title {
    font-size: 1.75rem;
  }

  .form-header h2 {
    font-size: 1.5rem;
  }

  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}

/* Loading spinner adjustments */
.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

/* Custom scrollbar for form content if needed */
.form-content::-webkit-scrollbar {
  width: 4px;
}

.form-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.form-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.form-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>

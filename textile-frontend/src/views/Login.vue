<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-12 col-md-8 col-lg-6">

        <!-- Pills navs -->
        <ul class="nav nav-pills nav-justified mb-4" id="authTabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button
              class="nav-link active"
              id="tab-login"
              data-bs-toggle="pill"
              data-bs-target="#pills-login"
              type="button"
              role="tab"
              aria-controls="pills-login"
              aria-selected="true"
            >
              Login
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button
              class="nav-link"
              id="tab-register"
              data-bs-toggle="pill"
              data-bs-target="#pills-register"
              type="button"
              role="tab"
              aria-controls="pills-register"
              aria-selected="false"
            >
              Register
            </button>
          </li>
        </ul>
        <!-- /Pills navs -->

        <!-- Pills content -->
        <div class="tab-content">
          <!-- LOGIN -->
          <div
            class="tab-pane fade show active"
            id="pills-login"
            role="tabpanel"
            aria-labelledby="tab-login"
            tabindex="0"
          >
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="loginName" class="form-label">Email or username</label>
                <input
                  type="text"
                  class="form-control"
                  id="loginName"
                  v-model.trim="loginForm.username"
                  autocomplete="username"
                  required
                />
              </div>

              <div class="mb-3">
                <label for="loginPassword" class="form-label">Password</label>
                <input
                  type="password"
                  class="form-control"
                  id="loginPassword"
                  v-model="loginForm.password"
                  autocomplete="current-password"
                  required
                />
              </div>

              <div class="row mb-3">
                <div class="col-md-6">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="rememberMe" v-model="loginForm.remember" />
                    <label class="form-check-label" for="rememberMe">Remember me</label>
                  </div>
                </div>
                <div class="col-md-6 text-md-end">
                  <a href="#">Forgot password?</a>
                </div>
              </div>

              <button type="submit" class="btn btn-primary w-100" :disabled="loadingLogin">
                <span v-if="!loadingLogin">Sign in</span>
                <span v-else class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              </button>

              <p v-if="loginError" class="text-danger text-center mt-3">{{ loginError }}</p>
            </form>
          </div>

            <!-- REGISTER -->
        <div
        class="tab-pane fade"
        id="pills-register"
        role="tabpanel"
        aria-labelledby="tab-register"
        tabindex="0"
        >
        <form @submit.prevent="handleRegister">
            <!-- Common -->
            <div class="mb-3">
            <label for="registerName" class="form-label">Full name</label>
            <input
                type="text"
                id="registerName"
                class="form-control"
                v-model.trim="registerForm.name"
                required
            />
            </div>

            <div class="mb-3">
            <label for="registerUsername" class="form-label">Username</label>
            <input
                type="text"
                id="registerUsername"
                class="form-control"
                v-model.trim="registerForm.username"
                required
            />
            </div>

            <!-- Role -->
            <div class="mb-3">
            <label for="registerRole" class="form-label">Account type</label>
            <select
                id="registerRole"
                class="form-select"
                v-model="registerForm.role"
                required
            >
                <option disabled value="">Select a role</option>
                <option value="customer">Customer</option>
                <option value="manufacturer">Manufacturer</option>
                <option value="shop_owner">Shop Owner / Manager</option>
            </select>
            </div>

            <!-- Role-specific fields -->
            <!-- CUSTOMER: just email -->
            <div v-if="registerForm.role === 'customer'" class="mb-3">
            <label for="registerEmail" class="form-label">Email</label>
            <input
                type="email"
                id="registerEmail"
                class="form-control"
                v-model.trim="registerForm.email"
                required
            />
            </div>

            <!-- SHOP OWNER -->
            <template v-if="registerForm.role === 'shop_owner'">
            <div class="mb-3">
                <label for="shopName" class="form-label">Shop name</label>
                <input id="shopName" class="form-control" v-model.trim="registerForm.shop.name" required />
            </div>
            <div class="mb-3">
                <label for="shopAddress" class="form-label">Shop address</label>
                <input id="shopAddress" class="form-control" v-model.trim="registerForm.shop.address" required />
            </div>
            <div class="mb-3">
                <label for="shopMobile" class="form-label">Mobile</label>
                <input id="shopMobile" class="form-control" v-model.trim="registerForm.shop.mobile" required />
            </div>
            </template>

            <!-- MANUFACTURER -->
            <template v-if="registerForm.role === 'manufacturer'">
            <div class="mb-3">
                <label for="plantName" class="form-label">Plant name</label>
                <input id="plantName" class="form-control" v-model.trim="registerForm.manufacturer.plantName" required />
            </div>
            <div class="mb-3">
                <label for="plantAddress" class="form-label">Plant address</label>
                <input id="plantAddress" class="form-control" v-model.trim="registerForm.manufacturer.address" required />
            </div>
            <div class="mb-3">
                <label for="plantMobile" class="form-label">Mobile</label>
                <input id="plantMobile" class="form-control" v-model.trim="registerForm.manufacturer.mobile" required />
            </div>
            </template>

            <!-- Passwords -->
            <div class="mb-3">
            <label for="registerPassword" class="form-label">Password</label>
            <input
                type="password"
                id="registerPassword"
                class="form-control"
                v-model="registerForm.password"
                minlength="8"
                required
            />
            </div>
            <div class="mb-3">
            <label for="registerRepeatPassword" class="form-label">Confirm password</label>
            <input
                type="password"
                id="registerRepeatPassword"
                class="form-control"
                v-model="registerForm.password2"
                required
            />
            </div>

            <div class="form-check mb-3">
            <input class="form-check-input" type="checkbox" id="terms" v-model="registerForm.terms" required />
            <label class="form-check-label" for="terms">I have read and agree to the terms</label>
            </div>

            <button type="submit" class="btn btn-primary w-100" :disabled="loadingRegister">
            <span v-if="!loadingRegister">Create account</span>
            <span v-else class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            </button>

            <p v-if="registerError" class="text-danger text-center mt-3">{{ registerError }}</p>
            <p v-if="registerSuccess" class="text-success text-center mt-3">{{ registerSuccess }}</p>
        </form>
        </div>

        </div>
        <!-- /Pills content -->

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/axios' // same axios instance you used before

const router = useRouter()

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

const handleLogin = async () => {
  loginError.value = ''
  loadingLogin.value = true
  try {
    const { data } = await api.post('/login', {
      username: loginForm.value.username,
      password: loginForm.value.password,
    })

  
    const { token, role, username, user_id } = data

    localStorage.setItem('token', token)
    localStorage.setItem('role', role)
    localStorage.setItem('username', username)
    localStorage.setItem('user_id', user_id)

    router.push(role === 'admin' ? '/admin' : '/user')
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

    registerSuccess.value = 'Account created. You can now log in.'
    // switch back to Login pill
    document.querySelector('#tab-login')?.click()

    // (optional) clear the form
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
.container { min-height: 100vh; }
</style>

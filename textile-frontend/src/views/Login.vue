<template>
  <div class="auth-container">
    <div class="auth-wrapper">
      <!-- Left Side - Branding -->
      <div class="auth-left">
        <div class="brand-section">
          <div class="brand-header">
            <div class="brand-icon">
              <svg class="icon-sparkle" viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                />
              </svg>
            </div>
            <h1 class="brand-title">SE Textile App</h1>
          </div>
          <p class="brand-subtitle">Smart Textile Supply Chain Management</p>

          <div class="features-list">
            <div class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                  />
                </svg>
              </div>
              <span>Role-based Access Control</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                  />
                </svg>
              </div>
              <span>Real-time Inventory Tracking</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                  />
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
                <label for="loginName" class="form-label"
                  >Email or Username</label
                >
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
                  <input
                    class="form-check-input"
                    type="checkbox"
                    id="rememberMe"
                    v-model="loginForm.remember"
                  />
                  <label class="form-check-label" for="rememberMe"
                    >Remember me</label
                  >
                </div>
                <a href="#" class="forgot-link">Forgot password?</a>
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loadingLogin"
              >
                <span v-if="!loadingLogin">Sign In</span>
                <span
                  v-else
                  class="spinner-border spinner-border-sm me-2"
                  role="status"
                  aria-hidden="true"
                ></span>
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
                <label for="registerUsername" class="form-label"
                  >Username</label
                >
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
                <label for="registerRole" class="form-label"
                  >Account Type</label
                >
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
                  <label for="shopAddress" class="form-label"
                    >Shop Address</label
                  >
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
                  <label for="plantAddress" class="form-label"
                    >Plant Address</label
                  >
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
                <label for="registerPassword" class="form-label"
                  >Password</label
                >
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
                <label for="registerRepeatPassword" class="form-label"
                  >Confirm Password</label
                >
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
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="terms"
                  v-model="registerForm.terms"
                  required
                />
                <label class="form-check-label" for="terms"
                  >I agree to the Terms and Conditions</label
                >
              </div>

              <button
                type="submit"
                class="btn btn-primary w-100"
                :disabled="loadingRegister"
              >
                <span v-if="!loadingRegister">Create Account</span>
                <span
                  v-else
                  class="spinner-border spinner-border-sm me-2"
                  role="status"
                  aria-hidden="true"
                ></span>
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
import { ref, nextTick } from "vue";
import { useRouter } from "vue-router";
import api from "@/api/axios";

defineOptions({
  name: "Login and Register View",
});

const router = useRouter();
const activeTab = ref("login");

// LOGIN STATE
const loginForm = ref({
  username: "",
  password: "",
  remember: true,
});
const loadingLogin = ref(false);
const loginError = ref("");

// REGISTER STATE
const registerForm = ref({
  name: "",
  username: "",
  role: "", // 'customer' | 'manufacturer' | 'shop_owner'
  email: "", // customer-only
  shop: {
    // shop_owner-only
    name: "",
    address: "",
    mobile: "",
  },
  manufacturer: {
    // manufacturer-only
    plantName: "",
    address: "",
    mobile: "",
  },
  password: "",
  password2: "",
  terms: false,
});

const loadingRegister = ref(false);
const registerError = ref("");
const registerSuccess = ref("");

const handleLogin = async () => {
  loginError.value = "";
  loadingLogin.value = true;

  try {
    const resp = await api.post("/auth/login", {
      username: loginForm.value.username,
      password: loginForm.value.password,
    });
    const data = resp?.data;

    if (!data) {
      loginError.value = "No response from server.";
      return;
    }

    if (data.status === "success") {
      const user = data.user;
      const token = data.token;

      localStorage.setItem("user", JSON.stringify(user));
      localStorage.setItem("role", user.role || "");
      localStorage.setItem("username", user.username || "");
      localStorage.setItem("user_id", user.id || "");
      localStorage.setItem("logged_in", "true");
      if (token) {
        localStorage.setItem("token", token);
      } else {
        localStorage.removeItem("token");
      }

      const roleRoutes = {
        customer: "/customer",
        manufacturer: "/distributor",
        shop_owner: "/shop",
        manager: "/shop",
        distributor: "/distributor",
      };
      
      // Wait for navigation to complete before finishing
      await router.push(roleRoutes[user.role] || "/");
      
      // Force event dispatch after navigation completes
      await nextTick();
      window.dispatchEvent(new Event("user-logged-in"));
    } else {
      loginError.value = data.message || "Login failed. Please try again.";
    }
  } catch (err) {
    const serverMsg = err?.response?.data?.message || err?.message;
    loginError.value = serverMsg || "Login failed. Please try again.";
    console.error("[Login Error]", err);
  } finally {
    loadingLogin.value = false;
  }
};

const handleRegister = async () => {
  registerError.value = "";
  registerSuccess.value = "";
  loadingRegister.value = true;

  try {
    if (!registerForm.value.role) {
      registerError.value = "Please select an account type.";
      return;
    }

    if (!registerForm.value.name || registerForm.value.name.trim() === "") {
      registerError.value = "Full name is required.";
      return;
    }

    if (!registerForm.value.username || registerForm.value.username.trim() === "") {
      registerError.value = "Username is required.";
      return;
    }

    if (registerForm.value.role === "customer" && (!registerForm.value.email || registerForm.value.email.trim() === "")) {
      registerError.value = "Email is required for customer accounts.";
      return;
    }

    if (registerForm.value.role === "shop_owner") {
      const s = registerForm.value.shop;
      if (!s.name || !s.address || !s.mobile) {
        registerError.value = "Shop name, address and mobile are required for Shop Owner.";
        return;
      }
    }

    if (registerForm.value.role === "manufacturer") {
      const m = registerForm.value.manufacturer;
      if (!m.plantName || !m.address || !m.mobile) {
        registerError.value = "Plant name, address and mobile are required for Manufacturer.";
        return;
      }
    }

    if (!registerForm.value.password || registerForm.value.password.length < 8) {
      registerError.value = "Password must be at least 8 characters.";
      return;
    }

    if (registerForm.value.password !== registerForm.value.password2) {
      registerError.value = "Passwords do not match.";
      return;
    }

    const base = {
      full_name: registerForm.value.name,
      username: registerForm.value.username,
      email: registerForm.value.email || `${registerForm.value.username}@noemail.com`,
      password: registerForm.value.password,
      role: registerForm.value.role,
    };

    if (registerForm.value.role === "shop_owner") {
      base.contact = registerForm.value.shop.mobile;
      base.address = registerForm.value.shop.address;
      base.shop_name = registerForm.value.shop.name;
    }

    if (registerForm.value.role === "manufacturer") {
      base.contact = registerForm.value.manufacturer.mobile;
      base.address = registerForm.value.manufacturer.address;
      base.plant_name = registerForm.value.manufacturer.plantName;
    }

    const resp = await api.post("/auth/register", base);
    const data = resp?.data;

    if (!data) {
      registerError.value = "No response from server.";
      return;
    }

    if (data.status === "success") {
      registerSuccess.value = data.message || "Account created successfully! Please sign in.";
      activeTab.value = "login";
      Object.assign(registerForm.value, {
        name: "",
        username: "",
        role: "",
        email: "",
        shop: { name: "", address: "", mobile: "" },
        manufacturer: { plantName: "", address: "", mobile: "" },
        password: "",
        password2: "",
        terms: false,
      });
    } else {
      // backend reported a failure
      registerError.value = data.message || "Registration failed. Please try again.";
    }
  } catch (err) {
    console.error("[Register Error]", err);
    registerError.value =
      err?.response?.data?.message || err?.message || "Registration failed. Please try again.";
  } finally {
    loadingRegister.value = false;
  }
};
</script>


<style scoped>
.auth-container {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--color-bg-alt) 0%, var(--color-bg) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.auth-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  min-height: 650px;
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* Left Side - Branding */
.auth-left {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: #4A4A4A;
  padding: 4rem 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.auth-left::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at top right, rgba(255,255,255,0.4), transparent 60%);
  pointer-events: none;
}

.brand-section {
  position: relative;
  z-index: 1;
}

.brand-header {
  text-align: center;
  margin-bottom: 3rem;
}

.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 5rem;
  height: 5rem;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  transform: rotate(-5deg);
  transition: transform 0.3s ease;
}

.brand-icon:hover {
  transform: rotate(0deg) scale(1.05);
}

.icon-sparkle {
  width: 2.5rem;
  height: 2.5rem;
  color: white;
}

.brand-title {
  font-size: 3rem;
  font-weight: 800;
  margin: 0 0 0.5rem 0;
  color: white;
  text-shadow: 0 2px 4px rgba(0,0,0,0.05);
  letter-spacing: -1px;
}

.brand-subtitle {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 2rem 0;
  font-weight: 500;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 2rem;
  border-radius: 20px;
  backdrop-filter: blur(5px);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  flex-shrink: 0;
}

.feature-icon svg {
  width: 1.25rem;
  height: 1.25rem;
  color: white;
}

.feature-item span {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

/* Right Side - Auth Forms */
.auth-right {
  padding: 4rem 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
}

.auth-card {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
}

/* Tab Navigation */
.auth-tabs {
  display: flex;
  background: #f1f5f9;
  border-radius: 16px;
  padding: 6px;
  margin-bottom: 2.5rem;
  position: relative;
}

.tab-button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  border-radius: 12px;
  font-weight: 600;
  color: #64748b;
  transition: all 0.3s ease;
  cursor: pointer;
  z-index: 1;
}

.tab-button.active {
  background: white;
  color: var(--color-text-dark);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.form-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.form-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.5px;
}

.form-header p {
  color: var(--color-text-muted);
  margin: 0;
  font-size: 1rem;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 600;
  color: var(--color-text-dark);
  font-size: 0.9rem;
  margin-bottom: 0;
}

.form-control, .form-select {
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: white;
  color: var(--color-text-dark);
}

.form-control:focus, .form-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(242, 190, 209, 0.15);
}

.form-control::placeholder {
  color: #94a3b8;
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

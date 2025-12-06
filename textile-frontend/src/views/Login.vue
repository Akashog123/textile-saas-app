<template>
  <div class="auth-container">
    <div class="auth-wrapper">
      <!-- Left Side - Branding -->
      <div class="auth-left">
        <div class="brand-section">
          <div class="brand-header">
            <img src="@/assets/icon.png" alt="Logo" style="width: 128px; height: 128px; object-fit: contain;" />
            <h1 class="brand-title">Textile Saas App</h1>
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
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <label for="shopAddress" class="form-label mb-0">Shop Address</label>
                    <button 
                      type="button" 
                      class="btn btn-sm btn-outline-primary" 
                      @click="useCurrentLocationRegister"
                      :disabled="locationLoading"
                    >
                      <span v-if="locationLoading" class="spinner-border spinner-border-sm me-1"></span>
                      <span v-else>📍</span>
                      Use Current Location
                    </button>
                  </div>
                  <input
                    id="shopAddress"
                    class="form-control"
                    v-model.trim="registerForm.shop.address"
                    required
                    placeholder="Enter shop address or use map"
                  />
                </div>
                <!-- Map for location selection -->
                <div class="form-group">
                  <small class="text-muted d-block mb-2">Click on the map or drag the marker to set your shop location</small>
                  <div id="register-map" class="register-map-container"></div>
                  <div class="row mt-2">
                    <div class="col-6">
                      <label class="form-label small">Latitude</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        :value="registerForm.shop.latitude?.toFixed(6) || ''" 
                        readonly 
                        placeholder="Auto-filled" 
                      />
                    </div>
                    <div class="col-6">
                      <label class="form-label small">Longitude</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        :value="registerForm.shop.longitude?.toFixed(6) || ''" 
                        readonly 
                        placeholder="Auto-filled" 
                      />
                    </div>
                  </div>
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
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <label for="plantAddress" class="form-label mb-0">Plant Address</label>
                    <button 
                      type="button" 
                      class="btn btn-sm btn-outline-primary" 
                      @click="useCurrentLocationRegister"
                      :disabled="locationLoading"
                    >
                      <span v-if="locationLoading" class="spinner-border spinner-border-sm me-1"></span>
                      <span v-else>📍</span>
                      Use Current Location
                    </button>
                  </div>
                  <input
                    id="plantAddress"
                    class="form-control"
                    v-model.trim="registerForm.manufacturer.address"
                    required
                    placeholder="Enter plant address or use map"
                  />
                </div>
                <!-- Map for location selection (shared container) -->
                <div class="form-group">
                  <small class="text-muted d-block mb-2">Click on the map or drag the marker to set your plant location</small>
                  <div id="register-map" class="register-map-container"></div>
                  <div class="row mt-2">
                    <div class="col-6">
                      <label class="form-label small">Latitude</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        :value="registerForm.manufacturer.latitude?.toFixed(6) || ''" 
                        readonly 
                        placeholder="Auto-filled" 
                      />
                    </div>
                    <div class="col-6">
                      <label class="form-label small">Longitude</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        :value="registerForm.manufacturer.longitude?.toFixed(6) || ''" 
                        readonly 
                        placeholder="Auto-filled" 
                      />
                    </div>
                  </div>
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
import L from "leaflet";
import { ref, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import api from "@/api/axios";

defineOptions({
  name: "Login and Register View",
});

// ---------- Map & Nominatim helpers for registration ----------
const mapRef = ref(null);
const markerRef = ref(null);
const mapInitialized = ref(false);
const locationLoading = ref(false);
const DEFAULT_COORDS = { lat: 10.8505, lon: 76.2711 }; // Kerala, India
const CACHE_TTL = 1000 * 60 * 60;
const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/reverse';
let lastGeocodeTs = 0;
let pendingGeoPromise = null;
let geocodingInFlight = false;

function cacheKey(lat, lon) {
  return `geo:${Number(lat).toFixed(5)}:${Number(lon).toFixed(5)}`;
}
function getCachedAddress(lat, lon) {
  try {
    const k = cacheKey(lat, lon);
    const raw = localStorage.getItem(k);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (Date.now() - parsed._ts > CACHE_TTL) {
      localStorage.removeItem(k);
      return null;
    }
    return parsed.data;
  } catch (e) {
    console.warn('geocode cache read failed', e);
    return null;
  }
}
function setCachedAddress(lat, lon, data) {
  try {
    const k = cacheKey(lat, lon);
    localStorage.setItem(k, JSON.stringify({ _ts: Date.now(), data }));
  } catch (e) {
    console.warn('geocode cache write failed', e);
  }
}

async function nominatimReverse(lat, lon, attempt = 0) {
  const cached = getCachedAddress(lat, lon);
  if (cached) return cached;

  const now = Date.now();
  const delta = now - lastGeocodeTs;
  const wait = delta >= 1000 ? 0 : 1000 - delta;

  if (wait > 0) {
    if (pendingGeoPromise) return pendingGeoPromise;
    pendingGeoPromise = new Promise((resolve) => {
      setTimeout(async () => {
        try {
          const d = await nominatimReverse(lat, lon, attempt);
          resolve(d);
        } finally {
          pendingGeoPromise = null;
        }
      }, wait);
    });
    return pendingGeoPromise;
  }

  lastGeocodeTs = Date.now();
  const params = new URLSearchParams({
    format: 'jsonv2',
    lat: String(lat),
    lon: String(lon),
    addressdetails: '1',
    email: 'ops@setextile.example'
  });

  const res = await fetch(`${NOMINATIM_BASE}?${params.toString()}`);
  if (!res.ok) {
    if (res.status === 429 && attempt < 3) {
      await new Promise(r => setTimeout(r, 500 * Math.pow(2, attempt)));
      return nominatimReverse(lat, lon, attempt + 1);
    }
    throw new Error(`Nominatim error ${res.status}`);
  }
  const data = await res.json();
  setCachedAddress(lat, lon, data);
  return data;
}

function destroyMap() {
  if (markerRef.value) markerRef.value = null;
  if (mapRef.value) {
    mapRef.value.remove();
    mapRef.value = null;
  }
  mapInitialized.value = false;
}

async function initRegisterMap() {
  if (mapInitialized.value) return;
  await nextTick();
  const el = document.getElementById('register-map');
  if (!el) return;

  const lat = DEFAULT_COORDS.lat;
  const lon = DEFAULT_COORDS.lon;

  mapRef.value = L.map(el, { center: [lat, lon], zoom: 6 });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(mapRef.value);

  markerRef.value = L.marker([lat, lon], { draggable: true }).addTo(mapRef.value);

  markerRef.value.on('dragend', (ev) => {
    const pos = ev.target.getLatLng();
    updateRegisterCoords(pos.lat, pos.lng);
  });

  mapRef.value.on('click', (e) => {
    const { lat: clickedLat, lng: clickedLng } = e.latlng;
    markerRef.value.setLatLng([clickedLat, clickedLng]);
    updateRegisterCoords(clickedLat, clickedLng);
  });

  mapInitialized.value = true;
}

function setRegisterMapMarker(lat, lon, center = true) {
  if (!mapInitialized.value) return;
  if (markerRef.value) {
    markerRef.value.setLatLng([lat, lon]);
  }
  if (center && mapRef.value) mapRef.value.setView([lat, lon], 15);
}

function updateRegisterCoords(lat, lon) {
  if (registerForm.value.role === 'shop_owner') {
    registerForm.value.shop.latitude = lat;
    registerForm.value.shop.longitude = lon;
  } else if (registerForm.value.role === 'manufacturer') {
    registerForm.value.manufacturer.latitude = lat;
    registerForm.value.manufacturer.longitude = lon;
  }
  reverseGeocodeRegister(lat, lon).catch(() => {});
}

async function reverseGeocodeRegister(lat, lon) {
  if (geocodingInFlight) return;
  geocodingInFlight = true;
  try {
    const data = await nominatimReverse(lat, lon);
    const address = data.display_name || (data.address ? Object.values(data.address).join(', ') : '');
    if (registerForm.value.role === 'shop_owner') {
      registerForm.value.shop.address = address;
    } else if (registerForm.value.role === 'manufacturer') {
      registerForm.value.manufacturer.address = address;
    }
  } finally {
    geocodingInFlight = false;
  }
}

function useCurrentLocationRegister() {
  if (!navigator.geolocation) {
    registerError.value = 'Geolocation not supported by your browser.';
    return;
  }
  // Check if we're on HTTPS (required for geolocation in most browsers)
  if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    registerError.value = 'Location access requires HTTPS. Please use the map to select your location.';
    return;
  }
  locationLoading.value = true;
  navigator.geolocation.getCurrentPosition(async (pos) => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    updateRegisterCoords(lat, lon);
    if (!mapInitialized.value) await initRegisterMap();
    setRegisterMapMarker(lat, lon, true);
    try {
      await reverseGeocodeRegister(lat, lon);
    } catch (e) {
      console.warn('reverse geocode failed', e);
    }
    locationLoading.value = false;
  }, (err) => {
    console.error('geolocation error', err);
    let errorMsg = 'Failed to get current location.';
    if (err.code === 1) {
      errorMsg = 'Location permission denied. Please allow location access or use the map.';
    } else if (err.code === 2) {
      errorMsg = 'Location unavailable. Please use the map to select your location.';
    } else if (err.code === 3) {
      errorMsg = 'Location request timed out. Please try again or use the map.';
    }
    registerError.value = errorMsg;
    locationLoading.value = false;
  }, { timeout: 10000, enableHighAccuracy: true });
}

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
    latitude: null,
    longitude: null,
  },
  manufacturer: {
    // manufacturer-only
    plantName: "",
    address: "",
    mobile: "",
    latitude: null,
    longitude: null,
  },
  password: "",
  password2: "",
  terms: false,
});

const loadingRegister = ref(false);
const registerError = ref("");
const registerSuccess = ref("");

// Watch role changes to init/destroy map (must be after registerForm is defined)
watch(() => registerForm.value.role, async (newRole, oldRole) => {
  if (['shop_owner', 'manufacturer'].includes(newRole)) {
    // Delay to let DOM render the map container
    await nextTick();
    await new Promise(r => setTimeout(r, 100));
    await initRegisterMap();
    // Invalidate map size after display
    if (mapRef.value) {
      setTimeout(() => mapRef.value.invalidateSize(), 200);
    }
  } else if (['shop_owner', 'manufacturer'].includes(oldRole)) {
    destroyMap();
  }
});

const handleLogin = async () => {
  loginError.value = "";
  loadingLogin.value = true;

  // Clear any cached data from previous user session
  sessionStorage.clear();

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
      
      // Also trigger a storage event for cross-tab communication
      window.dispatchEvent(new Event("storage"));
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
      if (registerForm.value.shop.latitude && registerForm.value.shop.longitude) {
        base.latitude = registerForm.value.shop.latitude;
        base.longitude = registerForm.value.shop.longitude;
      }
    }

    if (registerForm.value.role === "manufacturer") {
      base.contact = registerForm.value.manufacturer.mobile;
      base.address = registerForm.value.manufacturer.address;
      base.plant_name = registerForm.value.manufacturer.plantName;
      if (registerForm.value.manufacturer.latitude && registerForm.value.manufacturer.longitude) {
        base.latitude = registerForm.value.manufacturer.latitude;
        base.longitude = registerForm.value.manufacturer.longitude;
      }
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
      // Destroy map before resetting form
      destroyMap();
      Object.assign(registerForm.value, {
        name: "",
        username: "",
        role: "",
        email: "",
        shop: { name: "", address: "", mobile: "", latitude: null, longitude: null },
        manufacturer: { plantName: "", address: "", mobile: "", latitude: null, longitude: null },
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
  box-shadow: 0 0 0 4px rgba(74, 144, 226, 0.15);
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

/* Map container for registration */
.register-map-container {
  height: 200px;
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background-color: #f8fafc;
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

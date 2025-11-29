<template>
  <div class="shop-profile-tab fade-in-entry">
    <h5 class="mb-4">
      <i class="bi bi-person-circle me-2"></i>User Profile
    </h5>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status" aria-hidden="true"></div>
      <p class="mt-2 text-muted">Loading profile...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger" role="alert">
      <i class="bi bi-exclamation-triangle me-2" aria-hidden="true"></i>{{ error }}
    </div>

    <!-- Profile Card -->
    <div v-else class="card mb-5" ref="cardRef">
      <div class="card-body">
        <!-- View Mode -->
        <div v-if="!editMode">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h6 class="mb-0">Personal Information</h6>
            <button class="btn btn-primary" @click="enableEditMode">
              <i class="bi bi-pencil me-1"></i>Edit Profile
            </button>
          </div>

          <div class="row g-3">
            <div class="col-md-6">
              <div class="profile-field">
                <label class="text-muted small">Full Name</label>
                <p class="fw-semibold">{{ profile.full_name || 'N/A' }}</p>
              </div>
            </div>

            <div class="col-md-6">
              <div class="profile-field">
                <label class="text-muted small">Email Address</label>
                <p class="fw-semibold">{{ profile.email || 'N/A' }}</p>
              </div>
            </div>

            <div class="col-md-6">
              <div class="profile-field">
                <label class="text-muted small">Contact Number</label>
                <p class="fw-semibold">{{ profile.contact || 'N/A' }}</p>
              </div>
            </div>

            <div class="col-md-6">
              <div class="profile-field">
                <label class="text-muted small">Account Role</label>
                <p class="fw-semibold text-capitalize">
                  <span class="badge bg-info text-dark">{{ profile.role || 'User' }}</span>
                </p>
              </div>
            </div>

            <div class="col-12">
              <div class="profile-field">
                <label class="text-muted small">Address</label>
                <p class="fw-semibold">{{ profile.address || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else>
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h6 class="mb-0">Edit Personal Details</h6>
            <button class="btn btn-outline-secondary" @click="cancelEdit">
              <i class="bi bi-x me-1"></i>Cancel
            </button>
          </div>

          <form @submit.prevent="saveProfile" novalidate>
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label">Full Name *</label>
                <input
                  ref="firstInput"
                  type="text"
                  class="form-control"
                  v-model.trim="editForm.full_name"
                  required
                />
              </div>

              <div class="col-md-6">
                <label class="form-label">Email Address *</label>
                <input
                  type="email"
                  class="form-control"
                  v-model.trim="editForm.email"
                  required
                />
              </div>

              <div class="col-md-6">
                <label class="form-label">Contact Number</label>
                <input
                  type="tel"
                  class="form-control"
                  v-model.trim="editForm.contact"
                  placeholder="+91 XXXXXXXXXX"
                />
              </div>

              <div class="col-12">
                <label class="form-label">Address</label>
                <textarea
                  class="form-control"
                  v-model="editForm.address"
                  rows="2"
                  placeholder="Enter your address"
                ></textarea>
              </div>

              <div class="col-12 mt-4">
                <button
                  type="submit"
                  class="btn btn-primary me-2"
                  :disabled="saving || !isDirty || hasValidationError"
                >
                  <span v-if="saving">
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Saving...
                  </span>
                  <span v-else>
                    <i class="bi bi-check me-1"></i>Save Changes
                  </span>
                </button>
                <button type="button" class="btn btn-outline-secondary" @click="cancelEdit">
                  Cancel
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Linked Shops Section -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">
        <i class="bi bi-shop me-2"></i>Linked Shops
      </h5>
      <div>
        <button class="btn btn-outline-primary me-2" @click="openShopModal()">+ New Shop</button>
        <button class="btn btn-outline-secondary" @click="fetchShops()">Refresh</button>
      </div>
    </div>

    <div class="card mb-4">
      <div class="card-body">
        <div v-if="loadingShops" class="text-center py-4">
          <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
          <span class="ms-2 text-muted">Loading shops...</span>
        </div>

        <div v-else-if="shops.length === 0" class="text-center py-4 text-muted">
          <i class="bi bi-shop-window fs-1 d-block mb-2 opacity-50"></i>
          No shops linked to this account.
        </div>

        <div v-else class="table-responsive">
          <table class="table table-hover align-middle">
            <thead class="table-light">
              <tr>
                <th>Shop Name</th>
                <th>Location</th>
                <th>Contact</th>
                <th>GSTIN</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="shop in shops" :key="shop.id">
                <td class="fw-semibold">{{ shop.shop_name }}</td>
                <td>
                  <small class="text-muted d-block text-truncate" style="max-width: 300px;">
                    {{ shop.address || shop.location || 'No address' }}
                  </small>
                  <small class="text-muted d-block">Lat: {{ shop.latitude ?? '-' }}, Lon: {{ shop.longitude ?? '-' }}</small>
                </td>
                <td>{{ shop.contact || '-' }}</td>
                <td>{{ shop.gstin || '-' }}</td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-primary me-1" @click="openShopModal(shop)">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-secondary me-1" @click="goToShop(shop.id)">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="confirmDelete(shop.id)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Shop Modal (create/edit) -->
    <div v-if="showShopModal" class="modal-backdrop">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h6 class="modal-title">{{ editingShop.id ? 'Edit Shop' : 'Create Shop' }}</h6>
            <button class="btn-close" @click="closeShopModal()"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveShop">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label">Shop Name *</label>
                  <input v-model.trim="editingShop.name" required class="form-control" />
                </div>
                <div class="col-md-6">
                  <label class="form-label">Contact</label>
                  <input v-model.trim="editingShop.contact" class="form-control" />
                </div>
                <div class="col-md-6">
                  <label class="form-label">City</label>
                  <input v-model.trim="editingShop.city" class="form-control" />
                </div>
                <div class="col-md-6">
                  <label class="form-label">State</label>
                  <input v-model.trim="editingShop.state" class="form-control" />
                </div>

                <div class="col-12">
                  <label class="form-label">Address</label>
                  <textarea v-model="editingShop.address" rows="2" class="form-control"></textarea>
                </div>

                <div class="col-12">
                  <label class="form-label">Description</label>
                  <textarea v-model="editingShop.description" rows="2" class="form-control"></textarea>
                </div>

                <!-- Map and coords -->
                <div class="col-12">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                      <small class="text-muted">Click map to set location or drag marker. You can also use 'Current location'.</small>
                    </div>
                    <div>
                      <button type="button" class="btn btn-sm btn-outline-secondary me-2" @click="useCurrentLocation">Current location</button>
                      <button type="button" class="btn btn-sm btn-outline-secondary" @click="clearShopCoords">Clear coords</button>
                    </div>
                  </div>

                  <div id="shop-map" style="height:320px;border:1px solid #e9ecef;border-radius:8px;"></div>

                  <div class="row mt-2">
                    <div class="col-md-6">
                      <label class="form-label">Latitude</label>
                      <input v-model="editingShop.latitude" class="form-control" />
                    </div>
                    <div class="col-md-6">
                      <label class="form-label">Longitude</label>
                      <input v-model="editingShop.longitude" class="form-control" />
                    </div>
                  </div>
                </div>

              </div>

              <div class="mt-3 text-end">
                <button type="button" class="btn btn-secondary me-2" @click="closeShopModal()">Cancel</button>
                <button type="submit" :disabled="shopSaving" class="btn btn-primary">
                  <span v-if="shopSaving" class="spinner-border spinner-border-sm me-2"></span>
                  Save Shop
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div
      v-if="showToast"
      class="toast-notification"
      role="status"
      aria-live="polite"
      :aria-atomic="true"
    >
      <i :class="toastIcon" class="me-2" aria-hidden="true"></i>
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-console */
import L from 'leaflet';
import { ref, onMounted, nextTick } from 'vue';
import { getProfile, updateProfile } from '@/api/apiProfile';
import apiShop, { getMyShops, createShop, updateShop, deleteShop } from '@/api/apiShop';
import axios from '@/api/axios';

// ---------- profile state (unchanged) ----------
const loading = ref(false);
const error = ref('');
const profile = ref({});
const editMode = ref(false);
const editForm = ref({});
const saving = ref(false);
const cardRef = ref(null);
const firstInput = ref(null);

// ---------- toast ----------
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');
const showToastMessage = (message, icon = 'bi bi-check-circle-fill') => {
  toastMessage.value = message;
  toastIcon.value = icon;
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

// ---------- shops state ----------
const shops = ref([]);
const loadingShops = ref(false);

// modal / editing shop
const showShopModal = ref(false);
const editingShop = ref({
  id: null,
  name: '',
  description: '',
  address: '',
  location: '',
  city: '',
  state: '',
  contact: '',
  gstin: '',
  latitude: null,
  longitude: null,
  image: null
});
const shopSaving = ref(false);

// ---------- map & nominatim helpers (used inside modal) ----------
const mapRef = ref(null);
const markerRef = ref(null);
const mapInitialized = ref(false);
const DEFAULT_COORDS = { lat: 10.8505, lon: 76.2711 };
const CACHE_TTL = 1000 * 60 * 60;
const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/reverse';
const CONTACT_EMAIL = 'ops@yourdomain.example'; // change to real email if possible
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
    email: CONTACT_EMAIL
  });

  const res = await fetch(`${NOMINATIM_BASE}?${params.toString()}`);
  if (!res.ok) {
    if (res.status === 429 && attempt < 3) {
      await new Promise(r => setTimeout(r, 500 * Math.pow(2, attempt)));
      return nominatimReverse(lat, lon, attempt + 1);
    }
    const txt = await res.text();
    throw new Error(`Nominatim error ${res.status} ${txt}`);
  }
  const data = await res.json();
  setCachedAddress(lat, lon, data);
  return data;
}

// map init for modal
async function initMapFrontendOnly() {
  if (mapInitialized.value) return;
  await nextTick();
  const el = document.getElementById('shop-map');
  if (!el) return;

  const lat = parseFloat(editingShop.value.latitude) || DEFAULT_COORDS.lat;
  const lon = parseFloat(editingShop.value.longitude) || DEFAULT_COORDS.lon;

  mapRef.value = L.map(el, { center: [lat, lon], zoom: 13 });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(mapRef.value);

  markerRef.value = L.marker([lat, lon], { draggable: true }).addTo(mapRef.value);

  markerRef.value.on('dragend', (ev) => {
    const pos = ev.target.getLatLng();
    editingShop.value.latitude = pos.lat;
    editingShop.value.longitude = pos.lng;
    _reverseGeocodeFrontend(pos.lat, pos.lng).catch(()=>{});
  });

  mapRef.value.on('click', (e) => {
    const { lat: clickedLat, lng: clickedLng } = e.latlng;
    markerRef.value.setLatLng([clickedLat, clickedLng]);
    editingShop.value.latitude = clickedLat;
    editingShop.value.longitude = clickedLng;
    _reverseGeocodeFrontend(clickedLat, clickedLng).catch(()=>{});
  });

  mapInitialized.value = true;
}

function setMapMarker(lat, lon, center = true) {
  if (!mapInitialized.value) return;
  if (!markerRef.value) {
    markerRef.value = L.marker([lat, lon], { draggable: true }).addTo(mapRef.value);
    markerRef.value.on('dragend', (ev) => {
      const pos = ev.target.getLatLng();
      editingShop.value.latitude = pos.lat;
      editingShop.value.longitude = pos.lng;
      _reverseGeocodeFrontend(pos.lat, pos.lng).catch(()=>{});
    });
  } else {
    markerRef.value.setLatLng([lat, lon]);
  }
  if (center) mapRef.value.setView([lat, lon], 15);
}

function clearMapMarker() {
  if (markerRef.value) {
    mapRef.value.removeLayer(markerRef.value);
    markerRef.value = null;
  }
  mapRef.value.setView([DEFAULT_COORDS.lat, DEFAULT_COORDS.lon], 6);
}

async function _reverseGeocodeFrontend(lat, lon) {
  if (geocodingInFlight) return;
  geocodingInFlight = true;
  try {
    const data = await nominatimReverse(lat, lon);
    editingShop.value.address = data.display_name || (data.address ? Object.values(data.address).join(', ') : '');
    editingShop.value.location = editingShop.value.address;
    return data;
  } finally {
    geocodingInFlight = false;
  }
}

function clearShopCoords() {
  editingShop.value.latitude = null;
  editingShop.value.longitude = null;
  editingShop.value.address = editingShop.value.address || '';
  if (mapInitialized.value) {
    clearMapMarker();
  }
}

function useCurrentLocation() {
  if (!navigator.geolocation) {
    showToastMessage('Geolocation not supported', 'bi bi-exclamation-circle-fill');
    return;
  }
  showToastMessage('Getting current location...', 'bi bi-info-circle-fill');
  navigator.geolocation.getCurrentPosition(async (pos) => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    editingShop.value.latitude = lat;
    editingShop.value.longitude = lon;
    if (!mapInitialized.value) await initMapFrontendOnly();
    setMapMarker(lat, lon, true);
    try {
      await _reverseGeocodeFrontend(lat, lon);
      showToastMessage('Location set', 'bi bi-check-circle-fill');
    } catch (e) {
      showToastMessage('Location set (no address)', 'bi bi-info-circle-fill');
    }
  }, (err) => {
    console.error('geolocation error', err);
    showToastMessage('Failed to get current location', 'bi bi-exclamation-circle-fill');
  }, { timeout: 10000 });
}

// ---------- profile functions ----------
const fetchProfile = async () => {
  loading.value = true;
  error.value = '';
  try {
    const response = await getProfile();
    if (response?.data?.status === 'success') {
      profile.value = response.data.profile || {};
    } else {
      error.value = response?.data?.message || 'Failed to load profile';
    }
  } catch (err) {
    console.error('[Profile Error]', err);
    error.value = err?.response?.data?.message || 'Failed to load profile';
  } finally {
    loading.value = false;
  }
};

const enableEditMode = async () => {
  editForm.value = {
    full_name: profile.value.full_name ?? '',
    email: profile.value.email ?? '',
    contact: profile.value.contact ?? '',
    address: profile.value.address ?? ''
  };
  editMode.value = true;
  await nextTick();
  firstInput.value?.focus();
};

const cancelEdit = () => {
  if (isDirty.value) {
    const ok = confirm('You have unsaved changes. Discard them?');
    if (!ok) return;
  }
  editMode.value = false;
  editForm.value = {};
};

const normalize = (obj = {}) => JSON.stringify(obj);
const originalSnapshot = () => normalize({
  full_name: profile.value.full_name,
  email: profile.value.email,
  contact: profile.value.contact,
  address: profile.value.address
});
const editSnapshot = () => normalize(editForm.value);
const isDirty = { value: false }; // computed-like observer replaced by manual check
// simple watcher replacement: compute on demand
Object.defineProperty(isDirty, 'value', {
  get() { return originalSnapshot() !== editSnapshot(); }
});

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const phoneRegex = /^(\+91)?\s?\d{10}$/;

const hasValidationError = () => {
  if (!editForm.value) return false;
  if (!editForm.value.full_name || !editForm.value.email) return true;
  if (!emailRegex.test(editForm.value.email)) return true;
  if (editForm.value.contact && !phoneRegex.test(editForm.value.contact)) return true;
  return false;
};

const saveProfile = async () => {
  if (!editForm.value.full_name || !editForm.value.email) {
    return showToastMessage('Name and Email are required', 'bi bi-exclamation-circle-fill');
  }
  if (!emailRegex.test(editForm.value.email)) {
    return showToastMessage('Please enter a valid email', 'bi bi-exclamation-circle-fill');
  }
  if (editForm.value.contact && !phoneRegex.test(editForm.value.contact)) {
    return showToastMessage('Please enter a valid contact number', 'bi bi-exclamation-circle-fill');
  }

  saving.value = true;
  try {
    const payload = { ...editForm.value };
    const response = await updateProfile(payload);
    if (response?.data?.status === 'success') {
      await fetchProfile();
      editMode.value = false;
      showToastMessage('Profile updated successfully!', 'bi bi-check-circle-fill');
    } else {
      showToastMessage(response?.data?.message || 'Failed to update profile', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('[Update Error]', err);
    showToastMessage(err?.response?.data?.message || 'Failed to update profile', 'bi bi-exclamation-circle-fill');
  } finally {
    saving.value = false;
  }
};

// ---------- shops CRUD (frontend) ----------
const fetchShops = async () => {
  loadingShops.value = true;
  try {
    const res = await getMyShops();
    if (res && res.data && res.data.shops) shops.value = res.data.shops;
    else shops.value = Array.isArray(res?.data) ? res.data : [];
  } catch (err) {
    console.error('[Shops Error]', err);
    showToastMessage('Failed to load shops', 'bi bi-exclamation-circle-fill');
  } finally {
    loadingShops.value = false;
  }
};

function openShopModal(shop = null) {
  if (shop) {
    editingShop.value = {
      id: shop.id,
      name: shop.name || shop.shop_name || '',
      description: shop.description || '',
      address: shop.address || shop.location || '',
      location: shop.location || shop.address || '',
      city: shop.city || '',
      state: shop.state || '',
      contact: shop.contact || '',
      gstin: shop.gstin || '',
      latitude: shop.latitude ?? shop.lat ?? null,
      longitude: shop.longitude ?? shop.lon ?? null,
      image: shop.image || null
    };
  } else {
    editingShop.value = {
      id: null, name: '', description: '', address: '', location: '', city: '', state: '',
      contact: '', gstin: '', latitude: null, longitude: null, image: null
    };
  }
  showShopModal.value = true;
  // initialize map after DOM visible
  nextTick(() => initMapFrontendOnly().then(() => {
    if (editingShop.value.latitude && editingShop.value.longitude) {
      setMapMarker(editingShop.value.latitude, editingShop.value.longitude, true);
    } else {
      // center default
      mapRef.value.setView([DEFAULT_COORDS.lat, DEFAULT_COORDS.lon], 6);
      clearMapMarker();
    }
  }).catch(e => console.error('map init', e)));
}

function closeShopModal() {
  showShopModal.value = false;
  // leave map alive (to reuse), but clear marker for next open
}

async function saveShop() {
  if (!editingShop.value.name) {
    showToastMessage('Shop name is required', 'bi bi-exclamation-circle-fill');
    return;
  }
  shopSaving.value = true;
  try {
    const payload = {
      name: editingShop.value.name,
      shop_name: editingShop.value.name,
      description: editingShop.value.description,
      address: editingShop.value.address,
      location: editingShop.value.location || editingShop.value.address,
      city: editingShop.value.city,
      state: editingShop.value.state,
      contact: editingShop.value.contact,
      gstin: editingShop.value.gstin,
      latitude: editingShop.value.latitude,
      longitude: editingShop.value.longitude,
      image: editingShop.value.image
    };

    let res;
    if (editingShop.value.id) {
      res = await updateShop(editingShop.value.id, payload);
    } else {
      res = await createShop(payload);
    }

    if (res?.data?.status === 'success') {
      showToastMessage('Shop saved', 'bi bi-check-circle-fill');
      await fetchShops();
      closeShopModal();
    } else {
      const msg = res?.data?.message || 'Failed to save shop';
      showToastMessage(msg, 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('saveShop error', err);
    showToastMessage(err?.response?.data?.message || 'Failed to save shop', 'bi bi-exclamation-circle-fill');
  } finally {
    shopSaving.value = false;
  }
}

function confirmDelete(shopId) {
  if (!confirm('Delete this shop? This action is permanent.')) return;
  deleteShopById(shopId);
}

async function deleteShopById(shopId) {
  try {
    const res = await deleteShop(shopId);
    if (res?.data?.status === 'success') {
      showToastMessage('Shop deleted', 'bi bi-check-circle-fill');
      await fetchShops();
    } else {
      showToastMessage(res?.data?.message || 'Failed to delete shop', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('deleteShop error', err);
    showToastMessage('Failed to delete shop', 'bi bi-exclamation-circle-fill');
  }
}

function goToShop(shopId) {
  // Hook here to route to shop page if you have one
  showToastMessage(`Open shop ${shopId}`, 'bi bi-info-circle');
}

// ---------- lifecycle ----------
onMounted(() => {
  fetchProfile();
  fetchShops();
});
</script>

<style scoped>
/* --- existing styles kept (unchanged) --- */
.shop-profile-tab {
  background: transparent;
  min-height: calc(100vh - 60px);
  padding: 2rem;
  padding-bottom: 4rem;
}
.fade-in-entry { animation: fadeInPage 0.6s ease-out forwards; }
@keyframes fadeInPage { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
h5, h6 { background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 700; }
.card { border-radius: 24px; border: 1px solid var(--glass-border); background: rgba(255,255,255,0.8); backdrop-filter: blur(16px); box-shadow: 0 8px 30px rgba(0,0,0,0.05); transition: all 0.3s cubic-bezier(0.4,0,0.2,1); }
.profile-field { padding: 1rem; background: rgba(255,255,255,0.5); border: 1px solid var(--glass-border); border-radius: 12px; transition: all 0.3s ease; }
.profile-field:hover { transform: translateX(2px); box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.profile-field label { display:block; margin-bottom:0.25rem; }
.profile-field p { margin-bottom: 0; }
.form-control, .form-select { border-radius:8px; border:1.5px solid #dee2e6; transition: all .3s ease; }
.form-control:focus, .form-select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 .25rem rgba(74,144,226,0.15); }
.btn-primary { background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%); border:none; border-radius:8px; font-weight:500; transition: all .3s ease; }
.btn-outline-secondary { border-radius:8px; font-weight:500; transition: all .3s ease; }

/* modal & backdrop */
.modal-backdrop {
  position: fixed;
  z-index: 1200;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  display:flex;
  align-items:center;
  justify-content:center;
  padding: 1.5rem;
  background: rgba(0,0,0,0.35);
}
.modal-dialog { width: 100%; max-width: 980px; }
.modal-content { border-radius: 12px; overflow: hidden; }
.modal-header { display:flex; align-items:center; justify-content:space-between; padding:1rem 1.25rem; border-bottom:1px solid #eee; }
.modal-body { padding:1rem 1.25rem; max-height:78vh; overflow:auto; }

/* toast */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  z-index: 1300;
  animation: slideIn 0.3s ease;
}
@keyframes slideIn { from { transform: translateX(100%); opacity:0 } to { transform: translateX(0); opacity:1 } }
</style>

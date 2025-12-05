<template>
  <div class="shop-profile-tab fade-in-entry">
    <!-- Page Header -->
    <div class="page-header mb-4">
      <div class="d-flex align-items-center">
        <div class="header-icon me-3">
          <i class="bi bi-person-circle"></i>
        </div>
        <div>
          <h4 class="page-title mb-1">User Profile</h4>
          <p class="page-subtitle mb-0 text-muted">Manage your account and linked shops</p>
        </div>
      </div>
    </div>

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
    <div v-else class="card profile-card mb-4" ref="cardRef">
      <div class="card-body">
        <!-- View Mode -->
        <div v-if="!editMode">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h6 class="section-title mb-0"><i class="bi bi-person-lines-fill me-2"></i>Personal Information</h6>
            <button class="btn btn-gradient btn-sm" @click="enableEditMode">
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
                <label class="text-muted small">Registered Address</label>
                <p class="fw-semibold">{{ profile.address || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else>
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h6 class="section-title mb-0"><i class="bi bi-pencil-square me-2"></i>Edit Personal Details</h6>
            <button class="btn btn-outline-secondary btn-sm" @click="cancelEdit">
              <i class="bi bi-x-lg me-1"></i>Cancel
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
                <label class="form-label">Registered Address</label>
                <textarea
                  class="form-control"
                  v-model="editForm.address"
                  rows="2"
                  placeholder="Enter your registered business address"
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
    <div class="section-header d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-4 gap-2">
      <div class="d-flex align-items-center">
        <div class="header-icon-sm me-2">
          <i class="bi bi-shop"></i>
        </div>
        <div>
          <h5 class="section-title mb-0">Linked Shops</h5>
          <small class="text-muted" v-if="shops.length > 0">{{ shops.length }} shop{{ shops.length !== 1 ? 's' : '' }} registered</small>
        </div>
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-gradient btn-sm" @click="openShopModal()">
          <i class="bi bi-plus-lg me-1"></i>New Shop
        </button>
        <button class="btn btn-gradient btn-sm" @click="fetchShops()" title="Refresh">
          <i class="bi bi-arrow-clockwise"></i>
        </button>
      </div>
    </div>

    <!-- Primary Shop Card (if exists) -->
    <div v-if="primaryShop" class="card primary-shop-card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <div class="d-flex align-items-center">
          <i class="bi bi-star-fill text-warning me-2"></i>
          <span class="fw-semibold">Primary Shop</span>
        </div>
        <span class="badge bg-success">Active</span>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <div class="profile-field">
              <label class="text-muted small">Shop Name</label>
              <p class="fw-semibold mb-0">{{ primaryShop.name || primaryShop.shop_name || 'N/A' }}</p>
            </div>
          </div>
          <div class="col-md-6">
            <div class="profile-field">
              <label class="text-muted small">City</label>
              <p class="fw-semibold mb-0">{{ primaryShop.city || 'N/A' }}</p>
            </div>
          </div>
          <div class="col-md-6">
            <div class="profile-field">
              <label class="text-muted small">Contact</label>
              <p class="fw-semibold mb-0">{{ primaryShop.contact || 'N/A' }}</p>
            </div>
          </div>
          <div class="col-md-6">
            <div class="profile-field">
              <label class="text-muted small">Rating</label>
              <p class="fw-semibold mb-0">
                <i class="bi bi-star-fill text-warning me-1"></i>{{ primaryShop.rating || '4.0' }}
              </p>
            </div>
          </div>
          <div class="col-12">
            <div class="profile-field">
              <label class="text-muted small">Address</label>
              <p class="fw-semibold mb-0">{{ primaryShop.address || primaryShop.location || 'N/A' }}</p>
            </div>
          </div>
          <div class="col-12">
            <div class="d-flex gap-2">
              <span class="badge bg-light text-dark">
                <i class="bi bi-box me-1"></i>{{ primaryShop.product_count || 0 }} Products
              </span>
              <span class="badge bg-light text-dark">
                <i class="bi bi-chat-dots me-1"></i>{{ primaryShop.review_count || 0 }} Reviews
              </span>
              <span v-if="primaryShop.gstin" class="badge bg-light text-dark">
                <i class="bi bi-receipt me-1"></i>GSTIN: {{ primaryShop.gstin }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- All Shops Table -->
    <div class="card shops-table-card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span class="fw-semibold"><i class="bi bi-list-ul me-2"></i>All Shops</span>
      </div>
      <div class="card-body">
        <div v-if="loadingShops" class="text-center py-4">
          <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
          <span class="ms-2 text-muted">Loading shops...</span>
        </div>

        <div v-else-if="shops.length === 0" class="text-center py-4 text-muted">
          <i class="bi bi-shop-window fs-1 d-block mb-2 opacity-50"></i>
          <p class="mb-2">No shops linked to this account.</p>
          <button class="btn btn-primary btn-sm" @click="openShopModal()">
            <i class="bi bi-plus-lg me-1"></i>Create Your First Shop
          </button>
        </div>

        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th style="width: 40px;"></th>
                <th>Shop Name</th>
                <th>Location</th>
                <th>Contact</th>
                <th>Stats</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="shop in shops" :key="shop.id" :class="{ 'table-primary': shop.is_primary }">
                <td>
                  <i v-if="shop.is_primary" class="bi bi-star-fill text-warning" title="Primary Shop"></i>
                </td>
                <td>
                  <span class="fw-semibold">{{ shop.name || shop.shop_name }}</span>
                  <span v-if="shop.is_primary" class="badge bg-primary ms-2">Primary</span>
                </td>
                <td>
                  <small class="text-muted d-block text-truncate" style="max-width: 250px;">
                    {{ shop.address || shop.location || 'No address' }}
                  </small>
                  <small class="text-muted">{{ shop.city || '' }}{{ shop.city && shop.state ? ', ' : '' }}{{ shop.state || '' }}</small>
                </td>
                <td>{{ shop.contact || '-' }}</td>
                <td>
                  <span class="badge bg-light text-dark me-1">
                    <i class="bi bi-box"></i> {{ shop.product_count || 0 }}
                  </span>
                  <span class="badge bg-light text-dark">
                    <i class="bi bi-star-fill text-warning"></i> {{ shop.rating || '4.0' }}
                  </span>
                </td>
                <td class="text-end">
                  <div class="btn-group btn-group-sm">
                    <button 
                      v-if="!shop.is_primary" 
                      class="btn btn-outline-success" 
                      @click="makePrimary(shop.id)"
                      title="Set as Primary"
                      :disabled="settingPrimary"
                    >
                      <i class="bi bi-star"></i>
                    </button>
                    <button class="btn btn-gradient" @click="openShopModal(shop)" title="Edit">
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" @click="confirmDelete(shop.id)" title="Delete">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Shop Modal (create/edit) -->
    <Teleport to="body">
      <div v-if="showShopModal" class="modal-overlay" @click.self="closeShopModal()">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">
                <i :class="editingShop.id ? 'bi bi-pencil-square' : 'bi bi-plus-circle'" class="me-2"></i>
                {{ editingShop.id ? 'Edit Shop' : 'Create New Shop' }}
              </h5>
              <button type="button" class="btn-close" @click="closeShopModal()"></button>
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
                        <label class="form-label mb-0">Shop Location</label>
                        <small class="text-muted d-block">Click on map to pin location</small>
                      </div>
                      <button type="button" class="btn btn-sm btn-gradient d-flex align-items-center gap-2" @click="useCurrentLocation">
                        <i class="bi bi-geo-alt-fill"></i> Use Current Location
                      </button>
                    </div>

                    <div class="map-container-wrapper">
                      <div id="shop-map" class="shop-map-container"></div>
                      <div class="map-overlay-hint" v-if="!editingShop.latitude">
                        <span><i class="bi bi-geo-alt"></i> Click to set location</span>
                      </div>
                    </div>
                  </div>

                  <!-- Shop Images Section (only shown when editing existing shop) -->
                  <div v-if="editingShop.id" class="col-12 mt-4">
                    <div class="border rounded p-3">
                      <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                          <h6 class="mb-1">
                            <i class="bi bi-images me-2"></i>Shop Images
                          </h6>
                          <small class="text-muted">Upload up to 4 images to showcase your shop</small>
                        </div>
                        <span class="badge bg-secondary">{{ shopImages.length }}/4</span>
                      </div>

                      <!-- Loading state for images -->
                      <div v-if="loadingImages" class="text-center py-3">
                        <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
                        <span class="ms-2 text-muted">Loading images...</span>
                      </div>

                      <!-- Images Grid -->
                      <div v-else>
                        <div class="row g-2 mb-3">
                          <div v-for="(img, idx) in shopImages" :key="img.id" class="col-6 col-md-3">
                            <div class="position-relative shop-image-card">
                              <img 
                                :src="getImageUrl(img.url)" 
                                :alt="img.alt || `Shop image ${idx + 1}`"
                                class="img-fluid rounded"
                                style="height: 120px; width: 100%; object-fit: cover;"
                              />
                              <!-- Primary badge -->
                              <span v-if="idx === 0" class="position-absolute top-0 start-0 badge bg-primary m-1" style="font-size: 0.65rem;">
                                <i class="bi bi-star-fill me-1"></i>Primary
                              </span>
                              <!-- Actions overlay -->
                              <div class="position-absolute bottom-0 end-0 p-1">
                                <button 
                                  v-if="idx !== 0"
                                  type="button"
                                  class="btn btn-sm btn-light me-1" 
                                  @click.prevent="makePrimaryImage(img.id)"
                                  :disabled="imageActionLoading"
                                  title="Set as primary"
                                >
                                  <i class="bi bi-star"></i>
                                </button>
                                <button 
                                  type="button"
                                  class="btn btn-sm btn-danger" 
                                  @click.prevent="removeShopImage(img.id)"
                                  :disabled="imageActionLoading"
                                  title="Delete image"
                                >
                                  <i class="bi bi-trash"></i>
                                </button>
                              </div>
                            </div>
                          </div>

                          <!-- Upload placeholder -->
                          <div v-if="shopImages.length < 4" class="col-6 col-md-3">
                            <label 
                              class="d-flex flex-column align-items-center justify-content-center border border-dashed rounded text-muted"
                              style="height: 120px; cursor: pointer; background: #f8f9fa;"
                              :class="{ 'opacity-50': uploadingImages }"
                            >
                              <input 
                                type="file" 
                                accept="image/jpeg,image/png,image/webp,image/gif"
                                multiple
                                class="d-none"
                                @change="handleImageUpload"
                                :disabled="uploadingImages"
                              />
                              <span v-if="uploadingImages">
                                <span class="spinner-border spinner-border-sm" role="status"></span>
                              </span>
                              <span v-else>
                                <i class="bi bi-plus-lg fs-4"></i>
                                <small class="d-block mt-1">Add Image</small>
                              </span>
                            </label>
                          </div>
                        </div>

                        <!-- Empty state -->
                        <div v-if="shopImages.length === 0" class="text-center py-3 text-muted">
                          <i class="bi bi-images fs-2 d-block mb-2 opacity-50"></i>
                          <p class="mb-1">No images uploaded yet</p>
                          <small>Click the + button above to add images</small>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="modal-footer mt-4">
                  <button type="button" class="btn btn-outline-secondary" @click="closeShopModal()">Cancel</button>
                  <button type="submit" :disabled="shopSaving" class="btn btn-gradient">
                    <span v-if="shopSaving" class="spinner-border spinner-border-sm me-2"></span>
                    <i v-else class="bi bi-check-lg me-1"></i>
                    {{ editingShop.id ? 'Save Changes' : 'Create Shop' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Confirmation Modal -->
    <Teleport to="body">
      <div v-if="showConfirmModal" class="modal-overlay" @click.self="closeConfirmModal">
        <div class="modal-dialog modal-sm">
          <div class="modal-content">
            <div class="modal-header" :class="confirmModalType === 'danger' ? 'bg-danger-subtle' : 'bg-warning-subtle'">
              <h5 class="modal-title d-flex align-items-center">
                <i :class="confirmModalType === 'danger' ? 'bi bi-exclamation-triangle-fill text-danger' : 'bi bi-exclamation-circle-fill text-warning'" class="me-2"></i>
                {{ confirmModalTitle }}
              </h5>
              <button type="button" class="btn-close" @click="closeConfirmModal"></button>
            </div>
            <div class="modal-body">
              <p class="mb-0">{{ confirmModalMessage }}</p>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline-secondary" @click="closeConfirmModal">Cancel</button>
              <button class="btn" :class="confirmModalType === 'danger' ? 'btn-danger' : 'btn-warning'" @click="executeConfirmAction">
                <i class="bi bi-check-lg me-1"></i>Confirm
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

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
import { ref, computed, onMounted, nextTick } from 'vue';
import { getProfile, updateProfile, setPrimaryShop } from '@/api/apiProfile';
import { getMyShops, createShop, updateShop, deleteShop, getShopImages, uploadShopImages, deleteShopImage, setShopPrimaryImage } from '@/api/apiShop';

// Confirmation Modal State
const showConfirmModal = ref(false);
const confirmModalTitle = ref('');
const confirmModalMessage = ref('');
const confirmModalAction = ref(null);
const confirmModalType = ref('danger');

const openConfirmModal = (title, message, action, type = 'danger') => {
  confirmModalTitle.value = title;
  confirmModalMessage.value = message;
  confirmModalAction.value = action;
  confirmModalType.value = type;
  showConfirmModal.value = true;
};

const closeConfirmModal = () => {
  showConfirmModal.value = false;
  confirmModalAction.value = null;
};

const executeConfirmAction = () => {
  if (confirmModalAction.value) {
    confirmModalAction.value();
  }
  closeConfirmModal();
};

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
const settingPrimary = ref(false);

// Computed: get primary shop from shops list or profile
const primaryShop = computed(() => {
  // First check if we have shops loaded with is_primary flag
  const primary = shops.value.find(s => s.is_primary);
  if (primary) return primary;
  
  // Fallback to profile.shop (for backward compatibility)
  if (profile.value.shop) return profile.value.shop;
  
  // If we have shops but none marked primary, use first one
  if (shops.value.length > 0) return shops.value[0];
  
  return null;
});

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

// ---------- shop images state ----------
const shopImages = ref([]);
const loadingImages = ref(false);
const uploadingImages = ref(false);
const imageActionLoading = ref(false);

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001';

function getImageUrl(url) {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  // Handle relative URLs from backend
  return `${API_BASE}${url}`;
}

async function fetchShopImages(shopId) {
  if (!shopId) {
    shopImages.value = [];
    return;
  }
  loadingImages.value = true;
  try {
    const res = await getShopImages(shopId);
    if (res?.data?.status === 'success') {
      shopImages.value = res.data.images || [];
    } else {
      shopImages.value = [];
    }
  } catch (err) {
    console.error('Error fetching shop images:', err);
    shopImages.value = [];
  } finally {
    loadingImages.value = false;
  }
}

async function handleImageUpload(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  
  const shopId = editingShop.value.id;
  if (!shopId) {
    showToastMessage('Please save the shop first', 'bi bi-exclamation-circle-fill');
    return;
  }

  // Validate remaining slots
  const remainingSlots = 4 - shopImages.value.length;
  if (files.length > remainingSlots) {
    showToastMessage(`Only ${remainingSlots} slot(s) remaining`, 'bi bi-exclamation-circle-fill');
    event.target.value = '';
    return;
  }

  uploadingImages.value = true;
  try {
    const res = await uploadShopImages(shopId, files);
    if (res?.data?.status === 'success') {
      shopImages.value = res.data.images || [];
      showToastMessage(res.data.message || 'Images uploaded!', 'bi bi-check-circle-fill');
    } else {
      showToastMessage(res?.data?.message || 'Upload failed', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('Error uploading images:', err);
    showToastMessage(err?.response?.data?.message || 'Upload failed', 'bi bi-exclamation-circle-fill');
  } finally {
    uploadingImages.value = false;
    event.target.value = '';
  }
}

async function removeShopImage(imageId) {
  const shopId = editingShop.value.id;
  if (!shopId || !imageId) return;
  
  openConfirmModal(
    'Delete Image',
    'Are you sure you want to delete this image?',
    async () => {
      imageActionLoading.value = true;
      try {
        const res = await deleteShopImage(shopId, imageId);
        if (res?.data?.status === 'success') {
          shopImages.value = res.data.images || [];
          showToastMessage('Image deleted', 'bi bi-check-circle-fill');
        } else {
          showToastMessage(res?.data?.message || 'Failed to delete', 'bi bi-exclamation-circle-fill');
        }
      } catch (err) {
        console.error('Error deleting image:', err);
        showToastMessage('Failed to delete image', 'bi bi-exclamation-circle-fill');
      } finally {
        imageActionLoading.value = false;
      }
    }
  );
}

async function makePrimaryImage(imageId) {
  const shopId = editingShop.value.id;
  if (!shopId || !imageId) return;
  
  imageActionLoading.value = true;
  try {
    const res = await setShopPrimaryImage(shopId, imageId);
    if (res?.data?.status === 'success') {
      shopImages.value = res.data.images || [];
      showToastMessage('Primary image updated', 'bi bi-check-circle-fill');
    } else {
      showToastMessage(res?.data?.message || 'Failed to set primary', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('Error setting primary image:', err);
    showToastMessage('Failed to set primary image', 'bi bi-exclamation-circle-fill');
  } finally {
    imageActionLoading.value = false;
  }
}

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
    setMapMarker(clickedLat, clickedLng, false);
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
  if (markerRef.value && mapRef.value) {
    mapRef.value.removeLayer(markerRef.value);
    markerRef.value = null;
  }
  if (mapRef.value) {
    mapRef.value.setView([DEFAULT_COORDS.lat, DEFAULT_COORDS.lon], 6);
  }
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
  // Check if we're on HTTPS (required for geolocation in most browsers)
  if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    showToastMessage('Location requires HTTPS. Use the map instead.', 'bi bi-exclamation-circle-fill');
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
    let errorMsg = 'Failed to get location';
    if (err.code === 1) errorMsg = 'Location permission denied';
    else if (err.code === 2) errorMsg = 'Location unavailable';
    else if (err.code === 3) errorMsg = 'Location request timed out';
    showToastMessage(errorMsg, 'bi bi-exclamation-circle-fill');
  }, { timeout: 10000, enableHighAccuracy: true });
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
    openConfirmModal(
      'Discard Changes',
      'You have unsaved changes. Discard them?',
      () => {
        editMode.value = false;
        editForm.value = {};
      }
    );
  } else {
    editMode.value = false;
    editForm.value = {};
  }
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
    if (res && res.data && res.data.shops) {
      shops.value = res.data.shops;
    } else {
      shops.value = Array.isArray(res?.data) ? res.data : [];
    }
    
    // Sync is_primary flag from profile data
    if (profile.value.primary_shop_id) {
      shops.value = shops.value.map(s => ({
        ...s,
        is_primary: s.id === profile.value.primary_shop_id
      }));
    } else if (shops.value.length > 0 && !shops.value.some(s => s.is_primary)) {
      // If no primary set, mark first shop as primary (UI only)
      shops.value[0].is_primary = true;
    }
  } catch (err) {
    console.error('[Shops Error]', err);
    showToastMessage('Failed to load shops', 'bi bi-exclamation-circle-fill');
  } finally {
    loadingShops.value = false;
  }
};

// Set a shop as primary
const makePrimary = async (shopId) => {
  settingPrimary.value = true;
  try {
    const res = await setPrimaryShop(shopId);
    if (res?.data?.status === 'success') {
      // Update local state
      shops.value = shops.value.map(s => ({
        ...s,
        is_primary: s.id === shopId
      }));
      profile.value.primary_shop_id = shopId;
      showToastMessage(res.data.message || 'Primary shop updated!', 'bi bi-check-circle-fill');
    } else {
      showToastMessage(res?.data?.message || 'Failed to set primary shop', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('[Set Primary Error]', err);
    showToastMessage(err?.response?.data?.message || 'Failed to set primary shop', 'bi bi-exclamation-circle-fill');
  } finally {
    settingPrimary.value = false;
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
    // Fetch shop images when editing existing shop
    fetchShopImages(shop.id);
  } else {
    editingShop.value = {
      id: null, name: '', description: '', address: '', location: '', city: '', state: '',
      contact: '', gstin: '', latitude: null, longitude: null, image: null
    };
    shopImages.value = []; // Clear images for new shop
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
  // Destroy the map so it can be re-initialized when modal reopens
  destroyMap();
}

function destroyMap() {
  if (markerRef.value) {
    markerRef.value = null;
  }
  if (mapRef.value) {
    mapRef.value.remove();
    mapRef.value = null;
  }
  mapInitialized.value = false;
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
  openConfirmModal(
    'Delete Shop',
    'Delete this shop? This action is permanent.',
    () => deleteShopById(shopId)
  );
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

// ---------- lifecycle ----------
onMounted(() => {
  fetchProfile();
  fetchShops();
});
</script>

<style scoped>
/* ===== Page Layout ===== */
.shop-profile-tab {
  background: var(--gradient-bg);
  min-height: calc(100vh - 60px);
  padding: 2rem;
  padding-bottom: 4rem;
}

.fade-in-entry {
  animation: fadeInPage 0.5s ease-out forwards;
}

@keyframes fadeInPage {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ===== Page Header ===== */
.page-header {
  margin-bottom: 1.5rem;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: var(--gradient-primary);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.header-icon-sm {
  width: 40px;
  height: 40px;
  background: var(--gradient-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.page-title {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  font-size: 1.5rem;
  margin: 0;
}

.page-subtitle {
  font-size: 0.9rem;
}

/* ===== Section Headers ===== */
.section-header {
  padding: 0.5rem 0;
}

.section-title {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  font-size: 1.1rem;
}

/* ===== Cards ===== */
.card {
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}

.card-header {
  background: rgba(248, 250, 252, 0.8);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding: 1rem 1.25rem;
  border-radius: 16px 16px 0 0 !important;
}

.profile-card .card-body {
  padding: 1.5rem;
}

.primary-shop-card {
  border: 2px solid var(--color-primary) !important;
}

.primary-shop-card .card-header {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
}

/* ===== Profile Fields ===== */
.profile-field {
  padding: 1rem;
  background: rgba(248, 250, 252, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  transition: all 0.3s ease;
  height: 100%;
}

.profile-field:hover {
  background: rgba(248, 250, 252, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.profile-field label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.profile-field p {
  margin-bottom: 0;
  color: var(--color-text-dark);
}

/* ===== Form Elements ===== */
.form-control, .form-select {
  border-radius: 8px;
  border: 1.5px solid #dee2e6;
  transition: all 0.3s ease;
  padding: 0.6rem 0.875rem;
}

.form-control:focus, .form-select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 0.2rem rgba(59, 130, 246, 0.15);
}

.form-label {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-text-dark);
  margin-bottom: 0.4rem;
}

/* ===== Buttons ===== */
.btn-gradient {
  background: var(--gradient-primary);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-gradient:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
  color: white;
}

.btn-gradient:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
  color: white;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-outline-secondary {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-outline-secondary:hover {
  transform: translateY(-1px);
}

/* ===== Table Styles ===== */
.shops-table-card .table {
  margin-bottom: 0;
}

.shops-table-card .table th {
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  color: var(--color-text-muted);
  border-bottom: 2px solid rgba(0, 0, 0, 0.05);
  padding: 0.875rem 0.75rem;
}

.shops-table-card .table td {
  padding: 0.875rem 0.75rem;
  vertical-align: middle;
}

.shops-table-card .table tbody tr {
  transition: background-color 0.2s ease;
}

.shops-table-card .table tbody tr:hover {
  background-color: rgba(59, 130, 246, 0.03);
}

/* ===== Modal Overlay ===== */
.modal-overlay {
  position: fixed;
  z-index: 9999;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-dialog {
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  animation: slideUp 0.3s ease;
}

.modal-dialog.modal-sm {
  max-width: 420px;
}

.modal-dialog.modal-lg {
  max-width: 900px;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-content {
  border-radius: 16px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: #f8fafc;
  flex-shrink: 0;
}

.modal-header .modal-title {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--color-text-dark);
  margin: 0;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
  background: #ffffff;
}

.modal-footer {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: #f8fafc;
  flex-shrink: 0;
}

/* Map Styles */
.map-container-wrapper {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid var(--color-border);
  transition: border-color 0.2s ease;
}

.map-container-wrapper:hover {
  border-color: var(--color-primary);
}

.shop-map-container {
  height: 350px;
  width: 100%;
  background: #f1f5f9;
}

.map-overlay-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.9);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  pointer-events: none;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Form Improvements */
.form-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-text-dark);
  margin-bottom: 0.5rem;
}

.form-control {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.form-control:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.shop-image-card {
  transition: transform 0.2s ease;
}

.shop-image-card:hover {
  transform: translateY(-2px);
}

/* ===== Toast Notification ===== */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: white;
  color: var(--color-text-dark);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  animation: toastSlide 0.3s ease;
  display: flex;
  align-items: center;
  border-left: 4px solid var(--color-primary);
}

@keyframes toastSlide {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* ===== Shop Images ===== */
.shop-image-card {
  border: 1px solid #dee2e6;
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.shop-image-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.shop-image-card .btn-sm {
  padding: 0.2rem 0.4rem;
  font-size: 0.7rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.shop-image-card:hover .btn-sm {
  opacity: 1;
}

.border-dashed {
  border-style: dashed !important;
  border-width: 2px !important;
  transition: all 0.2s ease;
}

.border-dashed:hover {
  border-color: var(--color-primary) !important;
  background: rgba(59, 130, 246, 0.05) !important;
}

/* ===== Utility Classes ===== */
.bg-danger-subtle {
  background-color: rgba(239, 68, 68, 0.1) !important;
}

.bg-warning-subtle {
  background-color: rgba(245, 158, 11, 0.1) !important;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .shop-profile-tab {
    padding: 1rem;
  }

  .page-title {
    font-size: 1.25rem;
  }

  .header-icon {
    width: 48px;
    height: 48px;
    font-size: 1.25rem;
  }

  .modal-dialog {
    margin: 0.5rem;
    max-height: 95vh;
  }

  .modal-body {
    padding: 1rem;
  }

  .profile-field {
    padding: 0.75rem;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 1rem;
  }
}
</style>

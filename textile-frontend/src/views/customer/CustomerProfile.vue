<template>
  <div class="customer-profile-tab fade-in-entry">
    <h5 class="mb-4">
      <i class="bi bi-person-circle me-2"></i>My Profile
    </h5>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
      <p class="mt-2 text-muted">Loading profile...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    </div>

    <!-- Profile Card -->
    <div v-else class="card">
      <div class="card-body">
        <!-- View Mode -->
        <div v-if="!editMode">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h6 class="mb-0">Profile Information</h6>
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
                <label class="text-muted small">Email</label>
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
                <label class="text-muted small">Role</label>
                <p class="fw-semibold text-capitalize">
                  <span class="badge bg-primary">{{ profile.role || 'N/A' }}</span>
                </p>
              </div>
            </div>

            <div class="col-12">
              <div class="profile-field">
                <label class="text-muted small">Address</label>
                <p class="fw-semibold">{{ profile.address || 'N/A' }}</p>
              </div>
            </div>

            <div v-if="profile.shop_name" class="col-md-6">
              <div class="profile-field">
                <label class="text-muted small">Shop Name</label>
                <p class="fw-semibold">{{ profile.shop_name }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Edit Mode -->
        <div v-else>
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h6 class="mb-0">Edit Profile</h6>
            <button class="btn btn-outline-secondary" @click="cancelEdit">
              <i class="bi bi-x me-1"></i>Cancel
            </button>
          </div>

          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Full Name *</label>
              <input
                type="text"
                class="form-control"
                v-model="editForm.full_name"
                required
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Email *</label>
              <input
                type="email"
                class="form-control"
                v-model="editForm.email"
                required
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Contact Number</label>
              <input
                type="tel"
                class="form-control"
                v-model="editForm.contact"
                placeholder="+91 XXXXXXXXXX"
              />
            </div>

            <div class="col-md-6">
              <label class="form-label">Role</label>
              <input
                type="text"
                class="form-control"
                :value="profile.role"
                disabled
                readonly
              />
              <small class="text-muted">Role cannot be changed</small>
            </div>

            <div class="col-12">
              <label class="form-label">Address</label>
              <textarea
                class="form-control"
                v-model="editForm.address"
                rows="3"
                placeholder="Enter your complete address"
              ></textarea>
            </div>

            <div class="col-12">
              <button
                class="btn btn-primary me-2"
                @click="saveProfile"
                :disabled="saving"
              >
                <span v-if="saving">
                  <span class="spinner-border spinner-border-sm me-2"></span>
                  Saving...
                </span>
                <span v-else>
                  <i class="bi bi-check me-1"></i>Save Changes
                </span>
              </button>
              <button class="btn btn-outline-secondary" @click="cancelEdit">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="showToast" class="toast-notification">
      <i :class="toastIcon" class="me-2"></i>
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getProfile, updateProfile } from '@/api/apiProfile';

const loading = ref(false);
const error = ref('');
const profile = ref({});
const editMode = ref(false);
const editForm = ref({});
const saving = ref(false);

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

/**
 * Fetch user profile
 */
const fetchProfile = async () => {
  loading.value = true;
  error.value = '';

  try {
    const response = await getProfile();
    if (response.data && response.data.status === 'success') {
      profile.value = response.data.profile || {};
    } else {
      error.value = response.data?.message || 'Failed to load profile';
    }
  } catch (err) {
    console.error('[Profile Error]', err);
    error.value = err.response?.data?.message || 'Failed to load profile';
  } finally {
    loading.value = false;
  }
};

/**
 * Enable edit mode
 */
const enableEditMode = () => {
  editForm.value = {
    full_name: profile.value.full_name || '',
    email: profile.value.email || '',
    contact: profile.value.contact || '',
    address: profile.value.address || ''
  };
  editMode.value = true;
};

/**
 * Cancel edit
 */
const cancelEdit = () => {
  editMode.value = false;
  editForm.value = {};
};

/**
 * Save profile
 */
const saveProfile = async () => {
  // Basic validation
  if (!editForm.value.full_name || !editForm.value.email) {
    showToastMessage('Name and email are required', 'bi bi-exclamation-circle-fill');
    return;
  }

  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(editForm.value.email)) {
    showToastMessage('Please enter a valid email', 'bi bi-exclamation-circle-fill');
    return;
  }

  saving.value = true;

  try {
    const response = await updateProfile(editForm.value);
    if (response.data && response.data.status === 'success') {
      // Refetch profile to get updated data
      await fetchProfile();
      editMode.value = false;
      showToastMessage('Profile updated successfully!', 'bi bi-check-circle-fill');
    } else {
      showToastMessage(response.data?.message || 'Failed to update profile', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('[Update Error]', err);
    showToastMessage(
      err.response?.data?.message || 'Failed to update profile',
      'bi bi-exclamation-circle-fill'
    );
  } finally {
    saving.value = false;
  }
};

/**
 * Show toast message
 */
const showToastMessage = (message, icon) => {
  toastMessage.value = message;
  toastIcon.value = icon;
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

// Fetch profile on mount
onMounted(() => {
  fetchProfile();
});
</script>

<style scoped>
.customer-profile-tab {
  background: transparent;
  min-height: calc(100vh - 60px);
  padding: 2rem;
  padding-bottom: 4rem;
}

.fade-in-entry {
  animation: fadeInPage 0.6s ease-out forwards;
}

@keyframes fadeInPage {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h5, h6 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.card {
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.profile-field {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.profile-field:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.profile-field label {
  display: block;
  margin-bottom: 0.25rem;
}

.profile-field p {
  margin-bottom: 0;
}

.form-control,
.form-select {
  border-radius: 8px;
  border: 1.5px solid #dee2e6;
  transition: all 0.3s ease;
}

.form-control:focus,
.form-select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 0.25rem rgba(74, 144, 226, 0.15);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.35);
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
}

.btn-outline-secondary {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.toast-notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  z-index: 1100;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>

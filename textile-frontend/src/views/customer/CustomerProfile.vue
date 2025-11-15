<template>
  <div class="customer-profile-page">
    <div class="row">
      <!-- User Profile Section -->
      <div class="col-md-6">
        <div class="card">
          <div class="card-body">
            <div class="d-flex align-items-start mb-4">
              <div
                class="profile-avatar bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3"
                style="width: 80px; height: 80px; font-size: 2rem;"
              >
                <i class="bi bi-person-circle"></i>
              </div>
              <div class="flex-grow-1">
                <h5 class="mb-1">{{ profileData.name }}</h5>
                <p v-if="profileData.contact" class="text-muted mb-0 small">
                  {{ profileData.contact }}
                </p>
                <p v-if="profileData.email" class="text-muted mb-0 small">
                  {{ profileData.email }}
                </p>
                <p v-if="profileData.address" class="text-muted mb-0 small">
                  {{ profileData.address }}
                </p>
                <button class="btn btn-sm btn-primary mt-2" @click="enableEdit">
                  Edit Profile
                </button>
              </div>
            </div>

            <!-- Feedback messages -->
            <div v-if="errorMsg" class="alert alert-danger mt-3">{{ errorMsg }}</div>
            <div v-if="successMsg" class="alert alert-success mt-3">{{ successMsg }}</div>

            <!-- Edit Form -->
            <div v-if="isEditing" class="edit-form">
              <h6 class="mb-3">Edit Profile Information</h6>
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label small">Full name</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="editForm.fullName"
                    :disabled="saving"
                  />
                </div>
                <div class="col-md-6">
                  <label class="form-label small">Username</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="editForm.username"
                    :disabled="saving"
                  />
                </div>

                <!-- Contact -->
                <div class="col-md-6">
                  <label class="form-label small">Contact</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="editForm.contact"
                    :disabled="saving"
                    placeholder="+91 98765 43210"
                  />
                </div>

                <!-- Email -->
                <div class="col-md-6">
                  <label class="form-label small">Email</label>
                  <input
                    type="email"
                    class="form-control"
                    v-model="editForm.email"
                    :disabled="saving"
                    placeholder="you@example.com"
                  />
                </div>

                <!-- Address -->
                <div class="col-md-6">
                  <label class="form-label small">Address</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="editForm.address"
                    :disabled="saving"
                    placeholder="Street, Building, Apt"
                  />
                </div>

                <!-- City -->
                <div class="col-md-6">
                  <label class="form-label small">City</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="editForm.city"
                    :disabled="saving"
                    placeholder="City name"
                  />
                </div>
              </div>

              <div class="text-center mt-4">
                <button
                  class="btn btn-primary me-2"
                  @click="updateProfile"
                  :disabled="saving"
                >
                  <span v-if="!saving">Update</span>
                  <span v-else>Saving...</span>
                </button>
                <button class="btn btn-outline-secondary" @click="cancelEdit" :disabled="saving">
                  Cancel
                </button>
              </div>
            </div>
            <!-- end edit form -->
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import api from "@/api/axios"; // your single axios instance

// UI state
const isEditing = ref(false);
const saving = ref(false);
const errorMsg = ref("");
const successMsg = ref("");

// Profile reactive model (what UI displays)
const profileData = reactive({
  id: null,
  name: "User Name",
  username: "username",
  contact: "",
  email: "",
  address: "",
  city: ""
});

// Edit form (local copy while editing)
const editForm = reactive({
  fullName: "",
  username: "",
  contact: "",
  email: "",
  address: "",
  city: ""
});

// Load profile from localStorage.user (fallback to defaults)
function loadFromLocalStorage() {
  try {
    const raw = localStorage.getItem("user");
    if (!raw) return;
    const u = JSON.parse(raw);

    // Map backend user fields to our UI fields.
    profileData.id = u.id ?? u.user_id ?? profileData.id;
    profileData.name = u.full_name || u.fullName || u.name || profileData.name;
    profileData.username = u.username || profileData.username;

    // semantic mapping: try multiple common field names
    profileData.contact = u.contact || u.phone || u.mobile || "";
    profileData.email = u.email || "";
    profileData.address = u.address || "";
    profileData.city = u.city || "";

    // initialize edit form with same values
    Object.assign(editForm, {
      fullName: profileData.name,
      username: profileData.username,
      contact: profileData.contact,
      email: profileData.email,
      address: profileData.address,
      city: profileData.city
    });
  } catch (e) {
    console.warn("Failed to parse local user", e);
  }
}

onMounted(() => {
  loadFromLocalStorage();
});

// enable editing
const enableEdit = () => {
  errorMsg.value = "";
  successMsg.value = "";
  // ensure edit form is current
  editForm.fullName = profileData.name;
  editForm.username = profileData.username;
  editForm.contact = profileData.contact;
  editForm.email = profileData.email;
  editForm.address = profileData.address;
  editForm.city = profileData.city;
  isEditing.value = true;
};

// cancel edits
const cancelEdit = () => {
  errorMsg.value = "";
  successMsg.value = "";
  isEditing.value = false;
};

// update profile — frontend only changes + backend PUT
const updateProfile = async () => {
  errorMsg.value = "";
  successMsg.value = "";

  // basic validations
  if (!editForm.fullName || editForm.fullName.trim() === "") {
    errorMsg.value = "Full name is required.";
    return;
  }
  if (!editForm.username || editForm.username.trim() === "") {
    errorMsg.value = "Username is required.";
    return;
  }
  if (editForm.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.email)) {
    errorMsg.value = "Please enter a valid email address.";
    return;
  }

  // prepare payload — only send fields you want to update
  const payload = {
    full_name: editForm.fullName,
    username: editForm.username,
    contact: editForm.contact || null,
    email: editForm.email || null,
    address: editForm.address || null,
    city: editForm.city || null
  };

  // If we don't know the user id, abort with helpful message
  const userId = profileData.id;
  if (!userId) {
    errorMsg.value = "No user id available. Please login again.";
    return;
  }

  saving.value = true;
  try {
    // NOTE: change this URL if your backend uses different path or PATCH vs PUT
    const url = `/users/${userId}`; // resolves to baseURL + /users/:id
    const resp = await api.put(url, payload);
    const data = resp?.data;

    if (!data) {
      throw new Error("No response from server");
    }

    // If backend returns an error structure, surface message
    if (data.status && data.status !== "success") {
      throw new Error(data.message || "Update failed");
    }

    // If backend returned updated user, use it. Else update fields locally from payload.
    const updatedUser = data.user || data.data || null;

    if (updatedUser) {
      profileData.name = updatedUser.full_name || updatedUser.name || editForm.fullName;
      profileData.username = updatedUser.username || editForm.username;
      profileData.contact = updatedUser.contact || editForm.contact;
      profileData.email = updatedUser.email || editForm.email;
      profileData.address = updatedUser.address || editForm.address;
      profileData.city = updatedUser.city || editForm.city;

      // save updated whole user object to localStorage if backend gave it
      try {
        localStorage.setItem("user", JSON.stringify(updatedUser));
      } catch (e) {
        // ignore storage errors
      }
    } else {
      // fallback: optimistic update from editForm
      profileData.name = editForm.fullName;
      profileData.username = editForm.username;
      profileData.contact = editForm.contact;
      profileData.email = editForm.email;
      profileData.address = editForm.address;
      profileData.city = editForm.city;

      // patch localStorage.user minimal fields so UI elsewhere stays consistent
      try {
        const raw = localStorage.getItem("user");
        const rawObj = raw ? JSON.parse(raw) : {};
        rawObj.full_name = profileData.name;
        rawObj.username = profileData.username;
        rawObj.contact = profileData.contact;
        rawObj.email = profileData.email;
        rawObj.address = profileData.address;
        rawObj.city = profileData.city;
        localStorage.setItem("user", JSON.stringify(rawObj));
      } catch (e) {
        // ignore
      }
    }

    successMsg.value = "Profile updated successfully.";
    isEditing.value = false;
  } catch (err) {
    console.error("Profile update error:", err);
    // prefer API-provided message
    errorMsg.value =
      err?.response?.data?.message ||
      err?.message ||
      "Failed to update profile. Try again.";
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.customer-profile-page {
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* Card Styling */
.card {
  border: none;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  background: white;
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 50px rgba(102, 126, 234, 0.15);
}

.card-body {
  padding: 2rem;
}

/* Profile Avatar */
.profile-avatar {
  width: 100px;
  height: 100px;
  font-size: 3rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}

.profile-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 30px rgba(102, 126, 234, 0.5);
}

.shop-avatar {
  width: 80px;
  height: 80px;
  font-size: 2.5rem;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 8px 20px rgba(240, 147, 251, 0.3);
  flex-shrink: 0;
}

/* Profile Info */
.card-body h5 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.card-body p {
  color: #718096;
  font-size: 0.95rem;
  line-height: 1.6;
}

/* Edit Button */
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50px;
  padding: 0.6rem 1.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(102, 126, 234, 0.4);
}

/* Edit Form */
.edit-form {
  padding-top: 1.5rem;
  margin-top: 1.5rem;
  border-top: 2px solid #e2e8f0;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.edit-form h6 {
  font-weight: 700;
  color: #2d3748;
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

/* Form Labels and Inputs */
.form-label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #4a5568;
  font-size: 0.9rem;
}

.form-control {
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  outline: none;
}

/* Update and Cancel Buttons */
.btn-outline-secondary {
  border: 2px solid #cbd5e0;
  color: #4a5568;
  background: white;
  border-radius: 50px;
  padding: 0.6rem 1.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-outline-secondary:hover {
  background: #f7fafc;
  border-color: #a0aec0;
  color: #2d3748;
  transform: translateY(-2px);
}

/* Feedback Alerts */
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
  .customer-profile-page {
    padding: 1rem;
  }

  .card-body {
    padding: 1.5rem;
  }

  .profile-avatar {
    width: 80px;
    height: 80px;
    font-size: 2.5rem;
  }

  .shop-avatar {
    width: 60px;
    height: 60px;
    font-size: 2rem;
  }

  .edit-form {
    padding-top: 1rem;
    margin-top: 1rem;
  }
}

/* Smooth Transitions */
* {
  transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}
</style>

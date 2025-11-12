<template>
  <div class="customer-profile-page">
    <div class="row">
      <!-- User Profile Section -->
      <div class="col-md-6">
        <div class="card">
          <div class="card-body">
            <div class="d-flex align-items-start mb-4">
              <div class="profile-avatar bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 80px; height: 80px; font-size: 2rem;">
                <i class="bi bi-person-circle"></i>
              </div>
              <div class="flex-grow-1">
                <h5 class="mb-1">{{ profileData.name }}</h5>
                <p class="text-muted mb-0 small">{{ profileData.detail1 }}</p>
                <p class="text-muted mb-0 small">{{ profileData.detail2 }}</p>
                <p class="text-muted mb-0 small">{{ profileData.detail3 }}</p>
                <button class="btn btn-sm btn-primary mt-2" @click="enableEdit">Edit Profile</button>
              </div>
            </div>

            <!-- Edit Form -->
            <div v-if="isEditing" class="edit-form">
              <h6 class="mb-3">Edit Profile Information</h6>
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label small">Full name</label>
                  <input type="text" class="form-control" v-model="editForm.fullName">
                </div>
                <div class="col-md-6">
                  <label class="form-label small">Username</label>
                  <input type="text" class="form-control" v-model="editForm.username">
                </div>
                <div class="col-md-6">
                  <label class="form-label small">Detail 1</label>
                  <input type="text" class="form-control" v-model="editForm.detail1">
                </div>
                <div class="col-md-6">
                  <label class="form-label small">Detail 2</label>
                  <input type="text" class="form-control" v-model="editForm.detail2">
                </div>
                <div class="col-md-6">
                  <label class="form-label small">Detail 3</label>
                  <input type="text" class="form-control" v-model="editForm.detail3">
                </div>
                <div class="col-md-6">
                  <label class="form-label small">Detail 4</label>
                  <input type="text" class="form-control" v-model="editForm.detail4">
                </div>
              </div>
              
              <div class="text-center mt-4">
                <button class="btn btn-primary me-2" @click="updateProfile">Update</button>
                <button class="btn btn-outline-secondary" @click="cancelEdit">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const isEditing = ref(false)

const profileData = reactive({
  name: 'User Name',
  detail1: 'Detail 1',
  detail2: 'Detail 2',
  detail3: 'Detail 3'
})

const editForm = reactive({
  fullName: 'User Name',
  username: 'username',
  detail1: 'Detail 1',
  detail2: 'Detail 2',
  detail3: 'Detail 3',
  detail4: 'Detail 4'
})

const selectedShop = ref({
  name: 'Shop Name 03',
  rating: 4,
  address: '298/09 Block 63 Highway 98',
  contact: '+91 98675 54321',
  hours: 'Open Monday to Friday, 8AM To 8PM',
  products: [
    { id: 1, name: 'Product Name 01', rating: 4, description: 'Product Description...' },
    { id: 2, name: 'Product Name 02', rating: 4, description: 'Product Description...' }
  ]
})

const enableEdit = () => {
  isEditing.value = true
}

const updateProfile = () => {
  profileData.name = editForm.fullName
  profileData.detail1 = editForm.detail1
  profileData.detail2 = editForm.detail2
  profileData.detail3 = editForm.detail3
  isEditing.value = false
  alert('Profile updated successfully!')
}

const cancelEdit = () => {
  isEditing.value = false
}
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

/* Rating Stars */
.rating {
  font-size: 1.1rem;
}

.rating span {
  transition: transform 0.2s ease;
}

.rating span:hover {
  transform: scale(1.2);
}

/* Shop Profile Section */
.shop-profile-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  padding: 1.5rem;
  border-radius: 16px;
  border: 2px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.shop-profile-card h6 {
  font-weight: 700;
  color: #2d3748;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

/* Product Cards */
.product-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s ease;
  height: 100%;
}

.product-card:hover {
  border-color: #667eea;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
  transform: translateY(-3px);
}

.product-card h6 {
  font-weight: 600;
  color: #2d3748;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.product-card p {
  font-size: 0.85rem;
  color: #718096;
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

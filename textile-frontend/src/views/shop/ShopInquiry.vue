<template>
  <div class="shop-inquiry-tab">
    <h5 class="mb-3">
      <i class="bi bi-chat-dots me-2"></i>Distributor Inquiries & Fabric Analysis
    </h5>

    <!-- Inquiry Form Card -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">Submit Inquiry to Distributors</h6>
        
        <div class="mb-3">
          <label class="form-label">Search and Select Distributors</label>
          <div class="distributor-search">
            <div class="input-group">
              <input
                type="text"
                class="form-control"
                v-model="distributorSearch"
                @input="searchDistributors"
                placeholder="Type to search distributors by name, city, or state..."
              />
              <button class="btn btn-outline-secondary" type="button">
                <i class="bi bi-search"></i>
              </button>
            </div>
            
            <!-- Search Results Dropdown -->
            <div v-if="searchResults.length > 0 && showDropdown" class="search-dropdown">
              <div class="search-results">
                <div
                  v-for="distributor in searchResults"
                  :key="distributor.id"
                  class="search-result-item"
                  @click="addDistributor(distributor)"
                >
                  <div class="distributor-info">
                    <strong>{{ distributor.full_name }}</strong>
                    <small class="text-muted d-block">{{ distributor.city }}, {{ distributor.state }}</small>
                    <small class="text-muted">{{ distributor.email }}</small>
                  </div>
                  <button class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-plus"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Selected Distributors -->
        <div v-if="selectedDistributors.length > 0" class="mb-3">
          <label class="form-label">Selected Distributors</label>
          <div class="selected-distributors">
            <div
              v-for="(dist, index) in selectedDistributors"
              :key="dist.id"
              class="distributor-chip"
              :class="{ 'favorite': dist.isFavorite }"
              @click="toggleFavorite(dist)"
            >
              <i class="bi bi-star-fill" v-if="dist.isFavorite"></i>
              <i class="bi bi-person" v-else></i>
              {{ dist.full_name }}
              <button
                class="btn-close btn-close-sm ms-2"
                @click.stop="removeDistributor(index)"
              ></button>
            </div>
          </div>
          <small class="text-muted">Click the star icon to mark as favorite</small>
        </div>

        <div class="mb-3">
          <label class="form-label">Your Message</label>
          <textarea
            class="form-control"
            v-model="inquiryForm.message"
            rows="4"
            placeholder="Enter your inquiry message..."
            required
          ></textarea>
        </div>

        <div class="mb-3">
          <label class="form-label">Upload Fabric Image (Optional)</label>
          <p class="small text-muted mb-2">
            Upload a fabric image to send directly to distributors for review
          </p>
          <div class="upload-zone" @click="$refs.imageInput.click()">
            <div v-if="!inquiryForm.image" class="text-center">
              <i class="bi bi-image fs-1 text-muted mb-2"></i>
              <p class="mb-0">Click to upload fabric image</p>
              <small class="text-muted">JPG, PNG, WEBP (max 16MB)</small>
            </div>
            <div v-else class="text-center">
              <img
                :src="imagePreview"
                alt="Fabric preview"
                class="img-fluid rounded mb-2"
                style="max-height: 200px"
              />
              <p class="mb-0">{{ inquiryForm.image.name }}</p>
              <button
                class="btn btn-sm btn-outline-danger mt-2"
                @click.stop="removeImage"
              >
                <i class="bi bi-trash"></i> Remove
              </button>
            </div>
          </div>
          <input
            type="file"
            ref="imageInput"
            accept="image/*"
            @change="handleImageUpload"
            class="d-none"
          />
        </div>

        <button
          class="btn btn-primary w-100"
          @click="submitInquiry"
          :disabled="submitting || selectedDistributors.length === 0 || !inquiryForm.message"
        >
          <span v-if="submitting">
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
          </span>
          <span v-else>
            <i class="bi bi-send me-2"></i>Send Inquiry to {{ selectedDistributors.length }} Distributor(s)
          </span>
        </button>
      </div>
    </div>

    <!-- Inquiry History -->
    <div class="card">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h6 class="mb-0">Your Inquiry History</h6>
          <button
            class="btn btn-sm btn-outline-primary"
            @click="fetchInquiryHistory"
            :disabled="loadingHistory"
          >
            <i class="bi bi-arrow-clockwise me-1"></i>Refresh
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loadingHistory" class="text-center py-4">
          <div class="spinner-border text-primary"></div>
          <p class="mt-2 text-muted">Loading inquiries...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="historyError" class="alert alert-danger">
          <i class="bi bi-exclamation-triangle me-2"></i>{{ historyError }}
        </div>

        <!-- Empty State -->
        <div v-else-if="inquiryHistory.length === 0" class="text-center py-4 text-muted">
          <i class="bi bi-inbox fs-1 d-block mb-2"></i>
          <p>No inquiries yet. Submit your first inquiry above!</p>
        </div>

        <!-- History List -->
        <div v-else class="inquiry-list">
          <div
            v-for="(inquiry, idx) in inquiryHistory"
            :key="idx"
            class="inquiry-item p-3 mb-3 border rounded"
          >
            <div class="d-flex justify-content-between align-items-start mb-2">
              <div>
                <strong>Shop ID: {{ inquiry.shop_id }}</strong>
                <small class="d-block text-muted">
                  {{ formatDate(inquiry.timestamp) }}
                </small>
              </div>
              <span class="badge bg-primary">{{ inquiry.status || 'Submitted' }}</span>
            </div>
            <p class="mb-0">{{ inquiry.message }}</p>
            <div v-if="inquiry.fabric_analysis" class="mt-2 p-2 bg-light rounded">
              <small class="fw-bold">AI Analysis:</small>
              <small class="d-block">{{ inquiry.fabric_analysis.fabric_name }} - {{ inquiry.fabric_analysis.material }}</small>
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
import { ref, onMounted, onUnmounted } from 'vue';
import { getDistributors } from '@/api/apiShop';
import { submitInquiry as submitInquiryAPI, getInquiryHistory } from '@/api/apiInquiry';

// Form data
const inquiryForm = ref({
  message: '',
  image: null
});

// Distributor search
const distributorSearch = ref('');
const searchResults = ref([]);
const selectedDistributors = ref([]);
const showDropdown = ref(false);
const favoriteDistributors = ref([]);

// Loading states
const submitting = ref(false);
const imagePreview = ref('');

// Inquiry history
const inquiryHistory = ref([]);
const loadingHistory = ref(false);
const historyError = ref('');

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

/**
 * Search distributors with debouncing
 */
let searchTimeout;
const searchDistributors = () => {
  clearTimeout(searchTimeout);
  const query = distributorSearch.value.trim();
  
  if (query.length < 2) {
    searchResults.value = [];
    showDropdown.value = false;
    return;
  }
  
  searchTimeout = setTimeout(async () => {
    try {
      const response = await getDistributors(query);
      if (response.data && response.data.status === 'success') {
        // Filter out already selected distributors
        searchResults.value = response.data.data.filter(
          dist => !selectedDistributors.value.find(selected => selected.id === dist.id)
        );
        showDropdown.value = searchResults.value.length > 0;
      }
    } catch (err) {
      console.error('[Search Error]', err);
      searchResults.value = [];
    }
  }, 300);
};

/**
 * Add distributor to selected list
 */
const addDistributor = (distributor) => {
  // Check if already selected
  if (selectedDistributors.value.find(d => d.id === distributor.id)) {
    return;
  }
  
  // Add with favorite status
  const isFavorite = favoriteDistributors.value.includes(distributor.id);
  selectedDistributors.value.push({
    ...distributor,
    isFavorite
  });
  
  // Clear search
  distributorSearch.value = '';
  searchResults.value = [];
  showDropdown.value = false;
};

/**
 * Remove distributor from selected list
 */
const removeDistributor = (index) => {
  selectedDistributors.value.splice(index, 1);
};

/**
 * Toggle distributor favorite status
 */
const toggleFavorite = (distributor) => {
  distributor.isFavorite = !distributor.isFavorite;
  
  if (distributor.isFavorite) {
    // Move to top of list
    const index = selectedDistributors.value.findIndex(d => d.id === distributor.id);
    if (index > 0) {
      selectedDistributors.value.splice(index, 1);
      selectedDistributors.value.unshift(distributor);
    }
    favoriteDistributors.value.push(distributor.id);
  } else {
    // Remove from favorites
    const favIndex = favoriteDistributors.value.indexOf(distributor.id);
    if (favIndex > -1) {
      favoriteDistributors.value.splice(favIndex, 1);
    }
  }
  
  // Save to localStorage
  localStorage.setItem('favoriteDistributors', JSON.stringify(favoriteDistributors.value));
};

/**
 * Handle image upload
 */
const handleImageUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // Validate file size
  if (file.size > 16 * 1024 * 1024) {
    showToastMessage('Image too large (max 16MB)', 'bi bi-exclamation-circle-fill');
    return;
  }

  inquiryForm.value.image = file;
  
  // Create preview
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreview.value = e.target.result;
  };
  reader.readAsDataURL(file);
};

/**
 * Remove image
 */
const removeImage = () => {
  inquiryForm.value.image = null;
  imagePreview.value = '';
};

/**
 * Submit inquiry
 */
const submitInquiry = async () => {
  if (selectedDistributors.value.length === 0 || !inquiryForm.value.message) {
    showToastMessage('Please select at least one distributor and enter a message', 'bi bi-exclamation-circle-fill');
    return;
  }

  submitting.value = true;

  try {
    // Submit to each selected distributor
    const distributorIds = selectedDistributors.value.map(d => d.id);
    const response = await submitInquiryAPI(
      distributorIds,
      inquiryForm.value.message,
      inquiryForm.value.image
    );

    if (response.data) {
      showToastMessage(`Inquiry sent to ${distributorIds.length} distributor(s)!`, 'bi bi-check-circle-fill');

      // Reset form
      inquiryForm.value = {
        message: '',
        image: null
      };
      imagePreview.value = '';
      selectedDistributors.value = [];

      // Refresh history
      await fetchInquiryHistory();
    }
  } catch (err) {
    console.error('[Inquiry Error]', err);
    showToastMessage(
      err.response?.data?.message || 'Failed to submit inquiry',
      'bi bi-exclamation-circle-fill'
    );
  } finally {
    submitting.value = false;
  }
};

/**
 * Fetch inquiry history
 */
const fetchInquiryHistory = async () => {
  loadingHistory.value = true;
  historyError.value = '';

  try {
    const response = await getInquiryHistory();
    if (response.data && response.data.inquiries) {
      inquiryHistory.value = response.data.inquiries;
    }
  } catch (err) {
    console.error('[History Error]', err);
    historyError.value = err.response?.data?.message || 'Failed to load inquiry history';
  } finally {
    loadingHistory.value = false;
  }
};

/**
 * Format date
 */
const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A';
  try {
    return new Date(timestamp).toLocaleString();
  } catch {
    return timestamp;
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

// Fetch history on mount
onMounted(() => {
  fetchInquiryHistory();
  // Load favorites from localStorage
  const savedFavorites = localStorage.getItem('favoriteDistributors');
  if (savedFavorites) {
    favoriteDistributors.value = JSON.parse(savedFavorites);
  }
});

// Close dropdown when clicking outside
onUnmounted(() => {
  clearTimeout(searchTimeout);
});

// Handle click outside to close dropdown
document.addEventListener('click', (e) => {
  if (!e.target.closest('.distributor-search')) {
    showDropdown.value = false;
  }
});
</script>

<style scoped>
.shop-inquiry-tab {
  background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-bg-alt) 100%);
  min-height: calc(100vh - 60px);
  padding: 2rem;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
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
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.upload-zone {
  border: 2px dashed var(--color-primary);
  border-radius: 12px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, #e9ecef 100%);
}

.upload-zone:hover {
  border-color: var(--color-accent);
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  transform: translateY(-2px);
}

.ai-analysis-card {
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  border: 2px solid var(--color-primary);
}

.inquiry-item {
  background: linear-gradient(135deg, var(--color-bg-light) 0%, #e9ecef 100%);
  transition: all 0.3s ease;
}

.inquiry-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

/* Distributor Search Styles */
.distributor-search {
  position: relative;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 4px;
}

.search-results {
  padding: 8px 0;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.search-result-item:hover {
  background-color: #f8f9fa;
}

.distributor-info {
  flex: 1;
  min-width: 0;
}

.distributor-info strong {
  display: block;
  margin-bottom: 2px;
  color: #333;
}

.distributor-info small {
  display: block;
  line-height: 1.3;
}

.selected-distributors {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.distributor-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #e9ecef;
  border: 1px solid #dee2e6;
  border-radius: 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.distributor-chip:hover {
  background: #dee2e6;
  transform: translateY(-1px);
}

.distributor-chip.favorite {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  border-color: #ffd700;
  color: #333;
}

.distributor-chip i {
  font-size: 0.875rem;
}

.distributor-chip.favorite i {
  color: #ff6b35;
}
</style>

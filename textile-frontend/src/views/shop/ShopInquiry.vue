<template>
  <div class="shop-inquiry-tab">
    <h5 class="mb-3">
      <i class="bi bi-chat-dots me-2"></i>Customer Inquiries & Fabric Analysis
    </h5>

    <!-- Inquiry Form Card -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">Submit Inquiry</h6>
        
        <div class="mb-3">
          <label class="form-label">Shop ID</label>
          <input
            type="number"
            class="form-control"
            v-model.number="inquiryForm.shopId"
            placeholder="Enter shop ID"
            required
          />
          <small class="text-muted">Enter the shop ID you want to inquire about</small>
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
            Upload a fabric image to get AI-powered analysis including material identification and price estimation
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
          :disabled="submitting || !inquiryForm.shopId || !inquiryForm.message"
        >
          <span v-if="submitting">
            <span class="spinner-border spinner-border-sm me-2"></span>
            Submitting...
          </span>
          <span v-else>
            <i class="bi bi-send me-2"></i>Submit Inquiry
          </span>
        </button>
      </div>
    </div>

    <!-- AI Fabric Analysis Result -->
    <div v-if="fabricAnalysis" class="card mb-4 ai-analysis-card">
      <div class="card-body">
        <h6 class="mb-3">
          <i class="bi bi-stars me-2"></i>AI Fabric Analysis
        </h6>
        <div class="row g-3">
          <div class="col-md-6">
            <strong>Fabric Name:</strong>
            <p>{{ fabricAnalysis.fabric_name }}</p>
          </div>
          <div class="col-md-6">
            <strong>Material:</strong>
            <p>{{ fabricAnalysis.material }}</p>
          </div>
          <div class="col-md-6">
            <strong>Estimated Price:</strong>
            <p class="fs-5 text-success">{{ fabricAnalysis.estimated_price }}</p>
          </div>
          <div class="col-12">
            <strong>AI Suggestion:</strong>
            <p class="text-muted">{{ fabricAnalysis.suggestion }}</p>
          </div>
        </div>
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
import { ref, onMounted } from 'vue';
import { submitInquiry as submitInquiryAPI, getInquiryHistory } from '@/api/apiInquiry';

// Form data
const inquiryForm = ref({
  shopId: null,
  message: '',
  image: null
});

const imagePreview = ref('');
const submitting = ref(false);
const fabricAnalysis = ref(null);

// History
const inquiryHistory = ref([]);
const loadingHistory = ref(false);
const historyError = ref('');

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

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
  if (!inquiryForm.value.shopId || !inquiryForm.value.message) {
    showToastMessage('Please fill in all required fields', 'bi bi-exclamation-circle-fill');
    return;
  }

  submitting.value = true;
  fabricAnalysis.value = null;

  try {
    const response = await submitInquiryAPI(
      inquiryForm.value.shopId,
      inquiryForm.value.message,
      inquiryForm.value.image
    );

    if (response.data) {
      showToastMessage('Inquiry submitted successfully!', 'bi bi-check-circle-fill');
      
      // Display fabric analysis if provided
      if (response.data.fabric_analysis) {
        fabricAnalysis.value = response.data.fabric_analysis;
      }

      // Reset form
      inquiryForm.value = {
        shopId: null,
        message: '',
        image: null
      };
      imagePreview.value = '';

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
  box-shadow: 0 6px 20px rgba(242, 190, 209, 0.4);
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
</style>

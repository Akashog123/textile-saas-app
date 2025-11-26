<template>
  <div class="shop-marketing-tab">
    <h5 class="mb-3">Marketing Content Generation</h5>
    <p class="text-muted">
      Upload sales data (CSV/XLSX) or product images to generate AI-powered marketing content
    </p>

    <div class="card">
      <div class="card-body">
        <div
          class="upload-zone border border-2 border-dashed rounded p-5 text-center mb-4"
          @dragover.prevent
          @drop.prevent="handleFileDrop"
          @click="$refs.fileInput.click()"
        >
          <div class="mb-3">
            <svg width="48" height="48" fill="currentColor" class="text-muted">
              <rect
                x="10"
                y="10"
                width="28"
                height="28"
                rx="4"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              />
              <path
                d="M24 18v12M18 24h12"
                stroke="currentColor"
                stroke-width="2"
              />
            </svg>
          </div>
          <p class="mb-2">Click to Browse and Upload</p>
          <input
            type="file"
            @change="handleFileUpload"
            class="d-none"
            ref="fileInput"
            accept=".csv,.xlsx,.xls,.jpg,.jpeg,.png,.webp"
          />
          <button
            class="btn btn-outline-secondary btn-sm"
            @click.stop="$refs.fileInput.click()"
            :disabled="loading"
          >
            <i class="bi bi-folder2-open"></i> Import CSV/XLSX or Image
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Generating content...</span>
          </div>
          <p class="mt-2 text-muted">AI is generating your marketing content...</p>
        </div>

        <!-- Error State -->
        <div v-if="error" class="alert alert-danger">
          <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
        </div>

        <!-- Generated Content Display -->
        <div v-if="generatedContent && !loading" class="row g-3">
          <!-- Image Display (if type is image) -->
          <div v-if="generatedContent.type === 'image'" class="col-md-6">
            <h6>Generated Marketing Poster</h6>
            <div class="border rounded p-3 bg-light">
              <img
                v-if="generatedContent.poster"
                :src="getImageUrl(generatedContent.poster)"
                alt="Marketing Poster"
                class="img-fluid rounded mb-3"
              />
              <button
                class="btn btn-sm btn-primary w-100"
                @click="downloadImage(generatedContent.poster)"
              >
                <i class="bi bi-download me-1"></i> Download Poster
              </button>
            </div>
          </div>

          <!-- Caption Display -->
          <div :class="generatedContent.type === 'image' ? 'col-md-6' : 'col-12'">
            <h6>AI-Generated Content</h6>
            <div class="border rounded p-3 bg-light" style="max-height: 400px; overflow-y: auto">
              <!-- Single Caption for Image -->
              <div v-if="generatedContent.type === 'image'">
                <p class="small mb-2"><strong>Marketing Caption:</strong></p>
                <p class="mb-3">{{ generatedContent.caption }}</p>
                <div class="d-flex gap-2">
                  <button
                    class="btn btn-sm btn-outline-secondary"
                    @click="copyToClipboard(generatedContent.caption)"
                  >
                    <i class="bi bi-files"></i> Copy
                  </button>
                </div>
              </div>

              <!-- Multiple Captions for CSV Data -->
              <div v-else-if="generatedContent.type === 'data'">
                <p class="small text-muted mb-3">
                  Generated {{ generatedContent.ai_captions?.length || 0 }} captions
                  from {{ generatedContent.rows_processed }} products
                </p>
                <div
                  v-for="(item, idx) in generatedContent.ai_captions"
                  :key="idx"
                  class="mb-3 pb-3 border-bottom"
                >
                  <strong class="d-block mb-1">{{ item.product }}</strong>
                  <small class="text-muted d-block mb-2">{{ item.category }}</small>
                  <p class="small mb-2">{{ item.caption }}</p>
                  <button
                    class="btn btn-sm btn-outline-secondary"
                    @click="copyToClipboard(item.caption)"
                  >
                    <i class="bi bi-files"></i> Copy
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!generatedContent && !loading && !error" class="row g-3">
          <div class="col-md-6">
            <h6>Marketing Image</h6>
            <div class="border rounded p-3 bg-light" style="min-height: 250px">
              <div
                class="text-center text-muted d-flex align-items-center justify-content-center"
                style="height: 220px"
              >
                <div>
                  <div class="mb-2"><i class="bi bi-image fs-3"></i></div>
                  Image will be generated here
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-6">
            <h6>AI Caption</h6>
            <div class="border rounded p-3 bg-light" style="min-height: 250px">
              <div
                class="text-center text-muted d-flex align-items-center justify-content-center"
                style="height: 220px"
              >
                <div>
                  <div class="mb-2">
                    <i class="bi bi-pencil-square fs-3"></i>
                  </div>
                  Caption will be generated here
                </div>
              </div>
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
import { ref } from 'vue';
import { generateMarketingContent } from '@/api/apiMarketing';

const loading = ref(false);
const error = ref('');
const generatedContent = ref(null);

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

/**
 * Handle file upload
 */
const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  await processFile(file);
};

/**
 * Handle file drop
 */
const handleFileDrop = async (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;

  await processFile(file);
};

/**
 * Process uploaded file
 */
const processFile = async (file) => {
  // Validate file size (16MB max)
  if (file.size > 16 * 1024 * 1024) {
    showToastMessage('File too large (max 16MB)', 'bi bi-exclamation-circle-fill');
    return;
  }

  // Validate file type
  const allowedExtensions = ['.csv', '.xlsx', '.xls', '.jpg', '.jpeg', '.png', '.webp'];
  const fileExt = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedExtensions.includes(fileExt)) {
    showToastMessage(
      'Invalid file type. Allowed: CSV, XLSX, JPG, PNG, WEBP',
      'bi bi-exclamation-circle-fill'
    );
    return;
  }

  loading.value = true;
  error.value = '';
  generatedContent.value = null;

  try {
    const response = await generateMarketingContent(file);
    if (response.data) {
      generatedContent.value = response.data;
      showToastMessage('Marketing content generated successfully!', 'bi bi-check-circle-fill');
    }
  } catch (err) {
    console.error('[Marketing Error]', err);
    error.value = err.response?.data?.message || 'Failed to generate content';
    showToastMessage(error.value, 'bi bi-exclamation-circle-fill');
  } finally {
    loading.value = false;
  }
};

/**
 * Get full image URL
 */
const getImageUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `http://127.0.0.1:5001${path}`;
};

/**
 * Download generated image
 */
const downloadImage = async (imagePath) => {
  try {
    const imageUrl = getImageUrl(imagePath);
    const response = await fetch(imageUrl);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `marketing_poster_${Date.now()}.png`;
    link.click();
    window.URL.revokeObjectURL(url);
    showToastMessage('Poster downloaded!', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[Download Error]', err);
    showToastMessage('Download failed', 'bi bi-exclamation-circle-fill');
  }
};

/**
 * Copy text to clipboard
 */
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    showToastMessage('Copied to clipboard!', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[Copy Error]', err);
    showToastMessage('Failed to copy', 'bi bi-exclamation-circle-fill');
  }
};

/**
 * Show toast notification
 */
const showToastMessage = (message, icon) => {
  toastMessage.value = message;
  toastIcon.value = icon;
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};
</script>

<style scoped>
.shop-marketing-tab {
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

.card {
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.upload-zone {
  background: linear-gradient(135deg, var(--color-bg-light) 0%, #e9ecef 100%);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.upload-zone::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(242, 190, 209, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 100%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
}

.upload-zone:hover::before {
  opacity: 1;
}

.upload-zone:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  border-color: var(--color-primary) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(242, 190, 209, 0.15);
}

.border.rounded {
  border-radius: 12px !important;
  border-color: rgba(242, 190, 209, 0.2) !important;
}

.bg-light {
  background: linear-gradient(135deg, var(--color-bg-light) 0%, #e9ecef 100%) !important;
}

.btn-outline-secondary,
.btn-outline-primary,
.btn-primary {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-outline-secondary:hover,
.btn-outline-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(242, 190, 209, 0.2);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(242, 190, 209, 0.4);
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
}

h5,
h6 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
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

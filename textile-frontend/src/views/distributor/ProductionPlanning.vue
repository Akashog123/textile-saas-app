<template>
  <div class="production-planning-tab">
    <h5 class="mb-4">
      <i class="bi bi-gear me-2"></i>Production Planning
    </h5>
    <p class="text-muted mb-4">
      Upload sales data to generate AI-powered production recommendations
    </p>

    <!-- Upload Section -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">Upload Sales Data</h6>
        <div
          class="upload-zone"
          @click="$refs.fileInput.click()"
          @dragover.prevent
          @drop.prevent="handleFileDrop"
        >
          <div class="text-center">
            <i class="bi bi-cloud-upload fs-1 text-muted mb-2"></i>
            <p class="mb-2">Click to upload or drag and drop</p>
            <small class="text-muted">CSV or XLSX file (max 16MB)</small>
          </div>
          <input
            type="file"
            ref="fileInput"
            accept=".csv,.xlsx,.xls"
            @change="handleFileUpload"
            class="d-none"
          />
        </div>
        <button
          class="btn btn-primary w-100 mt-3"
          @click="generatePlan"
          :disabled="!file || loading"
        >
          <span v-if="loading">
            <span class="spinner-border spinner-border-sm me-2"></span>
            Generating Plan...
          </span>
          <span v-else>
            <i class="bi bi-magic me-2"></i>Generate Production Plan
          </span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    </div>

    <!-- Production Plan Results -->
    <div v-if="planData" class="row g-3">
      <!-- Production Priorities -->
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h6 class="mb-3">Production Priorities</h6>
            <div class="row g-3">
              <div v-if="planData.increase_production?.length" class="col-md-4">
                <div class="priority-card increase">
                  <h6><i class="bi bi-arrow-up-circle"></i> Increase Production</h6>
                  <ul class="list-unstyled">
                    <li v-for="product in planData.increase_production" :key="product">
                      {{ product }}
                    </li>
                  </ul>
                </div>
              </div>
              <div v-if="planData.maintain_production?.length" class="col-md-4">
                <div class="priority-card maintain">
                  <h6><i class="bi bi-dash-circle"></i> Maintain Production</h6>
                  <ul class="list-unstyled">
                    <li v-for="product in planData.maintain_production" :key="product">
                      {{ product }}
                    </li>
                  </ul>
                </div>
              </div>
              <div v-if="planData.reduce_production?.length" class="col-md-4">
                <div class="priority-card reduce">
                  <h6><i class="bi bi-arrow-down-circle"></i> Reduce Production</h6>
                  <ul class="list-unstyled">
                    <li v-for="product in planData.reduce_production" :key="product">
                      {{ product }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Recommendations -->
      <div v-if="planData.ai_recommendations" class="col-12">
        <div class="card ai-card">
          <div class="card-body">
            <h6><i class="bi bi-stars me-2"></i>AI Recommendations</h6>
            <p>{{ planData.ai_recommendations }}</p>
          </div>
        </div>
      </div>

      <!-- Export Button -->
      <div class="col-12 text-center">
        <button class="btn btn-outline-primary" @click="exportPlan">
          <i class="bi bi-download me-2"></i>Export Plan
        </button>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="showToast" class="toast-notification">
      <i :class="toastIcon" class="me-2"></i>{{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { generateProductionPlan, exportProductionPlan } from '@/api/apiDistributor';

const file = ref(null);
const loading = ref(false);
const error = ref('');
const planData = ref(null);
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

const handleFileUpload = (event) => {
  const uploadedFile = event.target.files[0];
  if (!uploadedFile) return;

  if (uploadedFile.size > 16 * 1024 * 1024) {
    showToastMsg('File too large (max 16MB)', 'bi bi-exclamation-circle-fill');
    return;
  }

  file.value = uploadedFile;
  showToastMsg('File uploaded', 'bi bi-check-circle-fill');
};

const handleFileDrop = (event) => {
  const uploadedFile = event.dataTransfer.files[0];
  if (uploadedFile) {
    file.value = uploadedFile;
    showToastMsg('File uploaded', 'bi bi-check-circle-fill');
  }
};

const generatePlan = async () => {
  if (!file.value) return;

  loading.value = true;
  error.value = '';
  planData.value = null;

  try {
    const response = await generateProductionPlan(file.value);
    if (response.data) {
      planData.value = response.data;
      showToastMsg('Production plan generated!', 'bi bi-check-circle-fill');
    }
  } catch (err) {
    console.error('[Plan Error]', err);
    error.value = err.response?.data?.message || 'Failed to generate plan';
  } finally {
    loading.value = false;
  }
};

const exportPlan = async () => {
  try {
    const response = await exportProductionPlan();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `production_plan_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
    showToastMsg('Plan exported!', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[Export Error]', err);
    showToastMsg('Export failed', 'bi bi-exclamation-circle-fill');
  }
};

const showToastMsg = (message, icon) => {
  toastMessage.value = message;
  toastIcon.value = icon;
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};
</script>

<style scoped>
.production-planning-tab {
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
}

.upload-zone {
  border: 2px dashed var(--color-primary);
  border-radius: 12px;
  padding: 3rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, #e9ecef 100%);
}

.upload-zone:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
}

.priority-card {
  padding: 1.5rem;
  border-radius: 12px;
  height: 100%;
}

.priority-card.increase {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 2px solid #10b981;
}

.priority-card.maintain {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 2px solid #f59e0b;
}

.priority-card.reduce {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border: 2px solid #ef4444;
}

.ai-card {
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  border: 2px solid var(--color-primary);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
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
  }
  to {
    transform: translateX(0);
  }
}
</style>

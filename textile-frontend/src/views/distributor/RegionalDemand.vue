<template>
  <div class="regional-demand-tab">
    <h5 class="mb-4">
      <i class="bi bi-geo-alt me-2"></i>Regional Demand Analysis
    </h5>
    <p class="text-muted mb-4">
      Upload regional sales data to analyze demand patterns across different regions
    </p>

    <!-- Upload Section -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">Upload Regional Sales Data</h6>
        <p class="small text-muted mb-3">
          CSV format: Region, Product, Date, Sales
        </p>
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
          @click="analyzeDemand"
          :disabled="!file || loading"
        >
          <span v-if="loading">
            <span class="spinner-border spinner-border-sm me-2"></span>
            Analyzing...
          </span>
          <span v-else>
            <i class="bi bi-graph-up me-2"></i>Analyze Regional Demand
          </span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    </div>

    <!-- Analysis Results -->
    <div v-if="demandData" class="row g-3">
      <!-- Regional Summary -->
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h6 class="mb-3">Top Regions by Revenue</h6>
            <div class="row g-3">
              <div
                v-for="(region, idx) in demandData.regional_summary?.slice(0, 3)"
                :key="idx"
                class="col-md-4"
              >
                <div class="region-card">
                  <div class="region-rank">#{{ idx + 1 }}</div>
                  <h6 class="mb-2">{{ region.region }}</h6>
                  <div class="region-stats">
                    <div class="stat">
                      <small class="text-muted">Revenue</small>
                      <strong>₹{{ parseFloat(region.total_sales || 0).toLocaleString() }}</strong>
                    </div>
                    <div class="stat">
                      <small class="text-muted">Products</small>
                      <strong>{{ region.unique_products || 0 }}</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Product Rankings -->
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h6 class="mb-3">Product Rankings by Region</h6>
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>Region</th>
                    <th>Product</th>
                    <th>Sales</th>
                    <th>Rank</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(item, idx) in demandData.product_rankings?.slice(0, 10)"
                    :key="idx"
                  >
                    <td>{{ item.region }}</td>
                    <td>{{ item.product }}</td>
                    <td>{{ item.sales }}</td>
                    <td><span class="badge bg-primary">{{ item.rank }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Insights -->
      <div v-if="demandData.ai_demand_insights" class="col-12">
        <div class="card ai-card">
          <div class="card-body">
            <h6><i class="bi bi-stars me-2"></i>AI Demand Insights</h6>
            <p>{{ demandData.ai_demand_insights }}</p>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="col-12 text-center">
        <button class="btn btn-outline-primary me-2" @click="downloadReport">
          <i class="bi bi-file-pdf me-2"></i>Download Report
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
import { analyzeRegionalDemand, downloadRegionalReport } from '@/api/apiDistributor';

const file = ref(null);
const loading = ref(false);
const error = ref('');
const demandData = ref(null);
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

const analyzeDemand = async () => {
  if (!file.value) return;

  loading.value = true;
  error.value = '';
  demandData.value = null;

  try {
    const response = await analyzeRegionalDemand(file.value);
    if (response.data) {
      demandData.value = response.data;
      showToastMsg('Analysis complete!', 'bi bi-check-circle-fill');
    }
  } catch (err) {
    console.error('[Analysis Error]', err);
    error.value = err.response?.data?.message || 'Failed to analyze demand';
  } finally {
    loading.value = false;
  }
};

const downloadReport = async () => {
  try {
    const response = await downloadRegionalReport();
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `regional_demand_report_${new Date().toISOString().split('T')[0]}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
    showToastMsg('Report downloaded!', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[Download Error]', err);
    showToastMsg('Download failed', 'bi bi-exclamation-circle-fill');
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
.regional-demand-tab {
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

.region-card {
  padding: 1.5rem;
  border-radius: 12px;
  background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
  border: 2px solid var(--color-primary);
  position: relative;
  transition: all 0.3s ease;
}

.region-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(242, 190, 209, 0.3);
}

.region-rank {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: var(--color-primary);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.region-stats {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
}

.region-stats .stat {
  display: flex;
  flex-direction: column;
}

.region-stats small {
  display: block;
  margin-bottom: 0.25rem;
}

.table th {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  border: none;
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
  }
  to {
    transform: translateX(0);
  }
}
</style>

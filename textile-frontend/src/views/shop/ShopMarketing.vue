<template>
  <div class="shop-marketing-tab">
    <h5 class="mb-3">Marketing Content Generation</h5>
    <p class="text-muted">Upload a product or export your product from sales data to generate your marketing content</p>

    <div class="card">
      <div class="card-body">
        <div class="upload-zone border border-2 border-dashed rounded p-5 text-center mb-4" 
             @dragover.prevent 
             @drop.prevent="handleFileDrop"
             @click="$refs.fileInput.click()">
          <div class="mb-3">
            <svg width="48" height="48" fill="currentColor" class="text-muted">
              <rect x="10" y="10" width="28" height="28" rx="4" fill="none" stroke="currentColor" stroke-width="2"/>
              <path d="M24 18v12M18 24h12" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <p class="mb-2">Click to Browse and Upload your product</p>
          <input type="file" @change="handleFileUpload" class="d-none" ref="fileInput" accept=".csv,.xlsx,image/*">
          <button class="btn btn-outline-secondary btn-sm" @click.stop="$refs.fileInput.click()"><i class="bi bi-folder2-open"></i> Import csv/xlsx</button>
        </div>

        <div v-if="uploadedFile" class="alert alert-success d-flex align-items-center">
          <span class="me-2"><i class="bi bi-check-circle-fill"></i></span> Content Preprocessed
        </div>

        <div class="row g-3">
          <div class="col-md-6">
            <h6>Review and Post Your Content</h6>
            <div class="border rounded p-3 bg-light" style="min-height: 250px;">
              <div v-if="!uploadedFile" class="text-center text-muted d-flex align-items-center justify-content-center" style="height: 220px;">
                <div>
                  <div class="mb-2"><i class="bi bi-image fs-3"></i></div>
                  Image will be generated here
                </div>
              </div>
              <div v-else class="text-center">
                <div class="mb-2 fw-semibold">Generated Marketing Image</div>
                <div class="bg-secondary rounded mb-3 d-flex align-items-center justify-content-center" style="height: 150px;">
                  <span class="text-white fs-1"><i class="bi bi-palette-fill"></i></span>
                </div>
                <button class="btn btn-sm btn-outline-primary">
                  <svg width="16" height="16" fill="currentColor" class="me-1">
                    <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" fill="none"/>
                  </svg>
                  Download Image
                </button>
              </div>
            </div>
          </div>

          <div class="col-md-6">
            <h6>&nbsp;</h6>
            <div class="border rounded p-3 bg-light" style="min-height: 250px;">
              <div v-if="!uploadedFile" class="text-center text-muted d-flex align-items-center justify-content-center" style="height: 220px;">
                <div>
                  <div class="mb-2"><i class="bi bi-pencil-square fs-3"></i></div>
                  Caption will be generated here
                </div>
              </div>
              <div v-else>
                <h6>Product Name</h6>
                <p class="small mb-2"><strong>AI-generated Caption:</strong></p>
                <p class="small">
                  Handwoven elegance! Our latest premium silk collection brings 
                  together traditional craft and modern design. Perfect for 
                  festive occasions. Limited stock available!
                </p>
                <div class="d-flex gap-2 mt-3">
                  <button class="btn btn-sm btn-outline-secondary">
                    <i class="bi bi-files"></i> Copy
                  </button>
                  <button class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-share"></i> Share
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="text-center mt-4">
          <button class="btn btn-primary" :disabled="!uploadedFile">Preview</button>
        </div>
      </div>
    </div>

    <div v-if="uploadedFile" class="mt-4 text-center text-muted small">
      After uploading products set up Ads on <button class="btn btn-link p-0">Preview Flash</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const uploadedFile = ref(null)

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    uploadedFile.value = file
    setTimeout(() => {
      console.log('File processed:', file.name)
    }, 1000)
  }
}

const handleFileDrop = (event) => {
  const file = event.dataTransfer.files[0]
  if (file) {
    uploadedFile.value = file
  }
}
</script>

<style scoped>
.shop-marketing-tab {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
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
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.upload-zone {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
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
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.upload-zone:hover::before {
  opacity: 1;
}

.upload-zone:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  border-color: #667eea !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
}

.alert-success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 1.5px solid #6ee7b7;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.border.rounded {
  border-radius: 12px !important;
  border-color: rgba(102, 126, 234, 0.2) !important;
}

.bg-light {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
}

.bg-secondary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

.btn-outline-secondary,
.btn-outline-primary,
.btn-primary {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border-width: 1.5px;
}

.btn-outline-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.2);
}

.btn-outline-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(13, 110, 253, 0.4);
}

h5, h6 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}
</style>

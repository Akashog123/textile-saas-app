<template>
  <div class="shop-inquiry-tab">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">Fabric Stock Inquiry</h5>
      <button class="btn btn-outline-secondary btn-sm">
        <svg width="16" height="16" fill="currentColor" class="me-1">
          <path d="M2 4h12M2 8h8M2 12h10" stroke="currentColor" stroke-width="2" fill="none"/>
        </svg>
        Inquiry History
      </button>
    </div>

    <div class="card">
      <div class="card-body">
        <div class="mb-4">
          <label class="form-label">Inquiry</label>
          <div class="input-group">
            <textarea 
              class="form-control" 
              placeholder="Add a Message (Optional)"
              v-model="inquiryMessage"
              rows="3"
            ></textarea>
          </div>
        </div>

        <div class="upload-zone border border-2 border-dashed rounded p-4 text-center mb-4"
             @dragover.prevent
             @drop.prevent="handleInquiryFileDrop"
             @click="$refs.inquiryFileInput.click()">
          <div class="mb-2">
            <svg width="40" height="40" fill="currentColor" class="text-muted">
              <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" stroke-width="2"/>
              <path d="M20 12v16M12 20h16" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <p class="mb-2 small fw-semibold">Upload Image</p>
          <p class="text-muted small mb-2">Drag and drop or click to upload</p>
          <input type="file" @change="handleInquiryFileUpload" class="d-none" ref="inquiryFileInput" accept="image/*">
          <button class="btn btn-outline-secondary btn-sm" @click.stop="$refs.inquiryFileInput.click()">
            Choose File / Browse
          </button>
          
          <div v-if="inquiryFile" class="mt-3 text-start">
            <div class="alert alert-info small mb-0">
              <i class="bi bi-paperclip"></i> Selected: {{ inquiryFile.name }}
            </div>
          </div>
        </div>

        <div class="d-flex gap-2 justify-content-center">
          <button class="btn btn-primary" @click="sendInquiry" :disabled="!inquiryMessage && !inquiryFile">
            Send Inquiry
          </button>
        </div>

        <div v-if="inquirySubmitted" class="alert alert-success mt-4">
          <i class="bi bi-check-circle-fill"></i> Inquiry submitted successfully! You'll receive stock updates shortly.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const inquiryMessage = ref('')
const inquiryFile = ref(null)
const inquirySubmitted = ref(false)

const handleInquiryFileUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    inquiryFile.value = file
  }
}

const handleInquiryFileDrop = (event) => {
  const file = event.dataTransfer.files[0]
  if (file) {
    inquiryFile.value = file
  }
}

const sendInquiry = () => {
  inquirySubmitted.value = true
  setTimeout(() => {
    inquirySubmitted.value = false
    inquiryMessage.value = ''
    inquiryFile.value = null
  }, 3000)
}
</script>

<style scoped>
.shop-inquiry-tab {
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

.alert-info {
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  border: 1.5px solid #7dd3fc;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
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

.btn-outline-primary {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border-width: 1.5px;
}

.btn-outline-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
}

h5 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.form-control,
.form-select {
  border-radius: 8px;
  border: 1.5px solid #dee2e6;
  transition: all 0.3s ease;
}

.form-control:focus,
.form-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.25rem rgba(102, 126, 234, 0.15);
}
</style>

<template>
  <div class="shop-marketing-tab">
    <!-- Header with History Button -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h5 class="mb-1">Marketing Content Generation</h5>
        <p class="text-muted mb-0">
          Upload sales data (CSV/XLSX) or product images to generate AI-powered marketing content
        </p>
      </div>
      <button 
        class="btn btn-outline-primary"
        @click="toggleHistory"
      >
        <i class="bi bi-clock-history me-2"></i>
        <span v-if="!showHistory">Show History</span>
        <span v-else>Hide History</span>
      </button>
    </div>

    <!-- Template Section -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">
          <i class="bi bi-file-earmark-text me-2"></i>
          File Template Guide
        </h6>
        <div class="row align-items-center">
          <div class="col-md-8">
            <p class="mb-2">
              <strong>Required Columns:</strong> ProductName, Category, Price
            </p>
            <p class="mb-2">
              <strong>Optional Columns:</strong> Description, ImageURL
            </p>
            <small class="text-muted">
              Use the template below for best results. Image URLs will be downloaded and used to enhance content generation.
            </small>
          </div>
          <div class="col-md-4 text-end">
            <button 
              class="btn btn-primary"
              @click="downloadTemplate"
              :disabled="templateLoading"
            >
              <i class="bi bi-download me-2"></i>
              <span v-if="templateLoading">Generating...</span>
              <span v-else>Download Template</span>
            </button>
          </div>
        </div>
        
        <!-- Template Preview -->
        <div class="mt-3">
          <div class="table-responsive">
            <table class="table table-sm table-bordered">
              <thead class="table-light">
                <tr>
                  <th>ProductName</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Description</th>
                  <th>ImageURL</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Elegant Wedding Saree</td>
                  <td>Sarees</td>
                  <td>2500</td>
                  <td>Premium silk saree with intricate embroidery</td>
                  <td>https://example.com/image.jpg</td>
                </tr>
                <tr class="text-muted">
                  <td colspan="5" class="text-center">
                    <em>Download the template file for complete format</em>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- History Section -->
    <div v-if="showHistory" class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
          <i class="bi bi-clock-history me-2"></i>
          Marketing History
        </h6>
        <button class="btn btn-sm btn-outline-secondary" @click="fetchMarketingHistory">
          <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
      </div>
      <div class="card-body">
        <!-- History Loading -->
        <div v-if="historyLoading" class="text-center py-4">
          <div class="spinner-border spinner-border-sm text-primary me-2"></div>
          Loading history...
        </div>
        
        <!-- History Error -->
        <div v-else-if="historyError" class="alert alert-danger">
          <i class="bi bi-exclamation-triangle me-2"></i>
          {{ historyError }}
        </div>
        
        <!-- History List -->
        <div v-else-if="marketingHistory.length > 0">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Items</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in marketingHistory" :key="item.id">
                  <td>
                    <div class="d-flex align-items-center">
                      <i :class="getFileIcon(item.file_type)" class="me-2"></i>
                      {{ item.file_name }}
                    </div>
                  </td>
                  <td>
                    <span class="badge bg-light text-dark">
                      {{ item.content_type }}
                    </span>
                  </td>
                  <td>
                    <span :class="getStatusBadgeClass(item.status)">
                      {{ item.status }}
                    </span>
                  </td>
                  <td>{{ item.rows_processed || '-' }}</td>
                  <td>{{ formatDate(item.created_at) }}</td>
                  <td>
                    <div class="btn-group" role="group">
                      <button 
                        class="btn btn-sm btn-outline-primary"
                        @click="viewHistoryItem(item)"
                        :disabled="item.status === 'failed'"
                        title="View generated content"
                      >
                        <i class="bi bi-eye"></i> View
                      </button>
                      <button 
                        class="btn btn-sm btn-outline-danger"
                        @click="deleteHistoryItem(item.id)"
                        title="Delete history item"
                      >
                        <i class="bi bi-trash"></i> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Empty History -->
        <div v-else class="text-center py-4 text-muted">
          <i class="bi bi-clock-history d-block fs-2 mb-3"></i>
          No marketing history found. Generate your first content to see it here!
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <!-- Upload Type Selection -->
        <div class="row mb-3">
          <div class="col-12">
            <div class="btn-group w-100" role="group">
              <input type="radio" class="btn-check" name="uploadType" id="csvType" value="csv" v-model="uploadType" @change="resetForm">
              <label class="btn btn-outline-primary" for="csvType">
                <i class="bi bi-file-earmark-excel me-2"></i>CSV/XLSX File
              </label>
              
              <input type="radio" class="btn-check" name="uploadType" id="singleType" value="single" v-model="uploadType" @change="resetForm">
              <label class="btn btn-outline-primary" for="singleType">
                <i class="bi bi-image me-2"></i>Single Image
              </label>
            </div>
          </div>
        </div>

        <!-- CSV/XLSX Upload Section -->
        <div v-if="uploadType === 'csv'" class="mb-4">
          <div
            class="upload-zone border border-2 border-dashed rounded p-4 text-center"
            @dragover.prevent
            @drop.prevent="handleFileDrop"
            @click="$refs.fileInput.click()"
          >
            <div class="mb-2">
              <svg width="32" height="32" fill="currentColor" class="text-muted">
                <rect
                  x="6"
                  y="6"
                  width="20"
                  height="20"
                  rx="4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <path
                  d="M16 12v8M12 16h8"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </div>
            <p class="mb-2 small">Upload CSV/XLSX with product data (max 5 products)</p>
            <input
              type="file"
              @change="handleFileUpload"
              class="d-none"
              ref="fileInput"
              accept=".csv,.xlsx,.xls"
            />
            <button
              class="btn btn-outline-secondary btn-sm"
              @click.stop="$refs.fileInput.click()"
              :disabled="loading"
            >
              <i class="bi bi-folder2-open"></i> Browse CSV/XLSX
            </button>
          </div>
        </div>

        <!-- Single Image Upload Section -->
        <div v-if="uploadType === 'single'" class="mb-4">
          <div class="row">
            <div class="col-md-8">
              <div
                class="upload-zone border border-2 border-dashed rounded p-3 text-center"
                @dragover.prevent
                @drop.prevent="handleFileDrop"
                @click="$refs.imageInput.click()"
              >
                <div class="mb-2">
                  <svg width="24" height="24" fill="currentColor" class="text-muted">
                    <rect
                      x="4"
                      y="4"
                      width="16"
                      height="16"
                      rx="2"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                    />
                    <circle cx="12" cy="10" r="2" fill="currentColor" />
                    <path
                      d="M6 14l2-2 2 2 4-4 2 2"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </div>
                <p class="mb-1 small">Upload product image</p>
                <input
                  type="file"
                  @change="handleFileUpload"
                  class="d-none"
                  ref="imageInput"
                  accept=".jpg,.jpeg,.png,.webp"
                />
                <button
                  class="btn btn-outline-secondary btn-sm"
                  @click.stop="$refs.imageInput.click()"
                  :disabled="loading"
                >
                  <i class="bi bi-image"></i> Choose Image
                </button>
              </div>
            </div>
            <div class="col-md-4">
              <div class="preview-container border rounded p-2 bg-light" style="min-height: 80px">
                <div v-if="singleImagePreview" class="text-center">
                  <img :src="singleImagePreview" class="img-fluid rounded" style="max-height: 60px" />
                </div>
                <div v-else class="text-center text-muted d-flex align-items-center justify-content-center" style="height: 60px">
                  <small>Image preview</small>
                </div>
              </div>
            </div>
          </div>

          <!-- Product Details Form -->
          <div class="row mt-3">
            <div class="col-md-6">
              <label for="productName" class="form-label small">Product Name *</label>
              <input
                type="text"
                id="productName"
                class="form-control form-control-sm"
                v-model="singleProduct.name"
                placeholder="e.g., Elegant Silk Saree"
                :disabled="loading"
              />
            </div>
            <div class="col-md-6">
              <label for="productCategory" class="form-label small">Category *</label>
              <select
                id="productCategory"
                class="form-select form-select-sm"
                v-model="singleProduct.category"
                :disabled="loading"
              >
                <option value="">Select category</option>
                <option value="Sarees">Sarees</option>
                <option value="Kurtis">Kurtis</option>
                <option value="Dresses">Dresses</option>
                <option value="Fabrics">Fabrics</option>
                <option value="Accessories">Accessories</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          <div class="row mt-2">
            <div class="col-md-6">
              <label for="productPrice" class="form-label small">Price (₹) *</label>
              <input
                type="number"
                id="productPrice"
                class="form-control form-control-sm"
                v-model="singleProduct.price"
                placeholder="e.g., 2500"
                min="0"
                :disabled="loading"
              />
            </div>
            <div class="col-md-6">
              <label for="productDescription" class="form-label small">Description (optional)</label>
              <textarea
                id="productDescription"
                class="form-control form-control-sm"
                v-model="singleProduct.description"
                placeholder="Brief product description"
                rows="1"
                :disabled="loading"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Aspect Ratio Selection (Compact) -->
        <div class="row mb-3">
          <div class="col-md-12">
            <label for="aspectRatio" class="form-label small">Aspect Ratio</label>
            <select 
              id="aspectRatio" 
              class="form-select form-select-sm"
              v-model="selectedAspectRatio"
              :disabled="loading"
            >
              <option value="">Default (16:9)</option>
              <option value="672x1568">Portrait (9:21)</option>
              <option value="720x1456">Portrait (5:10)</option>
              <option value="800x1328">Portrait (3:5)</option>
              <option value="832x1248">Portrait (2:3)</option>
              <option value="880x1184">Portrait (3:4)</option>
              <option value="1024x1024">Square (1:1)</option>
              <option value="1184x880">Landscape (4:3)</option>
              <option value="1328x800">Landscape (5:3)</option>
              <option value="1568x672">Landscape (21:9)</option>
            </select>
          </div>
        </div>

        <!-- Progress Display -->
        <div v-if="loading && progressStatus" class="mb-4">
          <div class="card">
            <div class="card-body">
              <h6 class="card-title mb-3">
                <i class="bi bi-hourglass-split me-2"></i>
                Processing Progress
              </h6>
              
              <!-- Progress Bar -->
              <div class="progress mb-3" style="height: 8px;">
                <div 
                  class="progress-bar progress-bar-striped progress-bar-animated"
                  :style="{ width: progressPercentage + '%' }"
                  role="progressbar"
                ></div>
              </div>
              
              <!-- Progress Details -->
              <div class="row small text-muted">
                <div class="col-md-6">
                  <div><strong>Status:</strong> {{ progressStatus }}</div>
                  <div><strong>Step:</strong> {{ currentStep }}</div>
                  <div><strong>Progress:</strong> {{ currentItem }}/{{ totalItems }}</div>
                </div>
                <div class="col-md-6">
                  <div><strong>Batch:</strong> {{ batchProgress }}/{{ totalBatches }}</div>
                  <div><strong>Time:</strong> {{ formatTime(elapsedTime) }}</div>
                  <div><strong>Completion:</strong> {{ Math.round(progressPercentage) }}%</div>
                </div>
              </div>
              
              <!-- Errors (if any) -->
              <div v-if="progressErrors.length > 0" class="mt-2">
                <div class="alert alert-warning alert-sm py-2">
                  <small><strong>Warnings:</strong></small>
                  <ul class="mb-0 small">
                    <li v-for="(error, idx) in progressErrors.slice(-2)" :key="idx">{{ error }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
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
        <div v-if="generatedContent" class="generated-content">
          <!-- Image Upload Results -->
          <div v-if="generatedContent.type === 'image'">
            <div class="row">
              <div class="col-md-6">
                <h6>Marketing Image</h6>
                <div class="border rounded p-3 bg-light" style="min-height: 250px">
                  <div
                    v-if="generatedContent.poster"
                    class="text-center"
                    style="height: 220px; display: flex; align-items: center; justify-content: center;"
                  >
                    <img
                      :src="getImageUrl(generatedContent.poster)"
                      alt="Marketing Poster"
                      class="img-fluid rounded"
                      style="max-height: 220px; max-width: 100%; object-fit: contain;"
                      @error="handleImageError"
                    />
                  </div>
                  <div
                    v-else
                    class="text-center text-muted d-flex align-items-center justify-content-center"
                    style="height: 220px"
                  >
                    <div>
                      <div class="mb-2"><i class="bi bi-image fs-3"></i></div>
                      <div class="small">
                        <strong>Poster generation unavailable</strong><br>
                        <span class="text-muted">
                          {{ getGenerationMethodMessage(generatedContent.generation_method) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-if="generatedContent.poster" class="text-center mt-2">
                  <div class="d-flex align-items-center justify-content-center mb-2">
                    <small class="text-muted me-2">Generation Method:</small>
                    <span :class="`badge ${getGenerationMethodBadgeClass(generatedContent.generation_method)}`">
                      <i :class="`bi ${getGenerationMethodIcon(generatedContent.generation_method)} me-1`"></i>
                      {{ generatedContent.generation_method || 'ai_context' }}
                    </span>
                  </div>
                  <button
                    class="btn btn-sm btn-outline-secondary"
                    @click="downloadImage(generatedContent.poster)"
                  >
                    <i class="bi bi-download"></i> Download
                  </button>
                </div>
              </div>

              <div class="col-md-6">
                <h6>AI Caption</h6>
                <div class="border rounded p-3 bg-light" style="min-height: 250px">
                  <div class="d-flex align-items-center justify-content-center" style="height: 220px">
                    <div v-if="generatedContent.caption" class="w-100">
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
                    <div
                      v-else
                      class="text-center text-muted"
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

          <!-- CSV/XLSX Results -->
          <div v-else-if="generatedContent.type === 'data'">
            <h6 class="mb-3">Generated Marketing Captions</h6>
            <p class="small text-muted mb-3">
              Generated {{ generatedContent.ai_captions?.length || 0 }} captions
              from {{ generatedContent.rows_processed }} products
            </p>
            <div class="row">
              <div 
                v-for="(item, idx) in generatedContent.ai_captions"
                :key="idx"
                class="col-md-6 mb-4"
              >
                <div class="card h-100">
                  <div class="card-body">
                    <!-- Product Image (if available) -->
                    <div v-if="item.has_image" class="text-center mb-3">
                      <div class="badge bg-success">
                        <i class="bi bi-image me-1"></i>Image Used
                      </div>
                    </div>
                    
                    <!-- Product Info -->
                    <h6 class="card-title">{{ item.product }}</h6>
                    <div class="mb-2">
                      <span class="badge bg-light text-dark me-2">{{ item.category }}</span>
                      <span class="badge bg-success">₹{{ item.price }}</span>
                    </div>
                    <p v-if="item.description" class="text-muted small mb-2">{{ item.description }}</p>
                    
                    <!-- Poster Information -->
                    <div v-if="item.poster_path" class="mb-3">
                      <div class="d-flex align-items-center mb-2">
                        <small class="text-muted me-2">Poster:</small>
                        <span :class="`badge ${getGenerationMethodBadgeClass(item.generation_method)}`">
                          <i :class="`bi ${getGenerationMethodIcon(item.generation_method)} me-1`"></i>
                          {{ item.generation_method || 'generated' }}
                        </span>
                      </div>
                      <div class="border rounded p-2 bg-light text-center" style="height: 120px;">
                        <img 
                          v-if="item.poster_path"
                          :src="getImageUrl(item.poster_path)"
                          :alt="`Poster for ${item.product}`"
                          class="img-fluid rounded"
                          style="max-height: 110px; object-fit: contain;"
                          @error="handleImageError"
                        />
                        <div v-else class="text-muted d-flex align-items-center justify-content-center h-100">
                          <small>No poster available</small>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Generated Caption -->
                    <div class="caption-box bg-light p-2 rounded mb-3">
                      <p class="small mb-0">{{ item.caption }}</p>
                    </div>
                    
                    <!-- Actions -->
                    <div class="d-flex gap-2">
                      <button
                        class="btn btn-outline-primary btn-sm flex-fill"
                        @click="copyToClipboard(item.caption)"
                      >
                        <i class="bi bi-clipboard me-1"></i> Copy
                      </button>
                      <button
                        v-if="item.poster_path"
                        class="btn btn-outline-secondary btn-sm"
                        @click="downloadImage(item.poster_path)"
                      >
                        <i class="bi bi-download"></i>
                      </button>
                    </div>
                  </div>
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
import { 
  generateMarketingContent, 
  getMarketingTemplate, 
  getGenerationProgress, 
  resetGenerationProgress,
  getMarketingHistory, 
  deleteMarketingHistoryItem 
} from '@/api/apiMarketing';

const loading = ref(false);
const error = ref('');
const generatedContent = ref(null);

// Image generation settings
const selectedAspectRatio = ref('');
const batchSize = ref(3);

// Progress tracking state
const progressStatus = ref('');
const currentStep = ref('');
const currentItem = ref(0);
const totalItems = ref(0);
const batchProgress = ref(0);
const totalBatches = ref(0);
const progressPercentage = ref(0);
const progressErrors = ref([]);
const elapsedTime = ref(0);
let progressInterval = null;

// Upload type management
const uploadType = ref('csv'); // 'csv' or 'single'

// Single image upload state
const singleImagePreview = ref('');
const singleProduct = ref({
  name: '',
  category: '',
  price: '',
  description: ''
});

// Template state
const templateLoading = ref(false);

// History state
const showHistory = ref(false);
const marketingHistory = ref([]);
const historyLoading = ref(false);
const historyError = ref('');

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

  // Handle image preview for single image upload
  if (uploadType.value === 'single' && file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      singleImagePreview.value = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  await processFile(file);
};

/**
 * Handle file drop
 */
const handleFileDrop = async (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;

  // Handle image preview for single image upload
  if (uploadType.value === 'single' && file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      singleImagePreview.value = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  await processFile(file);
};

/**
 * Reset form when switching upload types
 */
const resetForm = () => {
  error.value = '';
  generatedContent.value = null;
  singleImagePreview.value = '';
  singleProduct.value = {
    name: '',
    category: '',
    price: '',
    description: ''
  };
  
  // Reset progress tracking
  stopProgressTracking();
  progressStatus.value = '';
  currentStep.value = '';
  currentItem.value = 0;
  totalItems.value = 0;
  batchProgress.value = 0;
  totalBatches.value = 0;
  progressPercentage.value = 0;
  progressErrors.value = [];
  elapsedTime.value = 0;
};

/**
 * Start progress tracking
 */
const startProgressTracking = () => {
  // Reset progress state
  progressStatus.value = '';
  currentStep.value = '';
  currentItem.value = 0;
  totalItems.value = 0;
  batchProgress.value = 0;
  totalBatches.value = 0;
  progressPercentage.value = 0;
  progressErrors.value = [];
  elapsedTime.value = 0;
  
  // Start polling for progress updates
  progressInterval = setInterval(async () => {
    try {
      const response = await getGenerationProgress();
      const progress = response.data;
      
      progressStatus.value = progress.status;
      currentStep.value = progress.current_step;
      currentItem.value = progress.current_item;
      totalItems.value = progress.total_items;
      batchProgress.value = progress.batch_progress;
      totalBatches.value = progress.total_batches;
      progressPercentage.value = progress.progress_percentage || 0;
      progressErrors.value = progress.errors || [];
      elapsedTime.value = progress.elapsed_time || 0;
      
      // Stop tracking when completed
      if (progress.status === 'completed' || progress.status === 'idle') {
        stopProgressTracking();
      }
    } catch (err) {
      console.error('Progress tracking error:', err);
    }
  }, 1000); // Update every second
};

/**
 * Stop progress tracking
 */
const stopProgressTracking = () => {
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }
};

/**
 * Format time display
 */
const formatTime = (seconds) => {
  if (!seconds) return '0s';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
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

  // Handle single image upload
  if (uploadType.value === 'single') {
    // Validate single image fields
    if (!singleProduct.value.name || !singleProduct.value.category || !singleProduct.value.price) {
      showToastMessage('Please fill in all required product fields', 'bi bi-exclamation-circle-fill');
      return;
    }

    // Validate file type for single image
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!imageExtensions.includes(fileExt)) {
      showToastMessage('Please upload an image file (JPG, PNG, WEBP)', 'bi bi-exclamation-circle-fill');
      return;
    }
  } else {
    // Validate file type for CSV
    const csvExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!csvExtensions.includes(fileExt)) {
      showToastMessage('Please upload a CSV or Excel file', 'bi bi-exclamation-circle-fill');
      return;
    }
  }

  loading.value = true;
  error.value = '';
  generatedContent.value = null;

  // Start progress tracking for CSV uploads
  if (uploadType.value === 'csv') {
    startProgressTracking();
  }

  try {
    // Create FormData with additional fields for single image
    const formData = new FormData();
    formData.append('file', file);
    
    if (uploadType.value === 'single') {
      formData.append('product_name', singleProduct.value.name);
      formData.append('product_category', singleProduct.value.category);
      formData.append('product_price', singleProduct.value.price);
      formData.append('product_description', singleProduct.value.description);
    }
    
    // Add generation options
    if (selectedAspectRatio.value) {
      formData.append('aspect_ratio', selectedAspectRatio.value);
    }
    if (batchSize.value) {
      formData.append('batch_size', parseInt(batchSize.value));
    }

    const response = await generateMarketingContent(formData);
    if (response.data) {
      generatedContent.value = response.data;
      showToastMessage('Marketing content generated successfully!', 'bi bi-check-circle-fill');
      
      // Refresh history if it's visible
      if (showHistory.value) {
        await fetchMarketingHistory();
      }
    }
  } catch (err) {
    console.error('[Marketing Error]', err);
    error.value = err.response?.data?.message || 'Failed to generate content';
    showToastMessage(error.value, 'bi bi-exclamation-circle-fill');
  } finally {
    loading.value = false;
    stopProgressTracking();
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
 * Handle image loading errors
 */
const handleImageError = (event) => {
  console.error('Image failed to load:', event.target.src);
  event.target.style.display = 'none';
  const parent = event.target.parentElement;
  if (parent) {
    parent.innerHTML = `
      <div class="text-center text-muted">
        <div class="mb-2"><i class="bi bi-exclamation-triangle fs-3"></i></div>
        <div class="small">
          <strong>Failed to load poster</strong><br>
          <span class="text-muted">Image file not found or server error</span>
        </div>
      </div>
    `;
  }
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
    showToastMessage('Copy failed', 'bi bi-exclamation-circle-fill');
  }
};

/**
 * Download template file
 */
const downloadTemplate = async () => {
  templateLoading.value = true;
  try {
    const response = await getMarketingTemplate();
    if (response.data.status === 'success') {
      const link = document.createElement('a');
      link.href = getImageUrl(response.data.template_url);
      link.download = 'marketing_template.csv';
      link.click();
      showToastMessage('Template downloaded successfully!', 'bi bi-check-circle-fill');
    }
  } catch (err) {
    console.error('[Template Error]', err);
    showToastMessage('Failed to download template', 'bi bi-exclamation-circle-fill');
  } finally {
    templateLoading.value = false;
  }
};

/**
 * Fetch marketing history
 */
const fetchMarketingHistory = async () => {
  historyLoading.value = true;
  historyError.value = '';
  
  try {
    const response = await getMarketingHistory();
    if (response.data.status === 'success') {
      marketingHistory.value = response.data.data;
    }
  } catch (err) {
    console.error('[History Error]', err);
    historyError.value = 'Failed to load history';
  } finally {
    historyLoading.value = false;
  }
};

/**
 * Delete marketing history item
 */
const deleteHistoryItem = async (itemId) => {
  if (!confirm('Are you sure you want to delete this history item?')) {
    return;
  }
  
  try {
    const response = await deleteMarketingHistoryItem(itemId);
    if (response.data.status === 'success') {
      showToastMessage('History item deleted successfully!', 'bi bi-check-circle-fill');
      // Refresh the history list
      await fetchMarketingHistory();
    }
  } catch (err) {
    console.error('[Delete Error]', err);
    showToastMessage('Failed to delete history item', 'bi bi-exclamation-circle-fill');
  }
};

/**
 * Toggle history visibility with auto-refresh
 */
const toggleHistory = async () => {
  showHistory.value = !showHistory.value;
  if (showHistory.value) {
    await fetchMarketingHistory();
  }
};

/**
 * View history item
 */
const viewHistoryItem = (item) => {
  if (item.status === 'completed' && item.generated_content) {
    generatedContent.value = item.generated_content;
    error.value = '';
    // Scroll to generated content
    setTimeout(() => {
      const element = document.querySelector('.generated-content');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  }
};

/**
 * Format date
 */
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Get file icon
 */
const getFileIcon = (fileType) => {
  switch (fileType) {
    case 'csv':
    case 'xlsx':
      return 'bi bi-file-earmark-spreadsheet text-success';
    case 'image':
      return 'bi bi-file-earmark-image text-primary';
    default:
      return 'bi bi-file-earmark text-muted';
  }
};

/**
 * Get status badge class
 */
const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'completed':
      return 'badge bg-success';
    case 'failed':
      return 'badge bg-danger';
    default:
      return 'badge bg-warning';
  }
};

/**
 * Get generation method message
 */
const getGenerationMethodMessage = (method) => {
  const messages = {
    'failed': 'AI services unavailable. Please check API configuration.',
    'text_based': 'Basic AI generation with optimized prompt.',
    'ai_context': 'AI generation with enhanced product details.'
  };
  return messages[method] || 'Generation method unknown.';
};

/**
 * Get generation method badge class
 */
const getGenerationMethodBadgeClass = (method) => {
  const classes = {
    'failed': 'bg-danger',
    'text_based': 'bg-warning',
    'ai_context': 'bg-success'
  };
  return classes[method] || 'bg-secondary';
};

/**
 * Get generation method icon
 */
const getGenerationMethodIcon = (method) => {
  const icons = {
    'failed': 'bi-exclamation-triangle',
    'text_based': 'bi-cpu',
    'ai_context': 'bi-magic'
  };
  return icons[method] || 'bi-question-circle';
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
    rgba(74, 144, 226, 0.05) 0%,
    rgba(179, 217, 255, 0.05) 100%
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
  box-shadow: 0 8px 20px rgba(74, 144, 226, 0.15);
}

.border.rounded {
  border-radius: 12px !important;
  border-color: rgba(74, 144, 226, 0.2) !important;
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
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.35);
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

.caption-box {
  border-left: 4px solid var(--color-primary);
  font-style: italic;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.btn-group .btn {
  border-radius: 0;
}

.btn-group .btn:first-child {
  border-top-left-radius: 0.375rem;
  border-bottom-left-radius: 0.375rem;
}

.btn-group .btn:last-child {
  border-top-right-radius: 0.375rem;
  border-bottom-right-radius: 0.375rem;
}

.btn-outline-danger:hover {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
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

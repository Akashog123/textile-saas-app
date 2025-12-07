<template>
  <div class="shop-inventory-tab">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0"><i class="bi bi-box-seam me-2"></i>Sales Inventory</h5>
      <div class="d-flex gap-2">
        <button class="btn btn-gradient btn-sm" @click="openInventoryUpdateModal" :disabled="loading">
          <i class="bi bi-database-add me-1"></i>Inventory Update
        </button>
        <button class="btn btn-outline-gradient btn-sm" @click="handleExport" :disabled="loading">
          <i class="bi bi-download me-1"></i> Export Inventory
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading inventory...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    </div>

    <!-- Inventory Table -->
    <div v-else class="card">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>S. No.</th>
                <th>Image</th>
                <th>Product Name</th>
                <th>Sales QTY</th>
                <th>Unit Price</th>
                <th>Stock</th>
                <th>Min Stock</th>
                <th>Status</th>
                <th>SKU ID</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in inventoryData" :key="item.id || idx">
                <td>{{ idx + 1 }}</td>
                <td>
                  <div class="product-thumbnail">
                    <img 
                      :src="getProductImage(item)" 
                      :alt="item.name"
                      @error="handleImageError($event, item)"
                    />
                  </div>
                </td>
                <td>
                  <div class="product-name-cell">
                    <strong>{{ item.name }}</strong>
                    <small class="d-block text-muted">{{ item.category }}</small>
                  </div>
                </td>
                <td>
                  <span class="qty-badge">{{ item.qty }}</span>
                </td>
                <td>
                  <strong class="price-text">{{ item.price }}</strong>
                </td>
                <td>
                  <div class="stock-info">
                    <span class="stock-amount" :class="getStockClass(item.stock, item.minimumStock)">{{ item.stock }}</span>
                  </div>
                </td>
                <td>
                  <span class="min-stock-badge">{{ item.minimumStock || 0 }}</span>
                </td>
                <td>
                  <span class="stock-status" :class="getStockStatusClass(item.stock, item.minimumStock)">
                    {{ getStockStatus(item.stock, item.minimumStock) }}
                  </span>
                </td>
                <td>
                  <code class="sku-code">{{ item.sku }}</code>
                </td>
                <td>
                  <div class="action-buttons">
                    <button
                      class="btn btn-sm btn-outline-secondary"
                      title="Edit"
                      @click="openEditModal(item)"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button
                      class="btn btn-sm btn-outline-danger"
                      title="Delete"
                      @click="openDeleteModal(item)"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="inventoryData.length === 0">
                <td colspan="10" class="text-center text-muted py-4">
                  <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                  No inventory items found. Click Import to add products.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="d-flex justify-content-between align-items-center mt-3">
          <div class="inventory-stats">
            <span class="stat-item">
              <i class="bi bi-box-seam-fill"></i>
              <strong>{{ inventoryData.length }}</strong> Products
            </span>
            <span class="stat-item">
              <i class="bi bi-graph-up-arrow"></i>
              <strong>{{ totalQuantity }}</strong> Total Units Sold
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="modal-dialog" @click.stop>
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Product</h5>
            <button class="btn-close" @click="closeEditModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Product Name</label>
              <input type="text" class="form-control" v-model="editForm.name" disabled />
            </div>
            <div class="mb-3">
              <label class="form-label">Price (per unit)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="editForm.price"
                step="0.01"
                min="0"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">Stock (units)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="editForm.stock"
                min="0"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">Minimum Stock (units)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="editForm.minimumStock"
                min="0"
              />
            </div>
            
            <!-- Product Images Section -->
            <div class="mb-3">
              <label class="form-label d-flex justify-content-between align-items-center">
                <span><i class="bi bi-images me-2"></i>Product Images</span>
                <span class="badge bg-secondary">{{ productImages.length }}/4</span>
              </label>
              
              <!-- Loading state -->
              <div v-if="loadingProductImages" class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary"></div>
                <span class="ms-2 text-muted small">Loading images...</span>
              </div>
              
              <!-- Images grid -->
              <div v-else>
                <div class="row g-2 mb-2">
                  <div v-for="(img, idx) in productImages" :key="img.id" class="col-3">
                    <div class="position-relative product-image-thumb">
                      <img 
                        :src="getImageUrl(img.url)" 
                        :alt="img.alt" 
                        class="img-fluid rounded"
                        @error="(e) => e.target.src = `https://placehold.co/100x100?text=Image`"
                      />
                      <span v-if="idx === 0" class="position-absolute top-0 start-0 badge bg-primary" style="font-size: 0.6rem;">Primary</span>
                      <div class="image-actions position-absolute bottom-0 end-0 p-1">
                        <button v-if="idx !== 0" type="button" class="btn btn-xs btn-light me-1" @click="handleSetPrimaryImage(img.id)" :disabled="imageActionLoading" title="Set as primary">
                          <i class="bi bi-star" style="font-size: 0.65rem;"></i>
                        </button>
                        <button type="button" class="btn btn-xs btn-danger" @click="handleDeleteProductImage(img.id)" :disabled="imageActionLoading" title="Delete">
                          <i class="bi bi-trash" style="font-size: 0.65rem;"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Upload button -->
                  <div v-if="productImages.length < 4" class="col-3">
                    <label class="upload-placeholder d-flex flex-column align-items-center justify-content-center border border-dashed rounded text-muted" :class="{ 'opacity-50': uploadingProductImages }">
                      <input type="file" accept="image/*" multiple class="d-none" @change="handleProductImageUpload" :disabled="uploadingProductImages" />
                      <span v-if="uploadingProductImages"><span class="spinner-border spinner-border-sm"></span></span>
                      <span v-else>
                        <i class="bi bi-plus-lg"></i>
                        <small class="d-block" style="font-size: 0.65rem;">Add</small>
                      </span>
                    </label>
                  </div>
                </div>
                
                <small v-if="productImages.length === 0" class="text-muted">No images. Click + to add up to 4 images.</small>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeEditModal">Cancel</button>
            <button class="btn btn-primary" @click="saveEdit" :disabled="saving">
              <span v-if="saving">Saving...</span>
              <span v-else>Save Changes</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal-dialog" @click.stop>
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Delete</h5>
            <button class="btn-close" @click="closeDeleteModal"></button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete <strong>{{ deleteItem?.name }}</strong>?</p>
            <p class="text-muted small">This action cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeDeleteModal">Cancel</button>
            <button class="btn btn-danger" @click="confirmDelete" :disabled="deleting">
              <span v-if="deleting">Deleting...</span>
              <span v-else>Delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Inventory Update Modal -->
    <div v-if="showInventoryUpdateModal" class="modal-overlay" @click="closeInventoryUpdateModal">
      <div class="modal-dialog modal-lg" @click.stop>
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Update Inventory</h5>
            <button class="btn-close" @click="closeInventoryUpdateModal"></button>
          </div>
          <div class="modal-body">
            <!-- Step 1 -->
            <div class="step-section mb-4">
                <h6><span class="badge rounded me-2">1</span>Prepare Data</h6>
                <p class="text-muted small mb-2">Download the template to ensure your data is formatted correctly.</p>
                <button class="btn btn-sm btn-gradient" @click="handleDownloadTemplate">
                    <i class="bi bi-file-earmark-arrow-down me-1"></i> Download CSV Template
                </button>
            </div>
            <hr class="text-muted opacity-25">

            <!-- Step 2 -->
            <div class="step-section mb-4">
                <h6><span class="badge rounded me-2">2</span>Upload Inventory Data</h6>
                <p class="text-muted small mb-2">Upload your filled CSV or Excel file. Supported formats: .csv, .xlsx, .xls</p>
                
                <div class="d-flex align-items-center gap-3">
                    <input type="file" class="form-control form-control-sm" ref="inventoryFileInput" accept=".csv,.xlsx,.xls" @change="onInventoryFileSelect">
                    <button class="btn btn-sm btn-gradient" @click="uploadInventoryFile" :disabled="!selectedInventoryFile || inventoryUploading">
                        <span v-if="inventoryUploading" class="spinner-border spinner-border-sm me-1"></span>
                        Upload
                    </button>
                </div>
                <div v-if="inventoryUploadStatus" class="mt-2 small" :class="inventoryUploadStatus.type === 'success' ? 'text-success' : 'text-danger'">
                    <i :class="inventoryUploadStatus.type === 'success' ? 'bi bi-check-circle' : 'bi bi-exclamation-circle'"></i>
                    {{ inventoryUploadStatus.message }}
                </div>
            </div>
            <hr class="text-muted opacity-25">

            <!-- Step 3 -->
            <div class="step-section">
                <h6><span class="badge rounded me-2">3</span>Upload Product Images (Optional)</h6>
                
                <div class="alert alert-light border mb-3 p-3 bg-light">
                  <h6 class="alert-heading h6 mb-2"><i class="bi bi-info-circle me-2"></i>Format Instructions</h6>
                  <ul class="mb-0 small text-muted ps-3">
                    <li>Create a <strong>ZIP file</strong> containing your product images.</li>
                    <li><strong>Naming Convention:</strong>
                      <ul class="ps-3 mt-1 mb-1">
                        <li>Single image: <code>SKU.jpg</code> (e.g., <em>COT-001.jpg</em>)</li>
                        <li>Multiple images: <code>SKU_1.jpg</code>, <code>SKU_2.jpg</code> (e.g., <em>COT-001_1.jpg</em>)</li>
                      </ul>
                    </li>
                    <li>Supported formats: <strong>.jpg, .jpeg, .png, .webp</strong></li>
                    <li>Max 4 images per product. Max ZIP size: <strong>50MB</strong>.</li>
                  </ul>
                </div>
                
                <div class="d-flex align-items-center gap-3">
                    <input type="file" class="form-control form-control-sm" ref="imageZipInput" accept=".zip" @change="onZipFileSelect">
                    <button class="btn btn-sm btn-gradient" @click="uploadImageZip" :disabled="!selectedZipFile || zipUploading">
                        <span v-if="zipUploading" class="spinner-border spinner-border-sm me-1"></span>
                        Upload
                    </button>
                </div>
                 <div v-if="zipUploadStatus" class="mt-2 small" :class="zipUploadStatus.type === 'success' ? 'text-success' : 'text-danger'">
                    <i :class="zipUploadStatus.type === 'success' ? 'bi bi-check-circle' : 'bi bi-exclamation-circle'"></i>
                    {{ zipUploadStatus.message }}
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
import { ref, computed, onMounted } from 'vue';
import { getInventory, importInventory, editInventoryItem, deleteInventoryItem, exportInventory, downloadInventoryTemplate, getProductImages, deleteProductImage, setProductPrimaryImage, bulkUploadProductImages } from '@/api/apiInventory';

// Loading and error states
const loading = ref(false);
const error = ref('');
const saving = ref(false);
const deleting = ref(false);

// Data
const inventoryData = ref([]);

// Shop ID - get from user's primary shop, then fallback to shop_id, then user.id
const shopId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  // Priority: primary_shop_id > shop_id > first shop from shops array
  return user.primary_shop_id || user.shop_id || (user.shops && user.shops[0]?.id) || null;
});

// Check if shop is available
const hasShop = computed(() => shopId.value !== null && shopId.value !== undefined);

// Modals
const showEditModal = ref(false);
const showDeleteModal = ref(false);
const showInventoryUpdateModal = ref(false);
const editForm = ref({ id: null, name: '', price: 0, stock: 0, minimumStock: 0 });
const deleteItem = ref(null);

// Inventory Update Modal State
const inventoryFileInput = ref(null);
const imageZipInput = ref(null);
const selectedInventoryFile = ref(null);
const selectedZipFile = ref(null);
const inventoryUploading = ref(false);
const zipUploading = ref(false);
const inventoryUploadStatus = ref(null);
const zipUploadStatus = ref(null);

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

// Product images state
const productImages = ref([]);
const loadingProductImages = ref(false);
const uploadingProductImages = ref(false);
const imageActionLoading = ref(false);

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001';

/**
 * Check if URL is from our local API (might have wrong port)
 */
const isLocalApiUrl = (url) => {
  if (!url) return false;
  // Check if it's a localhost/127.0.0.1 URL (our API)
  return url.includes('127.0.0.1') || url.includes('localhost');
};

/**
 * Extract path from URL - only for local API URLs
 * Fixes issue where DB may have stored URLs with wrong port
 */
const extractImagePath = (url) => {
  if (!url) return null;
  // Only extract path from local API URLs (to fix wrong port issue)
  if (isLocalApiUrl(url)) {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname; // Returns just the path like /uploads/product_images/...
    } catch {
      return url;
    }
  }
  // For external URLs (like placehold.co), return as-is
  return url;
};

/**
 * Get product image URL - matches Marketing page logic
 * Checks both image_url and image fields, resolves relative paths
 */
const getProductImage = (product) => {
  // Check for image_url or image field (backend may return either)
  const rawUrl = product?.image_url || product?.image;
  if (rawUrl) {
    // If it's an external URL (not our API), use directly
    if (rawUrl.startsWith('http') && !isLocalApiUrl(rawUrl)) {
      return rawUrl;
    }
    // Extract path from local API URL (fixes wrong port) or use relative path
    const path = extractImagePath(rawUrl);
    if (path && path.startsWith('/')) {
      return `${API_BASE}${path}`;
    }
    // Fallback - use as-is
    return rawUrl;
  }
  // Return placeholder with product name
  return `https://placehold.co/100x100?text=${encodeURIComponent(product?.name?.substring(0, 10) || 'Product')}`;
};

/**
 * Resolve image URL to full URL (for modal images)
 */
const getImageUrl = (url) => {
  if (!url) return '';
  // External URLs (like placehold.co) - use directly
  if (url.startsWith('http') && !isLocalApiUrl(url)) {
    return url;
  }
  // Local API URL - extract path and rebuild with correct base
  const path = extractImagePath(url);
  if (path && path.startsWith('/')) {
    return `${API_BASE}${path}`;
  }
  return url;
};

/**
 * Handle image load errors by showing a placeholder
 */
const handleImageError = (event, item) => {
  // Prevent infinite loop - only set fallback if not already a placeholder
  if (!event.target.src.includes('placehold.co')) {
    event.target.src = `https://placehold.co/100x100?text=${encodeURIComponent(item?.name?.substring(0, 10) || 'Product')}`;
  }
};

const fetchProductImages = async (productId) => {
  if (!productId) {
    productImages.value = [];
    return;
  }
  loadingProductImages.value = true;
  try {
    const res = await getProductImages(productId);
    if (res?.data?.status === 'success') {
      productImages.value = res.data.images || [];
    } else {
      productImages.value = [];
    }
  } catch (err) {
    console.error('Error fetching product images:', err);
    productImages.value = [];
  } finally {
    loadingProductImages.value = false;
  }
};

const handleProductImageUpload = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  
  const productId = editForm.value.id;
  if (!productId) return;
  
  const remainingSlots = 4 - productImages.value.length;
  if (files.length > remainingSlots) {
    showToastMessage(`Only ${remainingSlots} slot(s) remaining`, 'bi bi-exclamation-circle-fill');
    event.target.value = '';
    return;
  }
  
  uploadingProductImages.value = true;
  try {
    const res = await editInventoryItem(productId, {}, files);
    if (res?.data?.status === 'success') {
      showToastMessage(res.data.message || 'Images uploaded!', 'bi bi-check-circle-fill');
      await fetchProductImages(productId);
      await fetchInventory(); // Refresh main list to show updated image
    } else {
      showToastMessage(res?.data?.message || 'Upload failed', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('Error uploading images:', err);
    showToastMessage(err?.response?.data?.message || 'Upload failed', 'bi bi-exclamation-circle-fill');
  } finally {
    uploadingProductImages.value = false;
    event.target.value = '';
  }
};

const handleDeleteProductImage = async (imageId) => {
  const productId = editForm.value.id;
  if (!productId || !imageId) return;
  
  deleteItem.value = { id: imageId, name: 'this image', type: 'image', productId: productId };
  showDeleteModal.value = true;
};

const handleSetPrimaryImage = async (imageId) => {
  const productId = editForm.value.id;
  if (!productId || !imageId) return;
  
  imageActionLoading.value = true;
  try {
    const res = await setProductPrimaryImage(productId, imageId);
    if (res?.data?.status === 'success') {
      await fetchProductImages(productId);
      await fetchInventory();
      showToastMessage('Primary image updated', 'bi bi-check-circle-fill');
    } else {
      showToastMessage(res?.data?.message || 'Failed', 'bi bi-exclamation-circle-fill');
    }
  } catch (err) {
    console.error('Error setting primary image:', err);
    showToastMessage('Failed to set primary image', 'bi bi-exclamation-circle-fill');
  } finally {
    imageActionLoading.value = false;
  }
};

/**
 * Fetch inventory from backend
 */
const fetchInventory = async () => {
  if (!shopId.value) {
    error.value = 'Shop ID not found. Please log in again.';
    return;
  }

  loading.value = true;
  error.value = '';
  try {
    const response = await getInventory(shopId.value);
    if (response.data && response.data.status === 'success') {
      const products = response.data.data || [];
      inventoryData.value = products.map(p => ({
        id: p.id,
        name: p.name,
        category: p.category || 'Uncategorized',
        image: p.image_url || p.image || null,
        image_url: p.image_url || p.image || null,
        qty: p.sales_qty || 0,
        price: p.price ? `₹${parseFloat(p.price).toLocaleString()}` : '₹0',
        priceRaw: parseFloat(p.price) || 0,
        stock: p.stock || 0,
        minimumStock: p.minimum_stock || 0,
        sku: p.sku || 'N/A',
        rating: p.rating || 0
      }));
    }
  } catch (err) {
    console.error('[Inventory Error]', err);
    error.value = err.response?.data?.message || 'Failed to load inventory';
  } finally {
    loading.value = false;
  }
};

/**
 * Download CSV template for inventory import
 */
const handleDownloadTemplate = async () => {
  try {
    const response = await downloadInventoryTemplate();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'inventory_template.csv';
    link.click();
    window.URL.revokeObjectURL(url);
    showToastMessage('Template downloaded! Fill in your data and upload.', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[Template Download Error]', err);
    showToastMessage('Failed to download template', 'bi bi-exclamation-circle-fill');
  }
};

/**
 * Inventory Update Modal Functions
 */
const openInventoryUpdateModal = () => {
  showInventoryUpdateModal.value = true;
  // Reset states
  selectedInventoryFile.value = null;
  selectedZipFile.value = null;
  inventoryUploadStatus.value = null;
  zipUploadStatus.value = null;
  if (inventoryFileInput.value) inventoryFileInput.value.value = '';
  if (imageZipInput.value) imageZipInput.value.value = '';
};

const closeInventoryUpdateModal = () => {
  showInventoryUpdateModal.value = false;
};

const onInventoryFileSelect = (event) => {
  const file = event.target.files[0];
  if (!file) {
    selectedInventoryFile.value = null;
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    inventoryUploadStatus.value = { type: 'error', message: 'File too large (max 16MB)' };
    event.target.value = '';
    selectedInventoryFile.value = null;
    return;
  }
  selectedInventoryFile.value = file;
  inventoryUploadStatus.value = null;
};

const uploadInventoryFile = async () => {
  if (!hasShop.value || !selectedInventoryFile.value) return;

  inventoryUploading.value = true;
  inventoryUploadStatus.value = null;

  try {
    const response = await importInventory(shopId.value, selectedInventoryFile.value);
    const data = response.data;
    let msg = 'Inventory uploaded successfully!';
    if (data?.added !== undefined || data?.updated !== undefined) {
      msg = `Success! Added: ${data.added || 0}, Updated: ${data.updated || 0}`;
    }
    inventoryUploadStatus.value = { type: 'success', message: msg };
    showToastMessage(msg, 'bi bi-check-circle-fill');
    await fetchInventory();
  } catch (err) {
    console.error('[Inventory Upload Error]', err);
    const errorMsg = err.response?.data?.message || 'Upload failed';
    const hint = err.response?.data?.hint || '';
    inventoryUploadStatus.value = { type: 'error', message: hint ? `${errorMsg}. ${hint}` : errorMsg };
  } finally {
    inventoryUploading.value = false;
  }
};

const onZipFileSelect = (event) => {
  const file = event.target.files[0];
  if (!file) {
    selectedZipFile.value = null;
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    zipUploadStatus.value = { type: 'error', message: 'ZIP file too large (max 50MB)' };
    event.target.value = '';
    selectedZipFile.value = null;
    return;
  }
  selectedZipFile.value = file;
  zipUploadStatus.value = null;
};

const uploadImageZip = async () => {
  if (!hasShop.value || !selectedZipFile.value) return;

  zipUploading.value = true;
  zipUploadStatus.value = null;

  try {
    const response = await bulkUploadProductImages(shopId.value, selectedZipFile.value);
    const data = response.data;
    
    let message = `Images uploaded! ${data.matched || 0} products updated with ${data.images_added || 0} images.`;
    if (data.skipped && data.skipped.length > 0) {
      message += ` (${data.skipped.length} skipped)`;
    }
    
    zipUploadStatus.value = { type: 'success', message: message };
    showToastMessage('Images uploaded successfully', 'bi bi-check-circle-fill');
    await fetchInventory();
  } catch (err) {
    console.error('[Bulk Image Upload Error]', err);
    zipUploadStatus.value = { type: 'error', message: err.response?.data?.message || 'Upload failed' };
  } finally {
    zipUploading.value = false;
  }
};

/**
 * Handle initial inventory upload (Legacy - kept for reference if needed, but UI now uses modal)
 */
const handleInitialInventoryUpload = () => {
  openInventoryUpdateModal();
};

/**
 * Handle import (Legacy)
 */
const handleImport = () => {
  openInventoryUpdateModal();
};

/**
 * Handle export
 */
const handleExport = async () => {
  try {
    loading.value = true;
    const response = await exportInventory(shopId.value);
    
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `inventory_${shopId.value}_${new Date().toISOString().split('T')[0]}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);

    showToastMessage('Inventory exported successfully!', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[Export Error]', err);
    showToastMessage(err.response?.data?.message || 'Export failed', 'bi bi-exclamation-circle-fill');
  } finally {
    loading.value = false;
  }
};

/**
 * Handle bulk image upload via ZIP file (Legacy - UI uses modal)
 */
const handleBulkImageUpload = () => {
  openInventoryUpdateModal();
};

/**
 * Open edit modal
 */
const openEditModal = (item) => {
  editForm.value = {
    id: item.id,
    name: item.name,
    price: item.priceRaw,
    stock: item.stock,
    minimumStock: item.minimumStock || 0
  };
  showEditModal.value = true;
  fetchProductImages(item.id);
};

/**
 * Close edit modal
 */
const closeEditModal = () => {
  showEditModal.value = false;
  editForm.value = { id: null, name: '', price: 0, stock: 0, minimumStock: 0 };
  productImages.value = [];
};

/**
 * Save edit
 */
const saveEdit = async () => {
  if (editForm.value.price < 0 || editForm.value.stock < 0 || editForm.value.minimumStock < 0) {
    showToastMessage('Price, stock, and minimum stock must be non-negative', 'bi bi-exclamation-circle-fill');
    return;
  }

  saving.value = true;
  try {
    await editInventoryItem(editForm.value.id, {
      price: editForm.value.price,
      stock: editForm.value.stock,
      minimum_stock: editForm.value.minimumStock
    });
    showToastMessage('Product updated successfully!', 'bi bi-check-circle-fill');
    closeEditModal();
    await fetchInventory();
  } catch (err) {
    console.error('[Edit Error]', err);
    showToastMessage(err.response?.data?.message || 'Update failed', 'bi bi-exclamation-circle-fill');
  } finally {
    saving.value = false;
  }
};

/**
 * Open delete modal
 */
const openDeleteModal = (item) => {
  deleteItem.value = item;
  showDeleteModal.value = true;
};

/**
 * Close delete modal
 */
const closeDeleteModal = () => {
  showDeleteModal.value = false;
  deleteItem.value = null;
};

/**
 * Confirm delete
 */
const confirmDelete = async () => {
  if (!deleteItem.value) return;

  deleting.value = true;
  try {
    if (deleteItem.value.type === 'image') {
      // Handle image deletion
      const res = await deleteProductImage(deleteItem.value.productId, deleteItem.value.id);
      if (res?.data?.status === 'success') {
        await fetchProductImages(deleteItem.value.productId);
        await fetchInventory();
        showToastMessage('Image deleted', 'bi bi-check-circle-fill');
      } else {
        showToastMessage(res?.data?.message || 'Failed to delete', 'bi bi-exclamation-circle-fill');
      }
    } else {
      // Handle product deletion
      await deleteInventoryItem(deleteItem.value.id);
      showToastMessage('Product deleted successfully!', 'bi bi-check-circle-fill');
      await fetchInventory();
    }
    closeDeleteModal();
  } catch (err) {
    console.error('[Delete Error]', err);
    showToastMessage(err.response?.data?.message || 'Delete failed', 'bi bi-exclamation-circle-fill');
  } finally {
    deleting.value = false;
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

/**
 * Get stock class based on quantity (legacy function)
 */
const getStockClassLegacy = (stock) => {
  if (stock < 20) return 'low';
  if (stock < 50) return 'medium';
  return 'high';
};

/**
 * Compute total quantity
 */
const totalQuantity = computed(() => {
  return inventoryData.value.reduce((sum, item) => sum + item.qty, 0);
});

/**
 * Get stock status class based on stock levels
 */
const getStockClass = (stock, minStock) => {
  if (stock <= minStock) return 'stock-critical';
  if (stock <= minStock * 2) return 'stock-low';
  return 'stock-good';
};

/**
 * Get stock status text
 */
const getStockStatus = (stock, minStock) => {
  if (stock <= minStock) return 'Critical';
  if (stock <= minStock * 2) return 'Low';
  return 'Good';
};

/**
 * Get stock status class for badge
 */
const getStockStatusClass = (stock, minStock) => {
  if (stock <= minStock) return 'bg-danger';
  if (stock <= minStock * 2) return 'bg-warning';
  return 'bg-success';
};

// Fetch inventory on mount
onMounted(() => {
  fetchInventory();
});
</script>

<style scoped>
.shop-inventory-tab {
  background: var(--gradient-bg);
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

h5 {
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

.card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.table-responsive {
  border-radius: 12px;
  overflow: hidden;
}

.table {
  margin-bottom: 0;
}

.table th {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 1rem 0.75rem;
  border: none;
  white-space: nowrap;
}

.table tbody tr {
  transition: all 0.3s ease;
  border-bottom: 1px solid var(--color-bg-alt);
}

.table tbody tr:hover {
  background: linear-gradient(
    135deg,
    rgba(74, 144, 226, 0.05) 0%,
    rgba(179, 217, 255, 0.03) 100%
  );
  transform: scale(1.01);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.table td {
  padding: 0.75rem;
  vertical-align: middle;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.product-thumbnail {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid var(--color-bg-alt);
  transition: all 0.3s ease;
}

.product-thumbnail:hover {
  border-color: var(--color-primary);
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.25);
}

.product-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image-placeholder {
  width: 60px;
  height: 60px;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  color: #6c757d;
}

.no-image-placeholder i {
  font-size: 1.2rem;
}

.product-name-cell strong {
  color: var(--color-text-dark);
  font-weight: 600;
  font-size: 0.95rem;
}

.product-name-cell small {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}

.qty-badge {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  display: inline-block;
}

.price-text {
  color: #10b981;
  font-weight: 700;
  font-size: 1rem;
}

.stock-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  display: inline-block;
}

.stock-badge.high {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.stock-badge.medium {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.stock-badge.low {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

/* ===== Buttons ===== */
.btn-gradient {
  background: var(--gradient-primary);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: 12px;
  padding: 0.6rem 1.2rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.btn-gradient:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
  color: white;
}

.btn-gradient:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
  color: white;
}

.btn-outline-gradient {
  border: 2px solid transparent;
  background: linear-gradient(white, white) padding-box,
              var(--gradient-primary) border-box;
  color: var(--color-primary);
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.btn-outline-gradient:hover:not(:disabled) {
  background: var(--gradient-primary) padding-box,
              var(--gradient-primary) border-box;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.25);
}

.btn-outline-gradient:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-buttons .btn {
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.action-buttons .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.inventory-stats {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.stat-item i {
  font-size: 1.25rem;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-item strong {
  color: var(--color-text-dark);
  font-weight: 700;
  font-size: 1.1rem;
}

/* Stock Status Styles */
.stock-status.bg-danger {
  background-color: #f8d7da !important;
  color: #ff6b6b !important;
  font-weight: 700;
}

.stock-status.bg-warning {
  background-color: #fff3cd !important;
  color: #ffa94d !important;
  font-weight: 600;
}

.stock-status.bg-success {
  background-color: #d1e7dd !important;
  color: #51cf66 !important;
  font-weight: 500;
}

.min-stock-badge {
  background: rgba(13, 110, 253, 0.1);
  color: var(--color-primary);
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.stock-status {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-dialog {
  min-width: 400px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-bg-alt);
}

.modal-title {
  font-weight: 600;
  color: var(--color-text-dark);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-bg-alt);
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

/* Toast Notification */
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

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.25);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.35);
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
}

.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

@media (max-width: 768px) {
  .shop-inventory-tab {
    padding: 1rem;
  }

  .modal-dialog {
    min-width: 90%;
  }
}

/* Product Images in Edit Modal */
.product-image-thumb {
  height: 70px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
}
.product-image-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.product-image-thumb .image-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}
.product-image-thumb:hover .image-actions {
  opacity: 1;
}
.btn-xs {
  padding: 0.1rem 0.25rem;
  font-size: 0.65rem;
  line-height: 1;
}
.upload-placeholder {
  height: 70px;
  cursor: pointer;
  background: #f8f9fa;
  transition: all 0.2s ease;
}
.upload-placeholder:hover {
  border-color: var(--color-primary) !important;
  background: rgba(74, 144, 226, 0.05);
}
.border-dashed {
  border-style: dashed !important;
  border-width: 2px !important;
}
</style>

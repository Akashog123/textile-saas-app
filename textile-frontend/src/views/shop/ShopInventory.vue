<template>
  <div class="shop-inventory-tab">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0"><i class="bi bi-box-seam me-2"></i>Sales Inventory</h5>
      <div class="d-flex gap-2">
        <button class="btn btn-success btn-sm" @click="handleInitialInventoryUpload" :disabled="loading">
          <i class="bi bi-database-add me-1"></i> Initial Inventory Upload
        </button>
        <button class="btn btn-outline-primary btn-sm" @click="handlePDFReport" :disabled="loading">
          <i class="bi bi-file-earmark-pdf me-1"></i> PDF Report
        </button>
        <button class="btn btn-outline-secondary btn-sm" @click="handleExport" :disabled="loading">
          <i class="bi bi-download me-1"></i> Export Excel
        </button>
        <button class="btn btn-outline-info btn-sm" @click="openUploadLogsModal" :disabled="loading">
          <i class="bi bi-clock-history me-1"></i> Recent Uploads
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
                <th>Price/Meter</th>
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
                  <div class="product-thumbnail" v-if="item.image">
                    <img :src="item.image" :alt="item.name" />
                  </div>
                  <div class="no-image-placeholder" v-else>
                    <i class="bi bi-image"></i>
                  </div>
                </td>
                <td>
                  <div class="product-name-cell">
                    <strong>{{ item.name }}</strong>
                    <small class="d-block text-muted">{{ item.category }}</small>
                  </div>
                </td>
                <td>
                  <span class="qty-badge">{{ item.qty }} m</span>
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
              <strong>{{ totalQuantity }}</strong> Total Meters Sold
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
              <label class="form-label">Price (per meter)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="editForm.price"
                step="0.01"
                min="0"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">Stock (meters)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="editForm.stock"
                min="0"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">Minimum Stock (meters)</label>
              <input
                type="number"
                class="form-control"
                v-model.number="editForm.minimumStock"
                min="0"
              />
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

    <!-- Toast Notification -->
    <div v-if="showToast" class="toast-notification">
      <i :class="toastIcon" class="me-2"></i>
      {{ toastMessage }}
    </div>

    <!-- Upload Logs Modal -->
    <div v-if="showUploadLogsModal" class="modal-overlay" @click="closeUploadLogsModal">
      <div class="modal-dialog" style="max-width: 700px;" @click.stop>
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-clock-history me-2"></i>Recent Upload Activity</h5>
            <button class="btn-close" @click="closeUploadLogsModal"></button>
          </div>
          <div class="modal-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <p class="mb-0 text-muted small">Last 6 uploads with SLA insights.</p>
              <button class="btn btn-sm btn-outline-primary" @click="fetchUploadLogs" :disabled="uploadLogsLoading">
                <i class="bi bi-arrow-clockwise"></i>
                Refresh
              </button>
            </div>

            <div v-if="uploadLogsLoading" class="text-center py-4">
              <div class="spinner-border text-primary"></div>
              <p class="mt-2 mb-0">Fetching logs…</p>
            </div>
            <div v-else-if="uploadLogsError" class="alert alert-danger">
              <i class="bi bi-exclamation-triangle me-2"></i>{{ uploadLogsError }}
            </div>
            <div v-else-if="uploadLogs.length === 0" class="text-center py-4 text-muted">
              <i class="bi bi-inbox fs-1 d-block mb-2"></i>
              No uploads recorded yet.
            </div>
            <div v-else class="table-responsive">
              <table class="table table-sm align-middle">
                <thead>
                  <tr>
                    <th>Started</th>
                    <th>Status</th>
                    <th>Rows</th>
                    <th>Duration</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in uploadLogs" :key="log.id">
                    <td>
                      <small class="text-muted">{{ formatLogDate(log.started_at) }}</small>
                    </td>
                    <td>
                      <span :class="['badge', log.status === 'completed' ? 'bg-success-subtle text-success' : log.status === 'failed' ? 'bg-danger-subtle text-danger' : 'bg-warning-subtle text-warning']">
                        {{ log.status }}
                      </span>
                    </td>
                    <td>{{ log.rows_processed || 0 }}</td>
                    <td>
                      {{ log.duration_ms ? (log.duration_ms / 1000).toFixed(1) + 's' : '—' }}
                      <small v-if="log.sla_breached" class="text-danger d-block">SLA exceeded</small>
                    </td>
                    <td>
                      <small>{{ log.message || '—' }}</small>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getInventory, importInventory, editInventoryItem, deleteInventoryItem, exportInventory, generateInventoryPDF } from '@/api/apiInventory';
import { getSalesUploadLogs } from '@/api/apiShop';

// Loading and error states
const loading = ref(false);
const error = ref('');
const saving = ref(false);
const deleting = ref(false);

// Data
const inventoryData = ref([]);

// Shop ID
const shopId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  return user.shop_id || user.id;
});

// Modals
const showEditModal = ref(false);
const showDeleteModal = ref(false);
const showUploadLogsModal = ref(false);
const editForm = ref({ id: null, name: '', price: 0, stock: 0, minimumStock: 0 });
const deleteItem = ref(null);

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

// Upload logs state
const uploadLogs = ref([]);
const uploadLogsLoading = ref(false);
const uploadLogsError = ref('');

const formatLogDate = (timestamp) => {
  if (!timestamp) return '—';
  try {
    return new Date(timestamp).toLocaleString();
  } catch (err) {
    return timestamp;
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
        image: p.image || null,
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

const fetchUploadLogs = async () => {
  if (!shopId.value) return;
  uploadLogsLoading.value = true;
  uploadLogsError.value = '';
  try {
    const response = await getSalesUploadLogs(shopId.value, 6);
    if (response.data?.status === 'success') {
      uploadLogs.value = response.data.logs || [];
    } else {
      uploadLogsError.value = response.data?.message || 'Unable to fetch logs';
    }
  } catch (err) {
    console.error('[Upload Logs Error]', err);
    uploadLogsError.value = err.response?.data?.message || 'Failed to load upload history';
  } finally {
    uploadLogsLoading.value = false;
  }
};

const openUploadLogsModal = async () => {
  showUploadLogsModal.value = true;
  if (uploadLogs.value.length === 0) {
    await fetchUploadLogs();
  }
};

const closeUploadLogsModal = () => {
  showUploadLogsModal.value = false;
};

/**
 * Handle initial inventory upload
 */
const handleInitialInventoryUpload = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.csv,.xlsx,.xls';

  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 16 * 1024 * 1024) {
      showToastMessage('File too large (max 16MB)', 'bi bi-exclamation-circle-fill');
      return;
    }

    loading.value = true;
    try {
      await importInventory(shopId.value, file);
      showToastMessage('Initial inventory data uploaded successfully!', 'bi bi-check-circle-fill');
      await fetchInventory();
    } catch (err) {
      console.error('[Initial Upload Error]', err);
      showToastMessage(err.response?.data?.message || 'Initial upload failed', 'bi bi-exclamation-circle-fill');
    } finally {
      loading.value = false;
    }
  };

  input.click();
};

/**
 * Handle import
 */
const handleImport = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.csv,.xlsx,.xls';

  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 16 * 1024 * 1024) {
      showToastMessage('File too large (max 16MB)', 'bi bi-exclamation-circle-fill');
      return;
    }

    loading.value = true;
    try {
      await importInventory(shopId.value, file);
      showToastMessage('Inventory imported successfully!', 'bi bi-check-circle-fill');
      await fetchInventory();
    } catch (err) {
      console.error('[Import Error]', err);
      showToastMessage(err.response?.data?.message || 'Import failed', 'bi bi-exclamation-circle-fill');
    } finally {
      loading.value = false;
    }
  };

  input.click();
};

/**
 * Handle PDF report generation
 */
const handlePDFReport = async () => {
  try {
    loading.value = true;
    const response = await generateInventoryPDF(shopId.value);
    
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `inventory_report_${shopId.value}_${new Date().toISOString().split('T')[0]}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);

    showToastMessage('PDF report generated successfully!', 'bi bi-check-circle-fill');
  } catch (err) {
    console.error('[PDF Report Error]', err);
    showToastMessage(err.response?.data?.message || 'Failed to generate PDF report', 'bi bi-exclamation-circle-fill');
  } finally {
    loading.value = false;
  }
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
};

/**
 * Close edit modal
 */
const closeEditModal = () => {
  showEditModal.value = false;
  editForm.value = { id: null, name: '', price: 0, stock: 0, minimumStock: 0 };
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
    await deleteInventoryItem(deleteItem.value.id);
    showToastMessage('Product deleted successfully!', 'bi bi-check-circle-fill');
    closeDeleteModal();
    await fetchInventory();
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

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.35);
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
}

@media (max-width: 768px) {
  .shop-inventory-tab {
    padding: 1rem;
  }

  .modal-dialog {
    min-width: 90%;
  }
}
</style>

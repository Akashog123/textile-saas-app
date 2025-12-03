<template>
  <div class="regional-demand-tab">
    <!-- Page Header -->
    <div class="page-header">
      <h5 class="mb-2">
        <i class="bi bi-geo-alt me-2"></i>Shop Stock Levels
      </h5>
      <p class="text-muted mb-0">
        Monitor stock health across shops you supply - identify which shops need restocking
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-content">
        <div class="spinner-border text-primary mb-3" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <h6>Loading Stock Data...</h6>
        <p class="text-muted">Fetching inventory levels from your supplied shops</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="empty-state">
      <div class="empty-state-content">
        <i class="bi bi-exclamation-triangle fs-1 mb-3 text-warning"></i>
        <h5>Failed to Load Stock Data</h5>
        <p class="text-muted mb-4">{{ error }}</p>
        <button class="btn btn-primary" @click="fetchStockData">
          <i class="bi bi-arrow-clockwise me-2"></i>Try Again
        </button>
      </div>
    </div>

    <!-- Empty State - No Shops -->
    <div v-else-if="!stockData || !stockData.heatmapPoints || stockData.heatmapPoints.length === 0" class="empty-state">
      <div class="empty-state-content">
        <i class="bi bi-shop fs-1 mb-3"></i>
        <h5>No Shops Found</h5>
        <p class="text-muted mb-4">
          You haven't supplied to any shops yet. Start supplying products to see stock levels here.
        </p>
        <router-link to="/distributor" class="btn btn-primary">
          <i class="bi bi-arrow-left me-2 text-white"></i>Go to Dashboard
        </router-link>
      </div>
    </div>

    <!-- Stock Heatmap Section -->
    <div v-else class="row g-3">
      <!-- Summary Cards -->
      <div class="col-12">
        <div class="row g-3 mb-3">
          <div class="col-md-3">
            <div class="summary-card critical">
              <div class="summary-icon">
                <i class="bi bi-exclamation-triangle-fill"></i>
              </div>
              <div class="summary-content">
                <span class="summary-value">{{ stockData.summary.criticalStockShops }}</span>
                <span class="summary-label">Critical Stock</span>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="summary-card low">
              <div class="summary-icon">
                <i class="bi bi-arrow-down-circle"></i>
              </div>
              <div class="summary-content">
                <span class="summary-value">{{ stockData.summary.lowStockShops }}</span>
                <span class="summary-label">Low Stock</span>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="summary-card healthy">
              <div class="summary-icon">
                <i class="bi bi-check-circle-fill"></i>
              </div>
              <div class="summary-content">
                <span class="summary-value">{{ stockData.summary.healthyStockShops }}</span>
                <span class="summary-label">Healthy Stock</span>
              </div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="summary-card total">
              <div class="summary-icon">
                <i class="bi bi-currency-rupee"></i>
              </div>
              <div class="summary-content">
                <span class="summary-value">₹{{ formatNumber(stockData.summary.totalStockValue) }}</span>
                <span class="summary-label">Total Stock Value</span>
              </div>
            </div>
          </div>
        </div>
        <!-- Info Button -->
        <div class="info-btn-row">
          <button class="info-btn" @click="showStockLevelInfo = true" title="How are these calculated?">
            <i class="bi bi-info-circle me-1"></i>How is this calculated?
          </button>
        </div>
      </div>

      <!-- Interactive Map -->
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0"><i class="bi bi-map me-2"></i>Shop Stock Heatmap</h6>
            <div class="legend">
              <span class="legend-item"><span class="legend-dot critical"></span> Critical</span>
              <span class="legend-item"><span class="legend-dot low"></span> Low</span>
              <span class="legend-item"><span class="legend-dot healthy"></span> Healthy</span>
            </div>
          </div>
          <div class="card-body p-0">
            <div id="heatmap" ref="mapContainer" class="heatmap-container"></div>
          </div>
        </div>
      </div>

      <!-- Shop Details Table -->
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0"><i class="bi bi-table me-2"></i>Shop Stock Details</h6>
            <button class="btn btn-sm btn-outline-primary" @click="fetchStockData">
              <i class="bi bi-arrow-clockwise me-1"></i>Refresh
            </button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>Shop</th>
                    <th>Location</th>
                    <th>Total Stock</th>
                    <th>Stock Value</th>
                    <th>Critical Items</th>
                    <th>Stock Level</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(point, idx) in stockData.heatmapPoints"
                    :key="idx"
                    class="shop-row"
                  >
                    <td @click="focusOnShop(point)" style="cursor: pointer;">
                      <i class="bi bi-shop me-2"></i>{{ point.shopName }}
                    </td>
                    <td>{{ point.region }}</td>
                    <td>{{ point.totalStock.toLocaleString() }} units</td>
                    <td>₹{{ formatNumber(point.stockValue) }}</td>
                    <td>
                      <span v-if="point.criticalItems > 0" class="text-danger fw-bold">
                        {{ point.criticalItems }}
                      </span>
                      <span v-else class="text-muted">0</span>
                    </td>
                    <td>
                      <span :class="'badge stock-badge ' + point.stockLevel">
                        {{ point.stockLevel.toUpperCase() }}
                      </span>
                    </td>
                    <td>
                      <button 
                        class="btn btn-sm btn-outline-primary"
                        @click="showProductDetails(point)"
                      >
                        <i class="bi bi-box-seam me-1"></i>Products
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="col-12 text-center">
        <router-link to="/distributor/planning" class="btn btn-primary">
          <i class="bi bi-gear me-2"></i>View AI Planning
        </router-link>
      </div>
    </div>

    <!-- Product Details Modal -->
    <div v-if="showProductModal" class="modal-overlay" @click.self="closeProductModal">
      <div class="product-modal">
        <div class="modal-header">
          <h5>
            <i class="bi bi-box-seam me-2"></i>
            Products at {{ selectedShop?.shopName }}
          </h5>
          <button class="btn-close" @click="closeProductModal"></button>
        </div>
        <div class="modal-body">
          <!-- Shop Summary -->
          <div class="shop-summary mb-4">
            <div class="row g-3">
              <div class="col-md-3">
                <div class="mini-stat critical">
                  <span class="mini-stat-value">{{ selectedShop?.criticalItems || 0 }}</span>
                  <span class="mini-stat-label">Critical</span>
                </div>
              </div>
              <div class="col-md-3">
                <div class="mini-stat low">
                  <span class="mini-stat-value">{{ selectedShop?.lowItems || 0 }}</span>
                  <span class="mini-stat-label">Low Stock</span>
                </div>
              </div>
              <div class="col-md-3">
                <div class="mini-stat healthy">
                  <span class="mini-stat-value">{{ selectedShop?.healthyItems || 0 }}</span>
                  <span class="mini-stat-label">Healthy</span>
                </div>
              </div>
              <div class="col-md-3">
                <div class="mini-stat total">
                  <span class="mini-stat-value">{{ formatNumber(selectedShop?.totalSold || 0) }}</span>
                  <span class="mini-stat-label">Units Sold</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Products Table -->
          <div class="products-table-wrapper">
            <table class="table products-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Stock</th>
                  <th>Safety</th>
                  <th>Sold</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="product in selectedShop?.stockDetails" 
                  :key="product.product_id"
                  :class="'product-row ' + product.status"
                >
                  <td class="product-name-cell">
                    <span class="status-dot" :class="product.status"></span>
                    {{ product.product_name }}
                  </td>
                  <td>
                    <span class="category-tag">{{ product.category || 'N/A' }}</span>
                  </td>
                  <td>
                    <span :class="product.qty_available < product.safety_stock ? 'text-danger fw-bold' : ''">
                      {{ product.qty_available }}
                    </span>
                  </td>
                  <td>{{ product.safety_stock }}</td>
                  <td>
                    <span v-if="product.total_sold > 0" class="sold-badge">
                      {{ product.total_sold }}
                    </span>
                    <span v-else class="text-muted">-</span>
                  </td>
                  <td>
                    <span class="status-badge" :class="product.status">
                      {{ product.status.toUpperCase() }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Top Performing Products -->
          <div v-if="topPerformingProducts.length > 0" class="performance-section mt-4">
            <h6><i class="bi bi-trophy me-2"></i>Top Performing Products</h6>
            <div class="performance-grid">
              <div v-for="product in topPerformingProducts.slice(0, 3)" :key="product.product_id" class="performance-card">
                <span class="product-name">{{ product.product_name }}</span>
                <span class="units-sold">{{ formatNumber(product.total_sold) }} units sold</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline-secondary" @click="closeProductModal">Close</button>
          <router-link to="/distributor/planning" class="btn btn-primary">
            <i class="bi bi-cpu me-1"></i>View AI Insights
          </router-link>
        </div>
      </div>
    </div>

    <!-- Stock Level Info Popup -->
    <div v-if="showStockLevelInfo" class="info-overlay" @click="showStockLevelInfo = false">
      <div class="info-popup" @click.stop>
        <div class="info-popup-header">
          <h5><i class="bi bi-info-circle me-2"></i>How Stock Levels Are Calculated</h5>
          <button class="info-close-btn" @click="showStockLevelInfo = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="info-popup-body">
          <div class="info-item">
            <div class="info-icon bg-danger-light">
              <i class="bi bi-exclamation-triangle-fill text-danger"></i>
            </div>
            <div class="info-content">
              <h6>Critical Stock</h6>
              <p>Shops where the overall health score is below 50%. This happens when most products have stock levels less than 50% of their safety stock threshold.</p>
              <code>Health Score = (Critical×0 + Low×0.5 + Healthy×1) ÷ Total Items</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-warning-light">
              <i class="bi bi-arrow-down-circle text-warning"></i>
            </div>
            <div class="info-content">
              <h6>Low Stock</h6>
              <p>Shops where the health score is between 50% and 80%. Some products need attention but the overall stock situation is manageable.</p>
              <code>Low Stock: Health Score between 0.5 and 0.8</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-success-light">
              <i class="bi bi-check-circle-fill text-success"></i>
            </div>
            <div class="info-content">
              <h6>Healthy Stock</h6>
              <p>Shops where the health score is 80% or above. Most products have stock at or above their safety stock levels.</p>
              <code>Healthy Stock: Health Score ≥ 0.8</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-primary-light">
              <i class="bi bi-currency-rupee text-primary"></i>
            </div>
            <div class="info-content">
              <h6>Total Stock Value</h6>
              <p>The total monetary value of all inventory across all shops you supply, calculated by multiplying each product's quantity by its unit price.</p>
              <code>Total Value = Σ (Product Price × Quantity Available)</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-info-light">
              <i class="bi bi-box-seam text-info"></i>
            </div>
            <div class="info-content">
              <h6>Product Stock Status</h6>
              <p>Each product's status is based on comparing current stock to safety stock:</p>
              <ul class="action-list">
                <li><span class="action-badge critical">Critical</span> Stock is below 50% of safety stock</li>
                <li><span class="action-badge warning">Low</span> Stock is between 50-100% of safety stock</li>
                <li><span class="action-badge healthy">Healthy</span> Stock is at or above 100% of safety stock</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stock Level Info Popup -->
    <div v-if="showStockLevelInfo" class="info-overlay" @click="showStockLevelInfo = false">
      <div class="info-popup" @click.stop>
        <div class="info-popup-header">
          <h5><i class="bi bi-info-circle me-2"></i>How Stock Levels Are Calculated</h5>
          <button class="info-close-btn" @click="showStockLevelInfo = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="info-popup-body">
          <div class="info-item">
            <div class="info-icon bg-danger-light">
              <i class="bi bi-exclamation-triangle-fill text-danger"></i>
            </div>
            <div class="info-content">
              <h6>Critical Stock</h6>
              <p>Shops where the overall health score is below 50%. This happens when most products have stock levels less than 50% of their safety stock threshold.</p>
              <code>Health Score = (Critical×0 + Low×0.5 + Healthy×1) ÷ Total Items</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-warning-light">
              <i class="bi bi-arrow-down-circle text-warning"></i>
            </div>
            <div class="info-content">
              <h6>Low Stock</h6>
              <p>Shops where the health score is between 50% and 80%. Some products need attention but the overall stock situation is manageable.</p>
              <code>Low Stock: Health Score between 0.5 and 0.8</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-success-light">
              <i class="bi bi-check-circle-fill text-success"></i>
            </div>
            <div class="info-content">
              <h6>Healthy Stock</h6>
              <p>Shops where the health score is 80% or above. Most products have stock at or above their safety stock levels.</p>
              <code>Healthy Stock: Health Score ≥ 0.8</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-primary-light">
              <i class="bi bi-currency-rupee text-primary"></i>
            </div>
            <div class="info-content">
              <h6>Total Stock Value</h6>
              <p>The total monetary value of all inventory across all shops you supply, calculated by multiplying each product's quantity by its unit price.</p>
              <code>Total Value = Σ (Product Price × Quantity Available)</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-info-light">
              <i class="bi bi-box-seam text-info"></i>
            </div>
            <div class="info-content">
              <h6>Product Stock Status</h6>
              <p>Each product's status is based on comparing current stock to safety stock:</p>
              <ul class="action-list">
                <li><span class="action-badge critical">Critical</span> Stock is below 50% of safety stock</li>
                <li><span class="action-badge warning">Low</span> Stock is between 50-100% of safety stock</li>
                <li><span class="action-badge healthy">Healthy</span> Stock is at or above 100% of safety stock</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <i :class="toastIcon" class="me-2"></i>{{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue';
import { getDistributorStockHeatmap, downloadRegionalReport } from '@/api/apiDistributor';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Refs
const stockData = ref(null);
const loading = ref(true);
const error = ref('');
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');
const toastType = ref('success');
const mapContainer = ref(null);
const showProductModal = ref(false);
const selectedShop = ref(null);
const showStockLevelInfo = ref(false);

// Computed
const topPerformingProducts = computed(() => {
  if (!selectedShop.value?.stockDetails) return [];
  return selectedShop.value.stockDetails
    .filter(p => p.total_sold > 0)
    .sort((a, b) => (b.total_sold || 0) - (a.total_sold || 0))
    .slice(0, 5);
});

// Modal functions
const showProductDetails = (shop) => {
  selectedShop.value = shop;
  showProductModal.value = true;
};

const closeProductModal = () => {
  showProductModal.value = false;
  selectedShop.value = null;
};

// Map instance
let map = null;
let markers = [];

// Fetch stock data on mount
onMounted(async () => {
  await fetchStockData();
});

// Fetch stock data from API
const fetchStockData = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    console.log('[Stock Heatmap] Fetching stock data...');
    const response = await getDistributorStockHeatmap();
    console.log('[Stock Heatmap] Response:', response);
    
    if (response.data && response.data.status === 'success') {
      stockData.value = response.data.data;
      
      // Store in sessionStorage for planning page
      sessionStorage.setItem('stockHeatmapData', JSON.stringify(response.data.data));
      
      // Initialize map after data is loaded
      await nextTick();
      initializeMap();
      
      showToastMsg('Stock data loaded successfully', 'bi bi-check-circle-fill', 'success');
    } else {
      error.value = response.data?.message || 'Failed to load stock data';
    }
  } catch (err) {
    console.error('[Stock Heatmap Error]', err);
    console.error('[Stock Heatmap Error Details]', {
      message: err.message,
      code: err.code,
      response: err.response?.data,
      status: err.response?.status
    });
    
    // More specific error messages
    if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
      error.value = 'Cannot connect to server. Please ensure the backend is running on port 5001.';
    } else if (err.response?.status === 401) {
      error.value = 'Session expired. Please login again.';
    } else if (err.response?.status === 403) {
      error.value = 'Access denied. You need distributor role to access this page.';
    } else {
      error.value = err.response?.data?.message || err.message || 'Failed to fetch stock data from server';
    }
  } finally {
    loading.value = false;
  }
};

// Initialize Leaflet map
const initializeMap = () => {
  if (!stockData.value || !stockData.value.heatmapPoints.length) return;

  // Destroy existing map if any
  if (map) {
    map.remove();
    map = null;
  }

  // Wait for DOM to be ready
  const mapElement = document.getElementById('heatmap');
  if (!mapElement) {
    console.error('[Map] Container element not found, retrying...');
    setTimeout(initializeMap, 100);
    return;
  }

  try {
    // Create map centered on India
    map = L.map('heatmap').setView([20.5937, 78.9629], 5);

  // Add tile layer (OpenStreetMap)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map);

  // Clear existing markers
  markers = [];

  // Add circle markers for each shop
  stockData.value.heatmapPoints.forEach((point) => {
    // Calculate radius based on stock value (min 15000, max 50000 meters)
    const maxValue = Math.max(...stockData.value.heatmapPoints.map(p => p.stockValue));
    const normalizedValue = maxValue > 0 ? point.stockValue / maxValue : 0.5;
    const radius = 15000 + (normalizedValue * 35000);
    
    // Create circle marker
    const circle = L.circle([point.lat, point.lon], {
      color: point.color,
      fillColor: point.color,
      fillOpacity: 0.5 + (normalizedValue * 0.3),
      radius: radius,
      weight: 2
    }).addTo(map);

    // Create popup content
    const popupContent = `
      <div class="heatmap-popup">
        <h6 class="popup-title">${point.shopName}</h6>
        <div class="popup-stats">
          <div class="popup-stat">
            <span class="popup-label">Location:</span>
            <span class="popup-value">${point.region}</span>
          </div>
          <div class="popup-stat">
            <span class="popup-label">Total Stock:</span>
            <span class="popup-value">${point.totalStock.toLocaleString()} units</span>
          </div>
          <div class="popup-stat">
            <span class="popup-label">Stock Value:</span>
            <span class="popup-value">₹${formatNumber(point.stockValue)}</span>
          </div>
          <div class="popup-stat">
            <span class="popup-label">Critical Items:</span>
            <span class="popup-value ${point.criticalItems > 0 ? 'text-danger' : ''}">${point.criticalItems}</span>
          </div>
          <div class="popup-stat">
            <span class="popup-label">Low Stock Items:</span>
            <span class="popup-value ${point.lowItems > 0 ? 'text-warning' : ''}">${point.lowItems}</span>
          </div>
          <div class="popup-stat">
            <span class="popup-label">Stock Level:</span>
            <span class="popup-value stock-${point.stockLevel}">${point.stockLevel.toUpperCase()}</span>
          </div>
          <div class="popup-stat">
            <span class="popup-label">Top Product:</span>
            <span class="popup-value">${point.topProduct}</span>
          </div>
        </div>
      </div>
    `;

    circle.bindPopup(popupContent, {
      className: 'custom-popup'
    });

    // Add hover effect
    circle.on('mouseover', function() {
      this.setStyle({ fillOpacity: 0.8, weight: 3 });
    });
    circle.on('mouseout', function() {
      this.setStyle({ fillOpacity: 0.5 + (normalizedValue * 0.3), weight: 2 });
    });

    markers.push({ circle, point });
  });

  // Fit bounds to show all markers
  if (markers.length > 0) {
    const group = L.featureGroup(markers.map(m => m.circle));
    map.fitBounds(group.getBounds().pad(0.1));
  }
  } catch (mapError) {
    console.error('[Map Init Error]', mapError);
    error.value = 'Map container not found. Please refresh the page.';
  }
};

// Focus on specific shop
const focusOnShop = (point) => {
  if (map) {
    map.setView([point.lat, point.lon], 10);
    
    // Open popup for this shop
    const marker = markers.find(m => m.point.shopId === point.shopId);
    if (marker) {
      marker.circle.openPopup();
    }
  }
};

// Download report
const downloadReport = async () => {
  try {
    const response = await downloadRegionalReport();
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `stock_report_${new Date().toISOString().split('T')[0]}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
    showToastMsg('Report downloaded!', 'bi bi-check-circle-fill', 'success');
  } catch (err) {
    console.error('[Download Error]', err);
    showToastMsg('Download failed', 'bi bi-exclamation-circle-fill', 'error');
  }
};

// Format large numbers
const formatNumber = (num) => {
  if (num >= 10000000) {
    return (num / 10000000).toFixed(2) + ' Cr';
  } else if (num >= 100000) {
    return (num / 100000).toFixed(2) + ' L';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(2) + ' K';
  }
  return num.toFixed(2);
};

// Toast notification
const showToastMsg = (message, icon, type = 'success') => {
  toastMessage.value = message;
  toastIcon.value = icon;
  toastType.value = type;
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

// Cleanup on unmount
onUnmounted(() => {
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<style scoped>
.regional-demand-tab {
  background: #ffffff;
  min-height: calc(100vh - 60px);
  padding: 2rem;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Page Header */
.page-header {
  margin-bottom: 2rem;
}

.page-header h5 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  font-size: 1.75rem;
}

h6 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.card {
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.card-header {
  background: transparent;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  padding: 1rem 1.5rem;
}

/* Loading State */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-content {
  text-align: center;
}

.loading-content h6 {
  margin-top: 1rem;
}

/* Empty State */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-state-content {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
}

.empty-state-content i {
  color: var(--color-primary);
}

.empty-state-content h5 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* Summary Cards */
.summary-card {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  border-radius: 12px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
  transition: transform 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
}

.summary-card.critical {
  border-left: 4px solid #dc3545;
}

.summary-card.low {
  border-left: 4px solid #ffc107;
}

.summary-card.healthy {
  border-left: 4px solid #28a745;
}

.summary-card.total {
  border-left: 4px solid var(--color-primary);
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-right: 1rem;
}

.summary-card.critical .summary-icon {
  background: rgba(220, 53, 69, 0.1);
  color: #dc3545;
}

.summary-card.low .summary-icon {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.summary-card.healthy .summary-icon {
  background: rgba(40, 167, 69, 0.1);
  color: #28a745;
}

.summary-card.total .summary-icon {
  background: rgba(74, 144, 226, 0.1);
  color: var(--color-primary);
}

.summary-content {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
}

.summary-label {
  font-size: 0.85rem;
  color: #666;
}

/* Legend */
.legend {
  display: flex;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  color: #666;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.legend-dot.critical {
  background: #dc3545;
}

.legend-dot.low {
  background: #ffc107;
}

.legend-dot.healthy {
  background: #28a745;
}

/* Heatmap Container */
.heatmap-container {
  height: 500px;
  width: 100%;
  border-radius: 0 0 16px 16px;
  z-index: 1;
}

/* Table */
.table th {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  border: none;
  font-weight: 600;
}

.shop-row {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.shop-row:hover {
  background: rgba(74, 144, 226, 0.08);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.stock-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.stock-badge.critical {
  background: rgba(220, 53, 69, 0.15);
  color: #dc3545;
}

.stock-badge.low {
  background: rgba(255, 193, 7, 0.15);
  color: #856404;
}

.stock-badge.healthy {
  background: rgba(40, 167, 69, 0.15);
  color: #28a745;
}

/* Buttons */
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

.btn-outline-primary {
  border-radius: 8px;
}

.btn-outline-secondary {
  border-radius: 8px;
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  z-index: 1100;
  animation: slideIn 0.3s ease;
  color: white;
}

.toast-notification.success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
}

.toast-notification.error {
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

/* Leaflet Popup Styles */
:deep(.custom-popup .leaflet-popup-content-wrapper) {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

:deep(.custom-popup .leaflet-popup-content) {
  margin: 0;
  padding: 0;
}

:deep(.heatmap-popup) {
  padding: 1rem;
  min-width: 220px;
}

:deep(.popup-title) {
  margin: 0 0 0.75rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--color-primary);
  color: var(--color-primary);
  font-weight: 700;
}

:deep(.popup-stats) {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

:deep(.popup-stat) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.popup-label) {
  color: #666;
  font-size: 0.85rem;
}

:deep(.popup-value) {
  font-weight: 600;
  color: #333;
}

:deep(.popup-value.stock-critical) {
  color: #dc3545;
}

:deep(.popup-value.stock-low) {
  color: #ffc107;
}

:deep(.popup-value.stock-healthy) {
  color: #28a745;
}

:deep(.popup-value.text-danger) {
  color: #dc3545 !important;
}

:deep(.popup-value.text-warning) {
  color: #ffc107 !important;
}

/* Product Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  backdrop-filter: blur(4px);
}

.product-modal {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalIn 0.3s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.product-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.product-modal .modal-header h5 {
  margin: 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.product-modal .modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.product-modal .modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* Mini Stats in Modal */
.shop-summary {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1rem;
}

.mini-stat {
  background: white;
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
  border-left: 4px solid;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border-top: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
}

.mini-stat.critical { border-left-color: #dc3545; }
.mini-stat.low { border-left-color: #ffc107; }
.mini-stat.healthy { border-left-color: #28a745; }
.mini-stat.total { border-left-color: #4a90e2; }

.mini-stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
}

.mini-stat-label {
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
}

/* Products Table in Modal */
.products-table-wrapper {
  max-height: 300px;
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.products-table {
  margin: 0;
  font-size: 0.9rem;
}

.products-table thead th {
  background: #f8fafc;
  position: sticky;
  top: 0;
  font-weight: 600;
  color: #475569;
  padding: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
}

.products-table tbody td {
  padding: 0.75rem;
  vertical-align: middle;
}

.product-row {
  transition: background 0.2s ease;
}

.product-row.critical {
  background: #fef2f2;
}

.product-row.low {
  background: #fffbeb;
}

.product-row:hover {
  background: rgba(74, 144, 226, 0.08) !important;
}

.product-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.critical {
  background: #dc3545;
  box-shadow: 0 0 6px rgba(220, 53, 69, 0.5);
}

.status-dot.low {
  background: #ffc107;
}

.status-dot.healthy {
  background: #28a745;
}

.category-tag {
  background: #f1f5f9;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #475569;
}

.sold-badge {
  background: #dbeafe;
  color: #1d4ed8;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85rem;
}

/* Tooltip Header Styles */


.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.status-badge.critical {
  background: #fee2e2;
  color: #dc2626;
}

.status-badge.low {
  background: #fef3c7;
  color: #d97706;
}

.status-badge.healthy {
  background: #d1fae5;
  color: #059669;
}

/* Performance Section */
.performance-section h6 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  margin-bottom: 1rem;
}

.performance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.performance-card {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 10px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.performance-card .product-name {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.performance-card .units-sold {
  font-size: 0.85rem;
  font-weight: 700;
  color: #166534;
}

/* Info Button Row */
.info-btn-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.info-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  color: var(--color-primary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.info-btn:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}

/* Info Popup Overlay */
.info-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 20px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.info-popup {
  background: white;
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { 
    opacity: 0; 
    transform: translateY(20px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

.info-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border-bottom: 1px solid #e5e7eb;
}

.info-popup-header h5 {
  margin: 0;
  color: var(--color-primary);
  font-weight: 600;
  display: flex;
  align-items: center;
}

.info-close-btn {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1e293b;
}

.info-popup-body {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(80vh - 70px);
}

.info-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.bg-primary-light { background: rgba(59, 130, 246, 0.15); }
.bg-warning-light { background: rgba(245, 158, 11, 0.15); }
.bg-danger-light { background: rgba(220, 53, 69, 0.15); }
.bg-success-light { background: rgba(16, 185, 129, 0.15); }
.bg-info-light { background: rgba(6, 182, 212, 0.15); }

.info-content h6 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-weight: 600;
}

.info-content p {
  margin: 0 0 0.75rem 0;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.5;
}

.info-content code {
  display: inline-block;
  background: #e2e8f0;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #475569;
}

.info-content .action-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}

.info-content .action-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: #64748b;
}

.info-content .action-list li:last-child {
  margin-bottom: 0;
}

.info-content .action-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.info-content .action-badge.critical {
  background: rgba(220, 53, 69, 0.15);
  color: #dc2626;
}

.info-content .action-badge.warning {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.info-content .action-badge.healthy {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
</style>

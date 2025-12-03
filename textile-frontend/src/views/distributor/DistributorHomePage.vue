<template>
  <div class="distributor-home-page">
    <div class="page-header">
      <h5 class="mb-2">
        <i class="bi bi-building me-2"></i>Distributor Dashboard
      </h5>
      <p class="text-muted mb-4">
        Welcome to your distributor portal. Monitor shop stock levels and get AI-powered production recommendations.
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container mb-4">
      <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
      <span class="text-muted">Loading dashboard data...</span>
    </div>

    <!-- Quick Stats Row -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon shops">
            <i class="bi bi-shop"></i>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.totalShops }}</span>
            <span class="stat-label">Shops Supplied</span>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon products">
            <i class="bi bi-box-seam"></i>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.totalProducts }}</span>
            <span class="stat-label">Products</span>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card clickable" @click="scrollToSection('criticalProducts')">
          <div class="stat-icon critical">
            <i class="bi bi-exclamation-triangle"></i>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.criticalProductCount }}</span>
            <span class="stat-label">Critical Products</span>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon health">
            <i class="bi bi-heart-pulse"></i>
          </div>
          <div class="stat-content">
            <span class="stat-value" :class="healthScoreClass">{{ stats.healthScore }}%</span>
            <span class="stat-label">Stock Health</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Critical Products Alert Banner -->
    <div v-if="criticalProducts.length > 0" class="critical-banner mb-4" id="criticalProducts">
      <div class="banner-header">
        <div class="banner-title">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          <strong>{{ criticalProducts.length }} Products Need Immediate Restocking</strong>
          <button class="info-btn-small" @click="showCriticalInfo = true" title="How is this calculated?">
            <i class="bi bi-info-circle"></i>
          </button>
        </div>
        <button class="btn btn-sm btn-outline-danger" @click="showAllCritical = !showAllCritical">
          {{ showAllCritical ? 'Show Less' : 'View All' }}
        </button>
      </div>

      <!-- Info Popup Overlay -->
      <div v-if="showCriticalInfo" class="info-overlay" @click.self="showCriticalInfo = false">
        <div class="info-popup">
          <div class="info-popup-header">
            <h6><i class="bi bi-info-circle me-2"></i>Understanding Critical Products</h6>
            <button class="close-btn" @click="showCriticalInfo = false">&times;</button>
          </div>
          <div class="info-popup-body">
            <div class="info-item">
              <strong>Critical Status</strong>
              <p>A product is marked as <span class="text-danger fw-bold">CRITICAL</span> when its stock level falls below 50% of the safety stock threshold.</p>
            </div>
            <div class="info-item">
              <strong>In Stock</strong>
              <p>The current quantity of this product available in the shop's inventory.</p>
            </div>
            <div class="info-item">
              <strong>Safety Stock</strong>
              <p>The minimum stock level required to avoid stockouts. This is your buffer inventory.</p>
            </div>
            <div class="info-item">
              <strong>Stock Level %</strong>
              <p>Shows how much stock you have relative to safety stock.</p>
              <code>= (In Stock ÷ Safety Stock) × 100</code>
              <ul class="status-list">
                <li><span class="text-danger">Critical:</span> Below 50%</li>
                <li><span class="text-warning">Low:</span> 50% - 100%</li>
                <li><span class="text-success">Healthy:</span> Above 100%</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <div class="critical-products-grid">
        <div 
          v-for="(product, idx) in displayedCriticalProducts" 
          :key="idx" 
          class="critical-product-card"
        >
          <div class="product-status-badge">
            <span class="badge bg-danger">CRITICAL</span>
          </div>
          <div class="product-name">{{ product.product_name }}</div>
          <div class="product-category">{{ product.category }}</div>
          <div class="product-stats">
            <div class="stat">
              <span class="stat-num">{{ product.qty_available }}</span>
              <span class="stat-txt">In Stock</span>
            </div>
            <div class="stat">
              <span class="stat-num">{{ product.safety_stock }}</span>
              <span class="stat-txt">Safety</span>
            </div>
            <div class="stat">
              <span class="stat-num text-danger">{{ Math.round(product.stock_ratio * 100) }}%</span>
              <span class="stat-txt">Level</span>
            </div>
          </div>
          <div class="product-shop">
            <i class="bi bi-shop me-1"></i>{{ product.shop_name }}
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Row -->
    <div class="row g-4">
      <!-- Recent Alerts Panel -->
      <div class="col-lg-7">
        <div class="alerts-panel">
          <div class="panel-header">
            <h6><i class="bi bi-bell me-2"></i>Stock Alerts by Shop</h6>
            <span class="badge bg-danger" v-if="alerts.length">{{ alerts.length }}</span>
          </div>
          <div class="alerts-list" v-if="alerts.length">
            <div v-for="(alert, idx) in alerts" :key="idx" class="alert-item" :class="alert.level">
              <div class="alert-icon">
                <i :class="getAlertIcon(alert.level)"></i>
              </div>
              <div class="alert-content">
                <span class="alert-title">{{ alert.shop }}</span>
                <span class="alert-message">{{ alert.message }}</span>
                <div class="alert-products" v-if="alert.products && alert.products.length">
                  <span class="products-label">Products:</span>
                  <span class="product-tag" v-for="p in alert.products.slice(0, 3)" :key="p">{{ p }}</span>
                  <span v-if="alert.products.length > 3" class="more-tag">+{{ alert.products.length - 3 }} more</span>
                </div>
              </div>
              <span class="alert-time">{{ alert.time }}</span>
            </div>
          </div>
          <div v-else class="empty-alerts">
            <i class="bi bi-check-circle text-success fs-2 mb-2"></i>
            <p class="mb-0">All shops have healthy stock levels!</p>
          </div>
        </div>

        <!-- Category Issues -->
        <div class="category-panel mt-4" v-if="Object.keys(categorySummary).length > 0">
          <div class="panel-header">
            <h6><i class="bi bi-tags me-2"></i>Stock Issues by Category</h6>
          </div>
          <div class="category-grid">
            <div v-for="(data, category) in categorySummary" :key="category" class="category-item">
              <span class="category-name">{{ category }}</span>
              <div class="category-badges">
                <span class="badge bg-danger" v-if="data.critical > 0">{{ data.critical }} critical</span>
                <span class="badge bg-warning text-dark" v-if="data.low > 0">{{ data.low }} low</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions Panel -->
      <div class="col-lg-5">
        <div class="quick-actions-panel">
          <div class="panel-header">
            <h6><i class="bi bi-lightning me-2"></i>Quick Actions</h6>
          </div>
          <div class="action-buttons">
            <router-link to="/distributor/regional-demand" class="action-btn stock-levels">
              <div class="action-btn-icon">
                <i class="bi bi-geo-alt"></i>
              </div>
              <div class="action-btn-content">
                <span class="action-btn-title">View Stock Heatmap</span>
                <span class="action-btn-desc">See real-time stock levels on map</span>
              </div>
              <i class="bi bi-chevron-right"></i>
            </router-link>
            <router-link to="/distributor/planning" class="action-btn planning">
              <div class="action-btn-icon">
                <i class="bi bi-cpu"></i>
              </div>
              <div class="action-btn-content">
                <span class="action-btn-title">AI Production Planning</span>
                <span class="action-btn-desc">Get AI-powered recommendations</span>
              </div>
              <i class="bi bi-chevron-right"></i>
            </router-link>
          </div>

          <!-- Stock Summary -->
          <div class="stock-summary mt-3">
            <div class="summary-header">
              <h6 class="summary-title"><i class="bi bi-pie-chart me-2"></i>Stock Overview</h6>
              <button class="info-btn-small" @click="showStockOverviewInfo = true" title="How is this calculated?">
                <i class="bi bi-info-circle"></i>
              </button>
            </div>

            <!-- Stock Overview Info Popup -->
            <div v-if="showStockOverviewInfo" class="info-overlay" @click.self="showStockOverviewInfo = false">
              <div class="info-popup">
                <div class="info-popup-header">
                  <h6><i class="bi bi-info-circle me-2"></i>Stock Overview Explained</h6>
                  <button class="close-btn" @click="showStockOverviewInfo = false">&times;</button>
                </div>
                <div class="info-popup-body">
                  <div class="info-item">
                    <strong>What do these numbers mean?</strong>
                    <p>These counts show how many shops fall into each stock health category based on their overall inventory status.</p>
                  </div>
                  <div class="info-item">
                    <strong><span class="dot critical"></span> Critical Shops</strong>
                    <p>Shops with a health score below 50%. These shops have multiple products with dangerously low stock levels and need immediate attention.</p>
                  </div>
                  <div class="info-item">
                    <strong><span class="dot warning"></span> Low Stock Shops</strong>
                    <p>Shops with a health score between 50% and 80%. These shops have some products running low and should be restocked soon.</p>
                  </div>
                  <div class="info-item">
                    <strong><span class="dot healthy"></span> Healthy Shops</strong>
                    <p>Shops with a health score of 80% or above. These shops have adequate stock levels across their products.</p>
                  </div>
                  <div class="info-item">
                    <strong>How is Shop Health Score calculated?</strong>
                    <p>Each product in a shop is scored based on its stock level:</p>
                    <ul class="status-list">
                      <li>Critical product (below 50%): scores 0</li>
                      <li>Low product (50-100%): scores 0.5</li>
                      <li>Healthy product (above 100%): scores 1</li>
                    </ul>
                    <code>Shop Health = Average of all product scores × 100</code>
                  </div>
                </div>
              </div>
            </div>

            <div class="summary-bars">
              <div class="summary-item">
                <div class="summary-label">
                  <span class="dot critical"></span>
                  <span>Critical</span>
                </div>
                <div class="summary-bar">
                  <div class="bar-fill critical" :style="{ width: stats.criticalPercent + '%' }"></div>
                </div>
                <span class="summary-count">{{ stats.criticalShops }}</span>
              </div>
              <div class="summary-item">
                <div class="summary-label">
                  <span class="dot warning"></span>
                  <span>Low Stock</span>
                </div>
                <div class="summary-bar">
                  <div class="bar-fill warning" :style="{ width: stats.lowPercent + '%' }"></div>
                </div>
                <span class="summary-count">{{ stats.lowShops }}</span>
              </div>
              <div class="summary-item">
                <div class="summary-label">
                  <span class="dot healthy"></span>
                  <span>Healthy</span>
                </div>
                <div class="summary-bar">
                  <div class="bar-fill healthy" :style="{ width: stats.healthyPercent + '%' }"></div>
                </div>
                <span class="summary-count">{{ stats.healthyShops }}</span>
              </div>
            </div>
          </div>

          <!-- Top Products Quick View -->
          <div class="top-products-quick mt-3" v-if="topSellingProducts.length > 0">
            <h6 class="summary-title"><i class="bi bi-trophy me-2"></i>Top Performing Products</h6>
            <div class="top-product-list">
              <div v-for="(product, idx) in topSellingProducts.slice(0, 3)" :key="idx" class="top-product-item">
                <span class="rank-badge">{{ idx + 1 }}</span>
                <div class="product-info">
                  <span class="product-name">{{ product.product_name }}</span>
                  <span class="product-sales">{{ product.total_sold }} units sold</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <i :class="toastType === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-circle-fill'" class="me-2"></i>
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDistributorStockHeatmap } from '@/api/apiDistributor'

// State
const loading = ref(true)
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
const stockData = ref(null)
const alerts = ref([])
const criticalProducts = ref([])
const lowProducts = ref([])
const categorySummary = ref({})
const showAllCritical = ref(false)
const showCriticalInfo = ref(false)
const showStockOverviewInfo = ref(false)

// Computed stats
const stats = computed(() => {
  if (!stockData.value?.summary) {
    return {
      totalShops: 0,
      totalProducts: 0,
      criticalAlerts: 0,
      criticalProductCount: 0,
      healthScore: 0,
      criticalShops: 0,
      lowShops: 0,
      healthyShops: 0,
      criticalPercent: 0,
      lowPercent: 0,
      healthyPercent: 0
    }
  }
  
  const summary = stockData.value.summary
  const total = summary.totalShops || 1
  const healthyShops = summary.healthyStockShops || 0
  const healthScore = Math.round((healthyShops / total) * 100)
  
  return {
    totalShops: summary.totalShops || 0,
    totalProducts: summary.totalProducts || 0,
    criticalAlerts: summary.criticalStockShops || 0,
    criticalProductCount: summary.criticalProductCount || criticalProducts.value.length || 0,
    healthScore,
    criticalShops: summary.criticalStockShops || 0,
    lowShops: summary.lowStockShops || 0,
    healthyShops: healthyShops,
    criticalPercent: Math.round((summary.criticalStockShops / total) * 100),
    lowPercent: Math.round((summary.lowStockShops / total) * 100),
    healthyPercent: Math.round((healthyShops / total) * 100)
  }
})

const healthScoreClass = computed(() => {
  if (stats.value.healthScore >= 80) return 'text-success'
  if (stats.value.healthScore >= 50) return 'text-warning'
  return 'text-danger'
})

// Displayed critical products (limited or all)
const displayedCriticalProducts = computed(() => {
  return showAllCritical.value ? criticalProducts.value : criticalProducts.value.slice(0, 4)
})

// Top selling products from stock data
const topSellingProducts = computed(() => {
  if (!stockData.value?.heatmapPoints) return []
  
  // Collect all products with sales data
  const allProducts = []
  stockData.value.heatmapPoints.forEach(shop => {
    if (shop.stockDetails) {
      shop.stockDetails.forEach(product => {
        if (product.total_sold > 0) {
          allProducts.push({
            ...product,
            shop_name: shop.shopName
          })
        }
      })
    }
  })
  
  // Sort by total_sold descending and take top 5
  return allProducts
    .sort((a, b) => b.total_sold - a.total_sold)
    .slice(0, 5)
})

// Load dashboard data
onMounted(async () => {
  await loadDashboardData()
})

const loadDashboardData = async () => {
  loading.value = true
  try {
    const response = await getDistributorStockHeatmap()
    if (response.data?.status === 'success') {
      stockData.value = response.data.data
      // Store for planning page
      sessionStorage.setItem('stockHeatmapData', JSON.stringify(response.data.data))
      
      // Extract critical and low products
      if (response.data.data.criticalProducts) {
        criticalProducts.value = response.data.data.criticalProducts
      }
      if (response.data.data.lowProducts) {
        lowProducts.value = response.data.data.lowProducts
      }
      if (response.data.data.categorySummary) {
        categorySummary.value = response.data.data.categorySummary
      }
      
      // Generate alerts from heatmap points
      generateAlerts(response.data.data.heatmapPoints)
    }
  } catch (err) {
    console.error('[Dashboard Error]', err)
    showToastMsg('Failed to load dashboard data', 'error')
  } finally {
    loading.value = false
  }
}

const generateAlerts = (heatmapPoints) => {
  if (!heatmapPoints) return
  
  const alertList = []
  
  // Critical stock alerts with product details
  heatmapPoints
    .filter(p => p.stockLevel === 'critical')
    .forEach(shop => {
      alertList.push({
        level: 'critical',
        shop: shop.shopName,
        message: `${shop.criticalItems || 0} items critically low`,
        products: shop.criticalProducts || [],
        time: 'Now'
      })
    })
  
  // Low stock warnings with product details
  heatmapPoints
    .filter(p => p.stockLevel === 'low')
    .slice(0, 3)
    .forEach(shop => {
      alertList.push({
        level: 'warning',
        shop: shop.shopName,
        message: `${shop.lowItems || 0} items running low`,
        products: shop.lowProducts || [],
        time: 'Today'
      })
    })
  
  alerts.value = alertList.slice(0, 5)
}

const getAlertIcon = (level) => {
  switch (level) {
    case 'critical': return 'bi bi-exclamation-triangle-fill'
    case 'warning': return 'bi bi-exclamation-circle-fill'
    default: return 'bi bi-info-circle-fill'
  }
}

const scrollToSection = (id) => {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000000) return (num / 10000000).toFixed(1) + 'Cr'
  if (num >= 100000) return (num / 100000).toFixed(1) + 'L'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toFixed(0)
}

const getSellThroughClass = (rate) => {
  if (rate >= 80) return 'excellent'
  if (rate >= 50) return 'good'
  if (rate >= 25) return 'average'
  return 'poor'
}

// Toast notification
const showToastMsg = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => (showToast.value = false), 3000)
}
</script>

<style scoped>
.distributor-home-page {
  background: #ffffff;
  min-height: calc(100vh - 80px);
  padding: 2rem;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.page-header h5 {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  font-size: 1.75rem;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

/* Quick Stats Cards */
.stat-card {
  background: white;
  border-radius: 16px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
  border-color: var(--color-primary);
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.stat-icon.shops {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1565c0;
}

.stat-icon.products {
  background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
  color: #7b1fa2;
}

.stat-icon.critical {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  color: #c62828;
}

.stat-icon.health {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  color: #2e7d32;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.8rem;
  color: #666;
}

/* Critical Products Banner */
.critical-banner {
  background: linear-gradient(135deg, rgba(220, 53, 69, 0.15) 0%, rgba(200, 35, 51, 0.12) 100%);
  border-radius: 16px;
  padding: 1.25rem;
  color: white;
  border: 1px solid rgba(220, 53, 69, 0.15);
  position: relative;
}

.banner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.banner-title {
  display: flex;
  align-items: center;
  font-size: 1rem;
  color: #dc3545;
  gap: 8px;
}

/* Info Button Small */
.info-btn-small {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 2px 6px;
  font-size: 0.9rem;
  transition: color 0.2s ease;
}

.info-btn-small:hover {
  color: #3b82f6;
}

/* Info Overlay & Popup */
.info-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.info-popup {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 450px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.info-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px 12px 0 0;
}

.info-popup-header h6 {
  margin: 0;
  color: #1e293b;
  font-weight: 600;
}

.info-popup-header .close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #64748b;
  cursor: pointer;
  line-height: 1;
}

.info-popup-header .close-btn:hover {
  color: #1e293b;
}

.info-popup-body {
  padding: 1.25rem;
}

.info-item {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.info-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.info-item strong {
  display: block;
  color: #1e293b;
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
}

.info-item p {
  margin: 0;
  color: #64748b;
  font-size: 0.85rem;
  line-height: 1.5;
}

.info-item code {
  display: inline-block;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #3b82f6;
  margin-top: 0.5rem;
}

.info-item .status-list {
  margin: 0.5rem 0 0 0;
  padding-left: 1.25rem;
  font-size: 0.8rem;
  color: #64748b;
}

.info-item .status-list li {
  margin-bottom: 0.25rem;
}

.critical-products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.critical-product-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 12px;
  padding: 1rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(220, 53, 69, 0.2);
  transition: all 0.2s ease;
  color: #1e293b;
}

.critical-product-card:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.15);
}

.product-status-badge {
  margin-bottom: 0.5rem;
}

.product-name {
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-category {
  font-size: 0.75rem;
  opacity: 0.8;
  margin-bottom: 0.75rem;
}

.product-stats {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.product-stats .stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.product-stats .stat-num {
  font-weight: 700;
  font-size: 1rem;
}

.product-stats .stat-txt {
  font-size: 0.65rem;
  opacity: 0.8;
  text-transform: uppercase;
}

.product-shop {
  font-size: 0.75rem;
  opacity: 0.9;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 0.5rem;
  margin-top: 0.5rem;
}

/* Alerts Panel */
.alerts-panel, .quick-actions-panel, .category-panel {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #eee;
}

.panel-header h6 {
  margin: 0;
  font-weight: 600;
  color: #333;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.alert-item.critical {
  background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
  border-left: 3px solid #dc3545;
}

.alert-item.warning {
  background: linear-gradient(135deg, #fffbf0 0%, #fff3cd 100%);
  border-left: 3px solid #ffc107;
}

.alert-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.alert-item.critical .alert-icon {
  background: rgba(220, 53, 69, 0.15);
  color: #dc3545;
}

.alert-item.warning .alert-icon {
  background: rgba(255, 193, 7, 0.2);
  color: #d39e00;
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.alert-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
}

.alert-message {
  font-size: 0.8rem;
  color: #666;
}

.alert-products {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.5rem;
  align-items: center;
}

.products-label {
  font-size: 0.7rem;
  color: #888;
}

.product-tag {
  background: rgba(0, 0, 0, 0.05);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  color: #555;
}

.more-tag {
  font-size: 0.7rem;
  color: #888;
}

.alert-time {
  font-size: 0.75rem;
  color: #999;
  white-space: nowrap;
}

.empty-alerts {
  text-align: center;
  padding: 2rem 1rem;
  color: #666;
}

/* Category Panel */
.category-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.category-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #333;
}

.category-badges {
  display: flex;
  gap: 0.35rem;
}

.category-badges .badge {
  font-size: 0.7rem;
  font-weight: 500;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.3s ease;
  border: 1px solid #eee;
}

.action-btn:hover {
  transform: translateX(5px);
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.15);
}

.action-btn-icon {
  width: 45px;
  height: 45px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.action-btn.stock-levels .action-btn-icon {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  color: #2e7d32;
}

.action-btn.planning .action-btn-icon {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1565c0;
}

.action-btn-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.action-btn-title {
  font-weight: 600;
  color: #333;
  font-size: 0.95rem;
}

.action-btn-desc {
  font-size: 0.8rem;
  color: #666;
}

.action-btn .bi-chevron-right {
  color: #999;
}

/* Stock Summary */
.stock-summary {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1rem;
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.summary-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0;
}

.summary-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.summary-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 90px;
  font-size: 0.8rem;
  color: #555;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.critical { background: #dc3545; }
.dot.warning { background: #ffc107; }
.dot.healthy { background: #28a745; }

.summary-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-fill.critical { background: linear-gradient(90deg, #dc3545, #e57373); }
.bar-fill.warning { background: linear-gradient(90deg, #ffc107, #ffca28); }
.bar-fill.healthy { background: linear-gradient(90deg, #28a745, #66bb6a); }

.summary-count {
  width: 25px;
  text-align: right;
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
}

/* Top Products Quick View */
.top-products-quick {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1rem;
}

.top-product-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.top-product-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: white;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.top-product-item:hover {
  transform: translateX(3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.rank-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.top-product-item .product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.top-product-item .product-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-product-item .product-sales {
  font-size: 0.7rem;
  color: #666;
}

.sell-through {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.sell-through.excellent {
  background: #d4edda;
  color: #155724;
}

.sell-through.good {
  background: #cce5ff;
  color: #004085;
}

.sell-through.average {
  background: #fff3cd;
  color: #856404;
}

.sell-through.poor {
  background: #f8d7da;
  color: #721c24;
}

/* Toast Notification */
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
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

/* Responsive */
@media (max-width: 992px) {
  .alerts-panel, .quick-actions-panel {
    margin-bottom: 1rem;
  }
  
  .critical-products-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .distributor-home-page {
    padding: 1rem;
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }

  .stat-value {
    font-size: 1.25rem;
  }
  
  .critical-products-grid {
    grid-template-columns: 1fr;
  }
}
</style>

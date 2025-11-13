<template>
  <div class="production-planning-page">
    <!-- Header with Export -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h5 class="mb-0"><i class="bi bi-clipboard-check me-2"></i> Production Planning</h5>
      <button class="btn btn-success">
        <i class="bi bi-download me-2"></i> Export Production Plan (CSV)
      </button>
    </div>

    <!-- Filters Section -->
    <div class="filters-card card mb-4">
      <div class="card-body">
        <div class="d-flex gap-3 align-items-center flex-wrap">
          <div class="d-flex align-items-center gap-2">
            <span class="fw-semibold">Filter ▼</span>
          </div>
          
          <div class="filter-group">
            <label class="small text-muted mb-1">Date Picker</label>
            <select class="form-select form-select-sm" v-model="selectedMonth">
              <option value="November 2025">November 2025</option>
              <option value="October 2025">October 2025</option>
              <option value="September 2025">September 2025</option>
            </select>
          </div>

          <div class="filter-group">
            <label class="small text-muted mb-1">Location</label>
            <button class="btn btn-outline-secondary btn-sm">
              <i class="bi bi-geo-alt-fill me-1"></i> All Regions
            </button>
          </div>

          <div class="filter-group">
            <label class="small text-muted mb-1">Time Period</label>
            <select class="form-select form-select-sm" v-model="timePeriod">
              <option value="Monthly">Monthly</option>
              <option value="Quarterly">Quarterly</option>
              <option value="Yearly">Yearly</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- AI-Generated Production Priorities -->
    <div class="card ai-priorities-card mb-4">
      <div class="card-body">
        <h6 class="mb-3"><i class="bi bi-stars me-2"></i>AI-Generated Production Priorities for December 2025</h6>
        <div class="priorities-list">
          <div class="priority-item increase">
            <div class="priority-icon">
              <i class="bi bi-arrow-up-circle-fill"></i>
            </div>
            <div class="priority-content">
              <strong>Increase Production:</strong> Handwoven Silk Brocade & Premium Cotton Batik
              <div class="text-muted small mt-1">Demand up 32% in Northern & Eastern Regions due to festive season</div>
            </div>
          </div>
          <div class="priority-item maintain">
            <div class="priority-icon">
              <i class="bi bi-dash-circle-fill"></i>
            </div>
            <div class="priority-content">
              <strong>Maintain Production:</strong> Designer Silk Collection & Georgette Floral
              <div class="text-muted small mt-1">Stable demand with consistent sales velocity across all regions</div>
            </div>
          </div>
          <div class="priority-item reduce">
            <div class="priority-icon">
              <i class="bi bi-arrow-down-circle-fill"></i>
            </div>
            <div class="priority-content">
              <strong>Reduce Production:</strong> Heavy Velvet & Winter Wool Blends
              <div class="text-muted small mt-1">Seasonal decline down 28% as winter demand subsides</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Top-Selling Products by Region -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3"><i class="bi bi-trophy-fill me-2"></i>Top-Selling Products by Region</h6>
        
        <div class="products-grid">
          <div v-for="(product, idx) in topSellingProducts" :key="idx" class="product-card">
            <div class="product-image-wrapper mb-2">
              <img :src="product.image" :alt="product.name" class="product-image">
              <div class="rank-badge">#{{ idx + 1 }}</div>
            </div>
            <div class="product-info">
              <strong class="product-name">{{ product.name }}</strong>
              <div class="growth-indicator">
                <i class="bi bi-graph-up-arrow"></i>
                <span>{{ product.growth }}</span>
              </div>
              <div class="region-tag">
                <i class="bi bi-geo-alt-fill"></i>
                {{ product.region }}
              </div>
              <div class="sales-volume">
                <span class="label">Sales Volume:</span>
                <span class="value">{{ product.volume }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Section: Performance & Bottom 5 Products -->
    <div class="row g-3">
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h6 class="mb-3"><i class="bi bi-pie-chart-fill me-2"></i>Performance by Product Line</h6>
            <div class="chart-container d-flex justify-content-center align-items-center" style="height: 280px;">
              <!-- Enhanced Pie Chart SVG -->
              <svg viewBox="0 0 240 240" width="240" height="240">
                <defs>
                  <linearGradient id="gradSilk" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                  </linearGradient>
                  <linearGradient id="gradCotton" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#f093fb;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#f5576c;stop-opacity:1" />
                  </linearGradient>
                  <linearGradient id="gradGeorgette" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
                  </linearGradient>
                  <linearGradient id="gradOthers" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#43e97b;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#38f9d7;stop-opacity:1" />
                  </linearGradient>
                </defs>
                <!-- Silk - 35% -->
                <path d="M 120 120 L 120 30 A 90 90 0 0 1 198 75 Z" 
                      fill="url(#gradSilk)" 
                      class="pie-slice" />
                <!-- Cotton - 30% -->
                <path d="M 120 120 L 198 75 A 90 90 0 0 1 198 165 Z" 
                      fill="url(#gradCotton)" 
                      class="pie-slice" />
                <!-- Georgette - 25% -->
                <path d="M 120 120 L 198 165 A 90 90 0 0 1 60 180 Z" 
                      fill="url(#gradGeorgette)" 
                      class="pie-slice" />
                <!-- Others - 10% -->
                <path d="M 120 120 L 60 180 A 90 90 0 0 1 120 30 Z" 
                      fill="url(#gradOthers)" 
                      class="pie-slice" />
                <!-- Center circle -->
                <circle cx="120" cy="120" r="50" fill="white" />
                <text x="120" y="115" text-anchor="middle" font-size="14" font-weight="600" fill="#4a5568">Total</text>
                <text x="120" y="135" text-anchor="middle" font-size="18" font-weight="700" fill="#667eea">85.2K</text>
              </svg>
            </div>
            <div class="legend-container mt-3">
              <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"></span>
                <span class="legend-label">Silk Products (35%)</span>
              </div>
              <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"></span>
                <span class="legend-label">Cotton Products (30%)</span>
              </div>
              <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"></span>
                <span class="legend-label">Georgette Products (25%)</span>
              </div>
              <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);"></span>
                <span class="legend-label">Others (10%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h6 class="mb-3"><i class="bi bi-graph-down-arrow me-2"></i>Bottom 5 Underperforming Products</h6>
            <div class="underperforming-list">
              <div v-for="(item, idx) in underperformingProducts" :key="idx" class="underperforming-item">
                <div class="item-rank">{{ idx + 1 }}</div>
                <div class="item-image">
                  <img :src="item.image" :alt="item.name">
                </div>
                <div class="item-details">
                  <div class="item-name">{{ item.name }}</div>
                  <div class="item-region">{{ item.region }}</div>
                </div>
                <div class="item-metrics">
                  <div class="decline">{{ item.decline }}</div>
                  <div class="volume">{{ item.volume }} units</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedMonth = ref('November 2025')
const timePeriod = ref('Monthly')

const topSellingProducts = ref([
  { 
    name: 'Handwoven Silk Brocade',
    image: 'https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400',
    growth: '+32% MoM',
    region: 'Northern Region',
    volume: '2,450 meters'
  },
  { 
    name: 'Premium Cotton Batik',
    image: 'https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400',
    growth: '+28% MoM',
    region: 'Eastern Region',
    volume: '3,120 meters'
  },
  { 
    name: 'Luxury Georgette Floral',
    image: 'https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400',
    growth: '+24% MoM',
    region: 'Southern Region',
    volume: '1,890 meters'
  },
  { 
    name: 'Designer Silk Collection',
    image: 'https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400',
    growth: '+22% MoM',
    region: 'Western Region',
    volume: '1,650 meters'
  },
  { 
    name: 'Traditional Block Print',
    image: 'https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400',
    growth: '+19% MoM',
    region: 'Central Region',
    volume: '2,280 meters'
  }
])

const underperformingProducts = ref([
  {
    name: 'Heavy Velvet Fabric',
    image: 'https://images.unsplash.com/photo-1636545732552-a94515d1b4c0?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=200',
    region: 'All Regions',
    decline: '-28%',
    volume: '420'
  },
  {
    name: 'Winter Wool Blend',
    image: 'https://images.unsplash.com/photo-1613132955165-3db1e7526e08?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=200',
    region: 'Northern Region',
    decline: '-22%',
    volume: '580'
  },
  {
    name: 'Thick Denim Cotton',
    image: 'https://images.unsplash.com/photo-1636545659284-0481a5aab979?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=200',
    region: 'Western Region',
    decline: '-18%',
    volume: '650'
  },
  {
    name: 'Dark Paisley Print',
    image: 'https://images.unsplash.com/photo-1639654768139-9fd59f1a8417?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=200',
    region: 'Southern Region',
    decline: '-15%',
    volume: '720'
  },
  {
    name: 'Vintage Linen Blend',
    image: 'https://images.unsplash.com/photo-1636545662955-5225152e33bf?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=200',
    region: 'Eastern Region',
    decline: '-12%',
    volume: '890'
  }
])
</script>

<style scoped>
/* ===== Base Styles ===== */
.production-planning-page {
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: calc(100vh - 120px);
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

/* ===== Typography ===== */
h5, h6 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* ===== Cards ===== */
.filters-card, .card {
  border: none;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 8px 30px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

/* ===== AI Priorities Card ===== */
.ai-priorities-card {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border: 2px solid rgba(102, 126, 234, 0.15);
}

.priorities-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.priority-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border-radius: 12px;
  background: white;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.priority-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.priority-item.increase {
  border-left-color: #10b981;
}

.priority-item.increase .priority-icon {
  color: #10b981;
}

.priority-item.maintain {
  border-left-color: #f59e0b;
}

.priority-item.maintain .priority-icon {
  color: #f59e0b;
}

.priority-item.reduce {
  border-left-color: #ef4444;
}

.priority-item.reduce .priority-icon {
  color: #ef4444;
}

.priority-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.priority-content {
  flex: 1;
}

.priority-content strong {
  color: #2d3748;
  font-size: 1rem;
}

/* ===== Filter Section ===== */
.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-group label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6c757d;
}

/* ===== Products Grid ===== */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.25rem;
}

.product-card {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(102, 126, 234, 0.1);
  position: relative;
  overflow: hidden;
}

.product-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.product-card:hover::before {
  transform: scaleX(1);
}

.product-card:hover {
  box-shadow: 0 12px 28px rgba(102, 126, 234, 0.25);
  transform: translateY(-6px);
  border-color: rgba(102, 126, 234, 0.3);
}

.product-image-wrapper {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  height: 140px;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card:hover .product-image {
  transform: scale(1.08);
}

.rank-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.product-info {
  margin-top: 0.75rem;
}

.product-name {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.5rem;
  line-height: 1.3;
}

.growth-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.region-tag {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #6b7280;
  font-size: 0.8rem;
  margin-bottom: 0.4rem;
}

.sales-volume {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.sales-volume .label {
  color: #9ca3af;
  font-weight: 500;
}

.sales-volume .value {
  color: #667eea;
  font-weight: 700;
}

/* ===== Chart Styles ===== */
.chart-container svg {
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.1));
}

.pie-slice {
  cursor: pointer;
  transition: all 0.3s ease;
  transform-origin: center;
}

.pie-slice:hover {
  opacity: 0.85;
  filter: brightness(1.1);
}

.legend-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
}

.legend-label {
  color: #4a5568;
  font-weight: 500;
}

/* ===== Underperforming Products ===== */
.underperforming-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.underperforming-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 10px;
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.underperforming-item:hover {
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transform: translateX(3px);
}

.item-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.item-image {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-details {
  flex: 1;
}

.item-name {
  font-weight: 600;
  color: #2d3748;
  font-size: 0.9rem;
  margin-bottom: 0.15rem;
}

.item-region {
  font-size: 0.75rem;
  color: #6b7280;
}

.item-metrics {
  text-align: right;
}

.decline {
  font-weight: 700;
  color: #ef4444;
  font-size: 0.95rem;
  margin-bottom: 0.15rem;
}

.volume {
  font-size: 0.75rem;
  color: #6b7280;
}

/* ===== Buttons ===== */
.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
  padding: 0.6rem 1.25rem;
}

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.btn-outline-secondary {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border-width: 1.5px;
}

.btn-outline-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.2);
}

/* ===== Form Elements ===== */
.form-select {
  border-radius: 8px;
  border: 1.5px solid #dee2e6;
  transition: all 0.3s ease;
}

.form-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.25rem rgba(102, 126, 234, 0.15);
}

.badge {
  border-radius: 6px;
  padding: 0.35rem 0.65rem;
  font-weight: 500;
}

/* ===== Responsive Design ===== */
@media (max-width: 768px) {
  .production-planning-page {
    padding: 1rem;
  }

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
  }

  .legend-container {
    grid-template-columns: 1fr;
  }

  .d-flex.gap-3 {
    flex-wrap: wrap;
  }
}
</style>

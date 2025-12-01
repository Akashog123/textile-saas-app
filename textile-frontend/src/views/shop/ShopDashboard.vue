<template>
  <div class="shop-dashboard-tab">
    <!-- Hero Header Section -->
    <div class="dashboard-hero mb-4 animate-fade-in">
      <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3">
        <div>
          <h3 class="hero-title mb-2 d-flex align-items-center">
            <i class="bi bi-shop-window me-2"></i>
            Shop Manager
          </h3>
          <p class="hero-subtitle mb-0">
            Welcome back! Here's your business overview.
          </p>
          <small class="text-muted d-block mt-1">Upload supports CSV/XLS/XLSX files up to 16MB.</small>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-gradient btn-sm d-flex align-items-center" @click="handleUploadSalesData">
            <i class="bi bi-cloud-arrow-up me-2"></i>
            Upload Sales Data
          </button>
        </div>
      </div>
    </div>

    <!-- Top metric cards with animations -->
    <div class="row g-3 mb-4">
      <div
        class="col-12 col-sm-6 col-lg-3"
        v-for="(metric, index) in metrics"
        :key="index"
      >
        <div
          class="metric-card p-3 h-100"
          :style="{ animationDelay: (index * 0.1) + 's' }"
        >
          <div class="d-flex align-items-center justify-content-between mb-3">
            <small class="metric-label">{{ metric.label }}</small>
            <div class="metric-icon" :class="metric.iconClass">
              <i :class="metric.icon"></i>
            </div>
          </div>
          <div class="d-flex align-items-end justify-content-between">
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-change" :class="metric.changeClass">
              <i :class="metric.changeIcon" class="me-1"></i>
              {{ metric.change }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="row g-3">
      <div class="col-lg-6 d-flex">
        <div class="card modern-card w-100">
          <div class="card-body d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h6 class="card-title mb-0">
                <i class="bi bi-graph-up me-2"></i>
                Sales Summary
                <small class="text-muted ms-2 fw-normal">{{ salesDateRange }}</small>
              </h6>
              <span 
                class="badge px-3 py-2 rounded-pill" 
                :class="salesComparison.trend === 'up' ? 'bg-success-soft' : salesComparison.trend === 'down' ? 'bg-danger-soft' : 'bg-secondary-soft'"
                v-if="salesGrowth"
              >
                <i :class="salesComparison.trend === 'up' ? 'bi bi-arrow-up me-1' : salesComparison.trend === 'down' ? 'bi bi-arrow-down me-1' : 'bi bi-dash me-1'"></i>
                {{ salesGrowth }}
              </span>
            </div>
            
            <!-- Loading State -->
            <div v-if="salesSummaryLoading" class="summary-content p-4 rounded flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status"></div>
                <p class="text-muted mb-0">Loading sales data...</p>
              </div>
            </div>
            
            <!-- Data State -->
            <div v-else class="summary-content p-4 rounded flex-grow-1 d-flex flex-column justify-content-center">
              <div class="summary-item mb-4">
                <div class="d-flex align-items-start gap-3">
                  <div class="check-icon-circle" :class="salesComparison.trend === 'down' ? 'bg-danger-soft text-danger' : ''">
                    <i :class="salesComparison.trend === 'up' ? 'bi bi-graph-up-arrow' : salesComparison.trend === 'down' ? 'bi bi-graph-down-arrow' : 'bi bi-dash-lg'"></i>
                  </div>
                  <div>
                    <p class="mb-1 fw-medium">
                      {{ salesComparison.message || 'Upload sales data to see weekly insights' }}
                    </p>
                    <small class="text-muted" v-if="topCategory">
                      {{ topCategory.name }} showing highest demand ({{ topCategory.percentage }}%)
                    </small>
                    <small class="text-muted" v-else>
                      Upload data to see category insights
                    </small>
                  </div>
                </div>
              </div>
              <div class="summary-stats row g-3 mb-4">
                <div class="col-6">
                  <div class="stat-box h-100">
                    <small class="text-muted d-block mb-1">Total Quantity</small>
                    <strong class="fs-4 text-dark">{{ salesSummaryMetrics.totalQuantity.toLocaleString() }}</strong>
                  </div>
                </div>
                <div class="col-6">
                  <div class="stat-box h-100">
                    <small class="text-muted d-block mb-1">Total Revenue</small>
                    <strong class="fs-4 text-dark">{{ salesSummaryMetrics.totalRevenue }}</strong>
                  </div>
                </div>
              </div>
              
              <!-- Daily Breakdown Mini Chart -->
              <div v-if="salesSummaryData?.daily_breakdown?.length" class="daily-mini-chart">
                <small class="text-muted d-block mb-2">Daily Breakdown</small>
                <div class="d-flex align-items-end gap-1" style="height: 40px;">
                  <div 
                    v-for="(day, idx) in salesSummaryData.daily_breakdown" 
                    :key="idx"
                    class="daily-bar bg-primary"
                    :style="{ height: `${Math.max(10, (day.revenue / Math.max(...salesSummaryData.daily_breakdown.map(d => d.revenue), 1)) * 100)}%` }"
                    :title="`${day.day_name}: ${day.revenue_formatted}`"
                  ></div>
                </div>
                <div class="d-flex justify-content-between mt-1">
                  <small v-for="(day, idx) in salesSummaryData.daily_breakdown" :key="idx" class="text-muted" style="font-size: 0.65rem;">
                    {{ day.day_name?.substring(0, 2) }}
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 d-flex">
        <div class="card modern-card w-100">
          <div class="card-body d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h6 class="card-title mb-0">
                <i class="bi bi-activity me-2"></i>
                Sales Growth Trend
              </h6>
              <div class="btn-group btn-group-sm" role="group">
                <button 
                  type="button" 
                  class="btn"
                  :class="chartPeriod === 'weekly' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="changeChartPeriod('weekly')"
                >
                  Week
                </button>
                <button 
                  type="button" 
                  class="btn"
                  :class="chartPeriod === 'monthly' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="changeChartPeriod('monthly')"
                >
                  Month
                </button>
                <button 
                  type="button" 
                  class="btn"
                  :class="chartPeriod === 'yearly' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="changeChartPeriod('yearly')"
                >
                  Year
                </button>
              </div>
            </div>
            
            <!-- Growth Badge -->
            <div v-if="salesTrendData?.growth_percent !== undefined" class="mb-2">
              <span 
                class="badge px-2 py-1 rounded-pill"
                :class="salesTrendData.trend === 'up' ? 'bg-success-soft' : salesTrendData.trend === 'down' ? 'bg-danger-soft' : 'bg-secondary-soft'"
              >
                <i :class="salesTrendData.trend === 'up' ? 'bi bi-arrow-up' : salesTrendData.trend === 'down' ? 'bi bi-arrow-down' : 'bi bi-dash'" class="me-1"></i>
                {{ salesTrendData.growth_percent_formatted }}
              </span>
              <small class="text-muted ms-2">{{ salesTrendData.total_revenue_formatted }} total</small>
            </div>
            
            <!-- Loading State -->
            <div v-if="chartLoading" class="chart-container flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <div class="spinner-border spinner-border-sm text-primary mb-2" role="status"></div>
                <p class="text-muted small mb-0">Loading chart...</p>
              </div>
            </div>
            
            <!-- No Data State -->
            <div v-else-if="!salesTrendData || salesTrendData.status === 'no_data'" class="chart-container flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <i class="bi bi-bar-chart-line fs-2 text-muted mb-2"></i>
                <p class="text-muted small mb-0">Upload sales data to see trends</p>
              </div>
            </div>
            
            <!-- Chart -->
            <div v-else class="chart-container flex-grow-1 d-flex flex-column justify-content-center" @click="viewDetailedChart">
              <div class="chart-wrapper">
                <svg viewBox="0 0 400 180" class="w-100 h-100" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stop-color="var(--color-primary)" stop-opacity="0.2"/>
                      <stop offset="100%" stop-color="var(--color-primary)" stop-opacity="0"/>
                    </linearGradient>
                  </defs>
                  <path
                    :d="salesTrendData.chart_area_path || 'M0,160 L400,160 L400,180 L0,180 Z'"
                    fill="url(#chartGradient)"
                    class="chart-area"
                  />
                  <path
                    :d="salesTrendData.chart_path || 'M0,160 L400,160'"
                    fill="none"
                    stroke="var(--color-primary)"
                    stroke-width="3"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="chart-path"
                  />
                  <circle
                    v-for="(point, i) in salesTrendData.data_points"
                    :key="i"
                    :cx="point.x"
                    :cy="point.y"
                    r="5"
                    class="chart-point"
                    @mouseenter="showChartTooltip($event, point)"
                    @mouseleave="hideChartTooltip"
                  />
                </svg>
                <!-- Tooltip -->
                <div 
                  v-if="chartTooltip.visible" 
                  class="chart-tooltip"
                  :style="{ left: chartTooltip.x + 'px', top: chartTooltip.y + 'px' }"
                >
                  <strong>{{ chartTooltip.label }}</strong>
                  <div>{{ chartTooltip.value }}</div>
                </div>
              </div>
              <div class="chart-labels d-flex justify-content-between mt-3 px-2">
                <small 
                  class="text-muted fw-medium" 
                  v-for="(label, idx) in chartLabels" 
                  :key="idx"
                  :style="{ fontSize: chartPeriod === 'monthly' ? '0.6rem' : '0.75rem' }"
                >{{ label }}</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 d-flex">
        <div class="card modern-card w-100">
          <div class="card-body d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h6 class="card-title mb-0">
                <i class="bi bi-graph-up-arrow me-2"></i>
                Next Quarter Demand Forecast
              </h6>
              <span v-if="quarterlyForecastData?.summary?.confidence_level" class="badge" :class="{
                'bg-success-soft': quarterlyForecastData.summary.confidence_level === 'High',
                'bg-warning-soft': quarterlyForecastData.summary.confidence_level === 'Medium',
                'bg-danger-soft': quarterlyForecastData.summary.confidence_level === 'Low'
              }">
                {{ quarterlyForecastData.summary.confidence_level }} Confidence
              </span>
            </div>
            
            <!-- Loading State -->
            <div v-if="quarterlyForecastLoading" class="forecast-container p-3 rounded flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status"></div>
                <p class="text-muted mb-0">Generating forecast...</p>
              </div>
            </div>
            
            <!-- Error State -->
            <div v-else-if="quarterlyForecastError" class="forecast-container p-4 rounded flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <i class="bi bi-exclamation-triangle fs-1 text-warning mb-2"></i>
                <p class="text-muted mb-2">{{ quarterlyForecastError }}</p>
                <button class="btn btn-outline-primary btn-sm" @click="fetchQuarterlyForecast">
                  <i class="bi bi-arrow-clockwise me-1"></i>Retry
                </button>
              </div>
            </div>
            
            <!-- No Data State -->
            <div v-else-if="!quarterlyForecastData || quarterlyForecastData.status === 'no_data'" class="forecast-container p-4 rounded flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <i class="bi bi-bar-chart-line fs-1 text-muted mb-2"></i>
                <p class="fw-medium mb-1">No Forecast Data Available</p>
                <small class="text-muted d-block mb-3">Upload at least 30 days of sales data to generate demand forecasts</small>
              </div>
            </div>
            
            <!-- Data State -->
            <div v-else class="forecast-container p-3 rounded flex-grow-1">
              <!-- Total Predicted Revenue -->
              <div v-if="quarterlyForecastData?.summary" class="forecast-total mb-3 p-3 bg-primary-soft rounded text-center">
                <small class="text-muted d-block">Predicted Quarter Revenue</small>
                <strong class="fs-4 text-primary">{{ quarterlyForecastData.summary.total_predicted_revenue_formatted || '₹0' }}</strong>
                <div v-if="quarterlyForecastData.summary.total_predicted_quantity" class="mt-1">
                  <small class="text-muted">Est. {{ quarterlyForecastData.summary.total_predicted_quantity.toLocaleString() }} units</small>
                </div>
              </div>
              
              <!-- Category Forecasts - Show actionable items -->
              <div v-if="actionableForecasts.length > 0">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <small class="text-muted">Top Categories</small>
                  <button 
                    v-if="quarterlyForecastData?.category_forecast?.length > 3" 
                    class="btn btn-link btn-sm p-0 text-primary"
                    @click="showAllCategories = !showAllCategories"
                  >
                    {{ showAllCategories ? 'Show Less' : `View All (${quarterlyForecastData.category_forecast.length})` }}
                  </button>
                </div>
                <div class="row g-2">
                  <div
                    :class="showAllCategories ? 'col-6 col-md-4' : 'col-4'"
                    v-for="(forecast, index) in displayedForecasts"
                    :key="index"
                  >
                    <div
                      class="forecast-item h-100 d-flex flex-column align-items-center justify-content-center text-center p-2"
                      :class="{ 'border-primary': forecast.is_actionable }"
                      @click="viewForecastDetails(forecast)"
                    >
                      <div class="forecast-icon mb-1" :class="getTrendIconBg(forecast.trend)">
                        <i :class="getTrendIcon(forecast.trend)" :style="{ color: getTrendColor(forecast.trend) }"></i>
                      </div>
                      <small class="d-block fw-bold mb-1 text-dark text-truncate" style="max-width: 100%; font-size: 0.75rem;">{{ forecast.name }}</small>
                      <div class="forecast-badge small" :class="getTrendBadgeClass(forecast.trend)">
                        <i :class="forecast.trend === 'up' ? 'bi bi-arrow-up' : forecast.trend === 'down' ? 'bi bi-arrow-down' : 'bi bi-dash'" class="me-1"></i>
                        {{ formatTrendPercent(forecast) }}
                      </div>
                      <small class="text-muted mt-1" style="font-size: 0.65rem;">{{ forecast.predicted }}</small>
                      <small v-if="forecast.insight" class="text-primary mt-1 d-none d-md-block" style="font-size: 0.6rem;">{{ forecast.insight }}</small>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Fallback to static forecasts if no data -->
              <div v-else class="row g-3">
                <div
                  class="col-4"
                  v-for="(forecast, index) in forecasts"
                  :key="index"
                >
                  <div
                    class="forecast-item h-100 d-flex flex-column align-items-center justify-content-center text-center p-3"
                    @click="viewForecastDetails(forecast)"
                  >
                    <div class="forecast-icon mb-2" :class="forecast.iconBg">
                      <i :class="forecast.icon" :style="{ color: forecast.color }"></i>
                    </div>
                    <small class="d-block fw-bold mb-1 text-dark text-truncate" style="max-width: 100%;">{{ forecast.name }}</small>
                    <div class="forecast-badge" :class="forecast.badgeClass">
                      <i :class="forecast.trendIcon" class="me-1"></i>
                      {{ forecast.trend }}
                    </div>
                    <small v-if="forecast.predicted" class="text-muted mt-1" style="font-size: 0.7rem;">{{ forecast.predicted }}</small>
                  </div>
                </div>
              </div>
              
              <!-- Monthly Breakdown -->
              <div v-if="quarterlyForecastData?.monthly_forecast?.length" class="mt-3">
                <small class="text-muted d-block mb-2">Monthly Breakdown</small>
                <div class="d-flex gap-2">
                  <div 
                    v-for="(month, idx) in quarterlyForecastData.monthly_forecast" 
                    :key="idx"
                    class="flex-fill p-2 rounded text-center monthly-breakdown-item"
                    :class="idx === 0 ? 'bg-primary-soft' : 'bg-light'"
                  >
                    <small class="text-muted d-block" style="font-size: 0.65rem;">{{ month.month?.split(' ')[0] }}</small>
                    <strong class="small">{{ month.predicted_revenue_formatted }}</strong>
                  </div>
                </div>
              </div>
              
              <!-- Insights from Forecast -->
              <div v-if="quarterlyForecastData?.insights?.length" class="mt-3">
                <div 
                  v-for="(insight, idx) in quarterlyForecastData.insights.slice(0, 2)" 
                  :key="idx"
                  class="d-flex align-items-start gap-2 p-2 rounded mb-2"
                  :class="insight.type === 'warning' ? 'bg-warning-soft' : 'bg-light'"
                >
                  <i :class="insight.icon || 'bi bi-lightbulb'" class="text-primary mt-1"></i>
                  <small class="text-muted">{{ insight.message }}</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 d-flex">
        <div class="card modern-card ai-insights-card w-100">
          <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between align-items-center mb-4">
              <h6 class="card-title mb-0">
                <i class="bi bi-stars me-2"></i>
                AI-Powered Insights
              </h6>
              <button class="btn btn-outline-primary btn-sm" @click="generateInsightsPDF" :disabled="generatingPDF">
                <span v-if="generatingPDF"><span class="spinner-border spinner-border-sm me-1"></span>Generating...</span>
                <span v-else><i class="bi bi-file-earmark-pdf me-1"></i>Export PDF</span>
              </button>
            </div>
            <div class="insights-container flex-grow-1 custom-scrollbar">
              <div
                class="insight-item mb-3"
                v-for="(insight, index) in aiInsights"
                :key="index"
              >
                <div class="d-flex align-items-start gap-3">
                  <div class="insight-icon flex-shrink-0">
                    <i :class="insight.icon"></i>
                  </div>
                  <div class="flex-grow-1">
                    <strong class="d-block mb-1 text-dark">{{ insight.title }}</strong>
                    <p class="mb-0 small text-muted lh-sm">
                      {{ insight.description }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-12">
        <div class="card modern-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-4">
              <h6 class="card-title mb-0">
                <i class="bi bi-cart-check me-2"></i>
                Smart Reorder Suggestions
              </h6>
              <button
                class="btn btn-outline-gradient btn-sm"
                @click="viewAllSuggestions"
              >
                <i class="bi bi-grid-3x3-gap me-1"></i>
                View All
              </button>
            </div>
            
            <!-- Grouped reorder suggestions -->
            <div v-if="Object.keys(groupedReorderSuggestions).length === 0" class="text-center py-5 text-muted">
              <div class="empty-state-icon mb-3">
                <i class="bi bi-inbox"></i>
              </div>
              <p class="mb-0">No reorder suggestions at this time</p>
            </div>
            
            <div v-else class="distributor-groups">
              <div 
                v-for="(products, distributorName) in groupedReorderSuggestions" 
                :key="distributorName"
                class="distributor-group mb-4"
              >
                <div class="distributor-header p-3 rounded-top bg-light-subtle border-bottom">
                  <div class="d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center gap-3">
                      <div class="distributor-icon">
                        <i class="bi bi-building"></i>
                      </div>
                      <div>
                        <h6 class="mb-0 fw-bold text-dark">{{ distributorName }}</h6>
                        <small class="text-muted">{{ products.length }} item(s) to reorder</small>
                      </div>
                    </div>
                    <button 
                      class="btn btn-sm btn-primary d-flex align-items-center"
                      @click="reorderFromDistributor(distributorName, products)"
                    >
                      <i class="bi bi-cart-plus me-2"></i>
                      Order All
                    </button>
                  </div>
                </div>
                
                <div class="reorder-carousel">
                  <div class="carousel-track" style="overflow-x: auto;">
                    <div
                      class="reorder-card"
                      v-for="(product, index) in products"
                      :key="index"
                      @click="viewProduct(product)"
                    >
                      <div class="product-image-wrapper">
                        <img
                          :src="product.image"
                          :alt="product.name"
                          class="product-image"
                        />
                        <div class="product-badge">
                          <i class="bi bi-lightning-fill"></i>
                          Low Stock
                        </div>
                      </div>
                      <div class="product-details p-3">
                        <h6 class="product-name mb-1">{{ product.name }}</h6>
                        <p class="product-supplier mb-2">
                          <i class="bi bi-tag me-1"></i>
                          {{ product.category }}
                        </p>
                        <div class="mb-2">
                          <small class="text-muted d-block">Current: {{ product.currentStock }} units</small>
                          <small class="text-danger d-block">Min Required: {{ product.minimumStock }} units</small>
                        </div>
                        <div class="d-flex align-items-center justify-content-between mb-2">
                          <span class="product-quantity text-success fw-bold"
                            >Reorder: {{ product.quantity }}</span
                          >
                          <span class="product-price">{{ product.price }}</span>
                        </div>
                        <div class="product-sku mb-3">
                          <small class="text-muted">SKU: {{ product.sku }}</small>
                        </div>
                        <div class="text-muted small mt-2">
                          Review supplier contact to place the order directly.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick View Modal -->
    <transition name="modal-fade">
      <div v-if="showQuickView" class="modal-overlay" @click="closeQuickView">
        <div class="quick-view-modal" @click.stop>
          <button class="modal-close-btn" @click="closeQuickView">
            <i class="bi bi-x-lg"></i>
          </button>
          <div class="row g-4" v-if="selectedProduct">
            <div class="col-md-6">
              <img
                :src="selectedProduct.image"
                :alt="selectedProduct.name"
                class="w-100 rounded"
              />
            </div>
            <div class="col-md-6">
              <h4 class="mb-3">{{ selectedProduct.name }}</h4>
              <div class="rating mb-3">
                <span v-for="i in 5" :key="i" class="text-warning">
                  <i
                    :class="
                      i <= selectedProduct.rating
                        ? 'bi bi-star-fill'
                        : 'bi bi-star'
                    "
                  ></i>
                </span>
                <span class="ms-2">({{ selectedProduct.rating }}/5)</span>
              </div>
              <p class="mb-3">{{ selectedProduct.description }}</p>
              <div class="mb-3">
                <h5 class="price-large">{{ selectedProduct.price }}</h5>
                <small class="text-muted"
                  >Sold by: {{ selectedProduct.soldBy }}</small
                >
              </div>
              <div class="alert alert-info mt-3 mb-0">
                Reach out to the distributor to place this reorder.
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- AI Insights Modal -->
    <transition name="modal-fade">
      <div v-if="showInsightsModal" class="modal-overlay" @click="closeInsightsModal">
        <div class="quick-view-modal" @click.stop style="max-width: 600px;">
          <button class="modal-close-btn" @click="closeInsightsModal">
            <i class="bi bi-x-lg"></i>
          </button>
          <div class="text-center mb-4">
            <div class="insight-icon-large mb-3 text-primary">
              <i class="bi bi-stars fs-1"></i>
            </div>
            <h4 class="mb-2">AI Sales Analysis</h4>
            <p class="text-muted" v-if="!insightsLoading">Insights generated from your latest upload</p>
            <p class="text-muted" v-else>Processing your data...</p>
          </div>
          
          <div v-if="insightsLoading" class="text-center py-5">
            <div class="spinner-border text-primary mb-3" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted mb-0">Analyzing sales patterns...</p>
            <small class="text-muted">This may take a moment</small>
          </div>
          
          <div class="insights-list" v-else-if="uploadInsights">
            <div class="card bg-light border-0 mb-3" v-if="uploadInsights.demand_summary">
              <div class="card-body">
                <h6 class="card-title text-primary mb-2">
                  <i class="bi bi-graph-up-arrow me-2"></i>Demand Summary
                </h6>
                <p class="mb-0 small">{{ uploadInsights.demand_summary }}</p>
              </div>
            </div>

            <div class="card bg-light border-0 mb-3" v-if="uploadInsights.recommendation">
              <div class="card-body">
                <h6 class="card-title text-success mb-2">
                  <i class="bi bi-lightbulb me-2"></i>Recommendation
                </h6>
                <p class="mb-0 small">{{ uploadInsights.recommendation }}</p>
              </div>
            </div>

            <div class="d-flex flex-column gap-2">
              <div v-for="(insight, idx) in uploadInsights.ai_insights" :key="idx" class="d-flex align-items-start gap-2 p-2 border rounded bg-white">
                <i class="bi bi-check-circle-fill text-primary mt-1"></i>
                <div>
                  <strong>{{ insight.title }}</strong>
                  <p class="mb-0 small text-muted">{{ insight.description }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-4">
            <button class="btn btn-gradient w-100" @click="closeInsightsModal">
              Got it
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Toast Notification -->
    <transition name="toast">
      <div v-if="showToast" class="toast-notification">
        <i :class="toastIcon" class="me-2"></i>
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { 
  getShopDashboard, 
  uploadSalesData as uploadSalesDataAPI, 
  getDemandForecast, 
  getSalesUploadLogs, 
  generateSalesReportPdf,
  getSalesSummary,
  getQuarterlyForecast,
  getSalesGrowthTrend
} from '@/api/apiShop';

// Loading and error states
const loading = ref(false);
const error = ref('');

// Dashboard data from backend
const dashboardData = ref(null);

// NEW: Sales Summary (Last 7 Days) data
const salesSummaryData = ref(null);
const salesSummaryLoading = ref(false);
const salesSummaryError = ref('');

// NEW: Quarterly Forecast data
const quarterlyForecastData = ref(null);
const quarterlyForecastLoading = ref(false);
const quarterlyForecastError = ref('');

// NEW: Sales Growth Trend chart data
const salesTrendData = ref(null);
const chartLoading = ref(false);
const chartPeriod = ref('weekly');
const chartTooltip = ref({ visible: false, x: 0, y: 0, label: '', value: '' });

// Demand forecast data (legacy)
const demandForecast = ref([]);
const forecastLoading = ref(false);
const forecastError = ref('');

// Upload logs for audit transparency
const uploadLogs = ref([]);
const uploadLogsLoading = ref(false);
const uploadLogsError = ref('');

// PDF generation state
const generatingPDF = ref(false);

// Sales summary computed properties
const salesDateRange = computed(() => {
  if (salesSummaryData.value?.period?.label) {
    return salesSummaryData.value.period.label;
  }
  if (!dashboardData.value) return 'Last 7 days';
  return dashboardData.value.date_range || 'Last 7 days';
});

const salesGrowth = computed(() => {
  if (salesSummaryData.value?.comparison?.revenue_change_percent) {
    return salesSummaryData.value.comparison.revenue_change_percent;
  }
  if (!dashboardData.value) return null;
  return dashboardData.value.growth || null;
});

// NEW: Computed properties for sales summary display
const salesSummaryMetrics = computed(() => {
  if (!salesSummaryData.value?.metrics) {
    return {
      totalRevenue: '₹0',
      totalQuantity: 0,
      avgOrderValue: '₹0',
      totalOrders: 0
    };
  }
  const m = salesSummaryData.value.metrics;
  return {
    totalRevenue: m.total_revenue_formatted || '₹0',
    totalQuantity: m.total_quantity || 0,
    avgOrderValue: m.average_order_value_formatted || '₹0',
    totalOrders: m.total_orders || 0
  };
});

const salesComparison = computed(() => {
  if (!salesSummaryData.value?.comparison) {
    return { trend: 'stable', changePercent: '0%', message: '' };
  }
  const c = salesSummaryData.value.comparison;
  return {
    trend: c.trend || 'stable',
    changePercent: c.revenue_change_percent || '0%',
    message: c.trend === 'up' 
      ? `Sales increased by ${c.revenue_change_percent} compared to last week`
      : c.trend === 'down'
      ? `Sales decreased by ${c.revenue_change_percent.replace('-', '')} compared to last week`
      : 'Sales remained stable compared to last week'
  };
});

const topCategory = computed(() => {
  if (!salesSummaryData.value?.top_categories?.length) {
    return null;
  }
  return salesSummaryData.value.top_categories[0];
});

// Chart labels based on period
const chartLabels = computed(() => {
  if (salesTrendData.value?.labels?.length) {
    // For monthly, show fewer labels to avoid crowding
    if (chartPeriod.value === 'monthly' && salesTrendData.value.labels.length > 10) {
      const labels = salesTrendData.value.labels;
      const step = Math.ceil(labels.length / 10);
      return labels.filter((_, idx) => idx % step === 0 || idx === labels.length - 1);
    }
    return salesTrendData.value.labels;
  }
  // Default labels based on period
  if (chartPeriod.value === 'weekly') {
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  } else if (chartPeriod.value === 'monthly') {
    return Array.from({ length: 10 }, (_, i) => `${(i + 1) * 3}`);
  } else {
    return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  }
});

// NEW: Category forecast computed properties
const showAllCategories = ref(false);

// Transform category forecast data for display
const actionableForecasts = computed(() => {
  if (!quarterlyForecastData.value?.category_forecast?.length) {
    return [];
  }
  return quarterlyForecastData.value.category_forecast.map(cat => ({
    name: cat.category,
    predicted: cat.predicted_revenue_formatted,
    trend: cat.trend,
    growth_rate: cat.growth_rate,
    proportion: cat.proportion_percent,
    insight: cat.insight,
    is_actionable: cat.is_actionable,
    priority: cat.priority
  }));
});

// Show top 3 by default, all when expanded
const displayedForecasts = computed(() => {
  if (showAllCategories.value) {
    return actionableForecasts.value;
  }
  // Show top 3 actionable items, or just top 3 if none are actionable
  const actionable = actionableForecasts.value.filter(f => f.is_actionable);
  if (actionable.length >= 3) {
    return actionable.slice(0, 3);
  }
  return actionableForecasts.value.slice(0, 3);
});

// Helper functions for trend display
const getTrendIcon = (trend) => {
  switch (trend) {
    case 'up': return 'bi bi-graph-up-arrow fs-4';
    case 'down': return 'bi bi-graph-down-arrow fs-4';
    default: return 'bi bi-dash-lg fs-4';
  }
};

const getTrendColor = (trend) => {
  switch (trend) {
    case 'up': return '#10b981';
    case 'down': return '#ef4444';
    default: return '#6b7280';
  }
};

const getTrendIconBg = (trend) => {
  switch (trend) {
    case 'up': return 'bg-success-soft';
    case 'down': return 'bg-danger-soft';
    default: return 'bg-secondary-soft';
  }
};

const getTrendBadgeClass = (trend) => {
  switch (trend) {
    case 'up': return 'bg-success-soft text-success';
    case 'down': return 'bg-danger-soft text-danger';
    default: return 'bg-secondary-soft text-secondary';
  }
};

const formatTrendPercent = (forecast) => {
  if (forecast.growth_rate !== undefined && forecast.growth_rate !== 0) {
    return forecast.growth_rate > 0 ? `+${forecast.growth_rate}%` : `${forecast.growth_rate}%`;
  }
  return `${forecast.proportion}%`;
};

// Shop ID - get from logged-in user
const shopId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  return user.shop_id || user.id; // Adjust based on your user object structure
});

// Metrics Data - dynamically populated from backend
const metrics = ref([
  {
    label: 'Weekly Sales',
    value: '₹0',
    change: '+0%',
    changeClass: 'positive',
    changeIcon: 'bi bi-arrow-up',
    icon: 'bi bi-currency-rupee',
    iconClass: 'bg-success-soft',
  },
  {
    label: 'Pending Reorders',
    value: '0',
    change: '-0',
    changeClass: 'positive',
    changeIcon: 'bi bi-arrow-down',
    icon: 'bi bi-cart-check',
    iconClass: 'bg-warning-soft',
  },
  {
    label: 'Customer Rating',
    value: '0.0★',
    change: '+0',
    changeClass: 'positive',
    changeIcon: 'bi bi-arrow-up',
    icon: 'bi bi-star-fill',
    iconClass: 'bg-info-soft ',
  },
  {
    label: 'Growth',
    value: '0%',
    change: '+0%',
    changeClass: 'positive',
    changeIcon: 'bi bi-graph-up',
    icon: 'bi bi-graph-up-arrow',
    iconClass: 'bg-success-soft',
  },
]);

// Chart Points - from forecast data
const chartPoints = ref([
  { x: 0, y: 140, value: 0 },
  { x: 50, y: 130, value: 0 },
  { x: 100, y: 100, value: 0 },
  { x: 150, y: 110, value: 0 },
  { x: 200, y: 70, value: 0 },
  { x: 250, y: 60, value: 0 },
  { x: 300, y: 50, value: 0 },
  { x: 350, y: 35, value: 0 },
]);

// Forecasts - populated from backend
const forecasts = ref([
  {
    name: 'Cotton',
    icon: 'bi bi-graph-up-arrow fs-3',
    color: '#10b981',
    iconBg: 'bg-success-soft',
    trend: '+0%',
    trendIcon: 'bi bi-arrow-up',
    badgeClass: 'trend-up',
  },
  {
    name: 'Silk',
    icon: 'bi bi-bar-chart-fill fs-3',
    color: 'var(--color-primary)',
    iconBg: 'bg-primary-soft',
    trend: 'Stable',
    trendIcon: 'bi bi-dash',
    badgeClass: 'trend-stable',
  },
  {
    name: 'Linen',
    icon: 'bi bi-graph-down-arrow fs-3',
    color: '#ef4444',
    iconBg: 'bg-danger-soft',
    trend: '-0%',
    trendIcon: 'bi bi-arrow-down',
    badgeClass: 'trend-down',
  },
]);

// AI Insights - from backend
const aiInsights = ref([]);

// Reorder Products
const reorderProducts = ref([]);

// Grouped reorder suggestions by distributor (Story 2)
const groupedReorderSuggestions = ref({});

// Available Products
const availableProducts = ref([]);

// Product Filters
const productFilters = ref([
  { id: 'all', label: 'All', icon: 'bi bi-grid' },
  { id: 'category', label: 'Category', icon: 'bi bi-palette-fill' },
  { id: 'price', label: 'Price', icon: 'bi bi-rulers' },
  { id: 'brand', label: 'Brand', icon: 'bi bi-tag-fill' },
]);

const selectedFilter = ref('all');

// Carousel Controls
const carouselTrack = ref(null);
const showLeftArrow = ref(false);
const showRightArrow = ref(true);

// Quick View
const showQuickView = ref(false);
const selectedProduct = ref(null);

// AI Insights Modal
const showInsightsModal = ref(false);
const insightsLoading = ref(false);
const uploadInsights = ref(null);

const closeInsightsModal = () => {
  if (insightsLoading.value) return; // Prevent closing while loading
  showInsightsModal.value = false;
  uploadInsights.value = null;
};

// Toast
const showToast = ref(false);
const toastMessage = ref('');
const toastIcon = ref('bi bi-check-circle-fill');

const formatUploadTiming = (log) => {
  if (!log) return '';
  const duration = log.duration_ms ? (log.duration_ms / 1000).toFixed(1) : null;
  const sla = log.sla_limit_ms ? log.sla_limit_ms / 1000 : 120;
  if (!duration) return '';
  const breached = log.sla_breached ? ' (SLA exceeded)' : '';
  return `Processed in ${duration}s (SLA ${sla}s)${breached}`;
};

const limitSentences = (text, max = 4) => {
  if (!text) return text;
  const sentences = text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return sentences.slice(0, max).join(' ');
};

const formatLogDate = (timestamp) => {
  if (!timestamp) return '—';
  try {
    return new Date(timestamp).toLocaleString();
  } catch {
    return timestamp;
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

/**
 * Fetch dashboard data from backend
 */
const fetchDashboard = async () => {
  if (!shopId.value) {
    error.value = 'Shop ID not found. Please log in again.';
    return;
  }

  loading.value = true;
  error.value = '';
  try {
    const response = await getShopDashboard(shopId.value);
    const payload = response.data?.data || response.data;
    if (payload) {
      dashboardData.value = payload;
      updateMetricsFromData(payload);
      updateReorderSuggestions(payload);
      updateForecastsFromData(payload);
      updateInsightsFromData(payload);
      if (response.data?.warning) {
        toastMessage.value = response.data.warning;
        toastIcon.value = 'bi bi-exclamation-triangle';
        showToast.value = true;
        setTimeout(() => (showToast.value = false), 5000);
      }
    }
  } catch (err) {
    console.error('[Dashboard Error]', err);
    error.value = err.response?.data?.message || 'Failed to load dashboard';
    // Keep default values if API fails
  } finally {
    loading.value = false;
  }
};

/**
 * Update metrics from dashboard data
 */
const updateMetricsFromData = (data) => {
  // metrics[0] = Weekly Sales
  if (data.weekly_sales !== undefined) {
    metrics.value[0].value = data.weekly_sales || '₹0';
  }
  // metrics[1] = Pending Reorders
  if (data.pending_reorders !== undefined) {
    metrics.value[1].value = data.pending_reorders || 0;
  }
  // metrics[2] = Customer Rating
  if (data.customer_rating !== undefined) {
    metrics.value[2].value = `${data.customer_rating}★`;
  }
  // metrics[3] = Growth
  if (data.growth !== undefined) {
    metrics.value[3].value = data.growth || '0%';
    // Update change indicator based on growth direction
    const growthNum = parseFloat(data.growth);
    if (!isNaN(growthNum)) {
      metrics.value[3].changeClass = growthNum >= 0 ? 'positive' : 'negative';
      metrics.value[3].changeIcon = growthNum >= 0 ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
    }
  }
};

const updateReorderSuggestions = (data) => {
  // Backend returns grouped suggestions as a dictionary:
  // { "Distributor Name (ID: X)": { distributor_id, distributor_name, products: [...] }, ... }
  if (data.reorder_suggestions && typeof data.reorder_suggestions === 'object') {
    const grouped = {};
    
    // Process each distributor's products
    for (const [distributorKey, distributorData] of Object.entries(data.reorder_suggestions)) {
      // Handle both old format (array) and new format (object with products array)
      const products = Array.isArray(distributorData) 
        ? distributorData 
        : (distributorData.products || []);
      
      if (products.length > 0) {
        grouped[distributorKey] = products.map(item => ({
          name: item.product_name,
          image: item.image || `https://placehold.co/100x100?text=${encodeURIComponent(item.product_name?.substring(0, 10) || 'Product')}`,
          supplier: distributorData.distributor_name || distributorKey,
          quantity: item.reorder_quantity,
          price: `₹${parseFloat(item.price || 0).toLocaleString()}`,
          sku: item.sku,
          currentStock: item.current_stock,
          minimumStock: item.minimum_stock,
          category: item.category,
          distributorContact: distributorData.distributor_contact,
          distributorEmail: distributorData.distributor_email
        }));
      }
    }
    
    groupedReorderSuggestions.value = grouped;
    
    // Also create a flat list for compatibility
    reorderProducts.value = Object.values(grouped).flat();
  } else {
    groupedReorderSuggestions.value = {};
    reorderProducts.value = [];
  }
};

/**
 * Update forecasts from dashboard data
 */
const updateForecastsFromData = (data) => {
  if (data.forecast && data.forecast.length > 0) {
    // Map forecast data to chart points for visualization
    const forecastData = data.forecast.slice(0, 8); // First 8 points
    chartPoints.value = forecastData.map((point, idx) => ({
      x: idx * 50,
      y: 140 - (point.yhat / 100), // Adjust based on your data scale
      value: point.yhat
    }));
  }
};

/**
 * Update AI insights from dashboard data
 */
/**
 * Update AI insights from dashboard data
 */
const updateInsightsFromData = (data) => {
  if (data.ai_insights && data.ai_insights.length > 0) {
    aiInsights.value = data.ai_insights.map(insight => ({
      icon: insight.category === 'Trend' ? 'bi bi-graph-up-arrow' : 
            insight.category === 'Inventory' ? 'bi bi-box-seam' : 'bi bi-lightbulb',
      title: insight.title,
      description: limitSentences(insight.description || insight.impact, 4)
    }));
  } else {
    // Default insights
    aiInsights.value = [
      {
        icon: 'bi bi-lightbulb-fill',
        title: 'Upload Sales Data',
        description: limitSentences('Upload your sales data to get AI-powered insights and forecasts.', 4)
      }
    ];
  }
};

/**
 * Upload sales data file
 */
const handleUploadSalesData = async () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.csv,.xlsx,.xls';
  
  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
      toastMessage.value = 'File too large (max 16MB)';
      toastIcon.value = 'bi bi-exclamation-circle-fill';
      showToast.value = true;
      setTimeout(() => (showToast.value = false), 3000);
      return;
    }

    loading.value = true;
    
    // Open modal immediately in loading state
    showInsightsModal.value = true;
    insightsLoading.value = true;
    uploadInsights.value = null;

    try {
      // toastMessage.value = 'Uploading periodic sales data...';
      // toastIcon.value = 'bi bi-upload';
      // showToast.value = true;

      const response = await uploadSalesDataAPI(shopId.value, file);
      
      const timingMessage = formatUploadTiming(response.data?.upload_log);
      toastMessage.value = timingMessage || 'Analysis complete!';
      toastIcon.value = response.data?.upload_log?.sla_breached
        ? 'bi bi-exclamation-circle-fill'
        : 'bi bi-check-circle-fill';
      showToast.value = true;
      
      // Update Modal Content
      if (response.data && (response.data.ai_insights || response.data.demand_summary)) {
        uploadInsights.value = {
          ai_insights: (response.data.ai_insights || []).map(item => ({
            ...item,
            description: limitSentences(item.description || item.impact, 4)
          })),
          demand_summary: limitSentences(response.data.demand_summary, 4),
          recommendation: limitSentences(response.data.recommendation, 4)
        };
      } else {
         // Fallback if no specific insights returned
         uploadInsights.value = {
            demand_summary: "Data uploaded successfully.",
            ai_insights: []
         };
      }
      
      // Refresh dashboard after upload
      await fetchDashboard();
      await fetchUploadLogs();
    } catch (err) {
      console.error('[Upload Error]', err);
      if (err.response?.status === 409 && err.response?.data?.upload_log) {
        const duplicateOf = err.response.data.duplicate_of;
        const timingMessage = formatUploadTiming(err.response.data.upload_log);
        toastMessage.value = `${err.response.data.message} ${timingMessage}`.trim();
      } else {
        toastMessage.value = err.response?.data?.message || 'Upload failed';
      }
      toastIcon.value = 'bi bi-exclamation-circle-fill';
      showToast.value = true;
      showInsightsModal.value = false; // Close modal on error
    } finally {
      loading.value = false;
      insightsLoading.value = false;
      setTimeout(() => (showToast.value = false), 3000);
    }
  };
  
  input.click();
};

/**
 * Generate PDF report for AI insights and dashboard summary
 */
const generateInsightsPDF = async () => {
  if (!shopId.value) {
    toastMessage.value = 'Shop ID not found';
    toastIcon.value = 'bi bi-exclamation-circle-fill';
    showToast.value = true;
    setTimeout(() => (showToast.value = false), 3000);
    return;
  }

  generatingPDF.value = true;
  try {
    const payload = {
      shop_id: shopId.value,
      report_type: 'dashboard_insights',
      include_sections: ['sales_summary', 'ai_insights', 'forecast', 'reorder_suggestions']
    };

    const response = await generateSalesReportPdf(payload);
    
    // Create download link
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `shop_insights_${shopId.value}_${new Date().toISOString().split('T')[0]}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);

    toastMessage.value = 'PDF report downloaded successfully!';
    toastIcon.value = 'bi bi-check-circle-fill';
    showToast.value = true;
  } catch (err) {
    console.error('[PDF Generation Error]', err);
    toastMessage.value = err.response?.data?.message || 'Failed to generate PDF';
    toastIcon.value = 'bi bi-exclamation-circle-fill';
    showToast.value = true;
  } finally {
    generatingPDF.value = false;
    setTimeout(() => (showToast.value = false), 3000);
  }
};

const viewDetailedChart = () => {
  toastMessage.value = 'Opening chart analytics...';
  toastIcon.value = 'bi bi-graph-up';
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

const viewForecastDetails = (forecast) => {
  toastMessage.value = `Viewing ${forecast.name} forecast details`;
  toastIcon.value = 'bi bi-calendar-check';
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

const viewAllSuggestions = () => {
  toastMessage.value = 'Loading all suggestions...';
  toastIcon.value = 'bi bi-grid-3x3-gap';
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

const reorderFromDistributor = (distributorName, products) => {
  toastMessage.value = `Reordering ${products.length} items from ${distributorName}`;
  toastIcon.value = 'bi bi-cart-check-fill';
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

const scrollCarousel = (direction) => {
  const track = carouselTrack.value;
  const scrollAmount = 280;
  if (direction === 'left') {
    track.scrollLeft -= scrollAmount;
  } else {
    track.scrollLeft += scrollAmount;
  }
};

const updateArrows = () => {
  const track = carouselTrack.value;
  if (track) {
    showLeftArrow.value = track.scrollLeft > 0;
    showRightArrow.value =
      track.scrollLeft < track.scrollWidth - track.clientWidth - 10;
  }
};

const viewProduct = (product) => {
  selectedProduct.value = product;
  showQuickView.value = true;
};


const selectFilter = (filterId) => {
  selectedFilter.value = filterId;
  toastMessage.value = `Filter applied: ${productFilters.value.find((f) => f.id === filterId).label}`;
  toastIcon.value = 'bi bi-funnel-fill';
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

const viewProductDetails = (product) => {
  selectedProduct.value = product;
  showQuickView.value = true;
};

const quickView = (product) => {
  selectedProduct.value = product;
  showQuickView.value = true;
};

const closeQuickView = () => {
  showQuickView.value = false;
  selectedProduct.value = null;
};

// Tooltip handlers for chart points (can be enhanced with proper tooltip UI)
const tooltipData = ref(null);
const showTooltip = (point) => {
  tooltipData.value = point;
};

const hideTooltip = () => {
  tooltipData.value = null;
};

/**
 * Fetch demand forecast data
 */
const fetchDemandForecast = async () => {
  if (!shopId.value) return;
  
  forecastLoading.value = true;
  forecastError.value = '';
  
  try {
    const response = await getDemandForecast(shopId.value);
    if (response.data && response.data.status === 'success') {
      demandForecast.value = response.data.forecast || [];
    }
  } catch (err) {
    console.error('[Demand Forecast Error]', err);
    forecastError.value = err.response?.data?.message || 'Failed to load demand forecast';
  } finally {
    forecastLoading.value = false;
  }
};

/**
 * Get confidence badge class
 */
const getConfidenceClass = (confidence) => {
  switch (confidence) {
    case 'High': return 'bg-success';
    case 'Medium': return 'bg-warning';
    case 'Low': return 'bg-danger';
    default: return 'bg-secondary';
  }
};

/**
 * NEW: Fetch comprehensive sales summary for last 7 days
 */
const fetchSalesSummary = async () => {
  if (!shopId.value) return;
  
  salesSummaryLoading.value = true;
  salesSummaryError.value = '';
  
  try {
    const response = await getSalesSummary(shopId.value);
    if (response.data?.status === 'success') {
      salesSummaryData.value = response.data.data;
      
      // Update chart points from daily breakdown
      if (salesSummaryData.value?.daily_breakdown?.length > 0) {
        updateChartFromDailyData(salesSummaryData.value.daily_breakdown);
      }
      
      // Update AI insights from sales summary
      if (salesSummaryData.value?.insights?.length > 0) {
        // Merge with existing AI insights
        const summaryInsights = salesSummaryData.value.insights.map(i => ({
          title: i.title,
          icon: i.icon || 'bi bi-lightbulb',
          description: i.message
        }));
        aiInsights.value = [...summaryInsights, ...aiInsights.value.slice(0, 2)];
      }
    } else {
      salesSummaryError.value = response.data?.message || 'Failed to load sales summary';
    }
  } catch (err) {
    console.error('[Sales Summary Error]', err);
    salesSummaryError.value = err.response?.data?.message || 'Failed to load sales summary';
  } finally {
    salesSummaryLoading.value = false;
  }
};

/**
 * NEW: Fetch quarterly demand forecast
 */
const fetchQuarterlyForecast = async () => {
  if (!shopId.value) return;
  
  quarterlyForecastLoading.value = true;
  quarterlyForecastError.value = '';
  
  try {
    const response = await getQuarterlyForecast(shopId.value);
    if (response.data?.status === 'success') {
      quarterlyForecastData.value = response.data.data;
      
      // Update forecast cards from category data
      if (quarterlyForecastData.value?.category_forecast?.length > 0) {
        updateForecastCardsFromData(quarterlyForecastData.value.category_forecast);
      }
    } else {
      quarterlyForecastError.value = response.data?.message || 'Failed to load forecast';
    }
  } catch (err) {
    console.error('[Quarterly Forecast Error]', err);
    quarterlyForecastError.value = err.response?.data?.message || 'Failed to load forecast';
  } finally {
    quarterlyForecastLoading.value = false;
  }
};

/**
 * Update chart points from daily sales data
 */
const updateChartFromDailyData = (dailyData) => {
  if (!dailyData || dailyData.length === 0) return;
  
  // Get max revenue for scaling
  const maxRevenue = Math.max(...dailyData.map(d => d.revenue || 0), 1);
  
  // Map to chart points (7 days)
  const newPoints = [];
  const xSpacing = 400 / Math.max(dailyData.length - 1, 1);
  
  dailyData.forEach((day, index) => {
    // Scale Y from 30 (top) to 160 (bottom)
    const yValue = 160 - ((day.revenue / maxRevenue) * 130);
    newPoints.push({
      x: index * xSpacing,
      y: Math.max(30, Math.min(160, yValue)),
      value: day.revenue,
      label: day.day_name
    });
  });
  
  if (newPoints.length > 0) {
    chartPoints.value = newPoints;
  }
};

/**
 * Update forecast cards from category forecast data
 */
const updateForecastCardsFromData = (categoryData) => {
  if (!categoryData || categoryData.length === 0) return;
  
  const iconConfigs = [
    { icon: 'bi bi-graph-up-arrow fs-3', color: '#10b981', iconBg: 'bg-success-soft' },
    { icon: 'bi bi-bar-chart-fill fs-3', color: 'var(--color-primary)', iconBg: 'bg-primary-soft' },
    { icon: 'bi bi-graph-down-arrow fs-3', color: '#ef4444', iconBg: 'bg-danger-soft' }
  ];
  
  const newForecasts = categoryData.slice(0, 3).map((cat, index) => {
    const config = iconConfigs[index] || iconConfigs[0];
    let trendIcon, badgeClass;
    
    if (cat.trend === 'up') {
      trendIcon = 'bi bi-arrow-up';
      badgeClass = 'trend-up';
    } else if (cat.trend === 'down') {
      trendIcon = 'bi bi-arrow-down';
      badgeClass = 'trend-down';
    } else {
      trendIcon = 'bi bi-dash';
      badgeClass = 'trend-stable';
    }
    
    return {
      name: cat.category,
      icon: config.icon,
      color: config.color,
      iconBg: config.iconBg,
      trend: cat.trend === 'up' ? `+${cat.proportion_percent}%` 
           : cat.trend === 'down' ? `-${cat.proportion_percent}%` 
           : `${cat.proportion_percent}%`,
      trendIcon,
      badgeClass,
      predicted: cat.predicted_revenue_formatted
    };
  });
  
  if (newForecasts.length > 0) {
    forecasts.value = newForecasts;
  }
};

/**
 * NEW: Fetch sales growth trend data for chart
 */
const fetchSalesGrowthTrend = async () => {
  if (!shopId.value) return;
  
  chartLoading.value = true;
  
  try {
    const response = await getSalesGrowthTrend(shopId.value, chartPeriod.value);
    if (response.data?.status === 'success') {
      salesTrendData.value = response.data.data;
    } else {
      salesTrendData.value = null;
    }
  } catch (err) {
    console.error('[Sales Growth Trend Error]', err);
    salesTrendData.value = null;
  } finally {
    chartLoading.value = false;
  }
};

/**
 * Change chart period and refetch data
 */
const changeChartPeriod = (period) => {
  if (chartPeriod.value === period) return;
  chartPeriod.value = period;
  fetchSalesGrowthTrend();
};

/**
 * Show tooltip on chart point hover
 */
const showChartTooltip = (event, point) => {
  const rect = event.target.closest('.chart-wrapper').getBoundingClientRect();
  const targetRect = event.target.getBoundingClientRect();
  chartTooltip.value = {
    visible: true,
    x: targetRect.left - rect.left + 10,
    y: targetRect.top - rect.top - 40,
    label: point.label,
    value: point.value_formatted || `₹${point.value?.toLocaleString() || 0}`
  };
};

/**
 * Hide chart tooltip
 */
const hideChartTooltip = () => {
  chartTooltip.value.visible = false;
};

// Fetch dashboard data on mount
onMounted(() => {
  fetchDashboard();
  updateArrows();
  fetchSalesSummary();
  fetchQuarterlyForecast();
  fetchSalesGrowthTrend();
  fetchUploadLogs();
});
</script>

<style scoped>
/* ===== Base Styles ===== */
.shop-dashboard-tab {
  background: var(--gradient-bg);
  min-height: calc(100vh - 80px);
  padding: 2rem;
}

.animate-fade-in {
  animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
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

/* ===== Card Styles ===== */
.card {
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
  border-color: rgba(255, 255, 255, 0.9);
}

.modern-card {
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h6.card-title {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* ===== Hero Header ===== */
.dashboard-hero {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.8) 0%,
    rgba(255, 255, 255, 0.4) 100%
  );
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
}

.icon-box {
  width: 48px;
  height: 48px;
  background: var(--gradient-primary);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.25);
}

.hero-title {
  background: linear-gradient(135deg, var(--color-text-dark) 0%, var(--color-primary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.03em;
}

.hero-subtitle {
  color: var(--color-text-muted);
  font-size: 1.05rem;
  font-weight: 500;
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

.btn-gradient:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
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

.btn-outline-gradient:hover {
  background: var(--gradient-primary) padding-box,
              var(--gradient-primary) border-box;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.25);
}

/* ===== Metric Cards ===== */
.metric-card {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
  animation: fadeIn 0.6s backwards;
}

.metric-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
  background: white;
  z-index: 1;
}

.metric-label {
  color: var(--color-text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.7rem;
}

.metric-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  transition: transform 0.3s ease;
}

.metric-card:hover .metric-icon {
  transform: rotate(10deg) scale(1.1);
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text-dark);
  letter-spacing: -0.02em;
}

.metric-change {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.35rem 0.6rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
}

.metric-change.positive {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.metric-change.negative {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

/* ===== Background Utilities ===== */
.bg-success-soft { background: rgba(16, 185, 129, 0.1); color: #059669; }
.bg-warning-soft { background: rgba(245, 158, 11, 0.1); color: #d97706; }
.bg-primary-soft { background: rgba(59, 130, 246, 0.1); color: #2563eb; }
.bg-info-soft { background: rgba(6, 182, 212, 0.1); color: #0891b2; }
.bg-danger-soft { background: rgba(239, 68, 68, 0.1); color: #dc2626; }
.bg-secondary-soft { background: rgba(107, 114, 128, 0.1); color: #6b7280; }

/* ===== Sales Summary ===== */
.summary-content {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(248, 250, 252, 0) 100%);
  border: 1px solid rgba(0, 0, 0, 0.03);
  border-radius: 16px;
}

.check-icon-circle {
  width: 32px;
  height: 32px;
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.stat-box {
  background: white;
  padding: 1rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.03);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-box:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

/* ===== Chart ===== */
.chart-container {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(248, 250, 252, 0) 100%);
  border-radius: 16px;
  padding: 1rem;
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.chart-wrapper {
  height: 200px;
  width: 100%;
  position: relative;
}

.chart-path {
  filter: drop-shadow(0 4px 6px rgba(59, 130, 246, 0.3));
  animation: drawLine 2s ease-out forwards;
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
}

@keyframes drawLine {
  to { stroke-dashoffset: 0; }
}

.chart-point {
  fill: white;
  stroke: var(--color-primary);
  stroke-width: 3px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
}

.chart-point:hover {
  r: 8;
  stroke-width: 4px;
  filter: drop-shadow(0 4px 10px rgba(59, 130, 246, 0.5));
}

/* Chart Tooltip */
.chart-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.85);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  pointer-events: none;
  z-index: 100;
  white-space: nowrap;
  transform: translateX(-50%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chart-tooltip::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid rgba(0, 0, 0, 0.85);
}

/* Period Button Group */
.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.7rem;
  border-radius: 6px;
}

.btn-group > .btn:not(:last-child) {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.btn-group > .btn:not(:first-child) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  margin-left: -1px;
}

/* ===== Forecast Section ===== */
.forecast-container {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(248, 250, 252, 0) 100%);
  border: 1px solid rgba(0, 0, 0, 0.03);
  border-radius: 16px;
}

.forecast-item {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 16px;
  background: white;
  border: 1px solid transparent;
}

.forecast-item:hover {
  background: white;
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.05);
}

.forecast-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  font-size: 1.75rem;
  transition: transform 0.3s ease;
}

.forecast-item:hover .forecast-icon {
  transform: scale(1.1) rotate(5deg);
}

.forecast-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
}

.trend-up { background: rgba(16, 185, 129, 0.1); color: #059669; }
.trend-stable { background: rgba(59, 130, 246, 0.1); color: #2563eb; }
.trend-down { background: rgba(239, 68, 68, 0.1); color: #dc2626; }

/* ===== AI Insights ===== */
.insights-container {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}

.insight-item {
  padding: 1.25rem;
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
}

.insight-item:hover {
  border-color: var(--color-primary);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.1);
  transform: translateX(5px);
}

.insight-icon {
  width: 42px;
  height: 42px;
  background: var(--gradient-primary);
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

/* ===== Carousel ===== */
.reorder-carousel {
  position: relative;
  padding: 0.5rem 0;
}

.carousel-track {
  display: flex;
  gap: 1.5rem;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding: 1rem 0.5rem;
  scrollbar-width: none; /* Firefox */
}

.carousel-track::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

/* ===== Reorder Product Cards ===== */
.reorder-card {
  min-width: 280px;
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.reorder-card:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
  z-index: 2;
}

.product-image-wrapper {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.reorder-card:hover .product-image {
  transform: scale(1.15);
}

.product-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(239, 68, 68, 0.9);
  backdrop-filter: blur(4px);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.product-details {
  padding: 1.25rem;
}

.product-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-text-dark);
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.product-supplier {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

/* ===== Filter Chips ===== */
.filter-chip {
  padding: 0.6rem 1.2rem;
  border-radius: 50px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: white;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-2px);
  background: rgba(59, 130, 246, 0.05);
}

.filter-chip.active {
  background: var(--gradient-primary);
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

/* ===== Products Grid ===== */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.product-grid-card {
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.product-grid-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
}

.product-grid-image {
  position: relative;
  width: 100%;
  height: 240px;
  overflow: hidden;
}

.product-grid-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.product-grid-card:hover .product-grid-image img {
  transform: scale(1.15);
}

.product-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
}

.product-grid-card:hover .product-overlay {
  opacity: 1;
}

.product-discount-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(220, 38, 38, 0.9);
  backdrop-filter: blur(4px);
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

/* ===== Quick View Modal ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 2rem;
  animation: fadeIn 0.3s ease-out;
}

.quick-view-modal {
  background: white;
  border-radius: 24px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 2.5rem;
  position: relative;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: modalSlideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalSlideUp {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-close-btn {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  width: 40px;
  height: 40px;
  background: #f3f4f6;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
  color: var(--color-text-muted);
}

.modal-close-btn:hover {
  background: #fee2e2;
  color: #ef4444;
  transform: rotate(90deg);
}

/* ===== Toast Notification ===== */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  z-index: 1100;
  border: 1px solid rgba(0, 0, 0, 0.05);
  animation: toastSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateX(100px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* ===== Sales Summary Enhanced Styles ===== */
.daily-mini-chart {
  background: rgba(248, 250, 252, 0.5);
  border-radius: 12px;
  padding: 0.75rem;
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.daily-bar {
  flex: 1;
  border-radius: 4px 4px 0 0;
  min-width: 20px;
  max-width: 40px;
  transition: all 0.3s ease;
  opacity: 0.8;
}

.daily-bar:hover {
  opacity: 1;
  transform: scaleY(1.05);
  transform-origin: bottom;
}

.summary-item {
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== Forecast Enhanced Styles ===== */
.forecast-container {
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(248, 250, 252, 0) 100%);
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.forecast-total {
  animation: pulseGlow 2s ease-in-out infinite;
}

@keyframes pulseGlow {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.1);
  }
  50% {
    box-shadow: 0 0 20px 5px rgba(59, 130, 246, 0.15);
  }
}

.forecast-item {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.03);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.forecast-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  border-color: var(--color-primary);
}

.forecast-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  transition: transform 0.3s ease;
}

.forecast-item:hover .forecast-icon {
  transform: scale(1.1);
}

.forecast-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}

.forecast-badge.bg-success-soft {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.forecast-badge.bg-danger-soft {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.forecast-badge.bg-warning-soft {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

/* Monthly breakdown styles */
.monthly-breakdown-item {
  transition: all 0.2s ease;
}

.monthly-breakdown-item:hover {
  transform: scale(1.02);
}

/* ===== Loading States ===== */
.spinner-border {
  --bs-spinner-width: 2rem;
  --bs-spinner-height: 2rem;
  --bs-spinner-border-width: 0.2em;
}

.spinner-border-sm {
  --bs-spinner-width: 1rem;
  --bs-spinner-height: 1rem;
}

/* Skeleton loading animation */
.skeleton-loader {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* ===== Responsive Design ===== */
@media (max-width: 768px) {
  .shop-dashboard-tab {
    padding: 1rem;
  }

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1rem;
  }

  .dashboard-hero {
    padding: 1.5rem;
  }

  .hero-title {
    font-size: 1.5rem;
  }

  .modal-overlay {
    padding: 1rem;
  }

  .quick-view-modal {
    padding: 1.5rem;
  }
  
  .metric-value {
    font-size: 1.5rem;
  }
}
</style>

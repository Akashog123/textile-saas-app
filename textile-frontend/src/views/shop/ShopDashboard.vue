<template>
  <div class="shop-dashboard-tab">
    <!-- Hero Header Section -->
    <div class="dashboard-hero mb-4 animate-fade-in">
      <div class="d-flex flex-column flex-md-row align-items-md-center justify-content-between gap-3">
        <div class="d-flex align-items-center gap-3">
          <div class="hero-icon-box bg-white p-3 rounded-circle shadow-sm d-none d-md-block">
             <i class="bi bi-shop-window fs-3 text-primary"></i>
          </div>
          <div>
            <h3 class="hero-title mb-1">Shop Manager</h3>
            <p class="hero-subtitle mb-0 text-muted">
              Welcome back! Here's your business overview.
            </p>
          </div>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-gradient btn-sm d-flex align-items-center shadow-sm" @click="openSalesUploadModal">
            <i class="bi bi-cloud-arrow-up me-2"></i>
            Upload Sales Data
          </button>
          <button class="btn btn-gradient btn-sm d-flex align-items-center border shadow-sm" @click="openUploadLogsModal" title="View recent upload activity">
            <i class="bi bi-clock-history me-2"></i>
            History
          </button>
        </div>
      </div>
    </div>

    <!-- Top metric cards with animations -->
    <div class="row g-4 mb-4">
      <div
        class="col-12 col-sm-6 col-lg-3"
        v-for="(metric, index) in metrics"
        :key="index"
      >
        <div
          class="metric-card p-4 h-100 d-flex flex-column justify-content-between"
          :style="{ animationDelay: (index * 0.1) + 's' }"
        >
          <div class="d-flex align-items-start justify-content-between mb-3">
            <div>
              <small class="metric-label text-uppercase text-muted fw-bold" style="font-size: 0.7rem; letter-spacing: 0.5px;">{{ metric.label }}</small>
              <div class="metric-value mt-1">{{ metric.value }}</div>
            </div>
            <div class="metric-icon rounded-3 d-flex align-items-center justify-content-center" :class="metric.iconClass" style="width: 48px; height: 48px;">
              <i :class="metric.icon" class="fs-4"></i>
            </div>
          </div>
          <div class="d-flex align-items-center">
            <div class="metric-change badge rounded-pill fw-normal" :class="metric.changeClass === 'positive' ? 'bg-success-soft text-success' : 'bg-danger-soft text-danger'">
              <i :class="metric.changeIcon" class="me-1"></i>
              {{ metric.change }}
            </div>
            <small class="text-muted ms-2" style="font-size: 0.75rem;">vs last period</small>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="row g-4">
      <!-- Sales Summary -->
      <div class="col-lg-6 d-flex">
        <div class="card modern-card w-100 border-0 shadow-sm">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h6 class="card-title mb-0 fw-bold d-flex align-items-center">
                <span class="bg-primary-soft text-primary rounded p-1 me-2"><i class="bi bi-graph-up"></i></span>
                Sales Summary
                <small class="bg-primary-soft ms-2 fw-normal" style="font-size: 0.8rem;">{{ salesDateRange }}</small>
              </h6>
              <span 
                class="badge px-3 py-2 rounded-pill" 
                :class="salesComparison.trend === 'up' ? 'bg-success-soft text-success' : salesComparison.trend === 'down' ? 'bg-danger-soft text-danger' : 'bg-secondary-soft text-secondary'"
                v-if="salesGrowth"
              >
                <i :class="salesComparison.trend === 'up' ? 'bi bi-arrow-up me-1' : salesComparison.trend === 'down' ? 'bi bi-arrow-down me-1' : 'bi bi-dash me-1'"></i>
                {{ salesGrowth }}
              </span>
            </div>
            
            <!-- Loading State -->
            <div v-if="salesSummaryLoading" class="flex-grow-1 d-flex align-items-center justify-content-center py-5">
              <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status"></div>
                <p class="text-muted mb-0 small">Loading sales data...</p>
              </div>
            </div>
            
            <!-- Empty State - No Sales Data -->
            <div v-else-if="!hasSalesData" class="flex-grow-1 d-flex align-items-center justify-content-center py-4">
              <div class="text-center">
                <div class="empty-state-icon mb-3">
                  <i class="bi bi-bar-chart-line text-muted" style="font-size: 3rem; opacity: 0.4;"></i>
                </div>
                <h6 class="text-muted fw-semibold mb-2">No Sales Data Yet</h6>
                <p class="text-muted small mb-3" style="max-width: 250px;">
                  Upload your sales data to see revenue insights, trends, and category performance.
                </p>
              </div>
            </div>
            
            <!-- Data State -->
            <div v-else class="flex-grow-1 d-flex flex-column">
              <div class="summary-item mb-4 p-3 bg-light rounded-3">
                <div class="d-flex align-items-start gap-3">
                  <div class="check-icon-circle flex-shrink-0" :class="salesComparison.trend === 'down' ? 'bg-danger-soft text-danger' : 'bg-success-soft text-success'">
                    <i :class="salesComparison.trend === 'up' ? 'bi bi-graph-up-arrow' : salesComparison.trend === 'down' ? 'bi bi-graph-down-arrow' : 'bi bi-dash-lg'"></i>
                  </div>
                  <div>
                    <p class="mb-1 fw-medium text-dark">
                      {{ salesComparison.message || 'Upload sales data to see weekly insights' }}
                    </p>
                    <small class="text-muted" v-if="topCategory">
                      <strong class="text-dark">{{ topCategory.name }}</strong> is the top seller ({{ topCategory.percentage }}% of sales)
                    </small>
                    <small class="text-muted" v-else>
                      Upload data to see category insights
                    </small>
                  </div>
                </div>
              </div>

              <div class="row g-3 mb-4">
                <div class="col-6">
                  <div class="stat-box h-100 p-3 border rounded-3 bg-white text-center">
                    <small class="text-muted d-block mb-1 text-uppercase" style="font-size: 0.7rem; letter-spacing: 0.5px;">Total Quantity Sold</small>
                    <strong class="fs-4 text-dark">{{ salesSummaryMetrics.totalQuantity.toLocaleString() }}</strong>
                  </div>
                </div>
                <div class="col-6">
                  <div class="stat-box h-100 p-3 border rounded-3 bg-white text-center">
                    <small class="text-muted d-block mb-1 text-uppercase" style="font-size: 0.7rem; letter-spacing: 0.5px;">Total Revenue</small>
                    <strong class="fs-4 text-dark">{{ salesSummaryMetrics.totalRevenue }}</strong>
                  </div>
                </div>
              </div>
              
              <!-- Daily Breakdown Mini Chart -->
              <div v-if="salesSummaryData?.daily_breakdown?.length" class="daily-mini-chart mt-auto">
                <small class="text-muted d-block mb-2 fw-bold" style="font-size: 0.75rem;">Daily Breakdown</small>
                <div style="height: 90px;">
                  <DailyBarChart
                    :daily-data="salesSummaryData.daily_breakdown"
                    :height="90"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sales Growth Trend -->
      <div class="col-lg-6 d-flex">
        <div class="card modern-card w-100 border-0 shadow-sm">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h6 class="card-title mb-0 fw-bold d-flex align-items-center">
                <span class="bg-info-soft text-info rounded p-1 me-2"><i class="bi bi-activity"></i></span>
                Sales Growth Trend
              </h6>
              <div class="d-flex align-items-center gap-2">
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
                <button 
                  class="btn btn-sm btn-primary rounded-circle shadow-sm d-flex align-items-center justify-content-center" 
                  style="width: 32px; height: 32px;"
                  @click="shopBot?.toggleChat()"
                  title="Ask AI Analyst"
                >
                  <i class="bi bi-chat-dots-fill" style="font-size: 0.8rem;"></i>
                </button>
              </div>
            </div>
            
            <!-- Growth Badge -->
            <div v-if="salesTrendData?.growth_percent !== undefined" class="mb-3 d-flex align-items-center">
              <span 
                class="badge px-2 py-1 rounded-pill me-2"
                :class="salesTrendData.trend === 'up' ? 'bg-success-soft text-success' : salesTrendData.trend === 'down' ? 'bg-danger-soft text-danger' : 'bg-secondary-soft text-secondary'"
              >
                <i :class="salesTrendData.trend === 'up' ? 'bi bi-arrow-up' : salesTrendData.trend === 'down' ? 'bi bi-arrow-down' : 'bi bi-dash'" class="me-1"></i>
                {{ salesTrendData.growth_percent_formatted }}
              </span>
              <small class="text-muted">{{ salesTrendData.total_revenue_formatted }} total revenue</small>
            </div>
            
            <!-- Loading State -->
            <div v-if="chartLoading" class="flex-grow-1 d-flex align-items-center justify-content-center">
              <div class="text-center">
                <div class="spinner-border spinner-border-sm text-primary mb-2" role="status"></div>
                <p class="text-muted small mb-0">Loading chart...</p>
              </div>
            </div>
            
            <!-- No Data State -->
            <div v-else-if="!salesTrendData || salesTrendData.status === 'no_data'" class="flex-grow-1 d-flex align-items-center justify-content-center bg-light rounded-3">
              <div class="text-center p-4">
                <div class="mb-3 text-muted opacity-50">
                  <i class="bi bi-graph-up" style="font-size: 2.5rem;"></i>
                </div>
                <h6 class="text-muted fw-semibold mb-2">No Trend Data</h6>
                <p class="text-muted small mb-3">
                  Upload sales data to visualize your growth trends over time.
                </p>
              </div>
            </div>
            
            <!-- Chart.js Chart -->
            <div v-else class="flex-grow-1 d-flex flex-column justify-content-center position-relative" @click="viewDetailedChart">
              <div class="chart-wrapper w-100" style="height: 220px; cursor: pointer;">
                <SalesLineChart
                  :labels="chartLabels"
                  :data-points="salesTrendData.data_points || []"
                  :trend="salesTrendData.trend || 'flat'"
                  :period="chartPeriod"
                  :height="220"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Demand Forecast -->
      <div class="col-lg-6 d-flex">
        <div class="card modern-card w-100 border-0 shadow-sm">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h6 class="card-title mb-0 fw-bold d-flex align-items-center">
                <span class="text-warning rounded p-1 me-2"><i class="bi bi-graph-up-arrow"></i></span>
                Next Quarter Demand Forecast
              </h6>
              <span v-if="quarterlyForecastData?.summary?.confidence_level && !quarterlyForecastLoading && !quarterlyForecastError && quarterlyForecastData?.status !== 'no_data' && quarterlyForecastData?.status !== 'insufficient_data'" class="badge" :class="{
                'bg-success-soft text-success': quarterlyForecastData.summary.confidence_level === 'High',
                'bg-warning-soft text-warning': quarterlyForecastData.summary.confidence_level === 'Medium',
                'bg-danger-soft text-danger': quarterlyForecastData.summary.confidence_level === 'Low' || quarterlyForecastData.summary.confidence_level === 'Very Low'
              }" :title="getConfidenceTooltip(quarterlyForecastData.summary)">
                <i v-if="quarterlyForecastData.summary.confidence_level === 'Very Low'" class="bi bi-exclamation-triangle me-1"></i>
                {{ quarterlyForecastData.summary.confidence_level }} Confidence
              </span>
            </div>
            
            <!-- Loading State -->
            <div v-if="quarterlyForecastLoading" class="flex-grow-1 d-flex align-items-center justify-content-center py-5">
              <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status"></div>
                <p class="text-muted mb-0 small">Generating forecast...</p>
              </div>
            </div>
            
            <!-- Error State -->
            <div v-else-if="quarterlyForecastError" class="flex-grow-1 d-flex align-items-center justify-content-center bg-light rounded-3 p-4">
              <div class="text-center">
                <i class="bi bi-exclamation-triangle fs-1 text-warning mb-2"></i>
                <p class="text-muted mb-2">{{ quarterlyForecastError }}</p>
                <button class="btn btn-outline-primary btn-sm" @click="fetchQuarterlyForecast">
                  <i class="bi bi-arrow-clockwise me-1"></i>Retry
                </button>
              </div>
            </div>
            
            <!-- No Data State -->
            <div v-else-if="!quarterlyForecastData || quarterlyForecastData.status === 'no_data' || quarterlyForecastData.status === 'insufficient_data'" class="flex-grow-1 d-flex align-items-center justify-content-center bg-light rounded-3 p-4">
              <div class="text-center">
                <i class="bi bi-bar-chart-line fs-1 text-muted mb-2"></i>
                <p class="fw-medium mb-1">{{ quarterlyForecastData?.status === 'insufficient_data' ? 'Insufficient Sales Data' : 'No Forecast Data Available' }}</p>
                <small class="text-muted d-block mb-3">
                  {{ quarterlyForecastData?.insights?.[0]?.message || 'Upload at least 7 days of sales data to generate forecasts.' }}
                </small>
              </div>
            </div>
            
            <!-- Data State -->
            <div v-else class="flex-grow-1 d-flex flex-column">
              <!-- Total Predicted Revenue -->
              <div v-if="quarterlyForecastData?.summary" class="mb-4 p-3 bg-primary-soft rounded-3 text-center">
                <small class="text-primary d-block fw-bold text-uppercase" style="font-size: 0.7rem; letter-spacing: 0.5px;">Predicted Quarter Revenue</small>
                <strong class="fs-3 text-primary">{{ quarterlyForecastData.summary.total_predicted_revenue_formatted || '₹0' }}</strong>
                <div v-if="quarterlyForecastData.summary.total_predicted_quantity" class="mt-1">
                  <small class="text-muted">Est. {{ quarterlyForecastData.summary.total_predicted_quantity.toLocaleString() }} units</small>
                </div>
              </div>
              
              <!-- Category Forecasts -->
              <div v-if="actionableForecasts.length > 0" class="mb-4">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <small class="text-muted fw-bold">Top Categories</small>
                  <button 
                    v-if="quarterlyForecastData?.category_forecast?.length > 3" 
                    class="btn btn-link btn-sm p-0 text-primary text-decoration-none"
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
                      class="forecast-item h-100 d-flex flex-column align-items-center justify-content-center text-center p-2 border rounded-3"
                      :class="{ 'border-primary bg-primary-soft-hover': forecast.is_actionable }"
                      @click="viewForecastDetails(forecast)"
                    >
                      <div class="forecast-icon mb-2 rounded-circle d-flex align-items-center justify-content-center" :class="getTrendIconBg(forecast.trend)" style="width: 40px; height: 40px;">
                        <i :class="getTrendIcon(forecast.trend)" :style="{ color: getTrendColor(forecast.trend) }" class="fs-6"></i>
                      </div>
                      <small class="d-block fw-bold mb-1 text-dark text-truncate w-100" style="font-size: 0.75rem;">{{ forecast.name }}</small>
                      <div class="forecast-badge small px-2 py-0" :class="getTrendBadgeClass(forecast.trend)">
                        <i :class="forecast.trend === 'up' ? 'bi bi-arrow-up' : forecast.trend === 'down' ? 'bi bi-arrow-down' : 'bi bi-dash'" class="me-1"></i>
                        {{ formatTrendPercent(forecast) }}
                      </div>
                      <small class="text-muted mt-1" style="font-size: 0.65rem;">{{ forecast.predicted }}</small>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Monthly Breakdown -->
              <div v-if="quarterlyForecastData?.monthly_forecast?.length" class="mt-auto">
                <small class="text-muted d-block mb-2 fw-bold">Monthly Breakdown</small>
                <div class="d-flex gap-2">
                  <div 
                    v-for="(month, idx) in quarterlyForecastData.monthly_forecast" 
                    :key="idx"
                    class="flex-fill p-2 rounded text-center monthly-breakdown-item border bg-light"
                  >
                    <small class="text-muted d-block text-uppercase" style="font-size: 0.65rem;">{{ month.month?.split(' ')[0] }}</small>
                    <strong class="small text-dark">{{ month.predicted_revenue_formatted }}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Insights -->
      <div class="col-lg-6 d-flex">
        <div class="card modern-card ai-insights-card w-100 border-0 shadow-sm">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex justify-content-between align-items-center mb-4">
              <h6 class="card-title mb-0 fw-bold d-flex align-items-center">
                <span class="bg-primary-soft text-primary rounded p-1 me-2"><i class="bi bi-stars"></i></span>
                AI-Powered Insights
              </h6>
              <button v-if="aiInsights.length > 0" class="btn btn-gradient btn-sm rounded" @click="generateInsightsPDF" :disabled="generatingPDF">
                <span v-if="generatingPDF"><span class="spinner-border spinner-border-sm me-1"></span>Generating...</span>
                <span v-else><i class="bi bi-download me-1"></i>Export Report</span>
              </button>
            </div>
            <!-- Loading State -->
            <div v-if="loading" class="flex-grow-1 d-flex align-items-center justify-content-center py-5">
              <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status"></div>
                <p class="text-muted mb-0 small">Analyzing trends...</p>
              </div>
            </div>

            <div v-else class="insights-container flex-grow-1 custom-scrollbar">
              <!-- Empty State -->
              <div v-if="aiInsights.length === 0" class="h-100 d-flex align-items-center justify-content-center text-center">
                 <div class="p-4">
                    <div class="mb-3 text-muted opacity-50">
                       <i class="bi bi-stars" style="font-size: 3rem;"></i>
                    </div>
                    <h6 class="text-muted fw-semibold mb-2">No Insights Yet</h6>
                    <p class="text-muted small mb-3">
                       Upload inventory and sales data to unlock AI-powered insights about trends, pricing, and inventory.
                    </p>
                 </div>
              </div>

              <!-- Insights List -->
              <div
                v-else
                class="insight-item mb-3 p-3 rounded-3 mx-2"
                :class="[
                  insight.type === 'success' ? 'insight-success' : 
                  insight.type === 'warning' ? 'insight-warning' : 'insight-info'
                ]"
                v-for="(insight, index) in aiInsights"
                :key="index"
              >
                <div class="d-flex align-items-start gap-3">
                  <div 
                    class="insight-icon flex-shrink-0 rounded-circle d-flex align-items-center justify-content-center" 
                    :class="[
                      insight.type === 'success' ? 'icon-success' : 
                      insight.type === 'warning' ? 'icon-warning' : 'icon-primary'
                    ]"
                    style="width: 40px; height: 40px;"
                  >
                    <i :class="insight.icon"></i>
                  </div>
                  <div class="flex-grow-1 min-w-0">
                    <div class="d-flex align-items-center gap-2 mb-1">
                      <strong class="text-dark text-truncate" style="font-size: 0.95rem;">{{ insight.title }}</strong>
                      <span 
                        v-if="insight.category" 
                        class="badge rounded-pill flex-shrink-0"
                        :class="[
                          insight.type === 'success' ? 'bg-success-soft text-success' : 
                          insight.type === 'warning' ? 'bg-warning-soft text-warning' : 'bg-primary-soft text-primary'
                        ]"
                        style="font-size: 0.65rem; font-weight: 500;"
                      >
                        {{ insight.category }}
                      </span>
                    </div>
                    <p class="mb-0 small text-muted lh-sm text-line-clamp-2">
                      {{ insight.description }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Smart Reorder Suggestions -->
      <div class="col-12">
        <div class="card modern-card border-0 shadow-sm">
          <div class="card-body p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
              <h6 class="card-title mb-0 fw-bold d-flex align-items-center">
                <span class="bg-success-soft text-success rounded p-1 me-2"><i class="bi bi-cart-check"></i></span>
                Smart Reorder Suggestions
              </h6>
            </div>
            
            <!-- Loading State -->
            <div v-if="loading" class="text-center py-5">
              <div class="spinner-border text-primary mb-3" role="status"></div>
              <p class="text-muted mb-0">Checking inventory levels...</p>
            </div>
            
            <!-- Grouped reorder suggestions -->
            <div v-else-if="Object.keys(groupedReorderSuggestions).length === 0" class="text-center py-5 text-muted bg-light rounded-3">
              <div class="empty-state-icon mb-3">
                <i class="bi bi-inbox fs-1"></i>
              </div>
              <p class="mb-0">No reorder suggestions at this time</p>
            </div>
            
            <div v-else class="distributor-groups">
              <div 
                v-for="(products, distributorName) in groupedReorderSuggestions" 
                :key="distributorName"
                class="distributor-group mb-4 border rounded-3 overflow-hidden"
              >
                <div class="distributor-header p-3 bg-light border-bottom">
                  <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                    <div class="d-flex align-items-center gap-3">
                      <div class="distributor-icon bg-white p-2 rounded shadow-sm text-primary">
                        <i class="bi bi-building"></i>
                      </div>
                      <div>
                        <h6 class="mb-0 fw-bold text-dark">{{ distributorName }}</h6>
                        <small class="text-muted">{{ products.length }} item(s) to reorder</small>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="reorder-carousel p-3 bg-white">
                  <div class="carousel-track d-flex gap-3" style="overflow-x: auto; padding-bottom: 10px;">
                    <div
                      class="reorder-card border rounded-3 flex-shrink-0"
                      style="width: 280px;"
                      v-for="(product, index) in products"
                      :key="index"
                      @click="viewProduct(product)"
                    >
                      <div class="product-image-wrapper position-relative" style="height: 180px;">
                        <img
                          :src="product.image"
                          :alt="product.name"
                          class="product-image w-100 h-100 object-fit-cover"
                        />
                        <div class="product-badge position-absolute top-0 end-0 m-2 badge bg-danger rounded-pill shadow-sm">
                          <i class="bi bi-lightning-fill me-1"></i>
                          Low Stock
                        </div>
                      </div>
                      <div class="product-details p-3">
                        <h6 class="product-name mb-1 text-truncate" :title="product.name">{{ product.name }}</h6>
                        <p class="product-supplier mb-2 text-muted small">
                          <i class="bi bi-tag me-1"></i>
                          {{ product.category }}
                        </p>
                        <div class="d-flex justify-content-between mb-2 small">
                          <span class="text-muted">Stock: {{ product.currentStock }}</span>
                          <span class="text-danger fw-bold">Min: {{ product.minimumStock }}</span>
                        </div>
                        <div class="d-flex align-items-center justify-content-between mt-3 pt-3 border-top">
                          <span class="product-quantity text-success fw-bold small"
                            >Reorder: {{ product.quantity }}</span
                          >
                          <span class="product-price fw-bold">{{ product.price }}</span>
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

    <!-- Upload Logs Modal -->
    <transition name="modal-fade">
      <div v-if="showUploadLogsModal" class="modal-overlay" @click="closeUploadLogsModal">
        <div class="quick-view-modal" @click.stop style="max-width: 700px;">
          <button class="modal-close-btn" @click="closeUploadLogsModal">
            <i class="bi bi-x-lg"></i>
          </button>
          <div class="text-center mb-4">
            <div class="insight-icon-large mb-3 text-primary">
              <i class="bi bi-clock-history fs-1"></i>
            </div>
            <h4 class="mb-2">Recent Upload Activity</h4>
            <p class="text-muted">Last 6 sales data uploads with SLA insights</p>
          </div>
          <div v-if="uploadLogsLoading" class="text-center py-4">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted mb-0">Fetching logs…</p>
          </div>
          <div v-else-if="uploadLogsError" class="alert alert-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>{{ uploadLogsError }}
          </div>
          <div v-else-if="uploadLogs.length === 0" class="text-center py-4 text-muted">
            <i class="bi bi-inbox fs-1 d-block mb-2"></i>
            <p class="mb-0">No uploads recorded yet.</p>
            <small>Upload sales data to see activity here</small>
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
                    <span :class="['badge', log.status === 'completed' ? 'bg-success-soft text-success' : log.status === 'failed' ? 'bg-danger-soft text-danger' : 'bg-warning-soft text-warning']">
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
    </transition>

    <!-- Sales Upload Modal -->
    <transition name="modal-fade">
      <div v-if="showSalesUploadModal" class="modal-overlay" @click="closeSalesUploadModal">
        <div class="quick-view-modal" @click.stop style="max-width: 600px;">
          <button class="modal-close-btn" @click="closeSalesUploadModal">
            <i class="bi bi-x-lg"></i>
          </button>
          <div class="text-center mb-4">
            <div class="insight-icon-large mb-3 text-primary">
              <i class="bi bi-cloud-arrow-up fs-1"></i>
            </div>
            <h4 class="mb-2">Upload Sales Data</h4>
            <p class="text-muted">Update your sales records to get fresh insights</p>
          </div>

          <div class="modal-body">
            <!-- Step 1 -->
            <div class="step-section mb-4">
                <h6><span class="badge rounded me-2">1</span>Prepare Data</h6>
                <p class="text-muted small mb-2">Download the template to ensure your data is formatted correctly.</p>
                <button class="btn btn-sm btn-gradient" @click="handleDownloadSalesTemplate">
                    <i class="bi bi-file-earmark-arrow-down me-1"></i> Download CSV Template
                </button>
            </div>
            <hr class="text-muted opacity-25">

            <!-- Step 2 -->
            <div class="step-section mb-4">
                <h6><span class="badge rounded me-2">2</span>Upload Sales Data</h6>
                <p class="text-muted small mb-2">Upload your filled CSV or Excel file. Supported formats: .csv, .xlsx, .xls</p>
                
                <div class="d-flex align-items-center gap-3">
                    <input type="file" class="form-control form-control-sm" ref="salesFileInput" accept=".csv,.xlsx,.xls" @change="onSalesFileSelect">
                    <button class="btn btn-sm btn-gradient" @click="uploadSalesFile" :disabled="!selectedSalesFile || salesUploading">
                        <span v-if="salesUploading" class="spinner-border spinner-border-sm me-1"></span>
                        Upload
                    </button>
                </div>
                <div v-if="salesUploadStatus" class="mt-2 small" :class="{
                    'text-success': salesUploadStatus.type === 'success',
                    'text-danger': salesUploadStatus.type === 'error',
                    'text-warning': salesUploadStatus.type === 'warning',
                    'text-info': salesUploadStatus.type === 'info'
                }">
                    <i :class="{
                        'bi bi-check-circle': salesUploadStatus.type === 'success',
                        'bi bi-exclamation-circle': salesUploadStatus.type === 'error',
                        'bi bi-exclamation-triangle': salesUploadStatus.type === 'warning',
                        'bi bi-info-circle': salesUploadStatus.type === 'info'
                    }"></i>
                    {{ salesUploadStatus.message }}
                </div>
            </div>
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

    <!-- Shop Owner Bot (Hidden Trigger) -->
    <ShopOwnerBot ref="shopBot" :hide-trigger="true" :has-data="hasSalesData" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { 
  getShopDashboard, 
  uploadSalesData as uploadSalesDataAPI, 
  getDemandForecast, 
  getSalesUploadLogs, 
  generateSalesReportPdf,
  getSalesSummary,
  getQuarterlyForecast,
  getSalesGrowthTrend,
  downloadSalesTemplate
} from '@/api/apiShop';
import ShopOwnerBot from '@/components/ShopOwnerBot.vue';
import SalesLineChart from '@/components/charts/SalesLineChart.vue';
import DailyBarChart from '@/components/charts/DailyBarChart.vue';

// Loading and error states
const loading = ref(false);
const error = ref('');

// Request deduplication flags to prevent multiple simultaneous requests
const requestInProgress = ref({
  dashboard: false,
  salesSummary: false,
  quarterlyForecast: false,
  salesTrend: false,
  uploadLogs: false
});


// Dashboard data from backend
const dashboardData = ref(null);

// Sales Summary (Last 7 Days) data
const salesSummaryData = ref(null);
const salesSummaryLoading = ref(false);
const salesSummaryError = ref('');

// Quarterly Forecast data
const quarterlyForecastData = ref(null);
const quarterlyForecastLoading = ref(false);
const quarterlyForecastError = ref('');

// Sales Growth Trend chart data
const salesTrendData = ref(null);
const chartLoading = ref(false);
const chartPeriod = ref('weekly');

// Demand forecast data (legacy)
const demandForecast = ref([]);
const forecastLoading = ref(false);
const forecastError = ref('');

// Upload logs for audit transparency
const uploadLogs = ref([]);
const uploadLogsLoading = ref(false);
const uploadLogsError = ref('');
const showUploadLogsModal = ref(false);

// Sales Upload Modal State
const showSalesUploadModal = ref(false);
const salesFileInput = ref(null);
const selectedSalesFile = ref(null);
const salesUploading = ref(false);
const salesUploadStatus = ref(null);

// Shop Bot Ref
const shopBot = ref(null);

// PDF generation state
const generatingPDF = ref(false);

// Check if shop has sales data
const hasSalesData = computed(() => {
  // Check if we actually have meaningful sales data (not just zeros)
  const hasSummaryData = salesSummaryData.value?.status === 'success' && 
    (salesSummaryData.value?.metrics?.total_quantity > 0 || salesSummaryData.value?.metrics?.total_revenue > 0);
  const hasDashboardData = dashboardData.value && 
    dashboardData.value.weekly_sales && 
    dashboardData.value.weekly_sales !== '₹0' &&
    dashboardData.value.weekly_sales !== '₹0.00';
  return !!(hasSummaryData || hasDashboardData);
});

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

// Computed properties for sales summary display
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

const dailyMaxRevenue = computed(() => {
  if (!salesSummaryData.value?.daily_breakdown?.length) return 1;
  return Math.max(...salesSummaryData.value.daily_breakdown.map(d => d.revenue), 1);
});

const formatCompactNumber = (value) => {
  if (value === 0) return '0';
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
  return `${value}`;
};

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

// Shop ID - get from logged-in user (consistent with multishop mechanism)
const shopId = computed(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  // Priority: primary_shop_id > shop_id > first shop from shops array
  return user.primary_shop_id || user.shop_id || (user.shops && user.shops[0]?.id) || null;
});

// Metrics Data - dynamically populated from backend
const metrics = ref([
  {
    label: 'Average Order Value',
    value: '₹0',
    change: '+0%',
    changeClass: 'positive',
    changeIcon: 'bi bi-arrow-up',
    icon: 'bi bi-receipt',
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
  if (!shopId.value || requestInProgress.value.uploadLogs) return;
  
  requestInProgress.value.uploadLogs = true;
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
    requestInProgress.value.uploadLogs = false;
  }
};

/**
 * Open Upload Logs Modal
 */
const openUploadLogsModal = async () => {
  showUploadLogsModal.value = true;
  if (uploadLogs.value.length === 0) {
    await fetchUploadLogs();
  }
};

/**
 * Close Upload Logs Modal
 */
const closeUploadLogsModal = () => {
  showUploadLogsModal.value = false;
};

/**
 * Fetch dashboard data from backend
 * Uses deduplication to prevent multiple simultaneous requests
 */
const fetchDashboard = async () => {
  if (!shopId.value) {
    error.value = 'Shop ID not found. Please log in again.';
    return;
  }
  
  // Prevent duplicate requests
  if (requestInProgress.value.dashboard) {
    console.log('[Dashboard] Request already in progress, skipping');
    return;
  }

  requestInProgress.value.dashboard = true;
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
      // Handle info messages (non-alarming, informational)
      if (response.data?.info) {
        toastMessage.value = response.data.info;
        toastIcon.value = 'bi bi-info-circle';
        showToast.value = true;
        setTimeout(() => (showToast.value = false), 6000);
      }
      // Handle warning messages (potential issues)
      else if (response.data?.warning) {
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
    requestInProgress.value.dashboard = false;
  }
};

/**
 * Update metrics from dashboard data
 */
const updateMetricsFromData = (data) => {
  // metrics[0] = Average Order Value (from sales summary if available)
  if (salesSummaryData.value?.metrics?.average_order_value_formatted) {
    metrics.value[0].value = salesSummaryData.value.metrics.average_order_value_formatted;
  } else if (data.weekly_sales && data.total_orders) {
    // Fallback: calculate from dashboard data
    const weeklySalesNum = parseFloat(data.weekly_sales.replace(/[₹,]/g, '')) || 0;
    const avgOrderVal = data.total_orders > 0 ? weeklySalesNum / data.total_orders : 0;
    metrics.value[0].value = `₹${avgOrderVal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
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
 * Maps insight categories to appropriate icons and styles
 */
const getInsightIcon = (insight) => {
  // If backend sends icon directly, use it
  if (insight.icon) {
    if (insight.icon.startsWith('bi ')) return insight.icon;
    if (insight.icon.startsWith('bi-')) return `bi ${insight.icon}`;
    return insight.icon;
  }
  
  // Map categories to icons
  const iconMap = {
    'Performance': 'bi bi-speedometer2',
    'Timing': 'bi bi-calendar-check',
    'Pricing': 'bi bi-cash-stack',
    'Strategy': 'bi bi-lightbulb',
    'Trend': 'bi bi-graph-up-arrow',
    'Product': 'bi bi-star',
    'Inventory': 'bi bi-box-seam',
    'Sales': 'bi bi-graph-up',
    'Revenue': 'bi bi-currency-rupee',
    'Growth': 'bi bi-arrow-up-right-circle',
    'Demand': 'bi bi-activity',
    'Restock': 'bi bi-box-arrow-in-down',
    'Customer': 'bi bi-people',
    'Rating': 'bi bi-star-half'
  };
  
  return iconMap[insight.category] || 'bi bi-lightbulb';
};

const getInsightTypeClass = (insight) => {
  const typeMap = {
    'success': 'insight-success',
    'warning': 'insight-warning',
    'info': 'insight-info'
  };
  return typeMap[insight.type] || 'insight-info';
};

const updateInsightsFromData = (data) => {
  if (data.ai_insights && data.ai_insights.length > 0) {
    aiInsights.value = data.ai_insights.map(insight => {
      // Map backend 'impact' field to frontend 'type' field
      let insightType = insight.type || 'info';
      if (!insight.type && insight.impact) {
        const impactMap = {
          'Positive': 'success',
          'Action': 'warning',
          'Negative': 'warning',
          'Critical': 'warning'
        };
        insightType = impactMap[insight.impact] || 'info';
      }
      
      return {
        icon: getInsightIcon(insight),
        title: insight.title,
        description: limitSentences(insight.message || insight.description || '', 4),
        type: insightType,
        category: insight.category || 'General'
      };
    });
  } else {
    // No insights available
    aiInsights.value = [];
  }
};

/**
 * Sales Upload Modal Functions
 */
const openSalesUploadModal = () => {
  showSalesUploadModal.value = true;
  selectedSalesFile.value = null;
  salesUploadStatus.value = null;
  if (salesFileInput.value) salesFileInput.value.value = '';
};

const closeSalesUploadModal = () => {
  showSalesUploadModal.value = false;
};

const onSalesFileSelect = (event) => {
  const file = event.target.files[0];
  if (!file) {
    selectedSalesFile.value = null;
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    salesUploadStatus.value = { type: 'error', message: 'File too large (max 16MB)' };
    event.target.value = '';
    selectedSalesFile.value = null;
    return;
  }
  selectedSalesFile.value = file;
  salesUploadStatus.value = null;
};

const uploadSalesFile = async () => {
  if (!shopId.value || !selectedSalesFile.value) return;

  salesUploading.value = true;
  salesUploadStatus.value = { type: 'info', message: 'Uploading and analyzing data...' };

  try {
    const response = await uploadSalesDataAPI(shopId.value, selectedSalesFile.value);
    
    if (response.data?.status === 'error') {
      throw new Error(response.data.message || 'Analysis failed');
    }

    // Success! Close modal immediately
    closeSalesUploadModal();

    // User feedback via Toast
    toastMessage.value = 'Sales data uploaded! Updating dashboard...';
    toastIcon.value = 'bi bi-arrow-repeat';
    showToast.value = true;

    // Trigger granular updates - fire and forget (don't await them blocking each other)
    // We explicitly call each fetch function to trigger its own independent loading state
    fetchSalesSummary();
    fetchSalesGrowthTrend(true); // Force refresh
    fetchQuarterlyForecast();
    fetchDashboard(); // This will trigger 'loading' for AI insights and Reorders

    // Show final success toast with timing from the response if available
    const timingMessage = formatUploadTiming(response.data?.upload_log);
    
    // We set a timeout for the completion toast to not override the "Updating" toast immediately
    setTimeout(() => {
        if (response.data?.warning) {
        toastMessage.value = response.data.warning;
        toastIcon.value = 'bi bi-exclamation-triangle';
        } else {
        toastMessage.value = `Dashboard updated! ${timingMessage || ''}`;
        toastIcon.value = 'bi bi-check-circle-fill';
        }
        showToast.value = true;
        setTimeout(() => (showToast.value = false), 5000);
    }, 1500);

  } catch (err) {
    console.error('[Upload Error]', err);
    let errorMsg = 'Upload failed';
    if (err.response?.status === 409) {
      const timingMessage = formatUploadTiming(err.response.data?.upload_log);
      errorMsg = `${err.response.data?.message || 'Duplicate file detected'} ${timingMessage}`.trim();
    } else if (err.response?.status === 400) {
      errorMsg = err.response.data?.message || 'Invalid file format';
    } else if (err.response?.status === 403) {
      errorMsg = 'You do not have permission to upload sales data';
    } else {
      errorMsg = err.response?.data?.message || err.message || 'Upload failed. Please try again.';
    }
    
    if (salesUploading.value) {
        // Still in upload phase, show in modal
        salesUploadStatus.value = { type: 'error', message: errorMsg };
    } else {
        // Modal likely closed
        toastMessage.value = errorMsg;
        toastIcon.value = 'bi bi-x-circle-fill';
        showToast.value = true;
    }
  } finally {
    salesUploading.value = false;
  }
};

/**
 * Download CSV template for sales data upload
 */
const handleDownloadSalesTemplate = async () => {
  try {
    const response = await downloadSalesTemplate();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sales_template.csv';
    link.click();
    window.URL.revokeObjectURL(url);
    toastMessage.value = 'Template downloaded! Fill in your sales data and upload.';
    toastIcon.value = 'bi bi-check-circle-fill';
    showToast.value = true;
    setTimeout(() => (showToast.value = false), 3000);
  } catch (err) {
    console.error('[Template Download Error]', err);
    toastMessage.value = 'Failed to download template';
    toastIcon.value = 'bi bi-exclamation-circle-fill';
    showToast.value = true;
    setTimeout(() => (showToast.value = false), 3000);
  }
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
    const shopName = dashboardData.value?.shop_name || "Shop";
    const reportData = {
        title: `${shopName} Insights Report`,
        subtitle: `Generated on ${new Date().toLocaleDateString()} | Textile Saas App Analytics`,
        metrics: [],
        summary: "Detailed analysis of sales performance, inventory needs, and AI-driven growth opportunities.",
        sections: []
    };

    // Helper to check for empty/zero values
    const isZeroOrEmpty = (val) => {
        if (!val) return true;
        const s = String(val).replace(/[₹Rs.\s,]/g, ''); // Remove currency symbols, spaces, commas
        return s === '' || s === '—' || s === '-' || parseFloat(s) === 0;
    };

    // 1. Sales Summary Metrics
    let hasSalesData = false;
    let metricsList = [];

    if (salesSummaryData.value && salesSummaryData.value.metrics) {
      const m = salesSummaryData.value.metrics;
      metricsList = [
        { label: "Total Revenue", value: m.total_revenue_formatted || "—" },
        { label: "Total Quantity", value: (m.total_quantity || 0).toLocaleString() },
        { label: "Average Order Value", value: m.average_order_value_formatted || "—" },
        { label: "Revenue Growth", value: salesSummaryData.value.comparison?.revenue_change_percent || "—" }
      ];
    } else {
       // Fallback metrics from ref
       if (metrics.value && metrics.value.length > 0) {
           metricsList = metrics.value.slice(0, 4).map(m => ({
               label: m.label,
               value: m.value
           }));
       }
    }

    // Filter metrics: Only show if there is at least one non-zero/non-empty value
    hasSalesData = metricsList.some(m => !isZeroOrEmpty(m.value));
    
    if (hasSalesData) {
        reportData.metrics = metricsList;
    }

    // 2. Sales Summary Text (Trend) - Only show if valid sales data exists
    if (hasSalesData && salesComparison.value && salesComparison.value.message) {
        let summaryText = salesComparison.value.message;
        if (topCategory.value) {
            summaryText += `\nTop seller: ${topCategory.value.name} (${topCategory.value.percentage}% of sales).`;
        }
        reportData.summary = summaryText;
    }

    // 3. AI Insights - Only show if sales data exists (avoids irrelevant insights on empty data)
    if (hasSalesData && aiInsights.value && aiInsights.value.length > 0) {
        let insightsBody = "";
        aiInsights.value.forEach(insight => {
            insightsBody += `• ${insight.title} (${insight.category || 'General'})\n  ${insight.description}\n\n`;
        });
        reportData.sections.push({
            heading: "AI Strategic Insights",
            body: insightsBody
        });
    }

    // 4. Forecast - Only show if projected revenue/quantity is non-zero
    if (quarterlyForecastData.value && quarterlyForecastData.value.summary) {
        const fSummary = quarterlyForecastData.value.summary;
        const predRev = fSummary.total_predicted_revenue_formatted;
        const predQty = fSummary.total_predicted_quantity;
        
        // Show forecast only if there is a positive prediction
        if (!isZeroOrEmpty(predRev) || (predQty && predQty > 0)) {
            let forecastBody = `Projected Revenue: ${predRev}\n`;
            forecastBody += `Projected Quantity: ${predQty}\n`;
            forecastBody += `Confidence Level: ${fSummary.confidence_level || 'N/A'}\n\n`;
            
            if (quarterlyForecastData.value.category_forecast) {
                 forecastBody += "Category Trends:\n";
                 quarterlyForecastData.value.category_forecast.slice(0, 5).forEach(cat => {
                     forecastBody += `- ${cat.name}: ${cat.predicted} (${cat.trend === 'up' ? 'Growing' : 'Declining'})\n`;
                 });
            }
            reportData.sections.push({
                heading: "Quarterly Forecast",
                body: forecastBody
            });
        }
    }

    // 5. Reorder Suggestions
    // Need to get valid reorder suggestions. 
    // They are in groupedReorderSuggestions (dict) or reorderProducts (if that's a ref, but I saw grouped in template)
    // Checking previous code: used reorderProducts.value if available, but let's check groupedReorderSuggestions
    const suggestions = Object.values(groupedReorderSuggestions.value || {}).flat();
    
    if (suggestions.length > 0) {
        let reorderBody = `Total Items Recommended: ${suggestions.length}\n\n`;
        suggestions.slice(0, 10).forEach(p => {
            reorderBody += `• ${p.name}: Order ${p.quantity} units (Stock: ${p.currentStock})\n`;
        });
        if (suggestions.length > 10) {
            reorderBody += `...and ${suggestions.length - 10} more items.`;
        }
        reportData.sections.push({
            heading: "Inventory Reorder Recommendations",
            body: reorderBody
        });
    }

    const response = await generateSalesReportPdf(reportData);
    
    // Create download link
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Shop_Insights_${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);

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
    case 'Very Low': return 'bg-danger';
    default: return 'bg-secondary';
  }
};

/**
 * Get tooltip text for confidence level with data quality info
 */
const getConfidenceTooltip = (summary) => {
  if (!summary) return '';
  
  const daysUsed = summary.historical_days_used || 0;
  const qualityScore = summary.data_quality_score || 0;
  const minRecommended = summary.minimum_recommended_days || 90;
  
  let tooltip = `Data Quality Score: ${qualityScore.toFixed(0)}%\n`;
  tooltip += `Historical Data: ${daysUsed} days\n`;
  
  if (daysUsed < minRecommended) {
    tooltip += `Recommended: ${minRecommended}+ days for better accuracy`;
  } else {
    tooltip += `Sufficient data for reliable forecasts`;
  }
  
  return tooltip;
};

/**
 * Fetch comprehensive sales summary for last 7 days
 * Uses deduplication to prevent multiple simultaneous requests
 */
const fetchSalesSummary = async () => {
  if (!shopId.value || requestInProgress.value.salesSummary) {
    console.log('[SalesSummary] Skipping - no shop or request in progress');
    return;
  }
  
  requestInProgress.value.salesSummary = true;
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
        const summaryInsights = salesSummaryData.value.insights
          .filter(i => i.title !== 'No Sales Data')
          .map(i => ({
            title: i.title,
            icon: i.icon || 'bi bi-lightbulb',
            description: i.message
          }));
        
        if (summaryInsights.length > 0) {
          aiInsights.value = [...summaryInsights, ...aiInsights.value.slice(0, 2)];
        }
      }
      
      // Update average order value metric
      if (salesSummaryData.value?.metrics?.average_order_value_formatted) {
        metrics.value[0].value = salesSummaryData.value.metrics.average_order_value_formatted;
      }
    } else {
      salesSummaryError.value = response.data?.message || 'Failed to load sales summary';
    }
  } catch (err) {
    console.error('[Sales Summary Error]', err);
    salesSummaryError.value = err.response?.data?.message || 'Failed to load sales summary';
  } finally {
    salesSummaryLoading.value = false;
    requestInProgress.value.salesSummary = false;
  }
};

/**
 * Fetch quarterly demand forecast
 * Uses deduplication to prevent multiple simultaneous requests
 */
const fetchQuarterlyForecast = async () => {
  if (!shopId.value || requestInProgress.value.quarterlyForecast) {
    console.log('[QuarterlyForecast] Skipping - no shop or request in progress');
    return;
  }
  
  requestInProgress.value.quarterlyForecast = true;
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
    requestInProgress.value.quarterlyForecast = false;
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
 * Fetch sales growth trend data for chart
 * Uses deduplication to prevent multiple simultaneous requests
 */
const fetchSalesGrowthTrend = async (forceRefresh = false) => {
  if (!shopId.value) return;
  
  // Skip if already fetching (unless forced, e.g., period change)
  if (requestInProgress.value.salesTrend && !forceRefresh) {
    console.log('[SalesGrowthTrend] Request already in progress, skipping');
    return;
  }
  
  requestInProgress.value.salesTrend = true;
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
    requestInProgress.value.salesTrend = false;
  }
};

/**
 * Change chart period and refetch data
 */
const changeChartPeriod = (period) => {
  if (chartPeriod.value === period) return;
  chartPeriod.value = period;
  // Force refresh when changing period
  fetchSalesGrowthTrend(true);
};

/**
 * Initialize dashboard data loading
 * Fetches data sequentially to avoid overwhelming the server
 * Primary data (dashboard + sales summary) loads first, then secondary data
 */
const initializeDashboard = async () => {
  if (!shopId.value) {
    error.value = 'Shop ID not found. Please log in again.';
    return;
  }
  
  try {
    // Phase 1: Load essential data first (dashboard provides base data)
    await fetchDashboard();
    
    // Phase 2: Load sales summary (provides metrics for cards)
    await fetchSalesSummary();
    
    // Phase 3: Load supplementary data in parallel (these can use cached data from backend)
    await Promise.all([
      fetchSalesGrowthTrend(),
      fetchQuarterlyForecast(),
      fetchUploadLogs()
    ]);
  } catch (err) {
    console.error('[Dashboard Init Error]', err);
    error.value = 'Failed to initialize dashboard';
  }
};

/**
 * Refresh all dashboard data (called after upload or inventory changes)
 * Resets request flags to ensure fresh data is fetched
 */
const refreshDashboard = async () => {
  // Reset request flags to ensure we can fetch fresh data
  requestInProgress.value = {
    dashboard: false,
    salesSummary: false,
    quarterlyForecast: false,
    salesTrend: false,
    uploadLogs: false
  };
  
  // Re-initialize to fetch fresh data
  await initializeDashboard();
};

// Fetch dashboard data on mount
onMounted(() => {
  initializeDashboard();
  updateArrows();
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
.bg-purple-soft { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.bg-primary-soft-hover:hover { background: rgba(59, 130, 246, 0.15); border-color: var(--color-primary) !important; }

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
  height: 220px;
  width: 100%;
  position: relative;
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
.ai-insights-card {
  background: linear-gradient(145deg, #ffffff, #f8faff);
  border: 1px solid rgba(59, 130, 246, 0.15); /* Primary tint border */
  position: relative;
  overflow: hidden;
}

.ai-insights-card::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.insights-container {
  height: 400px;
  overflow-y: auto;
  padding: 0.5rem 1rem;
  margin: 0 -0.5rem;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.2);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.4);
}

.text-line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.insight-item {
  padding: 1.25rem;
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  position: relative;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.insight-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.insight-item:hover {
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.1);
  transform: translateY(-2px);
}

.insight-item:hover::before {
  opacity: 1;
}

.insight-icon {
  width: 48px;
  height: 48px;
  color: white;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  transition: transform 0.3s ease;
}

.insight-icon.icon-primary {
  background: var(--gradient-primary, linear-gradient(135deg, #3b82f6 0%, #2563eb 100%));
}

.insight-icon.icon-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
}

.insight-icon.icon-warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
}

.insight-item:hover .insight-icon {
  transform: scale(1.1) rotate(5deg);
}

/* Insight Type Variations */
.insight-success {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.03) 0%, rgba(16, 185, 129, 0.08) 100%);
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.insight-success::before {
  background: linear-gradient(180deg, #10b981 0%, #059669 100%);
}

.insight-success:hover {
  border-color: rgba(16, 185, 129, 0.35);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);
}

.insight-warning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.03) 0%, rgba(245, 158, 11, 0.08) 100%);
  border: 1px solid rgba(245, 158, 11, 0.15);
}

.insight-warning::before {
  background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%);
}

.insight-warning:hover {
  border-color: rgba(245, 158, 11, 0.35);
  box-shadow: 0 8px 25px rgba(245, 158, 11, 0.15);
}

.insight-info {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.03) 0%, rgba(59, 130, 246, 0.08) 100%);
  border: 1px solid rgba(59, 130, 246, 0.15);
}

.insight-info::before {
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
}

.insight-info:hover {
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
}

.bg-warning-soft {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #d97706;
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
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: var(--color-primary-light) transparent;
}

.carousel-track::-webkit-scrollbar {
  height: 8px; /* Horizontal scrollbar thickness */
}

.carousel-track::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
  margin: 0.5rem;
}

.carousel-track::-webkit-scrollbar-thumb {
  background-color: rgba(59, 130, 246, 0.3);
  border-radius: 10px;
  border: 2px solid transparent; /* padding around thumb */
  background-clip: content-box;
}

.carousel-track::-webkit-scrollbar-thumb:hover {
  background-color: rgba(59, 130, 246, 0.6);
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

.toast-notification .bi-info-circle {
  color: #3b82f6;
}

.toast-notification .bi-check-circle-fill {
  color: #10b981;
}

.toast-notification .bi-exclamation-triangle {
  color: #f59e0b;
}

.toast-notification .bi-exclamation-circle-fill {
  color: #ef4444;
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
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.25);
}

.btn-outline-gradient:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>

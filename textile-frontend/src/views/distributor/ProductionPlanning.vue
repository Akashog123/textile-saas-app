<template>
  <div class="production-planning-page">
    <!-- Page Header -->
    <div class="page-header">
      <h5 class="mb-2">
        <i class="bi bi-gear me-2"></i>AI Production Planning
      </h5>
      <p class="text-muted mb-0">
        AI-powered insights for production optimization, stock replenishment, and targeted marketing
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-content">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="loading-text">Generating AI insights...</p>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else-if="!hasData" class="empty-state">
      <div class="empty-state-content">
        <i class="bi bi-box-seam fs-1 mb-3"></i>
        <h5>No Stock Data Available</h5>
        <p class="text-muted mb-4">
          View the Shop Stock Levels page first to load stock data for AI-powered production planning insights.
        </p>
        <router-link to="/distributor/regional-demand" class="btn btn-primary">
          <i class="bi bi-geo-alt me-2 text-white"></i>View Stock Levels
        </router-link>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="planning-content">
      <!-- AI Strategic Analysis Banner -->
      <div class="ai-insights-banner mb-4" v-if="planningData?.aiInsights">
        <div class="ai-header">
          <i class="bi bi-stars me-2"></i>
          <span>AI Strategic Analysis</span>
        </div>
        <p class="ai-summary" v-html="parseMarkdown(planningData.aiInsights.summary)"></p>
        <div class="row mt-3">
          <div class="col-md-6">
            <h6><i class="bi bi-lightbulb me-2"></i>Key Findings</h6>
            <ul class="findings-list">
              <li v-for="(finding, idx) in planningData.aiInsights.keyFindings" :key="idx" v-html="parseMarkdown(finding)">
              </li>
            </ul>
          </div>
          <div class="col-md-6">
            <h6><i class="bi bi-arrow-right-circle me-2"></i>Strategic Recommendations</h6>
            <ul class="recommendations-list">
              <li v-for="(rec, idx) in planningData.aiInsights.strategicRecommendations" :key="idx" v-html="parseMarkdown(rec)">
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Stock Impact Section -->
      <div class="ai-section mb-4">
        <div class="section-header" @click="toggleSection('revenue')">
          <div class="section-title">
            <i class="bi bi-box-seam me-2"></i>
            <span>Stock Impact</span>
          </div>
          <i :class="expandedSections.revenue ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        </div>
        
        <div v-if="expandedSections.revenue" class="section-content">
          <div v-if="revenueLoading" class="section-loading">
            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
            Analyzing stock impact...
          </div>
          <div v-else-if="!revenueImpact && !revenueLoading" class="section-loading">
            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
            Loading stock analysis...
          </div>
          <div v-else-if="revenueImpact">
            <!-- Stock Impact Summary Cards -->
            <div class="row g-3 mb-3">
              <div class="col-md-6">
                <div class="revenue-card at-risk">
                  <div class="revenue-icon">
                    <i class="bi bi-exclamation-triangle"></i>
                  </div>
                  <div class="revenue-content">
                    <div class="revenue-label">Units at Risk</div>
                    <div class="revenue-value">{{ formatNumber(revenueImpact.summary?.totalUnitsAtRisk || 0) }} units</div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="revenue-card potential">
                  <div class="revenue-icon">
                    <i class="bi bi-box-arrow-in-down"></i>
                  </div>
                  <div class="revenue-content">
                    <div class="revenue-label">Restock Needed</div>
                    <div class="revenue-value">{{ formatNumber(revenueImpact.summary?.totalRestockNeeded || 0) }} units</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Stock Impact Table -->
            <div class="forecast-table-container">
              <div class="table-header-row">
                <button class="info-btn" @click.stop="showStockInfo = true" title="How are these calculated?">
                  <i class="bi bi-info-circle me-1"></i>How is this calculated?
                </button>
                <button class="view-all-btn" @click.stop="showStockModal = true">
                  <i class="bi bi-arrows-fullscreen me-1"></i>View All
                </button>
              </div>
              <table class="table forecast-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Shop</th>
                    <th>Stock Level</th>
                    <th>Units Sold</th>
                    <th>Units at Risk</th>
                    <th>Restock Qty</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in revenueImpact.stockImpacts?.slice(0, 10)" :key="item.productId">
                    <td>
                      <strong>{{ item.productName }}</strong>
                      <div class="text-muted small">{{ item.category }}</div>
                    </td>
                    <td>{{ item.shopName }}</td>
                    <td>
                      <div class="stock-bar">
                        <div class="stock-fill" :class="item.status" :style="{ width: Math.min(item.stockRatio, 100) + '%' }"></div>
                      </div>
                      <span class="small">{{ item.stockRatio }}%</span>
                    </td>
                    <td>{{ formatNumber(item.totalSold) }}</td>
                    <td :class="item.unitsAtRisk > 0 ? 'text-danger fw-bold' : ''">
                      {{ formatNumber(item.unitsAtRisk) }}
                    </td>
                    <td class="text-success fw-bold">{{ formatNumber(item.restockQty) }}</td>
                    <td>
                      <span class="status-badge" :class="item.status">
                        {{ item.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Demand Forecast Section -->
      <div class="ai-section mb-4">
        <div class="section-header" @click="toggleSection('forecast')">
          <div class="section-title">
            <i class="bi bi-graph-up-arrow me-2"></i>
            <span>Demand Forecast</span>
          </div>
          <i :class="expandedSections.forecast ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        </div>
        
        <div v-if="expandedSections.forecast" class="section-content">
          <div v-if="forecastLoading" class="section-loading">
            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
            Analyzing demand patterns...
          </div>
          <div v-else-if="!demandForecast && !forecastLoading" class="section-loading">
            <div class="spinner-border spinner-border-sm text-primary me-2"></div>
            Loading forecast data...
          </div>
          <div v-else-if="demandForecast">
            <!-- Forecast Summary Cards -->
            <div class="row g-3 mb-3">
              <div class="col-md-3">
                <div class="mini-stat-card critical">
                  <div class="stat-value">{{ demandForecast.summary?.criticalCount || 0 }}</div>
                  <div class="stat-label">Order Now</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="mini-stat-card warning">
                  <div class="stat-value">{{ demandForecast.summary?.warningCount || 0 }}</div>
                  <div class="stat-label">Restock Soon</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="mini-stat-card healthy">
                  <div class="stat-value">{{ demandForecast.summary?.healthyCount || 0 }}</div>
                  <div class="stat-label">Adequate</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="mini-stat-card info">
                  <div class="stat-value">{{ demandForecast.summary?.totalProducts || 0 }}</div>
                  <div class="stat-label">Total Products</div>
                </div>
              </div>
            </div>
            
            <!-- Forecast Table -->
            <div class="forecast-table-container">
              <div class="table-header-row">
                <button class="info-btn" @click.stop="showForecastInfo = true" title="How are these calculated?">
                  <i class="bi bi-info-circle me-1"></i>How is this calculated?
                </button>
                <button class="view-all-btn" @click.stop="showForecastModal = true">
                  <i class="bi bi-arrows-fullscreen me-1"></i>View All
                </button>
              </div>
              <table class="table forecast-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Shop</th>
                    <th>Current Stock</th>
                    <th>14-Day Demand</th>
                    <th>Daily Avg</th>
                    <th>Stockout In</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in demandForecast.forecasts?.slice(0, 10)" :key="item.productId">
                    <td>
                      <strong>{{ item.productName }}</strong>
                      <div class="text-muted small">{{ item.category }}</div>
                    </td>
                    <td>{{ item.shopName }}</td>
                    <td>{{ item.currentStock }} units</td>
                    <td>
                      <span :class="item.predictedDemand14d > item.currentStock ? 'text-danger fw-bold' : ''">
                        {{ item.predictedDemand14d }} units
                      </span>
                    </td>
                    <td>{{ item.avgDailySales }} /day</td>
                    <td>
                      <span v-if="item.daysUntilStockout" :class="item.daysUntilStockout < 7 ? 'text-danger fw-bold' : 'text-warning'">
                        {{ item.daysUntilStockout }} days
                      </span>
                      <span v-else class="text-success">Safe</span>
                    </td>
                    <td>
                      <span class="action-badge" :class="item.actionClass">
                        {{ item.action }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger mt-4">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
    </div>

    <!-- Floating Chat Widget -->
    <div class="floating-chat-widget" :class="{ 'chat-open': isChatOpen }">
      <!-- Chat Toggle Button -->
      <button 
        class="chat-toggle-btn" 
        @click="toggleChat"
        :disabled="!allInsightsLoaded"
        :class="{ 'loading': !allInsightsLoaded }"
      >
        <template v-if="!allInsightsLoaded">
          <div class="chat-btn-loading">
            <div class="spinner-border spinner-border-sm" role="status"></div>
          </div>
        </template>
        <template v-else>
          <i v-if="!isChatOpen" class="bi bi-chat-dots-fill"></i>
          <i v-else class="bi bi-x-lg"></i>
        </template>
      </button>
      
      <!-- Loading Tooltip -->
      <div v-if="!allInsightsLoaded && !isChatOpen" class="chat-loading-tooltip">
        <i class="bi bi-hourglass-split me-1"></i>
        Loading AI insights...
      </div>

      <!-- Chat Panel -->
      <div v-if="isChatOpen" class="chat-panel" :class="{ 'chat-expanded': isChatExpanded }">
        <div class="chat-panel-header">
          <div class="chat-header-info">
            <i class="bi bi-robot me-2"></i>
            <span>AI Inventory Assistant</span>
          </div>
          <div class="chat-header-actions">
            <button class="chat-action-btn" @click="toggleChatSize" :title="isChatExpanded ? 'Minimize' : 'Expand'">
              <i :class="isChatExpanded ? 'bi bi-arrows-angle-contract' : 'bi bi-arrows-angle-expand'"></i>
            </button>
            <button class="chat-action-btn" @click="toggleChat" title="Close">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>
        
        <div class="chat-panel-body" ref="chatMessagesRef">
          <!-- Welcome Message -->
          <div v-if="chatMessages.length === 0" class="chat-welcome-floating">
            <div class="welcome-icon">
              <i class="bi bi-robot"></i>
            </div>
            <h6>How can I help you today?</h6>
            <p>I have access to your AI insights, demand forecasts, stock risks, and planning data.</p>
            <div class="quick-actions">
              <button @click="askSuggested('What should I prioritize restocking?')" class="quick-action-btn">
                <i class="bi bi-arrow-repeat me-1"></i>Restock priorities
              </button>
              <button @click="askSuggested('Which products are at highest stockout risk?')" class="quick-action-btn">
                <i class="bi bi-exclamation-triangle me-1"></i>Stockout risks
              </button>
              <button @click="askSuggested('Give me a summary of my inventory health')" class="quick-action-btn">
                <i class="bi bi-clipboard-data me-1"></i>Inventory summary
              </button>
            </div>
          </div>
          
          <!-- Chat Messages -->
          <div v-for="(msg, idx) in chatMessages" :key="idx" class="chat-bubble" :class="msg.role">
            <div class="bubble-content" v-html="parseMarkdown(msg.content)"></div>
          </div>
          
          <!-- Typing Indicator -->
          <div v-if="chatLoading" class="chat-bubble assistant">
            <div class="bubble-content typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
        
        <div class="chat-panel-footer">
          <input 
            v-model="chatInput"
            @keyup.enter="sendChatMessage"
            type="text"
            class="chat-input-floating"
            placeholder="Ask about inventory, demand, restocking..."
            :disabled="chatLoading"
          >
          <button @click="sendChatMessage" class="send-btn-floating" :disabled="chatLoading || !chatInput.trim()">
            <i class="bi bi-send-fill"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <i :class="toastType === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-circle-fill'" class="me-2"></i>
      {{ toastMessage }}
    </div>

    <!-- Forecast Info Popup -->
    <div v-if="showForecastInfo" class="info-overlay" @click="showForecastInfo = false">
      <div class="info-popup" @click.stop>
        <div class="info-popup-header">
          <h5><i class="bi bi-info-circle me-2"></i>How Forecast Metrics Are Calculated</h5>
          <button class="info-close-btn" @click="showForecastInfo = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="info-popup-body">
          <div class="info-item">
            <div class="info-icon bg-primary-light">
              <i class="bi bi-calendar-week text-primary"></i>
            </div>
            <div class="info-content">
              <h6>14-Day Demand</h6>
              <p>Calculated by analyzing your historical sales data over the past 30 days. We compute the average daily sales and project it forward for 14 days to estimate upcoming demand.</p>
              <code>14-Day Demand = Daily Average × 14</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-warning-light">
              <i class="bi bi-graph-up text-warning"></i>
            </div>
            <div class="info-content">
              <h6>Daily Average</h6>
              <p>The average number of units sold per day, calculated from your sales records over the past 30 days.</p>
              <code>Daily Avg = Total Units Sold ÷ Number of Days</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-danger-light">
              <i class="bi bi-clock-history text-danger"></i>
            </div>
            <div class="info-content">
              <h6>Stockout In</h6>
              <p>Estimates how many days until your current stock runs out, based on your daily average sales rate.</p>
              <code>Stockout In = Current Stock ÷ Daily Average</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-success-light">
              <i class="bi bi-lightning-charge text-success"></i>
            </div>
            <div class="info-content">
              <h6>Action Status</h6>
              <p>The recommended action is determined by comparing your current stock against the predicted 14-day demand:</p>
              <ul class="action-list">
                <li><span class="action-badge critical">Order Now</span> Current stock is less than 50% of 14-day demand (covers &lt; 7 days)</li>
                <li><span class="action-badge warning">Restock Soon</span> Current stock is less than 14-day demand (covers 7-14 days)</li>
                <li><span class="action-badge healthy">Adequate</span> Current stock meets or exceeds 14-day demand</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stock Impact Info Popup -->
    <div v-if="showStockInfo" class="info-overlay" @click="showStockInfo = false">
      <div class="info-popup" @click.stop>
        <div class="info-popup-header">
          <h5><i class="bi bi-info-circle me-2"></i>How Stock Impact Metrics Are Calculated</h5>
          <button class="info-close-btn" @click="showStockInfo = false">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="info-popup-body">
          <div class="info-item">
            <div class="info-icon bg-primary-light">
              <i class="bi bi-battery-half text-primary"></i>
            </div>
            <div class="info-content">
              <h6>Stock Level</h6>
              <p>Shows the percentage of current stock compared to your safety stock threshold. The progress bar visually indicates how healthy your inventory is.</p>
              <code>Stock Level % = (Current Stock ÷ Safety Stock) × 100</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-success-light">
              <i class="bi bi-cart-check text-success"></i>
            </div>
            <div class="info-content">
              <h6>Units Sold</h6>
              <p>The total number of units sold for this product across all transactions in the selected time period (typically last 30 days).</p>
              <code>Units Sold = Sum of all sales quantities</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-danger-light">
              <i class="bi bi-exclamation-triangle text-danger"></i>
            </div>
            <div class="info-content">
              <h6>Units at Risk</h6>
              <p>The number of units you're short of reaching safe stock levels. For critical items, this is the full gap to safety stock. For low-stock items, it's calculated at 50% of the gap.</p>
              <code>Units at Risk = Safety Stock - Current Stock</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-warning-light">
              <i class="bi bi-box-arrow-in-down text-warning"></i>
            </div>
            <div class="info-content">
              <h6>Restock Qty</h6>
              <p>The recommended quantity to order to bring stock levels to 150% of safety stock, providing a comfortable buffer above the minimum threshold.</p>
              <code>Restock Qty = (Safety Stock × 1.5) - Current Stock</code>
            </div>
          </div>
          
          <div class="info-item">
            <div class="info-icon bg-info-light">
              <i class="bi bi-flag text-info"></i>
            </div>
            <div class="info-content">
              <h6>Status</h6>
              <p>The status is determined by comparing current stock to safety stock levels:</p>
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

    <!-- Demand Forecast Full View Modal -->
    <div v-if="showForecastModal" class="forecast-modal-overlay" @click.self="showForecastModal = false">
      <div class="forecast-modal">
        <div class="forecast-modal-header">
          <div class="modal-title-section">
            <h5><i class="bi bi-graph-up-arrow me-2"></i>Demand Forecast - All Products</h5>
            <span class="product-count-badge">{{ filteredForecasts.length }} products</span>
          </div>
          <div class="modal-actions">
            <div class="search-box">
              <i class="bi bi-search"></i>
              <input 
                type="text" 
                v-model="forecastSearchQuery" 
                placeholder="Search by product, shop, or category..."
                class="search-input"
              />
              <button v-if="forecastSearchQuery" class="clear-search" @click="forecastSearchQuery = ''">
                <i class="bi bi-x"></i>
              </button>
            </div>
            <button class="close-modal-btn" @click="showForecastModal = false">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>
        
        <div class="forecast-modal-body">
          <!-- Summary Cards -->
          <div class="modal-summary-row">
            <div class="modal-stat critical">
              <span class="stat-num">{{ demandForecast?.summary?.criticalCount || 0 }}</span>
              <span class="stat-txt">Order Now</span>
            </div>
            <div class="modal-stat warning">
              <span class="stat-num">{{ demandForecast?.summary?.warningCount || 0 }}</span>
              <span class="stat-txt">Restock Soon</span>
            </div>
            <div class="modal-stat healthy">
              <span class="stat-num">{{ demandForecast?.summary?.healthyCount || 0 }}</span>
              <span class="stat-txt">Adequate</span>
            </div>
            <div class="modal-stat info">
              <span class="stat-num">{{ demandForecast?.summary?.totalProducts || 0 }}</span>
              <span class="stat-txt">Total</span>
            </div>
          </div>

          <!-- Full Table -->
          <div class="modal-table-wrapper">
            <table class="table forecast-modal-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Shop</th>
                  <th>Current Stock</th>
                  <th>14-Day Demand</th>
                  <th>Daily Avg</th>
                  <th>Stockout In</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredForecasts" :key="item.productId + item.shopName">
                  <td>
                    <strong>{{ item.productName }}</strong>
                    <div class="text-muted small">{{ item.category }}</div>
                  </td>
                  <td>{{ item.shopName }}</td>
                  <td>{{ item.currentStock }} units</td>
                  <td>
                    <span :class="item.predictedDemand14d > item.currentStock ? 'text-danger fw-bold' : ''">
                      {{ item.predictedDemand14d }} units
                    </span>
                  </td>
                  <td>{{ item.avgDailySales }} /day</td>
                  <td>
                    <span v-if="item.daysUntilStockout" :class="item.daysUntilStockout < 7 ? 'text-danger fw-bold' : 'text-warning'">
                      {{ item.daysUntilStockout }} days
                    </span>
                    <span v-else class="text-success">Safe</span>
                  </td>
                  <td>
                    <span class="action-badge" :class="item.actionClass">
                      {{ item.action }}
                    </span>
                  </td>
                </tr>
                <tr v-if="filteredForecasts.length === 0">
                  <td colspan="7" class="text-center text-muted py-4">
                    <i class="bi bi-search me-2"></i>
                    No products found matching "{{ forecastSearchQuery }}"
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Stock Impact Full View Modal -->
    <div v-if="showStockModal" class="forecast-modal-overlay" @click.self="showStockModal = false">
      <div class="forecast-modal">
        <div class="forecast-modal-header">
          <div class="modal-title-section">
            <h5><i class="bi bi-box-seam me-2"></i>Stock Impact - All Products</h5>
            <span class="product-count-badge">{{ filteredStockImpacts.length }} products</span>
          </div>
          <div class="modal-actions">
            <div class="search-box">
              <i class="bi bi-search"></i>
              <input 
                type="text" 
                v-model="stockSearchQuery" 
                placeholder="Search by product, shop, category, or status..."
                class="search-input"
              />
              <button v-if="stockSearchQuery" class="clear-search" @click="stockSearchQuery = ''">
                <i class="bi bi-x"></i>
              </button>
            </div>
            <button class="close-modal-btn" @click="showStockModal = false">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        </div>
        
        <div class="forecast-modal-body">
          <!-- Summary Cards -->
          <div class="modal-summary-row">
            <div class="modal-stat critical">
              <span class="stat-num">{{ revenueImpact?.summary?.criticalProducts || 0 }}</span>
              <span class="stat-txt">Critical</span>
            </div>
            <div class="modal-stat warning">
              <span class="stat-num">{{ revenueImpact?.summary?.warningProducts || 0 }}</span>
              <span class="stat-txt">Low Stock</span>
            </div>
            <div class="modal-stat healthy">
              <span class="stat-num">{{ formatNumber(revenueImpact?.summary?.totalUnitsAtRisk || 0) }}</span>
              <span class="stat-txt">Units at Risk</span>
            </div>
            <div class="modal-stat info">
              <span class="stat-num">{{ formatNumber(revenueImpact?.summary?.totalRestockNeeded || 0) }}</span>
              <span class="stat-txt">Restock Needed</span>
            </div>
          </div>

          <!-- Full Table -->
          <div class="modal-table-wrapper">
            <table class="table forecast-modal-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Shop</th>
                  <th>Stock Level</th>
                  <th>Units Sold</th>
                  <th>Units at Risk</th>
                  <th>Restock Qty</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredStockImpacts" :key="item.productId + item.shopName">
                  <td>
                    <strong>{{ item.productName }}</strong>
                    <div class="text-muted small">{{ item.category }}</div>
                  </td>
                  <td>{{ item.shopName }}</td>
                  <td>
                    <div class="stock-bar">
                      <div class="stock-fill" :class="item.status" :style="{ width: Math.min(item.stockRatio, 100) + '%' }"></div>
                    </div>
                    <span class="small">{{ item.stockRatio }}%</span>
                  </td>
                  <td>{{ formatNumber(item.totalSold) }}</td>
                  <td :class="item.unitsAtRisk > 0 ? 'text-danger fw-bold' : ''">
                    {{ formatNumber(item.unitsAtRisk) }}
                  </td>
                  <td class="text-success fw-bold">{{ formatNumber(item.restockQty) }}</td>
                  <td>
                    <span class="status-badge" :class="item.status">
                      {{ item.status }}
                    </span>
                  </td>
                </tr>
                <tr v-if="filteredStockImpacts.length === 0">
                  <td colspan="7" class="text-center text-muted py-4">
                    <i class="bi bi-search me-2"></i>
                    No products found matching "{{ stockSearchQuery }}"
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { getAIStockPlanning, getAIDemandForecast, getAIRevenueImpact, sendAIChatMessage } from '@/api/apiDistributor'

// State
const loading = ref(false)
const error = ref('')
const planningData = ref(null)
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

// New AI features state
const demandForecast = ref(null)
const forecastLoading = ref(false)
const revenueImpact = ref(null)
const revenueLoading = ref(false)

// Floating chat state
const isChatOpen = ref(false)
const isChatExpanded = ref(false)
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatMessagesRef = ref(null)

// Forecast info popup state
const showForecastInfo = ref(false)
const showStockInfo = ref(false)

// Forecast modal state
const showForecastModal = ref(false)
const forecastSearchQuery = ref('')

// Stock Impact modal state
const showStockModal = ref(false)
const stockSearchQuery = ref('')

// Expandable sections
const expandedSections = ref({
  forecast: true,
  revenue: true
})

// Check if we have data
const hasData = computed(() => {
  return !!planningData.value
})

// Check if all AI insights are loaded
const allInsightsLoaded = computed(() => {
  return planningData.value && demandForecast.value && revenueImpact.value
})

// Filtered forecasts for modal search
const filteredForecasts = computed(() => {
  if (!demandForecast.value?.forecasts) return []
  if (!forecastSearchQuery.value.trim()) {
    return demandForecast.value.forecasts
  }
  const query = forecastSearchQuery.value.toLowerCase().trim()
  return demandForecast.value.forecasts.filter(item => 
    item.productName?.toLowerCase().includes(query) ||
    item.shopName?.toLowerCase().includes(query) ||
    item.category?.toLowerCase().includes(query)
  )
})

// Filtered stock impacts for modal search
const filteredStockImpacts = computed(() => {
  if (!revenueImpact.value?.stockImpacts) return []
  if (!stockSearchQuery.value.trim()) {
    return revenueImpact.value.stockImpacts
  }
  const query = stockSearchQuery.value.toLowerCase().trim()
  return revenueImpact.value.stockImpacts.filter(item => 
    item.productName?.toLowerCase().includes(query) ||
    item.shopName?.toLowerCase().includes(query) ||
    item.category?.toLowerCase().includes(query) ||
    item.status?.toLowerCase().includes(query)
  )
})

// Toggle chat panel
const toggleChat = () => {
  if (allInsightsLoaded.value) {
    isChatOpen.value = !isChatOpen.value
    if (!isChatOpen.value) {
      isChatExpanded.value = false  // Reset to normal size when closing
    }
  }
}

// Toggle chat size (expand/minimize)
const toggleChatSize = () => {
  isChatExpanded.value = !isChatExpanded.value
}

// Toggle section expansion
const toggleSection = (section) => {
  expandedSections.value[section] = !expandedSections.value[section]
  
  // Auto-load data when section is expanded
  if (expandedSections.value[section]) {
    if (section === 'forecast' && !demandForecast.value) {
      loadDemandForecast()
    } else if (section === 'revenue' && !revenueImpact.value) {
      loadRevenueImpact()
    }
  }
}

// Lifecycle
onMounted(async () => {
  loadFromCache()
  
  if (!planningData.value) {
    await loadPlanningData()
  }
  
  // Only load AI features if not already cached
  if (planningData.value) {
    if (!demandForecast.value) {
      loadDemandForecast()
    }
    if (!revenueImpact.value) {
      loadRevenueImpact()
    }
  }
})

// Load from cache
const loadFromCache = () => {
  // Load main planning data
  const cachedPlanning = sessionStorage.getItem('stockPlanningData')
  if (cachedPlanning) {
    try {
      planningData.value = JSON.parse(cachedPlanning)
    } catch (e) {
      sessionStorage.removeItem('stockPlanningData')
      sessionStorage.removeItem('stockPlanningDataHash')
    }
  }
  
  // Load demand forecast cache
  const cachedForecast = sessionStorage.getItem('demandForecastData')
  if (cachedForecast) {
    try {
      demandForecast.value = JSON.parse(cachedForecast)
    } catch (e) {
      sessionStorage.removeItem('demandForecastData')
    }
  }
  
  // Load revenue impact cache
  const cachedRevenue = sessionStorage.getItem('revenueImpactData')
  if (cachedRevenue) {
    try {
      revenueImpact.value = JSON.parse(cachedRevenue)
    } catch (e) {
      sessionStorage.removeItem('revenueImpactData')
    }
  }
}

// Generate hash for cache detection
const generateDataHash = (data) => {
  const str = JSON.stringify(data)
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return hash.toString()
}

// Load planning data
const loadPlanningData = async () => {
  if (planningData.value) return

  const storedData = sessionStorage.getItem('stockHeatmapData')
  if (!storedData) return

  const stockData = JSON.parse(storedData)
  const currentDataHash = generateDataHash(stockData)
  const cachedDataHash = sessionStorage.getItem('stockPlanningDataHash')

  const cachedPlanning = sessionStorage.getItem('stockPlanningData')
  if (cachedPlanning && cachedDataHash === currentDataHash) {
    try {
      planningData.value = JSON.parse(cachedPlanning)
      return
    } catch (e) {
      sessionStorage.removeItem('stockPlanningData')
      sessionStorage.removeItem('stockPlanningDataHash')
    }
  }

  loading.value = true
  error.value = ''

  try {
    const response = await getAIStockPlanning({
      heatmapPoints: stockData.heatmapPoints,
      summary: stockData.summary
    })

    if (response.data && response.data.status === 'success') {
      planningData.value = response.data.data
      sessionStorage.setItem('stockPlanningData', JSON.stringify(response.data.data))
      sessionStorage.setItem('stockPlanningDataHash', currentDataHash)
      showToastMsg('AI insights generated successfully', 'success')
    } else {
      error.value = response.data?.message || 'Failed to generate planning insights'
    }
  } catch (err) {
    console.error('[Planning Error]', err)
    error.value = err.response?.data?.message || 'Failed to load planning data'
    showToastMsg('Error loading planning data', 'error')
  } finally {
    loading.value = false
  }
}

// Load demand forecast
const loadDemandForecast = async () => {
  // Check cache first
  if (demandForecast.value) return
  
  forecastLoading.value = true
  try {
    const response = await getAIDemandForecast()
    if (response.data?.status === 'success') {
      demandForecast.value = response.data.data
      // Cache the result
      sessionStorage.setItem('demandForecastData', JSON.stringify(response.data.data))
    }
  } catch (err) {
    console.error('[Demand Forecast Error]', err)
    showToastMsg('Error loading demand forecast', 'error')
  } finally {
    forecastLoading.value = false
  }
}

// Load revenue impact
const loadRevenueImpact = async () => {
  // Check cache first
  if (revenueImpact.value) return
  
  revenueLoading.value = true
  try {
    const response = await getAIRevenueImpact()
    if (response.data?.status === 'success') {
      revenueImpact.value = response.data.data
      // Cache the result
      sessionStorage.setItem('revenueImpactData', JSON.stringify(response.data.data))
    }
  } catch (err) {
    console.error('[Revenue Impact Error]', err)
    showToastMsg('Error loading revenue analysis', 'error')
  } finally {
    revenueLoading.value = false
  }
}

// Chat functions
const sendChatMessage = async () => {
  const message = chatInput.value.trim()
  if (!message || chatLoading.value) return
  
  chatMessages.value.push({ role: 'user', content: message })
  chatInput.value = ''
  chatLoading.value = true
  
  await nextTick()
  scrollChatToBottom()
  
  try {
    // Build context from loaded AI insights
    const context = {
      stockPlanning: planningData.value,
      demandForecast: demandForecast.value,
      stockImpact: revenueImpact.value
    }
    
    const response = await sendAIChatMessage(message, context)
    if (response.data?.status === 'success') {
      chatMessages.value.push({ role: 'assistant', content: response.data.data.response })
    } else {
      chatMessages.value.push({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' })
    }
  } catch (err) {
    console.error('[Chat Error]', err)
    chatMessages.value.push({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' })
  } finally {
    chatLoading.value = false
    await nextTick()
    scrollChatToBottom()
  }
}

const askSuggested = (question) => {
  chatInput.value = question
  sendChatMessage()
}

const scrollChatToBottom = () => {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

// Helper functions
const formatNumber = (num) => {
  if (!num) return '0'
  return new Intl.NumberFormat('en-IN').format(Math.round(num))
}

const formatCompact = (num) => {
  if (!num) return '0'
  if (num >= 10000000) return (num / 10000000).toFixed(1) + 'Cr'
  if (num >= 100000) return (num / 100000).toFixed(1) + 'L'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const parseMarkdown = (text) => {
  if (!text) return ''
  return text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

const showToastMsg = (message, type = 'success') => {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => (showToast.value = false), 3000)
}
</script>

<style scoped>
.production-planning-page {
  background: #ffffff;
  min-height: calc(100vh - 80px);
  padding: 2rem;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
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

/* Loading State */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.loading-text {
  margin-top: 1rem;
  color: #666;
  font-weight: 500;
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

/* AI Insights Banner */
.ai-insights-banner {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 2px solid var(--color-primary);
  border-radius: 16px;
  padding: 1.5rem;
}

.ai-header {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 1rem;
}

.ai-summary {
  font-size: 1rem;
  color: #333;
  line-height: 1.6;
}

.findings-list, .recommendations-list {
  padding-left: 1.2rem;
  margin: 0;
}

.findings-list li, .recommendations-list li {
  margin-bottom: 0.5rem;
  color: #444;
}

/* AI Section Styles */
.ai-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: all 0.3s ease;
}

.ai-section:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  cursor: pointer;
  transition: background 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.section-header:hover {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-primary);
}

:deep(.section-title .bi) {
  color: var(--color-primary);
  font-size: 1.1rem;
}

.section-header:hover .section-title {
  color: var(--color-primary);
}

:deep(.section-header:hover .section-title .bi) {
  color: var(--color-primary);
}

.section-content {
  padding: 0.5rem 1.5rem 1rem 1.5rem;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 2000px; }
}

.section-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
}

/* AI Analysis Box */
.ai-analysis-box {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-left: 4px solid var(--color-primary);
  padding: 1rem;
  border-radius: 8px;
  color: #333;
}

/* Mini Stat Cards */
.mini-stat-card {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border-left: 4px solid;
  border-top: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.mini-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
}

.mini-stat-card.critical { border-color: #dc2626; }
.mini-stat-card.warning { border-color: #f59e0b; }
.mini-stat-card.healthy { border-color: #10b981; }
.mini-stat-card.info { border-color: #3b82f6; }

.mini-stat-card .stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
}

.mini-stat-card .stat-label {
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
}

/* Forecast Table */
.forecast-table-container {
  overflow-x: auto;
}

.forecast-table {
  width: 100%;
  border-collapse: collapse;
}

.forecast-table th {
  background: #f8fafc;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
}

.forecast-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s ease;
}

.forecast-table tbody tr {
  transition: all 0.2s ease;
}

.forecast-table tbody tr:hover {
  background: #f8fafc;
}

/* Action Badge */
.action-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.action-badge.critical { background: #fee2e2; color: #dc2626; }
.action-badge.warning { background: #fef3c7; color: #d97706; }
.action-badge.healthy { background: #d1fae5; color: #059669; }

/* Status Badge */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.critical { background: #fee2e2; color: #dc2626; }
.status-badge.warning { background: #fef3c7; color: #d97706; }
.status-badge.healthy { background: #d1fae5; color: #059669; }

/* Stock Bar */
.stock-bar {
  width: 60px;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  display: inline-block;
  margin-right: 0.5rem;
}

.stock-fill {
  height: 100%;
  border-radius: 4px;
}

.stock-fill.critical { background: #dc2626; }
.stock-fill.warning { background: #f59e0b; }
.stock-fill.healthy { background: #10b981; }

/* Revenue Cards */
.revenue-card {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  border-radius: 12px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.revenue-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
}

.revenue-card.at-risk {
  border-left: 4px solid #dc2626;
  background: linear-gradient(135deg, #fff 0%, #fef2f2 100%);
}

.revenue-card.potential {
  border-left: 4px solid #10b981;
  background: linear-gradient(135deg, #fff 0%, #ecfdf5 100%);
}

.revenue-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-right: 1rem;
}

.revenue-card.at-risk .revenue-icon { background: #fee2e2; color: #dc2626; }
.revenue-card.potential .revenue-icon { background: #d1fae5; color: #059669; }

.revenue-label {
  font-size: 0.85rem;
  color: #666;
}

.revenue-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
}

/* Floating Chat Widget */
.floating-chat-widget {
  position: fixed;
  bottom: 24px;
  left: 24px;
  z-index: 1000;
}

.chat-toggle-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: #3b82f6;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.25);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-toggle-btn:hover:not(:disabled) {
  transform: scale(1.1);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.3);
}

.chat-toggle-btn:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.chat-toggle-btn.loading {
  background: #94a3b8;
}

.chat-btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-btn-loading .spinner-border {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

.chat-loading-tooltip {
  position: absolute;
  left: 70px;
  bottom: 15px;
  background: #1e293b;
  color: white;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  animation: fadeIn 0.3s ease;
}

.chat-loading-tooltip::before {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
  border-width: 6px;
  border-style: solid;
  border-color: transparent #1e293b transparent transparent;
}

/* Chat Panel */
.chat-panel {
  position: absolute;
  bottom: 70px;
  left: 0;
  width: 380px;
  height: 500px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Expanded Chat Panel - Full size with equal margins (24px gap on all sides) */
.chat-panel.chat-expanded {
  position: fixed;
  left: 24px;
  right: 24px;
  bottom: 94px;  /* 24px gap + 70px for toggle button */
  top: 94px;  /* 24px gap + ~70px for navbar */
  width: auto;
  height: auto;
}

@keyframes slideUp {
  from { 
    opacity: 0; 
    transform: translateY(20px) scale(0.95); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

.chat-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(59, 130, 246, 0.75);
  color: white;
}

.chat-header-info {
  display: flex;
  align-items: center;
  font-weight: 700;
  font-size: 1.1rem;
}

.chat-header-actions {
  display: flex;
  gap: 8px;
}

.chat-action-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.chat-minimize-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: background 0.2s ease;
}

.chat-minimize-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.chat-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8fafc;
}

.chat-welcome-floating {
  text-align: center;
  padding: 20px 10px;
}

.welcome-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-bg-alt) 0%, rgba(59, 130, 246, 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 1.75rem;
  color: var(--color-primary);
}

.chat-welcome-floating h6 {
  margin-bottom: 8px;
  color: #1e293b;
}

.chat-welcome-floating p {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 16px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-action-btn {
  width: 100%;
  padding: 10px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.85rem;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.quick-action-btn:hover {
  background: rgba(59, 130, 246, 0.4);
  color: white;
  border-color: transparent;
  transform: translateX(4px);
}

.quick-action-btn i {
  color: var(--color-primary);
}

.quick-action-btn:hover i {
  color: white;
}

/* Chat Bubbles */
.chat-bubble {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
}

.chat-bubble.user {
  align-items: flex-end;
}

.chat-bubble.assistant {
  align-items: flex-start;
}

.bubble-content {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 1rem;
  line-height: 1.6;
}

.chat-bubble.user .bubble-content {
  background: rgba(59, 130, 246, 0.3);
  color: #1e293b;
  border-bottom-right-radius: 4px;
}

.chat-bubble.assistant .bubble-content {
  background: white;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px !important;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typingBounce 1s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes typingBounce {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50% { transform: translateY(-4px); opacity: 1; }
}

/* Chat Panel Footer */
.chat-panel-footer {
  display: flex;
  padding: 12px 16px;
  background: white;
  border-top: 1px solid #e2e8f0;
  gap: 8px;
}

.chat-input-floating {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 10px 16px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.chat-input-floating:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}

.send-btn-floating {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn-floating:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.send-btn-floating:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* No Data Message */
.no-data-message {
  text-align: center;
  padding: 2rem;
  color: #666;
}

/* Buttons */
.btn-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.25);
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
  background: linear-gradient(135deg, #10b981, #059669);
}

.toast-notification.error {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

/* Responsive */
@media (max-width: 768px) {
  .production-planning-page {
    padding: 1rem;
  }
  
  .floating-chat-widget {
    bottom: 16px;
    left: 16px;
  }
  
  .chat-panel {
    width: calc(100vw - 32px);
    height: 60vh;
    left: 0;
    bottom: 70px;
  }
  
  .chat-panel.chat-expanded {
    position: fixed;
    left: 16px;
    right: 16px;
    bottom: 86px;
    top: 80px;
    width: auto;
    height: auto;
  }
  
  .chat-toggle-btn {
    width: 54px;
    height: 54px;
    font-size: 1.25rem;
  }
  
  .chat-loading-tooltip {
    display: none;
  }
}

/* Table Header Row with Info Button */
.table-header-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.75rem;
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

/* View All Button */
.view-all-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  padding: 0.4rem 0.85rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.view-all-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.table-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

/* Forecast Modal Styles */
.forecast-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

.forecast-modal {
  background: white;
  border-radius: 16px;
  width: 95%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
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

.forecast-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px 16px 0 0;
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-title-section h5 {
  margin: 0;
  font-weight: 600;
  color: #1e293b;
}

.product-count-badge {
  background: #e0e7ff;
  color: #4f46e5;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-box i.bi-search {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  font-size: 0.9rem;
}

.search-input {
  padding: 0.5rem 2.5rem 0.5rem 2.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  width: 280px;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: #94a3b8;
}

.clear-search {
  position: absolute;
  right: 8px;
  background: #e2e8f0;
  border: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  font-size: 0.7rem;
}

.clear-search:hover {
  background: #cbd5e1;
}

.close-modal-btn {
  background: none;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s ease;
}

.close-modal-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.forecast-modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-summary-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.modal-stat {
  flex: 1;
  padding: 1rem;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.modal-stat.critical {
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.2);
}

.modal-stat.warning {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.modal-stat.healthy {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.modal-stat.info {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.modal-stat .stat-num {
  font-size: 1.5rem;
  font-weight: 700;
}

.modal-stat.critical .stat-num { color: #dc2626; }
.modal-stat.warning .stat-num { color: #d97706; }
.modal-stat.healthy .stat-num { color: #059669; }
.modal-stat.info .stat-num { color: #2563eb; }

.modal-stat .stat-txt {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
  margin-top: 4px;
}

.modal-table-wrapper {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.forecast-modal-table {
  width: 100%;
  margin: 0;
  font-size: 0.85rem;
}

.forecast-modal-table thead {
  background: #f8fafc;
  position: sticky;
  top: 0;
}

.forecast-modal-table th {
  padding: 0.875rem 1rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e2e8f0;
}

.forecast-modal-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.forecast-modal-table tbody tr:hover {
  background: #f8fafc;
}

.forecast-modal-table tbody tr:last-child td {
  border-bottom: none;
}
</style>

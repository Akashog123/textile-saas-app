<template>
  <div class="shop-dashboard-tab">
    <!-- Hero Header Section -->
    <div class="dashboard-hero mb-4">
      <div class="d-flex align-items-center justify-content-between">
        <div>
          <h3 class="hero-title mb-2">
            <i class="bi bi-speedometer2 me-2"></i>
            Shop Manager Dashboard
          </h3>
          <p class="hero-subtitle mb-0">
            Welcome back! Here's your business overview.
          </p>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-gradient btn-sm" @click="uploadSalesData">
            <i class="bi bi-graph-up-arrow me-1"></i>
            Upload Sales Data
          </button>
          <button class="btn btn-gradient btn-sm" @click="exportReport">
            <i class="bi bi-download me-1"></i>
            Export Report
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
          class="metric-card p-3"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="d-flex align-items-center justify-content-between mb-2">
            <small class="metric-label">{{ metric.label }}</small>
            <div class="metric-icon" :class="metric.iconClass">
              <i :class="metric.icon"></i>
            </div>
          </div>
          <div class="d-flex align-items-end justify-content-between">
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-change" :class="metric.changeClass">
              <i :class="metric.changeIcon"></i>
              {{ metric.change }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="row g-3">
      <div class="col-lg-6">
        <div class="card modern-card">
          <div class="card-body">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h6 class="card-title mb-0">
                <i class="bi bi-graph-up me-2"></i>
                Weekly Sales Summary
              </h6>
              <span class="badge bg-success-soft">
                <i class="bi bi-arrow-up"></i> 12%
              </span>
            </div>
            <div class="summary-content p-3 rounded">
              <div class="summary-item mb-3">
                <div class="d-flex align-items-start gap-2">
                  <i class="bi bi-check-circle-fill text-success mt-1"></i>
                  <div>
                    <p class="mb-1">
                      Sales increased by <strong>12%</strong> compared to last
                      week
                    </p>
                    <small class="text-muted"
                      >Cotton fabric showing highest demand</small
                    >
                  </div>
                </div>
              </div>
              <div class="summary-stats row g-2 mb-3">
                <div class="col-6">
                  <div class="stat-box">
                    <small class="text-muted d-block">Total Orders</small>
                    <strong class="fs-5">147</strong>
                  </div>
                </div>
                <div class="col-6">
                  <div class="stat-box">
                    <small class="text-muted d-block">Avg. Order Value</small>
                    <strong class="fs-5">₹1,815</strong>
                  </div>
                </div>
              </div>
              <button class="btn btn-gradient w-100" @click="viewSalesReport">
                <i class="bi bi-file-earmark-bar-graph me-1"></i>
                View Detailed Report
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card modern-card">
          <div class="card-body">
            <h6 class="card-title mb-3">
              <i class="bi bi-activity me-2"></i>
              Sales Growth Trend
            </h6>
            <div class="chart-placeholder mt-3" @click="viewDetailedChart">
              <svg viewBox="0 0 400 180" class="w-100" style="height: 180px">
                <defs>
                  <linearGradient
                    id="chartGradient"
                    x1="0"
                    x2="0"
                    y1="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stop-color="#667eea"
                      stop-opacity="0.15"
                    />
                    <stop
                      offset="100%"
                      stop-color="#764ba2"
                      stop-opacity="0.02"
                    />
                  </linearGradient>
                </defs>
                <!-- Chart line path -->
                <path
                  d="M0,140 L50,130 L100,100 L150,110 L200,70 L250,60 L300,50 L350,35 L400,30"
                  fill="none"
                  stroke="#667eea"
                  stroke-width="3"
                  class="chart-path"
                />
                <!-- Area fill under the line -->
                <path
                  d="M0,140 L50,130 L100,100 L150,110 L200,70 L250,60 L300,50 L350,35 L400,30 L400,180 L0,180 Z"
                  fill="url(#chartGradient)"
                  class="chart-area"
                />
                <!-- Data points -->
                <circle
                  v-for="(point, i) in chartPoints"
                  :key="i"
                  :cx="point.x"
                  :cy="point.y"
                  r="6"
                  fill="#fff"
                  stroke="#667eea"
                  stroke-width="2.5"
                  class="chart-point"
                  @mouseenter="showTooltip(point)"
                  @mouseleave="hideTooltip"
                />
              </svg>
              <div
                class="chart-labels d-flex justify-content-between mt-2 px-1"
              >
                <small class="text-muted">Mon</small>
                <small class="text-muted">Tue</small>
                <small class="text-muted">Wed</small>
                <small class="text-muted">Thu</small>
                <small class="text-muted">Fri</small>
                <small class="text-muted">Sat</small>
                <small class="text-muted">Sun</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card modern-card">
          <div class="card-body">
            <h6 class="card-title mb-3">
              <i class="bi bi-graph-up-arrow me-2"></i>
              Next Quarter Demand Forecast
            </h6>
            <div class="forecast-container p-3 rounded">
              <div class="row g-3">
                <div
                  class="col-4"
                  v-for="(forecast, index) in forecasts"
                  :key="index"
                >
                  <div
                    class="forecast-item text-center"
                    @click="viewForecastDetails(forecast)"
                  >
                    <div class="forecast-icon mb-2" :class="forecast.iconBg">
                      <i
                        :class="forecast.icon"
                        :style="{ color: forecast.color }"
                      ></i>
                    </div>
                    <small class="d-block fw-semibold mb-1">{{
                      forecast.name
                    }}</small>
                    <div class="forecast-badge" :class="forecast.badgeClass">
                      <i :class="forecast.trendIcon"></i>
                      {{ forecast.trend }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card modern-card ai-insights-card">
          <div class="card-body">
            <h6 class="card-title mb-3">
              <i class="bi bi-stars me-2"></i>
              AI-Powered Insights
            </h6>
            <div class="insights-container">
              <div
                class="insight-item mb-3"
                v-for="(insight, index) in aiInsights"
                :key="index"
              >
                <div class="d-flex align-items-start gap-3">
                  <div class="insight-icon">
                    <i :class="insight.icon"></i>
                  </div>
                  <div class="flex-grow-1">
                    <strong class="d-block mb-1">{{ insight.title }}</strong>
                    <p class="mb-0 small text-muted">
                      {{ insight.description }}
                    </p>
                  </div>
                  <button
                    class="btn btn-sm btn-outline-gradient"
                    @click="applyInsight(insight)"
                  >
                    Apply
                  </button>
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
            <div class="reorder-carousel">
              <button
                class="carousel-nav-btn prev"
                @click="scrollCarousel('left')"
                v-show="showLeftArrow"
              >
                <i class="bi bi-chevron-left"></i>
              </button>
              <div
                class="carousel-track"
                ref="carouselTrack"
                @scroll="updateArrows"
              >
                <div
                  class="reorder-card"
                  v-for="(product, index) in reorderProducts"
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
                      Hot
                    </div>
                  </div>
                  <div class="product-details p-3">
                    <h6 class="product-name mb-1">{{ product.name }}</h6>
                    <p class="product-supplier mb-2">
                      <i class="bi bi-shop me-1"></i>
                      {{ product.supplier }}
                    </p>
                    <div
                      class="d-flex align-items-center justify-content-between mb-2"
                    >
                      <span class="product-quantity"
                        >Qty: {{ product.quantity }}</span
                      >
                      <span class="product-price">{{ product.price }}</span>
                    </div>
                    <div class="product-sku mb-3">
                      <small class="text-muted">SKU: {{ product.sku }}</small>
                    </div>
                    <button
                      class="btn btn-gradient btn-sm w-100"
                      @click.stop="addToCart(product)"
                    >
                      <i class="bi bi-cart-plus me-1"></i>
                      Reorder Now
                    </button>
                  </div>
                </div>
              </div>
              <button
                class="carousel-nav-btn next"
                @click="scrollCarousel('right')"
                v-show="showRightArrow"
              >
                <i class="bi bi-chevron-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Browse Available Products Section -->
    <!-- ✅ Browse Available Products Section -->
    <div class="mt-4">
      <div class="card modern-card">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h5 class="section-title mb-0">
              <i class="bi bi-grid-3x3 me-2"></i>
              Browse Available Products
            </h5>
            <div class="d-flex gap-2">
              <button
                v-for="filter in productFilters"
                :key="filter.id"
                class="filter-chip"
                :class="{ active: selectedFilter === filter.id }"
                @click="selectFilter(filter.id)"
              >
                <i :class="filter.icon" class="me-1"></i>
                {{ filter.label }}
              </button>
            </div>
          </div>

          <!-- ✅ Loader while fetching -->
          <div v-if="catalogLoading" class="text-center py-4 text-muted">
            <i class="bi bi-arrow-repeat spin me-2"></i> Loading products...
          </div>

          <!-- ✅ Catalog Grid (uses live data) -->
          <div v-else class="products-grid">
            <div
              class="product-grid-card"
              v-for="(product, index) in catalog"
              :key="index"
              @click="viewProductDetails(product)"
            >
              <div class="product-grid-image">
                <img
                  :src="product.image_url"
                  :alt="product.product_name"
                  @error="onImgError"
                />
                <div class="product-overlay">
                  <button
                    class="btn btn-light btn-sm"
                    @click.stop="quickView(product)"
                  >
                    <i class="bi bi-eye"></i> Quick View
                  </button>
                </div>
              </div>

              <div class="product-grid-info p-3">
                <div
                  class="d-flex justify-content-between align-items-start mb-2"
                >
                  <h6 class="product-grid-name mb-0">
                    {{ product.product_name || "Untitled" }}
                  </h6>
                  <div class="rating">
                    <i class="bi bi-star-fill text-warning"></i>
                    <span class="small">{{ product.rating || "4.0" }}</span>
                  </div>
                </div>

                <p class="product-description mb-2">
                  {{ product.category || "General Fabric" }}
                </p>

                <div
                  class="d-flex justify-content-between align-items-center mb-2"
                >
                  <div class="supplier-info">
                    <small class="text-muted d-block">Category</small>
                    <strong class="small">{{
                      product.category || "N/A"
                    }}</strong>
                  </div>
                  <div class="stock-info text-end">
                    <small class="text-muted d-block">Color</small>
                    <strong class="small text-secondary">{{
                      product.color || "N/A"
                    }}</strong>
                  </div>
                </div>

                <div class="product-grid-footer">
                  <div class="price-section">
                    <span class="current-price">
                      ₹{{ product.price ? product.price : "—" }}
                    </span>
                  </div>
                  <button
                    class="btn btn-gradient btn-sm"
                    @click.stop="addToCart(product)"
                  >
                    <i class="bi bi-cart-plus"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- ✅ Empty State -->
          <div
            v-if="!catalogLoading && catalog.length === 0"
            class="text-center py-4 text-muted"
          >
            No products available in catalog.
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
              <button
                class="btn btn-gradient btn-lg w-100"
                @click="addToCart(selectedProduct)"
              >
                <i class="bi bi-cart-plus me-2"></i>
                Add to Cart
              </button>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios"; // ✅ main backend API
import catalogApi from "../../api/apiCatalog"; // ✅ catalog API for dataset

// ---------------------------------------------
// 🌍 Reactive State (Preserve UI placeholders)
// ---------------------------------------------
const metrics = ref([
  {
    label: "Weekly Sales",
    value: "₹0",
    change: "+0%",
    changeClass: "neutral",
    changeIcon: "bi bi-dash",
    icon: "bi bi-currency-rupee",
    iconClass: "bg-success-soft",
  },
  {
    label: "Pending Reorders",
    value: "0",
    change: "0",
    changeClass: "neutral",
    changeIcon: "bi bi-dash",
    icon: "bi bi-cart-check",
    iconClass: "bg-warning-soft",
  },
  {
    label: "Total Orders",
    value: "0",
    change: "+0%",
    changeClass: "neutral",
    changeIcon: "bi bi-dash",
    icon: "bi bi-bag-check",
    iconClass: "bg-primary-soft",
  },
  {
    label: "Customer Rating",
    value: "0",
    change: "+0",
    changeClass: "neutral",
    changeIcon: "bi bi-dash",
    icon: "bi bi-star-fill",
    iconClass: "bg-info-soft",
  },
]);

// Chart Points (Dynamic later)
const chartPoints = ref([]);

// Forecasts (Static placeholders retained)
const forecasts = ref([
  {
    name: "Cotton",
    icon: "bi bi-graph-up-arrow fs-3",
    color: "#10b981",
    iconBg: "bg-success-soft",
    trend: "+0%",
    trendIcon: "bi bi-dash",
    badgeClass: "trend-stable",
  },
  {
    name: "Silk",
    icon: "bi bi-bar-chart-fill fs-3",
    color: "#667eea",
    iconBg: "bg-primary-soft",
    trend: "Stable",
    trendIcon: "bi bi-dash",
    badgeClass: "trend-stable",
  },
  {
    name: "Linen",
    icon: "bi bi-graph-down-arrow fs-3",
    color: "#ef4444",
    iconBg: "bg-danger-soft",
    trend: "-0%",
    trendIcon: "bi bi-dash",
    badgeClass: "trend-stable",
  },
]);

// AI Insights and Reorder Products (filled later from backend)
const aiInsights = ref([]);
const reorderProducts = ref([]);

// ✅ Catalog Data
const catalog = ref([]);
const catalogLoading = ref(true);

function onImgError(e) {
  e.target.src = "https://via.placeholder.com/300x300?text=No+Image";
}

// Product Filters
const productFilters = ref([
  { id: "all", label: "All", icon: "bi bi-grid" },
  { id: "category", label: "Category", icon: "bi bi-palette-fill" },
  { id: "price", label: "Price", icon: "bi bi-rulers" },
  { id: "brand", label: "Brand", icon: "bi bi-tag-fill" },
]);

const selectedFilter = ref("all");
const carouselTrack = ref(null);
const showLeftArrow = ref(false);
const showRightArrow = ref(true);
const showQuickView = ref(false);
const selectedProduct = ref(null);
const showToast = ref(false);
const toastMessage = ref("");
const toastIcon = ref("bi bi-check-circle-fill");

// ---------------------------------------------
// ⚙️ Toast Utility
// ---------------------------------------------
const showToastMessage = (msg, icon = "bi bi-info-circle-fill") => {
  toastMessage.value = msg;
  toastIcon.value = icon;
  showToast.value = true;
  setTimeout(() => (showToast.value = false), 3000);
};

// ---------------------------------------------
// 📁 File Upload Logic (Working Upload Button)
// ---------------------------------------------
const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.accept = ".csv, .xlsx";
fileInput.style.display = "none";
document.body.appendChild(fileInput);

const uploadSalesData = async () => {
  fileInput.click();

  fileInput.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || !user.id) {
      showToastMessage(
        "User not found. Please log in again.",
        "bi bi-exclamation-triangle"
      );
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("shop_id", user.id);

      showToastMessage("Uploading sales data...", "bi bi-upload");
      const response = await api.post("/shop/upload_sales_data", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.status === "success") {
        showToastMessage(
          "Sales data uploaded successfully!",
          "bi bi-check-circle-fill"
        );
        setTimeout(() => window.location.reload(), 1200);
      } else {
        showToastMessage(
          response.data.message || "Upload failed.",
          "bi bi-exclamation-triangle"
        );
      }
    } catch (err) {
      console.error("Upload Error:", err);
      showToastMessage("Error uploading file.", "bi bi-exclamation-triangle");
    }
  };
};

// ---------------------------------------------
// 📤 Report Export Logic
// ---------------------------------------------
const exportReport = async () => {
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || !user.id) {
      showToastMessage(
        "User not found. Please log in again.",
        "bi bi-exclamation-triangle"
      );
      return;
    }

    showToastMessage("Generating report...", "bi bi-download");

    const response = await api.get("/shop/sales/export", {
      params: { shop_id: user.id },
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "sales_report.csv");
    document.body.appendChild(link);
    link.click();

    showToastMessage(
      "Report downloaded successfully!",
      "bi bi-check-circle-fill"
    );
  } catch (err) {
    console.error("Export Error:", err);
    showToastMessage("Failed to export report.", "bi bi-exclamation-triangle");
  }
};

// ---------------------------------------------
// 🔧 Other existing methods
// ---------------------------------------------
const viewSalesReport = () =>
  showToastMessage(
    "Opening detailed sales report...",
    "bi bi-file-earmark-bar-graph"
  );
const viewDetailedChart = () =>
  showToastMessage("Opening chart analytics...", "bi bi-graph-up");
const viewForecastDetails = (f) =>
  showToastMessage(
    `Viewing ${f.name} forecast details`,
    "bi bi-calendar-check"
  );
const applyInsight = (i) =>
  showToastMessage(`Applied: ${i.title}`, "bi bi-check-circle-fill");
const viewAllSuggestions = () =>
  showToastMessage("Loading all suggestions...", "bi bi-grid-3x3-gap");

const scrollCarousel = (dir) => {
  const track = carouselTrack.value;
  const scrollAmount = 280;
  if (!track) return;
  track.scrollLeft += dir === "left" ? -scrollAmount : scrollAmount;
  updateArrows();
};
const updateArrows = () => {
  const track = carouselTrack.value;
  if (track) {
    showLeftArrow.value = track.scrollLeft > 0;
    showRightArrow.value =
      track.scrollLeft < track.scrollWidth - track.clientWidth - 10;
  }
};

const quickView = (p) => {
  selectedProduct.value = p;
  showQuickView.value = true;
};
const closeQuickView = () => {
  showQuickView.value = false;
  selectedProduct.value = null;
};
const addToCart = (p) =>
  showToastMessage(`${p.name} added to cart!`, "bi bi-cart-check-fill");

// ---------------------------------------------
// 🔍 Catalog Filters (Dynamic Buttons)
// ---------------------------------------------
const selectFilter = async (id) => {
  selectedFilter.value = id;
  const f = productFilters.value.find((f) => f.id === id);
  showToastMessage(`Filter applied: ${f.label}`, "bi bi-funnel-fill");

  try {
    let params = {};
    if (id === "category") params.category = "Apparel";
    else if (id === "price") params.keyword = "Jeans";
    else if (id === "brand") params.keyword = "Turtle";

    // If "All" selected, fetch default view
    const endpoint =
      id === "all"
        ? "/view?limit=12"
        : "/search";

    const response = await catalogApi.get(endpoint, { params });
    catalog.value = (response.data.products || response.data || []).map(
      (item) => ({
        ...item,
        image_url: item.image_url.startsWith("http")
          ? item.image_url
          : `http://127.0.0.1:5001${item.image_url}`,
      })
    );
  } catch (err) {
    console.error("Filter Error:", err);
    showToastMessage("Failed to filter products.", "bi bi-exclamation-triangle");
  }
};

const showTooltip = (point) => console.log("Sales:", point.value);
const hideTooltip = () => console.log("Hide tooltip");

// ---------------------------------------------
// 🚀 Backend Sync Logic
// ---------------------------------------------
onMounted(async () => {
  updateArrows();

  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || !user.id) {
      showToastMessage(
        "User not found. Please log in again.",
        "bi bi-exclamation-triangle"
      );
      return;
    }

    const response = await api.get("/shop/dashboard", {
      params: { shop_id: user.id },
    });

    if (response.data.status === "success" && response.data.data) {
      const data = response.data.data;

      metrics.value[0].value = data.weekly_sales || "₹0";
      metrics.value[1].value = String(data.pending_reorders ?? "0");
      metrics.value[2].value = String(data.total_orders ?? "0");
      metrics.value[3].value = String(data.customer_rating ?? "0");

      aiInsights.value = data.ai_insights || [];
      reorderProducts.value = data.reorder_suggestions || [];

      chartPoints.value = (data.trend_chart || []).map((item, idx) => ({
        x: idx * 50,
        y: 200 - item.revenue / 100,
        value: item.revenue,
      }));
    } else {
      showToastMessage(
        response.data.message || "Failed to load dashboard data."
      );
    }
  } catch (err) {
    console.error("Dashboard Error:", err);
    showToastMessage(
      "Unable to fetch dashboard data.",
      "bi bi-exclamation-triangle"
    );
  }

  // ✅ Load initial catalog products
  try {
    const catalogRes = await catalogApi.get("/view?limit=12");
    catalog.value = (catalogRes.data || []).map((item) => ({
      ...item,
      image_url: item.image_url.startsWith("http")
        ? item.image_url
        : `http://127.0.0.1:5001${item.image_url}`,
    }));
  } catch (error) {
    console.error("Catalog Fetch Error:", error);
    catalog.value = [];
  } finally {
    catalogLoading.value = false;
  }
});
</script>


<style scoped>
/* ===== Base Styles ===== */
.shop-dashboard-tab {
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

/* ===== Card Styles ===== */
.card {
  border-radius: 16px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.modern-card {
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h6.card-title {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

/* ===== Hero Header ===== */
.dashboard-hero {
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.1) 0%,
    rgba(118, 75, 162, 0.1) 100%
  );
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.hero-title {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  margin: 0;
}

.hero-subtitle {
  color: #6c757d;
  font-size: 0.95rem;
}

/* ===== Buttons ===== */
.btn-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.btn-gradient:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #5568d3 0%, #65408b 100%);
  color: white;
}

.btn-outline-gradient {
  border: 1.5px solid #667eea;
  background: transparent;
  color: #667eea;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.btn-outline-gradient:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* ===== Metric Cards ===== */
.metric-card {
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: "";
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

.metric-card:hover::before {
  transform: scaleX(1);
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.08);
}

.metric-label {
  color: #6c757d;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.75rem;
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.metric-change {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
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
.bg-success-soft {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #059669;
}

.bg-warning-soft {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #d97706;
}

.bg-primary-soft {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #2563eb;
}

.bg-info-soft {
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  color: #0284c7;
}

.bg-danger-soft {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #dc2626;
}

/* ===== Sales Summary ===== */
.summary-content {
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 100%
  );
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
}

.summary-item i {
  font-size: 1.2rem;
}

.stat-box {
  background: white;
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* ===== Chart ===== */
.chart-placeholder {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-radius: 12px;
  padding: 1.5rem 1rem 0.5rem 1rem;
}

.chart-path {
  cursor: pointer;
  transition: all 0.3s ease;
}

.chart-area {
  pointer-events: none;
}

.chart-point {
  cursor: pointer;
  transition: all 0.3s ease;
}

.chart-point:hover {
  r: 8;
  filter: drop-shadow(0 2px 8px rgba(102, 126, 234, 0.5));
}

/* ===== Forecast Section ===== */
.forecast-container {
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 100%
  );
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 12px;
}

.forecast-item {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 1rem;
  border-radius: 12px;
}

.forecast-item:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.forecast-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.forecast-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  display: inline-block;
}

.trend-up {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.trend-stable {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.trend-down {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

/* ===== AI Insights ===== */
.ai-insights-card {
  background: white;
}

.insight-item {
  padding: 1rem;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.03) 0%,
    rgba(118, 75, 162, 0.03) 100%
  );
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.insight-item:hover {
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.insight-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

/* ===== Carousel ===== */
.reorder-carousel {
  position: relative;
}

.carousel-track {
  display: flex;
  gap: 1.5rem;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding: 1rem 0;
  scrollbar-width: thin;
  scrollbar-color: #667eea #f1f1f1;
}

.carousel-track::-webkit-scrollbar {
  height: 8px;
}

.carousel-track::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.carousel-track::-webkit-scrollbar-thumb {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
}

.carousel-track::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(90deg, #5568d3 0%, #65408b 100%);
}

.carousel-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.carousel-nav-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-50%) scale(1.1);
}

.carousel-nav-btn.prev {
  left: -20px;
}

.carousel-nav-btn.next {
  right: -20px;
}

/* ===== Reorder Product Cards ===== */
.reorder-card {
  min-width: 260px;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.reorder-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
}

.product-image-wrapper {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.3s ease;
}

.reorder-card:hover .product-image {
  transform: scale(1.1);
}

.product-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  padding: 0.35rem 0.65rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.product-details {
  background: white;
  padding: 1rem;
}

.product-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.product-supplier {
  font-size: 0.8rem;
  color: #6c757d;
  margin-bottom: 0.75rem;
}

.product-quantity,
.product-price {
  font-size: 0.875rem;
  font-weight: 600;
}

.product-price {
  color: #667eea;
}

.product-sku {
  font-size: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* ===== Filter Chips ===== */
.filter-chip {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  border: 1.5px solid #e9ecef;
  background: white;
  color: #6c757d;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-chip:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
}

.filter-chip.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* ===== Products Grid ===== */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.product-grid-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.product-grid-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
}

.product-grid-image {
  position: relative;
  width: 100%;
  height: 220px;
  overflow: hidden;
}

.product-grid-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.3s ease;
}

.product-grid-card:hover .product-grid-image img {
  transform: scale(1.1);
}

.product-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
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
  top: 10px;
  left: 10px;
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
}

.product-grid-info {
  background: white;
  padding: 1rem;
}

.product-grid-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.rating {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.product-description {
  font-size: 0.85rem;
  color: #6c757d;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.supplier-info strong,
.stock-info strong {
  color: #1f2937;
}

.product-grid-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.current-price {
  font-size: 1.25rem;
  font-weight: 700;
  color: #667eea;
}

.original-price {
  font-size: 0.875rem;
  color: #9ca3af;
  text-decoration: line-through;
  margin-left: 0.5rem;
}

/* ===== Quick View Modal ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 2rem;
}

.quick-view-modal {
  background: white;
  border-radius: 20px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 2rem;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideUp 0.3s ease-out;
}

@keyframes modalSlideUp {
  from {
    opacity: 0;
    transform: translateY(50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
}

.modal-close-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: rotate(90deg);
}

.price-large {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ===== Toast Notification ===== */
.toast-notification {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  z-index: 1100;
  animation: toastSlideIn 0.3s ease-out;
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateX(100px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* ===== Vue Transitions ===== */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .quick-view-modal,
.modal-fade-leave-to .quick-view-modal {
  transform: translateY(50px);
}

/* ===== Section Title ===== */
.section-title {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* ===== Responsive Design ===== */
@media (max-width: 768px) {
  .shop-dashboard-tab {
    padding: 1rem;
  }

  .carousel-nav-btn {
    display: none;
  }

  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }

  .dashboard-hero {
    padding: 1rem;
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
}
</style>

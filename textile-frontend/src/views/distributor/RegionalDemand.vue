<template>
  <div class="regional-demand-page">
    <!-- Header with Filters -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h5 class="mb-0">
        <i class="bi bi-bar-chart-fill me-2"></i> Regional Demand Analysis
      </h5>
      <button class="btn btn-success">
        <i class="bi bi-download me-2"></i> Download Full Report (PDF)
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
            <label class="small text-muted mb-1" for="filter-date-picker"
              >Date Picker</label
            >
            <select
              id="filter-date-picker"
              class="form-select form-select-sm"
              v-model="selectedMonth"
            >
              <option value="November 2025">November 2025</option>
              <option value="October 2025">October 2025</option>
              <option value="September 2025">September 2025</option>
            </select>
          </div>

          <div class="filter-group">
            <label class="small text-muted mb-1" for="filter-location"
              >Location</label
            >
            <button
              id="filter-location"
              class="btn btn-outline-secondary btn-sm"
              type="button"
            >
              <i class="bi bi-geo-alt-fill me-1"></i> All Regions
            </button>
          </div>

          <div class="filter-group">
            <label class="small text-muted mb-1" for="filter-time-period"
              >Time Period</label
            >
            <select
              id="filter-time-period"
              class="form-select form-select-sm"
              v-model="timePeriod"
            >
              <option value="Monthly">Monthly</option>
              <option value="Quarterly">Quarterly</option>
              <option value="Yearly">Yearly</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- AI-Generated Summary -->
    <div class="card ai-summary-card mb-4">
      <div class="card-body">
        <h6 class="mb-3">
          <i class="bi bi-stars me-2"></i>AI-Generated Summary for November 2025
        </h6>
        <div class="summary-content">
          <div class="summary-highlight">
            <i class="bi bi-graph-up-arrow"></i>
            <p class="mb-0">
              Demand for <strong>Handwoven Silk Brocade</strong> in the
              <strong>Northern Region</strong> surged by
              <span class="highlight-number">32%</span> this month, primarily
              driven by festive season purchases and wedding ceremonies.
              <strong>Premium Cotton Batik</strong> continues to show strong
              performance with consistent growth across all metropolitan areas.
            </p>
          </div>
          <div class="summary-recommendation">
            <i class="bi bi-lightbulb-fill"></i>
            <p class="mb-0">
              <strong>Recommendation:</strong> Increase inventory of silk-based
              fabrics and traditional designs for retailers in Northern and
              Eastern regions. Consider promotional campaigns for Georgette
              collections to capitalize on the upcoming party season.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Top 5 Trending Products -->
    <div class="card mb-4">
      <div class="card-body">
        <h6 class="mb-3">
          <i class="bi bi-fire me-2"></i>Top 5 Trending Products in Selected
          Regions
        </h6>

        <div class="row g-3">
          <div
            v-for="(product, idx) in topProducts"
            :key="idx"
            class="col-md-6"
          >
            <div class="product-chart-card">
              <div class="row g-0">
                <!-- Left Side: Image and Details -->
                <div class="col-5 d-flex flex-column">
                  <div class="product-image-wrapper">
                    <img
                      :src="product.image"
                      :alt="product.name"
                      class="product-image"
                    />
                    <div class="rank-badge">#{{ idx + 1 }}</div>
                  </div>
                  <div class="product-details-left mt-auto pt-3">
                    <strong class="product-name">{{ product.name }}</strong>
                    <div class="growth-tag">
                      <i class="bi bi-arrow-up"></i> {{ product.growth }}
                    </div>
                    <div class="region-info">
                      <i class="bi bi-geo-alt-fill"></i> {{ product.region }}
                    </div>
                    <div class="sales-info">
                      <span class="label">Sales Volume</span>
                      <span class="value">{{ product.volume }}</span>
                    </div>
                  </div>
                </div>

                <!-- Right Side: Chart -->
                <div class="col-7">
                  <div class="chart-section">
                    <div class="chart-header">
                      <h6 class="chart-title">Weekly Demand Trend</h6>
                      <span class="chart-subtitle">Last 4 Weeks</span>
                    </div>
                    <div class="bar-chart">
                      <div style="height: 200px">
                        <Bar
                          :data="getChartData(product.chartData)"
                          :options="getChartOptions()"
                        />
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

    <!-- Bottom Section: Demand by Category & Heatmap -->
    <div class="row g-3">
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h6 class="mb-3">
              <i class="bi bi-pie-chart-fill me-2"></i>Demand by Category
            </h6>
            <div
              class="chart-container d-flex justify-content-center align-items-center"
              style="height: 280px"
            >
              <!-- Enhanced Donut Chart SVG -->
              <svg viewBox="0 0 240 240" width="240" height="240">
                <defs>
                  <linearGradient
                    id="gradSilk2"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      style="stop-color: #667eea; stop-opacity: 1"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #764ba2; stop-opacity: 1"
                    />
                  </linearGradient>
                  <linearGradient
                    id="gradCotton2"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      style="stop-color: #f093fb; stop-opacity: 1"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #f5576c; stop-opacity: 1"
                    />
                  </linearGradient>
                  <linearGradient
                    id="gradGeorgette2"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      style="stop-color: #4facfe; stop-opacity: 1"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #00f2fe; stop-opacity: 1"
                    />
                  </linearGradient>
                  <linearGradient
                    id="gradOthers2"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop
                      offset="0%"
                      style="stop-color: #43e97b; stop-opacity: 1"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #38f9d7; stop-opacity: 1"
                    />
                  </linearGradient>
                </defs>
                <!-- Silk - 38% -->
                <path
                  d="M 120 120 L 120 30 A 90 90 0 0 1 205 88 Z"
                  fill="url(#gradSilk2)"
                  class="pie-slice"
                />
                <!-- Cotton - 32% -->
                <path
                  d="M 120 120 L 205 88 A 90 90 0 0 1 195 172 Z"
                  fill="url(#gradCotton2)"
                  class="pie-slice"
                />
                <!-- Georgette - 22% -->
                <path
                  d="M 120 120 L 195 172 A 90 90 0 0 1 50 165 Z"
                  fill="url(#gradGeorgette2)"
                  class="pie-slice"
                />
                <!-- Others - 8% -->
                <path
                  d="M 120 120 L 50 165 A 90 90 0 0 1 120 30 Z"
                  fill="url(#gradOthers2)"
                  class="pie-slice"
                />
                <!-- Center circle -->
                <circle cx="120" cy="120" r="50" fill="white" />
                <text
                  x="120"
                  y="115"
                  text-anchor="middle"
                  font-size="14"
                  font-weight="600"
                  fill="#4a5568"
                >
                  Demand
                </text>
                <text
                  x="120"
                  y="135"
                  text-anchor="middle"
                  font-size="18"
                  font-weight="700"
                  fill="#667eea"
                >
                  92.5K
                </text>
              </svg>
            </div>
            <div class="legend-container mt-3">
              <div class="legend-item">
                <span
                  class="legend-color"
                  style="
                    background: linear-gradient(
                      135deg,
                      #667eea 0%,
                      #764ba2 100%
                    );
                  "
                ></span>
                <span class="legend-label">Silk Fabrics (38%)</span>
              </div>
              <div class="legend-item">
                <span
                  class="legend-color"
                  style="
                    background: linear-gradient(
                      135deg,
                      #f093fb 0%,
                      #f5576c 100%
                    );
                  "
                ></span>
                <span class="legend-label">Cotton Fabrics (32%)</span>
              </div>
              <div class="legend-item">
                <span
                  class="legend-color"
                  style="
                    background: linear-gradient(
                      135deg,
                      #4facfe 0%,
                      #00f2fe 100%
                    );
                  "
                ></span>
                <span class="legend-label">Georgette (22%)</span>
              </div>
              <div class="legend-item">
                <span
                  class="legend-color"
                  style="
                    background: linear-gradient(
                      135deg,
                      #43e97b 0%,
                      #38f9d7 100%
                    );
                  "
                ></span>
                <span class="legend-label">Others (8%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h6 class="mb-3">
              <i class="bi bi-map-fill me-2"></i>Regional Demand Heatmap
            </h6>
            <div class="heatmap-container position-relative">
              <!-- Enhanced Gradient Heatmap with SVG -->
              <svg
                viewBox="0 0 400 280"
                class="heatmap-svg"
                style="width: 100%; height: 280px"
              >
                <defs>
                  <radialGradient id="hotspot1" cx="50%" cy="50%">
                    <stop
                      offset="0%"
                      style="stop-color: #ef4444; stop-opacity: 0.8"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #ef4444; stop-opacity: 0"
                    />
                  </radialGradient>
                  <radialGradient id="hotspot2" cx="50%" cy="50%">
                    <stop
                      offset="0%"
                      style="stop-color: #f59e0b; stop-opacity: 0.7"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #f59e0b; stop-opacity: 0"
                    />
                  </radialGradient>
                  <radialGradient id="hotspot3" cx="50%" cy="50%">
                    <stop
                      offset="0%"
                      style="stop-color: #10b981; stop-opacity: 0.6"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #10b981; stop-opacity: 0"
                    />
                  </radialGradient>
                  <radialGradient id="hotspot4" cx="50%" cy="50%">
                    <stop
                      offset="0%"
                      style="stop-color: #3b82f6; stop-opacity: 0.7"
                    />
                    <stop
                      offset="100%"
                      style="stop-color: #3b82f6; stop-opacity: 0"
                    />
                  </radialGradient>
                </defs>
                <!-- Background -->
                <rect width="400" height="280" fill="#f3f4f6" rx="12" />
                <!-- Hotspots -->
                <circle cx="100" cy="80" r="60" fill="url(#hotspot1)" />
                <circle cx="300" cy="70" r="50" fill="url(#hotspot2)" />
                <circle cx="280" cy="200" r="55" fill="url(#hotspot3)" />
                <circle cx="90" cy="220" r="50" fill="url(#hotspot4)" />
              </svg>

              <!-- Location Labels -->
              <div class="heatmap-labels">
                <div
                  class="location-label high"
                  style="position: absolute; top: 20%; left: 15%"
                >
                  <div class="label-name">Northern Region</div>
                  <div class="label-metric">High Demand</div>
                </div>
                <div
                  class="location-label medium"
                  style="position: absolute; top: 15%; right: 15%"
                >
                  <div class="label-name">Eastern Region</div>
                  <div class="label-metric">Medium-High</div>
                </div>
                <div
                  class="location-label moderate"
                  style="position: absolute; bottom: 22%; right: 18%"
                >
                  <div class="label-name">Southern Region</div>
                  <div class="label-metric">Moderate</div>
                </div>
                <div
                  class="location-label medium"
                  style="position: absolute; bottom: 18%; left: 12%"
                >
                  <div class="label-name">Western Region</div>
                  <div class="label-metric">Medium</div>
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
import { ref } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

const selectedMonth = ref("November 2025");
const timePeriod = ref("Monthly");

const topProducts = ref([
  {
    name: "Handwoven Silk Brocade",
    image:
      "https://images.unsplash.com/photo-1591176134674-87e8f7c73ce9?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
    growth: "+32% MoM",
    region: "Northern Region",
    volume: "2,850 m",
    chartData: [30, 50, 70, 95], // Dramatic upward trend
  },
  {
    name: "Premium Cotton Batik",
    image:
      "https://images.unsplash.com/photo-1642779978153-f5ed67cdecb2?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
    growth: "+28% MoM",
    region: "Eastern Region",
    volume: "3,420 m",
    chartData: [85, 90, 75, 95], // High with dip pattern
  },
  {
    name: "Luxury Georgette Floral",
    image:
      "https://images.unsplash.com/photo-1729772164459-6dbe32e20510?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
    growth: "+24% MoM",
    region: "Southern Region",
    volume: "2,180 m",
    chartData: [25, 40, 60, 85], // Aggressive growth curve
  },
  {
    name: "Designer Silk Collection",
    image:
      "https://images.unsplash.com/photo-1636545787095-8aa7e737f74e?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
    growth: "+22% MoM",
    region: "Western Region",
    volume: "1,920 m",
    chartData: [70, 45, 65, 80], // V-shaped recovery
  },
  {
    name: "Traditional Block Print",
    image:
      "https://images.unsplash.com/photo-1636545776450-32062836e1cd?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=400",
    growth: "+19% MoM",
    region: "Central Region",
    volume: "2,560 m",
    chartData: [55, 50, 70, 75], // Stable with moderate growth
  },
]);

const getChartOptions = () => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: "rgba(102, 126, 234, 0.9)",
      padding: 12,
      titleFont: {
        size: 13,
      },
      bodyFont: {
        size: 12,
      },
      callbacks: {
        label: function (context) {
          return `Demand: ${context.parsed.y}%`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: "#2d3748",
        font: {
          size: 11,
          weight: "700",
        },
      },
    },
    y: {
      display: false,
      beginAtZero: true,
      max: 100,
    },
  },
});

const getChartData = (chartData) => ({
  labels: ["W1", "W2", "W3", "W4"],
  datasets: [
    {
      data: chartData,
      backgroundColor: [
        "rgba(102, 126, 234, 0.8)",
        "rgba(118, 75, 162, 0.8)",
        "rgba(102, 126, 234, 0.8)",
        "rgba(118, 75, 162, 0.8)",
      ],
      borderColor: [
        "rgba(102, 126, 234, 1)",
        "rgba(118, 75, 162, 1)",
        "rgba(102, 126, 234, 1)",
        "rgba(118, 75, 162, 1)",
      ],
      borderWidth: 2,
      borderRadius: 4,
      barThickness: 35,
    },
  ],
});
</script>

<style scoped>
/* ===== Base Styles ===== */
.regional-demand-page {
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
h5,
h6 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* ===== Cards ===== */
.filters-card,
.card {
  border: none;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* ===== AI Summary Card ===== */
.ai-summary-card {
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 100%
  );
  border: 2px solid rgba(102, 126, 234, 0.15);
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.summary-highlight,
.summary-recommendation {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-radius: 12px;
  background: white;
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
}

.summary-highlight {
  border-left-color: #667eea;
}

.summary-recommendation {
  border-left-color: #f59e0b;
}

.summary-highlight:hover,
.summary-recommendation:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateX(3px);
}

.summary-highlight i {
  font-size: 1.5rem;
  color: #667eea;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.summary-recommendation i {
  font-size: 1.5rem;
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.summary-highlight p,
.summary-recommendation p {
  color: #4a5568;
  line-height: 1.6;
  font-size: 0.95rem;
}

.highlight-number {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  font-size: 1.1rem;
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

/* ===== Product Chart Cards ===== */
.product-chart-card {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  height: 100%;
  min-height: 280px;
}

.product-chart-card::before {
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

.product-chart-card:hover::before {
  transform: scaleX(1);
}

.product-chart-card:hover {
  box-shadow: 0 12px 28px rgba(102, 126, 234, 0.25);
  transform: translateY(-4px);
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

.product-chart-card:hover .product-image {
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Left side product details */
.product-details-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0 0.5rem;
}

.product-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #2d3748;
  line-height: 1.3;
  margin-bottom: 0.25rem;
}

.growth-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  width: fit-content;
}

.region-info {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #6b7280;
  font-size: 0.75rem;
}

.sales-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  border-radius: 6px;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(118, 75, 162, 0.05) 100%
  );
  border: 1px solid rgba(102, 126, 234, 0.1);
  font-size: 0.75rem;
}

.sales-info .label {
  color: #9ca3af;
  font-weight: 500;
}

.sales-info .value {
  color: #667eea;
  font-weight: 700;
  font-size: 0.9rem;
}

/* Right side chart section */
.chart-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0.5rem;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.02) 0%,
    rgba(118, 75, 162, 0.02) 100%
  );
  border-radius: 8px;
  border-left: 2px solid rgba(102, 126, 234, 0.1);
}

.chart-header {
  margin-bottom: 0.5rem;
  padding: 0 0.5rem;
  text-align: center;
}

.chart-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.chart-subtitle {
  font-size: 0.7rem;
  color: #9ca3af;
  font-weight: 500;
  display: block;
}

/* ===== Bar Chart ===== */
.bar-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  align-items: center;
}

/* Chart.js container styling */
.bar-chart > div {
  flex: 1;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.15);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.08);
}

/* ===== Pie Chart ===== */
.chart-container svg {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
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

/* ===== Heatmap ===== */
.heatmap-container {
  position: relative;
  height: 280px;
}

.heatmap-svg {
  border-radius: 12px;
}

.heatmap-labels {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.location-label {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  pointer-events: all;
  cursor: pointer;
}

.location-label:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

.location-label.high {
  border-left: 3px solid #ef4444;
}

.location-label.medium {
  border-left: 3px solid #f59e0b;
}

.location-label.moderate {
  border-left: 3px solid #10b981;
}

.label-name {
  font-weight: 700;
  color: #2d3748;
  font-size: 0.85rem;
  margin-bottom: 0.15rem;
}

.label-metric {
  font-size: 0.7rem;
  color: #6b7280;
  font-weight: 500;
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
  .regional-demand-page {
    padding: 1rem;
  }

  .legend-container {
    grid-template-columns: 1fr;
  }

  .d-flex.gap-3 {
    flex-wrap: wrap;
  }

  .summary-highlight,
  .summary-recommendation {
    flex-direction: column;
    gap: 0.5rem;
  }

  .summary-highlight i,
  .summary-recommendation i {
    font-size: 1.25rem;
  }
}
</style>

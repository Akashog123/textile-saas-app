<template>
  <div class="sales-line-chart">
    <Line
      v-if="chartData && chartData.labels?.length"
      :data="chartData"
      :options="chartOptions"
    />
    <div v-else class="d-flex align-items-center justify-content-center h-100">
      <span class="text-muted">No data available</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'vue-chartjs';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const props = defineProps({
  labels: {
    type: Array,
    default: () => []
  },
  dataPoints: {
    type: Array,
    default: () => []
  },
  trend: {
    type: String,
    default: 'up' // 'up', 'down', 'flat'
  },
  period: {
    type: String,
    default: 'weekly'
  },
  height: {
    type: Number,
    default: 220
  }
});

// Define color based on trend
const trendColor = computed(() => {
  if (props.trend === 'down') return '#ef4444'; // red
  if (props.trend === 'up') return '#10b981'; // green
  return '#3b82f6'; // blue (primary)
});

const trendColorLight = computed(() => {
  if (props.trend === 'down') return 'rgba(239, 68, 68, 0.1)';
  if (props.trend === 'up') return 'rgba(16, 185, 129, 0.1)';
  return 'rgba(59, 130, 246, 0.1)';
});

// Chart data configuration
const chartData = computed(() => {
  if (!props.labels?.length || !props.dataPoints?.length) {
    return null;
  }

  // Extract values from data points
  const values = props.dataPoints.map(p => p.value ?? p);

  return {
    labels: props.labels,
    datasets: [
      {
        label: 'Revenue',
        data: values,
        fill: true,
        backgroundColor: (context) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, props.height);
          gradient.addColorStop(0, trendColorLight.value);
          gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
          return gradient;
        },
        borderColor: trendColor.value,
        borderWidth: 3,
        tension: 0.4,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: trendColor.value,
        pointBorderWidth: 3,
        pointRadius: 5,
        pointHoverRadius: 8,
        pointHoverBorderWidth: 4,
        pointHoverBackgroundColor: '#ffffff',
        pointHoverBorderColor: trendColor.value
      }
    ]
  };
});

// Chart options configuration
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      enabled: true,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      titleFont: {
        size: 12,
        weight: 'bold'
      },
      bodyFont: {
        size: 12
      },
      padding: 12,
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: false,
      callbacks: {
        title: (tooltipItems) => {
          const index = tooltipItems[0]?.dataIndex;
          const point = props.dataPoints[index];
          return point?.label || tooltipItems[0]?.label || '';
        },
        label: (context) => {
          const index = context.dataIndex;
          const point = props.dataPoints[index];
          if (point?.value_formatted) {
            return point.value_formatted;
          }
          const value = context.parsed.y;
          return `₹${value.toLocaleString('en-IN')}`;
        }
      }
    }
  },
  scales: {
    x: {
      display: true,
      grid: {
        display: false
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: props.period === 'monthly' ? 10 : 11
        },
        maxRotation: 0,
        autoSkip: true,
        maxTicksLimit: props.period === 'monthly' ? 10 : props.period === 'yearly' ? 12 : 7
      },
      border: {
        display: false
      }
    },
    y: {
      display: true,
      position: 'left',
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
        drawBorder: false
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 10
        },
        callback: (value) => {
          if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
          if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
          if (value >= 1000) return `₹${(value / 1000).toFixed(0)}T`;
          return `₹${value}`;
        },
        maxTicksLimit: 5
      },
      border: {
        display: false
      },
      beginAtZero: true
    }
  },
  animation: {
    duration: 1000,
    easing: 'easeOutQuart'
  },
  elements: {
    line: {
      capBezierPoints: true
    }
  }
}));
</script>

<style scoped>
.sales-line-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>

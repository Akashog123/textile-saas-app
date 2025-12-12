<template>
  <div class="daily-bar-chart">
    <Bar
      v-if="chartData && chartData.labels?.length"
      :data="chartData"
      :options="chartOptions"
    />
    <div v-else class="d-flex align-items-center justify-content-center h-100">
      <span class="text-muted small">No data available</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'vue-chartjs';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const props = defineProps({
  dailyData: {
    type: Array,
    default: () => []
  },
  height: {
    type: Number,
    default: 80
  }
});

// Format values using Indian number system (Lakhs and Crores)
const formatIndianNumber = (value) => {
  if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(0)}k`;
  return `₹${value}`;
};

// Chart data configuration
const chartData = computed(() => {
  if (!props.dailyData?.length) {
    return null;
  }

  const labels = props.dailyData.map(d => d.day_name?.substring(0, 2) || '');
  const values = props.dailyData.map(d => d.revenue ?? 0);

  return {
    labels,
    datasets: [
      {
        label: 'Revenue',
        data: values,
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        hoverBackgroundColor: 'rgba(59, 130, 246, 0.9)',
        borderRadius: 4,
        borderSkipped: false,
        barPercentage: 0.7,
        categoryPercentage: 0.8
      }
    ]
  };
});

// Chart options configuration
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
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
        size: 11,
        weight: 'bold'
      },
      bodyFont: {
        size: 11
      },
      padding: 8,
      cornerRadius: 6,
      displayColors: false,
      callbacks: {
        title: (tooltipItems) => {
          const index = tooltipItems[0]?.dataIndex;
          const day = props.dailyData[index];
          return day?.day_name || tooltipItems[0]?.label || '';
        },
        label: (context) => {
          const index = context.dataIndex;
          const day = props.dailyData[index];
          if (day?.revenue_formatted) {
            return day.revenue_formatted;
          }
          const value = context.parsed.y;
          return formatIndianNumber(value);
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
          size: 9,
          weight: '500'
        },
        textTransform: 'uppercase'
      },
      border: {
        display: false
      }
    },
    y: {
      display: true,
      position: 'left',
      grid: {
        display: false
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 9
        },
        callback: (value) => {
          if (value >= 10000000) return `${(value / 10000000).toFixed(1)}Cr`;
          if (value >= 100000) return `${(value / 100000).toFixed(1)}L`;
          if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
          return value;
        },
        maxTicksLimit: 3
      },
      border: {
        display: false
      },
      beginAtZero: true
    }
  },
  animation: {
    duration: 800,
    easing: 'easeOutQuart'
  }
}));
</script>

<style scoped>
.daily-bar-chart {
  width: 100%;
  height: 100%;
  min-height: 70px;
}
</style>

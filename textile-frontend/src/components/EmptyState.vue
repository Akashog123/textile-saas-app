<template>
  <div class="empty-state-container" :class="[variant, { 'compact': compact }]">
    <div class="empty-state-icon" :class="iconColorClass">
      <i :class="iconClass"></i>
    </div>
    <h5 class="empty-state-title" v-if="title">{{ title }}</h5>
    <p class="empty-state-message" v-if="message">{{ message }}</p>
    <slot name="action">
      <button 
        v-if="actionText" 
        class="btn empty-state-btn"
        :class="actionButtonClass"
        @click="$emit('action')"
      >
        <i v-if="actionIcon" :class="actionIcon" class="me-2"></i>
        {{ actionText }}
      </button>
    </slot>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  // Icon to display (Bootstrap Icons class)
  icon: {
    type: String,
    default: 'bi-inbox'
  },
  // Title text
  title: {
    type: String,
    default: ''
  },
  // Descriptive message
  message: {
    type: String,
    default: 'No data available'
  },
  // Action button text (if provided, shows button)
  actionText: {
    type: String,
    default: ''
  },
  // Action button icon
  actionIcon: {
    type: String,
    default: ''
  },
  // Visual variant: 'default', 'warning', 'info', 'subtle'
  variant: {
    type: String,
    default: 'default'
  },
  // Compact mode for smaller spaces
  compact: {
    type: Boolean,
    default: false
  }
});

defineEmits(['action']);

const iconClass = computed(() => {
  return `bi ${props.icon}`;
});

const iconColorClass = computed(() => {
  switch (props.variant) {
    case 'warning':
      return 'icon-warning';
    case 'info':
      return 'icon-info';
    case 'subtle':
      return 'icon-subtle';
    default:
      return 'icon-default';
  }
});

const actionButtonClass = computed(() => {
  switch (props.variant) {
    case 'warning':
      return 'btn-outline-warning';
    case 'info':
      return 'btn-outline-primary';
    default:
      return 'btn-outline-secondary';
  }
});
</script>

<style scoped>
.empty-state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 2rem;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px dashed #dee2e6;
}

.empty-state-container.compact {
  padding: 1.5rem 1rem;
}

.empty-state-container.warning {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
  border-color: #ffc107;
}

.empty-state-container.info {
  background: linear-gradient(135deg, #e7f3ff 0%, #cce5ff 100%);
  border-color: #0d6efd;
}

.empty-state-container.subtle {
  background: transparent;
  border: none;
  padding: 2rem 1rem;
}

.empty-state-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.7;
}

.empty-state-container.compact .empty-state-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.icon-default {
  color: #6c757d;
}

.icon-warning {
  color: #856404;
}

.icon-info {
  color: #0d6efd;
}

.icon-subtle {
  color: #adb5bd;
}

.empty-state-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

.empty-state-container.compact .empty-state-title {
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.empty-state-message {
  color: #6c757d;
  margin-bottom: 1.5rem;
  max-width: 400px;
  line-height: 1.5;
}

.empty-state-container.compact .empty-state-message {
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.empty-state-btn {
  border-radius: 8px;
  padding: 0.5rem 1.5rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.empty-state-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>

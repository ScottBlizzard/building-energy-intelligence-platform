<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['info', 'success', 'warning', 'error'].includes(value)
  }
});

const statusConfig = computed(() => {
  const configs = {
    info: {
      icon: 'ℹ️',
      class: 'status-info',
      background: 'rgba(15, 139, 141, 0.12)',
      border: 'rgba(15, 139, 141, 0.18)',
      color: 'var(--accent-deep)'
    },
    success: {
      icon: '✅',
      class: 'status-success',
      background: 'rgba(76, 175, 80, 0.12)',
      border: 'rgba(76, 175, 80, 0.18)',
      color: '#2e7d32'
    },
    warning: {
      icon: '⚠️',
      class: 'status-warning',
      background: 'rgba(255, 159, 28, 0.12)',
      border: 'rgba(255, 159, 28, 0.18)',
      color: '#8f5100'
    },
    error: {
      icon: '❌',
      class: 'status-error',
      background: 'rgba(244, 67, 54, 0.12)',
      border: 'rgba(244, 67, 54, 0.18)',
      color: '#c62828'
    }
  };
  return configs[props.type];
});
</script>

<template>
  <div 
    class="status-banner" 
    :class="[statusConfig.class, $attrs.class]"
    :style="{
      backgroundColor: statusConfig.background,
      borderColor: statusConfig.border,
      color: statusConfig.color
    }"
  >
    <span class="status-icon">{{ statusConfig.icon }}</span>
    <span class="status-text">{{ status }}</span>
  </div>
</template>

<style scoped>
.status-banner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid;
  font-size: 14px;
  white-space: nowrap;
}

.status-icon {
  font-size: 16px;
}

.status-text {
  font-weight: 500;
}

.status-info .status-icon,
.status-success .status-icon,
.status-warning .status-icon,
.status-error .status-icon {
  filter: grayscale(0.2);
}
</style>
<script setup>
defineProps({
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  text: {
    type: String,
    default: '加载中...'
  },
  showText: {
    type: Boolean,
    default: true
  }
});

const sizeMap = {
  small: { width: '20px', height: '20px', border: '2px' },
  medium: { width: '40px', height: '40px', border: '3px' },
  large: { width: '60px', height: '60px', border: '4px' }
};
</script>

<template>
  <div class="loading-spinner">
    <div 
      class="spinner" 
      :style="{
        width: sizeMap[size].width,
        height: sizeMap[size].height,
        borderWidth: sizeMap[size].border
      }"
    ></div>
    <p v-if="showText" class="loading-text">{{ text }}</p>
  </div>
</template>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.spinner {
  border: solid rgba(15, 139, 141, 0.2);
  border-top: solid var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin: 0;
  color: var(--ink-soft);
  font-size: 14px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
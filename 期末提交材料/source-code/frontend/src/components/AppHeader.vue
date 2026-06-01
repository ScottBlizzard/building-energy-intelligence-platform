<script setup>
defineProps({
  title: {
    type: String,
    default: "建筑能源智能管理与运维优化系统"
  },
  subtitle: {
    type: String,
    default: "Software Engineering Management Project"
  }
});
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <div class="header-brand">
        <span class="header-eyebrow">{{ subtitle }}</span>
        <h1 class="header-title">{{ title }}</h1>
      </div>
      <div class="header-actions">
        <slot name="actions"></slot>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.header-brand {
  flex: 1;
}

.header-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 12px;
  color: var(--accent-deep);
  margin-bottom: 8px;
}

.header-title {
  margin: 0;
  font-size: clamp(28px, 4vw, 48px);
  line-height: 1.1;
  max-width: 16ch;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: flex-end;
  }
}
</style>
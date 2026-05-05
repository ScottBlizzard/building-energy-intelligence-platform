<script setup>
import { computed } from 'vue';

const props = defineProps({
  tabs: {
    type: Array,
    required: true,
    validator: (tabs) => tabs.every(tab => tab.key && tab.label)
  },
  activeTab: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:activeTab']);

const activeTabIndex = computed(() => 
  props.tabs.findIndex(tab => tab.key === props.activeTab)
);

function selectTab(tabKey) {
  emit('update:activeTab', tabKey);
}
</script>

<template>
  <nav class="tab-navigation">
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="tab-button"
        :class="{ 'tab-button--active': activeTab === tab.key }"
        @click="selectTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="tab-indicator" :style="{ left: `${activeTabIndex * 120}px` }"></div>
  </nav>
</template>

<style scoped>
.tab-navigation {
  position: relative;
  margin-bottom: 24px;
}

.tab-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.tab-button {
  border: 1px solid rgba(20, 34, 48, 0.1);
  background: rgba(255, 255, 255, 0.78);
  color: var(--ink-soft);
  border-radius: 999px;
  padding: 12px 18px;
  font: inherit;
  cursor: pointer;
  transition: 160ms ease;
  min-width: 100px;
}

.tab-button:hover,
.tab-button--active {
  background: rgba(15, 139, 141, 0.12);
  color: var(--accent-deep);
  border-color: rgba(15, 139, 141, 0.18);
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  height: 3px;
  width: 100px;
  background: var(--accent);
  border-radius: 2px;
  transition: left 0.3s ease;
  margin-left: 10px;
}

@media (max-width: 768px) {
  .tab-bar {
    justify-content: center;
  }
  
  .tab-button {
    min-width: 80px;
    padding: 10px 14px;
  }
}
</style>
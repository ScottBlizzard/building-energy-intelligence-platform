<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({
  buildings: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['filterChange']);

const filters = reactive({
  buildingId: '',
  limit: 10
});

function applyFilters() {
  emit('filterChange', {
    building_id: filters.buildingId,
    limit: filters.limit
  });
}

function resetFilters() {
  filters.buildingId = '';
  filters.limit = 10;
  applyFilters();
}

watch(filters, () => {
  applyFilters();
}, { deep: true });
</script>

<template>
  <div class="filter-toolbar">
    <div class="filter-row">
      <label class="field-label">
        <span>建筑筛选</span>
        <select v-model="filters.buildingId" :disabled="loading">
          <option value="">全部建筑</option>
          <option 
            v-for="building in buildings" 
            :key="building.building_id" 
            :value="building.building_id"
          >
            {{ building.building_name }}
          </option>
        </select>
      </label>
      
      <label class="field-label field-label--small">
        <span>显示条数</span>
        <input 
          v-model.number="filters.limit" 
          type="number" 
          min="1" 
          max="50" 
          :disabled="loading"
        />
      </label>
      
      <div class="filter-actions">
        <button 
          class="primary-button" 
          type="button" 
          :disabled="loading"
          @click="applyFilters"
        >
          {{ loading ? "加载中..." : "刷新数据" }}
        </button>
        
        <button 
          class="secondary-button" 
          type="button" 
          :disabled="loading"
          @click="resetFilters"
        >
          重置
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-toolbar {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: end;
}

.field-label {
  display: grid;
  gap: 8px;
  min-width: 220px;
}

.field-label--small {
  min-width: 100px;
}

.field-label span {
  color: var(--ink-soft);
  font-size: 14px;
}

.field-label select,
.field-label input {
  width: 100%;
  border: 1px solid rgba(20, 34, 48, 0.12);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 14px;
  padding: 12px 14px;
  font: inherit;
  color: var(--ink-strong);
}

.field-label select:disabled,
.field-label input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.filter-actions {
  display: flex;
  gap: 10px;
  align-items: end;
}

.primary-button {
  border: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: white;
  padding: 12px 18px;
  font: inherit;
  cursor: pointer;
  min-height: 46px;
}

.secondary-button {
  border: 1px solid rgba(20, 34, 48, 0.12);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ink-soft);
  padding: 12px 18px;
  font: inherit;
  cursor: pointer;
  min-height: 46px;
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .field-label {
    min-width: auto;
  }
  
  .filter-actions {
    justify-content: stretch;
  }
  
  .primary-button,
  .secondary-button {
    flex: 1;
  }
}
</style>
<script setup>
import { computed } from "vue";

const props = defineProps({
  buildings: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  exporting: {
    type: Boolean,
    default: false
  },
  timeRange: {
    type: Object,
    default: () => ({ start: "", end: "" })
  }
});

const emit = defineEmits(["apply", "reset", "export"]);
const filters = defineModel("filters", {
  type: Object,
  default: () => ({
    buildingId: "",
    startTime: "",
    endTime: "",
    limit: 10
  })
});

const rangeHint = computed(() => {
  if (!props.timeRange?.start || !props.timeRange?.end) {
    return "当前未获取到可用时间范围";
  }
  return `当前数据范围：${props.timeRange.start.replace("T", " ")} 至 ${props.timeRange.end.replace("T", " ")}`;
});

function applyFilters() {
  emit("apply");
}

function resetFilters() {
  Object.assign(filters.value, {
    buildingId: "",
    startTime: "",
    endTime: "",
    limit: 10
  });
  emit("reset");
}

function exportRecords() {
  emit("export");
}
</script>

<template>
  <div class="filter-toolbar">
    <p class="filter-hint">{{ rangeHint }}</p>
    <div class="filter-row">
      <label class="field-label">
        <span>建筑筛选</span>
        <select v-model="filters.buildingId" :disabled="loading || exporting">
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
      
      <label class="field-label">
        <span>开始时间</span>
        <input
          v-model="filters.startTime"
          type="datetime-local"
          :min="timeRange.start || undefined"
          :max="timeRange.end || undefined"
          :disabled="loading || exporting"
        />
      </label>

      <label class="field-label">
        <span>结束时间</span>
        <input
          v-model="filters.endTime"
          type="datetime-local"
          :min="timeRange.start || undefined"
          :max="timeRange.end || undefined"
          :disabled="loading || exporting"
        />
      </label>

      <label class="field-label field-label--small">
        <span>显示条数</span>
        <input 
          v-model.number="filters.limit" 
          type="number" 
          min="1" 
          max="50" 
          :disabled="loading || exporting"
        />
      </label>
      
      <div class="filter-actions">
        <button 
          class="primary-button" 
          type="button" 
          :disabled="loading || exporting"
          @click="applyFilters"
        >
          {{ loading ? "加载中..." : "刷新数据" }}
        </button>
        
        <button 
          class="secondary-button" 
          type="button" 
          :disabled="loading || exporting"
          @click="resetFilters"
        >
          重置
        </button>

        <button
          class="secondary-button secondary-button--accent"
          type="button"
          :disabled="loading || exporting"
          @click="exportRecords"
        >
          {{ exporting ? "导出中..." : "导出 CSV" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-toolbar {
  margin-bottom: 20px;
}

.filter-hint {
  margin: 0 0 12px;
  color: var(--ink-soft);
  font-size: 13px;
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

.secondary-button--accent {
  border-color: rgba(15, 139, 141, 0.2);
  color: var(--accent-deep);
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
    flex-wrap: wrap;
  }
  
  .primary-button,
  .secondary-button {
    flex: 1;
  }
}
</style>

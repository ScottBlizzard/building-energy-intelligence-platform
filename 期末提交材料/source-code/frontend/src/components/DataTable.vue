<script setup>
defineProps({
  columns: {
    type: Array,
    default: () => []
  },
  rows: {
    type: Array,
    default: () => []
  },
  emptyText: {
    type: String,
    default: "暂无数据"
  },
  rowActionLabel: {
    type: String,
    default: ""
  }
});

const emit = defineEmits(["row-action"]);

function cellValue(row, column) {
  const value = row[column.key];
  if (value === undefined || value === null || value === "") {
    return "—";
  }
  return value;
}

function rowKey(row, index) {
  return (
    row.record_id ||
    row.work_order_id ||
    row.recommendation_id ||
    row.equipment_id ||
    `${row.building_id || row.building_name || "row"}-${row.floor_label || row.timestamp || index}-${row.zone_name || index}`
  );
}
</script>

<template>
  <div class="table-shell">
    <table v-if="rows.length" class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
          <th v-if="rowActionLabel">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in rows" :key="rowKey(row, index)">
          <td v-for="column in columns" :key="column.key">{{ cellValue(row, column) }}</td>
          <td v-if="rowActionLabel">
            <button class="row-action-button" type="button" @click="emit('row-action', row)">
              {{ rowActionLabel }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-panel">{{ emptyText }}</div>
  </div>
</template>

<style scoped>
.row-action-button {
  border: 0;
  border-radius: 999px;
  background: rgba(15, 139, 141, 0.12);
  color: #0b6770;
  cursor: pointer;
  font: inherit;
  padding: 6px 10px;
  white-space: nowrap;
}

.row-action-button:hover {
  background: rgba(15, 139, 141, 0.2);
}
</style>

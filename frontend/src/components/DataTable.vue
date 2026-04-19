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
  }
});
</script>

<template>
  <div class="table-shell">
    <table v-if="rows.length" class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.record_id || row.timestamp || row.building_id">
          <td v-for="column in columns" :key="column.key">{{ row[column.key] }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-panel">{{ emptyText }}</div>
  </div>
</template>


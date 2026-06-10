<template>
  <div class="budget-panel">
    <StatusBanner v-if="error" :status="error" type="warning" />

    <div class="budget-toolbar">
      <div class="budget-period">
        <label>
          <span>年份</span>
          <select v-model.number="selectedYear" @change="loadBudgetAnalysis">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </label>
        <label>
          <span>月份</span>
          <select v-model.number="selectedMonth" @change="loadBudgetAnalysis">
            <option v-for="m in 12" :key="m" :value="m">{{ m }} 月</option>
          </select>
        </label>
      </div>
      <div class="budget-actions">
        <button class="primary-button" type="button" :disabled="loading" @click="handleAutoGenerate">
          自动生成预算
        </button>
        <button class="secondary-button" type="button" :disabled="loading" @click="loadBudgetAnalysis">
          刷新数据
        </button>
      </div>
    </div>

    <div v-if="loading" class="data-loading">
      <LoadingSpinner text="正在加载预算数据..." />
    </div>

    <template v-else-if="analysis">
      <div class="budget-kpi-grid">
        <div class="budget-kpi-card">
          <span>本月总预算</span>
          <strong>{{ formatNumber(analysis.total_budget_kwh) }} kWh</strong>
        </div>
        <div class="budget-kpi-card">
          <span>本月实际用电</span>
          <strong :class="{ 'text-danger': analysis.total_execution_rate > 100 }">
            {{ formatNumber(analysis.total_actual_kwh) }} kWh
          </strong>
        </div>
        <div class="budget-kpi-card" :class="execRateClass">
          <span>预算执行率</span>
          <strong>{{ analysis.total_execution_rate }}%</strong>
        </div>
        <div class="budget-kpi-card" :class="projectedRateClass">
          <span>月末预测执行率</span>
          <strong>{{ analysis.total_projected_execution_rate }}%</strong>
        </div>
        <div class="budget-kpi-card">
          <span>超预算楼栋</span>
          <strong class="text-danger">{{ analysis.over_budget_count }} / {{ analysis.buildings.length }}</strong>
        </div>
      </div>

      <div class="budget-chart">
        <div class="budget-bar-header">
          <span>楼栋预算执行对比 · {{ selectedMonth }} 月</span>
          <span class="budget-bar-legend">
            <span class="legend-dot legend-dot--safe"></span>健康
            <span class="legend-dot legend-dot--warn"></span>预警
            <span class="legend-dot legend-dot--over"></span>超预算
          </span>
        </div>
        <div
          v-for="building in analysis.buildings"
          :key="building.building_id"
          class="budget-bar-row"
        >
          <div class="budget-bar-label">
            <strong>{{ building.building_name }}</strong>
            <span>{{ formatNumber(building.actual_kwh) }} / {{ formatNumber(building.budget_kwh) }} kWh</span>
          </div>
          <div class="budget-bar-subtitle">
            <span>已观测 {{ building.observed_days }} 天</span>
            <span>月末预测 {{ formatNumber(building.month_end_estimate_kwh) }} kWh · {{ building.projected_execution_rate }}%</span>
          </div>
          <div class="budget-bar-track">
            <div
              class="budget-bar-fill"
              :class="`budget-bar-fill--${building.status}`"
              :style="{ width: `${Math.min(building.projected_execution_rate || building.execution_rate, 120)}%` }"
            ></div>
            <span class="budget-bar-pct">{{ building.projected_execution_rate }}%</span>
          </div>
        </div>
      </div>

      <div v-if="selectedKPI" class="kpi-detail">
        <SectionCard eyebrow="KPI Scorecard" :title="`${selectedKPI.building_name} · ${selectedKPI.year} 年度考核`" description="">
          <div class="kpi-header">
            <div class="kpi-grade" :class="`kpi-grade--${selectedKPI.grade}`">
              {{ selectedKPI.grade }}
            </div>
            <div class="kpi-summary">
              <div><span>综合评分</span><strong>{{ selectedKPI.average_score }} / 100</strong></div>
              <div><span>年度执行率</span><strong>{{ selectedKPI.overall_execution_rate }}%</strong></div>
              <div><span>COP 达标率</span><strong>{{ selectedKPI.cop_pass_rate }}%</strong></div>
              <div><span>异常响应及时率</span><strong>{{ selectedKPI.anomaly_response_timely_rate }}%</strong></div>
              <div><span>预算控制率</span><strong>{{ selectedKPI.budget_control_rate }}%</strong></div>
              <div><span>实际用电</span><strong>{{ formatNumber(selectedKPI.total_actual_kwh) }} kWh</strong></div>
            </div>
          </div>
          <div class="kpi-strengths">
            <strong>优势</strong>
            <ul>
              <li v-for="s in selectedKPI.strengths" :key="s">{{ s }}</li>
            </ul>
          </div>
          <div class="kpi-improvements">
            <strong>改进建议</strong>
            <ul>
              <li v-for="i in selectedKPI.improvements" :key="i">{{ i }}</li>
            </ul>
          </div>
          <div class="kpi-monthly">
            <strong>月度明细</strong>
            <table class="kpi-table">
              <thead>
                <tr>
                  <th>月份</th>
                  <th>预算 kWh</th>
                  <th>实际 kWh</th>
                  <th>执行率</th>
                  <th>预测执行率</th>
                  <th>COP达标率</th>
                  <th>异常数</th>
                  <th>评分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in selectedKPI.monthly_details" :key="m.month" :class="{ 'row-warn': m.execution_rate > 100 }">
                  <td>{{ m.month }} 月</td>
                  <td>{{ formatNumber(m.budget_kwh) }}</td>
                  <td>{{ formatNumber(m.actual_kwh) }}</td>
                  <td>{{ m.execution_rate }}%</td>
                  <td>{{ m.projected_execution_rate }}%</td>
                  <td>{{ m.cop_pass_rate }}%</td>
                  <td>{{ m.anomaly_count }}</td>
                  <td>{{ m.score }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      <div class="budget-set-form">
        <SectionCard eyebrow="Admin" title="预算调整" description="手动设置或调整楼栋月度预算目标。">
          <div class="budget-set-grid">
            <label>
              <span>楼栋</span>
              <select v-model="budgetForm.building_id">
                <option v-for="b in buildings" :key="b.building_id" :value="b.building_id">
                  {{ b.building_name }}
                </option>
              </select>
            </label>
            <label>
              <span>预算 (kWh)</span>
              <input v-model.number="budgetForm.budget_kwh" type="number" min="1000" step="1000" />
            </label>
            <label>
              <span>备注</span>
              <input v-model="budgetForm.note" type="text" placeholder="调整原因" />
            </label>
            <button class="primary-button" type="button" :disabled="loading" @click="handleSetBudget">
              保存预算
            </button>
          </div>
        </SectionCard>
      </div>
    </template>

    <EmptyState v-else icon="📊" title="暂无预算数据" description="请点击「自动生成预算」按钮或手动设置预算。" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import {
  fetchBudgetAnalysis,
  fetchBudgetKPI,
  generateBudgets,
  setBudget,
} from "../lib/api.js";
import SectionCard from "./SectionCard.vue";
import StatusBanner from "./StatusBanner.vue";
import LoadingSpinner from "./LoadingSpinner.vue";
import EmptyState from "./EmptyState.vue";

const props = defineProps({
  buildings: { type: Array, default: () => [] },
});

const selectedYear = ref(2026);
const selectedMonth = ref(6);
const loading = ref(false);
const error = ref("");
const analysis = ref(null);
const selectedKPI = ref(null);

const yearOptions = [2024, 2025, 2026, 2027];

const budgetForm = reactive({
  building_id: "BLD-A",
  budget_kwh: 80000,
  note: "",
});

const execRateClass = computed(() => {
  if (!analysis.value) return "";
  const rate = analysis.value.total_execution_rate;
  if (rate > 100) return "kpi-card--danger";
  if (rate > 85) return "kpi-card--warn";
  return "kpi-card--safe";
});

const projectedRateClass = computed(() => {
  if (!analysis.value) return "";
  const rate = analysis.value.total_projected_execution_rate;
  if (rate > 100) return "kpi-card--danger";
  if (rate > 85) return "kpi-card--warn";
  return "kpi-card--safe";
});

function formatNumber(val) {
  if (val == null) return "-";
  const num = Number(val);
  if (Number.isNaN(num)) return "-";
  return num.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

async function loadBudgetAnalysis() {
  loading.value = true;
  error.value = "";
  try {
    const result = await fetchBudgetAnalysis(selectedYear.value, selectedMonth.value);
    analysis.value = result.item;
    if (result.item.buildings.length && !selectedKPI.value) {
      await loadKPI(result.item.buildings[0].building_id);
    }
  } catch (e) {
    error.value = "预算数据加载失败，请确认后端服务可用。";
  } finally {
    loading.value = false;
  }
}

async function loadKPI(buildingId) {
  try {
    const result = await fetchBudgetKPI(buildingId, selectedYear.value);
    selectedKPI.value = result.item;
  } catch {
    selectedKPI.value = null;
  }
}

async function handleAutoGenerate() {
  loading.value = true;
  error.value = "";
  try {
    await generateBudgets(selectedYear.value, selectedMonth.value);
    await loadBudgetAnalysis();
  } catch {
    error.value = "自动生成预算失败。";
  } finally {
    loading.value = false;
  }
}

async function handleSetBudget() {
  loading.value = true;
  error.value = "";
  try {
    await setBudget({
      building_id: budgetForm.building_id,
      year: selectedYear.value,
      month: selectedMonth.value,
      budget_kwh: budgetForm.budget_kwh,
      note: budgetForm.note,
    });
    await loadBudgetAnalysis();
    budgetForm.note = "";
  } catch {
    error.value = "预算设置失败。";
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.buildings,
  (list) => {
    if (list.length && budgetForm.building_id === "BLD-A") {
      budgetForm.building_id = list[0].building_id;
    }
  },
  { immediate: true }
);

defineExpose({ loadBudgetAnalysis });

onMounted(() => {
  if (props.buildings.length) {
    loadBudgetAnalysis();
  }
});
</script>

<style scoped>
.budget-panel { display: grid; gap: 20px; }
.budget-toolbar {
  display: flex; justify-content: space-between; align-items: flex-end;
  flex-wrap: wrap; gap: 16px;
}
.budget-period { display: flex; gap: 12px; }
.budget-period select { padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(20,34,48,0.12); font: inherit; }
.budget-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.budget-kpi-grid {
  display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px;
}
.budget-kpi-card {
  background: rgba(255,255,255,0.92); border-radius: 16px; padding: 18px;
  box-shadow: 0 10px 28px rgba(20,34,48,0.06); text-align: center;
}
.budget-kpi-card span { color: var(--ink-soft); font-size: 13px; }
.budget-kpi-card strong { display: block; font-size: 22px; margin-top: 6px; }
.kpi-card--safe strong { color: #22a06b; }
.kpi-card--warn strong { color: #f39c12; }
.kpi-card--danger strong { color: #d9364f; }
.text-danger { color: #d9364f; }

.budget-chart {
  background: rgba(255,255,255,0.92); border-radius: 16px; padding: 20px;
  box-shadow: 0 10px 28px rgba(20,34,48,0.06);
}
.budget-bar-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; font-weight: 600;
}
.budget-bar-legend { display: flex; gap: 12px; font-size: 12px; font-weight: 400; color: var(--ink-soft); }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 4px; }
.legend-dot--safe { background: #22a06b; }
.legend-dot--warn { background: #f39c12; }
.legend-dot--over { background: #d9364f; }

.budget-bar-row { margin-bottom: 14px; }
.budget-bar-label { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px; }
.budget-bar-label strong { font-size: 14px; }
.budget-bar-subtitle {
  display: flex; justify-content: space-between; gap: 10px;
  color: var(--ink-soft); font-size: 12px; margin-bottom: 6px;
}
.budget-bar-track {
  position: relative; height: 22px; border-radius: 11px;
  background: rgba(20,34,48,0.05); overflow: hidden;
}
.budget-bar-fill {
  height: 100%; border-radius: 11px; transition: width 0.5s ease;
  min-width: 2px;
}
.budget-bar-fill--healthy { background: linear-gradient(90deg, #22a06b, #2ecc71); }
.budget-bar-fill--warning { background: linear-gradient(90deg, #f39c12, #f7c948); }
.budget-bar-fill--over { background: linear-gradient(90deg, #e74c3c, #d9364f); }
.budget-bar-pct {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  font-size: 11px; font-weight: 600; color: var(--ink-strong);
}

.kpi-detail { margin-top: 8px; }
.kpi-header { display: flex; gap: 24px; align-items: center; margin-bottom: 16px; }
.kpi-grade {
  width: 72px; height: 72px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; font-size: 34px; font-weight: 700;
  color: white;
}
.kpi-grade--A { background: linear-gradient(135deg, #22a06b, #2ecc71); }
.kpi-grade--B { background: linear-gradient(135deg, #0f8b8d, #1ec5a7); }
.kpi-grade--C { background: linear-gradient(135deg, #f39c12, #f7c948); }
.kpi-grade--D { background: linear-gradient(135deg, #e74c3c, #d9364f); }
.kpi-summary { display: grid; gap: 6px; flex: 1; }
.kpi-summary div { display: flex; justify-content: space-between; max-width: 320px; }
.kpi-summary span { color: var(--ink-soft); font-size: 13px; }
.kpi-summary strong { font-size: 18px; }
.kpi-strengths, .kpi-improvements { margin-bottom: 12px; }
.kpi-strengths strong, .kpi-improvements strong { color: var(--ink-strong); font-size: 14px; }
.kpi-strengths ul, .kpi-improvements ul { margin: 4px 0 0 16px; color: var(--ink-soft); font-size: 13px; }
.kpi-monthly strong { display: block; margin-bottom: 8px; }
.kpi-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.kpi-table th, .kpi-table td { padding: 8px 10px; border-bottom: 1px solid rgba(20,34,48,0.06); text-align: center; }
.kpi-table th { color: var(--ink-soft); font-weight: 500; }
.row-warn { background: rgba(249, 231, 159, 0.22); }

.budget-set-form { margin-top: 8px; }
.budget-set-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; align-items: end;
}
.budget-set-grid label { display: grid; gap: 6px; font-size: 13px; color: var(--ink-soft); }
.budget-set-grid select, .budget-set-grid input {
  padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(20,34,48,0.12);
  font: inherit; width: 100%;
}

.primary-button, .secondary-button {
  padding: 10px 18px; border-radius: 12px; font: inherit; cursor: pointer;
  border: 0; font-weight: 500;
}
.primary-button { background: linear-gradient(135deg, #0f8b8d, #1ec5a7); color: white; }
.secondary-button { background: rgba(20,34,48,0.06); color: var(--ink-strong); border: 1px solid rgba(20,34,48,0.1); }

.data-loading { display: flex; justify-content: center; padding: 40px; }

@media (max-width: 768px) {
  .budget-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .budget-set-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .budget-bar-subtitle { flex-direction: column; gap: 2px; }
}
</style>

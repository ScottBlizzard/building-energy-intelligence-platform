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
      <StatusBanner v-if="periodNote" :status="periodNote" :type="analysis.period_status === 'future' ? 'warning' : 'info'" />

      <template v-if="analysis.period_status !== 'future'">
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

      <div v-if="closureImpact" class="closure-impact-panel">
        <div>
          <span>Closure Impact</span>
          <strong>已关闭工单预算修正</strong>
          <p>{{ closureImpact.summary }}</p>
        </div>
        <div class="closure-impact-grid">
          <div>
            <span>减少预测电量</span>
            <strong>{{ formatNumber(closureImpact.total_saved_kwh) }} kWh</strong>
          </div>
          <div>
            <span>回收金额</span>
            <strong>{{ formatNumber(closureImpact.total_saving_yuan) }} 元</strong>
          </div>
          <div>
            <span>减排影响</span>
            <strong>{{ formatNumber(closureImpact.total_carbon_kg) }} kg</strong>
          </div>
          <div>
            <span>预测执行率</span>
            <strong>
              {{ closureImpact.budget_projection?.after_projected_execution_rate ?? analysis.total_projected_execution_rate }}%
            </strong>
          </div>
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
        <div v-if="analysis.buildings.length > 1" class="kpi-building-tabs">
          <button
            v-for="b in analysis.buildings"
            :key="b.building_id"
            type="button"
            class="kpi-building-tab"
            :class="{ 'kpi-building-tab--active': selectedKPI.building_id === b.building_id }"
            :disabled="loading"
            @click="loadKPI(b.building_id)"
          >
            {{ b.building_name }}
          </button>
        </div>
        <SectionCard eyebrow="KPI Scorecard" :title="`${selectedKPI.building_name} · ${selectedKPI.year} 年度考核`" :description="selectedKPI.settled_note || ''">
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
          <div v-if="kpiBreakdownItems.length" class="kpi-breakdown-grid">
            <div v-for="item in kpiBreakdownItems" :key="item.key">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }} / {{ item.max }}</strong>
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
                  <th>分项评分</th>
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
                  <td class="breakdown-cell" :title="(m.score_reasons || []).join('\n')">{{ formatScoreBreakdown(m.score_breakdown) }}</td>
                  <td>{{ m.score }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
      </template>

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
  fetchDecisionBudgetImpact,
  generateBudgets,
  setBudget,
} from "../lib/api.js";
import SectionCard from "./SectionCard.vue";
import StatusBanner from "./StatusBanner.vue";
import LoadingSpinner from "./LoadingSpinner.vue";
import EmptyState from "./EmptyState.vue";

const props = defineProps({
  buildings: { type: Array, default: () => [] },
  simClock: { type: Object, default: () => ({}) },
});

function simYearMonth() {
  const raw = props.simClock?.current_date;
  if (raw) {
    const dt = new Date(raw);
    if (!Number.isNaN(dt.getTime())) {
      return { year: dt.getFullYear(), month: dt.getMonth() + 1 };
    }
  }
  return null;
}

const _initPeriod = simYearMonth();
const selectedYear = ref(_initPeriod?.year ?? 2026);
const selectedMonth = ref(_initPeriod?.month ?? 5);
const loading = ref(false);
const error = ref("");
const analysis = ref(null);
const selectedKPI = ref(null);
const closureImpact = ref(null);

const yearOptions = [2024, 2025, 2026, 2027];

const budgetForm = reactive({
  building_id: "BLD-A",
  budget_kwh: 80000,
  note: "",
});

const kpiScoreParts = [
  { key: "budget_control", label: "预算控制", max: 40 },
  { key: "efficiency", label: "能效表现", max: 20 },
  { key: "anomaly_risk", label: "异常风险", max: 20 },
  { key: "work_order_closure", label: "工单闭环", max: 15 },
  { key: "improvement", label: "改善收益", max: 5 },
];

function rateClass(rate) {
  if (rate > 103) return "kpi-card--danger";
  if (rate > 100) return "kpi-card--warn";
  return "kpi-card--safe";
}

const execRateClass = computed(() => {
  if (!analysis.value) return "";
  return rateClass(analysis.value.total_execution_rate);
});

const projectedRateClass = computed(() => {
  if (!analysis.value) return "";
  return rateClass(analysis.value.total_projected_execution_rate);
});

const kpiBreakdownItems = computed(() => {
  const breakdown = selectedKPI.value?.score_breakdown;
  if (!breakdown) return [];
  return kpiScoreParts.map((item) => ({
    ...item,
    value: Number(breakdown[item.key] || 0).toFixed(1),
  }));
});

const periodNote = computed(() => {
  const status = analysis.value?.period_status;
  if (status === "future") {
    return analysis.value?.message || `${selectedMonth.value} 月尚未开始，暂无预算执行数据。`;
  }
  if (status === "in_progress") {
    return `${selectedMonth.value} 月为当前演示月份（进行中、未结算），以下为实时执行情况与月末预测。`;
  }
  return "";
});

function formatNumber(val) {
  if (val == null) return "-";
  const num = Number(val);
  if (Number.isNaN(num)) return "-";
  return num.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

function formatScoreBreakdown(breakdown) {
  if (!breakdown) return "-";
  return kpiScoreParts
    .map((item) => `${item.label.slice(0, 2)} ${Number(breakdown[item.key] || 0).toFixed(1)}`)
    .join(" / ");
}

async function loadBudgetAnalysis() {
  loading.value = true;
  error.value = "";
  try {
    const result = await fetchBudgetAnalysis(selectedYear.value, selectedMonth.value);
    analysis.value = result.item;
    const impact = await fetchDecisionBudgetImpact(selectedYear.value, selectedMonth.value);
    closureImpact.value = impact.item;
    if (result.item.buildings.length) {
      // Always refresh the KPI scorecard alongside the analysis so the built-in
      // "刷新数据" button (and the sandbox clock advancing) updates the card
      // without requiring a manual month switch + hard refresh. Keep the
      // currently inspected building when possible.
      const kpiBuildingId =
        selectedKPI.value?.building_id &&
        result.item.buildings.some((b) => b.building_id === selectedKPI.value.building_id)
          ? selectedKPI.value.building_id
          : result.item.buildings[0].building_id;
      await loadKPI(kpiBuildingId);
    } else {
      selectedKPI.value = null;
    }
  } catch (e) {
    error.value = "预算数据加载失败，请确认后端服务可用。";
    closureImpact.value = null;
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

// Keep the budget period aligned with the sandbox clock: when the demo advances
// to a new day/month the scorecard and analysis should follow without a manual
// month switch or hard refresh.
watch(
  () => props.simClock?.current_date,
  () => {
    const period = simYearMonth();
    if (!period) return;
    const changed = period.year !== selectedYear.value || period.month !== selectedMonth.value;
    if (changed) {
      selectedYear.value = period.year;
      selectedMonth.value = period.month;
    }
    if (props.buildings.length) {
      loadBudgetAnalysis();
    }
  }
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

.closure-impact-panel {
  display: grid;
  grid-template-columns: minmax(220px, 0.8fr) minmax(0, 1.2fr);
  gap: 16px;
  border: 1px solid rgba(15,139,141,0.16);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(15,139,141,0.08), rgba(255,255,255,0.94));
  padding: 18px;
}

.closure-impact-panel > div:first-child span {
  color: #0f8b8d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.closure-impact-panel > div:first-child strong {
  display: block;
  color: var(--ink-strong);
  font-size: 18px;
  margin-top: 4px;
}

.closure-impact-panel p {
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.5;
  margin: 8px 0 0;
}

.closure-impact-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.closure-impact-grid > div {
  border: 1px solid rgba(20,34,48,0.07);
  border-radius: 12px;
  background: rgba(255,255,255,0.78);
  padding: 12px;
}

.closure-impact-grid span {
  display: block;
  color: var(--ink-soft);
  font-size: 12px;
}

.closure-impact-grid strong {
  display: block;
  color: #0f6f71;
  font-size: 18px;
  margin-top: 4px;
}

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
.kpi-building-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.kpi-building-tab {
  padding: 7px 14px; border-radius: 999px; font: inherit; font-size: 13px; cursor: pointer;
  border: 1px solid rgba(20,34,48,0.14); background: rgba(255,255,255,0.8); color: var(--ink-soft);
  transition: all 0.15s;
}
.kpi-building-tab:hover { border-color: rgba(15,139,141,0.4); }
.kpi-building-tab--active {
  background: linear-gradient(135deg, #0f8b8d, #1ec5a7); color: #fff;
  border-color: transparent; font-weight: 600;
}
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
.kpi-breakdown-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin: 4px 0 16px;
}
.kpi-breakdown-grid div {
  border: 1px solid rgba(20,34,48,0.08);
  border-radius: 8px;
  background: rgba(255,255,255,0.62);
  padding: 10px;
}
.kpi-breakdown-grid span {
  display: block;
  color: var(--ink-soft);
  font-size: 12px;
}
.kpi-breakdown-grid strong {
  display: block;
  margin-top: 4px;
  color: var(--ink-strong);
  font-size: 15px;
}
.kpi-strengths, .kpi-improvements { margin-bottom: 12px; }
.kpi-strengths strong, .kpi-improvements strong { color: var(--ink-strong); font-size: 14px; }
.kpi-strengths ul, .kpi-improvements ul { margin: 4px 0 0 16px; color: var(--ink-soft); font-size: 13px; }
.kpi-monthly strong { display: block; margin-bottom: 8px; }
.kpi-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.kpi-table th, .kpi-table td { padding: 8px 10px; border-bottom: 1px solid rgba(20,34,48,0.06); text-align: center; }
.kpi-table th { color: var(--ink-soft); font-weight: 500; }
.breakdown-cell { min-width: 190px; color: var(--ink-soft); font-size: 12px; }
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
  .closure-impact-panel,
  .closure-impact-grid {
    grid-template-columns: 1fr;
  }
  .budget-set-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .kpi-breakdown-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .budget-bar-subtitle { flex-direction: column; gap: 2px; }
}
</style>

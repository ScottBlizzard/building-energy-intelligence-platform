<template>
  <div class="roi-panel">
    <StatusBanner v-if="error" :status="error" type="warning" />

    <div class="roi-toolbar">
      <label>
        <span>选择楼栋</span>
        <select v-model="selectedBuilding" @change="loadAudit">
          <option v-for="b in buildings" :key="b.building_id" :value="b.building_id">
            {{ b.building_name }}
          </option>
        </select>
      </label>
      <button class="primary-button" type="button" :disabled="loading" @click="loadAudit">
        刷新设备诊断
      </button>
    </div>

    <div v-if="roiCandidates.length" class="roi-candidate-panel">
      <div class="roi-candidate-head">
        <span>Retrofit Pool</span>
        <strong>重复异常改造候选池</strong>
        <p>设备多次异常后自动进入 ROI 讨论，改造通过后应影响未来预算基线和异常概率假设。</p>
      </div>
      <div class="roi-candidate-grid">
        <article
          v-for="item in roiCandidates.slice(0, 4)"
          :key="item.equipment_id"
          class="roi-candidate-card"
          @click="selectCandidate(item)"
        >
          <strong>#{{ item.retrofit_score }} · {{ item.equipment_id }}</strong>
          <span>{{ item.building_name }} · {{ item.equipment_type }}</span>
          <p>{{ item.reason }}</p>
          <em>{{ item.recommended_option }}</em>
        </article>
      </div>
    </div>

    <div v-if="loading" class="data-loading">
      <LoadingSpinner text="正在分析设备能效..." />
    </div>

    <template v-else-if="audit">
      <div class="equipment-audit-grid">
        <div
          v-for="eq in audit.equipment_list"
          :key="eq.equipment_type"
          class="equipment-card"
          :class="`equipment-card--${eq.cop_status}`"
          @click="selectEquipment(eq)"
        >
          <div class="eq-card-head">
            <strong>{{ eq.equipment_type }}</strong>
            <span class="eq-cop-badge" :class="`cop-badge--${eq.cop_status}`">{{ eq.cop_status }}</span>
          </div>
          <div class="eq-card-stats">
            <div><span>设备数量</span><strong>{{ eq.equipment_count }}</strong></div>
            <div><span>年度用电</span><strong>{{ formatNumber(eq.total_kwh) }} kWh</strong></div>
            <div><span>年度电费</span><strong>{{ formatNumber(eq.annual_cost_yuan) }} 元</strong></div>
            <div><span>平均 COP</span><strong>{{ eq.avg_cop }}</strong></div>
            <div><span>异常次数</span><strong>{{ eq.anomaly_count }}</strong></div>
          </div>
          <p v-if="eq.data_note" class="eq-data-note">{{ eq.data_note }}</p>
        </div>
      </div>

      <div v-if="selectedEquipment" class="roi-analyzer">
        <SectionCard eyebrow="ROI Calculator" :title="`${selectedEquipment.equipment_type} · 改造方案分析`" description="">
          <div class="roi-preset-grid">
            <div
              v-for="option in selectedEquipment.retrofit_candidates"
              :key="option.option"
              class="roi-preset-card"
              :class="{ 'roi-preset--selected': selectedPreset === option.option }"
              @click="applyPreset(option)"
            >
              <strong>{{ option.option }}</strong>
              <span>投资 {{ formatNumber(option.investment_yuan) }} 元</span>
              <span>年节省 {{ formatNumber(option.annual_saving_yuan) }} 元</span>
              <span>EAA {{ formatNumber(option.eaa_yuan) }} 元/年</span>
              <span class="roi-preset-payback">动态回收 {{ paybackText(option.discounted_payback_years) }}</span>
            </div>
          </div>

          <div v-if="scenarioComparison" class="scenario-compare">
            <div class="scenario-compare-head">
              <div>
                <span>Scenario Comparison</span>
                <strong>多方案经济性对比</strong>
              </div>
              <p>{{ scenarioComparison.recommendation }}</p>
            </div>
            <div class="scenario-table-wrap">
              <table class="scenario-table">
                <thead>
                  <tr>
                    <th>方案</th>
                    <th>投资</th>
                    <th>年节省</th>
                    <th>动态回收期</th>
                    <th>NPV(8%)</th>
                    <th>EAA(元/年)</th>
                    <th>结论</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="scenario in scenarioComparison.scenarios"
                    :key="scenario.project_name"
                    :class="{ 'scenario-row--best': scenario.project_name === scenarioComparison.comparison.best_eaa?.name }"
                  >
                    <td>{{ scenario.project_name }}</td>
                    <td>{{ formatNumber(scenario.investment_yuan) }} 元</td>
                    <td>{{ formatNumber(scenario.annual_saving_yuan) }} 元</td>
                    <td>{{ scenario.payback_label || paybackText(scenario.discounted_payback_years) }}</td>
                    <td :class="scenario.npv_yuan > 0 ? 'text-green' : 'text-red'">
                      {{ formatNumber(scenario.npv_yuan) }} 元
                    </td>
                    <td :class="scenario.eaa_yuan > 0 ? 'text-green' : 'text-red'">
                      {{ formatNumber(scenario.eaa_yuan) }}
                    </td>
                    <td>{{ scenario.assessment }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="scenario-foot">主判据：先筛 NPV(8% 社会折现率)&gt;0，再按等额年值 EAA 最大择优（寿命不同，EAA 才公平）；动态回收期仅作辅助。</p>
          </div>

          <div class="roi-custom-form">
            <label>
              <span>投资金额 (元)</span>
              <input v-model.number="roiForm.investment_yuan" type="number" min="1000" step="10000" />
            </label>
            <label>
              <span>预计节能率 (%)</span>
              <input v-model.number="roiForm.expected_saving_pct" type="range" min="5" max="50" step="1" />
              <strong>{{ roiForm.expected_saving_pct }}%</strong>
            </label>
            <label>
              <span>项目寿命 (年)</span>
              <input v-model.number="roiForm.lifespan" type="number" min="3" max="25" />
            </label>
            <label>
              <span>年维护成本 (元)</span>
              <input v-model.number="roiForm.annual_maintenance" type="number" min="0" step="1000" />
            </label>
            <button class="primary-button" type="button" :disabled="analyzing" @click="runAnalysis">
              计算 ROI
            </button>
          </div>
        </SectionCard>

        <div v-if="roiResult" class="roi-result-summary">
          <div class="roi-result-summary-head">
            <span>投资评估结果</span>
            <strong>{{ roiResult.project_name }}</strong>
          </div>
          <div class="roi-result-grid">
          <div class="roi-result-card" :class="`roi-result--${roiResult.assessment === '强烈推荐' || roiResult.assessment === '推荐' ? 'good' : 'warn'}`">
            <span>投资评估</span>
            <strong>{{ roiResult.assessment }}</strong>
          </div>
          <div class="roi-result-card">
            <span>净现值 NPV</span>
            <strong :class="roiResult.npv_yuan > 0 ? 'text-green' : 'text-red'">
              {{ formatNumber(roiResult.npv_yuan) }} 元
            </strong>
          </div>
          <div class="roi-result-card">
            <span>内部收益率 IRR</span>
            <strong>{{ roiResult.irr_pct }}%</strong>
          </div>
          <div class="roi-result-card">
            <span>动态回收期</span>
            <strong>{{ roiResult.payback_label || paybackText(roiResult.discounted_payback_years) }}</strong>
          </div>
          <div class="roi-result-card">
            <span>等额年值 EAA</span>
            <strong :class="roiResult.eaa_yuan > 0 ? 'text-green' : 'text-red'">
              {{ formatNumber(roiResult.eaa_yuan) }} 元/年
            </strong>
          </div>
          <div class="roi-result-card">
            <span>年减排 CO₂</span>
            <strong>{{ formatNumber(roiResult.carbon_reduction_kg_per_year) }} kg</strong>
          </div>
          </div>
        </div>

        <div v-if="roiResult" class="roi-detail-grid">
          <div class="roi-detail-card">
            <strong>项目概要</strong>
            <table class="roi-table">
              <tr><td>项目名称</td><td>{{ roiResult.project_name }}</td></tr>
              <tr><td>楼栋</td><td>{{ roiResult.building_name }}</td></tr>
              <tr><td>设备类型</td><td>{{ roiResult.equipment_type }}</td></tr>
              <tr><td>投资金额</td><td>{{ formatNumber(roiResult.investment_yuan) }} 元</td></tr>
              <tr><td>年节省电费</td><td>{{ formatNumber(roiResult.annual_saving_yuan) }} 元</td></tr>
              <tr><td>年节省电量</td><td>{{ formatNumber(roiResult.annual_saving_kwh) }} kWh</td></tr>
              <tr><td>节能率</td><td>{{ roiResult.expected_saving_pct }}%</td></tr>
              <tr><td>5年 ROI</td><td>{{ roiResult.roi_5year_pct }}%</td></tr>
              <tr><td>当前年度电费</td><td>{{ formatNumber(roiResult.current_annual_cost_yuan) }} 元</td></tr>
              <tr><td>折现率 / 电价递增</td><td>{{ roiResult.discount_rate }}% / {{ roiResult.price_escalation }}%·年</td></tr>
              <tr><td>含碳价 NPV</td><td>{{ formatNumber(roiResult.npv_with_carbon_yuan) }} 元（碳价 {{ roiResult.carbon_price_yuan_per_ton }} 元/吨）</td></tr>
              <tr><td>节能率口径</td><td>{{ roiResult.saving_basis }}</td></tr>
              <tr><td>投资口径</td><td>{{ roiResult.investment_basis }}</td></tr>
              <tr><td>年化口径</td><td>基于 {{ roiResult.observed_days || selectedEquipment.observed_days }} 天可见数据年化</td></tr>
            </table>
          </div>
          <div class="roi-detail-card">
            <strong>现金流分析</strong>
            <p class="cashflow-axis-note">柱高 = 累计净现金流（含电价递增、未折现）；红色为回本前累计为负，绿色为转正后净收益。</p>
            <div class="cashflow-chart">
              <div v-for="point in cashflowSeries" :key="point.year" class="cashflow-bar-wrap">
                <span class="cashflow-value" :class="point.cumulative_yuan >= 0 ? 'text-green' : 'text-red'">
                  {{ formatCompact(point.cumulative_yuan) }}
                </span>
                <div
                  class="cashflow-bar"
                  :class="point.cumulative_yuan >= 0 ? 'cashflow--positive' : 'cashflow--negative'"
                  :style="{ height: `${cashflowBarHeight(point.cumulative_yuan)}px` }"
                  :title="`第 ${point.year} 年：累计 ${formatNumber(point.cumulative_yuan)} 元`"
                ></div>
                <span>Y{{ point.year }}</span>
              </div>
            </div>
            <p class="cashflow-note">
              {{ cashflowNote }}
            </p>
          </div>
        </div>

        <div v-if="roiResult?.sensitivity?.length" class="sensitivity-card">
          <strong>敏感性分析</strong>
          <div class="sensitivity-grid">
            <div v-for="item in roiResult.sensitivity" :key="item.case" class="sensitivity-item">
              <span>{{ item.case }}</span>
              <strong>{{ formatNumber(item.npv_yuan) }} 元</strong>
              <small>{{ item.expected_saving_pct }}% 节能率 · {{ item.payback_label }}</small>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!selectedEquipment && audit.equipment_list.length" class="roi-hint">
        <EmptyState title="选择设备类型" description="点击上方设备卡片，查看改造方案并计算投资回报。" />
      </div>
    </template>

    <EmptyState v-else-if="!loading" title="暂无设备诊断数据" description="请选择楼栋后点击刷新。" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import {
  fetchDecisionROICandidates,
  fetchEquipmentAudit,
  analyzeROIProject,
  compareROIScenarios
} from "../lib/api.js";
import SectionCard from "./SectionCard.vue";
import StatusBanner from "./StatusBanner.vue";
import LoadingSpinner from "./LoadingSpinner.vue";
import EmptyState from "./EmptyState.vue";

const props = defineProps({
  buildings: { type: Array, default: () => [] },
});

const selectedBuilding = ref("BLD-A");
const loading = ref(false);
const analyzing = ref(false);
const error = ref("");
const audit = ref(null);
const selectedEquipment = ref(null);
const selectedPreset = ref("");
const roiResult = ref(null);
const scenarioComparison = ref(null);
const roiCandidates = ref([]);

const roiForm = reactive({
  investment_yuan: 150000,
  expected_saving_pct: 20,
  lifespan: 12,
  annual_maintenance: 5000,
});

function formatNumber(val) {
  if (val == null) return "-";
  const num = Number(val);
  if (Number.isNaN(num)) return "-";
  return num.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

function paybackText(years) {
  if (years == null || Number(years) >= 999) return "寿命期内无法回本";
  return `${Number(years).toFixed(1)} 年`;
}

async function loadAudit() {
  loading.value = true;
  error.value = "";
  try {
    const [result, candidates] = await Promise.all([
      fetchEquipmentAudit(selectedBuilding.value),
      fetchDecisionROICandidates(8)
    ]);
    audit.value = result.item;
    roiCandidates.value = candidates.items || [];
    selectedEquipment.value = null;
    roiResult.value = null;
    scenarioComparison.value = null;
  } catch {
    error.value = "设备诊断数据加载失败。";
  } finally {
    loading.value = false;
  }
}

async function selectCandidate(candidate) {
  if (!candidate?.building_id) {
    return;
  }
  selectedBuilding.value = candidate.building_id;
  await loadAudit();
  const match = audit.value?.equipment_list?.find(
    (item) => item.equipment_type === candidate.equipment_type
  );
  if (match) {
    selectEquipment(match);
  }
}

function selectEquipment(eq) {
  selectedEquipment.value = eq;
  selectedPreset.value = "";
  roiResult.value = null;
  scenarioComparison.value = null;
  if (eq.retrofit_candidates?.length) {
    const best = eq.retrofit_candidates[0];
    roiForm.investment_yuan = best.investment_yuan;
    roiForm.expected_saving_pct = best.saving_pct;
    roiForm.lifespan = best.lifespan_years;
    loadScenarioComparison(eq);
  }
}

function applyPreset(option) {
  selectedPreset.value = option.option;
  roiForm.investment_yuan = option.investment_yuan;
  roiForm.expected_saving_pct = option.saving_pct;
  roiForm.lifespan = option.lifespan_years;
}

async function runAnalysis() {
  if (!selectedEquipment.value) return;
  analyzing.value = true;
  error.value = "";
  try {
    const result = await analyzeROIProject({
      building_id: selectedBuilding.value,
      equipment_type: selectedEquipment.value.equipment_type,
      investment_yuan: roiForm.investment_yuan,
      expected_saving_pct: roiForm.expected_saving_pct / 100,
      annual_maintenance_cost: roiForm.annual_maintenance,
      project_lifespan_years: roiForm.lifespan,
      project_name: `${selectedEquipment.value.equipment_type}·${selectedPreset.value || "自定义方案"}`,
    });
    roiResult.value = result.item;
  } catch {
    error.value = "ROI 分析失败。";
  } finally {
    analyzing.value = false;
  }
}

async function loadScenarioComparison(eq) {
  if (!eq?.retrofit_candidates?.length) return;
  const scenarios = eq.retrofit_candidates.slice(0, 4).map((option) => ({
    building_id: selectedBuilding.value,
    equipment_type: eq.equipment_type,
    project_name: option.option,
    investment_yuan: option.investment_yuan,
    expected_saving_pct: option.saving_pct / 100,
    annual_maintenance_cost: 0,
    project_lifespan_years: option.lifespan_years,
  }));
  try {
    const result = await compareROIScenarios({
      building_id: selectedBuilding.value,
      scenarios,
    });
    scenarioComparison.value = result.item;
  } catch {
    scenarioComparison.value = null;
  }
}

const cashflowSeries = computed(() => {
  const series = roiResult.value?.cumulative_cashflows;
  if (Array.isArray(series) && series.length) {
    return series;
  }
  // 兜底：后端未提供时，用寿命/年节省在前端推算一条累计曲线（不含递增）。
  const result = roiResult.value;
  if (!result?.project_lifespan_years) return [];
  const out = [];
  let cumulative = -(result.investment_yuan || 0);
  for (let year = 1; year <= result.project_lifespan_years; year += 1) {
    cumulative += result.annual_saving_yuan || 0;
    out.push({ year, cumulative_yuan: Math.round(cumulative) });
  }
  return out;
});

const cashflowMaxAbs = computed(() => {
  const values = cashflowSeries.value.map((p) => Math.abs(p.cumulative_yuan || 0));
  return Math.max(1, ...values);
});

function cashflowBarHeight(value) {
  const ratio = Math.abs(value || 0) / cashflowMaxAbs.value;
  return Math.round(Math.max(6, ratio * 96));
}

function formatCompact(val) {
  const num = Number(val) || 0;
  const abs = Math.abs(num);
  if (abs >= 10000) return `${(num / 10000).toFixed(1)}万`;
  return num.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

const cashflowNote = computed(() => {
  if (!roiResult.value) return "";
  if (!roiResult.value.payback_within_lifespan) {
    return `该方案在 ${roiResult.value.project_lifespan_years} 年寿命期内无法完全回收投资，建议降低初始投资或提高预期节能率。`;
  }
  const netYears = Math.max(0, roiResult.value.project_lifespan_years - roiResult.value.payback_years).toFixed(1);
  return `前 ${roiResult.value.payback_label || `${roiResult.value.payback_years} 年`} 回收投资，之后约 ${netYears} 年为净收益期。`;
});

watch(
  () => props.buildings,
  (list) => {
    if (list.length) {
      selectedBuilding.value = list[0].building_id;
    }
  },
  { immediate: true }
);

defineExpose({ loadAudit });

onMounted(() => {
  if (props.buildings.length) {
    loadAudit();
  }
});
</script>

<style scoped>
.roi-panel { display: grid; gap: 20px; }
.roi-toolbar {
  display: flex; gap: 14px; align-items: flex-end; flex-wrap: wrap;
}
.roi-toolbar label { display: grid; gap: 6px; font-size: 13px; color: var(--ink-soft); }
.roi-toolbar select {
  padding: 10px 14px; border-radius: 12px; border: 1px solid rgba(20,34,48,0.12); font: inherit;
}

.roi-candidate-panel {
  border: 1px solid rgba(15,139,141,0.16);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(15,139,141,0.08), rgba(255,255,255,0.94));
  padding: 18px;
}

.roi-candidate-head {
  display: grid;
  gap: 4px;
  margin-bottom: 14px;
}

.roi-candidate-head span {
  color: #0f8b8d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.roi-candidate-head strong {
  color: var(--ink-strong);
  font-size: 18px;
}

.roi-candidate-head p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.roi-candidate-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.roi-candidate-card {
  display: grid;
  gap: 6px;
  border: 1px solid rgba(20,34,48,0.08);
  border-radius: 14px;
  background: rgba(255,255,255,0.82);
  padding: 14px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.roi-candidate-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 26px rgba(20,34,48,0.09);
}

.roi-candidate-card strong {
  color: var(--accent-deep);
  font-size: 14px;
}

.roi-candidate-card span,
.roi-candidate-card p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.45;
}

.roi-candidate-card em {
  color: #15724d;
  font-size: 12px;
  font-style: normal;
  font-weight: 700;
}

.equipment-audit-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px;
}
.equipment-card {
  background: rgba(255,255,255,0.92); border-radius: 16px; padding: 18px;
  box-shadow: 0 10px 28px rgba(20,34,48,0.06); cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s; border: 2px solid transparent;
}
.equipment-card:hover { transform: translateY(-2px); box-shadow: 0 14px 34px rgba(20,34,48,0.1); }
.equipment-card--高效 { border-color: rgba(34,160,107,0.3); }
.equipment-card--正常 { border-color: rgba(15,139,141,0.3); }
.equipment-card--低效 { border-color: rgba(217,54,79,0.3); }
.equipment-card--无数据 { border-color: rgba(20,34,48,0.12); opacity: 0.85; }
.eq-data-note { margin: 10px 0 0; font-size: 12px; color: var(--ink-soft); }

.eq-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.eq-card-head strong { font-size: 16px; }
.eq-cop-badge {
  padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 600;
}
.cop-badge--高效 { background: rgba(34,160,107,0.12); color: #1a7d4e; }
.cop-badge--正常 { background: rgba(15,139,141,0.12); color: #0f6f71; }
.cop-badge--低效 { background: rgba(217,54,79,0.12); color: #a32035; }
.cop-badge--无数据 { background: rgba(20,34,48,0.08); color: var(--ink-soft); }

.eq-card-stats { display: grid; gap: 6px; }
.eq-card-stats div { display: flex; justify-content: space-between; font-size: 13px; }
.eq-card-stats span { color: var(--ink-soft); }

.roi-preset-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 18px;
}
.roi-preset-card {
  background: rgba(20,34,48,0.03); border-radius: 14px; padding: 14px;
  cursor: pointer; border: 2px solid transparent; transition: border-color 0.15s;
  display: grid; gap: 4px;
}
.roi-preset-card strong { font-size: 14px; }
.roi-preset-card span { font-size: 12px; color: var(--ink-soft); }
.roi-preset--selected { border-color: #0f8b8d; background: rgba(15,139,141,0.06); }
.roi-preset-payback { font-weight: 600; color: #0f8b8d !important; }

.scenario-compare {
  border: 1px solid rgba(15,139,141,0.16);
  background: linear-gradient(135deg, rgba(15,139,141,0.08), rgba(255,255,255,0.94));
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 18px;
}
.scenario-compare-head {
  display: grid;
  grid-template-columns: minmax(160px, 0.6fr) minmax(0, 1.4fr);
  gap: 14px;
  align-items: center;
  margin-bottom: 12px;
}
.scenario-compare-head span {
  color: #0f8b8d;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}
.scenario-compare-head strong { display: block; font-size: 17px; margin-top: 3px; }
.scenario-compare-head p { margin: 0; color: var(--ink-soft); font-size: 13px; line-height: 1.5; }
.scenario-table-wrap { overflow-x: auto; }
.scenario-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
  font-size: 13px;
}
.scenario-table th,
.scenario-table td {
  padding: 9px 10px;
  border-bottom: 1px solid rgba(20,34,48,0.07);
  text-align: left;
  white-space: nowrap;
}
.scenario-table th {
  color: var(--ink-soft);
  font-weight: 600;
}
.scenario-row--best {
  background: rgba(34,160,107,0.08);
}
.scenario-row--best td:first-child {
  color: #0f6f71;
  font-weight: 700;
}
.scenario-foot { margin: 10px 2px 0; font-size: 12px; color: var(--ink-soft); line-height: 1.5; }

.roi-custom-form {
  display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; align-items: end;
}
.roi-custom-form label { display: grid; gap: 6px; font-size: 13px; color: var(--ink-soft); }
.roi-custom-form input[type="number"], .roi-custom-form input[type="range"] {
  width: 100%; padding: 10px 12px; border-radius: 12px;
  border: 1px solid rgba(20,34,48,0.12); font: inherit;
}
.roi-custom-form strong { font-size: 16px; text-align: center; }

.roi-result-summary {
  border: 1px solid rgba(15,139,141,0.16);
  background: linear-gradient(135deg, rgba(15,139,141,0.06), rgba(255,255,255,0.94));
  border-radius: 16px;
  padding: 16px;
}
.roi-result-summary-head { margin-bottom: 12px; }
.roi-result-summary-head span {
  color: #0f8b8d; font-size: 11px; font-weight: 700; text-transform: uppercase;
}
.roi-result-summary-head strong { display: block; font-size: 16px; margin-top: 3px; }
.roi-result-grid {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px;
}
.roi-result-card {
  background: rgba(255,255,255,0.92); border-radius: 14px; padding: 16px;
  text-align: center; box-shadow: 0 8px 22px rgba(20,34,48,0.05);
}
.roi-result-card span { color: var(--ink-soft); font-size: 12px; display: block; }
.roi-result-card strong { font-size: 20px; display: block; margin-top: 4px; }
.roi-result--good { border-left: 3px solid #22a06b; }
.roi-result--warn { border-left: 3px solid #f39c12; }
.text-green { color: #22a06b; }
.text-red { color: #d9364f; }

.roi-detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
}
.roi-detail-card {
  background: rgba(255,255,255,0.92); border-radius: 16px; padding: 20px;
  box-shadow: 0 10px 28px rgba(20,34,48,0.06);
}
.roi-detail-card > strong { display: block; margin-bottom: 14px; font-size: 15px; }
.roi-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.roi-table td { padding: 7px 10px; border-bottom: 1px solid rgba(20,34,48,0.05); }
.roi-table td:first-child { color: var(--ink-soft); width: 40%; }
.roi-table td:last-child { font-weight: 500; }

.cashflow-axis-note { margin: 0 0 10px; font-size: 12px; color: var(--ink-soft); line-height: 1.5; }
.cashflow-chart {
  display: flex; gap: 6px; align-items: flex-end; height: 150px; padding: 10px 0;
}
.cashflow-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 4px; }
.cashflow-bar {
  width: 100%; max-width: 32px; border-radius: 6px 6px 0 0; transition: height 0.3s;
}
.cashflow--negative { background: linear-gradient(180deg, #f39c12, #e74c3c); }
.cashflow--positive { background: linear-gradient(180deg, #2ecc71, #22a06b); }
.cashflow-bar-wrap > span { font-size: 10px; color: var(--ink-soft); }
.cashflow-value { font-size: 9px; font-weight: 600; }
.cashflow-note { margin-top: 12px; font-size: 13px; color: var(--ink-soft); }

.sensitivity-card {
  background: rgba(255,255,255,0.92);
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 10px 28px rgba(20,34,48,0.06);
}
.sensitivity-card > strong { display: block; margin-bottom: 12px; font-size: 15px; }
.sensitivity-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.sensitivity-item {
  border: 1px solid rgba(20,34,48,0.08);
  background: rgba(20,34,48,0.025);
  border-radius: 12px;
  padding: 12px;
  display: grid;
  gap: 4px;
}
.sensitivity-item span { color: var(--ink-soft); font-size: 12px; }
.sensitivity-item strong { font-size: 18px; }
.sensitivity-item small { color: var(--ink-soft); font-size: 12px; }

.roi-hint { padding: 20px 0; }

.primary-button {
  padding: 10px 18px; border-radius: 12px; font: inherit; cursor: pointer;
  border: 0; font-weight: 500;
  background: linear-gradient(135deg, #0f8b8d, #1ec5a7); color: white;
}
.data-loading { display: flex; justify-content: center; padding: 40px; }

@media (max-width: 768px) {
  .equipment-audit-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .roi-candidate-grid { grid-template-columns: 1fr; }
  .roi-preset-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .roi-custom-form { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .roi-result-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .roi-detail-grid { grid-template-columns: 1fr; }
  .scenario-compare-head { grid-template-columns: 1fr; }
  .sensitivity-grid { grid-template-columns: 1fr; }
}
</style>

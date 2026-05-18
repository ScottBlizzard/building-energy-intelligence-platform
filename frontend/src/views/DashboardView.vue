<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import AppHeader from "../components/AppHeader.vue";
import TabNavigation from "../components/TabNavigation.vue";
import StatusBanner from "../components/StatusBanner.vue";
import FilterToolbar from "../components/FilterToolbar.vue";
import LoadingSpinner from "../components/LoadingSpinner.vue";
import EmptyState from "../components/EmptyState.vue";
import AssistantPanel from "../components/AssistantPanel.vue";
import DataTable from "../components/DataTable.vue";
import KpiCard from "../components/KpiCard.vue";
import SectionCard from "../components/SectionCard.vue";
import TrendChart from "../components/TrendChart.vue";
import BuildingComparisonChart from "../components/BuildingComparisonChart.vue";
import AnomalyReasonChart from "../components/AnomalyReasonChart.vue";
import {
  downloadCsvExport,
  fetchAnomalies,
  fetchAnomalyReasons,
  fetchBuildingComparison,
  fetchBuildings,
  fetchCopRanking,
  fetchDatasetMeta,
  fetchOverview,
  fetchRecords,
  fetchTimeSummary,
  queryAssistant
} from "../lib/api";

function createEmptyOverview() {
  return {
    total_records: 0,
    building_count: 0,
    average_cop: 0,
    abnormal_record_count: 0,
    time_range: { start: "-", end: "-" },
    totals: {}
  };
}

function createEmptyDatasetMeta() {
  return {
    fields: [],
    building_options: [],
    record_count: 0,
    building_count: 0,
    time_range: { start: "-", end: "-" }
  };
}

function createDefaultRecordFilters() {
  return {
    buildingId: "",
    startTime: "",
    endTime: "",
    limit: 10
  };
}

const activeTab = ref("overview");
const apiStatus = reactive({
  message: "正在尝试连接后端接口...",
  type: "info"
});
const overview = ref(createEmptyOverview());

const datasetMeta = ref(createEmptyDatasetMeta());

const buildings = ref([]);
const records = ref([]);
const assistantReply = ref(null);
const recordSummary = reactive({
  count: 0,
  totalFilteredCount: 0
});
const loading = reactive({
  overview: false,
  records: false,
  analytics: false,
  assistant: false
});
const errors = reactive({
  overview: "",
  records: "",
  analytics: "",
  assistant: "",
  export: ""
});
const exportState = reactive({
  loading: false,
  lastFile: ""
});

const recordFilters = reactive(createDefaultRecordFilters());

const analytics = reactive({
  timeSummary: [],
  buildingComparison: [],
  copRanking: [],
  anomalies: [],
  anomalyReasons: []
});

const tabs = [
  { key: "overview", label: "总览" },
  { key: "data", label: "数据浏览" },
  { key: "analytics", label: "统计分析" },
  { key: "assistant", label: "智能问答" }
];

const modules = [
  {
    title: "数据管理",
    description: "统一数据标准，确保数据质量和一致性。",
    status: "数据标准化"
  },
  {
    title: "后端接口",
    description: "提供稳定可靠的API服务，支持多场景应用。",
    status: "服务稳定"
  },
  {
    title: "前端工作台",
    description: "直观的可视化界面，便捷的操作体验。",
    status: "界面友好"
  },
  {
    title: "智能分析",
    description: "基于数据的智能分析和预测能力。",
    status: "AI赋能"
  }
];

const defaultQuestions = [
  "当前有哪些建筑？",
  "当前样例数据有哪些异常记录？",
  "当前样例数据的平均 COP 是多少？",
  "为什么实验楼电耗这么高？",
  "冷却塔应该多久维护一次？",
  "这些数据是纯随机生成的吗？"
];

const recordColumns = [
  { key: "record_id", label: "记录 ID" },
  { key: "building_name", label: "建筑" },
  { key: "timestamp", label: "时间" },
  { key: "electricity_kwh", label: "电耗(kWh)" },
  { key: "hvac_kwh", label: "空调电耗(kWh)" },
  { key: "equipment_status", label: "设备状态" }
];

const anomalyColumns = [
  { key: "building_name", label: "建筑" },
  { key: "timestamp", label: "时间" },
  { key: "equipment_id", label: "设备" },
  { key: "equipment_status", label: "状态" },
  { key: "anomaly_reason", label: "原因" }
];

const latestTrendPoints = computed(() => analytics.timeSummary.slice(-8));
const trendMax = computed(() =>
  Math.max(...latestTrendPoints.value.map((item) => item.electricity_kwh || 0), 1)
);
const topComparison = computed(() => analytics.buildingComparison.slice(0, 4));
const visibleFields = computed(() => datasetMeta.value.fields.slice(0, 10));
const availableTimeRange = computed(() => ({
  start: toDateTimeLocal(datasetMeta.value.time_range.start),
  end: toDateTimeLocal(datasetMeta.value.time_range.end)
}));
const activeFilterSummary = computed(() => {
  const parts = [];

  if (recordFilters.buildingId) {
    const match = buildings.value.find((item) => item.building_id === recordFilters.buildingId);
    parts.push(`建筑：${match?.building_name || recordFilters.buildingId}`);
  } else {
    parts.push("建筑：全部");
  }

  if (recordFilters.startTime) {
    parts.push(`开始：${recordFilters.startTime.replace("T", " ")}`);
  }
  if (recordFilters.endTime) {
    parts.push(`结束：${recordFilters.endTime.replace("T", " ")}`);
  }

  parts.push(`表格展示：${recordFilters.limit} 条`);
  return parts.join(" · ");
});

function toDateTimeLocal(value) {
  if (!value || value === "-") {
    return "";
  }
  return value.replace(" ", "T").slice(0, 16);
}

function buildFilterParams({ includeLimit = false } = {}) {
  const params = {};

  if (recordFilters.buildingId) {
    params.building_id = recordFilters.buildingId;
  }
  if (recordFilters.startTime) {
    params.start_time = recordFilters.startTime;
  }
  if (recordFilters.endTime) {
    params.end_time = recordFilters.endTime;
  }
  if (includeLimit) {
    params.limit = recordFilters.limit;
  }

  return params;
}

async function loadOverview() {
  loading.overview = true;
  errors.overview = "";
  try {
    const [overviewData, metaData, buildingData] = await Promise.all([
      fetchOverview(),
      fetchDatasetMeta(),
      fetchBuildings()
    ]);
    overview.value = overviewData;
    datasetMeta.value = metaData;
    buildings.value = buildingData.items;
    apiStatus.message = "后端已连接，当前页面展示真实接口数据。";
    apiStatus.type = "success";
  } catch (error) {
    apiStatus.message = "未检测到后端，当前页面将保留结构化占位并显示错误状态。";
    apiStatus.type = "warning";
    errors.overview = "当前无法加载总览数据，请确认后端服务与样例数据文件可用。";
    overview.value = createEmptyOverview();
    datasetMeta.value = createEmptyDatasetMeta();
    buildings.value = [];
  } finally {
    loading.overview = false;
  }
}

async function loadRecords() {
  loading.records = true;
  errors.records = "";
  try {
    const payload = await fetchRecords(buildFilterParams({ includeLimit: true }));
    records.value = payload.items;
    recordSummary.count = payload.count;
    recordSummary.totalFilteredCount = payload.total_filtered_count;
  } catch (error) {
    records.value = [];
    recordSummary.count = 0;
    recordSummary.totalFilteredCount = 0;
    errors.records = "原始记录加载失败，请检查后端接口或当前筛选条件。";
  } finally {
    loading.records = false;
  }
}

async function loadAnalytics() {
  loading.analytics = true;
  errors.analytics = "";
  try {
    const sharedFilters = buildFilterParams();
    const [timeSummary, buildingComparison, copRanking, anomalies, anomalyReasons] =
      await Promise.all([
        fetchTimeSummary({ ...sharedFilters, freq: "D" }),
        fetchBuildingComparison(sharedFilters),
        fetchCopRanking(sharedFilters),
        fetchAnomalies(sharedFilters),
        fetchAnomalyReasons(sharedFilters)
      ]);

    analytics.timeSummary = timeSummary.items;
    analytics.buildingComparison = buildingComparison.items;
    analytics.copRanking = copRanking.items;
    analytics.anomalies = anomalies.items;
    analytics.anomalyReasons = anomalyReasons.items;
  } catch (error) {
    analytics.timeSummary = [];
    analytics.buildingComparison = [];
    analytics.copRanking = [];
    analytics.anomalies = [];
    analytics.anomalyReasons = [];
    errors.analytics = "统计分析接口暂时不可用，请先检查后端是否正常运行。";
  } finally {
    loading.analytics = false;
  }
}

async function handleAsk(question) {
  loading.assistant = true;
  errors.assistant = "";
  try {
    assistantReply.value = await queryAssistant(question);
  } catch (error) {
    errors.assistant = "智能问答接口暂时不可用，当前展示的是降级提示。";
    assistantReply.value = {
      answer: "当前无法连接智能问答接口，请先确认后端服务已启动，再尝试继续提问。",
      citations: [{ title: "知识库入口", path: "knowledge_base/README.md" }],
      follow_up: ["先查看数据浏览页", "先查看统计分析页", "确认后端接口状态"]
    };
  } finally {
    loading.assistant = false;
  }
}

async function handleFilterApply() {
  errors.export = "";
  exportState.lastFile = "";
  await Promise.all([loadRecords(), loadAnalytics()]);
}

async function handleFilterReset() {
  Object.assign(recordFilters, createDefaultRecordFilters());
  errors.export = "";
  exportState.lastFile = "";
  await Promise.all([loadRecords(), loadAnalytics()]);
}

async function handleExport() {
  exportState.loading = true;
  errors.export = "";
  try {
    exportState.lastFile = await downloadCsvExport(buildFilterParams());
  } catch (error) {
    exportState.lastFile = "";
    errors.export = "导出失败，请确认后端导出接口已经可用。";
  } finally {
    exportState.loading = false;
  }
}

onMounted(async () => {
  await loadOverview();
  await Promise.allSettled([loadRecords(), loadAnalytics()]);
});
</script>

<template>
  <main class="dashboard-shell">
    <AppHeader>
      <template #actions>
        <StatusBanner 
          :status="apiStatus.message" 
          :type="apiStatus.type"
        />
      </template>
    </AppHeader>
    
    <div class="hero-stats">
      <div class="stat-card">
        <span class="stat-label">数据记录</span>
        <strong class="stat-value">{{ overview.total_records || datasetMeta.record_count || 0 }}</strong>
      </div>
      <div class="stat-card">
        <span class="stat-label">建筑数量</span>
        <strong class="stat-value">{{ overview.building_count || datasetMeta.building_count || 0 }}</strong>
      </div>
      <div class="stat-card">
        <span class="stat-label">平均 COP</span>
        <strong class="stat-value">{{ overview.average_cop || 0 }}</strong>
      </div>
      <div class="stat-card">
        <span class="stat-label">异常记录</span>
        <strong class="stat-value">{{ overview.abnormal_record_count || 0 }}</strong>
      </div>
    </div>

    <TabNavigation 
      :tabs="tabs" 
      v-model:activeTab="activeTab"
    />

    <template v-if="activeTab === 'overview'">
      <section class="kpi-grid">
        <KpiCard title="数据记录" :value="overview.total_records" caption="总记录数量" />
        <KpiCard title="建筑数量" :value="overview.building_count" caption="监测建筑总数" />
        <KpiCard title="平均 COP" :value="overview.average_cop" caption="系统能效比" />
        <KpiCard title="异常记录" :value="overview.abnormal_record_count" caption="异常检测数量" />
      </section>

      <div class="content-grid">
        <SectionCard eyebrow="System" title="系统概览" description="建筑能源管理系统运行状态总览">
          <div class="system-overview">
            <div class="overview-item">
              <span class="overview-label">运行状态</span>
              <strong class="overview-value status-active">正常运行</strong>
            </div>
            <div class="overview-item">
              <span class="overview-label">数据更新</span>
              <strong class="overview-value">实时更新</strong>
            </div>
            <div class="overview-item">
              <span class="overview-label">覆盖范围</span>
              <strong class="overview-value">全园区监测</strong>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Data" title="数据质量" description="当前数据集的基本信息和质量指标">
          <div class="data-quality-info">
            <div class="quality-item">
              <span class="quality-label">监测时间范围</span>
              <strong class="quality-value">{{ datasetMeta.time_range.start }} 至 {{ datasetMeta.time_range.end }}</strong>
            </div>
            <div class="quality-item">
              <span class="quality-label">监测指标数</span>
              <strong class="quality-value">{{ datasetMeta.fields.length }} 项</strong>
            </div>
            <div class="quality-item">
              <span class="quality-label">覆盖建筑</span>
              <strong class="quality-value">{{ buildings.map((item) => item.building_name).join("、") }}</strong>
            </div>
          </div>
          <div class="field-chip-list">
            <span v-for="field in visibleFields" :key="field" class="field-chip">{{ field }}</span>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Features" title="核心功能" description="系统提供的主要功能模块">
          <div class="feature-list">
            <div class="feature-item">
              <div class="feature-icon">📊</div>
              <div class="feature-content">
                <h4>能耗监测</h4>
                <p>实时监测建筑能耗数据，提供详细的用电分析</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">🚨</div>
              <div class="feature-content">
                <h4>异常检测</h4>
                <p>智能识别异常用电模式，及时发现潜在问题</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">💡</div>
              <div class="feature-content">
                <h4>智能问答</h4>
                <p>基于知识库的AI助手，解答能源管理相关问题</p>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Insights" title="数据洞察" description="基于当前数据的初步分析结论">
          <div class="insights-content">
            <div class="insight-item">
              <span class="insight-icon">📈</span>
              <div class="insight-text">
                <strong>能耗趋势：</strong>系统持续监测各建筑能耗变化，为节能优化提供数据支撑
              </div>
            </div>
            <div class="insight-item">
              <span class="insight-icon">🔍</span>
              <div class="insight-text">
                <strong>异常识别：</strong>通过智能算法识别异常用电模式，帮助及时发现设备问题
              </div>
            </div>
            <div class="insight-item">
              <span class="insight-icon">⚡</span>
              <div class="insight-text">
                <strong>能效优化：</strong>基于COP等指标分析，为建筑能效提升提供专业建议
              </div>
            </div>
          </div>
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'data'">
      <div class="content-grid content-grid--single">
        <SectionCard eyebrow="Filters" title="数据浏览" description="查看和管理建筑能源消耗数据">
          <FilterToolbar
            v-model:filters="recordFilters"
            :buildings="buildings"
            :loading="loading.records || loading.analytics"
            :exporting="exportState.loading"
            :time-range="availableTimeRange"
            @apply="handleFilterApply"
            @reset="handleFilterReset"
            @export="handleExport"
          />

          <StatusBanner
            :status="activeFilterSummary"
            type="info"
          />

          <div v-if="exportState.lastFile || errors.export" class="export-notifications">
            <div v-if="exportState.lastFile" class="export-success">
              <div class="export-icon">✅</div>
              <div class="export-content">
                <div class="export-title">导出成功</div>
                <div class="export-filename">{{ exportState.lastFile }}</div>
                <div class="export-hint">文件已保存到下载目录</div>
              </div>
            </div>
            <div v-if="errors.export" class="export-error">
              <div class="export-icon">❌</div>
              <div class="export-content">
                <div class="export-title">导出失败</div>
                <div class="export-message">{{ errors.export }}</div>
                <div class="export-hint">请检查后端服务状态</div>
              </div>
            </div>
          </div>

          <div v-if="recordSummary.totalFilteredCount && !errors.records" class="inline-banner-list">
            <StatusBanner
              :status="`当前筛选共命中 ${recordSummary.totalFilteredCount} 条记录，表格展示前 ${recordSummary.count} 条。`"
              type="info"
            />
          </div>

          <div v-if="loading.records" class="data-loading">
            <LoadingSpinner text="正在加载数据..." />
          </div>
          <div v-else-if="errors.records" class="data-empty">
            <EmptyState 
              icon="⚠️"
              title="记录加载失败"
              :description="errors.records"
              actionText="重新加载"
              @action="handleFilterApply"
            />
          </div>
          <div v-else-if="records.length === 0" class="data-empty">
            <EmptyState 
              icon="🔍"
              title="暂无数据"
              description="当前筛选条件下没有找到符合条件的记录"
              actionText="重置筛选"
              @action="handleFilterReset"
            />
          </div>
          <DataTable v-else :columns="recordColumns" :rows="records" empty-text="没有查到符合条件的记录" />
        </SectionCard>

        <SectionCard eyebrow="Export" title="数据导出" description="支持将筛选后的数据导出为CSV格式文件">
          <div class="export-info">
            <div class="export-feature">
              <h4>📊 灵活导出</h4>
              <p>根据筛选条件导出特定时间段和建筑的能耗数据</p>
            </div>
            <div class="export-feature">
              <h4>📋 标准格式</h4>
              <p>导出文件采用标准CSV格式，兼容Excel等常用工具</p>
            </div>
            <div class="export-feature">
              <h4>⚡ 快速下载</h4>
              <p>一键导出，文件自动生成并下载到本地</p>
            </div>
          </div>
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'analytics'">
      <div class="content-grid">
        <SectionCard eyebrow="Scope" title="分析筛选范围" description="统计分析与数据浏览共用同一组筛选条件。">
          <StatusBanner :status="activeFilterSummary" type="info" />
          <div v-if="errors.analytics" class="analytics-feedback">
            <EmptyState
              icon="📉"
              title="分析数据暂不可用"
              :description="errors.analytics"
              actionText="重新加载分析"
              @action="handleFilterApply"
            />
          </div>
        </SectionCard>

        <SectionCard eyebrow="Trend" title="日度能耗趋势" description="建筑能耗变化趋势分析">
          <TrendChart
            :data="analytics.timeSummary"
            :loading="loading.analytics"
            :error="errors.analytics"
          />
        </SectionCard>

        <SectionCard eyebrow="Comparison" title="建筑对比" description="专业图表展示建筑电耗和COP对比。">
          <BuildingComparisonChart
            :data="analytics.buildingComparison"
            :loading="loading.analytics"
            :error="errors.analytics"
          />
        </SectionCard>

        <SectionCard eyebrow="Ranking" title="COP 排名" description="建筑能效比综合排名">
          <ul v-if="analytics.copRanking.length && !errors.analytics" class="endpoint-list">
            <li v-for="item in analytics.copRanking" :key="item.building_id">
              {{ item.building_name }} · COP {{ item.average_cop }}
            </li>
          </ul>
          <EmptyState
            v-else
            icon="🧊"
            title="暂无 COP 排名"
            description="当前筛选范围内没有可展示的 COP 结果。"
          />
        </SectionCard>

        <SectionCard eyebrow="Anomaly" title="异常原因分布" description="">
          <AnomalyReasonChart
            :data="analytics.anomalyReasons"
            :loading="loading.analytics"
            :error="errors.analytics"
          />
        </SectionCard>

        <SectionCard eyebrow="Details" title="异常明细" description="">
          <div v-if="loading.analytics" class="data-loading">
            <LoadingSpinner text="正在加载异常明细..." />
          </div>
          <DataTable v-else :columns="anomalyColumns" :rows="analytics.anomalies.slice(0, 10)" empty-text="暂无异常" />
        </SectionCard>
      </div>
    </template>

    <template v-else>
      <div class="content-grid content-grid--assistant">
        <SectionCard eyebrow="Assistant" title="智能问答工作区" description="">
          <div v-if="errors.assistant" class="inline-banner-list">
            <StatusBanner :status="errors.assistant" type="warning" />
          </div>
          <AssistantPanel
            :loading="loading.assistant"
            :reply="assistantReply"
            :suggestions="defaultQuestions"
            @ask="handleAsk"
          />
        </SectionCard>

        <SectionCard eyebrow="Knowledge Base" title="知识库" description="">
          <ul class="bullet-list">
            <li>knowledge_base/manuals/anomaly_diagnosis_guide.md</li>
            <li>knowledge_base/manuals/equipment_maintenance_playbook.md</li>
            <li>knowledge_base/manuals/building_type_notes.md</li>
            <li>knowledge_base/glossary/metrics_and_rules.md</li>
            <li>knowledge_base/faq/qa_bank_round1.md</li>
          </ul>
        </SectionCard>
      </div>
    </template>
  </main>
</template>

<style scoped>
.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 22px;
  padding: 20px;
  text-align: center;
  backdrop-filter: blur(18px);
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--ink-soft);
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--accent-deep);
}

.data-loading,
.data-empty {
  padding: 40px;
  text-align: center;
}

.inline-banner-list {
  display: grid;
  gap: 10px;
  margin: 14px 0;
}

.analytics-feedback {
  margin-top: 18px;
}

.export-notifications {
  margin: 16px 0;
}

.export-success,
.export-error {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.export-success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border: 1px solid #b1dfbb;
}

.export-error {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  border: 1px solid #f1b0b7;
}

.export-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.export-content {
  flex: 1;
}

.export-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.export-success .export-title {
  color: #155724;
}

.export-error .export-title {
  color: #721c24;
}

.export-filename,
.export-message {
  font-size: 13px;
  color: #333;
  margin-bottom: 2px;
  word-break: break-all;
}

.export-hint {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

@media (max-width: 768px) {
  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .export-success,
  .export-error {
    padding: 10px 12px;
    gap: 8px;
  }
  
  .export-icon {
    font-size: 18px;
  }
  
  .export-title {
    font-size: 13px;
  }
  
  .export-filename,
  .export-message {
    font-size: 12px;
  }
}
</style>

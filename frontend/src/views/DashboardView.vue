<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import AppHeader from "../components/AppHeader.vue";
import TabNavigation from "../components/TabNavigation.vue";
import StatusBanner from "../components/StatusBanner.vue";
import FilterToolbar from "../components/FilterToolbar.vue";
import AnalyticsSummary from "../components/AnalyticsSummary.vue";
import LoadingSpinner from "../components/LoadingSpinner.vue";
import EmptyState from "../components/EmptyState.vue";
import AssistantPanel from "../components/AssistantPanel.vue";
import DataTable from "../components/DataTable.vue";
import KpiCard from "../components/KpiCard.vue";
import SectionCard from "../components/SectionCard.vue";
import {
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

const activeTab = ref("overview");
const apiStatus = ref("正在尝试连接后端接口...");

const overview = ref({
  total_records: 0,
  building_count: 0,
  average_cop: 0,
  abnormal_record_count: 0,
  time_range: { start: "-", end: "-" },
  totals: {}
});

const datasetMeta = ref({
  fields: [],
  building_options: [],
  record_count: 0,
  building_count: 0,
  time_range: { start: "-", end: "-" }
});

const buildings = ref([]);
const records = ref([]);
const assistantReply = ref(null);
const loading = reactive({
  overview: false,
  records: false,
  analytics: false,
  assistant: false
});

const recordFilters = reactive({
  buildingId: "",
  limit: 10
});

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
    description: "冻结字段、维护数据字典、生成样例数据并提供查询入口。",
    status: "适合数据与 AI 负责人继续扩展"
  },
  {
    title: "后端接口",
    description: "统一提供总览、建筑列表、查询、分析和问答接口。",
    status: "适合技术负责人继续细化"
  },
  {
    title: "前端工作台",
    description: "将总览、数据、分析和问答做成统一演示界面。",
    status: "适合前端负责人继续补交互"
  },
  {
    title: "交付文档",
    description: "接口契约、协作规则、集成清单和测试计划已经落库。",
    status: "适合项目经理统一推进"
  }
];

const defaultQuestions = [
  "当前有哪些建筑？",
  "当前样例数据有哪些异常记录？",
  "当前样例数据的平均 COP 是多少？",
  "当前系统有哪些模块？"
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

async function loadOverview() {
  loading.overview = true;
  try {
    const [overviewData, metaData, buildingData] = await Promise.all([
      fetchOverview(),
      fetchDatasetMeta(),
      fetchBuildings()
    ]);
    overview.value = overviewData;
    datasetMeta.value = metaData;
    buildings.value = buildingData.items;
    apiStatus.value = "后端已连接，当前页面展示真实接口数据。";
  } catch (error) {
    apiStatus.value = "未检测到后端，当前页面将保留部分静态结构。";
  } finally {
    loading.overview = false;
  }
}

async function loadRecords() {
  loading.records = true;
  try {
    const payload = await fetchRecords({
      building_id: recordFilters.buildingId,
      limit: recordFilters.limit
    });
    records.value = payload.items;
  } finally {
    loading.records = false;
  }
}

async function loadAnalytics() {
  loading.analytics = true;
  try {
    const [timeSummary, buildingComparison, copRanking, anomalies, anomalyReasons] =
      await Promise.all([
        fetchTimeSummary({ freq: "D" }),
        fetchBuildingComparison(),
        fetchCopRanking(),
        fetchAnomalies(),
        fetchAnomalyReasons()
      ]);

    analytics.timeSummary = timeSummary.items;
    analytics.buildingComparison = buildingComparison.items;
    analytics.copRanking = copRanking.items;
    analytics.anomalies = anomalies.items;
    analytics.anomalyReasons = anomalyReasons.items;
  } finally {
    loading.analytics = false;
  }
}

async function handleAsk(question) {
  loading.assistant = true;
  try {
    assistantReply.value = await queryAssistant(question);
  } finally {
    loading.assistant = false;
  }
}

function handleFilterChange(filters) {
  recordFilters.buildingId = filters.building_id;
  recordFilters.limit = filters.limit;
  loadRecords();
}

function resetFilters() {
  recordFilters.buildingId = "";
  recordFilters.limit = 10;
  loadRecords();
}

onMounted(async () => {
  await loadOverview();
  await Promise.all([loadRecords(), loadAnalytics()]);
});
</script>

<template>
  <main class="dashboard-shell">
    <AppHeader>
      <template #actions>
        <StatusBanner 
          :status="apiStatus" 
          :type="apiStatus.includes('已连接') ? 'success' : 'warning'"
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
        <KpiCard title="样例记录数" :value="overview.total_records" caption="当前数据规模适合联调与演示" />
        <KpiCard title="建筑数量" :value="overview.building_count" caption="已支持多建筑场景筛选" />
        <KpiCard title="平均 COP" :value="overview.average_cop" caption="可继续细化到建筑级和时间级" />
        <KpiCard title="异常记录" :value="overview.abnormal_record_count" caption="按状态异常与基线偏离识别" />
      </section>

      <div class="content-grid">
        <SectionCard eyebrow="Modules" title="模块责任区" description="这一版结构已经适合按模块分工。">
          <div class="module-list">
            <article v-for="module in modules" :key="module.title" class="module-item">
              <div>
                <h3>{{ module.title }}</h3>
                <p>{{ module.description }}</p>
              </div>
              <span class="module-tag">{{ module.status }}</span>
            </article>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Metadata" title="数据元信息" description="第一次任务分发前最应该冻结的就是这些信息。">
          <div class="meta-grid">
            <div class="meta-item">
              <span>时间范围</span>
              <strong>{{ datasetMeta.time_range.start }} 至 {{ datasetMeta.time_range.end }}</strong>
            </div>
            <div class="meta-item">
              <span>字段数量</span>
              <strong>{{ datasetMeta.fields.length }}</strong>
            </div>
            <div class="meta-item">
              <span>建筑列表</span>
              <strong>{{ buildings.map((item) => item.building_name).join("、") }}</strong>
            </div>
          </div>
          <div class="field-chip-list">
            <span v-for="field in visibleFields" :key="field" class="field-chip">{{ field }}</span>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Workflow" title="当前协作节奏" description="你后续给另外三个人分工时，直接以这条节奏推进即可。">
          <ol class="ordered-list">
            <li>先冻结字段、接口和目录责任区</li>
            <li>第一轮任务只做可接入的基础版</li>
            <li>中间整合一次，统一前后端和数据口径</li>
            <li>第二轮再补完整功能、交互和测试</li>
          </ol>
        </SectionCard>

        <SectionCard eyebrow="Docs" title="关键文档" description="这些文档已经补齐，足够支撑第一次任务分发。">
          <ul class="endpoint-list">
            <li>docs/06-api-contract.md</li>
            <li>docs/07-collaboration-rules.md</li>
            <li>docs/08-integration-checklist.md</li>
            <li>docs/09-testing-plan.md</li>
          </ul>
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'data'">
      <div class="content-grid content-grid--single">
        <SectionCard eyebrow="Filters" title="数据浏览" description="这里是前端与后端第一次联调时最先要跑通的模块。">
          <FilterToolbar
            :buildings="buildings"
            :loading="loading.records"
            @filterChange="handleFilterChange"
          />
          
          <div v-if="loading.records" class="data-loading">
            <LoadingSpinner text="正在加载数据..." />
          </div>
          <div v-else-if="records.length === 0" class="data-empty">
            <EmptyState 
              icon="🔍"
              title="暂无数据"
              description="当前筛选条件下没有找到符合条件的记录"
              actionText="重置筛选"
              @action="resetFilters"
            />
          </div>
          <DataTable v-else :columns="recordColumns" :rows="records" empty-text="没有查到符合条件的记录" />
        </SectionCard>

        <SectionCard eyebrow="Contract" title="字段冻结说明" description="这一块非常适合第一次任务分发时统一给所有人。">
          <ul class="bullet-list">
            <li>字段名以数据字典为准，不允许前端自己改口径</li>
            <li>时间字段统一使用字符串格式 `YYYY-MM-DD HH:mm:ss`</li>
            <li>原始记录查询接口统一返回 `items` 数组</li>
            <li>新增字段前先更新数据字典和 API 契约</li>
          </ul>
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'analytics'">
      <div class="content-grid">
        <SectionCard eyebrow="Trend" title="日度能耗趋势" description="目前使用真实接口数据驱动轻量图形占位。">
          <div class="chart-placeholder">
            <div class="chart-placeholder__bars chart-placeholder__bars--dense">
              <div v-for="item in latestTrendPoints" :key="item.timestamp" class="trend-bar-wrap">
                <span
                  class="trend-bar"
                  :style="{ height: `${Math.max((item.electricity_kwh / trendMax) * 100, 8)}%` }"
                ></span>
                <small>{{ item.timestamp.slice(5, 10) }}</small>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Comparison" title="建筑对比" description="适合后续接 ECharts 柱状图或雷达图。">
          <div class="comparison-list">
            <article v-for="item in topComparison" :key="item.building_id" class="comparison-item">
              <div>
                <strong>{{ item.building_name }}</strong>
                <span>{{ item.building_type }}</span>
              </div>
              <div class="comparison-values">
                <span>电耗 {{ item.electricity_kwh }}</span>
                <span>COP {{ item.average_cop }}</span>
              </div>
            </article>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Ranking" title="COP 排名" description="这里已经是后端真实计算结果。">
          <ul class="endpoint-list">
            <li v-for="item in analytics.copRanking" :key="item.building_id">
              {{ item.building_name }} · COP {{ item.average_cop }}
            </li>
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Anomaly" title="异常原因分布" description="异常明细和原因计数都已可用。">
          <ul class="endpoint-list">
            <li v-for="item in analytics.anomalyReasons" :key="item.anomaly_reason">
              {{ item.anomaly_reason }} · {{ item.count }} 条
            </li>
          </ul>
        </SectionCard>

        <SectionCard eyebrow="Details" title="异常明细" description="这个表格适合后续补颜色标记、导出和设备详情。">
          <DataTable :columns="anomalyColumns" :rows="analytics.anomalies.slice(0, 10)" empty-text="暂无异常" />
        </SectionCard>
      </div>
    </template>

    <template v-else>
      <div class="content-grid content-grid--assistant">
        <SectionCard eyebrow="Assistant" title="智能问答工作区" description="当前为规则化占位，已经能用于第一次联调和演示。">
          <AssistantPanel
            :loading="loading.assistant"
            :reply="assistantReply"
            :suggestions="defaultQuestions"
            @ask="handleAsk"
          />
        </SectionCard>

        <SectionCard eyebrow="Knowledge Base" title="知识库准备情况" description="AI 同学后续主要会在这里继续深化。">
          <ul class="bullet-list">
            <li>knowledge_base/manuals/operation_guide.md</li>
            <li>knowledge_base/glossary/energy_terms.md</li>
            <li>knowledge_base/faq/typical_questions.md</li>
            <li>后续可继续补充 SOP、设备手册、异常规则和 FAQ</li>
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

@media (max-width: 768px) {
  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>

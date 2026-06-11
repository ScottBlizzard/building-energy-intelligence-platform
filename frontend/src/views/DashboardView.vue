<script setup>
import { computed, defineAsyncComponent, onMounted, reactive, ref, watch } from "vue";

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
import BuildingRiskScene from "../components/BuildingRiskScene.vue";
import BudgetPanel from "../components/BudgetPanel.vue";
import ROIPanel from "../components/ROIPanel.vue";
import {
  acceptPersistentWorkOrder,
  assignPersistentWorkOrder,
  createAutoConfirmQueue,
  createPersistentWorkOrder,
  downloadCsvExport,
  fetchAdminDashboard,
  fetchAnomalyExplanation,
  fetchAnomalies,
  fetchAnomalyReasons,
  fetchAssistantProviders,
  fetchBuildingComparison,
  fetchBuildings,
  fetchCopRanking,
  fetchCounterfactualScenario,
  fetchCurrentUser,
  fetchDatasetMeta,
  fetchDecisionDispatchPlan,
  fetchDecisionPriorities,
  fetchDemoUsers,
  fetchEquipmentSummary,
  fetchFloorRegistry,
  fetchFloorSummary,
  fetchOverview,
  fetchOperationReport,
  fetchOptimizationRecommendations,
  fetchPersistentWorkOrders,
  fetchRecords,
  fetchTimeSummary,
  fetchWorkerDashboard,
  fetchWorkOrders,
  ignorePersistentWorkOrder,
  loginUser,
  queryAssistant,
  reviewPersistentWorkOrder,
  submitPersistentWorkOrder,
  updatePersistentWorkOrder,
  fetchSimState,
  startSimulation,
  advanceSimulation,
  resetSimulation,
  resetDemo,
  setApiOperator
} from "../lib/api";

const TrendChart = defineAsyncComponent(() => import("../components/TrendChart.vue"));
const BuildingComparisonChart = defineAsyncComponent(() =>
  import("../components/BuildingComparisonChart.vue")
);
const AnomalyReasonChart = defineAsyncComponent(() =>
  import("../components/AnomalyReasonChart.vue")
);

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
    floorLabel: "",
    startTime: "",
    endTime: "",
    limit: 10
  };
}

function createDefaultAnalysisFilters() {
  return {
    buildingId: "",
    floorLabel: "",
    startTime: "",
    endTime: ""
  };
}

const WORK_ORDER_STORAGE_KEY = "building-energy-work-order-state";
const AUTH_STORAGE_KEY = "building-energy-auth-state";

function loadPersistedWorkOrderState() {
  if (typeof window === "undefined") {
    return { statusById: {}, notesById: {}, generatedOrders: [], submitDrafts: {}, reviewNotes: {}, assignmentById: {} };
  }

  try {
    const raw = window.localStorage.getItem(WORK_ORDER_STORAGE_KEY);
    return raw
      ? JSON.parse(raw)
      : { statusById: {}, notesById: {}, generatedOrders: [], submitDrafts: {}, reviewNotes: {}, assignmentById: {} };
  } catch {
    return { statusById: {}, notesById: {}, generatedOrders: [], submitDrafts: {}, reviewNotes: {}, assignmentById: {} };
  }
}

function loadAuthState() {
  if (typeof window === "undefined") {
    return { user: null, token: "" };
  }

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : { user: null, token: "" };
  } catch {
    return { user: null, token: "" };
  }
}

const activeTab = ref("overview");
const persistedAuthState = loadAuthState();
const currentUser = ref(persistedAuthState.user || null);
const authToken = ref(persistedAuthState.token || "");
setApiOperator(currentUser.value?.user_id || null);
const simClock = ref({ active: false, current_date: null, interventions: [], data_range: {} });
const simLoading = ref(false);
const loginForm = reactive({
  username: persistedAuthState.user?.user_id || "admin",
  password: persistedAuthState.user?.role === "worker" ? "worker123" : "admin123"
});
const loggingIn = ref(false);
const loginError = ref("");
const apiStatus = reactive({
  message: "正在尝试连接后端接口...",
  type: "info"
});
const overview = ref(createEmptyOverview());

const datasetMeta = ref(createEmptyDatasetMeta());

const buildings = ref([]);
const records = ref([]);
const assistantReply = ref(null);
const anomalyExplanation = ref(null);
const selectedAnomalyKey = ref("");
const assistantProviders = ref({
  enabled: false,
  default_provider: "",
  default_model: "",
  options: []
});
const demoUsers = ref([]);
const adminDashboard = ref(null);
const workerDashboard = ref(null);
const selectedAssistantModelKey = ref("");
const recordSummary = reactive({
  count: 0,
  totalFilteredCount: 0
});
const loading = reactive({
  overview: false,
  records: false,
  analytics: false,
  assistant: false,
  explanation: false,
  orders: false,
  decision: false,
  report: false
});
const errors = reactive({
  overview: "",
  records: "",
  analytics: "",
  assistant: "",
  export: "",
  orders: "",
  decision: "",
  report: ""
});
const exportState = reactive({
  loading: false,
  lastFile: ""
});

const recordFilters = reactive(createDefaultRecordFilters());
const analysisFilters = reactive(createDefaultAnalysisFilters());
const persistedWorkOrderState = loadPersistedWorkOrderState();
const workOrderState = reactive({
  statusById: persistedWorkOrderState.statusById || {},
  notesById: persistedWorkOrderState.notesById || {},
  generatedOrders: persistedWorkOrderState.generatedOrders || [],
  submitDrafts: persistedWorkOrderState.submitDrafts || {},
  reviewNotes: persistedWorkOrderState.reviewNotes || {},
  assignmentById: persistedWorkOrderState.assignmentById || {}
});
const orderDraft = reactive({
  buildingId: "",
  floorLabel: "",
  anomalyKey: "",
  assigneeId: "worker_ahu"
});
const simulation = reactive({
  temperatureDelta: 1,
  nightShutdownHours: 1,
  electricityPrice: 0.82
});

const decisionState = reactive({
  workerCapacity: 3,
  priorities: [],
  dispatchPlan: null,
  counterfactual: null,
  counterfactualLoading: false,
  counterfactualError: ""
});

const analytics = reactive({
  timeSummary: [],
  globalTimeSummary: [],
  buildingComparison: [],
  copRanking: [],
  anomalies: [],
  anomalyReasons: [],
  floorSummary: [],
  floorRegistry: [],
  globalFloorSummary: [],
  globalAnomalies: [],
  equipmentSummary: [],
  workOrders: [],
  recommendations: [],
  operationReport: null
});

const adminTabs = [
  { key: "overview", label: "总览" },
  { key: "data", label: "数据浏览" },
  { key: "analytics", label: "统计分析" },
  { key: "orders", label: "工单中心" },
  { key: "budget", label: "预算管理" },
  { key: "roi", label: "改造分析" },
  { key: "report", label: "决策报告" },
  { key: "assistant", label: "智能问答" }
];
const workerTabs = [
  { key: "worker", label: "我的工单" },
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
  "科研实验楼D哪一层异常最多？",
  "哪些设备需要优先维护？",
  "生成当前异常处置建议",
  "有什么节能优化建议？",
  "当前样例数据的平均 COP 是多少？",
  "为什么实验楼电耗这么高？",
  "这些数据是纯随机生成的吗？"
];

const recordColumns = [
  { key: "record_id", label: "记录 ID" },
  { key: "building_name", label: "建筑" },
  { key: "floor_label", label: "楼层" },
  { key: "zone_name", label: "区域" },
  { key: "timestamp", label: "时间" },
  { key: "electricity_kwh", label: "电耗(kWh)" },
  { key: "water_m3", label: "水耗(m³)" },
  { key: "hvac_kwh", label: "空调电耗(kWh)" },
  { key: "cooling_load_kwh", label: "制冷量(kWh)" },
  { key: "environment_temp_c", label: "室外温度(℃)" },
  { key: "humidity_rh", label: "湿度(%)" },
  { key: "occupancy_density_per_100m2", label: "占用密度" },
  { key: "equipment_type", label: "设备类型" },
  { key: "equipment_id", label: "设备 ID" },
  { key: "equipment_status", label: "设备状态" }
];

const anomalyColumns = [
  { key: "building_name", label: "建筑" },
  { key: "timestamp", label: "时间" },
  { key: "equipment_id", label: "设备" },
  { key: "equipment_status", label: "状态" },
  { key: "anomaly_reason", label: "原因" },
  { key: "severity", label: "等级" },
  { key: "risk_score", label: "风险分" },
  { key: "wasted_cost_yuan", label: "损失(元)" }
];

const floorColumns = [
  { key: "building_name", label: "建筑" },
  { key: "floor_label", label: "楼层" },
  { key: "zone_name", label: "区域" },
  { key: "electricity_kwh", label: "电耗(kWh)" },
  { key: "average_cop", label: "COP" },
  { key: "anomaly_count", label: "异常数" },
  { key: "anomaly_rate", label: "异常率(%)" },
  { key: "operation_focus", label: "运维判断" }
];

const equipmentColumns = [
  { key: "building_name", label: "建筑" },
  { key: "equipment_id", label: "设备" },
  { key: "equipment_type", label: "类型" },
  { key: "floor_label", label: "楼层" },
  { key: "zone_name", label: "区域" },
  { key: "latest_status", label: "最新状态" },
  { key: "average_cop", label: "COP" },
  { key: "anomaly_count", label: "异常数" },
  { key: "priority", label: "优先级" },
  { key: "maintenance_hint", label: "维护建议" }
];

const workOrderColumns = [
  { key: "work_order_id", label: "工单号" },
  { key: "priority", label: "优先级" },
  { key: "building_name", label: "建筑" },
  { key: "floor_label", label: "楼层" },
  { key: "equipment_id", label: "设备" },
  { key: "anomaly_reason", label: "异常原因" },
  { key: "risk_score", label: "风险分" },
  { key: "wasted_cost_yuan", label: "损失(元)" },
  { key: "recommended_action", label: "处置建议" },
  { key: "owner_role", label: "负责人" }
];

const recommendationColumns = [
  { key: "building_name", label: "建筑" },
  { key: "category", label: "类别" },
  { key: "priority", label: "优先级" },
  { key: "finding", label: "发现" },
  { key: "action", label: "建议动作" },
  { key: "expected_impact", label: "预期效果" }
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
const availableFloorOptions = computed(() => {
  const floors = new Map();
  analytics.globalFloorSummary
    .filter((item) => !recordFilters.buildingId || item.building_id === recordFilters.buildingId)
    .forEach((item) => {
      const current = floors.get(item.floor_label) || {
        label: item.floor_label,
        anomalyCount: 0,
        buildingCount: new Set()
      };
      current.anomalyCount += Number(item.anomaly_count || 0);
      current.buildingCount.add(item.building_id);
      floors.set(item.floor_label, current);
    });

  return Array.from(floors.values())
    .map((item) => ({
      label: item.label,
      anomalyCount: item.anomalyCount,
      buildingCount: item.buildingCount.size
    }))
    .sort((a, b) => floorSortValue(a.label) - floorSortValue(b.label));
});
const availableAnalysisFloorOptions = computed(() => {
  const floors = new Map();
  analytics.globalFloorSummary
    .filter((item) => !analysisFilters.buildingId || item.building_id === analysisFilters.buildingId)
    .forEach((item) => {
      const current = floors.get(item.floor_label) || {
        label: item.floor_label,
        anomalyCount: 0,
        buildingCount: new Set()
      };
      current.anomalyCount += Number(item.anomaly_count || 0);
      current.buildingCount.add(item.building_id);
      floors.set(item.floor_label, current);
    });

  return Array.from(floors.values())
    .map((item) => ({
      label: item.label,
      anomalyCount: item.anomalyCount,
      buildingCount: item.buildingCount.size
    }))
    .sort((a, b) => floorSortValue(a.label) - floorSortValue(b.label));
});
const activeFilterSummary = computed(() => {
  const parts = [];

  if (recordFilters.buildingId) {
    const match = buildings.value.find((item) => item.building_id === recordFilters.buildingId);
    parts.push(`建筑：${match?.building_name || recordFilters.buildingId}`);
  } else {
    parts.push("建筑：全部");
  }

  if (recordFilters.floorLabel) {
    parts.push(`楼层：${recordFilters.floorLabel}`);
  } else {
    parts.push("楼层：全部");
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
const activeAnalysisSummary = computed(() => {
  const parts = [];

  if (analysisFilters.buildingId) {
    const match = buildings.value.find((item) => item.building_id === analysisFilters.buildingId);
    parts.push(`建筑：${match?.building_name || analysisFilters.buildingId}`);
  } else {
    parts.push("建筑：全部");
  }

  parts.push(analysisFilters.floorLabel ? `楼层：${analysisFilters.floorLabel}` : "楼层：全部");

  if (analysisFilters.startTime) {
    parts.push(`开始：${analysisFilters.startTime.replace("T", " ")}`);
  }
  if (analysisFilters.endTime) {
    parts.push(`结束：${analysisFilters.endTime.replace("T", " ")}`);
  }

  return parts.join(" · ");
});
const orderStatusOptions = [
  { key: "pending_confirm", label: "待确认" },
  { key: "assigned", label: "已派单" },
  { key: "in_progress", label: "处理中" },
  { key: "pending_review", label: "待复核" },
  { key: "rejected", label: "已驳回" },
  { key: "closed", label: "已关闭" },
  { key: "ignored", label: "已忽略" }
];
const orderAssignees = [
  "楼层巡检员-李明",
  "空调系统运维员-王强",
  "制冷机房值班员-赵磊",
  "能源管理员-陈晨"
];
const legacyStatusMap = {
  处理中: "in_progress",
  已完成: "closed",
  已忽略: "ignored"
};
const statusLabelMap = Object.fromEntries(orderStatusOptions.map((item) => [item.key, item.label]));
const statusRank = {
  pending_confirm: 0,
  assigned: 1,
  in_progress: 2,
  rejected: 3,
  pending_review: 4,
  closed: 5,
  ignored: 6
};
const priorityRank = {
  高: 0,
  中: 1,
  低: 2
};
const visibleTabs = computed(() => (currentUser.value?.role === "worker" ? workerTabs : adminTabs));
const isAuthenticated = computed(() => Boolean(currentUser.value && authToken.value));
const isAdmin = computed(() => currentUser.value?.role === "admin");
const isWorker = computed(() => currentUser.value?.role === "worker");
const workerUsers = computed(() => demoUsers.value.filter((item) => item.role === "worker"));
const selectedAssignee = computed(
  () =>
    workerUsers.value.find((item) => item.user_id === orderDraft.assigneeId) ||
    workerUsers.value[0] ||
    null
);
const analysisHealthState = computed(() => {
  if (!analysisFilters.floorLabel || loading.analytics || analytics.anomalies.length) {
    return null;
  }

  const summary = analytics.floorSummary[0];
  if (summary) {
    return {
      title: "当前分析范围未发现异常",
      description: `${summary.building_name} ${summary.floor_label} ${summary.zone_name} 当前无异常记录，可作为正常运行楼层观察。`,
      metrics: [
        { label: "记录数", value: summary.record_count },
        { label: "设备数", value: summary.equipment_count },
        { label: "电耗(kWh)", value: summary.electricity_kwh },
        { label: "平均 COP", value: summary.average_cop }
      ]
    };
  }

  return {
    title: "当前楼层运行非常健康",
    description: "该楼层当前没有识别到异常记录，整体运行状态稳定，可作为正常楼层对照样本。",
    metrics: [
      { label: "异常数", value: 0 },
      { label: "运行状态", value: "健康" }
    ]
  };
});
const enrichedWorkOrders = computed(() =>
  workOrderState.generatedOrders.map((item) => ({
    ...item,
    status: normalizeOrderStatus(workOrderState.statusById[item.work_order_id] || item.status || "pending_confirm"),
    status_label: item.status_label || statusLabelMap[normalizeOrderStatus(item.status)] || item.status_label || item.status,
    note: workOrderState.notesById[item.work_order_id] ?? item.note ?? "",
    assignee_id: item.assignee_id || "",
    assignee_name: item.assignee_name || item.owner_role || "",
    timeline: Array.isArray(item.timeline) ? item.timeline : []
  }))
);
const roleScopedWorkOrders = computed(() => {
  if (!isWorker.value) {
    return enrichedWorkOrders.value;
  }
  return enrichedWorkOrders.value.filter((item) => item.assignee_id === currentUser.value?.user_id);
});
const sortedWorkOrders = computed(() => {
  return [...roleScopedWorkOrders.value].sort((a, b) => {
    const statusDiff = (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9);
    if (statusDiff !== 0) {
      return statusDiff;
    }

    const priorityDiff = (priorityRank[a.priority] ?? 9) - (priorityRank[b.priority] ?? 9);
    if (priorityDiff !== 0) {
      return priorityDiff;
    }

    return String(b.timestamp || "").localeCompare(String(a.timestamp || ""));
  });
});
const orderStats = computed(() => {
  const stats = Object.fromEntries(orderStatusOptions.map((item) => [item.key, 0]));
  roleScopedWorkOrders.value.forEach((item) => {
    stats[item.status] = (stats[item.status] || 0) + 1;
  });
  return stats;
});
const adminClosureRate = computed(() => {
  const metrics = adminDashboard.value?.work_order_metrics;
  const total = Number(metrics?.total || roleScopedWorkOrders.value.length || 0);
  const closed = Number(metrics?.closed || orderStats.value.closed || 0);
  return total ? `${Math.round((closed / total) * 100)}%` : "0%";
});
const workerActionableOrders = computed(() =>
  sortedWorkOrders.value.filter((item) => ["assigned", "in_progress", "rejected"].includes(item.status))
);
const pendingReviewOrders = computed(() =>
  sortedWorkOrders.value.filter((item) => item.status === "pending_review")
);
const adminNextActions = computed(() =>
  adminDashboard.value?.next_actions?.length
    ? adminDashboard.value.next_actions
    : [
        "复核待复核工单，及时关闭已恢复问题。",
        "为高风险异常派单，避免停留在监测告警阶段。",
        "将已关闭工单纳入今日运营日报。"
      ]
);
const availableOrderFloorOptions = computed(() => {
  const floors = new Map();
  analytics.globalAnomalies
    .filter((item) => !orderDraft.buildingId || item.building_id === orderDraft.buildingId)
    .forEach((item) => {
      const current = floors.get(item.floor_label) || { label: item.floor_label, count: 0 };
      current.count += 1;
      floors.set(item.floor_label, current);
    });

  return Array.from(floors.values()).sort((a, b) => floorSortValue(a.label) - floorSortValue(b.label));
});
const availableOrderAnomalies = computed(() =>
  analytics.globalAnomalies
    .filter((item) => !orderDraft.buildingId || item.building_id === orderDraft.buildingId)
    .filter((item) => !orderDraft.floorLabel || item.floor_label === orderDraft.floorLabel)
);
const selectedOrderAnomaly = computed(() =>
  availableOrderAnomalies.value.find((item) => anomalyKey(item) === orderDraft.anomalyKey)
);
const selectedAnomaly = computed(() =>
  analytics.anomalies.find((item) => anomalyKey(item) === selectedAnomalyKey.value)
);
const decisionByWorkOrderId = computed(() => {
  const map = new Map();
  decisionState.priorities.forEach((item) => {
    if (item.work_order_id) {
      map.set(item.work_order_id, item);
    }
  });
  return map;
});
const selectedOrderDecision = computed(() => {
  if (!selectedOrderAnomaly.value) {
    return null;
  }
  return decisionState.priorities.find(
    (item) => item.equipment_id === selectedOrderAnomaly.value.equipment_id
  ) || null;
});
const highPriorityOrders = computed(() =>
  enrichedWorkOrders.value.filter((item) => item.priority === "高").slice(0, 6)
);
const orderBusinessStats = computed(() => {
  const closedStatuses = new Set(["closed", "ignored", "已关闭", "已完成", "已忽略"]);
  return enrichedWorkOrders.value.reduce(
    (stats, item) => {
      stats.totalWastedCost += Number(item.wasted_cost_yuan || 0);
      stats.totalSaving += Number(item.estimated_saving_yuan || 0);
      stats.totalCarbon += Number(item.carbon_kg || 0);
      if (!closedStatuses.has(item.status)) {
        stats.openCount += 1;
      }
      if (item.status === "pending_review" || item.status === "待验证") {
        stats.pendingVerifyCount += 1;
      }
      if (item.priority === "高" || Number(item.risk_score || 0) >= 72) {
        stats.highRiskCount += 1;
      }
      return stats;
    },
    {
      totalWastedCost: 0,
      totalSaving: 0,
      totalCarbon: 0,
      openCount: 0,
      pendingVerifyCount: 0,
      highRiskCount: 0
    }
  );
});
const anomalyBusinessStats = computed(() =>
  analytics.anomalies.reduce(
    (stats, item) => {
      stats.totalWastedKwh += Number(item.wasted_kwh || 0);
      stats.totalWastedCost += Number(item.wasted_cost_yuan || 0);
      stats.totalSaving += Number(item.estimated_saving_yuan || 0);
      stats.totalCarbon += Number(item.carbon_kg || 0);
      return stats;
    },
    {
      totalWastedKwh: 0,
      totalWastedCost: 0,
      totalSaving: 0,
      totalCarbon: 0
    }
  )
);
const forecastSeries = computed(() => {
  const points = (analytics.globalTimeSummary.length ? analytics.globalTimeSummary : analytics.timeSummary).slice(-10);
  if (!points.length) {
    return [];
  }

  const values = points.map((item) => Number(item.electricity_kwh || 0));
  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  const trend = values.length > 1 ? (values[values.length - 1] - values[0]) / values.length : 0;

  return Array.from({ length: 7 }, (_, index) => {
    const seasonal = Math.sin((index + 1) / 7 * Math.PI) * average * 0.035;
    return {
      day: `D+${index + 1}`,
      electricity_kwh: Math.max(0, Math.round(average + trend * (index + 1) + seasonal))
    };
  });
});
const forecastMax = computed(() =>
  Math.max(...forecastSeries.value.map((item) => item.electricity_kwh || 0), 1)
);
const projectedWeekKwh = computed(() =>
  forecastSeries.value.reduce((sum, item) => sum + item.electricity_kwh, 0)
);
const simulationResult = computed(() => {
  const hvacBase = Number(overview.value.totals?.hvac_kwh || 0);
  const electricityBase = Number(overview.value.totals?.electricity_kwh || 0);
  const temperatureSavingRate = Number(simulation.temperatureDelta || 0) * 0.045;
  const shutdownSavingRate = Number(simulation.nightShutdownHours || 0) * 0.012;
  const savingKwh = hvacBase * temperatureSavingRate + electricityBase * shutdownSavingRate;
  const savingCost = savingKwh * Number(simulation.electricityPrice || 0);

  return {
    savingKwh: Math.round(savingKwh),
    savingCost: Math.round(savingCost),
    savingRate: electricityBase ? ((savingKwh / electricityBase) * 100).toFixed(1) : "0.0"
  };
});
const operationReport = computed(() => {
  if (analytics.operationReport?.title) {
    return {
      title: analytics.operationReport.title,
      overview: analytics.operationReport.overview,
      risk: analytics.operationReport.risk,
      latestAnomaly: analytics.operationReport.latest_anomaly,
      workOrder: analytics.operationReport.work_order,
      workOrderClosure: analytics.operationReport.work_order_closure,
      closedCases: analytics.operationReport.closed_cases || [],
      businessSummary: analytics.operationReport.business_summary,
      verificationSummary: analytics.operationReport.verification_summary,
      businessImpact: analytics.operationReport.business_impact || {},
      forecast: analytics.operationReport.forecast,
      saving: `按当前模拟策略，预计节电 ${formatNumber(simulationResult.value.savingKwh)} kWh，节约约 ${formatNumber(simulationResult.value.savingCost)} 元。`,
      recommendation: analytics.operationReport.recommendation,
      actionItems: analytics.operationReport.action_items || [],
      generatedAt: analytics.operationReport.generated_at
    };
  }

  const topOrder = highPriorityOrders.value[0];
  const topRecommendation = analytics.recommendations[0];

  return {
    title: "本周期能源运营报告",
    generatedAt: "",
    closedCases: [],
    overview: `当前覆盖 ${overview.value.building_count || 0} 栋建筑、${overview.value.total_records || 0} 条记录，平均 COP 为 ${overview.value.average_cop || 0}。`,
    risk: topOrder
      ? `优先处理 ${topOrder.building_name} ${topOrder.floor_label} 的 ${topOrder.equipment_id}，原因是${topOrder.anomaly_reason}。`
      : "当前没有需要优先处理的异常工单。",
    latestAnomaly: analytics.anomalies[0]
      ? `最近异常：${analytics.anomalies[0].building_name} ${analytics.anomalies[0].floor_label}，${analytics.anomalies[0].anomaly_reason}。`
      : "当前筛选范围暂无异常。",
    workOrder: `${sortedWorkOrders.value.filter((item) => !isOrderClosed(item)).length} 个工单未完成。`,
    workOrderClosure: `${orderStats.value.closed || 0} 个工单已复核关闭，可作为日报归档案例。`,
    businessSummary: `异常估算浪费 ${formatNumber(anomalyBusinessStats.value.totalWastedKwh)} kWh，约 ${formatNumber(anomalyBusinessStats.value.totalWastedCost)} 元。`,
    verificationSummary: `当前工单估算可回收 ${formatNumber(orderBusinessStats.value.totalSaving)} 元，待验证任务需用下一采样周期数据关闭。`,
    businessImpact: {
      total_wasted_kwh: anomalyBusinessStats.value.totalWastedKwh,
      total_wasted_cost_yuan: anomalyBusinessStats.value.totalWastedCost,
      total_estimated_saving_yuan: anomalyBusinessStats.value.totalSaving,
      total_carbon_kg: anomalyBusinessStats.value.totalCarbon
    },
    forecast: `未来 7 天预测电耗约 ${formatNumber(projectedWeekKwh.value)} kWh。`,
    saving: `按当前模拟策略，预计节电 ${formatNumber(simulationResult.value.savingKwh)} kWh，节约约 ${formatNumber(simulationResult.value.savingCost)} 元。`,
    recommendation: topRecommendation
      ? `${topRecommendation.building_name}：${topRecommendation.action}`
      : "建议保持日报监测，重点关注 COP、夜间负荷和设备状态。",
    actionItems: [
      "优先处理高优先级工单。",
      "复核异常集中楼层的设备运行状态。",
      "跟踪未来 7 天预测负荷变化。"
    ]
  };
});

function floorSortValue(label = "") {
  if (label.startsWith("B")) {
    return 0;
  }
  if (label.startsWith("RF")) {
    return 99;
  }
  const match = label.match(/(\d+)F/);
  return match ? Number(match[1]) : 50;
}

function formatNumber(value, options = {}) {
  return Number(value || 0).toLocaleString("zh-CN", options);
}

function normalizeOrderStatus(status) {
  return legacyStatusMap[status] || status || "pending_confirm";
}

function getOrderStatusLabel(orderOrStatus) {
  const status = typeof orderOrStatus === "string" ? orderOrStatus : orderOrStatus?.status;
  const normalized = normalizeOrderStatus(status);
  if (typeof orderOrStatus === "object" && orderOrStatus?.status_label) {
    return orderOrStatus.status_label;
  }
  return statusLabelMap[normalized] || status || "待确认";
}

function isOrderClosed(order) {
  return ["closed", "ignored"].includes(normalizeOrderStatus(order?.status));
}

function anomalyKey(item) {
  return `${item.record_id}-${item.timestamp}-${item.equipment_id}`;
}

function inferOrderPriority(anomaly) {
  if (anomaly?.severity === "高" || Number(anomaly?.risk_score || 0) >= 72) {
    return "高";
  }
  if (anomaly?.severity === "中" || Number(anomaly?.risk_score || 0) >= 48) {
    return "中";
  }
  if (anomaly?.anomaly_reason === "设备状态异常") {
    return "高";
  }
  if (Number(anomaly?.average_cop || 3) < 2.5) {
    return "中";
  }
  return "中";
}

function inferOwnerRole(anomaly) {
  if (anomaly?.equipment_type === "冷水机组" || anomaly?.equipment_type === "冷却塔") {
    return "制冷机房值班员";
  }
  if (anomaly?.equipment_type === "空气处理机组") {
    return "空调系统运维员";
  }
  return "楼层巡检员";
}

function inferRecommendedAction(anomaly) {
  if (anomaly?.equipment_type === "冷却塔") {
    return "检查冷却塔风机、喷淋、补水和冷却水回水温度。";
  }
  if (anomaly?.equipment_type === "冷水机组") {
    return "检查主机负载率、供回水温差和冷凝压力。";
  }
  if (anomaly?.equipment_type === "空气处理机组") {
    return "核对运行时间表，检查新风阀、过滤网和风机频率。";
  }
  return "安排现场巡检，复核末端阀门、房间占用状态和设定温度。";
}

function orderStatusRank(status) {
  return {
    pending_confirm: 0,
    assigned: 1,
    in_progress: 2,
    rejected: 3,
    pending_review: 4,
    closed: 5,
    ignored: 6,
    待分派: 0,
    处理中: 2,
    待验证: 4,
    已关闭: 5,
    已完成: 5,
    已忽略: 6
  }[status] ?? 9;
}

function toDateTimeLocal(value) {
  if (!value || value === "-") {
    return "";
  }
  return value.replace(" ", "T").slice(0, 16);
}

function buildFilterParams({ includeLimit = false, includeFloor = false } = {}) {
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
  if (includeFloor && recordFilters.floorLabel) {
    params.floor_label = recordFilters.floorLabel;
  }
  if (includeLimit) {
    params.limit = recordFilters.limit;
  }

  return params;
}

function buildAnalysisFilterParams({ includeFloor = true } = {}) {
  const params = {};

  if (analysisFilters.buildingId) {
    params.building_id = analysisFilters.buildingId;
  }
  if (analysisFilters.startTime) {
    params.start_time = analysisFilters.startTime;
  }
  if (analysisFilters.endTime) {
    params.end_time = analysisFilters.endTime;
  }
  if (includeFloor && analysisFilters.floorLabel) {
    params.floor_label = analysisFilters.floorLabel;
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

function buildModelKey(provider, model) {
  return provider && model ? `${provider}::${model}` : "";
}

function parseSelectedAssistantModel() {
  if (!selectedAssistantModelKey.value) {
    return null;
  }
  const [provider, ...modelParts] = selectedAssistantModelKey.value.split("::");
  const model = modelParts.join("::");
  return provider && model ? { provider, model } : null;
}

function selectDefaultAssistantModel() {
  const options = assistantProviders.value.options || [];
  const defaultKey = buildModelKey(
    assistantProviders.value.default_provider,
    assistantProviders.value.default_model
  );
  const defaultOption = options.find(
    (item) => item.configured && buildModelKey(item.provider, item.model) === defaultKey
  );
  const firstConfigured = options.find((item) => item.configured);
  selectedAssistantModelKey.value = buildModelKey(
    defaultOption?.provider || firstConfigured?.provider,
    defaultOption?.model || firstConfigured?.model
  );
}

function persistAuthState() {
  setApiOperator(currentUser.value?.user_id || null);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ user: currentUser.value, token: authToken.value })
    );
  }
}

function clearAuthState() {
  currentUser.value = null;
  authToken.value = "";
  adminDashboard.value = null;
  workerDashboard.value = null;
  setApiOperator(null);
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

function switchToDefaultRoleTab() {
  activeTab.value = isWorker.value ? "worker" : "overview";
}

async function loadDemoUserList() {
  try {
    const payload = await fetchDemoUsers();
    demoUsers.value = payload.items || [];
    if (!orderDraft.assigneeId && workerUsers.value.length) {
      orderDraft.assigneeId = workerUsers.value[0].user_id;
    }
  } catch (error) {
    demoUsers.value = [];
  }
}

async function loadRoleDashboards() {
  if (!isAuthenticated.value) {
    return;
  }

  try {
    if (isAdmin.value) {
      const payload = await fetchAdminDashboard();
      adminDashboard.value = payload.item || payload;
      workerDashboard.value = null;
    } else if (isWorker.value && currentUser.value?.user_id) {
      const payload = await fetchWorkerDashboard(currentUser.value.user_id);
      workerDashboard.value = payload.item || payload;
      adminDashboard.value = null;
    }
  } catch (error) {
    if (isAdmin.value) {
      adminDashboard.value = null;
    } else {
      workerDashboard.value = null;
    }
  }
}

async function loadDecisionState() {
  if (!isAdmin.value) {
    decisionState.priorities = [];
    decisionState.dispatchPlan = null;
    decisionState.counterfactual = null;
    return;
  }

  loading.decision = true;
  errors.decision = "";
  try {
    const [priorities, dispatchPlan] = await Promise.all([
      fetchDecisionPriorities(12),
      fetchDecisionDispatchPlan(decisionState.workerCapacity)
    ]);
    decisionState.priorities = priorities.items || [];
    decisionState.dispatchPlan = dispatchPlan.item || null;
  } catch (error) {
    decisionState.priorities = [];
    decisionState.dispatchPlan = null;
    errors.decision = "经济决策建议暂时不可用，请确认后端 decisions 接口。";
  } finally {
    loading.decision = false;
  }
}

async function loadCounterfactualForEquipment(equipmentId) {
  if (!isAdmin.value || !equipmentId) {
    decisionState.counterfactual = null;
    decisionState.counterfactualError = "";
    return;
  }

  decisionState.counterfactualLoading = true;
  decisionState.counterfactualError = "";
  try {
    const payload = await fetchCounterfactualScenario({
      equipment_id: equipmentId,
      horizon_days: 7,
      delay_days: 3,
      start_date: simClock.value?.current_date || null
    });
    decisionState.counterfactual = payload.item;
  } catch (error) {
    decisionState.counterfactual = null;
    decisionState.counterfactualError = "对照实验生成失败，请确认该设备在样本窗口内存在后续数据。";
  } finally {
    decisionState.counterfactualLoading = false;
  }
}

async function bootstrapAuthenticatedApp() {
  await Promise.allSettled([loadOverview(), loadAssistantProviders(), loadDemoUserList(), loadSimState()]);
  await Promise.allSettled([loadRecords(), loadAnalytics(), loadPersistentWorkOrders(), loadRoleDashboards()]);
  await loadDecisionState();
}

async function loadSimState() {
  try {
    simClock.value = await fetchSimState();
  } catch (error) {
    simClock.value = { active: false, current_date: null, interventions: [], data_range: {} };
  }
}

async function reloadAfterClockChange() {
  await Promise.allSettled([loadOverview(), loadRecords(), loadAnalytics(), refreshBusinessState()]);
  await loadCounterfactualForEquipment(selectedOrderAnomaly.value?.equipment_id);
}

async function handleStartSimulation() {
  simLoading.value = true;
  try {
    simClock.value = await startSimulation(null);
    await reloadAfterClockChange();
  } catch (error) {
    errors.orders = "启动运营沙盘失败，请检查后端 /sim 接口。";
  } finally {
    simLoading.value = false;
  }
}

async function handleAdvanceDay(days = 1) {
  simLoading.value = true;
  try {
    simClock.value = await advanceSimulation(days);
    await reloadAfterClockChange();
  } catch (error) {
    errors.orders = "推进日期失败，请检查后端 /sim 接口。";
  } finally {
    simLoading.value = false;
  }
}

async function handleResetSimulation() {
  simLoading.value = true;
  try {
    simClock.value = await resetSimulation();
    await reloadAfterClockChange();
  } catch (error) {
    errors.orders = "重置运营沙盘失败，请检查后端 /sim 接口。";
  } finally {
    simLoading.value = false;
  }
}

async function handleResetDemo() {
  if (
    typeof window !== "undefined" &&
    !window.confirm("确定要重置演示吗？将清空所有工单与预算、重置时间机器，并预置历史样例后回到初始状态。")
  ) {
    return;
  }
  simLoading.value = true;
  try {
    await resetDemo(true);
    await loadSimState();
    await reloadAfterClockChange();
    await loadRoleDashboards();
  } catch (error) {
    errors.orders = "重置演示失败，请检查后端 /demo 接口。";
  } finally {
    simLoading.value = false;
  }
}

async function handleLogin() {
  loggingIn.value = true;
  loginError.value = "";
  try {
    const payload = await loginUser({
      username: loginForm.username.trim(),
      password: loginForm.password
    });
    currentUser.value = payload.user;
    authToken.value = payload.access_token || payload.token || "";
    persistAuthState();
    switchToDefaultRoleTab();
    await bootstrapAuthenticatedApp();
  } catch (error) {
    loginError.value = "账号或密码不正确，请使用管理员 admin/admin123 或工人 worker_ahu/worker123 登录。";
  } finally {
    loggingIn.value = false;
  }
}

function handleLogout() {
  clearAuthState();
  loginForm.username = "admin";
  loginForm.password = "admin123";
  activeTab.value = "overview";
}

async function restoreSession() {
  if (!authToken.value || !currentUser.value) {
    return;
  }

  try {
    const payload = await fetchCurrentUser(authToken.value);
    currentUser.value = payload.user || payload;
    persistAuthState();
    if (!visibleTabs.value.some((item) => item.key === activeTab.value)) {
      switchToDefaultRoleTab();
    }
    await bootstrapAuthenticatedApp();
  } catch (error) {
    clearAuthState();
    loginError.value = "登录状态已失效，请重新登录。";
  }
}

async function loadAssistantProviders() {
  try {
    assistantProviders.value = await fetchAssistantProviders();
    selectDefaultAssistantModel();
  } catch (error) {
    assistantProviders.value = {
      enabled: false,
      default_provider: "",
      default_model: "",
      options: []
    };
    selectedAssistantModelKey.value = "";
  }
}

async function loadRecords() {
  loading.records = true;
  errors.records = "";
  try {
    const payload = await fetchRecords(buildFilterParams({ includeLimit: true, includeFloor: true }));
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

async function loadAnomalyExplanation(anomaly) {
  if (!anomaly?.record_id) {
    anomalyExplanation.value = null;
    selectedAnomalyKey.value = "";
    return;
  }

  loading.explanation = true;
  selectedAnomalyKey.value = anomalyKey(anomaly);
  try {
    const payload = await fetchAnomalyExplanation(anomaly.record_id);
    anomalyExplanation.value = payload.item;
  } catch (error) {
    anomalyExplanation.value = null;
  } finally {
    loading.explanation = false;
  }
}

async function loadPersistentWorkOrders() {
  loading.orders = true;
  errors.orders = "";
  try {
    const params = isWorker.value
      ? { assignee_id: currentUser.value?.user_id, role: "worker" }
      : {};
    const payload = await fetchPersistentWorkOrders(params);
    workOrderState.generatedOrders.splice(0, workOrderState.generatedOrders.length, ...payload.items);
    payload.items.forEach((item) => {
      workOrderState.statusById[item.work_order_id] = normalizeOrderStatus(item.status || "pending_confirm");
      workOrderState.notesById[item.work_order_id] = item.note || "";
      if (!workOrderState.assignmentById[item.work_order_id]) {
        workOrderState.assignmentById[item.work_order_id] = item.assignee_id || orderDraft.assigneeId;
      }
      ensureOrderDrafts(item);
    });
  } catch (error) {
    errors.orders = "后端工单存储暂时不可用，当前无法同步持久化工单。";
  } finally {
    loading.orders = false;
  }
}

async function loadAnalytics() {
  loading.analytics = true;
  errors.analytics = "";
  try {
    const scopedFilters = buildAnalysisFilterParams({ includeFloor: true });
    const [
      timeSummary,
      globalTimeSummary,
      buildingComparison,
      copRanking,
      anomalies,
      anomalyReasons,
      floorSummary,
      floorRegistry,
      globalFloorSummary,
      globalAnomalies,
      equipmentSummary,
      workOrders,
      recommendations,
      operationReport
    ] = await Promise.all([
      fetchTimeSummary({ ...scopedFilters, freq: "D" }),
      fetchTimeSummary({ freq: "D" }),
      fetchBuildingComparison(),
      fetchCopRanking(),
      fetchAnomalies(scopedFilters),
      fetchAnomalyReasons(scopedFilters),
      fetchFloorSummary(scopedFilters),
      fetchFloorRegistry(scopedFilters),
      fetchFloorSummary(),
      fetchAnomalies(),
      fetchEquipmentSummary(scopedFilters),
      fetchWorkOrders(scopedFilters),
      fetchOptimizationRecommendations(scopedFilters),
      fetchOperationReport(scopedFilters)
    ]);

    analytics.timeSummary = timeSummary.items;
    analytics.globalTimeSummary = globalTimeSummary.items;
    analytics.buildingComparison = buildingComparison.items;
    analytics.copRanking = copRanking.items;
    analytics.anomalies = anomalies.items;
    analytics.anomalyReasons = anomalyReasons.items;
    analytics.floorSummary = floorSummary.items;
    analytics.floorRegistry = floorRegistry.items;
    analytics.globalFloorSummary = globalFloorSummary.items;
    analytics.globalAnomalies = globalAnomalies.items;
    analytics.equipmentSummary = equipmentSummary.items;
    analytics.workOrders = workOrders.items;
    analytics.recommendations = recommendations.items;
    analytics.operationReport = operationReport.item;
    if (analytics.anomalies.length) {
      const stillSelected = analytics.anomalies.find((item) => anomalyKey(item) === selectedAnomalyKey.value);
      await loadAnomalyExplanation(stillSelected || analytics.anomalies[0]);
    } else {
      await loadAnomalyExplanation(null);
    }
  } catch (error) {
    analytics.timeSummary = [];
    analytics.globalTimeSummary = [];
    analytics.buildingComparison = [];
    analytics.copRanking = [];
    analytics.anomalies = [];
    analytics.anomalyReasons = [];
    analytics.floorSummary = [];
    analytics.floorRegistry = [];
    analytics.globalFloorSummary = [];
    analytics.globalAnomalies = [];
    analytics.equipmentSummary = [];
    analytics.workOrders = [];
    analytics.recommendations = [];
    analytics.operationReport = null;
    errors.analytics = "统计分析接口暂时不可用，请先检查后端是否正常运行。";
  } finally {
    loading.analytics = false;
  }
}

async function refreshOperationReport() {
  loading.report = true;
  errors.report = "";
  try {
    const payload = await fetchOperationReport(buildAnalysisFilterParams({ includeFloor: true }));
    analytics.operationReport = payload.item;
  } catch (error) {
    errors.report = "运营日报生成失败，请检查后端分析接口。";
  } finally {
    loading.report = false;
  }
}

async function handleAsk(question) {
  loading.assistant = true;
  errors.assistant = "";
  try {
    assistantReply.value = await queryAssistant(question, parseSelectedAssistantModel());
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

async function handleAnalysisReset() {
  Object.assign(analysisFilters, createDefaultAnalysisFilters());
  await loadAnalytics();
}

async function handleSceneSelectFloor({ buildingId, floorLabel }) {
  analysisFilters.buildingId = buildingId;
  analysisFilters.floorLabel = floorLabel;
  activeTab.value = "analytics";
  errors.export = "";
  exportState.lastFile = "";
  await loadAnalytics();
}

function upsertWorkOrder(updated) {
  if (!updated?.work_order_id) {
    return;
  }

  updated.status = normalizeOrderStatus(updated.status);
  const index = workOrderState.generatedOrders.findIndex(
    (item) => item.work_order_id === updated.work_order_id
  );
  if (index >= 0) {
    workOrderState.generatedOrders.splice(index, 1, updated);
  } else {
    workOrderState.generatedOrders.unshift(updated);
  }
  workOrderState.statusById[updated.work_order_id] = updated.status;
  workOrderState.notesById[updated.work_order_id] = updated.note || workOrderState.notesById[updated.work_order_id] || "";
  workOrderState.assignmentById[updated.work_order_id] = updated.assignee_id || workOrderState.assignmentById[updated.work_order_id] || "";
  ensureOrderDrafts(updated);
}

async function updateWorkOrderStatus(workOrderId, status) {
  workOrderState.statusById[workOrderId] = status;
  const order = enrichedWorkOrders.value.find((item) => item.work_order_id === workOrderId);
  const note = workOrderState.notesById[workOrderId] || "";
  const payload = {
    status,
    note
  };
  if (status === "in_progress") {
    payload.dispatch_action = `已分派给${order?.owner_role || "能源管理员"}处理。`;
  }
  if (status === "pending_review") {
    payload.resolution_action = note || `已按建议动作处理：${order?.recommended_action || "完成现场处置"}`;
    payload.verification_status = "待验证";
  }
  if (status === "closed") {
    payload.verification_status = "通过";
    payload.verification_result = order?.verification_method
      ? `复测通过：${order.verification_method}`
      : "复测通过，异常指标已回落至阈值内。";
  }
  try {
    const updated = await updatePersistentWorkOrder(workOrderId, payload);
    const index = workOrderState.generatedOrders.findIndex((item) => item.work_order_id === workOrderId);
    if (index >= 0) {
      workOrderState.generatedOrders.splice(index, 1, updated);
    }
  } catch (error) {
    errors.orders = "工单状态已在页面更新，但同步到后端失败。";
  }
}

function ensureOrderDrafts(order) {
  const id = order?.work_order_id;
  if (!id) {
    return;
  }
  if (!workOrderState.submitDrafts[id]) {
    workOrderState.submitDrafts[id] = {
      actual_cause: order.actual_cause || "",
      resolution_note: order.resolution_note || "",
      recovery_confirmed: order.recovery_confirmed ?? true,
      parts_used: order.parts_used || "",
      safety_note: order.safety_note || "",
      attachment_name: order.attachment_name || "",
      attachment_note: order.attachment_note || ""
    };
  }
  if (workOrderState.reviewNotes[id] === undefined) {
    workOrderState.reviewNotes[id] = order.review_note || "";
  }
}

async function refreshBusinessState({ includeAnalytics = false } = {}) {
  await Promise.allSettled([
    loadPersistentWorkOrders(),
    loadRoleDashboards(),
    loadDecisionState(),
    refreshOperationReport(),
    includeAnalytics ? loadAnalytics() : Promise.resolve()
  ]);
}

function selectAnomalyForDispatch(item) {
  const equipmentId = item?.equipment_id;
  if (!equipmentId) {
    return;
  }
  const match = analytics.globalAnomalies.find((row) => row.equipment_id === equipmentId);
  if (match) {
    orderDraft.buildingId = match.building_id || "";
    orderDraft.floorLabel = "";
    orderDraft.anomalyKey = anomalyKey(match);
    if (item.recommended_worker_id) {
      orderDraft.assigneeId = item.recommended_worker_id;
    }
  } else {
    loadCounterfactualForEquipment(equipmentId);
  }
}

async function generateWorkOrder() {
  const anomaly = selectedOrderAnomaly.value;
  if (!anomaly) {
    return;
  }
  const assignee = selectedAssignee.value;
  if (!assignee) {
    errors.orders = "请先选择一名工人，再生成工单。";
    return;
  }

  const workOrderId = `WO-MANUAL-${Date.now()}`;
  const order = {
    work_order_id: workOrderId,
    source_record_id: anomaly.record_id,
    priority: inferOrderPriority(anomaly),
    status: "assigned",
    building_id: anomaly.building_id,
    building_name: anomaly.building_name,
    floor_label: anomaly.floor_label,
    zone_name: anomaly.zone_name,
    equipment_id: anomaly.equipment_id,
    equipment_type: anomaly.equipment_type,
    timestamp: anomaly.timestamp,
    anomaly_reason: anomaly.anomaly_reason,
    possible_cause: "由异常明细人工确认后生成工单，需现场复核设备运行状态。",
    recommended_action: inferRecommendedAction(anomaly),
    owner_role: assignee.display_name || inferOwnerRole(anomaly),
    assignee_id: assignee.user_id,
    assignee_name: assignee.display_name,
    created_by: currentUser.value?.user_id || "admin",
    before_kwh: Number(anomaly.electricity_kwh) || null,
    before_cop: Number(anomaly.average_cop) || null,
    severity: anomaly.severity,
    risk_score: anomaly.risk_score,
    triggered_rule_count: anomaly.triggered_rule_count,
    wasted_kwh: anomaly.wasted_kwh,
    wasted_cost_yuan: anomaly.wasted_cost_yuan,
    carbon_kg: anomaly.carbon_kg,
    estimated_saving_yuan: anomaly.estimated_saving_yuan,
    sla_hours: anomaly.sla_hours,
    business_impact_summary: anomaly.business_impact_summary,
    verification_method: anomaly.verification_method,
    verification_status: "未验证"
  };

  loading.orders = true;
  errors.orders = "";
  try {
    const saved = await createPersistentWorkOrder({
      ...order,
      note: `管理员已派单给${order.assignee_name}，等待接单。SLA ${order.sla_hours || 24} 小时。`
    });
    upsertWorkOrder(saved);
    orderDraft.anomalyKey = "";
    await refreshBusinessState({ includeAnalytics: true });
  } catch (error) {
    errors.orders = "生成工单失败，请确认后端工单接口可用。";
  } finally {
    loading.orders = false;
  }
}

async function completeWorkOrder(workOrderId) {
  await updateWorkOrderStatus(workOrderId, "closed");
  await refreshOperationReport();
}

async function saveWorkOrderNote(order) {
  const note = workOrderState.notesById[order.work_order_id] || "";
  try {
    const updated = await updatePersistentWorkOrder(order.work_order_id, {
      status: order.status,
      note
    });
    upsertWorkOrder(updated);
  } catch (error) {
    errors.orders = "备注保存失败，请稍后重试。";
  }
}

async function handleAssignWorkOrder(order) {
  const assigneeId = workOrderState.assignmentById[order.work_order_id] || order.assignee_id || orderDraft.assigneeId;
  if (!assigneeId) {
    errors.orders = "请选择工人后再派单。";
    return;
  }
  loading.orders = true;
  errors.orders = "";
  try {
    const updated = await assignPersistentWorkOrder(order.work_order_id, {
      assignee_id: assigneeId,
      operator_id: currentUser.value?.user_id || "admin",
      note: workOrderState.notesById[order.work_order_id] || "管理员重新派单。"
    });
    upsertWorkOrder(updated);
    await refreshBusinessState();
  } catch (error) {
    errors.orders = "派单失败，请检查后端工单状态。";
  } finally {
    loading.orders = false;
  }
}

async function handleAcceptWorkOrder(order) {
  loading.orders = true;
  errors.orders = "";
  try {
    const updated = await acceptPersistentWorkOrder(order.work_order_id, {
      operator_id: currentUser.value?.user_id || "",
      note: "工人已接单，开始现场处理。"
    });
    upsertWorkOrder(updated);
    await refreshBusinessState();
  } catch (error) {
    errors.orders = "接单失败：该工单可能不属于当前工人，或状态不允许接单。";
  } finally {
    loading.orders = false;
  }
}

async function handleSubmitWorkOrder(order) {
  const draft = workOrderState.submitDrafts[order.work_order_id] || {};
  if (!draft.actual_cause?.trim() || !draft.resolution_note?.trim()) {
    errors.orders = "提交复核前需要填写实际原因和处理结果。";
    return;
  }

  loading.orders = true;
  errors.orders = "";
  try {
    const updated = await submitPersistentWorkOrder(order.work_order_id, {
      operator_id: currentUser.value?.user_id || "",
      actual_cause: draft.actual_cause.trim(),
      resolution_note: draft.resolution_note.trim(),
      recovery_confirmed: Boolean(draft.recovery_confirmed),
      parts_used: draft.parts_used || "",
      safety_note: draft.safety_note || "",
      attachment_name: draft.attachment_name || "",
      attachment_note: draft.attachment_note || ""
    });
    upsertWorkOrder(updated);
    await refreshBusinessState();
  } catch (error) {
    errors.orders = "提交复核失败：请确认工单已处于处理中状态。";
  } finally {
    loading.orders = false;
  }
}

async function handleReviewWorkOrder(order, approved) {
  loading.orders = true;
  errors.orders = "";
  try {
    const updated = await reviewPersistentWorkOrder(order.work_order_id, {
      operator_id: currentUser.value?.user_id || "admin",
      approved,
      review_note:
        workOrderState.reviewNotes[order.work_order_id] ||
        (approved ? "现场结果复核通过，工单关闭归档。" : "复核未通过，请补充处理记录后重新提交。")
    });
    upsertWorkOrder(updated);
    await refreshBusinessState();
  } catch (error) {
    errors.orders = "复核失败：只有待复核工单可以执行复核。";
  } finally {
    loading.orders = false;
  }
}

async function handleIgnoreWorkOrder(order) {
  loading.orders = true;
  errors.orders = "";
  try {
    const updated = await ignorePersistentWorkOrder(order.work_order_id, {
      operator_id: currentUser.value?.user_id || "admin",
      note: workOrderState.notesById[order.work_order_id] || "管理员确认无需派工，记录为忽略。"
    });
    upsertWorkOrder(updated);
    await refreshBusinessState();
  } catch (error) {
    errors.orders = "忽略失败：当前状态不允许忽略。";
  } finally {
    loading.orders = false;
  }
}

async function handleAutoConfirmQueue() {
  loading.orders = true;
  errors.orders = "";
  try {
    const result = await createAutoConfirmQueue();
    if (result.created_count > 0) {
      result.created.forEach((order) => upsertWorkOrder(order));
    }
    await refreshBusinessState({ includeAnalytics: true });
    errors.orders = "";
  } catch (error) {
    errors.orders = "自动生成待确认队列失败，请检查后端接口。";
  } finally {
    loading.orders = false;
  }
}

async function handleExport() {
  exportState.loading = true;
  errors.export = "";
  try {
    exportState.lastFile = await downloadCsvExport(buildFilterParams({ includeFloor: true }));
  } catch (error) {
    exportState.lastFile = "";
    errors.export = "导出失败，请确认后端导出接口已经可用。";
  } finally {
    exportState.loading = false;
  }
}

watch(
  () => recordFilters.buildingId,
  () => {
    recordFilters.floorLabel = "";
  }
);

watch(
  () => orderDraft.buildingId,
  () => {
    orderDraft.floorLabel = "";
    orderDraft.anomalyKey = "";
  }
);

watch(
  () => orderDraft.floorLabel,
  () => {
    orderDraft.anomalyKey = "";
  }
);

watch(
  () => selectedOrderAnomaly.value?.equipment_id,
  (equipmentId) => {
    loadCounterfactualForEquipment(equipmentId);
  }
);

watch(
  () => decisionState.workerCapacity,
  () => {
    loadDecisionState();
  }
);

watch(
  workOrderState,
  (value) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(WORK_ORDER_STORAGE_KEY, JSON.stringify(value));
    }
  },
  { deep: true }
);

onMounted(async () => {
  await restoreSession();
});
</script>

<template>
  <main v-if="!isAuthenticated" class="login-shell">
    <section class="login-panel">
      <div class="login-copy">
        <span class="login-eyebrow">Energy Operations</span>
        <h1>建筑能源业务闭环工作台</h1>
        <p>使用管理员或工人账号进入系统，分别演示异常确认、派单、接单、现场处理、复核关闭的完整链路。</p>
        <div class="login-role-grid">
          <button type="button" @click="loginForm.username = 'admin'; loginForm.password = 'admin123'">
            <strong>管理员</strong>
            <span>admin / admin123</span>
          </button>
          <button type="button" @click="loginForm.username = 'worker_ahu'; loginForm.password = 'worker123'">
            <strong>空调巡检员</strong>
            <span>worker_ahu / worker123</span>
          </button>
          <button type="button" @click="loginForm.username = 'worker_chiller'; loginForm.password = 'worker123'">
            <strong>制冷值班员</strong>
            <span>worker_chiller / worker123</span>
          </button>
        </div>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <label class="field-label">
          <span>账号</span>
          <input v-model="loginForm.username" autocomplete="username" />
        </label>
        <label class="field-label">
          <span>密码</span>
          <input v-model="loginForm.password" type="password" autocomplete="current-password" />
        </label>
        <StatusBanner v-if="loginError" :status="loginError" type="warning" />
        <button class="primary-button" type="submit" :disabled="loggingIn">
          {{ loggingIn ? "正在登录..." : "进入系统" }}
        </button>
      </form>
    </section>
  </main>

  <main v-else class="dashboard-shell">
    <AppHeader>
      <template #actions>
        <StatusBanner 
          :status="apiStatus.message" 
          :type="apiStatus.type"
        />
      </template>
    </AppHeader>

    <section class="user-strip">
      <div>
        <span class="role-badge">{{ currentUser.role === "admin" ? "管理员" : "工人" }}</span>
        <strong>{{ currentUser.display_name }}</strong>
        <span>{{ currentUser.specialty }} · {{ currentUser.user_id }}</span>
      </div>
      <button class="secondary-button" type="button" @click="handleLogout">退出登录</button>
    </section>

    <section class="sim-strip" :class="{ 'sim-strip--active': simClock.active }">
      <div class="sim-clock">
        <span class="sim-clock-label">运营沙盘 · 时间机器</span>
        <strong v-if="simClock.active" class="sim-clock-date">{{ simClock.current_date }}</strong>
        <strong v-else class="sim-clock-date sim-clock-date--off">未启动（当前显示全量历史）</strong>
        <span v-if="simClock.active && simClock.data_range?.end" class="sim-clock-range">
          数据边界：{{ (simClock.data_range.start || '').slice(0, 10) }} ~ {{ (simClock.data_range.end || '').slice(0, 10) }}
        </span>
        <span v-if="simClock.active && simClock.interventions?.length" class="sim-clock-fixed">
          已修复设备：{{ simClock.interventions.length }}
        </span>
      </div>
      <div v-if="isAdmin" class="sim-actions">
        <button v-if="!simClock.active" class="primary-button" type="button" :disabled="simLoading" @click="handleStartSimulation">
          启动沙盘（定位到 5 月）
        </button>
        <template v-else>
          <button class="primary-button" type="button" :disabled="simLoading" @click="handleAdvanceDay(1)">
            ▶ 下一天
          </button>
          <button class="secondary-button" type="button" :disabled="simLoading" @click="handleAdvanceDay(7)">
            ⏭ 下一周
          </button>
          <button class="secondary-button" type="button" :disabled="simLoading" @click="handleResetSimulation">
            重置时钟
          </button>
        </template>
        <button class="reset-demo-button" type="button" :disabled="simLoading" @click="handleResetDemo" title="清空工单/预算并重置时间机器，回到演示初始状态">
          ⟲ 重置演示（回到初始）
        </button>
      </div>
      <p class="sim-hint">
        指针之前为已发生历史，之后为"未来"。关闭工单后该设备会在后续日期恢复正常；不处理则异常持续——推进日期即可看到你的决策如何改变系统未来。
      </p>
    </section>

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
      :tabs="visibleTabs"
      v-model:activeTab="activeTab"
    />

    <template v-if="activeTab === 'overview'">
      <section class="kpi-grid">
        <KpiCard title="数据记录" :value="overview.total_records" caption="总记录数量" />
        <KpiCard title="建筑数量" :value="overview.building_count" caption="监测建筑总数" />
        <KpiCard title="平均 COP" :value="overview.average_cop" caption="系统能效比" />
        <KpiCard title="异常记录" :value="overview.abnormal_record_count" caption="异常检测数量" />
      </section>

      <SectionCard
        v-if="isAdmin"
        class="business-command-card"
        eyebrow="Operations"
        title="管理员业务闭环看板"
        description="把异常监测、工单派发、现场处理和复核归档串成一条可演示的运营链路。"
      >
        <div class="business-kpi-grid">
          <div>
            <span>开放工单</span>
            <strong>{{ adminDashboard?.kpis?.open_work_order_count ?? orderStats.assigned + orderStats.in_progress + orderStats.pending_review + orderStats.rejected }}</strong>
          </div>
          <div>
            <span>待复核</span>
            <strong>{{ adminDashboard?.kpis?.pending_review_count ?? pendingReviewOrders.length }}</strong>
          </div>
          <div>
            <span>高优先级未闭环</span>
            <strong>{{ adminDashboard?.kpis?.high_priority_open_count ?? highPriorityOrders.length }}</strong>
          </div>
          <div>
            <span>闭环率</span>
            <strong>{{ adminClosureRate }}</strong>
          </div>
        </div>
        <div class="command-layout">
          <div class="command-list">
            <h3>下一步动作</h3>
            <ul>
              <li v-for="item in adminNextActions" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div class="command-list">
            <h3>待复核工单</h3>
            <ul v-if="(adminDashboard?.pending_review || []).length">
              <li v-for="item in adminDashboard.pending_review" :key="item.work_order_id">
                {{ item.work_order_id }} · {{ item.building_name }} {{ item.floor_label }} · {{ item.assignee_name || item.owner_role }}
              </li>
            </ul>
            <p v-else>暂无待复核工单。</p>
          </div>
        </div>
      </SectionCard>

      <div class="content-grid">
        <SectionCard
          class="overview-scene-card"
          eyebrow="3D Campus"
          title="楼宇风险三维态势"
          description="拖拽旋转查看四栋建筑，红色楼层表示当前识别到异常，绿色楼层表示未发现异常。"
        >
          <BuildingRiskScene
            :buildings="buildings"
            :floor-summary="analytics.globalFloorSummary"
            :loading="loading.analytics"
            @select-floor="handleSceneSelectFloor"
          />
        </SectionCard>

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
            :floor-options="availableFloorOptions"
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
        <SectionCard class="analysis-control-card" eyebrow="Scope" title="选择分析" description="这里是异常分析工作台，可按建筑、楼层和时间范围锁定问题对象。">
          <div class="analysis-filter-panel">
            <label class="field-label">
              <span>建筑筛选</span>
              <select
                v-model="analysisFilters.buildingId"
                :disabled="loading.analytics"
                @change="analysisFilters.floorLabel = ''"
              >
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
              <span>楼层筛选</span>
              <select
                v-model="analysisFilters.floorLabel"
                :disabled="loading.analytics || !availableAnalysisFloorOptions.length"
              >
                <option value="">全部楼层</option>
                <option
                  v-for="floor in availableAnalysisFloorOptions"
                  :key="floor.label"
                  :value="floor.label"
                >
                  {{ floor.label }} · 异常 {{ floor.anomalyCount }} 条
                </option>
              </select>
            </label>

            <label class="field-label">
              <span>开始时间</span>
              <input
                v-model="analysisFilters.startTime"
                type="datetime-local"
                :min="availableTimeRange.start || undefined"
                :max="availableTimeRange.end || undefined"
                :disabled="loading.analytics"
              />
            </label>

            <label class="field-label">
              <span>结束时间</span>
              <input
                v-model="analysisFilters.endTime"
                type="datetime-local"
                :min="availableTimeRange.start || undefined"
                :max="availableTimeRange.end || undefined"
                :disabled="loading.analytics"
              />
            </label>

            <div class="analysis-filter-actions">
              <button class="primary-button" type="button" :disabled="loading.analytics" @click="loadAnalytics">
                {{ loading.analytics ? "分析中..." : "刷新分析" }}
              </button>
              <button class="secondary-button" type="button" :disabled="loading.analytics" @click="handleAnalysisReset">
                重置分析
              </button>
            </div>
          </div>

          <StatusBanner :status="activeAnalysisSummary" type="info" />
          <div v-if="errors.analytics" class="analytics-feedback">
            <EmptyState
              icon="📉"
              title="分析数据暂不可用"
              :description="errors.analytics"
              actionText="重新加载分析"
              @action="loadAnalytics"
            />
          </div>
        </SectionCard>

        <SectionCard
          class="analysis-primary-card"
          eyebrow="Priority"
          :title="`选定范围异常明细（${analytics.anomalies.length} 条）`"
          description="锁定建筑或楼层后，优先完整展示该范围内的异常记录。"
        >
          <div v-if="loading.analytics" class="data-loading">
            <LoadingSpinner text="正在加载异常明细..." />
          </div>
          <DataTable
            v-else
            :columns="anomalyColumns"
            :rows="analytics.anomalies"
            empty-text="当前分析范围暂无异常"
            row-action-label="解释"
            @row-action="loadAnomalyExplanation"
          />
        </SectionCard>

        <SectionCard
          v-if="anomalyExplanation || loading.explanation"
          class="analysis-primary-card anomaly-explain-card"
          eyebrow="Explain"
          title="异常解释面板"
          description="把异常判断拆成触发规则、基线对比、可能原因和处置建议，避免只展示一条静态异常记录。"
        >
          <div v-if="loading.explanation" class="data-loading">
            <LoadingSpinner text="正在生成异常解释..." />
          </div>
          <div v-else-if="anomalyExplanation" class="anomaly-explain-layout">
            <div class="anomaly-conclusion">
              <span class="severity-pill">{{ anomalyExplanation.severity }}风险</span>
              <h3>{{ anomalyExplanation.building_name }} · {{ anomalyExplanation.floor_label }} · {{ anomalyExplanation.equipment_id }}</h3>
              <p>{{ anomalyExplanation.conclusion }}</p>
            </div>
            <div class="explain-metric-grid">
              <div>
                <span>当前电耗</span>
                <strong>{{ anomalyExplanation.metrics.electricity_kwh }} kWh</strong>
              </div>
              <div>
                <span>建筑均值</span>
                <strong>{{ anomalyExplanation.metrics.building_average_kwh }} kWh</strong>
              </div>
              <div>
                <span>动态阈值</span>
                <strong>{{ anomalyExplanation.metrics.dynamic_threshold_kwh }} kWh</strong>
              </div>
              <div>
                <span>平均 COP</span>
                <strong>{{ anomalyExplanation.metrics.average_cop }}</strong>
              </div>
              <div>
                <span>风险分</span>
                <strong>{{ anomalyExplanation.metrics.risk_score }}</strong>
              </div>
              <div>
                <span>估算损失</span>
                <strong>{{ formatNumber(anomalyExplanation.metrics.wasted_cost_yuan) }} 元</strong>
              </div>
              <div>
                <span>预计回收</span>
                <strong>{{ formatNumber(anomalyExplanation.metrics.estimated_saving_yuan) }} 元</strong>
              </div>
              <div>
                <span>碳排影响</span>
                <strong>{{ formatNumber(anomalyExplanation.metrics.carbon_kg) }} kg</strong>
              </div>
            </div>
            <div class="explain-detail-grid">
              <div>
                <h4>触发规则</h4>
                <ul>
                  <li v-for="rule in anomalyExplanation.triggered_rules" :key="rule.name">
                    <strong>{{ rule.name }}</strong>
                    <span>{{ rule.detail }}</span>
                  </li>
                </ul>
              </div>
              <div>
                <h4>处置建议</h4>
                <p><strong>可能原因：</strong>{{ anomalyExplanation.possible_cause }}</p>
                <p><strong>建议动作：</strong>{{ anomalyExplanation.recommended_action }}</p>
                <p v-if="anomalyExplanation.verification_method"><strong>验证口径：</strong>{{ anomalyExplanation.verification_method }}</p>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          v-if="analysisHealthState"
          class="analysis-primary-card analysis-health-card"
          eyebrow="Healthy"
          :title="analysisHealthState.title"
          :description="analysisHealthState.description"
        >
          <div class="health-metric-grid">
            <div v-for="item in analysisHealthState.metrics" :key="item.label" class="health-metric-card">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </SectionCard>

        <template v-if="!analysisHealthState">
        <SectionCard eyebrow="Registry" title="楼层 / 设备台账" description="展示当前分析范围的用途、面积、负责人、设备构成和健康评分。">
          <div v-if="loading.analytics" class="data-loading">
            <LoadingSpinner text="正在加载楼层台账..." />
          </div>
          <div v-else-if="analytics.floorRegistry.length" class="floor-registry-grid">
            <article v-for="item in analytics.floorRegistry" :key="`${item.building_id}-${item.floor_label}`" class="floor-registry-card">
              <div>
                <span class="registry-risk" :class="`registry-risk--${item.risk_level}`">{{ item.risk_level }}</span>
                <h3>{{ item.building_name }} · {{ item.floor_label }}</h3>
                <p>{{ item.usage }} · {{ item.zone_names }}</p>
              </div>
              <div class="registry-meta">
                <span>面积 {{ item.floor_area_m2 }} m²</span>
                <span>负责人 {{ item.owner }}</span>
                <span>设备 {{ item.main_equipment_types }}</span>
                <span>健康分 {{ item.health_score }}</span>
              </div>
              <p class="registry-policy">{{ item.operation_policy }}</p>
            </article>
          </div>
          <EmptyState
            v-else
            icon="🏢"
            title="暂无楼层台账"
            description="当前分析范围没有可展示的楼层台账信息。"
          />
        </SectionCard>

        <SectionCard eyebrow="Trend" title="选定范围能耗趋势" description="只展示当前分析筛选范围内的日度能耗趋势。">
          <TrendChart
            :data="analytics.timeSummary"
            :loading="loading.analytics"
            :error="errors.analytics"
          />
        </SectionCard>

        <SectionCard eyebrow="Floor" title="选定范围楼层与区域" description="如果已锁定单层，这里只保留该层相关的楼层/区域结果。">
          <div v-if="loading.analytics" class="data-loading">
            <LoadingSpinner text="正在加载楼层分析..." />
          </div>
          <DataTable
            v-else
            :columns="floorColumns"
            :rows="analytics.floorSummary"
            empty-text="暂无楼层分析结果"
          />
        </SectionCard>

        <SectionCard eyebrow="Anomaly" title="选定范围异常原因" description="只统计当前建筑或楼层范围内的异常原因分布。">
          <AnomalyReasonChart
            :data="analytics.anomalyReasons"
            :loading="loading.analytics"
            :error="errors.analytics"
          />
        </SectionCard>

        <SectionCard eyebrow="Equipment" title="选定范围设备监测" description="展示当前范围内设备状态、异常数和维护建议。">
          <div v-if="loading.analytics" class="data-loading">
            <LoadingSpinner text="正在加载设备监测..." />
          </div>
          <DataTable
            v-else
            :columns="equipmentColumns"
            :rows="analytics.equipmentSummary"
            empty-text="暂无设备监测结果"
          />
        </SectionCard>

        <SectionCard eyebrow="Optimization" title="选定范围运营优化建议" description="围绕当前建筑或楼层生成节能和运维建议。">
          <div v-if="loading.analytics" class="data-loading">
            <LoadingSpinner text="正在生成优化建议..." />
          </div>
          <DataTable
            v-else
            :columns="recommendationColumns"
            :rows="analytics.recommendations"
            empty-text="暂无优化建议"
          />
        </SectionCard>
        </template>

        <SectionCard class="analysis-divider-card" eyebrow="Global" title="全局基准数据" description="下面这些内容不受局部楼层锁定影响，用来做整体对比和汇报基准。" />

        <SectionCard eyebrow="Comparison" title="全局建筑对比" description="全局建筑电耗和 COP 对比，适合作为稳定基准查看。">
          <BuildingComparisonChart
            :data="analytics.buildingComparison"
            :loading="loading.analytics"
            :error="errors.analytics"
          />
        </SectionCard>

        <SectionCard eyebrow="Ranking" title="全局 COP 排名" description="全局建筑能效比综合排名，便于快速定位能效表现差异。">
          <ul v-if="analytics.copRanking.length && !errors.analytics" class="endpoint-list">
            <li v-for="item in analytics.copRanking" :key="item.building_id">
              {{ item.building_name }} · COP {{ item.average_cop }}
            </li>
          </ul>
          <EmptyState
            v-else
            icon="🧊"
            title="暂无 COP 排名"
            description="当前没有可展示的 COP 结果。"
          />
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'worker'">
      <div class="content-grid content-grid--single">
        <SectionCard eyebrow="My Tasks" title="我的工单工作台" description="工人只看到分配给自己的任务，并按接单、处理、提交复核的顺序推进。">
          <div class="business-kpi-grid">
            <div :class="{ 'kpi--highlight': (workerDashboard?.kpis?.assigned_count || orderStats.assigned) > 0 }">
              <span>待接单 <b v-if="(workerDashboard?.kpis?.assigned_count || orderStats.assigned) > 0" class="badge-dot">{{ workerDashboard?.kpis?.assigned_count || orderStats.assigned }}</b></span>
              <strong>{{ workerDashboard?.kpis?.assigned_count || orderStats.assigned }}</strong>
            </div>
            <div>
              <span>处理中</span>
              <strong>{{ workerDashboard?.kpis?.in_progress_count || orderStats.in_progress }}</strong>
            </div>
            <div>
              <span>待复核</span>
              <strong>{{ workerDashboard?.kpis?.pending_review_count || orderStats.pending_review }}</strong>
            </div>
            <div>
              <span>已关闭</span>
              <strong>{{ workerDashboard?.kpis?.closed_count || orderStats.closed }}</strong>
            </div>
          </div>

          <div class="worker-next-actions">
            <span v-for="item in workerDashboard?.next_actions || []" :key="item">{{ item }}</span>
          </div>

          <div v-if="workerDashboard?.standard_work_guidance" class="worker-support-grid">
            <div class="worker-support-card">
              <h3>{{ workerDashboard.standard_work_guidance.title }}</h3>
              <p>{{ workerDashboard.standard_work_guidance.equipment_type }} · {{ workerDashboard.standard_work_guidance.anomaly_reason }}</p>
              <ol>
                <li v-for="step in workerDashboard.standard_work_guidance.steps" :key="step">{{ step }}</li>
              </ol>
              <div class="support-evidence">
                <span v-for="item in workerDashboard.standard_work_guidance.required_evidence" :key="item">{{ item }}</span>
              </div>
            </div>
            <div class="worker-support-card">
              <h3>历史相似案例</h3>
              <ul v-if="workerDashboard.similar_cases?.length" class="similar-case-list">
                <li v-for="item in workerDashboard.similar_cases" :key="item.work_order_id">
                  <strong>{{ item.work_order_id }} · {{ item.equipment_id }}</strong>
                  <span>{{ item.actual_cause }} / {{ item.resolution_note }}</span>
                  <em>预计回收 {{ formatNumber(item.estimated_saving_yuan) }} 元</em>
                </li>
              </ul>
              <p v-else>暂无相似已关闭案例，按标准作业建议补充现场证据。</p>
            </div>
          </div>

          <div v-if="loading.orders" class="data-loading">
            <LoadingSpinner text="正在加载我的工单..." />
          </div>
          <div v-else-if="!sortedWorkOrders.length" class="data-empty">
            <EmptyState icon="🧾" title="暂无分配给你的工单" description="请让管理员从工单中心选择异常并派单给当前工人。" />
          </div>
          <div v-else class="work-order-board work-order-board--single">
            <article
              v-for="order in sortedWorkOrders"
              :key="order.work_order_id"
              class="work-order-card"
              :class="[
                `work-order-card--${order.priority}`,
                `work-order-card--${order.status}`
              ]"
            >
              <div class="work-order-card__head">
                <div>
                  <span class="work-order-id">{{ order.work_order_id }}</span>
                  <h3>{{ order.building_name }} · {{ order.floor_label }} · {{ order.equipment_id }}</h3>
                </div>
                <div class="order-badges">
                  <span class="priority-pill">{{ order.priority }}优先级</span>
                  <span class="status-chip">{{ getOrderStatusLabel(order) }}</span>
                </div>
              </div>
              <div class="work-order-meta">
                <span>区域：{{ order.zone_name }}</span>
                <span>设备：{{ order.equipment_type }}</span>
                <span>派单人：{{ order.created_by || "admin" }}</span>
                <span>时间：{{ order.timestamp }}</span>
              </div>
              <p><strong>异常原因：</strong>{{ order.anomaly_reason }}</p>
              <p><strong>处置建议：</strong>{{ order.recommended_action }}</p>

              <div class="work-order-actions">
                <button
                  v-if="['assigned', 'rejected'].includes(order.status)"
                  class="primary-button"
                  type="button"
                  :disabled="loading.orders"
                  @click="handleAcceptWorkOrder(order)"
                >
                  接单并开始处理
                </button>

                <div v-if="order.status === 'in_progress'" class="worker-submit-grid">
                  <label>
                    <span>现场实际原因</span>
                    <textarea v-model="workOrderState.submitDrafts[order.work_order_id].actual_cause" rows="2" placeholder="例如：AHU 过滤网堵塞导致风量不足。" />
                  </label>
                  <label>
                    <span>处理结果</span>
                    <textarea v-model="workOrderState.submitDrafts[order.work_order_id].resolution_note" rows="2" placeholder="例如：已清洗过滤网并恢复自动控制。" />
                  </label>
                  <label>
                    <span>更换部件</span>
                    <input v-model="workOrderState.submitDrafts[order.work_order_id].parts_used" placeholder="无或填写部件名称" />
                  </label>
                  <label>
                    <span>安全备注</span>
                    <input v-model="workOrderState.submitDrafts[order.work_order_id].safety_note" placeholder="例如：已挂牌确认，无安全隐患" />
                  </label>
                  <label class="checkbox-field">
                    <input v-model="workOrderState.submitDrafts[order.work_order_id].recovery_confirmed" type="checkbox" />
                    <span>现场已恢复正常</span>
                  </label>
                  <label>
                    <span>现场附件（文件名）</span>
                    <input v-model="workOrderState.submitDrafts[order.work_order_id].attachment_name" placeholder="例如：现场照片-20260610.jpg" />
                  </label>
                  <label>
                    <span>附件备注</span>
                    <input v-model="workOrderState.submitDrafts[order.work_order_id].attachment_note" placeholder="例如：过滤网清洗前后对比照片" />
                  </label>
                  <button class="primary-button" type="button" :disabled="loading.orders" @click="handleSubmitWorkOrder(order)">
                    提交管理员复核
                  </button>
                </div>

                <StatusBanner
                  v-if="order.status === 'pending_review'"
                  status="已提交管理员复核，请等待关闭或驳回。"
                  type="success"
                />
                <StatusBanner
                  v-if="order.status === 'closed'"
                  status="该工单已复核关闭，处理结果已归档。"
                  type="success"
                />
              </div>

              <!-- Before/After Comparison -->
              <div v-if="order.status === 'closed' && (order.before_kwh || order.after_kwh)" class="before-after-compare">
                <h4>处理前后能耗对比<span v-if="order.after_is_estimated" class="estimate-tag">处理后为估算值</span></h4>
                <div class="before-after-grid">
                  <div>
                    <span>处理前电耗</span>
                    <strong>{{ order.before_kwh || '-' }} kWh</strong>
                  </div>
                  <div>
                    <span>处理后电耗</span>
                    <strong>{{ order.after_kwh || '-' }} kWh</strong>
                  </div>
                  <div>
                    <span>处理前 COP</span>
                    <strong>{{ order.before_cop || '-' }}</strong>
                  </div>
                  <div>
                    <span>处理后 COP</span>
                    <strong>{{ order.after_cop || '-' }}</strong>
                  </div>
                </div>
              </div>
              <!-- Attachment Info -->
              <div v-if="order.attachment_name" class="attachment-info">
                <span>📎 现场附件：</span>
                <strong>{{ order.attachment_name }}</strong>
                <span v-if="order.attachment_note"> · {{ order.attachment_note }}</span>
              </div>

              <ol v-if="order.timeline.length" class="timeline-list">
                <li v-for="event in order.timeline.slice(-4)" :key="event.event_id">
                  <strong>{{ event.action }}</strong>
                  <span>{{ event.operator_name || event.operator }} · {{ event.created_at || event.timestamp }}</span>
                  <p>{{ event.note }}</p>
                </li>
              </ol>
            </article>
          </div>
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'orders'">
      <div class="content-grid content-grid--single">
        <SectionCard eyebrow="Work Orders" title="异常工单处理中心" description="把异常记录转成可分派、可处置、可复核归档的运维任务，支持管理员派单、工人接单处置、复核关闭的完整流程。">
          <div v-if="errors.orders" class="inline-banner-list">
            <StatusBanner :status="errors.orders" type="warning" />
          </div>
          <div class="order-create-panel">
            <div class="order-create-grid">
              <label class="field-label">
                <span>选择建筑</span>
                <select v-model="orderDraft.buildingId">
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
                <span>选择楼层</span>
                <select v-model="orderDraft.floorLabel" :disabled="!availableOrderFloorOptions.length">
                  <option value="">全部楼层</option>
                  <option
                    v-for="floor in availableOrderFloorOptions"
                    :key="floor.label"
                    :value="floor.label"
                  >
                    {{ floor.label }} · {{ floor.count }} 条异常
                  </option>
                </select>
              </label>

              <label class="field-label order-create-grid__wide">
                <span>选择异常</span>
                <select v-model="orderDraft.anomalyKey" :disabled="!availableOrderAnomalies.length">
                  <option value="">请选择一条异常记录</option>
                  <option
                    v-for="anomaly in availableOrderAnomalies"
                    :key="anomalyKey(anomaly)"
                    :value="anomalyKey(anomaly)"
                  >
                    {{ anomaly.building_name }} · {{ anomaly.floor_label }} · {{ anomaly.equipment_id }} · {{ anomaly.anomaly_reason }} · {{ anomaly.timestamp }}
                  </option>
                </select>
              </label>

              <label class="field-label">
                <span>分配工人</span>
                <select v-model="orderDraft.assigneeId">
                  <option v-for="worker in workerUsers" :key="worker.user_id" :value="worker.user_id">
                    {{ worker.display_name }} · {{ worker.specialty }}
                  </option>
                </select>
              </label>

              <button class="primary-button" type="button" :disabled="!selectedOrderAnomaly || loading.orders" @click="generateWorkOrder">
                生成并派单
              </button>
              <button class="secondary-button" type="button" :disabled="loading.orders" @click="handleAutoConfirmQueue" style="grid-column: 1 / -1; border-color: var(--accent-deep); color: var(--accent-deep);">
                🔄 一键生成待确认工单队列（从所有异常自动创建待确认工单）
              </button>
            </div>
            <p class="order-create-hint">
              先从异常记录中选择一个问题并分配工人，系统会携带风险分、估算损失、SLA 和验证方法生成工单，工人登录后即可接单处理。
            </p>
            <div v-if="selectedOrderAnomaly" class="order-preview-strip">
              <div>
                <span>风险分</span>
                <strong>{{ selectedOrderAnomaly.risk_score || "-" }}</strong>
              </div>
              <div>
                <span>估算浪费</span>
                <strong>{{ formatNumber(selectedOrderAnomaly.wasted_cost_yuan) }} 元</strong>
              </div>
              <div>
                <span>可回收</span>
                <strong>{{ formatNumber(selectedOrderAnomaly.estimated_saving_yuan) }} 元</strong>
              </div>
              <div>
                <span>SLA</span>
                <strong>{{ selectedOrderAnomaly.sla_hours || 24 }} 小时</strong>
              </div>
            </div>
            <p v-if="selectedOrderDecision" class="order-create-hint">
              已有同设备未闭环工单的经济决策分为 {{ selectedOrderDecision.decision_score }}：
              {{ selectedOrderDecision.reason }}
            </p>
          </div>

          <div class="order-impact-grid">
            <div>
              <span>未闭环工单</span>
              <strong>{{ orderBusinessStats.openCount }}</strong>
            </div>
            <div>
              <span>高风险任务</span>
              <strong>{{ orderBusinessStats.highRiskCount }}</strong>
            </div>
            <div>
              <span>估算损失</span>
              <strong>{{ formatNumber(orderBusinessStats.totalWastedCost) }} 元</strong>
            </div>
            <div>
              <span>预计可回收</span>
              <strong>{{ formatNumber(orderBusinessStats.totalSaving) }} 元</strong>
            </div>
          </div>

          <div v-if="errors.decision" class="inline-banner-list">
            <StatusBanner :status="errors.decision" type="warning" />
          </div>

          <div class="dispatch-decision-panel">
            <div class="dispatch-header">
              <div>
                <span>Economic Dispatch</span>
                <h3>今日资源约束派单建议</h3>
                <p>{{ decisionState.dispatchPlan?.summary || "等待经济决策接口返回派单建议。" }}</p>
              </div>
              <label>
                <span>今日可派工人</span>
                <input v-model.number="decisionState.workerCapacity" type="number" min="1" max="8" />
              </label>
            </div>
            <div v-if="loading.decision" class="data-loading data-loading--compact">
              <LoadingSpinner text="正在计算优先级..." />
            </div>
            <div v-else-if="decisionState.dispatchPlan?.selected?.length" class="dispatch-grid">
              <article
                v-for="item in decisionState.dispatchPlan.selected"
                :key="item.work_order_id"
                class="dispatch-card dispatch-card--clickable"
                :class="{ 'dispatch-card--active': selectedOrderAnomaly && selectedOrderAnomaly.equipment_id === item.equipment_id }"
                role="button"
                tabindex="0"
                title="点击在上方自动选中这条异常"
                @click="selectAnomalyForDispatch(item)"
                @keyup.enter="selectAnomalyForDispatch(item)"
              >
                <div>
                  <strong>#{{ item.decision_score }} · {{ item.work_order_id }}</strong>
                  <span>{{ item.building_name }} {{ item.floor_label }} · {{ item.equipment_id }}</span>
                </div>
                <p>{{ item.reason }}</p>
                <div class="dispatch-breakdown">
                  <span>风险 {{ item.score_breakdown.risk }}</span>
                  <span>损失 {{ item.score_breakdown.estimated_loss }}</span>
                  <span>SLA {{ item.score_breakdown.sla }}</span>
                  <span>碳排 {{ item.score_breakdown.carbon }}</span>
                </div>
              </article>
            </div>
            <EmptyState
              v-else
              icon="🧭"
              title="暂无待排序工单"
              description="生成或推进工单后，系统会按风险、损失、SLA 和碳排自动排序。"
            />
          </div>

          <div v-if="selectedOrderAnomaly || decisionState.counterfactual" class="counterfactual-panel">
            <div class="counterfactual-head">
              <div>
                <span>Time Machine Experiment</span>
                <h3>异常处置三情景对照</h3>
                <p>{{ decisionState.counterfactual?.decision_sentence || "选择一条异常后，系统会比较不处理、立即处理、延迟 3 天处理的未来 7 天影响。" }}</p>
              </div>
              <strong v-if="selectedOrderAnomaly">{{ selectedOrderAnomaly.equipment_id }}</strong>
            </div>
            <div v-if="decisionState.counterfactualLoading" class="data-loading data-loading--compact">
              <LoadingSpinner text="正在生成对照实验..." />
            </div>
            <StatusBanner v-else-if="decisionState.counterfactualError" :status="decisionState.counterfactualError" type="warning" />
            <div v-else-if="decisionState.counterfactual?.scenarios?.length" class="scenario-curve-grid">
              <article v-for="scenario in decisionState.counterfactual.scenarios" :key="scenario.key" class="scenario-curve-card">
                <strong>{{ scenario.label }}</strong>
                <div class="scenario-bars">
                  <span
                    v-for="point in scenario.daily"
                    :key="point.date"
                    :style="{ height: `${Math.max(8, Math.min(100, point.loss_yuan / Math.max(1, scenario.total_loss_yuan) * 100))}%` }"
                    :title="`${point.date} · ${point.loss_yuan} 元 · ${point.anomaly_count} 次异常`"
                  ></span>
                </div>
                <div class="scenario-metrics">
                  <span>{{ formatNumber(scenario.total_energy_kwh) }} kWh</span>
                  <span>{{ formatNumber(scenario.total_loss_yuan) }} 元</span>
                  <span>{{ formatNumber(scenario.total_carbon_kg) }} kg CO₂</span>
                  <span>{{ scenario.total_anomaly_count }} 次异常</span>
                </div>
              </article>
            </div>
          </div>

          <div class="order-summary-grid order-summary-grid--wide">
            <div v-for="status in orderStatusOptions" :key="status.key" class="order-summary-card">
              <span>{{ status.label }}</span>
              <strong>{{ orderStats[status.key] || 0 }}</strong>
            </div>
          </div>

          <div v-if="loading.analytics || loading.orders" class="data-loading">
            <LoadingSpinner text="正在加载异常工单..." />
          </div>
          <div v-else-if="!sortedWorkOrders.length" class="data-empty">
            <EmptyState icon="🧾" title="还没有生成工单" description="请先在上方选择异常记录并分配工人，然后生成派单工单。" />
          </div>
          <div v-else class="work-order-board">
            <article
              v-for="order in sortedWorkOrders"
              :key="order.work_order_id"
              class="work-order-card"
              :class="[
                `work-order-card--${order.priority}`,
                `work-order-card--${order.status}`
              ]"
            >
              <div class="work-order-card__head">
                <div>
                  <span class="work-order-id">{{ order.work_order_id }}</span>
                  <h3>{{ order.building_name }} · {{ order.floor_label }} · {{ order.equipment_id }}</h3>
                </div>
                <div class="work-order-pills">
                  <span class="priority-pill">{{ order.priority }}优先级</span>
                  <span class="status-pill">{{ getOrderStatusLabel(order) }}</span>
                </div>
              </div>
              <div class="work-order-meta">
                <span>区域：{{ order.zone_name }}</span>
                <span>设备：{{ order.equipment_type }}</span>
                <span>工人：{{ order.assignee_name || order.owner_role || "未分配" }}</span>
                <span>时间：{{ order.timestamp }}</span>
              </div>
              <div class="work-order-impact">
                <div>
                  <span>风险分</span>
                  <strong>{{ order.risk_score || "-" }}</strong>
                </div>
                <div>
                  <span>估算损失</span>
                  <strong>{{ formatNumber(order.wasted_cost_yuan) }} 元</strong>
                </div>
                <div>
                  <span>可回收</span>
                  <strong>{{ formatNumber(order.estimated_saving_yuan) }} 元</strong>
                </div>
                <div>
                  <span>SLA</span>
                  <strong>{{ order.sla_hours || 24 }}h</strong>
                </div>
              </div>
              <div v-if="decisionByWorkOrderId.get(order.work_order_id)" class="decision-score-box">
                <div>
                  <span>经济优先级分</span>
                  <strong>{{ decisionByWorkOrderId.get(order.work_order_id).decision_score }}</strong>
                </div>
                <p>{{ decisionByWorkOrderId.get(order.work_order_id).reason }}</p>
                <span>推荐工人：{{ decisionByWorkOrderId.get(order.work_order_id).recommended_worker_name }}</span>
              </div>
              <ol v-if="order.status !== 'ignored'" class="order-flow">
                <li
                  v-for="status in orderStatusOptions.filter((item) => item.key !== 'ignored')"
                  :key="status.key"
                  :class="{
                    'is-active': orderStatusRank(status.key) <= orderStatusRank(order.status),
                    'is-current': status.key === order.status
                  }"
                >
                  {{ status.label }}
                </li>
              </ol>
              <p><strong>异常原因：</strong>{{ order.anomaly_reason }}</p>
              <p><strong>可能原因：</strong>{{ order.possible_cause }}</p>
              <p><strong>处置建议：</strong>{{ order.recommended_action }}</p>
              <p v-if="order.business_impact_summary" class="work-order-business">{{ order.business_impact_summary }}</p>
              <p v-if="order.verification_method" class="work-order-business"><strong>验证口径：</strong>{{ order.verification_method }}</p>
              <p v-if="order.verification_result" class="work-order-business"><strong>复测结果：</strong>{{ order.verification_result }}</p>
              <p v-if="order.actual_cause"><strong>现场原因：</strong>{{ order.actual_cause }}</p>
              <p v-if="order.resolution_note"><strong>处理结果：</strong>{{ order.resolution_note }}</p>

              <div class="work-order-actions">
                <label>
                  <span>工单备注</span>
                  <textarea
                    v-model="workOrderState.notesById[order.work_order_id]"
                    rows="2"
                    placeholder="例如：要求优先检查制冷机组供回水温差。"
                    @blur="saveWorkOrderNote(order)"
                  />
                </label>

                <div v-if="order.status === 'pending_confirm'" class="admin-action-grid">
                  <label>
                    <span>调整分配工人</span>
                    <select v-model="workOrderState.assignmentById[order.work_order_id]">
                      <option v-for="worker in workerUsers" :key="worker.user_id" :value="worker.user_id">
                        {{ worker.display_name }} · {{ worker.specialty }}
                      </option>
                    </select>
                  </label>
                  <button class="primary-button" type="button" :disabled="loading.orders" @click="handleAssignWorkOrder(order)">
                    确认派单
                  </button>
                  <button class="secondary-button" type="button" :disabled="loading.orders" @click="handleIgnoreWorkOrder(order)">
                    忽略告警
                  </button>
                </div>

                <StatusBanner
                  v-if="order.status === 'assigned'"
                  :status="`已派单给 ${order.assignee_name || '工人'}，等待其接单处理。`"
                  type="info"
                />

                <div v-if="order.status === 'pending_review'" class="review-panel">
                  <label>
                    <span>复核意见</span>
                    <textarea v-model="workOrderState.reviewNotes[order.work_order_id]" rows="2" placeholder="例如：能耗曲线恢复正常，现场处理记录完整。" />
                  </label>
                  <div class="review-actions">
                    <button class="complete-button" type="button" :disabled="loading.orders" @click="handleReviewWorkOrder(order, true)">
                      复核通过并关闭
                    </button>
                    <button class="secondary-button" type="button" :disabled="loading.orders" @click="handleReviewWorkOrder(order, false)">
                      驳回重办
                    </button>
                  </div>
                </div>

                <StatusBanner
                  v-if="order.status === 'closed'"
                  status="该工单已关闭，处理过程已进入归档链路。"
                  type="success"
                />
                <StatusBanner
                  v-if="order.status === 'ignored'"
                  status="该告警已被管理员忽略，不再进入现场处理。"
                  type="info"
                />
              </div>

              <!-- Before/After Comparison -->
              <div v-if="order.status === 'closed' && (order.before_kwh || order.after_kwh)" class="before-after-compare">
                <h4>处理前后能耗对比<span v-if="order.after_is_estimated" class="estimate-tag">处理后为估算值</span></h4>
                <div class="before-after-grid">
                  <div>
                    <span>处理前电耗</span>
                    <strong>{{ order.before_kwh || '-' }} kWh</strong>
                  </div>
                  <div>
                    <span>处理后电耗</span>
                    <strong>{{ order.after_kwh || '-' }} kWh</strong>
                  </div>
                  <div>
                    <span>处理前 COP</span>
                    <strong>{{ order.before_cop || '-' }}</strong>
                  </div>
                  <div>
                    <span>处理后 COP</span>
                    <strong>{{ order.after_cop || '-' }}</strong>
                  </div>
                </div>
              </div>
              <!-- Attachment Info -->
              <div v-if="order.attachment_name" class="attachment-info">
                <span>📎 现场附件：</span>
                <strong>{{ order.attachment_name }}</strong>
                <span v-if="order.attachment_note"> · {{ order.attachment_note }}</span>
              </div>

              <ol v-if="order.timeline.length" class="timeline-list">
                <li v-for="event in order.timeline.slice(-4)" :key="event.event_id">
                  <strong>{{ event.action }}</strong>
                  <span>{{ event.operator_name || event.operator }} · {{ event.created_at || event.timestamp }}</span>
                  <p>{{ event.note }}</p>
                </li>
              </ol>
            </article>
          </div>
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'report'">
      <div class="content-grid">
        <SectionCard eyebrow="Forecast" title="未来 7 天能耗预测" description="基于最近趋势做轻量预测，用于课堂演示能源管理的前瞻判断。">
          <div v-if="forecastSeries.length" class="forecast-chart">
            <div
              v-for="item in forecastSeries"
              :key="item.day"
              class="forecast-bar-wrap"
            >
              <div
                class="forecast-bar"
                :style="{ height: `${Math.max(18, (item.electricity_kwh / forecastMax) * 160)}px` }"
              ></div>
              <strong>{{ item.day }}</strong>
              <span>{{ formatNumber(item.electricity_kwh) }} kWh</span>
            </div>
          </div>
          <EmptyState
            v-else
            icon="📈"
            title="暂无预测数据"
            description="全局时间序列暂未加载成功，请刷新页面或检查后端统计接口。"
          />
        </SectionCard>

        <SectionCard eyebrow="Simulation" title="节能策略模拟器" description="调整策略参数，快速估算节电量和经济收益。">
          <div class="simulation-form">
            <label>
              <span>空调设定温度上调</span>
              <input v-model.number="simulation.temperatureDelta" type="range" min="0" max="3" step="0.5" />
              <strong>{{ simulation.temperatureDelta }} ℃</strong>
            </label>
            <label>
              <span>夜间关闭非必要设备</span>
              <input v-model.number="simulation.nightShutdownHours" type="range" min="0" max="4" step="0.5" />
              <strong>{{ simulation.nightShutdownHours }} 小时/天</strong>
            </label>
            <label>
              <span>电价</span>
              <input v-model.number="simulation.electricityPrice" type="number" min="0" step="0.01" />
              <strong>{{ simulation.electricityPrice }} 元/kWh</strong>
            </label>
          </div>
          <div class="simulation-result">
            <div>
              <span>预计节电</span>
              <strong>{{ formatNumber(simulationResult.savingKwh) }} kWh</strong>
            </div>
            <div>
              <span>预计节约</span>
              <strong>{{ formatNumber(simulationResult.savingCost) }} 元</strong>
            </div>
            <div>
              <span>总电耗降幅</span>
              <strong>{{ simulationResult.savingRate }}%</strong>
            </div>
          </div>
        </SectionCard>

        <SectionCard class="report-card" eyebrow="Report" title="自动运营报告" description="自动汇总总览、风险、预测、节能收益和优化建议，适合录视频时直接展示。">
          <div class="report-toolbar">
            <button class="primary-button" type="button" :disabled="loading.report" @click="refreshOperationReport">
              {{ loading.report ? "生成中..." : "一键生成今日运营日报" }}
            </button>
            <span v-if="operationReport.generatedAt">生成时间：{{ operationReport.generatedAt }}</span>
          </div>
          <StatusBanner v-if="errors.report" :status="errors.report" type="warning" />
          <div class="operation-report">
            <h3>{{ operationReport.title }}</h3>
            <div class="report-metric-grid">
              <div>
                <span>异常浪费</span>
                <strong>{{ formatNumber(operationReport.businessImpact?.total_wasted_kwh) }} kWh</strong>
              </div>
              <div>
                <span>经济损失</span>
                <strong>{{ formatNumber(operationReport.businessImpact?.total_wasted_cost_yuan) }} 元</strong>
              </div>
              <div>
                <span>预计回收</span>
                <strong>{{ formatNumber(operationReport.businessImpact?.total_estimated_saving_yuan) }} 元</strong>
              </div>
              <div>
                <span>碳排影响</span>
                <strong>{{ formatNumber(operationReport.businessImpact?.total_carbon_kg) }} kg</strong>
              </div>
            </div>
            <p>{{ operationReport.overview }}</p>
            <p>{{ operationReport.risk }}</p>
            <p>{{ operationReport.latestAnomaly }}</p>
            <p>{{ operationReport.workOrder }}</p>
            <p>{{ operationReport.workOrderClosure }}</p>
            <p v-if="operationReport.businessSummary">{{ operationReport.businessSummary }}</p>
            <p v-if="operationReport.verificationSummary">{{ operationReport.verificationSummary }}</p>
            <p>{{ operationReport.forecast }}</p>
            <p>{{ operationReport.saving }}</p>
            <p>{{ operationReport.recommendation }}</p>
            <ul v-if="operationReport.actionItems?.length" class="report-action-list">
              <li v-for="item in operationReport.actionItems" :key="item">{{ item }}</li>
            </ul>
            <!-- Closed Case Cards -->
            <div v-if="operationReport.closedCases?.length" class="closed-cases-section">
              <h4>已关闭工单案例</h4>
              <div class="closed-case-grid">
                <article v-for="item in operationReport.closedCases.slice(0, 4)" :key="item.work_order_id" class="closed-case-card">
                  <h5>{{ item.building_name }} · {{ item.floor_label }} · {{ item.equipment_id }}</h5>
                  <p><strong>现场原因：</strong>{{ item.actual_cause || '-' }}</p>
                  <p><strong>处理结果：</strong>{{ item.resolution_note || '-' }}</p>
                  <p v-if="item.saving_summary || item.cop_summary" class="closed-case-effect">
                    {{ item.saving_summary }}{{ item.saving_summary && item.cop_summary ? ' · ' : '' }}{{ item.cop_summary }}
                  </p>
                  <span class="closed-case-time">{{ item.closed_at }}</span>
                </article>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Recommendations" title="重点优化清单" description="从分析结果中提取当前最值得讲的优化动作。">
          <ul v-if="analytics.recommendations.length" class="decision-list">
            <li v-for="item in analytics.recommendations.slice(0, 6)" :key="item.recommendation_id">
              <strong>{{ item.building_name }} · {{ item.category }} · {{ item.priority }}优先级</strong>
              <span>{{ item.finding }}</span>
              <em>{{ item.action }}</em>
            </li>
          </ul>
          <EmptyState
            v-else
            icon="💡"
            title="暂无优化建议"
            description="当前筛选范围没有触发明显节能建议。"
          />
        </SectionCard>
      </div>
    </template>

    <template v-else-if="activeTab === 'budget'">
      <div class="content-grid content-grid--single">
        <BudgetPanel :buildings="buildings" :sim-clock="simClock" />
      </div>
    </template>

    <template v-else-if="activeTab === 'roi'">
      <div class="content-grid content-grid--single">
        <ROIPanel :buildings="buildings" />
      </div>
    </template>

    <template v-else-if="activeTab === 'assistant'">
      <div class="content-grid content-grid--assistant">
        <SectionCard eyebrow="Assistant" title="智能问答工作区" description="">
          <div v-if="errors.assistant" class="inline-banner-list">
            <StatusBanner :status="errors.assistant" type="warning" />
          </div>
          <AssistantPanel
            :loading="loading.assistant"
            :reply="assistantReply"
            :suggestions="defaultQuestions"
            :model-options="assistantProviders.options"
            :llm-enabled="assistantProviders.enabled"
            v-model:selectedModelKey="selectedAssistantModelKey"
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
.login-shell {
  width: min(1120px, calc(100% - 32px));
  min-height: 100vh;
  margin: 0 auto;
  display: grid;
  align-items: center;
  padding: 36px 0;
}

.login-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
  gap: 24px;
  align-items: stretch;
}

.login-copy,
.login-form,
.user-strip,
.business-command-card {
  border: 1px solid rgba(20, 34, 48, 0.1);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 20px 48px rgba(25, 42, 70, 0.1);
  backdrop-filter: blur(18px);
}

.login-copy,
.login-form {
  border-radius: 18px;
  padding: 26px;
}

.login-eyebrow {
  display: inline-flex;
  color: var(--accent-deep);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.login-copy h1 {
  margin: 14px 0 14px;
  max-width: 12ch;
  font-size: clamp(34px, 5vw, 56px);
  line-height: 1.08;
}

.login-copy p {
  max-width: 58ch;
  margin: 0;
  color: var(--ink-soft);
}

.login-role-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 26px;
}

.login-role-grid button {
  border: 1px solid rgba(18, 93, 115, 0.14);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink-strong);
  cursor: pointer;
  display: grid;
  gap: 6px;
  padding: 14px;
  text-align: left;
}

.login-role-grid span {
  color: var(--ink-soft);
  font-size: 12px;
}

.login-form {
  align-content: center;
  display: grid;
  gap: 16px;
}

.user-strip {
  border-radius: 16px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 18px;
  padding: 14px 16px;
}

.user-strip > div {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  color: var(--ink-soft);
}

.user-strip strong {
  color: var(--ink-strong);
}

.role-badge,
.status-chip {
  display: inline-flex;
  border-radius: 999px;
  background: rgba(15, 139, 141, 0.12);
  color: var(--accent-deep);
  font-size: 12px;
  font-weight: 700;
  padding: 5px 10px;
}

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

.overview-scene-card {
  grid-column: 1 / -1;
}

.analysis-control-card,
.analysis-primary-card,
.analysis-divider-card {
  grid-column: 1 / -1;
}

.analysis-filter-panel {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr)) auto;
  gap: 14px;
  align-items: end;
  margin-bottom: 16px;
}

.analysis-filter-actions {
  display: flex;
  gap: 10px;
  align-items: end;
  flex-wrap: wrap;
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

.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.analysis-divider-card {
  background:
    linear-gradient(135deg, rgba(18, 93, 115, 0.12), rgba(255, 159, 28, 0.12)),
    rgba(255, 255, 255, 0.76);
}

.anomaly-explain-layout {
  display: grid;
  gap: 18px;
}

.anomaly-conclusion {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 24px;
  background:
    radial-gradient(circle at 0% 0%, rgba(217, 54, 79, 0.14), transparent 34%),
    rgba(255, 255, 255, 0.88);
  padding: 18px;
}

.anomaly-conclusion h3 {
  margin: 8px 0;
  color: var(--accent-deep);
}

.anomaly-conclusion p {
  margin: 0;
  color: #263f49;
}

.severity-pill,
.registry-risk {
  display: inline-flex;
  border-radius: 999px;
  background: rgba(217, 54, 79, 0.12);
  color: #a32035;
  font-size: 12px;
  padding: 5px 10px;
}

.explain-metric-grid,
.floor-registry-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.explain-metric-grid > div,
.floor-registry-card {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  padding: 16px;
}

.explain-metric-grid span,
.registry-meta span {
  display: block;
  color: var(--ink-soft);
  font-size: 13px;
}

.explain-metric-grid strong {
  display: block;
  color: var(--accent-deep);
  font-size: 22px;
  margin-top: 6px;
}

.explain-detail-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.explain-detail-grid > div {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  padding: 16px;
}

.explain-detail-grid h4,
.floor-registry-card h3 {
  margin: 0 0 10px;
  color: var(--accent-deep);
}

.explain-detail-grid ul {
  display: grid;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.explain-detail-grid li {
  display: grid;
  gap: 4px;
  color: #263f49;
}

.floor-registry-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.floor-registry-card {
  display: grid;
  gap: 12px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(235, 247, 245, 0.86));
}

.floor-registry-card p {
  margin: 0;
  color: #263f49;
}

.registry-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.registry-risk--健康 {
  background: rgba(34, 160, 107, 0.13);
  color: #15724d;
}

.registry-risk--关注 {
  background: rgba(242, 169, 0, 0.16);
  color: #9a6200;
}

.registry-risk--高风险 {
  background: rgba(217, 54, 79, 0.14);
  color: #a32035;
}

.registry-policy {
  font-weight: 600;
}

.report-card {
  grid-column: 1 / -1;
}

.business-command-card {
  border-radius: 18px;
  margin-bottom: 20px;
}

.business-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.business-kpi-grid > div {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(236, 247, 243, 0.88));
  padding: 14px;
}

.business-kpi-grid span {
  display: block;
  color: var(--ink-soft);
  font-size: 13px;
}

.business-kpi-grid strong {
  display: block;
  color: var(--accent-deep);
  font-size: 26px;
  margin-top: 5px;
}

.command-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.command-list {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  padding: 14px;
}

.command-list h3 {
  margin: 0 0 10px;
  color: var(--accent-deep);
  font-size: 16px;
}

.command-list ul,
.timeline-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.command-list li,
.command-list p {
  margin: 0;
  color: #263f49;
}

.command-list li + li {
  margin-top: 8px;
}

.worker-next-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: -4px 0 18px;
}

.worker-next-actions span {
  border: 1px solid rgba(15, 139, 141, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--accent-deep);
  font-size: 13px;
  padding: 7px 10px;
}

.worker-support-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.worker-support-card {
  border: 1px solid rgba(15, 139, 141, 0.14);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(237, 249, 248, 0.86));
  padding: 16px;
}

.worker-support-card h3 {
  margin: 0 0 6px;
  color: var(--accent-deep);
  font-size: 16px;
}

.worker-support-card p {
  margin: 0 0 10px;
  color: var(--ink-soft);
  font-size: 13px;
}

.worker-support-card ol,
.similar-case-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
  color: #263f49;
  font-size: 13px;
}

.similar-case-list {
  list-style: none;
  padding: 0;
}

.similar-case-list li {
  display: grid;
  gap: 3px;
  border-bottom: 1px solid rgba(20, 34, 48, 0.06);
  padding-bottom: 8px;
}

.similar-case-list strong {
  color: var(--accent-deep);
}

.similar-case-list span,
.similar-case-list em {
  color: var(--ink-soft);
  font-style: normal;
}

.support-evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.support-evidence span {
  border-radius: 999px;
  background: rgba(15, 139, 141, 0.1);
  color: #0f6f71;
  font-size: 12px;
  padding: 5px 9px;
}

.order-summary-grid,
.order-impact-grid,
.simulation-result {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.order-summary-grid--wide {
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.order-create-panel {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 24px;
  background:
    radial-gradient(circle at 12% 0%, rgba(255, 184, 77, 0.15), transparent 30%),
    rgba(255, 255, 255, 0.82);
  padding: 18px;
  margin-bottom: 18px;
}

.order-create-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(240px, 1fr));
  gap: 14px;
  align-items: end;
}

.order-create-grid__wide {
  grid-column: 1 / -1;
}

.order-create-grid > .primary-button {
  justify-self: start;
}

.order-create-hint {
  margin: 12px 0 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.dispatch-decision-panel,
.counterfactual-panel {
  border: 1px solid rgba(15, 139, 141, 0.16);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(237, 249, 248, 0.86));
  padding: 18px;
  margin-bottom: 18px;
}

.dispatch-header,
.counterfactual-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  margin-bottom: 14px;
}

.dispatch-header span,
.counterfactual-head span {
  color: #0f8b8d;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.dispatch-header h3,
.counterfactual-head h3 {
  margin: 3px 0 5px;
  color: var(--accent-deep);
  font-size: 18px;
}

.dispatch-header p,
.counterfactual-head p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.5;
}

.dispatch-header label {
  display: grid;
  gap: 6px;
  color: var(--ink-soft);
  font-size: 12px;
  min-width: 120px;
}

.dispatch-header input {
  width: 100%;
  border: 1px solid rgba(20, 34, 48, 0.12);
  border-radius: 12px;
  font: inherit;
  padding: 9px 10px;
}

.dispatch-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.dispatch-card {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  padding: 14px;
}

.dispatch-card--clickable {
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.dispatch-card--clickable:hover {
  border-color: var(--accent-deep);
  box-shadow: 0 8px 18px rgba(20, 34, 48, 0.12);
  transform: translateY(-1px);
}

.dispatch-card--active {
  border-color: var(--accent-deep);
  box-shadow: 0 0 0 2px rgba(20, 34, 48, 0.18);
}

.dispatch-card strong {
  color: var(--accent-deep);
}

.dispatch-card span,
.dispatch-card p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.45;
}

.dispatch-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dispatch-breakdown span {
  border-radius: 999px;
  background: rgba(15, 139, 141, 0.1);
  color: #0f6f71;
  padding: 4px 8px;
}

.counterfactual-head strong {
  border-radius: 999px;
  background: rgba(15, 139, 141, 0.1);
  color: #0f6f71;
  padding: 7px 11px;
  white-space: nowrap;
}

.scenario-curve-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.scenario-curve-card {
  display: grid;
  gap: 10px;
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  padding: 14px;
}

.scenario-curve-card strong {
  color: var(--accent-deep);
  font-size: 15px;
}

.scenario-bars {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 96px;
  border-bottom: 1px solid rgba(20, 34, 48, 0.1);
}

.scenario-bars span {
  flex: 1;
  min-height: 8px;
  border-radius: 8px 8px 0 0;
  background: linear-gradient(180deg, #f2a900, #d9364f);
}

.scenario-curve-card:nth-child(2) .scenario-bars span {
  background: linear-gradient(180deg, #22a06b, #0f8b8d);
}

.scenario-curve-card:nth-child(3) .scenario-bars span {
  background: linear-gradient(180deg, #7b61ff, #0f8b8d);
}

.scenario-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.scenario-metrics span {
  border-radius: 10px;
  background: rgba(20, 34, 48, 0.04);
  color: var(--ink-soft);
  font-size: 12px;
  padding: 6px 8px;
}

.data-loading--compact {
  padding: 18px;
}

.order-preview-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.order-preview-strip > div,
.order-impact-grid > div,
.work-order-impact > div,
.report-metric-grid > div {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
  padding: 12px;
}

.order-preview-strip span,
.order-impact-grid span,
.work-order-impact span,
.report-metric-grid span {
  display: block;
  color: var(--ink-soft);
  font-size: 12px;
}

.order-preview-strip strong,
.order-impact-grid strong,
.work-order-impact strong,
.report-metric-grid strong {
  display: block;
  color: var(--accent-deep);
  font-size: 18px;
  margin-top: 5px;
}

.order-summary-card,
.simulation-result > div {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(236, 247, 243, 0.88));
  padding: 16px;
}

.order-summary-card span,
.simulation-result span {
  display: block;
  color: var(--ink-soft);
  font-size: 13px;
}

.order-summary-card strong,
.simulation-result strong {
  display: block;
  color: var(--accent-deep);
  font-size: 26px;
  margin-top: 6px;
}

.work-order-board {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.work-order-board--single {
  grid-template-columns: 1fr;
}

.work-order-card {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-left: 6px solid rgba(15, 139, 141, 0.5);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  padding: 18px;
  box-shadow: 0 18px 42px rgba(20, 34, 48, 0.08);
}

.work-order-card--高 {
  border-left-color: #d9364f;
}

.work-order-card--中 {
  border-left-color: #f39c12;
}

.work-order-card--pending_confirm,
.work-order-card--assigned {
  border-left-color: #f2a900;
  background:
    linear-gradient(145deg, rgba(255, 245, 217, 0.96), rgba(255, 255, 255, 0.88));
  box-shadow: 0 22px 52px rgba(242, 169, 0, 0.18);
}

.work-order-card--in_progress,
.work-order-card--处理中 {
  border-left-color: #0f8b8d;
  background:
    linear-gradient(145deg, rgba(224, 246, 245, 0.94), rgba(255, 255, 255, 0.88));
}

.work-order-card--pending_review,
.work-order-card--待验证 {
  border-left-color: #7b61ff;
  background:
    linear-gradient(145deg, rgba(241, 238, 255, 0.95), rgba(255, 255, 255, 0.86));
}

.work-order-card--rejected {
  border-left-color: #d9364f;
  background:
    linear-gradient(145deg, rgba(253, 231, 235, 0.94), rgba(255, 255, 255, 0.88));
}

.work-order-card--closed,
.work-order-card--已关闭,
.work-order-card--已完成 {
  border-left-color: #22a06b;
  background:
    linear-gradient(145deg, rgba(225, 247, 237, 0.96), rgba(255, 255, 255, 0.84));
  opacity: 0.82;
}

.work-order-card--ignored {
  border-left-color: #9aa6ac;
  opacity: 0.78;
}

.work-order-card__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.work-order-id {
  color: var(--ink-soft);
  font-size: 12px;
}

.work-order-card h3 {
  margin: 4px 0 0;
  font-size: 17px;
}

.priority-pill {
  border-radius: 999px;
  background: rgba(217, 54, 79, 0.12);
  color: #a32035;
  font-size: 12px;
  padding: 6px 10px;
  white-space: nowrap;
}

.work-order-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-pill {
  border-radius: 999px;
  background: rgba(15, 139, 141, 0.12);
  color: #0f6f71;
  font-size: 12px;
  padding: 6px 10px;
  white-space: nowrap;
}

.work-order-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 14px 0;
  color: var(--ink-soft);
  font-size: 13px;
}

.work-order-card p {
  margin: 8px 0;
  color: #263f49;
}

.work-order-impact {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 12px 0;
}

.order-flow {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  list-style: none;
  margin: 12px 0;
  padding: 0;
}

.order-flow li {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 999px;
  color: var(--ink-soft);
  font-size: 12px;
  padding: 7px 8px;
  text-align: center;
}

.order-flow li.is-active {
  background: rgba(15, 139, 141, 0.12);
  color: #0f6f71;
}

.order-flow li.is-current {
  border-color: rgba(15, 139, 141, 0.32);
  font-weight: 700;
}

.work-order-business {
  border-radius: 14px;
  background: rgba(15, 139, 141, 0.08);
  padding: 10px 12px;
}

.decision-score-box {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(15, 139, 141, 0.16);
  border-radius: 14px;
  background: rgba(15, 139, 141, 0.08);
  padding: 12px;
  margin: 12px 0;
}

.decision-score-box > div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.decision-score-box span {
  color: var(--ink-soft);
  font-size: 12px;
}

.decision-score-box strong {
  color: var(--accent-deep);
  font-size: 22px;
}

.decision-score-box p {
  margin: 0;
  color: #263f49;
  font-size: 13px;
}

.work-order-actions {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.admin-action-grid,
.worker-submit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: end;
}

.worker-submit-grid label:nth-child(1),
.worker-submit-grid label:nth-child(2),
.review-panel label {
  grid-column: 1 / -1;
}

.review-panel {
  display: grid;
  gap: 12px;
}

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.status-quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-quick-actions button {
  border: 1px solid rgba(15, 139, 141, 0.2);
  border-radius: 14px;
  background: rgba(15, 139, 141, 0.1);
  color: #0f6f71;
  cursor: pointer;
  font: inherit;
  padding: 9px 12px;
}

.complete-button {
  border: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, #22a06b, #0f8b8d);
  color: white;
  cursor: pointer;
  font: inherit;
  padding: 10px 14px;
}

.work-order-actions label,
.simulation-form label {
  display: grid;
  gap: 7px;
  color: var(--ink-soft);
  font-size: 13px;
}

.work-order-actions select,
.work-order-actions textarea,
.work-order-actions input,
.simulation-form input {
  width: 100%;
  border: 1px solid rgba(20, 34, 48, 0.12);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ink-strong);
  font: inherit;
  padding: 10px 12px;
}

.work-order-note textarea {
  resize: vertical;
}

.checkbox-field {
  align-content: center;
  grid-template-columns: auto 1fr;
  min-height: 46px;
}

.checkbox-field input {
  width: 18px;
  height: 18px;
}

.timeline-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
  border-top: 1px solid rgba(20, 34, 48, 0.08);
  padding-top: 12px;
}

.timeline-list li {
  border-left: 3px solid rgba(15, 139, 141, 0.25);
  padding-left: 10px;
}

.timeline-list strong,
.timeline-list span,
.timeline-list p {
  display: block;
}

.timeline-list strong {
  color: var(--accent-deep);
  font-size: 13px;
}

.timeline-list span {
  color: var(--ink-soft);
  font-size: 12px;
}

.timeline-list p {
  margin: 2px 0 0;
  color: #263f49;
  font-size: 13px;
}

.forecast-chart {
  min-height: 230px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 4px 0;
}

.forecast-bar-wrap {
  flex: 1;
  display: grid;
  justify-items: center;
  align-items: end;
  gap: 8px;
  min-width: 0;
}

.forecast-bar {
  width: 100%;
  border-radius: 18px 18px 8px 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.38), transparent 35%),
    linear-gradient(180deg, #ffb84d, #0f8b8d);
  box-shadow: 0 14px 30px rgba(15, 139, 141, 0.18);
}

.forecast-bar-wrap strong {
  color: var(--accent-deep);
  font-size: 13px;
}

.forecast-bar-wrap span {
  color: var(--ink-soft);
  font-size: 12px;
  text-align: center;
}

.simulation-form {
  display: grid;
  gap: 16px;
  margin-bottom: 18px;
}

.simulation-form strong {
  color: var(--accent-deep);
}

.simulation-result {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 0;
}

.operation-report {
  border-radius: 24px;
  background:
    radial-gradient(circle at 8% 0%, rgba(255, 184, 77, 0.16), transparent 30%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(235, 247, 245, 0.9));
  border: 1px solid rgba(20, 34, 48, 0.08);
  padding: 22px;
}

.report-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.operation-report h3 {
  margin: 0 0 14px;
  color: var(--accent-deep);
}

.operation-report p {
  margin: 10px 0;
  color: #263f49;
}

.report-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.report-toolbar span {
  color: var(--ink-soft);
  font-size: 13px;
}

.report-action-list {
  display: grid;
  gap: 8px;
  margin: 16px 0 0;
  padding-left: 20px;
  color: #263f49;
}

.decision-list {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.decision-list li {
  display: grid;
  gap: 6px;
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  padding: 14px;
}

.decision-list strong {
  color: var(--accent-deep);
}

.decision-list span {
  color: var(--ink-soft);
}

.decision-list em {
  color: #263f49;
  font-style: normal;
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
  .login-panel,
  .login-role-grid,
  .command-layout,
  .business-kpi-grid,
  .worker-support-grid,
  .admin-action-grid,
  .worker-submit-grid {
    grid-template-columns: 1fr;
  }

  .user-strip {
    align-items: stretch;
    flex-direction: column;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .order-summary-grid,
  .order-impact-grid,
  .dispatch-header,
  .counterfactual-head,
  .dispatch-grid,
  .scenario-curve-grid,
  .order-preview-strip,
  .order-create-grid,
  .work-order-board,
  .work-order-impact,
  .order-flow,
  .work-order-meta,
  .analysis-filter-panel,
  .explain-metric-grid,
  .explain-detail-grid,
  .floor-registry-grid,
  .registry-meta,
  .report-metric-grid,
  .simulation-result {
    grid-template-columns: 1fr;
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

/* -------------------------------------------------- */
/* New: notification badge, before/after, closed cases */
/* -------------------------------------------------- */

.badge-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #d9364f;
  color: #fff;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  margin-left: 6px;
  animation: pulse-badge 1.8s ease-in-out infinite;
}

@keyframes pulse-badge {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}

.kpi--highlight {
  border-color: rgba(217, 54, 79, 0.35) !important;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(253, 235, 237, 0.9)) !important;
}

.before-after-compare {
  border: 1px solid rgba(34, 160, 107, 0.18);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(236, 251, 243, 0.88));
  padding: 14px;
  margin-top: 12px;
}

.before-after-compare h4 {
  margin: 0 0 10px;
  color: #15724d;
  font-size: 14px;
}

.before-after-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.before-after-grid > div {
  text-align: center;
  border: 1px solid rgba(20, 34, 48, 0.06);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  padding: 10px 6px;
}

.before-after-grid span {
  display: block;
  color: var(--ink-soft);
  font-size: 12px;
}

.before-after-grid strong {
  display: block;
  color: var(--accent-deep);
  font-size: 20px;
  margin-top: 4px;
}

.attachment-info {
  margin-top: 10px;
  border: 1px solid rgba(15, 139, 141, 0.14);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.74);
  padding: 10px;
  font-size: 13px;
  color: #263f49;
}

.attachment-info strong {
  color: var(--accent-deep);
}

.closed-cases-section {
  margin-top: 18px;
}

.closed-cases-section h4 {
  margin: 0 0 12px;
  color: var(--accent-deep);
  font-size: 15px;
}

.closed-case-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.closed-case-card {
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.88), rgba(242, 250, 250, 0.86));
  padding: 14px;
}

.closed-case-card h5 {
  margin: 0 0 8px;
  color: var(--accent-deep);
  font-size: 14px;
}

.closed-case-card p {
  margin: 0 0 6px;
  color: #263f49;
  font-size: 13px;
}

.closed-case-effect {
  color: #15724d !important;
  font-weight: 600;
}

.closed-case-time {
  display: block;
  color: var(--ink-soft);
  font-size: 11px;
  margin-top: 8px;
}

.estimate-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(20, 114, 77, 0.12);
  color: #15724d;
  font-size: 11px;
  font-weight: 600;
  vertical-align: middle;
}

.sim-strip {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 10px 16px;
  margin: 0 0 14px;
  padding: 12px 16px;
  border: 1px dashed rgba(20, 34, 48, 0.18);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(240, 243, 250, 0.85));
}

.sim-strip--active {
  border-style: solid;
  border-color: rgba(37, 99, 235, 0.35);
  background: linear-gradient(145deg, rgba(239, 246, 255, 0.95), rgba(224, 236, 255, 0.9));
}

.sim-clock {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 14px;
}

.sim-clock-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #2563eb;
  text-transform: uppercase;
}

.sim-clock-date {
  font-size: 22px;
  font-weight: 800;
  color: #14253a;
  font-variant-numeric: tabular-nums;
}

.sim-clock-date--off {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-soft);
}

.sim-clock-range,
.sim-clock-fixed {
  font-size: 12px;
  color: var(--ink-soft);
}

.sim-clock-fixed {
  color: #15724d;
  font-weight: 600;
}

.sim-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.reset-demo-button {
  margin-left: auto;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(220, 53, 69, 0.45);
  background: rgba(220, 53, 69, 0.08);
  color: #c0392b;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.reset-demo-button:hover:not(:disabled) {
  background: rgba(220, 53, 69, 0.16);
  border-color: rgba(220, 53, 69, 0.7);
}

.reset-demo-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.sim-hint {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 12px;
  color: var(--ink-soft);
  line-height: 1.5;
}
</style>

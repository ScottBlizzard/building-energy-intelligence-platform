const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function buildQueryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  return query.toString() ? `?${query.toString()}` : "";
}

export function buildApiUrl(path, params = {}) {
  return `${API_BASE}${path}${buildQueryString(params)}`;
}

async function request(path, options = {}, params = {}) {
  const response = await fetch(buildApiUrl(path, params), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

export function fetchOverview() {
  return request("/overview");
}

export function fetchDatasetMeta() {
  return request("/dataset-meta");
}

export function fetchBuildings() {
  return request("/buildings");
}

export function fetchRecords(params = {}) {
  return request("/records", {}, params);
}

export function fetchTimeSummary(params = {}) {
  return request("/analytics/time-summary", {}, params);
}

export function fetchBuildingComparison(params = {}) {
  return request("/analytics/building-comparison", {}, params);
}

export function fetchCopRanking(params = {}) {
  return request("/analytics/cop-ranking", {}, params);
}

export function fetchAnomalies(params = {}) {
  return request("/analytics/anomalies", {}, params);
}

export function fetchAnomalyExplanation(recordId) {
  return request(`/analytics/anomaly-explanations/${encodeURIComponent(recordId)}`);
}

export function fetchAnomalyReasons(params = {}) {
  return request("/analytics/anomaly-reasons", {}, params);
}

export function fetchFloorSummary(params = {}) {
  return request("/analytics/floor-summary", {}, params);
}

export function fetchFloorRegistry(params = {}) {
  return request("/analytics/floor-registry", {}, params);
}

export function fetchEquipmentSummary(params = {}) {
  return request("/analytics/equipment-summary", {}, params);
}

export function fetchWorkOrders(params = {}) {
  return request("/analytics/work-orders", {}, params);
}

export function fetchOptimizationRecommendations(params = {}) {
  return request("/analytics/optimization-recommendations", {}, params);
}

export function fetchOperationReport(params = {}) {
  return request("/analytics/operation-report", {}, params);
}

export function loginUser(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchCurrentUser(token) {
  return request("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export function fetchDemoUsers() {
  return request("/auth/users");
}

export function fetchAdminDashboard() {
  return request("/admin/dashboard");
}

export function fetchWorkerDashboard(userId) {
  return request(`/admin/worker-dashboard/${encodeURIComponent(userId)}`);
}

export function fetchAnomalyEvent(recordId) {
  return request(`/anomaly-events/${encodeURIComponent(recordId)}`);
}

export function fetchPersistentWorkOrders(params = {}) {
  return request("/work-orders", {}, params);
}

export function createPersistentWorkOrder(payload) {
  return request("/work-orders", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updatePersistentWorkOrder(workOrderId, payload) {
  return request(`/work-orders/${encodeURIComponent(workOrderId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function assignPersistentWorkOrder(workOrderId, payload) {
  return request(`/work-orders/${encodeURIComponent(workOrderId)}/assign`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function acceptPersistentWorkOrder(workOrderId, payload) {
  return request(`/work-orders/${encodeURIComponent(workOrderId)}/accept`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function submitPersistentWorkOrder(workOrderId, payload) {
  return request(`/work-orders/${encodeURIComponent(workOrderId)}/submit`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function reviewPersistentWorkOrder(workOrderId, payload) {
  return request(`/work-orders/${encodeURIComponent(workOrderId)}/review`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function ignorePersistentWorkOrder(workOrderId, payload) {
  return request(`/work-orders/${encodeURIComponent(workOrderId)}/ignore`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function createAutoConfirmQueue() {
  return request("/work-orders/auto-confirm-queue", {
    method: "POST"
  });
}

export function fetchSimState() {
  return request("/sim/state");
}

export function startSimulation(startDate = null) {
  return request("/sim/start", {
    method: "POST",
    body: JSON.stringify({ start_date: startDate })
  });
}

export function advanceSimulation(days = 1) {
  return request("/sim/advance", {
    method: "POST",
    body: JSON.stringify({ days })
  });
}

export function resetSimulation() {
  return request("/sim/reset", {
    method: "POST"
  });
}

export function fetchCounterfactualScenario(payload) {
  return request("/sim/counterfactual", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchAssistantProviders() {
  return request("/assistant/providers");
}

export function queryAssistant(question, modelSelection = null) {
  const body = { question };
  if (modelSelection?.provider && modelSelection?.model) {
    body.provider = modelSelection.provider;
    body.model = modelSelection.model;
  }

  return request("/assistant/query", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function fetchBudgets(params = {}) {
  return request("/budget/budgets", {}, params);
}

export function generateBudgets(year, month) {
  return request("/budget/budgets/generate", {
    method: "POST",
    body: JSON.stringify({})
  }, { year, month });
}

export function setBudget(payload) {
  return request("/budget/budgets", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchBudgetAnalysis(year, month) {
  return request("/budget/budgets/analysis", {}, { year, month });
}

export function fetchBudgetKPI(buildingId, year) {
  return request(`/budget/budgets/kpi/${encodeURIComponent(buildingId)}`, {}, { year });
}

export function fetchDecisionPriorities(limit = 10) {
  return request("/decisions/work-order-priorities", {}, { limit });
}

export function fetchDecisionDispatchPlan(workerCapacity = 3) {
  return request("/decisions/dispatch-plan", {}, { worker_capacity: workerCapacity });
}

export function fetchDecisionBudgetImpact(year = null, month = null) {
  return request("/decisions/budget-impact", {}, { year, month });
}

export function fetchDecisionROICandidates(limit = 8) {
  return request("/decisions/roi-candidates", {}, { limit });
}

export function fetchEquipmentAudit(buildingId) {
  return request(`/roi/audit/${encodeURIComponent(buildingId)}`);
}

export function analyzeROIProject(payload) {
  return request("/roi/analyze", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function compareROIScenarios(payload) {
  return request("/roi/compare", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function downloadCsvExport(params = {}) {
  const response = await fetch(buildApiUrl("/export/csv", params));

  if (!response.ok) {
    throw new Error(`Export failed: ${response.status}`);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/i);
  const filename = match?.[1] || "energy_records_export.csv";
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(objectUrl);

  return filename;
}

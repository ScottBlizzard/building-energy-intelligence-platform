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

export function fetchAnomalyReasons(params = {}) {
  return request("/analytics/anomaly-reasons", {}, params);
}

export function queryAssistant(question) {
  return request("/assistant/query", {
    method: "POST",
    body: JSON.stringify({ question })
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

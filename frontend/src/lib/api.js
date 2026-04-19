const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
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
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/records${suffix}`);
}

export function fetchTimeSummary(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/analytics/time-summary${suffix}`);
}

export function fetchBuildingComparison() {
  return request("/analytics/building-comparison");
}

export function fetchCopRanking() {
  return request("/analytics/cop-ranking");
}

export function fetchAnomalies(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/analytics/anomalies${suffix}`);
}

export function fetchAnomalyReasons() {
  return request("/analytics/anomaly-reasons");
}

export function queryAssistant(question) {
  return request("/assistant/query", {
    method: "POST",
    body: JSON.stringify({ question })
  });
}


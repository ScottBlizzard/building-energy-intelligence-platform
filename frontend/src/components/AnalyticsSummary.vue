<script setup>
import { computed } from 'vue';

const props = defineProps({
  analytics: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const hasAnalyticsData = computed(() => {
  return props.analytics.timeSummary?.length > 0 ||
         props.analytics.buildingComparison?.length > 0 ||
         props.analytics.copRanking?.length > 0 ||
         props.analytics.anomalies?.length > 0;
});

const latestTrendPoints = computed(() => 
  props.analytics.timeSummary?.slice(-8) || []
);

const trendMax = computed(() =>
  Math.max(...latestTrendPoints.value.map((item) => item.electricity_kwh || 0), 1)
);

const topComparison = computed(() => 
  props.analytics.buildingComparison?.slice(0, 4) || []
);
</script>

<template>
  <div class="analytics-summary">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>正在加载分析数据...</p>
    </div>
    
    <div v-else-if="!hasAnalyticsData" class="empty-state">
      <div class="empty-icon">📊</div>
      <p>暂无分析数据</p>
      <small>请检查后端连接或数据源配置</small>
    </div>
    
    <div v-else class="analytics-grid">
      <div class="analytics-card">
        <h3>日度能耗趋势</h3>
        <div class="trend-chart">
          <div 
            v-for="item in latestTrendPoints" 
            :key="item.timestamp" 
            class="trend-bar-container"
          >
            <div 
              class="trend-bar" 
              :style="{ height: `${Math.max((item.electricity_kwh / trendMax) * 100, 8)}%` }"
            ></div>
            <small>{{ item.timestamp.slice(5, 10) }}</small>
          </div>
        </div>
      </div>
      
      <div class="analytics-card">
        <h3>建筑对比</h3>
        <div class="comparison-list">
          <div 
            v-for="item in topComparison" 
            :key="item.building_id" 
            class="comparison-item"
          >
            <div>
              <strong>{{ item.building_name }}</strong>
              <span>{{ item.building_type }}</span>
            </div>
            <div class="comparison-values">
              <span>电耗 {{ item.electricity_kwh }}</span>
              <span>COP {{ item.average_cop }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="analytics-card">
        <h3>COP 排名</h3>
        <ul class="ranking-list">
          <li 
            v-for="item in analytics.copRanking" 
            :key="item.building_id"
            class="ranking-item"
          >
            <span>{{ item.building_name }}</span>
            <strong>COP {{ item.average_cop }}</strong>
          </li>
        </ul>
      </div>
      
      <div class="analytics-card">
        <h3>异常统计</h3>
        <div class="anomaly-summary">
          <div class="anomaly-count">
            <strong>{{ analytics.anomalies?.length || 0 }}</strong>
            <span>异常记录</span>
          </div>
          <ul class="anomaly-reasons">
            <li 
              v-for="reason in analytics.anomalyReasons" 
              :key="reason.anomaly_reason"
            >
              {{ reason.anomaly_reason }} · {{ reason.count }} 条
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-summary {
  min-height: 200px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(15, 139, 141, 0.2);
  border-top: 3px solid var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.analytics-card {
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(20, 34, 48, 0.08);
  border-radius: 22px;
  padding: 20px;
  backdrop-filter: blur(18px);
}

.analytics-card h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: var(--accent-deep);
}

.trend-chart {
  height: 120px;
  display: flex;
  align-items: end;
  gap: 8px;
  margin-bottom: 10px;
}

.trend-bar-container {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: end;
  align-items: center;
  gap: 6px;
}

.trend-bar {
  width: 100%;
  border-radius: 12px 12px 6px 6px;
  background: linear-gradient(180deg, rgba(15, 139, 141, 0.95), rgba(18, 93, 115, 0.55));
  min-height: 8px;
}

.trend-bar-container small {
  color: var(--ink-soft);
  font-size: 10px;
}

.comparison-list {
  display: grid;
  gap: 10px;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(243, 247, 246, 0.9);
  border: 1px solid rgba(20, 34, 48, 0.06);
}

.comparison-item strong,
.comparison-item span {
  display: block;
}

.comparison-item span {
  color: var(--ink-soft);
  font-size: 12px;
}

.comparison-values {
  display: grid;
  text-align: right;
  font-size: 12px;
}

.ranking-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.ranking-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(20, 34, 48, 0.08);
}

.ranking-item:last-child {
  border-bottom: none;
}

.anomaly-summary {
  display: grid;
  gap: 12px;
}

.anomaly-count {
  text-align: center;
  padding: 16px;
  background: rgba(255, 159, 28, 0.08);
  border-radius: 14px;
}

.anomaly-count strong {
  display: block;
  font-size: 24px;
  color: var(--warm);
}

.anomaly-count span {
  font-size: 12px;
  color: var(--ink-soft);
}

.anomaly-reasons {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
}

.anomaly-reasons li {
  padding: 4px 0;
  color: var(--ink-soft);
}

@media (max-width: 768px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
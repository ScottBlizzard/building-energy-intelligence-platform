<script setup>
import { computed } from "vue";

import { useEcharts } from "../lib/useEcharts";

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ""
  }
});

const chartOptions = computed(() => {
  if (!props.data.length) {
    return {
      title: {
        text: "暂无数据",
        left: "center",
        top: "middle",
        textStyle: {
          fontSize: 14,
          color: "#666"
        }
      },
      series: []
    };
  }

  const xAxisData = props.data.map(item => item.timestamp?.slice(5, 10) || "");
  const electricityData = props.data.map(item => item.electricity_kwh || 0);
  const hvacData = props.data.map(item => item.hvac_kwh || 0);

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross"
      },
      formatter: function(params) {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach(param => {
          result += `${param.marker} ${param.seriesName}: ${param.value} kWh<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: ["总电耗", "空调电耗"],
      top: 10
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: xAxisData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: "value",
      name: "能耗 (kWh)",
      nameTextStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: "总电耗",
        type: "line",
        smooth: true,
        data: electricityData,
        itemStyle: {
          color: "#5470c6"
        },
        areaStyle: {
          opacity: 0.3
        }
      },
      {
        name: "空调电耗",
        type: "line",
        smooth: true,
        data: hvacData,
        itemStyle: {
          color: "#91cc75"
        },
        areaStyle: {
          opacity: 0.3
        }
      }
    ]
  };
});

const { chartRef } = useEcharts(chartOptions);
</script>

<template>
  <div class="trend-chart">
    <div v-if="loading" class="chart-loading">
      <div class="loading-spinner"></div>
      <span>正在加载图表数据...</span>
    </div>
    <div v-else-if="error" class="chart-error">
      <div class="error-icon">⚠️</div>
      <div class="error-message">{{ error }}</div>
    </div>
    <div v-else ref="chartRef" class="chart-container"></div>
  </div>
</template>

<style scoped>
.trend-chart {
  width: 100%;
  height: 300px;
  position: relative;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #5470c6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #e74c3c;
}

.error-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.error-message {
  font-size: 14px;
  text-align: center;
}

@media (max-width: 768px) {
  .trend-chart {
    height: 250px;
  }
}
</style>

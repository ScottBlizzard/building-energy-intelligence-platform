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

  const reasons = props.data.map(item => item.anomaly_reason || "");
  const counts = props.data.map(item => item.count || 0);

  return {
    tooltip: {
      trigger: "item",
      formatter: function(params) {
        return `${params.name}<br/>异常次数: ${params.value} 条<br/>占比: ${params.percent}%`;
      }
    },
    legend: {
      orient: "vertical",
      left: "left",
      top: "middle",
      itemWidth: 14,
      itemHeight: 14,
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: "异常原因",
        type: "pie",
        radius: ["40%", "70%"],
        center: ["60%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: "#fff",
          borderWidth: 2
        },
        label: {
          show: false,
          position: "center"
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: "bold"
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.5)"
          }
        },
        labelLine: {
          show: false
        },
        data: reasons.map((reason, index) => ({
          name: reason,
          value: counts[index]
        }))
      }
    ],
    color: [
      "#5470c6",
      "#91cc75",
      "#fac858",
      "#ee6666",
      "#73c0de",
      "#3ba272",
      "#fc8452",
      "#9a60b4",
      "#ea7ccc"
    ]
  };
});

const { chartRef } = useEcharts(chartOptions);
</script>

<template>
  <div class="anomaly-reason-chart">
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
.anomaly-reason-chart {
  width: 100%;
  height: 350px;
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
  .anomaly-reason-chart {
    height: 300px;
  }
}
</style>

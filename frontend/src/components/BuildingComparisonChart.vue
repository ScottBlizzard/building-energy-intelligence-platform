<script setup>
import { computed, watch, ref } from "vue";
import * as echarts from "echarts";

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

const chartRef = ref(null);
let chartInstance = null;

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

  const buildingNames = props.data.map(item => item.building_name || "");
  const electricityData = props.data.map(item => item.electricity_kwh || 0);
  const copData = props.data.map(item => item.average_cop || 0);

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow"
      },
      formatter: function(params) {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach(param => {
          const unit = param.seriesName === "平均COP" ? "" : " kWh";
          result += `${param.marker} ${param.seriesName}: ${param.value}${unit}<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: ["电耗", "平均COP"],
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
      data: buildingNames,
      axisLabel: {
        rotate: 30,
        fontSize: 11
      }
    },
    yAxis: [
      {
        type: "value",
        name: "电耗 (kWh)",
        position: "left",
        nameTextStyle: {
          fontSize: 12
        }
      },
      {
        type: "value",
        name: "COP",
        position: "right",
        nameTextStyle: {
          fontSize: 12
        },
        min: 0,
        max: Math.max(...copData) * 1.2 || 5
      }
    ],
    series: [
      {
        name: "电耗",
        type: "bar",
        data: electricityData,
        itemStyle: {
          color: "#5470c6"
        },
        barWidth: "40%"
      },
      {
        name: "平均COP",
        type: "line",
        yAxisIndex: 1,
        data: copData,
        itemStyle: {
          color: "#91cc75"
        },
        symbol: "circle",
        symbolSize: 6,
        lineStyle: {
          width: 2
        }
      }
    ]
  };
});

watch(() => props.data, () => {
  if (chartInstance) {
    chartInstance.setOption(chartOptions.value);
  }
}, { deep: true });

watch(chartRef, (newRef) => {
  if (newRef && !chartInstance) {
    chartInstance = echarts.init(newRef);
    chartInstance.setOption(chartOptions.value);
    
    // 响应式处理
    const resizeObserver = new ResizeObserver(() => {
      chartInstance?.resize();
    });
    resizeObserver.observe(newRef);
  }
});
</script>

<template>
  <div class="building-comparison-chart">
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
.building-comparison-chart {
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
  .building-comparison-chart {
    height: 300px;
  }
}
</style>
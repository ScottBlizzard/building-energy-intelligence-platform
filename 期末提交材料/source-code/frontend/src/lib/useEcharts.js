import { nextTick, onBeforeUnmount, ref, watch } from "vue";

import { init } from "./chartCore";

export function useEcharts(chartOptions) {
  const chartRef = ref(null);
  let chartInstance = null;
  let resizeObserver = null;

  function disposeChart() {
    resizeObserver?.disconnect();
    resizeObserver = null;
    chartInstance?.dispose();
    chartInstance = null;
  }

  async function renderChart() {
    await nextTick();

    if (!chartRef.value) {
      disposeChart();
      return;
    }

    if (!chartInstance) {
      chartInstance = init(chartRef.value);
      resizeObserver = new ResizeObserver(() => {
        chartInstance?.resize();
      });
      resizeObserver.observe(chartRef.value);
    }

    chartInstance.setOption(chartOptions.value, true);
    chartInstance.resize();
  }

  watch(chartRef, renderChart);
  watch(chartOptions, renderChart, { deep: true });
  onBeforeUnmount(disposeChart);

  return {
    chartRef
  };
}

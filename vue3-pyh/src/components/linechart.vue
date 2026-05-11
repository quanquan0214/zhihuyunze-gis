<template>
    <div>
        <div id="barChart" ref="barRef"></div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
    data: { type: Array, default: () => [] } // [{value, name}]
});

const barRef = ref(null);

let barChart = null;


function renderBar() {
    if (!barRef.value) return;
    if (!barChart) barChart = echarts.init(barRef.value);
    const option = {
  title: {
    text: 'Stacked Line'
  },
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['Email', 'Union Ads', 'Video Ads', 'Direct', 'Search Engine']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  toolbox: {
    feature: {
      saveAsImage: {}
    }
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: 'Email',
      type: 'line',
      stack: 'Total',
      data: [120, 132, 101, 134, 90, 230, 210]
    },
    {
      name: 'Union Ads',
      type: 'line',
      stack: 'Total',
      data: [220, 182, 191, 234, 290, 330, 310]
    },
    {
      name: 'Video Ads',
      type: 'line',
      stack: 'Total',
      data: [150, 232, 201, 154, 190, 330, 410]
    },
    {
      name: 'Direct',
      type: 'line',
      stack: 'Total',
      data: [320, 332, 301, 334, 390, 330, 320]
    },
    {
      name: 'Search Engine',
      type: 'line',
      stack: 'Total',
      data: [820, 932, 901, 934, 1290, 1330, 1320]
    }
  ]
};
barChart.setOption(option)
    barChart.resize();
}

onMounted(() => {
    renderBar();
    window.addEventListener('resize', () => {
        barChart && barChart.resize();
    });
});

watch(() => props.data, () => {
    renderBar();
}, { deep: true });
</script>

<style scoped>
#barChart {
    width: 100%;
    height: 220px;
    margin-bottom: 1rem;
    border-radius: 4px;
    /* border: 1px solid var(--accent-blue); */
    background: transparent;
}
</style>
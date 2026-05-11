<template>
  <div class="region-compare-dialog">
    <div class="dialog-header">
      <h3>区域对比分析</h3>
      <button @click="$emit('close')" class="close-btn">&times;</button>
    </div>
    <div class="dialog-content">    
      <!-- 图表分页区域 -->
      <div class="charts-section">
        <div class="chart-tabs">
          <button
            v-for="tab in chartTabs"
            :key="tab.key"
            class="chart-tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <div class="chart-container" v-show="activeTab === 'trend'">
          <div ref="trendChartRef" style="width: 100%; height: 300px;"></div>
        </div>
        <div class="chart-container" v-show="activeTab === 'avgChange'">
          <div ref="avgChangeChartRef" style="width: 100%; height: 300px;"></div>
        </div>
        <div class="chart-container" v-show="activeTab === 'normalize'">
          <div ref="normalizeChartRef" style="width: 100%; height: 300px;"></div>
          <div class="normalize-desc">
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';

const props = defineProps<{ data: any }>();
const emit = defineEmits(['close']);

const chartTabs = [
  { key: 'trend', label: '时间序列对比' },
  { key: 'avgChange', label: '年均变化率对比' },
  { key: 'normalize', label: '归一化指标对比' }
];
const activeTab = ref('trend');

const trendChartRef = ref<HTMLElement | null>(null);
const avgChangeChartRef = ref<HTMLElement | null>(null);
const normalizeChartRef = ref<HTMLElement | null>(null);

let trendChart: echarts.ECharts | null = null;
let avgChangeChart: echarts.ECharts | null = null;
let normalizeChart: echarts.ECharts | null = null;

function createTrendChart() {
  if (!trendChartRef.value) return;
  trendChart = echarts.init(trendChartRef.value);
  const timeSeriesData = props.data.图表数据.Time_Series;
  const option = {
    title: { text: '时间序列对比', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: '5%' },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 23 }, (_, i) => 2000 + i)
    },
    yAxis: {
      type: 'value',
      name: '指数值'
    },
    series: Object.entries(timeSeriesData).map(([key, data]: [string, any]) => ({
      name: data.region_name,
      type: 'line',
      data: data.value,
      smooth: true
    }))
  };
  trendChart.setOption(option);
}

function createAvgChangeChart() {
  if (!avgChangeChartRef.value) return;
  avgChangeChart = echarts.init(avgChangeChartRef.value);
  const changeTrend = props.data.图表数据.Change_Trend || {};
  // region_name 需从 Time_Series 映射
  const regionNameMap: Record<string, string> = {};
  const timeSeriesData = props.data.图表数据.Time_Series || {};
  Object.entries(timeSeriesData).forEach(([key, val]: [string, any]) => {
    regionNameMap[key] = val.region_name;
  });

  const regions = Object.keys(changeTrend);
  const names = regions.map(key => regionNameMap[key] || key);
  const avgRates = regions.map(key => {
    const v = changeTrend[key]?.["Annual average rate of change"];
    return v !== undefined ? (v ).toFixed(8) : 0; // 转为百分比
  });
  const totals = regions.map(key => {
    const v = changeTrend[key]?.["Total of change"];
    return v !== undefined ? v.toFixed(8) : 0;
  });

  const option = {
    title: { text: '年均变化率对比', left: 'center' },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        // params为数组
        let res = '';
        params.forEach((param: any, idx: number) => {
          res += `${param.marker}${param.seriesName}: ${param.value}${param.seriesName === '年均变化率' ? '%' : ''}<br/>`;
          if (param.seriesName === '年均变化率') {
            res += `总变化量: ${totals[param.dataIndex]}<br/>`;
          }
        });
        return res;
      }
    },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: names
    },
    yAxis: {
      type: 'value',
      name: '年均变化率(%)'
    },
    series: [
      {
        name: '年均变化率',
        type: 'bar',
        data: avgRates,
        itemStyle: { color: '#91cc75' },
        label: { show: true, position: 'top', formatter: '{c}%' }
      }
    ]
  };
  avgChangeChart.setOption(option);
}

function createNormalizeChart() {
  if (!normalizeChartRef.value) return;
  normalizeChart = echarts.init(normalizeChartRef.value);
  const normIndexData = props.data.图表数据.Normalize || {};
  const fitInfo = props.data.分析摘要['归一化指标拟合'] || {};
  const a = Number(fitInfo['斜率(k)']) || 0.23456;
  const b = Number(fitInfo['截距(b)']) || 0.789;

  // 取每个城市所有年份的归一化总值和标准差，作为散点
  const scatterData: { name: string; value: [number, number] }[] = [];
  Object.values(normIndexData).forEach((d: any) => {
    if (Array.isArray(d.value)) {
      d.value.forEach((arr: [number, number], idx: number) => {
        // arr[0]: 总值, arr[1]: 标准差
        // 只添加有效点
        if (typeof arr[0] === 'number' && typeof arr[1] === 'number') {
          scatterData.push({
            name: `${d.region_name} (${2000 + idx}年)`,
            value: [arr[0], arr[1]]
          });
        }
      });
    }
  });

  // 计算x和y的范围
  const xArr = scatterData.map(d => d.value[0]);
  const yArr = scatterData.map(d => d.value[1]);
  const minX = Math.floor(Math.min(...xArr) * 10) / 10;
  const maxX = Math.ceil(Math.max(...xArr) * 10) / 10;
  const minY = Math.floor(Math.min(...yArr) * 10) / 10;
  const maxY = Math.ceil(Math.max(...yArr) * 10) / 10;

  // 生成拟合直线的两个端点
  const fitLine = [
    [minX, a * minX + b],
    [maxX, a * maxX + b]
  ];

  const option = {
    title: { text: '归一化指标对比', left: 'center' },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.seriesType === 'scatter') {
          return `${params.data.name}<br/>归一化总值: ${params.data.value[0]}<br/>归一化标准差: ${params.data.value[1]}`;
        }
        if (params.seriesType === 'line') {
          return `拟合方程: ${fitInfo['拟合方程'] || `y = ${a}x + ${b}`}`;
        }
        return '';
      }
    },
    grid: { left: '8%', right: '8%', bottom: '12%', top: 50, containLabel: true },
    xAxis: {
      type: 'value',
      name: '归一化总值',
      min: minX,
      max: maxX
    },
    yAxis: {
      type: 'value',
      name: '归一化标准差',
      min: minY,
      max: maxY
    },
    series: [
      {
        name: '城市',
        type: 'scatter',
        data: scatterData,
        symbolSize: 10,
        itemStyle: { color: '#4a90e2' },
        emphasis: {
          label: {
            show: true,
            formatter: (param: any) => param.data.name,
            position: 'top'
          }
        }
      },
      {
        name: '拟合直线',
        type: 'line',
        data: fitLine,
        showSymbol: false,
        lineStyle: { color: '#e74c3c', width: 2 },
        label: {
          show: true,
          position: 'insideEnd', // 确保label显示在直线末端
          formatter: fitInfo['拟合方程'] || `y = ${a.toFixed(4)}x + ${b.toFixed(4)}`,
          fontWeight: 'bold',
          color: '#e74c3c',
          fontSize: 14,
          backgroundColor: '#fff',
          padding: [2, 4]
        }
      }
    ]
  };
  normalizeChart.setOption(option);
}

function destroyCharts() {
  if (trendChart) { trendChart.dispose(); trendChart = null; }
  if (avgChangeChart) { avgChangeChart.dispose(); avgChangeChart = null; }
  if (normalizeChart) { normalizeChart.dispose(); normalizeChart = null; }
}

function renderActiveChart() {
  destroyCharts();
  if (activeTab.value === 'trend') createTrendChart();
  if (activeTab.value === 'avgChange') createAvgChangeChart();
  if (activeTab.value === 'normalize') createNormalizeChart();
}

onMounted(() => {
  nextTick(renderActiveChart);
});
onUnmounted(() => {
  destroyCharts();
});
watch(activeTab, async () => {
  await nextTick();
  renderActiveChart();
});
</script>

<style scoped>
.region-compare-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  max-height: 80vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.dialog-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-content {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(80vh - 60px);
}
.chart-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.chart-tab-btn {
  padding: 8px 16px;
  border: none;
  background: #f0f2f5;
  color: #666;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
}

.chart-tab-btn.active {
  background: #1890ff;
  color: #fff;
  font-weight: 500;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.normalize-desc {
  margin-top: 10px;
  font-size: 13px;
  color: #888;
  line-height: 1.6;
}
</style>

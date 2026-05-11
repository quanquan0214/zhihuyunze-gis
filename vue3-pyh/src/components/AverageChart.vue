<template>
  <div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import api from '@/utils/request';

const props = defineProps({
  category: {
    type: String,
    required: true
  },
  cachedData: {
    type: Object,
    default: () => ({})
  }
});

const chartRef = ref(null);
let chart = null;

// 获取历史平均值数据
async function fetchHistoricalData() {
  try {
    const years = Array.from({ length: 23 }, (_, i) => 2000 + i);
    const allData = [];
    
    // 使用 Promise.all 并行请求所有年份的数据
    const promises = years.map(async (year) => {
      // 如果数据已缓存，直接使用缓存数据
      if (props.cachedData[year]) {
        return {
          year,
          data: props.cachedData[year]
        };
      }

      const response = await api.get('/api/RT/avg', {
        params: {
          year: year,
          data_type: props.category === 'wendu' ? 'temperature' : 'rainfall'
        }
      });
      
      return {
        year,
        data: response.data
      };
    });

    const results = await Promise.all(promises);
    
    // 处理所有年份的数据
    results.forEach(({ year, data }) => {
      if (Array.isArray(data)) {
        data.forEach((value, monthIndex) => {
          allData.push({
            year: year,
            month: monthIndex + 1,
            value: value
          });
        });
      }
    });
    
    return allData;
  } catch (error) {
    console.error('获取历史数据失败:', error);
    return [];
  }

}

function renderChart(data) {
  if (!chartRef.value) return;
  if (!chart) {
    chart = echarts.init(chartRef.value);
  }

  // 按月份分组数据
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const series = months.map(month => {
    const monthData = data.filter(item => item.month === month);
    return {
      name: `${month}月`,
      type: 'line',
      data: monthData.map(item => item.value),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        width: 2
      }
    };
  });

  const option = {
    title: {
      text: props.category === 'wendu' ? '月均温度变化趋势' : '月均降水变化趋势',
      left: 'center',
      textStyle: {
        fontSize: 14,
        color: '#333'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = `${params[0].axisValue}年<br/>`;
        params.forEach(param => {
          if (param.value !== null) {
            result += `${param.seriesName}: ${param.value.toFixed(2)}${props.category === 'wendu' ? '°C' : 'mm'}<br/>`;
          }
        });
        return result;
      }
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      data: months.map(m => `${m}月`)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 23 }, (_, i) => 2000 + i),
      name: '年份',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: props.category === 'wendu' ? '温度(°C)' : '降水量(mm)',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: series
  };

  chart.setOption(option);
}

// 监听category变化
watch(() => props.category, async () => {
  const data = await fetchHistoricalData();
  renderChart(data);
});

let resizeHandler = null;

onMounted(async () => {
  const data = await fetchHistoricalData();
  renderChart(data);
  
  // 使用防抖处理resize事件
  resizeHandler = debounce(() => {
    if (chart) {
      chart.resize();
    }
  }, 100);
  
  window.addEventListener('resize', resizeHandler);
});

onUnmounted(() => {
  if (chart) {
    chart.dispose();
    chart = null;
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
    resizeHandler = null;
  }
});

// 防抖函数
function debounce(fn, delay) {
  let timer = null;
  return function() {
    if (timer) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => {
      fn.apply(this, arguments);
    }, delay);
  };
}

function disposeChart() {
  if (chart) {
    chart.dispose();
    chart = null;
  }
}

defineExpose({
  disposeChart
});
</script>

<style scoped>
</style> 

<template>
  <el-dialog
    v-model="dialogVisible"
    title="土地利用分析"
    width="90%"
    :before-close="handleClose"
    class="land-analysis-dialog"
  >
    <div class="analysis-content">
      <div class="chart-container">
        <!-- 添加年份选择器 -->
        <div v-if="analysisMode === 'timeseries' || analysisMode === 'matrix'" class="year-selector">
          <el-select v-model="startYear" placeholder="起始年份" size="small">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year.toString()"
              :value="year"
            />
          </el-select>
          <span class="year-separator">至</span>
          <el-select v-model="endYear" placeholder="结束年份" size="small">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year.toString()"
              :value="year"
            />
          </el-select>
        </div>
        <!-- 添加指标选择器 -->
        <div v-if="analysisMode === 'comparison'" class="metric-selector">
          <el-select v-model="comparisonMetric" placeholder="选择指标" size="small">
            <el-option label="面积" value="area" />
            <el-option label="变化" value="change" />
            <el-option label="异常" value="anomaly" />
          </el-select>
        </div>
        <div v-if="analysisMode === 'timeseries'" id="timeseries-chart" style="width: 100%; height: 500px;"></div>
        <div v-if="analysisMode === 'comparison'" id="comparison-chart" style="width: 100%; height: 500px;"></div>
        <div v-if="analysisMode === 'matrix'">
          <div id="matrix-chart" style="width: 100%; height: 500px;"></div>
          <!-- 主要土地类型转换说明 -->
          <div v-if="majorTransitions && majorTransitions.length" class="transition-summary">
            <h4>主要土地类型转换（面积前10）</h4>
            <ul>
              <li v-for="(item, idx) in majorTransitions" :key="idx">
                {{ item.from }} → {{ item.to }}：{{ item.area }} km²
              </li>
            </ul>
            <div class="transition-stats">
              稳定性比例：{{ stabilityRatio }}% ，总转换数：{{ totalTransitions }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import api from '@/utils/request';

interface TransitionResponse {
  status: string;
  sankey_data: {
    nodes: any[];
    links: any[];
    from_year: number;
    to_year: number;
  };
  transition_stats: {
    major_transitions: Array<{
      from: string;
      to: string;
      area: number;
    }>;
    stability_ratio: number;
    total_transitions: number;
  };
}

// 修改类型定义
interface ChartData {
  type: string;
  name: string;
  data: number[];
  stack?: string;
  emphasis?: {
    focus: string;
  };
}

type ChartOption = {
  title: {
    text: string;
    left: string;
  };
  tooltip: {
    trigger: string;
    axisPointer: {
      type: string;
    };
  };
  legend: {
    data: string[];
    bottom: number;
  };
  grid: {
    left: string;
    right: string;
    bottom: string;
    containLabel: boolean;
  };
  xAxis: {
    type: 'category';
    data: string[];
  };
  yAxis: {
    type: 'value';
    name: string;
  };
  series: ChartData[];
} & echarts.EChartsOption;

const props = defineProps<{
  modelValue: boolean;
  data: {
    data: {
      comparison_stats?: {
        area_comparison: Record<string, number>;
        land_types: string[];
        total_regions: number;
        year_range: number[];
      };
      metric?: string;
      regions?: Record<string, any>;
      relative_changes?: Record<string, Record<string, number>>;
      annual_change_rates?: Record<string, number[]>;
      anomalies?: Record<string, Record<string, number>>;
      sankey_data?: {
        nodes: any[];
        links: any[];
        from_year: number;
        to_year: number;
      };
      transition_stats?: {
        major_transitions: Array<{
          from: string;
          to: string;
          area: number;
        }>;
        stability_ratio: number;
        total_transitions: number;
      };
      region?: any;
    };
  };
  analysisMode: 'timeseries' | 'comparison' | 'matrix' | null;
  comparisonMetric: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'close'): void;
  (e: 'update:comparisonMetric', value: string): void;
}>();

const dialogVisible = ref(props.modelValue);
let timeseriesChart: echarts.ECharts | null = null;
let changesChart: echarts.ECharts | null = null;
let matrixChart: echarts.ECharts | null = null;

const startYear = ref<number>(2000);
const endYear = ref<number>(2022);

// 使用计算属性来处理 comparisonMetric
const comparisonMetric = computed({
  get: () => props.comparisonMetric,
  set: (value) => emit('update:comparisonMetric', value)
});

const yearOptions = computed(() => {
  const years: number[] = [];
  for (let year = 2000; year <= 2022; year++) {
    years.push(year);
  }
  return years;
});

function normalizeRegionGeometry(region: any) {
  if (!region) return null;
  if (region.type === 'Feature' && region.geometry) return region.geometry;
  if (region.type === 'FeatureCollection' && Array.isArray(region.features) && region.features[0]?.geometry) {
    return region.features[0].geometry;
  }
  return region;
}

// 添加一个标志来跟踪是否正在尝试渲染
let isRendering = false;
let pendingRender = false;

watch([startYear, endYear], async ([newStart, newEnd]) => {
  const start = typeof newStart === 'number' ? newStart : parseInt(newStart as any, 10);
  const end = typeof newEnd === 'number' ? newEnd : parseInt(newEnd as any, 10);

  if (isNaN(start) || isNaN(end)) {
    console.error('Invalid year values:', { start, end });
    return;
  }

  if (start > end) {
    const temp = startYear.value;
    startYear.value = endYear.value;
    endYear.value = temp;
    return;
  }

  if (props.analysisMode === 'timeseries') {
    nextTick(() => {
      renderTimeseriesChart();
    });
  } else if (props.analysisMode === 'matrix') {
    try {
      const region = normalizeRegionGeometry(props.data.data.region);
      if (!region) {
        console.error('区域数据不存在');
        ElMessage.error('区域数据不存在，请重新绘制区域');
        return;
      }

      console.log('重新获取桑基图数据:', {
        fromYear: start,
        toYear: end,
        region
      });

      const response = await api.get<TransitionResponse>('/api/transition', {
        params: {
          from_year: start,
          to_year: end,
          region: JSON.stringify(region)
        }
      });

      // 检查响应结构
      if (!response?.data?.sankey_data || !response?.data?.transition_stats) {
        console.error('API响应缺少必要数据:', {
          hasSankeyData: !!response?.data?.sankey_data,
          hasTransitionStats: !!response?.data?.transition_stats
        });
        ElMessage.error('获取转换矩阵数据失败: 数据不完整');
        return;
      }

      // 更新数据
      props.data.data.sankey_data = response.data.sankey_data;
      props.data.data.transition_stats = response.data.transition_stats;
      
      // 重新渲染图表
      nextTick(() => {
        renderMatrixChart();
      });
    } catch (error) {
      console.error('获取转换矩阵数据失败:', error);
      ElMessage.error('获取转换矩阵数据失败: ' + (error instanceof Error ? error.message : '未知错误'));
    }
  }
});

watch(() => props.modelValue, (newVal) => {
  dialogVisible.value = newVal;
  if (newVal && props.analysisMode) {
    console.log('弹窗显示，当前模式:', props.analysisMode);
    nextTick(() => {
      renderCurrentChart();
    });
  }
});

watch(() => dialogVisible.value, (newVal) => {
  emit('update:modelValue', newVal);
  if (!newVal) {
    // 对话框关闭时，清理图表
    if (timeseriesChart) {
      timeseriesChart.dispose();
      timeseriesChart = null;
    }
    if (changesChart) {
      changesChart.dispose();
      changesChart = null;
    }
    if (matrixChart) {
      matrixChart.dispose();
      matrixChart = null;
    }
  }
});

watch(() => props.analysisMode, (newVal) => {
  console.log('分析模式变化:', newVal);
  if (!newVal) {
    console.log('分析模式为空，不渲染图表');
    return;
  }
  
  if (!dialogVisible.value) {
    console.log('对话框未显示，等待显示后再渲染图表');
    return;
  }

  nextTick(() => {
    console.log('分析模式变化后开始渲染图表');
    renderCurrentChart();
  });
});

function handleClose() {
  dialogVisible.value = false;
  emit('close');
}

function renderCurrentChart() {
  console.log('当前分析模式:', props.analysisMode);
  if (!props.analysisMode) {
    console.log('分析模式为空，不渲染图表');
    return;
  }
  
  if (!dialogVisible.value) {
    console.log('对话框未显示，不渲染图表');
    return;
  }
  
  switch (props.analysisMode) {
    case 'timeseries':
      console.log('渲染时序分析图表');
      renderTimeseriesChart();
      break;
    case 'comparison':
      console.log('渲染对比分析图表');
      renderComparisonChart();
      break;
    case 'matrix':
      console.log('渲染转换矩阵图表');
      renderMatrixChart();
      break;
  }
}

function renderTimeseriesChart() {
  if (!props.data) {
    console.log('时序分析数据为空');
    return;
  }

  if (!dialogVisible.value) {
    console.log('对话框未显示，不渲染时序分析图表');
    return;
  }

  // 使用 nextTick 确保 DOM 已更新
  nextTick(() => {
    const container = document.getElementById('timeseries-chart');
    if (!container) {
      console.log('找不到时序分析图表容器，等待DOM更新');
      // 如果容器不存在，等待一段时间后重试
      setTimeout(() => {
        if (props.analysisMode === 'timeseries' && dialogVisible.value) {
          renderTimeseriesChart();
        }
      }, 200); // 增加延迟时间
      return;
    }

    if (timeseriesChart) {
      timeseriesChart.dispose();
    }

    try {
      timeseriesChart = echarts.init(container);
      console.log('初始化时序分析图表');

      const relativeChanges = props.data.data?.relative_changes || {};
      console.log('时序分析相对变化数据:', relativeChanges);

      if (Object.keys(relativeChanges).length === 0) {
        console.log('时序分析数据为空对象');
        return;
      }

      const filteredYears = Object.keys(relativeChanges)
        .filter(year => parseInt(year) >= startYear.value && parseInt(year) <= endYear.value)
        .sort();
      
      const landTypes = new Set<string>();
      
      const firstYear = filteredYears[0];
      if (firstYear && relativeChanges[firstYear]) {
        Object.keys(relativeChanges[firstYear]).forEach(type => landTypes.add(type));
      }
      
      console.log('提取的年份:', filteredYears);
      console.log('提取的土地类型:', Array.from(landTypes));

      const series = Array.from(landTypes).map(type => {
        const data = filteredYears.map(year => {
          const yearData = relativeChanges[year] || {};
          return yearData[type] || 0;
        });

        return {
          name: type,
          type: 'line',
          data: data,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8
        };
      });
      console.log('准备的图表数据:', series);

      const option = {
        title: {
          text: '土地类型年平均变化率',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: Array.from(landTypes),
          top: 30
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: filteredYears,
          name: '年份'
        },
        yAxis: {
          type: 'value',
          name: '年平均变化率 (%)',
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: series
      };

      console.log('设置图表配置:', option);
      timeseriesChart.setOption(option);
      console.log('图表渲染完成');
    } catch (error) {
      console.error('渲染时序分析图表失败:', error);
      // 如果渲染失败，等待一段时间后重试
      setTimeout(() => {
        if (props.analysisMode === 'timeseries' && dialogVisible.value) {
          renderTimeseriesChart();
        }
      }, 200);
    }
  });
}

function renderMatrixChart() {
  if (!props.data) {
    console.log('转换矩阵数据为空');
    return;
  }

  const container = document.getElementById('matrix-chart');
  if (!container) {
    console.log('找不到转换矩阵图表容器');
    return;
  }

  if (matrixChart) {
    matrixChart.dispose();
  }

  matrixChart = echarts.init(container);
  console.log('初始化转换矩阵图表');

  // 使用正确的数据路径
  const sankeyData = props.data.data?.sankey_data;
  console.log('桑基图原始数据:', sankeyData);

  if (!sankeyData || !sankeyData.nodes || !sankeyData.links) {
    matrixChart.clear();
    matrixChart.showLoading({
      text: '暂无可用的转换矩阵数据',
      color: '#888',
      textColor: '#888',
      maskColor: 'rgba(255,255,255,0.8)',
      zlevel: 0
    });
    return;
  }

  // 创建新的桑基图数据对象，避免修改原始数据
  const newSankeyData = {
    nodes: [...sankeyData.nodes],
    links: [...sankeyData.links],
    from_year: startYear.value,
    to_year: endYear.value
  };

  const option = {
    title: {
      text: '土地类型转换桑基图',
      subtext: `${newSankeyData.from_year}年 到 ${newSankeyData.to_year}年`,
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      formatter: function(params: any) {
        if (params.dataType === 'node') {
          return params.name;
        } else if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br>面积: ${params.data.value} 平方千米`;
        }
      }
    },
    series: [{
      type: 'sankey',
      data: newSankeyData.nodes,
      links: newSankeyData.links,
      emphasis: {
        focus: 'adjacency'
      },
      levels: [{
        depth: 0,
        itemStyle: {
          color: '#fbb4ae'
        },
        lineStyle: {
          color: 'source',
          opacity: 0.6
        }
      }, {
        depth: 1,
        itemStyle: {
          color: '#b3cde3'
        },
        lineStyle: {
          color: 'source',
          opacity: 0.6
        }
      }, {
        depth: 2,
        itemStyle: {
          color: '#ccebc5'
        },
        lineStyle: {
          color: 'source',
          opacity: 0.6
        }
      }, {
        depth: 3,
        itemStyle: {
          color: '#decbe4'
        },
        lineStyle: {
          color: 'source',
          opacity: 0.6
        }
      }],
      lineStyle: {
        curveness: 0.5
      },
      label: {
        color: 'rgba(0,0,0,0.7)',
        fontSize: 12
      },
      nodeWidth: 15,
      nodeGap: 25
    }]
  };

  console.log('设置桑基图配置:', option);
  matrixChart.setOption(option);

  // 支持窗口自适应
  window.addEventListener('resize', () => {
    matrixChart && matrixChart.resize();
  });

  console.log('桑基图渲染完成');
}

function renderComparisonChart() {
  if (!props.data?.data?.regions) {
    console.log('对比分析数据为空');
    return;
  }

  const container = document.getElementById('comparison-chart');
  if (!container) {
    console.log('找不到对比分析图表容器');
    return;
  }

  if (changesChart) {
    changesChart.dispose();
  }

  changesChart = echarts.init(container);
  console.log('初始化对比分析图表');

  const regions = Object.keys(props.data.data.regions);
  const regionData = props.data.data.regions;
  const metric = props.data.data.metric || comparisonMetric.value; // 优先使用props中的metric
  
  let seriesData: ChartData[] = [];
  let xAxisData: string[] = [];
  let legendData: string[] = [];
  
  try {
    if (metric === 'area') {
      // 面积对比图表
      const landTypes = new Set<string>();
      
      regions.forEach(region => {
        const rawData = regionData[region].raw_data;
        if (rawData && typeof rawData === 'object') {
          const years = Object.keys(rawData).sort();
          const latestYear = years[years.length - 1];
          
          if (latestYear && rawData[latestYear]) {
            Object.keys(rawData[latestYear]).forEach(type => {
              landTypes.add(type);
            });
          }
        }
      });
      
      legendData = Array.from(landTypes);
      xAxisData = regions;
      
      legendData.forEach(type => {
        const series: ChartData = {
          name: type,
          type: 'bar',
          stack: 'total',
          emphasis: {
            focus: 'series'
          },
          data: []
        };
        regions.forEach(region => {
          const rawData = regionData[region].raw_data;
          if (rawData && typeof rawData === 'object') {
            const years = Object.keys(rawData).sort();
            const latestYear = years[years.length - 1];
            if (latestYear && rawData[latestYear]) {
              series.data.push(Number(rawData[latestYear][type] ?? 0));
            } else {
              series.data.push(0);
            }
          } else {
            series.data.push(0);
          }
        });
        seriesData.push(series);
      });
      
      const option: ChartOption = {
        title: {
          text: '区域土地覆盖面积对比',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: legendData,
          bottom: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData
        },
        yAxis: {
          type: 'value',
          name: '面积 (平方千米)'
        },
        series: seriesData
      };
      
      changesChart.setOption(option);
      
    } else if (metric === 'change') {
      // 变化对比图表
      const landTypes = new Set<string>();
      
      regions.forEach(region => {
        const relativeChanges = regionData[region].relative_changes;
        if (relativeChanges && typeof relativeChanges === 'object') {
          Object.keys(relativeChanges).forEach(type => {
            landTypes.add(type);
          });
        }
      });
      
      legendData = Array.from(landTypes);
      xAxisData = regions;
      
      legendData.forEach(type => {
        const series: ChartData = {
          name: type,
          type: 'bar',
          emphasis: {
            focus: 'series'
          },
          data: []
        };
        
        regions.forEach(region => {
          const relativeChanges = regionData[region].relative_changes;
          if (relativeChanges && relativeChanges[type]) {
            // 计算平均变化率
            const changes = relativeChanges[type] as Record<string, number>;
            const sum = Object.values(changes).reduce((a, b) => a + b, 0);
            const avg = sum / Object.keys(changes).length;
            series.data.push(avg);
          } else {
            series.data.push(0);
          }
        });
        
        seriesData.push(series);
      });
      
      const option: ChartOption = {
        title: {
          text: '区域土地覆盖变化率对比 (%)',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: legendData,
          bottom: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData
        },
        yAxis: {
          type: 'value',
          name: '平均变化率 (%)'
        },
        series: seriesData
      };
      
      changesChart.setOption(option);
      
    } else if (metric === 'anomaly') {
      // 异常对比图表
      const anomalyTypes = ['increase', 'decrease'];
      legendData = anomalyTypes;
      xAxisData = regions;
      
      anomalyTypes.forEach(anomalyType => {
        const series: ChartData = {
          name: anomalyType === 'increase' ? '增加异常' : '减少异常',
          type: 'bar',
          emphasis: {
            focus: 'series'
          },
          data: []
        };
        
        regions.forEach(region => {
          let count = 0;
          const anomalies = regionData[region].anomalies;
          if (anomalies && typeof anomalies === 'object') {
            Object.values(anomalies).forEach(anomalyList => {
              if (Array.isArray(anomalyList)) {
                anomalyList.forEach(anomaly => {
                  if (anomaly && anomaly.type === anomalyType) {
                    count++;
                  }
                });
              }
            });
          }
          series.data.push(count);
        });
        
        seriesData.push(series);
      });
      
      const option: ChartOption = {
        title: {
          text: '区域土地覆盖异常对比',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: legendData.map(type => type === 'increase' ? '增加异常' : '减少异常'),
          bottom: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData
        },
        yAxis: {
          type: 'value',
          name: '异常次数'
        },
        series: seriesData
      };
      
      changesChart.setOption(option);
    }

    // 支持窗口自适应
    window.addEventListener('resize', () => {
      changesChart && changesChart.resize();
    });
  } catch (error) {
    console.error('渲染对比分析图表失败:', error);
    ElMessage.error('渲染对比分析图表失败: ' + (error instanceof Error ? error.message : '未知错误'));
  }
}

// 添加对指标变化的监听
watch(() => comparisonMetric.value, (newMetric) => {
  console.log('Dialog: 指标变化:', newMetric);
  if (props.analysisMode === 'comparison') {
    // 触发指标变化事件，让父组件处理数据更新
    emit('update:comparisonMetric', newMetric);
  }
});

watch(() => props.data, (newData) => {
  console.log('分析数据变化:', newData);
  if (newData) {
    nextTick(() => {
      if (props.analysisMode === 'timeseries') {
        renderTimeseriesChart();
      } else if (props.analysisMode === 'comparison') {
        renderComparisonChart();
      } else if (props.analysisMode === 'matrix') {
        renderMatrixChart();
      }
    });
  }
}, { deep: true, immediate: true });

onUnmounted(() => {
  if (timeseriesChart) {
    timeseriesChart.dispose();
    timeseriesChart = null;
  }
  if (changesChart) {
    changesChart.dispose();
    changesChart = null;
  }
  if (matrixChart) {
    matrixChart.dispose();
    matrixChart = null;
  }
  // 移除窗口大小变化监听
  window.removeEventListener('resize', () => {
    changesChart && changesChart.resize();
  });
});

// 主要转换与统计
const majorTransitions = computed(() => props.data?.data?.transition_stats?.major_transitions || []);
const stabilityRatio = computed(() => props.data?.data?.transition_stats?.stability_ratio ?? '-');
const totalTransitions = computed(() => props.data?.data?.transition_stats?.total_transitions ?? '-');
</script>

<style scoped>
.land-analysis-dialog :deep(.el-dialog__body) {
  padding: 10px 20px;
  height: calc(90vh - 120px);
  overflow: hidden;
}

.analysis-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 0;
}

#timeseries-chart,
#comparison-chart,
#matrix-chart {
  width: 100%;
  height: 100%;
  min-height: 0;
}

.year-selector {
  position: absolute;
  top: 10px;
  right: 20px;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 8px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.year-separator {
  color: #606266;
}

.year-selector .el-select {
  width: 100px;
}

.metric-selector {
  position: absolute;
  top: 10px;
  right: 20px;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 8px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.metric-selector .el-select {
  width: 100px;
}

.transition-summary {
  margin-top: 16px;
  background: #f7f7fa;
  padding: 12px 18px;
  border-radius: 6px;
  font-size: 15px;
}

.transition-summary h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #409eff;
}

.transition-summary ul {
  margin: 0 0 8px 0;
  padding-left: 18px;
}

.transition-summary li {
  margin-bottom: 2px;
}

.transition-stats {
  color: #666;
  font-size: 13px;
  margin-top: 6px;
}
</style>

<template>
  <div class="content">
    <!-- 主要内容区 -->
    <main class="main">
      <div class="map-area">
        <div class="toolbar">
          <el-button-group>
            <el-button @click="showToolbar('timeseries')" :disabled="analysisMode !== null" size="small"
              type="primary">时序分析</el-button>
            <el-button @click="showToolbar('comparison')" :disabled="analysisMode !== null" size="small"
              type="primary">对比分析</el-button>
            <el-button @click="showToolbar('matrix')" :disabled="analysisMode !== null" size="small"
              type="primary">土地类型转换矩阵</el-button>
          </el-button-group>
          <el-button-group class="toolbar-export">
            <el-button @click="exportSelectedRegions" :disabled="!hasAnyRegion" size="small" type="success">
              导出选区
            </el-button>
            <el-button @click="exportAnalysisResult" :disabled="!hasAnalysisResult" size="small" type="warning">
              导出结果
            </el-button>
          </el-button-group>
        </div>

        <!-- 对比分析工具条 -->
        <div v-if="analysisMode === 'comparison'" class="comparison-toolbar">
          <el-button-group>
            <el-button 
              @click="startDrawingRegion1" 
              :disabled="!!drawnRegions.region1" 
              size="small" 
              type="primary"
            >
              绘制区域1
            </el-button>
            <el-button 
              @click="startDrawingRegion2" 
              :disabled="!drawnRegions.region1 || !!drawnRegions.region2" 
              size="small" 
              type="primary"
            >
              绘制区域2
            </el-button>
            <el-button @click="clearAll" size="small" type="danger">
              清除所有
            </el-button>
          </el-button-group>
        </div>

        <!-- 绘制状态提示 -->
        <div v-if="drawingPrompt" class="drawing-prompt">
          <el-alert :title="drawingPrompt" type="info" :closable="false" />
        </div>

        <div class="analysis-status-panel">
          <div class="status-header">
            <span>GIS分析状态</span>
            <el-tag size="small" :type="analysisMode ? 'success' : 'info'">
              {{ activeModeLabel }}
            </el-tag>
          </div>
          <div class="status-row">
            <span>当前年份</span>
            <strong>{{ selectedYear }}年</strong>
          </div>
          <div class="status-row">
            <span>区域1</span>
            <strong>{{ drawnRegions.region1 ? '已绘制' : '未绘制' }}</strong>
          </div>
          <div class="status-row">
            <span>区域2</span>
            <strong>{{ drawnRegions.region2 ? '已绘制' : '未绘制' }}</strong>
          </div>
          <div class="status-row" v-if="analysisMode === 'comparison'">
            <span>对比指标</span>
            <strong>{{ comparisonMetricLabel }}</strong>
          </div>
          <div class="status-row">
            <span>结果状态</span>
            <strong>{{ hasAnalysisResult ? '可导出' : '待生成' }}</strong>
          </div>
        </div>

        <!-- 悬浮的年份选择区域 -->
        <div class="year-selector-float">
          <label>选择年份：</label>
          <el-select v-model="selectedYear" class="year-select">
            <el-option v-for="year in years" :key="year" :label="`${year}年`" :value="year" />
          </el-select>
        </div>
        
        <div class="table-area-float">
          <div class="table-header">
            <span>土地利用类型统计</span>
            <el-tag size="small" type="info">{{ selectedYear }}年</el-tag>
          </div>
          <div ref="scrollWrapper" class="table-content">
            <el-table :data="tableData" style="width: 100%;" size="small" stripe
              :default-sort="{ prop: 'area', order: 'descending' }"
              :header-cell-style="{ background: '#f5f7fa', color: '#606266' }">
              <el-table-column prop="type" label="土地类型" />
              <el-table-column prop="area" label="占地面积(km²)" sortable
                :sort-method="(a, b) => Number(b.area) - Number(a.area)" />
              <el-table-column prop="percent" label="百分比(%)" />
            </el-table>
          </div>
        </div>

        
        <div class="map">
          <Basemap
            :layersConfig="mapLayerConfig"
            :center="[118.75, 28.25]"
            :zoom="7"
            :legend-title="`土地覆盖图例 · ${selectedYear}年`"
            ref="basemapRef"
            @view-ready="onViewReady"
          >
            <template #legend>
              <div class="legend-slot">
                <img
                  :src="legendUrl"
                  alt="土地覆盖图例"
                  class="legend-image"
                  @error="onLegendError"
                />
              </div>
            </template>
          </Basemap>
        </div>
      </div>
    </main>

    <!-- 添加分析弹窗组件 -->
    <LandAnalysisDialog
      v-model="analysisDialogVisible"
      :data="analysisData"
      :analysis-mode="analysisMode"
      v-model:comparisonMetric="comparisonMetric"
      @close="onAnalysisDialogClose"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import Basemap from "@/components/baseMap.vue";
import * as echarts from 'echarts';
import LandAnalysisDialog from '@/components/LandAnalysisDialog.vue';
import api from '@/utils/request';
import axios from 'axios';
import Draw from 'ol/interaction/Draw';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import { Fill, Stroke, Style } from 'ol/style';
import type Map from 'ol/Map';
import type Feature from 'ol/Feature';
// 响应式数据
const years = ref<number[]>([]);
const selectedYear = ref<number>(2022);
const csvRaw = ref<string[]>([]);
const tableData = ref<any[]>([]);
const scrollWrapper = ref<HTMLElement | null>(null);
const basemapRef = ref<any>(null);

// 绘制相关状态
const drawingMode = ref<string | null>(null);
const analysisMode = ref<'timeseries' | 'comparison' | 'matrix' | null>(null);
const drawnRegions = ref<{region1: any, region2: any}>({region1: null, region2: null});
const drawingPrompt = ref<string>('');

// 分析数据状态
const analysisData = ref<any>({
  data: null
});
const regionAnalysisData = ref<any>(null);
const regionStatsData = ref<any[]>([]);
const comparisonData = ref<any>(null);

// 弹窗显示状态
const analysisDialogVisible = ref(false);
const regionAnalysisDialogVisible = ref(false);
const showComparisonDialog = ref(false);

// 地图相关
let mapInstance: Map | null = null;
let drawInteraction: Draw | null = null;
const drawSource = new VectorSource();
const drawLayer = new VectorLayer({
  source: drawSource,
  style: new Style({
    fill: new Fill({ color: 'rgba(64, 158, 255, 0.25)' }),
    stroke: new Stroke({ color: '#409EFF', width: 2 })
  }),
  zIndex: 100
});
const geojsonWriter = new GeoJSON();

// 添加新的响应式数据
// 新增：对比分析指标
const comparisonMetric = ref('area'); // 默认面积
const loading = ref(false);
const legendVariantIndex = ref(0);
const modeLabelMap: Record<'timeseries' | 'comparison' | 'matrix', string> = {
  timeseries: '时序分析',
  comparison: '对比分析',
  matrix: '转换矩阵'
};
const metricLabelMap: Record<string, string> = {
  area: '面积',
  change: '变化',
  anomaly: '异常'
};

// 监听弹窗内指标切换（来自 LandAnalysisDialog 子组件）
function onComparisonMetricChange(newMetric: string) {
  console.log('指标切换:', { oldMetric: comparisonMetric.value, newMetric });
  
  // 更新指标值
  comparisonMetric.value = newMetric;
  
  // 如果已绘制两个区域且弹窗已显示，则重新请求数据
  if (
    analysisMode.value === 'comparison' &&
    drawnRegions.value.region1 &&
    drawnRegions.value.region2 &&
    analysisDialogVisible.value
  ) {
    console.log('发送新的对比分析请求');
    handleComparisonAnalysis();
  }
}

// 添加对 comparisonMetric 的监听
watch(() => comparisonMetric.value, (newMetric) => {
  console.log('父组件: 指标变化:', newMetric);
  onComparisonMetricChange(newMetric);
});

// 计算属性
const mapLayerConfig = computed(() => {
  return [{
    type: 'WMSLayer',
    url: '/geoserver/predata/wms',
    subLayers: [
      {
        title: `predata:LC_${selectedYear.value}`,
        visible: true
      }
    ]
  }];
});

const legendCandidates = computed(() => {
  const layerCandidates = [`predata:LC_${selectedYear.value}`];
  const styleCandidates = ['', 'LC_style', 'lc_style', 'landcoverage_style'];
  const serviceCandidates = ['/geoserver/wms', '/geoserver/predata/wms'];
  const urls: string[] = [];

  serviceCandidates.forEach((service) => {
    layerCandidates.forEach((layer) => {
      styleCandidates.forEach((style) => {
        const params = new URLSearchParams({
          REQUEST: 'GetLegendGraphic',
          VERSION: '1.0.0',
          FORMAT: 'image/png',
          LAYER: layer
        });
        if (style) {
          params.set('STYLE', style);
        }
        urls.push(`${service}?${params.toString()}`);
      });
    });
  });

  return urls;
});

const legendUrl = computed(() => {
  if (!legendCandidates.value.length) return '';
  return legendCandidates.value[Math.min(legendVariantIndex.value, legendCandidates.value.length - 1)];
});

const activeModeLabel = computed(() => {
  if (!analysisMode.value) return '待选择模式';
  return modeLabelMap[analysisMode.value];
});

const comparisonMetricLabel = computed(() => metricLabelMap[comparisonMetric.value] ?? comparisonMetric.value);
const hasAnyRegion = computed(() => !!drawnRegions.value.region1 || !!drawnRegions.value.region2);
const hasAnalysisResult = computed(() => !!analysisData.value?.data);

function onLegendError() {
  if (legendVariantIndex.value < legendCandidates.value.length - 1) {
    legendVariantIndex.value += 1;
  }
}

function downloadTextFile(filename: string, content: string, mimeType = 'application/json;charset=utf-8') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function exportSelectedRegions() {
  if (!hasAnyRegion.value) {
    ElMessage.warning('当前没有可导出的选区');
    return;
  }

  const featureCollection = {
    type: 'FeatureCollection',
    features: [
      drawnRegions.value.region1
        ? {
            type: 'Feature',
            properties: { name: '区域1', mode: analysisMode.value ?? 'none' },
            geometry: normalizeRegionGeometry(drawnRegions.value.region1)
          }
        : null,
      drawnRegions.value.region2
        ? {
            type: 'Feature',
            properties: { name: '区域2', mode: analysisMode.value ?? 'none' },
            geometry: normalizeRegionGeometry(drawnRegions.value.region2)
          }
        : null
    ].filter(Boolean)
  };

  downloadTextFile(`landcoverage_regions_${selectedYear.value}.geojson`, JSON.stringify(featureCollection, null, 2), 'application/geo+json;charset=utf-8');
  ElMessage.success('选区已导出');
}

function exportAnalysisResult() {
  if (!hasAnalysisResult.value) {
    ElMessage.warning('当前没有可导出的分析结果');
    return;
  }

  const payload = {
    mode: analysisMode.value,
    year: selectedYear.value,
    metric: comparisonMetric.value,
    generated_at: new Date().toISOString(),
    data: analysisData.value.data
  };

  downloadTextFile(`landcoverage_analysis_${analysisMode.value ?? 'result'}_${selectedYear.value}.json`, JSON.stringify(payload, null, 2));
  ElMessage.success('分析结果已导出');
}

// 生成年份数组（2000-2022）
function generateYears(): number[] {
  const startYear = 2000;
  const endYear = 2022;
  const yearsArray = [];
  for (let year = endYear; year >= startYear; year--) {
    yearsArray.push(year);
  }
  return yearsArray;
}

// 更新表格数据
function updateTableData() {
  const year = selectedYear.value;
  if (!csvRaw.value || csvRaw.value.length === 0) return;

  const rows = csvRaw.value.filter(line => line.includes(`poyang_${year}`));
  tableData.value = rows
    .map(line => {
      const parts = line.split(',');
      if (parts.length < 6) return null;
      return {
        type: parts[2],
        area: Number(parts[4]).toFixed(2),
        percent: parts[5].replace('%', '')
      };
    })
    .filter(row => row && row.type && row.type !== '0');
}

// 监听地图视图就绪
function onViewReady(map: Map) {
  console.log('地图视图已就绪');
  mapInstance = map;
  if (mapInstance && !mapInstance.getLayers().getArray().includes(drawLayer)) {
    mapInstance.addLayer(drawLayer);
  }
}

function cleanupDrawInteraction() {
  if (drawInteraction && mapInstance) {
    mapInstance.removeInteraction(drawInteraction);
  }
  drawInteraction = null;
}

// 将 OpenLayers 几何转换为 GeoJSON
function convertFeatureToGeoJSON(feature: Feature) {
  if (!feature) return null;
  return geojsonWriter.writeFeatureObject(feature, {
    dataProjection: 'EPSG:4326',
    featureProjection: 'EPSG:3857'
  });
}

function normalizeRegionGeometry(region: any) {
  if (!region) return null;
  if (region.type === 'Feature' && region.geometry) return region.geometry;
  if (region.type === 'FeatureCollection' && Array.isArray(region.features) && region.features[0]?.geometry) {
    return region.features[0].geometry;
  }
  return region;
}

function startPolygonDraw(onComplete: (geojson: any) => Promise<void> | void, options: { clear?: boolean } = { clear: true }) {
  if (!mapInstance) {
    ElMessage.warning('地图正在加载中，请稍候...');
    return;
  }

  if (options.clear ?? true) {
    drawSource.clear();
  }

  cleanupDrawInteraction();
  drawInteraction = new Draw({
    source: drawSource,
    type: 'Polygon'
  });

  drawInteraction.on('drawend', async (event) => {
    const geojson = convertFeatureToGeoJSON(event.feature);
    if (geojson) {
      await onComplete(geojson);
    }
    cleanupDrawInteraction();
  }, { once: true });

  mapInstance.addInteraction(drawInteraction);
}

// 修改工具栏显示逻辑
function showToolbar(mode: 'timeseries' | 'comparison' | 'matrix') {
  console.log('显示工具栏，模式:', mode);
  analysisMode.value = mode;
  analysisData.value = { data: null };
  drawnRegions.value = {region1: null, region2: null};
  if (mode === 'timeseries' || mode === 'matrix') {
    nextTick(() => {
      startDrawing();
    });
  }
}

// 开始绘制
function startDrawing() {
  drawingMode.value = 'hybrid';
  drawingPrompt.value = '请绘制分析区域';

  startPolygonDraw(async (geojson) => {
    drawnRegions.value.region1 = geojson;
    drawingPrompt.value = '';
    ElMessage.success('区域绘制完成，开始分析');

    if (analysisMode.value === 'timeseries') {
      await handleTimeseriesAnalysis();
    } else if (analysisMode.value === 'matrix') {
      await handleTransitionAnalysis();
    }

    drawingMode.value = null;
  });

  return;
}

// 监听年份变化
watch(selectedYear, async (newYear) => {
  legendVariantIndex.value = 0;
  updateTableData();
  
  // 如果当前有分析模式且已绘制区域，重新获取数据
  if (analysisMode.value && drawnRegions.value.region1) {
    try {
      if (analysisMode.value === 'timeseries') {
        await handleTimeseriesAnalysis();
      } else if (analysisMode.value === 'matrix') {
        await handleTransitionAnalysis();
      }
    } catch (error) {
      console.error('年份切换后更新数据失败:', error);
      ElMessage.error('更新数据失败');
    }
  }
});

// 修改 handleTimeseriesAnalysis 函数
async function handleTimeseriesAnalysis() {
  try {
    const fromYear = 2000;
    const toYear = 2022;
    const region = drawnRegions.value.region1;
    
    if (!region) {
      console.error('区域数据不存在');
      ElMessage.error('区域数据不存在，请重新绘制区域');
      return;
    }

    console.log('开始时序分析，区域数据:', region);

    // 1. 先清理现有状态
    drawSource.clear();
    cleanupDrawInteraction();

    // 2. 获取数据
    const regionGeometry = normalizeRegionGeometry(region);
    const response = await api.get(`/api/timeseries`, {
      params: {
        years: `${fromYear}-${toYear}`,
        region: JSON.stringify(regionGeometry)
      }
    });

    console.log('时序分析API返回数据:', response);

    if (response && typeof response.status === 'string' && response.status === 'success') {
      // 设置分析模式
      analysisMode.value = 'timeseries';
      // 设置分析数据
      analysisData.value = response;
      // 显示对话框
      analysisDialogVisible.value = true;
      
      console.log('设置时序分析数据:', {
        analysisData: analysisData.value,
        analysisMode: analysisMode.value,
        dialogVisible: analysisDialogVisible.value
      });
    } else {
      ElMessage.error('获取分析数据失败: ' + (response?.message || '未知错误'));
      analysisMode.value = null;
      analysisDialogVisible.value = false;
    }
  } catch (error) {
    console.error('Error fetching timeseries data:', error);
    ElMessage.error('获取分析数据失败: ' + (error instanceof Error ? error.message : '未知错误'));
    analysisMode.value = null;
    analysisDialogVisible.value = false;
  }
}

// 修改 handleTransitionAnalysis 函数
async function handleTransitionAnalysis() {
  try {
    const { region1 } = drawnRegions.value;
    if (!region1) {
      ElMessage.warning('请先绘制区域');
      return;
    }
    const fromYear = 2000;
    const toYear = 2022;
    
    const regionGeometry = normalizeRegionGeometry(region1);
    const response = await api.get('/api/transition', {
      params: {
        from_year: fromYear,
        to_year: toYear,
        region: JSON.stringify(regionGeometry)
      }
    });

    console.log('转换矩阵API返回数据:', response);

    if (response && typeof response.status === 'string' && response.status === 'success') {
      // 设置分析模式
      analysisMode.value = 'matrix';
      // 设置分析数据，包含region信息
      analysisData.value = {
        data: {
          sankey_data: response.data.sankey_data,
          transition_stats: response.data.transition_stats,
          status: response.status,
          region: regionGeometry  // 添加region数据（仅几何）
        }
      };
      // 显示对话框
      await nextTick();
      analysisDialogVisible.value = true;

      // 清除绘制状态
      drawingMode.value = null;
      drawingPrompt.value = '';

      // 清除图形
      drawSource.clear();
      cleanupDrawInteraction();
    } else {
      ElMessage.error('获取转换矩阵数据失败');
      analysisMode.value = null;
      analysisDialogVisible.value = false;
    }
  } catch (error) {
    console.error('Error fetching transition data:', error);
    ElMessage.error('获取转换矩阵数据失败');
    analysisMode.value = null;
    analysisDialogVisible.value = false;
  }
}

// 清除所有图形
function clearGraphics() {
  drawSource.clear();
  cleanupDrawInteraction();
  drawnRegions.value = {region1: null, region2: null};
  drawingMode.value = null;
  analysisMode.value = null;
  drawingPrompt.value = '';
}

// 清除所有按钮点击事件
function clearAll() {
  clearGraphics();
  ElMessage.success('已清除所有绘制内容');
}

// 弹窗关闭处理函数
function onRegionAnalysisDialogClose() {
  regionAnalysisDialogVisible.value = false;
  regionAnalysisData.value = null;
  regionStatsData.value = [];
  clearGraphics();
}

function onComparisonDialogClose() {
  showComparisonDialog.value = false;
  comparisonData.value = null;
  clearGraphics();
}

function onAnalysisDialogClose() {
  analysisDialogVisible.value = false;
  analysisData.value = null;
  analysisMode.value = null; // 关闭弹窗时恢复功能条可用
  clearGraphics(); // 关闭弹窗时清除绘制图形
}

// 添加绘制区域1的函数
function startDrawingRegion1() {
  drawingMode.value = 'region1';
  drawingPrompt.value = '请绘制区域1';
  startPolygonDraw(async (geojson) => {
    drawnRegions.value.region1 = geojson;
    ElMessage.success('区域1绘制完成');
    drawingMode.value = null;
    drawingPrompt.value = '';
  });
}

function startDrawingRegion2() {
  drawingMode.value = 'region2';
  drawingPrompt.value = '请绘制区域2';
  startPolygonDraw(async (geojson) => {
    drawnRegions.value.region2 = geojson;
    drawingPrompt.value = '';
    ElMessage.success('区域2绘制完成，开始分析');
    await handleComparisonAnalysis();
    drawingMode.value = null;
  }, { clear: false });
}

// 处理对比分析
async function handleComparisonAnalysis() {
  try {
    const { region1, region2 } = drawnRegions.value;
    if (!region1 || !region2) {
      ElMessage.warning('请先绘制两个区域');
      return;
    }
    loading.value = true;

    // 构造请求数据
    const region1Geometry = normalizeRegionGeometry(region1);
    const region2Geometry = normalizeRegionGeometry(region2);
    const regions = [
      { name: '区域1', geometry: region1Geometry },
      { name: '区域2', geometry: region2Geometry }
    ];

    // metric 参数修正为字符串
    const metric = typeof comparisonMetric === 'string' ? comparisonMetric : comparisonMetric.value;
    const response = await api.get('/api/compare', {
      params: {
        regions: JSON.stringify(regions),
        metric
      }
    });

    console.log('API响应:', response);

    // 检查响应结构
    if (!response?.data) {
      throw new Error('API响应为空');
    }

    // 检查响应状态
    if (response && typeof response.status === 'string' && response.status === 'success') {
      // 构造正确的数据结构
      const comparisonData = {
        data: {
          regions: {
            '区域1': {
              raw_data: response.data.regions['区域1'].raw_data || {},
              relative_changes: response.data.regions['区域1'].relative_changes || {},
              anomalies: response.data.regions['区域1'].anomalies || {},
              geometry: region1
            },
            '区域2': {
              raw_data: response.data.regions['区域2'].raw_data || {},
              relative_changes: response.data.regions['区域2'].relative_changes || {},
              anomalies: response.data.regions['区域2'].anomalies || {},
              geometry: region2
            }
          },
          metric: comparisonMetric.value,
          comparison_stats: response.data.comparison_stats || {
            area_comparison: {},
            land_types: [],
            total_regions: 0,
            year_range: [2000, 2022]
          }
        }
      };
      
      // 添加调试日志
      console.log('API响应数据:', response.data);
      console.log('构造的分析数据:', comparisonData);
      
      // 验证数据结构
      const regions = Object.keys(comparisonData.data.regions);
      regions.forEach(region => {
        console.log(`${region} 数据:`, {
          hasRawData: !!comparisonData.data.regions[region].raw_data,
          rawDataContent: comparisonData.data.regions[region].raw_data,
          hasRelativeChanges: !!comparisonData.data.regions[region].relative_changes,
          hasAnomalies: !!comparisonData.data.regions[region].anomalies,
          hasGeometry: !!comparisonData.data.regions[region].geometry
        });
      });
      
      analysisData.value = comparisonData;
      analysisMode.value = 'comparison';
      analysisDialogVisible.value = true;
      drawingMode.value = null;
      drawingPrompt.value = '';
      drawSource.clear();
      cleanupDrawInteraction();
    } else {
      // 处理API返回的错误
      const errorMessage = response.message || '获取对比分析数据失败';
      const errorDetails = response.metadata?.error || '未知错误';
      console.error('API返回错误:', {
        status: response.status,
        message: errorMessage,
        details: errorDetails
      });
      throw new Error(`${errorMessage} - ${errorDetails}`);
    }
  } catch (error) {
    console.error('对比分析失败:', error);
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试');
    } else if (error.response) {
      ElMessage.error(`服务器错误: ${error.response.status} - ${error.response.data?.message || '未知错误'}`);
    } else if (error.request) {
      ElMessage.error('网络请求失败，请检查网络连接');
    } else {
      ElMessage.error(error.message || '获取对比分析数据失败');
    }
    analysisDialogVisible.value = false;
  } finally {
    loading.value = false;
  }
}

// 组件挂载
onMounted(async () => {
  try {
    // 读取指数统计数据
    const res = await axios.get('src/assets/landcoverage.csv');
    if (res.status !== 200) {
      throw new Error('Failed to load CSV file');
    }
    const text = res.data;
    csvRaw.value = text.trim().split('\n').slice(1);

    // 设置年份数组
    years.value = generateYears();
    selectedYear.value = years.value[0];
    updateTableData();
  } catch (error) {
    console.error('Error loading CSV data:', error);
  }
});

// 组件卸载时清理资源
onBeforeUnmount(() => {
  // 清理所有图表实例
  [
    'timeseriesChart',
    'changesChart', 
    'sankeyChart',
    'regionChart',
    'comparisonChart'
  ].forEach(chartName => {
    if (window[chartName as keyof Window]) {
      (window[chartName as keyof Window] as echarts.ECharts).dispose();
      (window as any)[chartName] = null;
    }
  });
  
  // 清理绘图状态
  cleanupDrawInteraction();
  drawSource.clear();
});
</script>
<style lang="less" scoped>
.content {
  height: calc(100vh - 60px);
  width: calc(100vw - 250px);
  display: flex;
  flex-direction: column;
  background: #f5f6fa;
  padding: 0 0 30px 0;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  padding: 0 16px;
}

.map-area {
  width: 100%;
  height: calc(100vh - 60px);
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 12px;
  overflow: hidden;
}

.map {
  height: 100%;
  width: 100%;
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

// 工具栏样式
.toolbar {
  position: absolute;
  left: 65px;
  top: 24px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-export {
  margin-left: 4px;
}

// 年份选择器样式
.year-selector-float {
  position: absolute;
  right: 400px;
  top: 24px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  gap: 8px;
  width: 220px;
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }
}

.year-select {
  width: 100px;
}

.analysis-status-panel {
  position: absolute;
  left: 65px;
  top: 88px;
  z-index: 10;
  width: 220px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px 14px;
  border-radius: 10px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(8px);
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1f2d3d;
}

.status-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: #475569;
  margin-top: 6px;
}

.status-row strong {
  color: #0f172a;
  font-weight: 600;
}

.legend-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 180px;
}

.legend-image {
  display: block;
  max-width: 180px;
  max-height: 260px;
  border-radius: 6px;
}

// 表格区域样式
.table-area-float {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 380px;
  height: 96%;
  background: rgba(255, 255, 255, 0.567);
  border-radius: 0 12px 12px 0;
  z-index: 10;
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;

  &:hover {
    transform: translateX(-5px);
  }

  .table-header {
    padding: 16px 20px;
    font-size: 10px;
    font-weight: 300;
    color: #333;
    background: #f8f9fa;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }

  .table-content {
    flex: 1;
    overflow-y: auto;
  }
}

// 表格样式覆盖
:deep(.el-table) {
  height: 100%;
  background: transparent !important;

  &::before {
    display: none;
  }

  .el-table__header-wrapper {
    th {
      background: #f5f7fa !important;
      font-weight: 500;
      color: #606266;
      padding: 12px !important;
    }
  }

  .el-table__body-wrapper {
    overflow-y: auto;

    td {
      padding: 12px !important;
    }

    tr:hover>td {
      background: rgba(64, 158, 255, 0.1) !important;
    }
  }
}

// Sketch微件样式
:deep(.esri-sketch) {
  background: white !important;
  border-radius: 4px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
  z-index: 1000 !important;
}

:deep(.esri-ui-bottom-left) {
  bottom: 40px !important;
}

:deep(.esri-sketch__section) {
  padding: 8px !important;
  border-bottom: 1px solid #e1e5e9;
  margin-bottom: 4px;

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
}

:deep(.esri-sketch__button) {
  margin: 1px !important;
  border-radius: 3px !important;
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background-color: #f0f0f0 !important;
  }

  &.esri-sketch__button--active {
    background-color: #0079c1 !important;
    color: white !important;
  }
}

:deep(.esri-sketch__tooltip) {
  background: rgba(0, 0, 0, 0.8) !important;
  color: white !important;
  border-radius: 4px !important;
  padding: 4px 8px !important;
  font-size: 12px !important;
}
:deep(.region-analysis-dialog .el-dialog__body) {
  padding: 0 10px 10px 10px;
  background: #f8f9fa;
}

// 动画效果
@keyframes slideInFromRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.custom-sketch-widget {
  animation: slideInFromRight 0.3s ease-out;
}

.analysis-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.comparison-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.comparison-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

  h3 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 18px;
  }
}

:deep(.comparison-dialog .el-dialog__body) {
  padding: 0;
  background: #f8f9fa;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.analysis-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comparison-container,
.transition-matrix-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
}

// 对比分析工具条样式
.comparison-toolbar {
  position: absolute;
  left: 65px;
  top: 80px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  animation: slideInFromTop 0.3s ease-out;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-panel {
  position: absolute;
  left: 20px;
  bottom: 20px;
  z-index: 110;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);

  .legend-title {
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
  }

  .legend-image {
    max-width: 130px;
    display: block;
  }
}

.metric-selector {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

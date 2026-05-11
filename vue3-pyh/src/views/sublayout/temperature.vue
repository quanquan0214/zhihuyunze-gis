<template>
  <div class="content">
    <div class="gis-summary-row">
      <div class="gis-summary-card">
        <span class="label">当前模式</span>
        <strong>{{ activeModeLabel }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">空间类型</span>
        <strong>{{ spatialTypeLabel }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">当前年份</span>
        <strong>{{ selectedYear }}年</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">结果状态</span>
        <strong>{{ resultStatusLabel }}</strong>
      </div>
    </div>
    <!-- 主要内容区 -->
    <main class="main">
      <div class="map-area">
        <!-- 添加年度数据图表 -->
        <div class="yearly-chart-container">
          <div ref="yearlyChartRef" class="yearly-chart"></div>
        </div>

        <div class="slider-panel">
          <el-radio-group v-model="category" size="small">
            <el-radio-button label="wendu">温度</el-radio-button>
            <el-radio-button label="rainfull">降水</el-radio-button>
          </el-radio-group>
          <div class="year-input">
            <el-input-number 
              v-model="selectedYear" 
              :min="startYear" 
              :max="endYearMap[category]" 
              size="small"
              @change="handleYearChange"
            />
            <span class="year-label">年</span>
          </div>
          <div style="flex: 1;">
            <el-slider 
              v-model="selectedMonth" 
              :min="1" 
              :max="12" 
              :marks="monthMarks" 
              :step="1" 
              show-tooltip
              :format-tooltip="formatMonthTooltip" 
              style="width: 100%;" 
            />
          </div>
          <div class="current-date">
            {{ selectedYear }}年
            <span class="month">{{ selectedMonth.toString().padStart(2, '0') }}</span>月
          </div>
        </div>

        <!-- 添加工具栏 -->
        <div class="toolbar">
          <el-button-group>
            <el-button
              @click="activateFeature('draw')"
              :disabled="!!activeFeature && activeFeature !== 'draw'"
              size="small"
              type="primary"
            >绘制区域分析</el-button>
            <el-button
              @click="clearAll"
              :disabled="!!activeFeature && activeFeature !== 'draw' && !polygon"
              size="small"
              type="danger"
            >清除区域</el-button>
          </el-button-group>
          <el-button
            type="success"
            @click="activateFeature('city')"
            :disabled="!!activeFeature && activeFeature !== 'city'"
            size="small"
            style="margin-left: 10px;"
          >显示城市数据</el-button>
          <el-button
            type="warning"
            @click="activateFeature('point')"
            :disabled="!!activeFeature && activeFeature !== 'point'"
            size="small"
            style="margin-left: 10px;"
          >单点分析</el-button>
          <el-button
            type="success"
            @click="activateFeature('monthly')"
            :disabled="!!activeFeature && activeFeature !== 'monthly'"
            size="small"
            style="margin-left: 10px;"
          >月度分析</el-button>
        </div>

        <div class="toolbar toolbar-export">
          <el-button-group>
            <el-button size="small" type="success" :disabled="!hasSpatialGeojson" @click="exportSpatialGeojson">导出空间</el-button>
            <el-button size="small" type="warning" :disabled="!hasAnalysisResult" @click="exportAnalysisResult">导出结果</el-button>
          </el-button-group>
        </div>

        <div class="analysis-status-panel">
          <div class="status-header">
            <span>GIS分析状态</span>
            <el-tag size="small" :type="activeFeature ? 'success' : 'info'">{{ activeModeLabel }}</el-tag>
          </div>
          <div class="status-row">
            <span>空间类型</span>
            <strong>{{ spatialTypeLabel }}</strong>
          </div>
          <div class="status-row">
            <span>选中对象</span>
            <strong>{{ selectionLabel }}</strong>
          </div>
          <div class="status-row">
            <span>当前统计</span>
            <strong>{{ statsLabel }}</strong>
          </div>
          <div class="status-row">
            <span>结果摘要</span>
            <strong>{{ resultSummaryLabel }}</strong>
          </div>
        </div>

        <div class="legend-panel">
          <div class="legend-title">{{ legendTitle }}</div>
          <img :src="legendUrl" :alt="legendTitle" class="legend-image" @error="onLegendError" />
        </div>

        <div v-if="selectionLabel !== '--'" class="map-selection-chip">
          {{ selectionLabel }}
        </div>

        <div class="map" ref="mapDivRef">
          <BaseMap
            :layersConfig="mapLayerConfig"
            :center="[118.75, 28.25]"
            :zoom="7"
            :geojson="geojsonData"
            :legend-title="legendTitle"
            ref="basemapRef"
            @view-ready="onViewReady"
            @map-click="onMapClick"
          >
            <template #legend>
              <div class="legend-slot">
                <img :src="legendUrl" :alt="legendTitle" class="legend-image" @error="onLegendError" />
              </div>
            </template>
          </BaseMap>
        </div>
      </div>
    </main>

    <!-- 添加弹窗组件 -->
    <el-dialog v-model="dialogVisible" title="提示" width="300px" :close-on-click-modal="false" align-center>
      <span>没有数据</span>
      <template #footer>
        <el-button type="primary" @click="dialogVisible = false">确定</el-button>
      </template>
    </el-dialog>

    <!-- 城市GeoJSON数据弹窗 -->
    <el-dialog 
      v-model="cityGeoJsonDialogVisible" 
      title="数据显示" 
      width="500px" 
      :close-on-click-modal="true"
      :modal="false"
      :append-to-body="true"
      class="city-data-dialog"
      align-center
    >
      <div v-loading="!selectedCityGeoJson">
        <div class="dialog-header" style="margin-bottom: 20px;" v-if="selectedCityGeoJson?.features[0]?.properties?.city_code !== 'point'">
          <el-radio-group v-model="selectedStat" size="small">
            <el-radio-button v-for="option in statsOptions" :key="option.value" :label="option.value">
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
        <div ref="chartRef" style="width: 100%; height: 300px;"></div>
      </div>
    </el-dialog>

    <!-- 添加月度分析弹窗 -->
    <el-dialog 
      v-model="monthlyAnalysisDialogVisible" 
      title="月度分析" 
      width="80%" 
      :close-on-click-modal="false" 
      align-center
      class="monthly-analysis-dialog"
    >
      <div v-loading="isLoading">
        <AverageChart 
          :category="category" 
          :cachedData="dataCache[category]" 
          ref="averageChartRef"
        />
      </div>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, onMounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import BaseMap from '@/components/baseMap.vue';
import AverageChart from '@/components/AverageChart.vue';
import api from '@/utils/request';
import Draw from 'ol/interaction/Draw';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import { Fill, Stroke, Style } from 'ol/style';
import { toLonLat } from 'ol/proj';
import type Map from 'ol/Map';
import type Feature from 'ol/Feature';

const category = ref('wendu');
const averageValue = ref('-');
const dialogVisible = ref(false);
const globalAlertRef = ref(null);
const showChart = ref(false);
const geojsonData = ref<any>(null);
const selectedPoint = ref<[number, number] | null>(null);
const analysisPayload = ref<any>(null);
const selectedGeometryName = ref('');


// 添加年份和月份的选择
const selectedYear = ref(2000);
const selectedMonth = ref(1);

// 不同类型的结束时间
const endYearMap = {
  wendu: 2022,
  rainfull: 2022
};

const startYear = 2000;

// 添加数据缓存
const dataCache = ref({
  wendu: {},
  rainfull: {}
});

// 添加加载状态
const isLoading = ref(false);

// 月份标记
const monthMarks = computed(() => {
  const marksObj = {};
  for (let i = 1; i <= 12; i++) {
    marksObj[i] = {
      style: {
        color: '#409EFF',
        fontWeight: 'bold',
        fontSize: '14px'
      },
      label: `${i}月`
    };
  }
  return marksObj;
});

// 月份tooltip格式化
function formatMonthTooltip(val) {
  return `${val}月`;
  }

// 处理年份变化
async function handleYearChange() {
  await fetchAverageValue();
  if (yearlyChart) {
    await updateYearlyChartData();
  }
  // 预加载数据
  preloadData();
}

// 监听月份变化
watch(selectedMonth, () => {
  fetchAverageValue();
  if (yearlyChart) {
    updateYearlyChartData();
  }
});

// 监听年份变化
watch(selectedYear, () => {
  fetchAverageValue();
  if (yearlyChart) {
    updateYearlyChartData();
  }
});

// 监听类别变化
watch(category, async () => {
  clearAll();
  await fetchAverageValue();
  if (yearlyChart) {
    await updateYearlyChartData();
  }
  // 预加载数据
  preloadData();
});

// 修改获取平均值的方法
async function fetchAverageValue() {
  try {
    isLoading.value = true;
    const currentCategory = category.value;
    const currentYear = selectedYear.value;
    
    // 如果数据已缓存，直接使用缓存数据
    if (dataCache.value[currentCategory][currentYear]) {
      const monthIndex = selectedMonth.value - 1;
      if (monthIndex >= 0 && monthIndex < dataCache.value[currentCategory][currentYear].length) {
        averageValue.value = dataCache.value[currentCategory][currentYear][monthIndex].toFixed(2);
      }
      isLoading.value = false;
      return;
    }

    // 如果没有缓存，则获取数据
    const response = await Promise.race([
      api.get('/api/RT/avg', {
        params: {
          year: currentYear,
          data_type: currentDataType.value
        }
      }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('请求超时')), 5000)
      )
    ]);
    console.log('API response for average value:', response);
    if (Array.isArray(response.data)) {
      // 缓存数据
      dataCache.value[currentCategory][currentYear] = response.data;
      const monthIndex = selectedMonth.value - 1;
      if (monthIndex >= 0 && monthIndex < response.data.length) {
        averageValue.value = Number(response.data[monthIndex]).toFixed(2);
      }
    }
  } catch (error) {
    console.error('获取平均值失败:', error);
    averageValue.value = '-';
    ElMessage.error('获取数据失败，请重试');
  } finally {
    isLoading.value = false;
  }
}

// 添加预加载数据的函数
async function preloadData() {
  const currentCategory = category.value;
  const currentYear = selectedYear.value;
  
  // 预加载当前年份的前后两年数据
  const yearsToLoad = [currentYear - 1, currentYear, currentYear + 1].filter(year => 
    year >= startYear && year <= endYearMap[currentCategory]
  );
  
  const loadPromises = yearsToLoad.map(async year => {
    if (!dataCache.value[currentCategory][year]) {
      try {
        const response = await Promise.race([
          api.get('/api/RT/avg', {
            params: {
              year: year,
              data_type: currentDataType.value
            }
          }),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('请求超时')), 5000)
          )
        ]);
        
        if (Array.isArray(response.data)) {
          dataCache.value[currentCategory][year] = response.data;
        }
      } catch (error) {
        console.error(`预加载${year}年数据失败:`, error);
      }
    }
  });
  
  await Promise.all(loadPromises);
}

// 修改 subLayerTitle 计算属性
const subLayerTitle = computed(() => {
  const y = selectedYear.value;
  const m = selectedMonth.value.toString().padStart(2, '0');
  return `${y}${m}`;
});

const legendVariantIndex = ref(0);

// 修改 mapLayerConfig 计算属性
const mapLayerConfig = computed(() => {
  const layerName = category.value === 'wendu'
    ? `predata:temperture_${subLayerTitle.value}`
    : `predata:rainfall_${subLayerTitle.value}`;
  return [{
    type: 'WMSLayer',
    url: '/geoserver/predata/wms',
    subLayers: [
      {
        title: layerName,
        visible: true
      }
    ],
    timeInfo: {
      startTimeField: "start_time",
      endTimeField: "end_time",
      trackIdField: "track_id",
      timeExtent: [new Date(2000, 0, 1), new Date(2022, 11, 31)]
    }
  }];
});

const legendCandidates = computed(() => {
  const isTemp = category.value === 'wendu';
  const layerCandidates = isTemp
    ? [
        `predata:temperature_${subLayerTitle.value}`,
        `predata:temperture_${subLayerTitle.value}`
      ]
    : [`predata:rainfall_${subLayerTitle.value}`];
  const styleCandidates = isTemp
    ? ['temperature_style', 'temperture_style']
    : ['rainfall_style'];
  const serviceCandidates = ['/geoserver/wms', '/geoserver/predata/wms'];

  const urls: string[] = [];
  serviceCandidates.forEach((service) => {
    layerCandidates.forEach((layer) => {
      styleCandidates.forEach((style) => {
        const params = new URLSearchParams({
          REQUEST: 'GetLegendGraphic',
          VERSION: '1.0.0',
          FORMAT: 'image/png',
          LAYER: layer,
          STYLE: style
        });
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

function extractMonthlySeries(payload: any): number[] {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload.map((item) => Number(item)).filter((item) => !Number.isNaN(item));
  if (Array.isArray(payload.monthly_stats)) return payload.monthly_stats.map((item: any) => Number(item)).filter((item: number) => !Number.isNaN(item));
  if (Array.isArray(payload.monthly_values)) return payload.monthly_values.map((item: any) => Number(item)).filter((item: number) => !Number.isNaN(item));
  if (Array.isArray(payload.data)) return payload.data.map((item: any) => Number(item)).filter((item: number) => !Number.isNaN(item));
  return [];
}

function setSpatialGeojson(feature: any, properties: Record<string, any> = {}) {
  if (!feature) {
    geojsonData.value = null;
    return;
  }

  geojsonData.value = {
    type: 'FeatureCollection',
    features: [
      {
        ...feature,
        properties: {
          ...(feature.properties ?? {}),
          ...properties
        }
      }
    ]
  };
}

watch([category, selectedYear, selectedMonth], () => {
  legendVariantIndex.value = 0;
});

// 地图相关变量
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
const citySource = new VectorSource();
const cityLayer = new VectorLayer({
  source: citySource,
  visible: false,
  style: new Style({
    fill: new Fill({ color: 'rgba(0, 0, 255, 0.2)' }),
    stroke: new Stroke({ color: '#1890ff', width: 1 })
  }),
  zIndex: 90
});
const geojsonFormat = new GeoJSON();

function cleanupDrawInteraction() {
  if (drawInteraction && mapInstance) {
    mapInstance.removeInteraction(drawInteraction);
  }
  drawInteraction = null;
}

function convertFeatureToGeoJSON(feature: Feature) {
  if (!feature) return null;
  return geojsonFormat.writeFeatureObject(feature, {
    dataProjection: 'EPSG:4326',
    featureProjection: 'EPSG:3857'
  });
}

function startPolygonDraw(onComplete: (geojson: any, feature: Feature) => Promise<void> | void, options: { clear?: boolean } = { clear: true }) {
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
      await onComplete(geojson, event.feature);
    }
    cleanupDrawInteraction();
  }, { once: true });

  mapInstance.addInteraction(drawInteraction);
}

// 绘制相关变量
const drawingMode = ref(null);
const polygon = ref(null);
const polygonCoordinates = ref([]);

// 添加新的响应式变量
const cityGeoJsonDialogVisible = ref(false);
const selectedCityGeoJson = ref(null);
const selectedStat = ref('mean');
const selectedCityCode = ref(null);
const statsOptions = [
  { label: '平均值', value: 'mean' },
  { label: '中位数', value: 'median' },
  { label: '最大值', value: 'max' },
  { label: '最小值', value: 'min' }
];

// 添加图表相关的变量
const chartRef = ref(null);
let chart = null;

// 添加地图容器引用
const mapDivRef = ref(null);

// 添加年度图表相关变量
const yearlyChartRef = ref(null);
let yearlyChart = null;

// 添加月度分析相关变量
const monthlyAnalysisDialogVisible = ref(false);
const monthlyChartRef = ref(null);
let monthlyChart = null;

// 添加单点分析相关变量
const isPointAnalysisActive = ref(false);

// 新增：当前激活的功能
const activeFeature = ref('');
const featureLabelMap: Record<string, string> = {
  draw: '区域分析',
  city: '城市分析',
  point: '单点分析',
  monthly: '月度分析'
};
const statsLabelMap: Record<string, string> = {
  mean: '平均值',
  median: '中位数',
  max: '最大值',
  min: '最小值'
};

const currentDataType = computed(() => category.value === 'wendu' ? 'temperature' : 'rainfall');
const currentDataLabel = computed(() => category.value === 'wendu' ? '温度' : '降水');
const legendTitle = computed(() => `${currentDataLabel.value}图例 · ${selectedYear.value}年${selectedMonth.value.toString().padStart(2, '0')}月`);
const activeModeLabel = computed(() => activeFeature.value ? featureLabelMap[activeFeature.value] ?? activeFeature.value : '待选择模式');
const spatialTypeLabel = computed(() => {
  if (activeFeature.value === 'point') return selectedPoint.value ? '点位' : '待选点位';
  if (activeFeature.value === 'city') return selectedCityCode.value ? '城市' : '待选城市';
  if (activeFeature.value === 'draw') return polygon.value ? '区域' : '待绘区域';
  if (selectedPoint.value) return '点位';
  if (selectedCityCode.value) return '城市';
  if (polygon.value) return '区域';
  return '未激活';
});
const selectionLabel = computed(() => {
  if (activeFeature.value === 'point' && selectedPoint.value) {
    return `${selectedPoint.value[0].toFixed(4)}, ${selectedPoint.value[1].toFixed(4)}`;
  }
  if (activeFeature.value === 'city' && selectedGeometryName.value) return selectedGeometryName.value;
  if (activeFeature.value === 'draw' && selectedGeometryName.value) return selectedGeometryName.value;
  if (selectedGeometryName.value) return selectedGeometryName.value;
  if (selectedCityCode.value) return selectedCityCode.value;
  return '--';
});
const statsLabel = computed(() => statsLabelMap[selectedStat.value] ?? selectedStat.value);
const resultStatusLabel = computed(() => analysisPayload.value ? '已生成' : activeFeature.value ? '分析中' : '待生成');
const resultSummaryLabel = computed(() => {
  const payload = analysisPayload.value;
  if (!payload) return '待生成';
  const value = payload.yearly_stat ?? payload.yearly_value;
  if (typeof value === 'number') {
    return `${value.toFixed(2)} ${category.value === 'wendu' ? '°C' : 'mm'}`;
  }
  const series = extractMonthlySeries(payload);
  if (series.length) {
    return `${series.length}个月序列`;
  }
  return '已生成';
});
const hasSpatialGeojson = computed(() => !!geojsonData.value?.features?.length);
const hasAnalysisResult = computed(() => !!analysisPayload.value);

// 添加单点分析函数
async function startPointAnalysis() {
  activeFeature.value = 'point';
  isPointAnalysisActive.value = true;
  setMapCursor('crosshair');
  ElMessage.info('请点击地图上的位置进行单点分析');
}

// 修改地图点击事件处理
async function onMapClick(event) {
  console.log('onMapClick event:', event); // 添加调试日志

  // 处理单点分析
  if (isPointAnalysisActive.value) {
    isPointAnalysisActive.value = false;
    setMapCursor('default');

    if (!event.latitude || !event.longitude) {
      ElMessage.warning('请点击地图区域');
      return;
    }

    try {
      console.log('Sending request with params:', { // 添加调试日志
        lon: event.longitude,
        lat: event.latitude,
        year: selectedYear.value,
        data_type: currentDataType.value
      });

      const response = await api.get('/api/RT/coodinate', {
        params: {
          lon: event.longitude,
          lat: event.latitude,
          year: selectedYear.value,
          data_type: currentDataType.value
        }
      });

      console.log('API response:', response); // 添加调试日志
      const pointData = response.data ?? response;

      // 更新数据
      selectedPoint.value = [event.longitude, event.latitude];
      selectedGeometryName.value = `坐标点(${event.longitude.toFixed(4)}, ${event.latitude.toFixed(4)})`;
      analysisPayload.value = pointData;
      setSpatialGeojson({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [event.longitude, event.latitude]
        }
      }, {
        name: selectedGeometryName.value,
        spatial_type: 'point'
      });
      selectedCityGeoJson.value = {
        features: [{
          properties: {
            city_code: 'point',
            city_name: selectedGeometryName.value,
            data: pointData
          }
        }]
      };

      // 显示数据对话框
      cityGeoJsonDialogVisible.value = true;

      // 初始化图表
      nextTick(() => {
        if (!chart) {
          initChart();
        }
        updateChartData();
      });
    } catch (error) {
      console.error('获取单点数据失败:', error);
      ElMessage.error('获取单点数据失败，请重试');
    }
    return;
  }

  // 处理城市点击
  try {
    // 检查是否点击了城市区域
    if (event.attributes?.city_code) {
      console.log('City clicked:', event.attributes);
      // 设置选中的城市代码
      selectedCityCode.value = event.attributes.city_code;
      // 显示城市数据
      await showCityData();
      return;
    }

    // 只有在城市数据显示模式下才显示提示
    if (citySource.getFeatures().length > 0) {
      ElMessage.warning('请点击城市区域');
    }
  } catch (error) {
    console.error('获取数据失败:', error);
    ElMessage.error('获取数据失败，请重试');
  }
}

// 修改 setMapCursor 函数
function setMapCursor(cursor) {
  if (mapDivRef.value) {
    mapDivRef.value.style.cursor = cursor;
  }
}

// 监听单点分析状态
watch(isPointAnalysisActive, (active) => {
  if (!active) setMapCursor('default');
});

// 修改弹窗关闭监听
watch(cityGeoJsonDialogVisible, (newVal) => {
  if (!newVal) {
    // 销毁图表
    if (chart) {
      chart.dispose();
      chart = null;
    }
    // 清除选中的城市和区域数据标记
    selectedCityCode.value = null;
    isRegionData.value = false;
    isPointAnalysisActive.value = false;
    activeFeature.value = '';
    selectedPoint.value = null;
    analysisPayload.value = null;
    geojsonData.value = null;
    setMapCursor('default');
  }
});

// 开始绘制
async function startDrawing() {
  if (!mapInstance) {
    ElMessage.error('地图未初始化');
    return;
  }

  if (polygon.value) {
    ElMessage.warning('请先清除现有区域再绘制新区域');
    return;
  }

  drawingMode.value = true;
  activeFeature.value = 'draw';

  startPolygonDraw(async (_, feature) => {
    const coordinates = (feature.getGeometry()?.getCoordinates()?.[0] ?? []).map((coord: number[]) => toLonLat(coord));
    polygon.value = feature;
    polygonCoordinates.value = coordinates;
    drawingMode.value = null;
    isRegionData.value = true;
    await fetchRegionData();
  });
}

// 清除所有绘制
function clearAll() {
  drawSource.clear();
  cleanupDrawInteraction();
  polygon.value = null;
  polygonCoordinates.value = [];
  drawingMode.value = null;
  activeFeature.value = '';
  isRegionData.value = false;
  selectedPoint.value = null;
  selectedGeometryName.value = '';
  geojsonData.value = null;
  analysisPayload.value = null;
  selectedCityGeoJson.value = null;
  selectedCityCode.value = null;
  cityLayer.setVisible(false);
  isPointAnalysisActive.value = false;
  cityGeoJsonDialogVisible.value = false;
  monthlyAnalysisDialogVisible.value = false;
  setMapCursor('default');
}

// 获取区域数据
async function fetchRegionData() {
  if (!polygon.value) return;

  try {
    activeFeature.value = 'draw';
    const regionGeojson = convertFeatureToGeoJSON(polygon.value);
    const response = await api.post('/api/RT/geojson', {
      geojson: regionGeojson,
      year: selectedYear.value,
      data_type: currentDataType.value,
      stats: selectedStat.value
    });
    const regionData = response.data ?? response;
    analysisPayload.value = regionData;
    selectedGeometryName.value = '选中区域';
    setSpatialGeojson(regionGeojson, {
      name: selectedGeometryName.value,
      spatial_type: 'region'
    });

    // 更新数据
    selectedCityGeoJson.value = {
      features: [{
        properties: {
          city_code: 'region',
          city_name: selectedGeometryName.value,
          data: regionData
        }
      }]
    };

    // 显示数据对话框
    cityGeoJsonDialogVisible.value = true;

    // 初始化图表
    nextTick(() => {
      if (!chart) {
        initChart();
      }
      updateChartData();
    });
  } catch (error) {
    console.error('获取区域数据失败:', error);
    ElMessage.error('获取区域数据失败，请重试');
  }
}

// 加载城市区域图层
async function loadCityRegions() {
  if (!mapInstance) return;

  try {
    citySource.clear();
    const res = await fetch('/src/assets/cityRegion.geojson');
    const data = await res.json();
    console.log('Loaded GeoJSON data:', data);

    const features = geojsonFormat.readFeatures(data, {
      featureProjection: 'EPSG:3857',
      dataProjection: 'EPSG:4326'
    });

    features.forEach(feature => {
      const props = feature.getProperties();
      feature.set('properties', props);
      feature.setProperties(props);
      citySource.addFeature(feature);
    });

    cityLayer.setVisible(true);
    console.log('City layer added to map');
  } catch (error) {
    console.error('加载城市区域失败:', error);
    ElMessage.error('加载城市区域失败');
  }
}

// 修改 onViewReady 函数
function onViewReady(map: Map) {
  mapInstance = map;
  fetchAverageValue();

  if (mapInstance && !mapInstance.getLayers().getArray().includes(drawLayer)) {
    mapInstance.addLayer(drawLayer);
  }
  if (mapInstance && !mapInstance.getLayers().getArray().includes(cityLayer)) {
    mapInstance.addLayer(cityLayer);
  }

  // 初始化年度图表
  nextTick(() => {
    if (yearlyChartRef.value) {
      initYearlyChart();
      updateYearlyChartData();
    }
  });
}

// 监听年份变化
watch(selectedYear, () => {
  fetchAverageValue();
});

// 添加一个变量来标记当前是否显示的是区域数据
const isRegionData = ref(false);

// 监听统计类型变化
watch(selectedStat, async () => {
  if (cityGeoJsonDialogVisible.value) {
    if (isRegionData.value) {
      // 如果是区域数据，重新获取区域数据
      await fetchRegionData();
    } else if (selectedCityCode.value) {
      // 如果是城市数据，重新获取城市数据
      await showCityData();
    }
  }
});

// 修改显示城市数据的函数
async function showCityData() {
  try {
    if (!selectedCityCode.value) {
      ElMessage.warning('请先选择一个城市');
      return;
    }

    activeFeature.value = 'city';
    isRegionData.value = false;

    console.log('Fetching data for city:', selectedCityCode.value);

    const response = await api.get('/api/RT/code', {
      params: {
        code: selectedCityCode.value,
        year: selectedYear.value,
        data_type: currentDataType.value,
        stats: selectedStat.value
      }
    });
    const cityData = response.data ?? response;

    const cityFeature = citySource.getFeatures().find(feature => feature.get('city_code') === selectedCityCode.value);
    selectedGeometryName.value = cityFeature?.get('city_name') ?? '未知城市';
    analysisPayload.value = cityData;
    if (cityFeature) {
      setSpatialGeojson(convertFeatureToGeoJSON(cityFeature), {
        name: selectedGeometryName.value,
        spatial_type: 'city'
      });
    }
    selectedCityGeoJson.value = {
      features: [{
        properties: {
          city_code: selectedCityCode.value,
          city_name: selectedGeometryName.value,
          data: cityData
        }
      }]
    };

    cityGeoJsonDialogVisible.value = true;

    nextTick(() => {
      if (!chart) {
        initChart();
      }
      updateChartData();
    });
  } catch (error) {
    console.error('获取城市数据失败:', error);
    ElMessage.error('获取城市数据失败，请重试');
  }
}

// 监听弹窗关闭
watch(cityGeoJsonDialogVisible, (newVal) => {
  if (!newVal) {
    // 销毁图表
    if (chart) {
      chart.dispose();
      chart = null;
    }
    cityLayer.setVisible(false);
    
    // 清除选中的城市和区域数据标记
    selectedCityCode.value = null;
    isRegionData.value = false;
    activeFeature.value = '';
    selectedGeometryName.value = '';
    analysisPayload.value = null;
    geojsonData.value = null;
  }
});

// 修改显示城市GeoJSON的方法
async function showCityGeoJson() {
  try {
    if (citySource.getFeatures().length === 0) {
      await loadCityRegions();
    }
    selectedGeometryName.value = '待选择城市';
  } catch (error) {
    console.error('获取城市GeoJSON数据失败:', error);
    ElMessage.error('获取城市数据失败，请重试');
  }
}

function exportSpatialGeojson() {
  if (!hasSpatialGeojson.value) {
    ElMessage.warning('当前没有可导出的空间结果');
    return;
  }

  downloadTextFile(
    `${currentDataType.value}_spatial_${selectedYear.value}_${selectedMonth.value.toString().padStart(2, '0')}.geojson`,
    JSON.stringify(geojsonData.value, null, 2),
    'application/geo+json;charset=utf-8'
  );
  ElMessage.success('空间结果已导出');
}

function exportAnalysisResult() {
  if (!hasAnalysisResult.value) {
    ElMessage.warning('当前没有可导出的分析结果');
    return;
  }

  downloadTextFile(
    `${currentDataType.value}_analysis_${selectedYear.value}_${selectedMonth.value.toString().padStart(2, '0')}.json`,
    JSON.stringify({
      data_type: currentDataType.value,
      year: selectedYear.value,
      month: selectedMonth.value,
      mode: activeFeature.value,
      stats: selectedStat.value,
      selection: selectionLabel.value,
      analysis: analysisPayload.value
    }, null, 2)
  );
  ElMessage.success('分析结果已导出');
}

// 添加更新图表数据的函数
function updateChartData() {
  if (chart && selectedCityGeoJson.value && selectedCityGeoJson.value.features.length > 0) {
    const cityData = extractMonthlySeries(selectedCityGeoJson.value.features[0].properties.data);
    if (cityData.length) {
      chart.setOption({
        title: {
          text: `${selectedCityGeoJson.value.features[0].properties.city_name}${currentDataLabel.value}数据`
        },
        series: [{
          data: cityData
        }]
      });
    }
  }
}

// 添加初始化图表的函数
function initChart() {
  if (chart) {
    chart.dispose();
  }
  
  chart = echarts.init(chartRef.value);
  const isTemperature = category.value === 'wendu';
  const mainColor = isTemperature ? '#ff4d4f' : '#1890ff';
  const gradientColors = isTemperature 
    ? [
        { offset: 0, color: 'rgba(255, 77, 79, 0.4)' },
        { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
      ]
    : [
        { offset: 0, color: 'rgba(24, 144, 255, 0.4)' },
        { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
      ];

  const option = {
    title: {
      text: `${selectedCityGeoJson.value.features[0].properties.city_name}${isTemperature ? '温度' : '降水'}数据`,
      left: 'center',
      top: '0px',
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: mainColor
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: {
        color: '#333',
        fontSize: 14
      },
      formatter: function(params) {
        const value = params[0].value;
        return `${params[0].name}: ${value.toFixed(2)}${isTemperature ? '°C' : 'mm'}`;
      }
    },
    grid: {
      top: '70px',
      left: '60px',
      right: '40px',
      bottom: '40px'
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
      axisLabel: {
        interval: 0,
        fontSize: 13,
        color: '#666'
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: isTemperature ? '温度(°C)' : '降水量(mm)',
      nameLocation: 'middle',
      nameGap: 45,
      nameTextStyle: {
        fontSize: 14,
        color: mainColor,
        padding: [0, 0, 0, 0]
      },
      axisLabel: {
        fontSize: 13,
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          color: '#eee',
          type: 'dashed'
        }
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 12,
      itemStyle: {
        color: mainColor,
        borderWidth: 2,
        borderColor: '#fff'
      },
      lineStyle: {
        width: 4,
        shadowColor: 'rgba(0, 0, 0, 0.1)',
        shadowBlur: 10
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, gradientColors)
      }
    }]
  };
  chart.setOption(option);
}

// 修改月度分析函数
async function showMonthlyAnalysis() {
  monthlyAnalysisDialogVisible.value = true;
  // 预加载数据
  await preloadData();
  // 不再手动调用 initChart，组件内部自动初始化
  // nextTick(() => {
  //   if (averageChartRef.value) {
  //     averageChartRef.value.initChart();
  //   }
  // });
}

// 添加月度分析图表引用
const averageChartRef = ref(null);

// 监听月度分析弹窗关闭
watch(monthlyAnalysisDialogVisible, (newVal) => {
  console.log('月度分析弹窗关闭watch触发', newVal, '当前activeFeature:', activeFeature.value);
  if (!newVal) {
    if (averageChartRef.value && typeof averageChartRef.value.disposeChart === 'function') {
      averageChartRef.value.disposeChart();
    }
    activeFeature.value = '';
    console.log('activeFeature已重置为空');
  }
});

// 监听类别变化
watch(category, () => {
  if (monthlyAnalysisDialogVisible.value && averageChartRef.value) {
    averageChartRef.value.updateChart();
  }
});

// 修改初始化年度图表的函数
function initYearlyChart() {
  if (!yearlyChartRef.value) return;
  
  if (yearlyChart) {
    yearlyChart.dispose();
  }
  
  yearlyChart = echarts.init(yearlyChartRef.value);
  const isTemperature = category.value === 'wendu';
  const mainColor = isTemperature ? '#ff4d4f' : '#1890ff';
  const gradientColors = isTemperature 
    ? [
        { offset: 0, color: 'rgba(255, 77, 79, 0.4)' },
        { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
      ]
    : [
        { offset: 0, color: 'rgba(24, 144, 255, 0.4)' },
        { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
      ];

  const option = {
    title: {
      text: `${selectedYear.value}年${isTemperature ? '温度' : '降水'}数据`,
      left: 'center',
      top: '0px',
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: mainColor
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: {
        color: '#333',
        fontSize: 14
      },
      formatter: function(params) {
        const value = params[0].value;
        return `${params[0].name}: ${value.toFixed(2)}${isTemperature ? '°C' : 'mm'}`;
      }
    },
    grid: {
      top: '70px',
      left: '60px',
      right: '40px',
      bottom: '40px'
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
      axisLabel: {
        interval: 0,
        fontSize: 13,
        color: '#666'
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: isTemperature ? '温度(°C)' : '降水量(mm)',
      nameLocation: 'middle',
      nameGap: 45,
      nameTextStyle: {
        fontSize: 14,
        color: mainColor,
        padding: [0, 0, 0, 0]
      },
      axisLabel: {
        fontSize: 13,
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          color: '#eee',
          type: 'dashed'
        }
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 12,
      itemStyle: {
        color: mainColor,
        borderWidth: 2,
        borderColor: '#fff'
      },
      lineStyle: {
        width: 4,
        shadowColor: 'rgba(0, 0, 0, 0.1)',
        shadowBlur: 10
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, gradientColors)
      },
      markPoint: {
        symbol: 'pin',
        symbolSize: 60,
        data: [],
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
          fontSize: 14,
          color: '#333',
          backgroundColor: 'transparent'
        },
        itemStyle: {
          color: mainColor
        }
      }
    }]
  };
  yearlyChart.setOption(option);
}

// 修改更新年度图表数据的函数
async function updateYearlyChartData() {
  if (!yearlyChart) return;
  
  try {
    isLoading.value = true;
    const response = await Promise.race([
      api.get('/api/RT/avg', {
        params: {
          year: selectedYear.value,
          data_type: currentDataType.value
        }
      }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('请求超时')), 5000)
      )
    ]);
    
    if (Array.isArray(response.data)) {
      const isTemperature = category.value === 'wendu';
      const mainColor = isTemperature ? '#ff4d4f' : '#1890ff';
      const gradientColors = isTemperature 
        ? [
            { offset: 0, color: 'rgba(255, 77, 79, 0.4)' },
            { offset: 1, color: 'rgba(255, 77, 79, 0.1)' }
          ]
        : [
            { offset: 0, color: 'rgba(24, 144, 255, 0.4)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
          ];

      const currentMonth = selectedMonth.value - 1;
      const markPointData = [{
        name: '当前月份',
        value: response.data[currentMonth],
        xAxis: currentMonth,
        yAxis: response.data[currentMonth],
        itemStyle: {
          color: mainColor
        }
      }];

      yearlyChart.setOption({
        title: {
          text: `${selectedYear.value}年${isTemperature ? '温度' : '降水'}数据`,
          textStyle: {
            color: mainColor
          }
        },
        yAxis: {
          name: isTemperature ? '温度(°C)' : '降水量(mm)',
          nameTextStyle: {
            color: mainColor
          }
        },
        series: [{
          data: response.data,
          markPoint: {
            data: markPointData
          },
          itemStyle: {
            color: mainColor
          },
          lineStyle: {
            color: mainColor
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, gradientColors)
          },
          label: {
            color: mainColor
          }
        }]
      });
    }
  } catch (error) {
    console.error('获取年度数据失败:', error);
    ElMessage.error('获取数据失败，请重试');
  } finally {
    isLoading.value = false;
  }
}

// 监听年份和月份变化
watch([selectedYear, selectedMonth, category], async () => {
  if (yearlyChart) {
    await updateYearlyChartData();
  }
});

// 监听窗口大小变化
onMounted(() => {
  window.addEventListener('resize', () => {
    if (yearlyChart) {
      yearlyChart.resize();
    }
  });
});

onUnmounted(() => {
  if (yearlyChart) {
    yearlyChart.dispose();
    yearlyChart = null;
  }
  window.removeEventListener('resize', () => {
    if (yearlyChart) {
      yearlyChart.resize();
    }
  });
});

// 修改：激活功能方法
function activateFeature(feature) {
  if (activeFeature.value !== feature) {
    clearAll();
  }
  activeFeature.value = feature;
  if (feature === 'draw') startDrawing();
  if (feature === 'point') startPointAnalysis();
  if (feature === 'city') {
    setMapCursor('crosshair');
    showCityGeoJson();
  }
  if (feature === 'monthly') showMonthlyAnalysis();
}
function deactivateFeature() {
  activeFeature.value = '';
  // 可根据需要添加额外的重置逻辑
}
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

.gis-summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 14px 16px 10px;
}

.gis-summary-card {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12), rgba(64, 158, 255, 0.04));
  border: 1px solid rgba(64, 158, 255, 0.18);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gis-summary-card .label {
  font-size: 12px;
  color: #64748b;
}

.gis-summary-card strong {
  color: #0f172a;
  font-size: 15px;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  padding: 0 16px;

  .map-area {
    width: 100%;
    height: calc(100vh - 60px);
    position: relative;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    padding: 12px;
    overflow: hidden;

    .map {
      height: 100%;
      width: 100%;
      background-color: white;
      border-radius: 8px;
      overflow: hidden;
      position: relative;
    }

    .slider-panel {
      position: absolute;
      bottom: 26px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 10;
      background: rgba(255, 255, 255, 0.075);
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      padding: 18px 32px 12px 32px;
      display: flex;
      align-items: center;
      gap: 32px;
      min-width: 480px;
      max-width: 900px;
      width: 80%;
      border: 1.5px solid #e0e6ed;
      padding: 1% 2% 2% 2%;

      .year-input {
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 120px;

        .el-input-number {
          width: 100px;
        }

        .year-label {
          font-size: 14px;
          color: #606266;
          font-weight: 500;
        }
      }

      .current-date {
        margin-left: 32px;
        font-size: 22px;
        font-weight: bold;
        color: #409EFF;
        letter-spacing: 2px;
        min-width: 110px;
        text-align: right;
        user-select: none;

        .month {
          font-size: 28px;
          color: #ff9800;
          font-weight: bold;
          margin: 0 2px;
        }
      }

      .el-radio-group {
        margin-right: 18px;
      }

      .el-slider {
        --el-slider-main-bg-color: #409EFF;
        --el-slider-runway-bg-color: #e4e7ed;
        --el-slider-height: 6px;
        --el-slider-button-size: 22px;
        --el-slider-button-bg-color: #fff;
        --el-slider-button-border: 2px solid #409EFF;
        --el-slider-tooltip-bg-color: #409EFF;
        --el-slider-tooltip-color: #fff;
        --el-slider-tooltip-font-size: 14px;
        margin-top: 0;
      }

      .el-slider__marks-text {
        color: #409EFF !important;
        font-weight: bold;
        font-size: 14px !important;
        margin-top: 8px;
      }

      .el-slider__button {
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
      }

      .el-slider__runway {
        border-radius: 4px;
      }

      .el-slider__bar {
        border-radius: 4px;
      }

      .el-slider__button-wrapper {
        top: -8px !important;
      }

      .el-slider__tooltip {
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.12);
      }
    }

    .toolbar {
      position: absolute;
      left: 70px;
      top: 20px;
      z-index: 100;
      height: 42px;
      border-radius: 8px;
      display: flex;
      align-items: center;
    }

    .toolbar-export {
      left: auto;
      right: 20px;
    }

    .analysis-status-panel {
      position: absolute;
      left: 70px;
      top: 72px;
      z-index: 100;
      width: 240px;
      background: rgba(255, 255, 255, 0.94);
      border-radius: 10px;
      border: 1px solid #e5e7eb;
      padding: 12px 14px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
      backdrop-filter: blur(8px);
    }

    .status-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #1f2937;
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

    .legend-panel {
      position: absolute;
      left: 40px;
      bottom: 30px;
      z-index: 110;
      background: rgba(255, 255, 255, 0.9);
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
        max-width: 120px;
        display: block;
      }
    }

    .legend-slot {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 120px;
    }
  }
}

.controls {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.map-selection-chip {
  position: absolute;
  right: 20px;
  bottom: 18px;
  z-index: 120;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(64, 158, 255, 0.18);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  color: #1e293b;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}

:deep(.city-data-dialog) {
  position: fixed;
  bottom: 20px;
  right: 40px;
  margin: 0;
  top: auto;
  left: auto;
  transform: none;

  .el-dialog__header {
    padding: 12px 16px;
    margin: 0;
    border-bottom: 1px solid #e4e7ed;
  }

  .el-dialog__body {
    padding: 16px;
  }

  .el-dialog__headerbtn {
    top: 12px;
  }
}

.yearly-chart-container {
  position: absolute;
  top: 40px;
  right: 40px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.408);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 25px;
  width: 450px;
  height: 320px;
  // backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  
  .yearly-chart {
    width: 100%;
    height: 100%;
  }
}

:deep(.monthly-analysis-dialog) {
  .el-dialog__body {
    padding: 20px;
  }
}
</style>

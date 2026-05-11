<template>
  <div class="content">
    <!-- 数据卡片区域 -->
    <div class="card-row">
      <div class="card">
        <h3>RSEI平均值</h3>
        <div class="card-value">
          <span class="value blue">{{ currentRSEI }}</span>
          <span class="unit">指数值</span>
        </div>
      </div>
      <div class="card">
        <h3>年度变化率</h3>
        <div class="card-value">
          <span class="value" :class="yearChange >= 0 ? 'green' : 'orange'">{{ yearChange >= 0 ? '+' : '' }}{{
            yearChange }}%</span>
          <span class="unit">较上年</span>
        </div>
      </div>
      <div class="card">
        <h3>高值区面积</h3>
        <div class="card-value">
          <span class="value blue">{{ highValue }}</span>
          <span class="unit">km²</span>
        </div>
      </div>
      <div class="card">
        <h3>低值区面积</h3>
        <div class="card-value">
          <span class="value orange">{{ lowValue }}</span>
          <span class="unit">km²</span>
        </div>
      </div>
    </div>

    <div class="gis-card-row">
      <div class="gis-card">
        <span class="gis-card-label">当前年份</span>
        <strong>{{ selectedYear }}年</strong>
      </div>
      <div class="gis-card">
        <span class="gis-card-label">当前模式</span>
        <strong>{{ activeModeLabel }}</strong>
      </div>
      <div class="gis-card">
        <span class="gis-card-label">空间选择</span>
        <strong>{{ spatialSelectionLabel }}</strong>
      </div>
      <div class="gis-card">
        <span class="gis-card-label">结果状态</span>
        <strong>{{ analysisStatusLabel }}</strong>
      </div>
    </div>

    <!-- 主要内容区 -->
    <main class="main">
      <div class="map-area">
        <!-- 新toolbar，仿照landcoverage布局 -->
        <div class="toolbar">
          <el-button-group>
            <el-button type="primary" size="small"
              :disabled="showDrawToolbar || (!!activeFeature && activeFeature !== 'trend')"
              @click="handleTrendCompare">
              趋势分析
            </el-button>
            <el-button type="primary" size="small"
              :disabled="showDrawToolbar || (!!activeFeature && activeFeature !== 'draw')"
              @click="handleStartDrawCompare">
              对比分析
            </el-button>
            <el-button type="primary" size="small"
              :disabled="showDrawToolbar || (!!activeFeature && activeFeature !== 'city')"
              @click="handleStartCityCompare">
              城市对比分析
            </el-button>
          </el-button-group>
        </div>

        <div class="toolbar toolbar-export">
          <el-button-group>
            <el-button size="small" type="success" :disabled="!hasSpatialGeojson" @click="exportSpatialGeojson">
              导出空间
            </el-button>
            <el-button size="small" type="warning" :disabled="!hasAnalysisResult" @click="exportAnalysisResult">
              导出结果
            </el-button>
          </el-button-group>
        </div>

        <div class="analysis-status-panel">
          <div class="status-header">
            <span>RSEI GIS状态</span>
            <el-tag size="small" :type="activeFeature ? 'success' : 'info'">{{ activeModeLabel }}</el-tag>
          </div>
          <div class="status-row">
            <span>空间选择</span>
            <strong>{{ spatialSelectionLabel }}</strong>
          </div>
          <div class="status-row">
            <span>选点坐标</span>
            <strong>{{ selectedPointLabel }}</strong>
          </div>
          <div class="status-row">
            <span>结果摘要</span>
            <strong>{{ analysisSummaryLabel }}</strong>
          </div>
          <div class="status-row">
            <span>结果状态</span>
            <strong>{{ analysisStatusLabel }}</strong>
          </div>
        </div>

        <!-- 对比分析工具条，仿照landcoverage -->
        <div v-if="showDrawToolbar" class="comparison-toolbar">
          <el-button-group>
            <el-button @click="startDrawing(1)"
              :disabled="drawStep > 0 || drawingMode !== null || (polygon1 && polygon2)"
              size="small" type="primary">绘制区域1</el-button>
            <el-button @click="startDrawing(2)"
              :disabled="drawStep !== 1 || drawingMode !== null || (polygon1 && polygon2)"
              size="small" type="primary">绘制区域2</el-button>
            <el-button @click="clearAll"
              :disabled="!polygon1 && !polygon2"
              size="small" type="danger">清除所有</el-button>
          </el-button-group>
        </div>
          <!-- 悬浮的年份选择区域 -->
        <div class="year-selector-float">
          <label>选择年份：</label>
          <el-select v-model="selectedYear" class="year-select">
            <el-option v-for="year in years" :key="year" :label="`${year}年`" :value="year" />
          </el-select>
        </div>
        <!-- 添加城市选择提示 -->
        <div v-if="showCitySelect" class="city-select-hint">
          {{ selectedCities.length === 0 ? '请选择第一个城市' : '请选择第二个城市' }}
        </div>

        <div v-if="selectedPointLabel !== '--'" class="map-selection-chip">
          {{ selectedPointLabel }}
        </div>
        
        <div class="map" ref="mapDivRef" style="position:relative;">
          <Basemap
            :layersConfig="mapLayerConfig"
            :center="[116.25, 28.25]"
            :zoom="7"
            :geojson="geojsonData"
            :legend-title="legendTitle"
            @map-click="onMapClick"
            @view-ready="onViewReady"
          >
            <template #legend>
              <div class="legend-slot">
                <img
                  :src="legendUrl"
                  alt="RSEI图例"
                  class="legend-image"
                  @error="onLegendError"
                />
              </div>
            </template>
          </Basemap>
        </div>
      </div>

      <!-- 图表 -->
      <div class="chart-group">
        <div class="chart">
          <Piechart :data="pieData"></Piechart>
        </div>
        <div class="chart">
          <Barchart :data="barChartData"></Barchart>
        </div>
      </div>
    </main>

    <!-- 添加城市对比弹窗组件 -->
    <RegionCompare v-if="showRegionDialog" :data="regionCompareData" @close="showRegionDialog = false" />

    <el-dialog v-model="dialogVisible" title="提示" width="300px" :close-on-click-modal="false" align-center>
      <span>没有数据</span>
      <template #footer>
        <el-button type="primary" @click="dialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>

  <GlobalAlert ref="globalAlertRef" />


</template>

<script lang="ts" setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue';
import Basemap from "@/components/baseMap.vue";
import Piechart from '@/components/piechart.vue';
import Barchart from '@/components/barchart.vue';
import GlobalAlert from "@/components/GlobalAlert.vue";
import RegionCompare from '@/components/RegionCompare.vue';
import { ElMessage } from 'element-plus';
import api from '@/utils/request';
import Draw from 'ol/interaction/Draw';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import { Fill, Stroke, Style } from 'ol/style';
import { toLonLat } from 'ol/proj';
import type Map from 'ol/Map';
import type Feature from 'ol/Feature';


interface SubLayer {
  title?: string;
  id?: number;
  visible: boolean;
  subLayers?: SubLayer[];
}

interface LayerConfig {
  type: string;
  url: string;
  subLayers?: SubLayer[];
}

// 基础数据
const years = ref<number[]>([]);
const selectedYear = ref<number>(2022);
const csvRaw = ref<string[]>([]);
const classificationData = ref<string[]>([]);

// 地图相关
const mapDivRef = ref<HTMLElement | null>(null);
const showCitySelect = ref(false);
const selectedCities = ref<string[]>([]);
const showRegionDialog = ref(false);
const regionCompareData = ref<any>(null);
// 新增：对比分析绘制工具栏显示控制
const showDrawToolbar = ref(false);
const legendVariantIndex = ref(0);

// 弹窗相关
const dialogVisible = ref(false);
const globalAlertRef = ref<any>(null);

// 图表数据
const pieData = ref<{ name: string, value: number }[]>([]);
const barChartData = ref<{ name: string, value: number }[]>([]);
const isTrendCompareActive = ref(false);
const markerPosition = ref<{ left: number; top: number } | null>(null);
const geojsonData = ref<any>(null);
const selectedPoint = ref<[number, number] | null>(null);

//多点
const drawingMode = ref<1 | 2 | null>(null);
const polygon1 = ref<any>(null);
const polygon2 = ref<any>(null);
const showAnalysisDialog = ref(false);
const analysisResult = ref<any>(null);

// 添加坐标存储变量
const polygon1Coordinates = ref<number[][]>([]);
const polygon2Coordinates = ref<number[][]>([]);

// 新增：绘制步骤 0=未开始，1=已画区域1，2=已画区域2
const drawStep = ref(0);

// 地图状态
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
    ElMessage.error('地图未初始化');
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

// 新增：全局功能激活状态
const activeFeature = ref<null | 'trend' | 'city' | 'draw'>(null);

// 定义地图图层配置
const mapLayerConfig = computed<LayerConfig[]>(() => {
  const layers = [{
    type: 'WMSLayer',
    url: '/geoserver/predata/wms',
    subLayers: [
      {
        title: `predata:RSEI_${selectedYear.value}`,
        visible: true
      }
    ]
  }];
  // 不再在这里处理城市区域图层
  return layers;
});

const legendCandidates = computed(() => {
  const layerCandidates = [`predata:RSEI_${selectedYear.value}`];
  const styleCandidates = ['', 'RSEI_style', 'rsei_style'];
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

const legendTitle = computed(() => `RSEI图例 · ${selectedYear.value}年`);
const modeLabelMap: Record<'trend' | 'city' | 'draw', string> = {
  trend: '趋势分析',
  city: '城市对比',
  draw: '区域对比'
};

const activeModeLabel = computed(() => {
  if (!activeFeature.value) return '待选择模式';
  return modeLabelMap[activeFeature.value];
});

const spatialSelectionLabel = computed(() => {
  if (selectedCities.value.length) {
    return `${selectedCities.value.length}个城市`;
  }
  if (polygon1.value && polygon2.value) {
    return '双区域已完成';
  }
  if (polygon1.value) {
    return '已绘制区域1';
  }
  if (selectedPoint.value) {
    return '已选点位';
  }
  if (activeFeature.value === 'city') return '待选城市';
  if (activeFeature.value === 'draw') return drawStep.value === 0 ? '待绘制区域1' : '待绘制区域2';
  if (activeFeature.value === 'trend') return '待选点位';
  return '未激活';
});

const selectedPointLabel = computed(() => {
  if (!selectedPoint.value) return '--';
  return `${selectedPoint.value[0].toFixed(4)}, ${selectedPoint.value[1].toFixed(4)}`;
});

const analysisStatusLabel = computed(() => {
  if (analysisResult.value) return '已生成';
  if (activeFeature.value) return '分析中';
  return '待生成';
});

const analysisSummaryLabel = computed(() => {
  if (analysisResult.value?.pixel_value !== undefined) {
    return `像元值 ${analysisResult.value.pixel_value}`;
  }
  if (analysisResult.value?.['分析摘要']) {
    return `${Object.keys(analysisResult.value['分析摘要']).length}项摘要`;
  }
  if (analysisResult.value?.trend_analysis) {
    return `${Object.keys(analysisResult.value.trend_analysis).length}项趋势`;
  }
  return '待生成';
});

const hasSpatialGeojson = computed(() => !!geojsonData.value?.features?.length);
const hasAnalysisResult = computed(() => !!analysisResult.value);

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

function setGeojsonFeatures(features: any[]) {
  const validFeatures = features.filter(Boolean);
  geojsonData.value = validFeatures.length
    ? { type: 'FeatureCollection', features: validFeatures }
    : null;
}

function updateTrendPointGeojson(lon: number, lat: number) {
  setGeojsonFeatures([
    {
      type: 'Feature',
      properties: {
        type: 'trend-point',
        year: selectedYear.value
      },
      geometry: {
        type: 'Point',
        coordinates: [lon, lat]
      }
    }
  ]);
}

function syncDrawGeojson() {
  setGeojsonFeatures([
    polygon1.value ? convertFeatureToGeoJSON(polygon1.value) : null,
    polygon2.value ? convertFeatureToGeoJSON(polygon2.value) : null
  ]);
}

async function syncCityGeojson(cityCodes: string[]) {
  const res = await fetch('/src/assets/cityRegion.geojson');
  const data = await res.json();
  const features = (data.features ?? []).filter((feature: any) => cityCodes.includes(feature.properties?.city_code));
  geojsonData.value = features.length ? { ...data, features } : null;
}

function exportSpatialGeojson() {
  if (!hasSpatialGeojson.value) {
    ElMessage.warning('当前没有可导出的空间结果');
    return;
  }

  downloadTextFile(
    `rsei_spatial_${selectedYear.value}.geojson`,
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

  const payload = {
    year: selectedYear.value,
    mode: activeFeature.value,
    generated_at: new Date().toISOString(),
    selected_point: selectedPoint.value,
    selected_cities: selectedCities.value,
    analysis: analysisResult.value
  };

  downloadTextFile(`rsei_analysis_${selectedYear.value}.json`, JSON.stringify(payload, null, 2));
  ElMessage.success('分析结果已导出');
}

// RSEI等级数据
const indexKeys = [
  { prefix: 'RSEI', name: 'RSEI指数' },
  { prefix: 'NDVI', name: 'NDVI指数' },
  { prefix: 'LST', name: 'LST指数' },
  { prefix: 'NDBSI', name: 'NDBI指数' },
  { prefix: 'Wet', name: '湿度指数' }
];
const levelNames = ['极差', '较差', '一般', '良好', '优秀'].reverse();

// 计算属性
const currentRSEI = computed<string>(() => {
  const row = classificationData.value.find(line => line.startsWith(`RSEI_${selectedYear.value}`));
  if (row) {
    const values = row.split(',');
    return (parseFloat(values[8])).toFixed(2);
  }
  return '-';
});

const highValue = computed(() => {
  const row = classificationData.value.find(line => line.startsWith(`RSEI_${selectedYear.value}`));
  if (row) {
    const values = row.split(',');
    return parseFloat(values[6]).toFixed(2);
  }
  return '-';
});

const lowValue = computed(() => {
  const row = classificationData.value.find(line => line.startsWith(`RSEI_${selectedYear.value}`));
  if (row) {
    const values = row.split(',');
    return parseFloat(values[7]).toFixed(2);
  }
  return '-';
});

const yearChange = computed(() => {
  const currentRow = classificationData.value.find(line => line.startsWith(`RSEI_${selectedYear.value}`));
  const prevRow = classificationData.value.find(line => line.startsWith(`RSEI_${selectedYear.value - 1}`));

  if (currentRow && prevRow) {
    const currentValue = parseFloat(currentRow.split(',')[8]);
    const prevValue = parseFloat(prevRow.split(',')[8]);
    return Number(((currentValue - prevValue) / prevValue * 100).toFixed(2));
  }
  return 0;
});

// 初始化数据
onMounted(async () => {
  try {
    // 读取指数统计数据
    const res = await fetch('/src/assets/RESI_Statistics.csv');
    const text = await res.text();
    csvRaw.value = text.trim().split('\n');

    // 读取分类数据
    const classRes = await fetch('/src/assets/RSEI_Classification.csv');
    const classText = await classRes.text();
    classificationData.value = classText.trim().split('\n');

    // 提取所有年份
    const yearSet = new Set<number>();
    for (const line of csvRaw.value) {
      const [key] = line.split(',');
      const match = key.match(/_(\d{4})\.tif$/);
      if (match) {
        yearSet.add(Number(match[1]));
      }
    }

    years.value = Array.from(yearSet).sort((a, b) => b - a);
    if (years.value.length > 0) {
      selectedYear.value = years.value[0];
      updateChartData();
    }
  } catch (error) {
    console.error('初始化数据失败:', error);
    ElMessage.error('数据加载失败');
  }
});

// 更新图表数据
function updateChartData() {
  const year = selectedYear.value;

  // 更新柱状图数据
  const data: { name: string, value: number }[] = [];
  for (const idx of indexKeys) {
    const row = csvRaw.value.find(line => line.startsWith(`${idx.prefix}_${year}`));
    if (row) {
      const [, value] = row.split(',');
      data.push({ name: idx.name, value: Number(value) });
    }
  }
  barChartData.value = data;

  // 更新饼图数据
  const classRow = classificationData.value.find(line => line.startsWith(`RSEI_${year}`));
  if (classRow) {
    const values = classRow.split(',').slice(1, 6);
    pieData.value = values.map((value, index) => ({
      name: levelNames[index],
      value: parseFloat(value.replace('%', ''))
    }));
  }
}


// 地图点击事件处理
async function onMapClick(event: any) {
  // 仅在趋势分析激活时处理趋势分析逻辑
  if (isTrendCompareActive.value) {
    isTrendCompareActive.value = false;
    setMapCursor('default');

    if (
      event.latitude === undefined ||
      event.longitude === undefined ||
      isNaN(Number(event.latitude)) ||
      isNaN(Number(event.longitude))
    ) {
      dialogVisible.value = true;
      return;
    }

    try {
      dialogVisible.value = false;
      const lon = Number(Number(event.longitude ?? event.lon).toFixed(6));
      const lat = Number(Number(event.latitude ?? event.lat).toFixed(6));
      selectedPoint.value = [lon, lat];
      analysisResult.value = null;
      updateTrendPointGeojson(lon, lat);

      const payload = {
        lat,
        lon,
        year: Number(selectedYear.value)
      };
      console.log('请求payload:', payload);
      try {
        const res = await api.post('/predict', payload, {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 10000 // 10秒超时
        });
        
        console.log('原始API响应:', res);
        console.log('API响应类型:', typeof res);
        console.log('API响应数据:', res?.data);
        
        // 检查响应数据
        const responseData = res?.data || res;
        if (!responseData) {
          console.error('API响应为空');
          dialogVisible.value = true;
          return;
        }

        if (!responseData.pixel_value) {
          console.error('API响应数据不完整，缺少pixel_value字段');
          dialogVisible.value = true;
          return;
        }

        const popupData = {
          anomalies: responseData.anomalies || [],
          coordinates: responseData.coordinates || {},
          ml_prediction: responseData.ml_prediction || {},
          pixel_value: responseData.pixel_value,
          time_series: responseData.time_series || {},
          trend_analysis: responseData.trend_analysis || {}
        };
        analysisResult.value = popupData;
        showAnalysisDialog.value = true;

        if (globalAlertRef.value?.closeAlert) {
          globalAlertRef.value.closeAlert();
          setTimeout(() => {
            globalAlertRef.value?.openAlert({
              title: '趋势分析',
              popupData: popupData
            });
          }, 10);
        } else {
          globalAlertRef.value?.openAlert({
            title: '趋势分析',
            popupData: popupData
          });
        }
      } catch (error: any) {
        console.error('API请求失败:', error);
        if (error.response) {
          console.error('错误响应:', error.response.data);
          console.error('错误状态:', error.response.status);
        } else if (error.request) {
          console.error('请求未收到响应:', error.request);
        } else {
          console.error('请求配置错误:', error.message);
        }
        dialogVisible.value = true;
      }
    } catch (error) {
      console.error('API请求失败:', error);
      dialogVisible.value = true;
    }
    return;
  }

  // 城市选择逻辑保持不变
  if (!showCitySelect.value) return;

  try {
    const attrs = event.attributes;
    if (attrs?.city_code) {
      const cityCode = attrs.city_code;

      // 只用city_code属性，不用event其他内容
      if (!selectedCities.value.includes(cityCode)) {
        if (selectedCities.value.length >= 2) {
          selectedCities.value.shift();
        }
        selectedCities.value.push(cityCode);

        if (selectedCities.value.length === 2) {
          // 传入city_code数组到fetchCityComparison
          await fetchCityComparison([...selectedCities.value]);
          showCitySelect.value = false;
        } else {
          ElMessage.info('请点击选择第二个城市');
        }
      }
    } else {
      // 没有命中要素时给出提示
      ElMessage.warning('请点击城市区域进行选择');
    }
  } catch (error) {
    console.error('处理城市点击事件失败:', error);
    ElMessage.error('获取城市数据失败');
  }
}

// 获取城市对比数据
async function fetchCityComparison(cityCodes?: string[]) {
  try {
    const codes = cityCodes ?? selectedCities.value;
    if (!codes || codes.length < 2) {
      ElMessage.warning('请选择两个城市进行对比');
      return;
    }
    // city_codes参数需作为对象属性传递
    const url = '/api/RegionCompare/geojson/';
    const res = await api.post(url, { city_codes: codes });
    console.log('城市对比API响应:', res);
    
    // 检查响应数据
    const responseData = res?.data || res;
    if (!responseData || !responseData['分析摘要'] || !responseData['图表数据']) {
      throw new Error('请求失败: 响应数据格式不正确');
    }

    analysisResult.value = responseData;
    regionCompareData.value = responseData;
    await syncCityGeojson(codes);
    showRegionDialog.value = true;
  } catch (error: any) {
    console.error('获取城市对比数据失败:', error);
    if (error.response) {
      console.error('错误响应:', error.response.data);
      console.error('错误状态:', error.response.status);
    } else if (error.request) {
      console.error('请求未收到响应:', error.request);
    } else {
      console.error('请求配置错误:', error.message);
    }
    ElMessage.error('获取城市数据失败，请确认已点击城市区域且服务可用');
    analysisResult.value = null;
    geojsonData.value = null;
    regionCompareData.value = null;
    selectedCities.value = [];
    showRegionDialog.value = false;
  }
}

// 开始城市对比
function handleStartCityCompare() {
  clearAll();
  activeFeature.value = 'city';
  selectedCities.value = [];
  regionCompareData.value = null;
  analysisResult.value = null;
  showRegionDialog.value = false;
  showCitySelect.value = true;
  setMapCursor('crosshair');
  ElMessage.info('请在地图上选择两个城市进行对比');
}

// 处理趋势对比分析按钮点击
function handleTrendCompare() {
  clearAll();
  activeFeature.value = 'trend';
  isTrendCompareActive.value = true;
  setMapCursor('crosshair');
  ElMessage.info('请在地图上点选RSEI像元位置');
}

function setMapCursor(cursor: string) {
  const mapArea = mapDivRef.value;
  if (mapArea) {
    mapArea.style.cursor = cursor;
  }
}

// 监听地图视图就绪
async function onViewReady(map: Map) {
  console.log('地图视图已就绪');
  mapInstance = map;
  if (mapInstance && !mapInstance.getLayers().getArray().includes(drawLayer)) {
    mapInstance.addLayer(drawLayer);
  }
  if (mapInstance && !mapInstance.getLayers().getArray().includes(cityLayer)) {
    mapInstance.addLayer(cityLayer);
  }

  if (showCitySelect.value) {
    await loadCityRegions();
  }
}

// 加载城市区域图层
async function loadCityRegions() {
  if (!mapInstance) return;
  citySource.clear();
  try {
    const res = await fetch('/src/assets/cityRegion.geojson');
    const data = await res.json();
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
  } catch (error) {
    console.error('加载城市区域失败:', error);
    ElMessage.error('加载城市区域失败');
  }
}

// 监听 showCitySelect 变化，动态加载/移除城市区域图层
watch(showCitySelect, async (val) => {
  if (val) {
    await loadCityRegions();
  } else {
    cityLayer.setVisible(false);
    if (activeFeature.value === 'city') setMapCursor('default');
  }
});

// 添加 analyzeAndShowComparison 函数
async function analyzeAndShowComparison() {
  if (!polygon1Coordinates.value.length || !polygon2Coordinates.value.length) return;

  try {
    // 发送数据到后端
    const response = await api.post('/api/RegionCompare/point/', {
      point_groups: [
        {
          id: "region1",
          name: "区域1",
          points: polygon1Coordinates.value
        },
        {
          id: "region2",
          name: "区域2",
          points: polygon2Coordinates.value
        }
      ]
    });

    // 检查响应数据
    const responseData = response?.data || response;
    if (!responseData || !responseData['分析摘要'] || !responseData['图表数据']) {
      throw new Error('请求失败: 响应数据格式不正确');
    }

    analysisResult.value = responseData;
    regionCompareData.value = responseData;
    syncDrawGeojson();
    showAnalysisDialog.value = true;
    showRegionDialog.value = true;
    // 新增：分析完成后隐藏绘制工具栏
    showDrawToolbar.value = false;
  } catch (error: any) {
    console.error('分析比较失败:', error);
    if (error.response) {
      console.error('错误响应:', error.response.data);
      console.error('错误状态:', error.response.status);
    } else if (error.request) {
      console.error('请求未收到响应:', error.request);
    } else {
      console.error('请求配置错误:', error.message);
    }
    ElMessage.error('分析比较失败，请重试');
    // 新增：失败时也隐藏绘制工具栏
    showDrawToolbar.value = false;
  }
}

// 添加 startDrawing 函数
async function startDrawing(mode: 1 | 2) {
  if (!mapInstance) {
    ElMessage.error('地图未初始化');
    return;
  }

  activeFeature.value = 'draw';
  drawingMode.value = mode;
  const shouldClear = mode === 1;

  startPolygonDraw(async (_, feature) => {
    const coords = (feature.getGeometry()?.getCoordinates()?.[0] ?? []).map((coord: number[]) => toLonLat(coord));
    if (mode === 1) {
      polygon1.value = feature;
      polygon1Coordinates.value = coords;
      drawStep.value = 1;
    } else {
      polygon2.value = feature;
      polygon2Coordinates.value = coords;
      drawStep.value = 2;
    }

    console.log(`区域${mode}的坐标:`, coords);
    drawingMode.value = null;
    syncDrawGeojson();
    if (polygon1.value && polygon2.value) {
      await analyzeAndShowComparison();
      showDrawToolbar.value = false;
      drawStep.value = 0;
    } else {
      ElMessage.info('已完成区域1绘制，请继续绘制区域2');
    }
  }, { clear: shouldClear });
}

// 修改 clearAll 函数
function clearAll() {
  drawSource.clear();
  cleanupDrawInteraction();
  polygon1.value = null;
  polygon2.value = null;
  polygon1Coordinates.value = [];
  polygon2Coordinates.value = [];
  drawingMode.value = null;
  showDrawToolbar.value = false;
  showCitySelect.value = false;
  selectedCities.value = [];
  selectedPoint.value = null;
  markerPosition.value = null;
  geojsonData.value = null;
  analysisResult.value = null;
  regionCompareData.value = null;
  showAnalysisDialog.value = false;
  isTrendCompareActive.value = false;
  activeFeature.value = null;
  drawStep.value = 0;
}

// 监听弹窗关闭时恢复鼠标样式和功能状态
watch(isTrendCompareActive, (active) => {
  if (!active) {
    setMapCursor('default');
  }
});

// 监听年份变化
watch(selectedYear, updateChartData);
watch(selectedYear, () => {
  legendVariantIndex.value = 0;
});

// 城市对比弹窗关闭时重置功能状态
watch(showRegionDialog, (val) => {
  if (!val && activeFeature.value === 'city') {
    activeFeature.value = null;
    setMapCursor('default');
  }
  // 新增：关闭弹窗时清除对比分析图形
  if (!val) {
    clearAll();
  }
});

// 新增：对比分析按钮点击处理
function handleStartDrawCompare() {
  clearAll();
  activeFeature.value = 'draw';
  showDrawToolbar.value = true;
  drawStep.value = 0;
  ElMessage.info('请依次绘制两个对比区域');
}
</script>

<style lang="less" scoped>
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow: hidden;
  background: #f5f6fa;
  padding: 15px 20px;
}

.card-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin: 0 4px 15px 4px;
  padding: 0;
  height: 64px;
  align-items: center;
}

.gis-card-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 0 4px 14px 4px;
}

.gis-card {
  background: linear-gradient(135deg, rgba(97, 136, 228, 0.12), rgba(58, 139, 237, 0.08));
  border: 1px solid rgba(97, 136, 228, 0.18);
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 68px;
}

.gis-card-label {
  font-size: 12px;
  color: #64748b;
}

.gis-card strong {
  font-size: 15px;
  color: #0f172a;
}

.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  transition: all 0.3s ease;
  cursor: pointer;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.card h3 {
  font-size: 14px;
  font-weight: 500;
  color: #444;
  margin-bottom: 4px;
}

.card-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.value {
  font-size: 20px;
  font-weight: 600;

  &.blue {
    color: #1890ff;
  }

  &.green {
    color: #52c41a;
  }

  &.orange {
    color: #fa8c16;
  }
}

.unit {
  font-size: 12px;
  color: #999;
}

.main {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 18px 4px;
  overflow: hidden;
  box-sizing: border-box;
  height: calc(100% - 100px);
  /* 调整主区域高度 */
}


.map-area {
  flex: 3;
  /* 增加地图区域的比例 */
  position: relative;
  background: #ffffff7a;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 6px 16px;
  min-width: 0;
  overflow: hidden;
  height: 100%;
  /* 确保地图区域占满高度 */
}


// 年份选择器样式
.year-selector-float {
  position: absolute;
  right: 70px;
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

.compare-btn-wrapper {
  position: absolute;
  z-index: 10;
}

.city {
  right: 140px;
  top: 24px;
}

.trend {
  right:40px;
  top: 24px;
}

.city-select-hint {
  position: absolute;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.95);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  animation: fadeInDown 0.3s ease-out;
}

.click-hint,
.click-region {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 10;
}

.click-region {
  bottom: 45px;
}

.toolbar {
  position: absolute;
  left: 75px;
  top: 24px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
}

.toolbar-export {
  left: auto;
  right: 20px;
}

.analysis-status-panel {
  position: absolute;
  left: 75px;
  top: 80px;
  z-index: 10;
  width: 240px;
  background: rgba(255, 255, 255, 0.96);
  padding: 12px 14px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(8px);
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
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

// 对比分析工具条样式
.comparison-toolbar {
  position: absolute;
  left: 75px;
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

.legend-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 180px;
}

.legend-image {
  display: block;
  max-width: 130px;
  max-height: 240px;
}

.map {
  height: calc(100% - 16px);
  background-color: white;
  padding: 0;
  border-radius: 8px;
  box-shadow: none;
  overflow: hidden;
  margin-top: 8px;
}

.map-selection-chip {
  position: absolute;
  right: 24px;
  bottom: 22px;
  z-index: 15;
  background: rgba(255, 255, 255, 0.96);
  color: #1e293b;
  border: 1px solid rgba(97, 136, 228, 0.18);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}

.chart-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 360px;
  /* 调整最小宽度 */
  max-width: 420px;
  /* 调整最大宽度 */
  height: 100%;
}

.chart {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 16px;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translate(-50%, -10px);
  }

  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.map-marker {
  position: absolute;
  width: 12px;
  height: 12px;
  background: #ff4444;
  border: 2px solid white;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: markerPulse 1.5s ease-in-out infinite;
  z-index: 10;
}

@keyframes markerPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(255, 68, 68, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(255, 68, 68, 0);
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

.compare-btn-wrapper.draw {
  right: 240px;
  top: 24px;
}
</style>

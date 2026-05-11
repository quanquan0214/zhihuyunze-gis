<template>
  <!-- 右侧内容区 -->
  <div class="content"> <!-- 主要内容区 -->
    <!-- 数据卡片区域 -->
    <div class="data-cards">
      <div class="card">
        <h3>水深平均值</h3>
        <div class="card-value deepth">
          <span class="value">{{ selectedData.depth }}</span>
          <span class="unit">m</span>
        </div>
      </div>
      <div class="card" area>
        <h3>水面面积</h3>
        <div class="card-value">
          <span class="value">{{ selectedData.area }}</span>
          <span class="unit">km²</span>
        </div>
      </div>
      <div class="card" storage>
        <h3>水储量</h3>
        <div class="card-value">
          <span class="value">{{ selectedData.volume }}</span>
          <span class="unit">亿m³</span>
        </div>
      </div>
      <div class="card">
        <h3>年降水量</h3>
        <div class="card-value">
          <span class="value">{{ selectedPrecipitation }}</span>
          <span class="unit">mm</span>
        </div>
      </div>
    </div>
    <div class="gis-summary-row">
      <div class="gis-summary-card">
        <span class="label">阶段</span>
        <strong>{{ currentPhaseLabel }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">年份</span>
        <strong>{{ selectedYear }}年</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">定位区域</span>
        <strong>{{ selectedRegionLabel }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">结果状态</span>
        <strong>{{ resultStatusLabel }}</strong>
      </div>
    </div>
    <main class="main">
      <!-- 地图和图表区域 -->
      <div class="map-area">
        <!-- 悬浮的时间选择区域 -->
        <div class="time-selector-float">
          <div class="year-select-bar">
            <label>水深选择年份：</label>
            <el-select v-model="selectedYear" style="width: 100px">
              <el-option v-for="item in yearOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <div class="time-phases">
            <div class="phase" v-for="(phase, idx) in phases" :key="phase" :class="{ active: selectedPhase === idx }"
              @click="selectedPhase = idx">
              <div class="phase-icon">
                <el-icon v-if="selectedPhase === idx">
                  <Check />
                </el-icon>
              </div>
              <span>{{ phase }}</span>
            </div>
          </div>
        </div>
        <div class="toolbar-export">
          <el-button-group>
            <el-button size="small" type="success" :disabled="!hasSpatialGeojson" @click="exportSpatialGeojson">导出空间</el-button>
            <el-button size="small" type="warning" :disabled="!hasSnapshot" @click="exportSnapshot">导出结果</el-button>
          </el-button-group>
        </div>
        <div class="analysis-status-panel">
          <div class="status-header">
            <span>水文GIS状态</span>
            <el-tag size="small" :type="selectedRegionCode ? 'success' : 'info'">{{ currentPhaseLabel }}</el-tag>
          </div>
          <div class="status-row">
            <span>阶段说明</span>
            <strong>{{ phaseDescription }}</strong>
          </div>
          <div class="status-row">
            <span>定位区域</span>
            <strong>{{ selectedRegionLabel }}</strong>
          </div>
          <div class="status-row">
            <span>当前水深</span>
            <strong>{{ selectedData.depth }} m</strong>
          </div>
          <div class="status-row">
            <span>当前水储量</span>
            <strong>{{ selectedData.volume }} 亿m³</strong>
          </div>
        </div>
        <div class="legend-panel">
          <div class="legend-title">{{ legendTitle }}</div>
          <img
            :src="legendUrl"
            :alt="legendTitle"
            class="legend-image"
            @error="onLegendError"
          />
        </div>
        <div v-if="selectedRegionLabel !== '未选择区域'" class="map-selection-chip">
          {{ selectedRegionLabel }}
        </div>
        <div class="map">
          <Basemap
            :layersConfig="mapConfig"
            :geojson="cityGeojsonOverlay"
            :legend-title="legendTitle"
            :show-layer-manager="false"
            @view-ready="onViewReady"
            @map-click="onMapClick"
          >
            <template #legend>
              <div class="legend-slot">
                <img
                  :src="legendUrl"
                  :alt="legendTitle"
                  class="legend-image"
                  @error="onLegendError"
                />
              </div>
            </template>
          </Basemap>
        </div>
      </div>
      <div class="chart-group">
        <div class="chart">
          <timechart :data="chartData"></timechart>
        </div>
        <div class="chart">
          <Deepchart :data="depthChartData"></Deepchart>
        </div>
      </div>
    </main>

  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted } from "vue";
import { Check } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import Basemap from "@/components/baseMap.vue";
import Timechart from "@/components/timechart.vue";
import Deepchart from "@/components/deepchart.vue";

// 水深等级名称
const depthLevelNames = ['极低', '低', '中', '高', '极高'];

// 阶段映射
const phases = ["上升期", "丰水期", "下降期", "枯水期"];
const phaseMap = ["up", "max", "down", "min"];
const selectedPhase = ref(0);

// 数据相关
const csvData = ref([]);
const depthLevelData = ref([]);
const yearOptions = ref([]);
const selectedYear = ref("2022");
const precipitationData = ref<{ year: number, value: string }[]>([]);
const cityGeojson = ref<any>(null);
const selectedRegionCode = ref("");
const selectedRegionName = ref("");

// 图层顺序缓存
const layerIds = ref<{[key: string]: number}>({});
const legendVariantIndex = ref(0);

// 监视年份和时期变化
watch([selectedYear, selectedPhase], async () => {
  console.log('切换到:', selectedYear.value, phaseMap[selectedPhase.value]);
  await updateMapLayer();
});

// 更新地图图层
const updateMapLayer = async () => {
  const year = Number(selectedYear.value);
  const phase = phaseMap[selectedPhase.value];
  
  console.log('正在切换图层:', year, phase);
  // 在这里添加断点或打印，以便调试
  
  const layerId = layerIds.value[`${year}_${phase}`];
  console.log('找到图层ID:', layerId);
  
  return layerId ?? 0;  // 如果找不到ID，默认显示第一个图层
};

function downloadTextFile(filename: string, content: string, mimeType = "application/json;charset=utf-8") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function loadCityRegions() {
  const res = await fetch("/src/assets/cityRegion.geojson");
  cityGeojson.value = await res.json();
}

// 读取CSV并解析
onMounted(async () => {
  // 读取水量数据
  const res = await fetch("/src/assets/Vol_revise.csv");
  const text = await res.text();
  const lines = text.trim().split("\n");
  const data = [];
  const yearSet = new Set();

  for (const line of lines) {
    const [key, depth, area, volume] = line.split(",");
    const match = key.match(/^NDWI_(\d{4})_(up|max|down|min)$/);
    if (match) {
      const year = match[1];
      const phase = match[2];
      data.push({
        year: Number(year),
        phase,
        depth,
        area,
        volume,
      });
      yearSet.add(year);
    }
  }
  csvData.value = data;

  // 读取水深等级数据
  const depthRes = await fetch("/src/assets/Depth_Level.csv");
  const depthText = await depthRes.text();
  const depthLines = depthText.trim().split("\n");
  depthLevelData.value = depthLines.map(line => {
    const [key, ...values] = line.split(",");
    const [, yearStr, phase] = key.match(/Depth_(\d{4})_(\w+)/);
    return {
      year: Number(yearStr),
      phase,
      values: values.map(v => parseFloat(v))
    };
  });

  // 读取年降水量数据
  const precipRes = await fetch("/src/assets/yearly_precipitation.csv");
  const precipText = await precipRes.text();
  const precipLines = precipText.trim().split("\n").slice(1); // 跳过表头
  precipitationData.value = precipLines.map(line => {
    const [year, value] = line.split(",");
    return { year: Number(year), value };
  });

  // 设置年份选项
  yearOptions.value = Array.from(yearSet)
    .sort((a, b) => Number(b) - Number(a))
    .map((y) => ({ value: y, label: `${y}年` }));

  // 默认选中最新年份
  if (yearOptions.value.length > 0) {
    selectedYear.value = yearOptions.value[0].value;
  }

  await loadCityRegions();
});

// 计算当前选中数据
const selectedData = computed(() => {
  const phaseKey = phaseMap[selectedPhase.value];
  return (
    csvData.value.find(
      (item) => item.year === Number(selectedYear.value) && item.phase === phaseKey
    ) || { depth: "-", area: "-", volume: "-" }
  );
});

// 计算水深等级图数据
const depthChartData = computed(() => {
  const phase = phaseMap[selectedPhase.value];
  const data = depthLevelData.value.find(
    item => item.year === Number(selectedYear.value) && item.phase === phase
  );

  if (data) {
    return data.values.map((value, index) => ({
      value,
      name: depthLevelNames[index]
    }));
  }
  return [];
});

// 计算 timechart 的数据：所有年份该时期的水储量
const chartData = computed(() => {
  const phaseKey = phaseMap[selectedPhase.value];
  return csvData.value
    .filter(item => item.phase === phaseKey)
    .sort((a, b) => a.year - b.year)
    .map(item => ({
      name: item.year + "年",
      value: Number(item.volume)
    }));
});

// 计算选中年份的降水量
const selectedPrecipitation = computed(() => {
  const year = Number(selectedYear.value);
  const found = precipitationData.value.find(item => item.year === year);
  return found ? found.value : "-";
});

const currentPhaseLabel = computed(() => phases[selectedPhase.value] ?? "未知阶段");
const phaseDescriptionMap: Record<string, string> = {
  up: "湖面扩张阶段，关注水深快速上升区。",
  max: "丰水位阶段，关注高水深与高水量分布。",
  down: "退水阶段，关注浅滩暴露与水量回落。",
  min: "枯水位阶段，关注低水深和敏感区域。"
};
const phaseDescription = computed(() => phaseDescriptionMap[phaseMap[selectedPhase.value]] ?? "阶段信息未定义");
const selectedRegionLabel = computed(() => selectedRegionName.value || "未选择区域");
const resultStatusLabel = computed(() => selectedData.value.depth !== "-" ? "已生成" : "待生成");
const legendTitle = computed(() => `水深图例 · ${selectedYear.value}年 · ${currentPhaseLabel.value}`);
const hasSnapshot = computed(() => selectedData.value.depth !== "-");
const hasSpatialGeojson = computed(() => !!cityGeojson.value?.features?.length);
const cityGeojsonOverlay = computed(() => cityGeojson.value);
const currentSnapshot = computed(() => ({
  year: Number(selectedYear.value),
  phase: phaseMap[selectedPhase.value],
  phase_label: currentPhaseLabel.value,
  phase_description: phaseDescription.value,
  region_code: selectedRegionCode.value || null,
  region_name: selectedRegionName.value || null,
  metrics: {
    depth: selectedData.value.depth,
    area: selectedData.value.area,
    volume: selectedData.value.volume,
    precipitation: selectedPrecipitation.value
  },
  depth_level_distribution: depthChartData.value,
  volume_series: chartData.value
}));

// 地图配置
const mapConfig = computed(() => {
  const year = Number(selectedYear.value);
  const phase = phaseMap[selectedPhase.value];
  const title = `predata:Depth_${year}_${phase}`;
  const currentLayerId = (() => {
    if (year === 2013) {
      switch (phase) {
        case 'up': return 0;
        case 'max': return 1;
        case 'down': return 2;
        case 'min': return 3;
      }
    }
    const yearOffset = (year - 2014) * 4;
    const baseIndex = 4;
    switch (phase) {
      case 'min': return baseIndex + yearOffset;
      case 'up': return baseIndex + yearOffset + 1;
      case 'max': return baseIndex + yearOffset + 2;
      case 'down': return baseIndex + yearOffset + 3;
      default: return -1;
    }
  })();

  return [{
    type: 'WMSLayer',
    url: '/geoserver/predata/wms',
    subLayers: [
      {
        title, // 新增，和服务一致
        visible: true
      }
    ]
  }];
});

const legendCandidates = computed(() => {
  const year = Number(selectedYear.value);
  const phase = phaseMap[selectedPhase.value];
  const layerCandidates = [`predata:Depth_${year}_${phase}`];
  const styleCandidates = ['', 'Depth_style', 'depth_style'];
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

function onViewReady() {}

function onMapClick(event: any) {
  if (!event?.attributes?.city_code) return;
  selectedRegionCode.value = String(event.attributes.city_code);
  selectedRegionName.value = String(event.attributes.city_name ?? event.attributes.name ?? event.attributes.city_code);
  ElMessage.success(`已定位区域：${selectedRegionName.value}`);
}

function exportSpatialGeojson() {
  if (!hasSpatialGeojson.value) {
    ElMessage.warning("当前没有可导出的空间图层");
    return;
  }

  downloadTextFile(
    `hydrology_regions_${selectedYear.value}_${phaseMap[selectedPhase.value]}.geojson`,
    JSON.stringify(cityGeojson.value, null, 2),
    "application/geo+json;charset=utf-8"
  );
  ElMessage.success("空间图层已导出");
}

function exportSnapshot() {
  if (!hasSnapshot.value) {
    ElMessage.warning("当前没有可导出的阶段结果");
    return;
  }

  downloadTextFile(
    `hydrology_snapshot_${selectedYear.value}_${phaseMap[selectedPhase.value]}.json`,
    JSON.stringify(currentSnapshot.value, null, 2)
  );
  ElMessage.success("阶段结果已导出");
}

function onLegendError() {
  if (legendVariantIndex.value < legendCandidates.value.length - 1) {
    legendVariantIndex.value += 1;
  }
}

watch([selectedYear, selectedPhase], () => {
  legendVariantIndex.value = 0;
});
</script>

<style scoped lang="less">
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow: hidden;
  background: #f5f6fa;
  padding: 15px 20px;
}

.gis-summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 0 4px 14px 4px;
}

.gis-summary-card {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.12), rgba(24, 144, 255, 0.04));
  border: 1px solid rgba(24, 144, 255, 0.18);
  border-radius: 10px;
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

.header {
  background-color: white;
  padding: 0 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background-color: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
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

.data-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin: 0 4px 15px 4px;
  padding: 0;
  height: 64px;
  align-items: center;
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
  align-items: flex-end;
}

.value {
  font-size: 20px;
  font-weight: 400;
  color: #1890ff;
}

.unit {
  margin-left: 8px;
  color: #888;
  font-size: 14px;
  margin-bottom: 2px;
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

.time-selector-float {
  position: absolute;
  top: 24px;
  right: 32px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  min-width: 150px;
  backdrop-filter: blur(8px);
}

.toolbar-export {
  position: absolute;
  right: 32px;
  top: 232px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
}

.analysis-status-panel {
  position: absolute;
  left: 24px;
  top: 24px;
  z-index: 10;
  width: 250px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px 14px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
}

.status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
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

.year-select-bar {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.year-select-bar label {
  font-size: 13px;
}

.year-select-bar .el-select {
  width: 100% !important;
}

.time-phases {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.phase {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 10px;
  transition: all 0.3s ease;
  border-radius: 6px;
  font-size: 13px;
}

.phase:hover {
  background: rgba(24, 144, 255, 0.1);
  transform: translateX(4px);
}

.phase.active {
  color: #1890ff;
  font-weight: 500;
  background: rgba(24, 144, 255, 0.15);
}

.phase-icon {
  width: 20px;
  height: 20px;
  margin-right: 8px;
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

.legend-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 180px;
}

.map-selection-chip {
  position: absolute;
  right: 24px;
  bottom: 24px;
  z-index: 12;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(24, 144, 255, 0.18);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  color: #1e293b;
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
</style>

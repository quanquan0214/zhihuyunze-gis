<template>
  <div class="map-container">
    <div ref="mapRef" class="map-root"></div>

    <div v-if="showLayerManager && layerStates.length" class="map-panel map-panel-layer">
      <div class="panel-header">
        <span>图层管理</span>
        <span class="panel-badge">{{ activeLayerCount }}/{{ layerStates.length }}</span>
      </div>
      <div class="layer-list">
        <div v-for="layer in layerStates" :key="layer.key" class="layer-item">
          <label class="layer-switch">
            <input v-model="layer.visible" type="checkbox">
            <span>{{ layer.title }}</span>
          </label>
          <div class="layer-opacity">
            <span>透明度</span>
            <input v-model.number="layer.opacity" max="1" min="0" step="0.05" type="range">
            <strong>{{ Math.round(layer.opacity * 100) }}%</strong>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCoordinates" class="map-panel map-panel-coord">
      <div class="panel-header">
        <span>坐标</span>
        <span class="panel-badge">GIS</span>
      </div>
      <div class="coord-line">
        <span>经度</span>
        <strong>{{ cursorCoordinate ? cursorCoordinate[0] : '--' }}</strong>
      </div>
      <div class="coord-line">
        <span>纬度</span>
        <strong>{{ cursorCoordinate ? cursorCoordinate[1] : '--' }}</strong>
      </div>
      <div class="coord-line">
        <span>缩放</span>
        <strong>{{ currentZoom }}</strong>
      </div>
    </div>

    <div v-if="shouldShowLegend" class="map-panel map-panel-legend">
      <div class="panel-header">
        <span>{{ legendTitle }}</span>
        <span class="panel-badge">Legend</span>
      </div>
      <slot name="legend">
        <div v-if="legendItems.length" class="legend-list">
          <div v-for="item in legendItems" :key="item.label" class="legend-item">
            <span class="legend-swatch" :style="{ backgroundColor: item.color }"></span>
            <span class="legend-label">{{ item.label }}</span>
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, useSlots, watch } from 'vue';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import ImageLayer from 'ol/layer/Image';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import ImageWMS from 'ol/source/ImageWMS';
import GeoJSON from 'ol/format/GeoJSON';
import { defaults as defaultControls, ScaleLine } from 'ol/control';
import { fromLonLat, toLonLat } from 'ol/proj';
import { Fill, Stroke, Style, Circle as CircleStyle } from 'ol/style';
import type { MapBrowserEvent } from 'ol';

interface SubLayerConfig {
  title?: string;
  visible?: boolean;
}

interface LayerConfig {
  id?: string;
  url: string;
  subLayers?: SubLayerConfig[];
  opacity?: number;
  visible?: boolean;
  params?: Record<string, unknown>;
}

interface LegendItem {
  label: string;
  color: string;
}

interface LayerState {
  key: string;
  title: string;
  visible: boolean;
  opacity: number;
  config: LayerConfig;
}

const props = withDefaults(defineProps<{
  layersConfig?: LayerConfig[];
  center?: [number, number];
  zoom?: number;
  geojson?: any;
  legendTitle?: string;
  legendItems?: LegendItem[];
  showLayerManager?: boolean;
  showCoordinates?: boolean;
}>(), {
  layersConfig: () => [],
  center: () => [116.25, 29.05] as [number, number],
  zoom: 9,
  legendTitle: '专题图例',
  legendItems: () => [],
  showLayerManager: true,
  showCoordinates: true
});

const emit = defineEmits<{
  (event: 'map-click', payload: { longitude: number; latitude: number; attributes?: Record<string, unknown> | null }): void;
  (event: 'view-ready', map: Map): void;
}>();

const slots = useSlots();
const mapRef = ref<HTMLDivElement | null>(null);
const cursorCoordinate = ref<[number, number] | null>(null);
const currentZoom = ref<number>(props.zoom ?? 9);
const layerStates = ref<LayerState[]>([]);

let mapInstance: Map | null = null;
let viewInstance: View | null = null;
let geojsonLayer: VectorLayer<VectorSource> | null = null;
let dynamicLayers: ImageLayer[] = [];
let resizeObserver: ResizeObserver | null = null;

const geojsonFormat = new GeoJSON();
const activeLayerCount = computed(() => layerStates.value.filter((layer) => layer.visible).length);
const shouldShowLegend = computed(() => !!slots.legend || props.legendItems.length > 0);

function getLayerTitle(config: LayerConfig) {
  if (!config.subLayers || config.subLayers.length === 0) return '';
  const visibleLayer = config.subLayers.find((subLayer) => subLayer.visible ?? true);
  return visibleLayer?.title ?? config.subLayers[0].title ?? '';
}

function getLayerKey(config: LayerConfig, index: number) {
  return String(config.id ?? config.params?.LAYERS ?? getLayerTitle(config) ?? config.url ?? index);
}

function syncLayerStates() {
  const previousState = new Map(layerStates.value.map((layer) => [layer.key, layer]));
  layerStates.value = props.layersConfig.map((config, index) => {
    const key = getLayerKey(config, index);
    const cached = previousState.get(key);
    return {
      key,
      title: getLayerTitle(config) || `图层 ${index + 1}`,
      visible: cached?.visible ?? config.visible ?? true,
      opacity: cached?.opacity ?? config.opacity ?? 1,
      config
    };
  });
}

function buildLayerFromConfig(config: LayerConfig) {
  if (!config?.url) return null;

  const layerName = (config.params?.LAYERS as string) ?? getLayerTitle(config);
  const params: Record<string, unknown> = {
    FORMAT: 'image/png',
    TRANSPARENT: true,
    ...(config.params ?? {})
  };

  if (layerName) {
    params.LAYERS = layerName;
  }

  return new ImageLayer({
    source: new ImageWMS({
      url: config.url,
      params,
      ratio: 1,
      serverType: 'geoserver'
    }),
    opacity: config.opacity ?? 1,
    visible: !!layerName,
    zIndex: 10
  });
}

function rebuildDynamicLayers() {
  if (!mapInstance) return;

  dynamicLayers.forEach((layer) => mapInstance?.removeLayer(layer));
  dynamicLayers = [];

  layerStates.value.forEach((state) => {
    const layer = buildLayerFromConfig(state.config);
    if (!layer) return;
    layer.setVisible(state.visible);
    layer.setOpacity(state.opacity);
    mapInstance?.addLayer(layer);
    dynamicLayers.push(layer);
  });
}

function applyLayerStateToMap() {
  dynamicLayers.forEach((layer, index) => {
    const state = layerStates.value[index];
    if (!state) return;
    layer.setVisible(state.visible);
    layer.setOpacity(state.opacity);
  });
}

function updateGeojsonLayer() {
  if (!geojsonLayer) return;

  if (!props.geojson || !props.geojson.type) {
    geojsonLayer.getSource()?.clear();
    return;
  }

  const features = geojsonFormat.readFeatures(props.geojson, {
    featureProjection: viewInstance?.getProjection() ?? 'EPSG:3857'
  });

  const source = geojsonLayer.getSource();
  source?.clear();
  source?.addFeatures(features);
}

function updateCursorCoordinate(coordinate: [number, number]) {
  cursorCoordinate.value = [
    Number(coordinate[0].toFixed(4)),
    Number(coordinate[1].toFixed(4))
  ];
}

function handleMapClick(event: MapBrowserEvent<any>) {
  if (!mapInstance) return;

  const [lon, lat] = toLonLat(event.coordinate);
  updateCursorCoordinate([lon, lat]);

  let attributes: Record<string, unknown> | null = null;
  mapInstance.forEachFeatureAtPixel(event.pixel, (feature) => {
    const featureProps = feature.getProperties();
    const { geometry, ...rest } = featureProps;
    attributes = (rest as any).properties ?? rest;
    return true;
  });

  emit('map-click', { longitude: lon, latitude: lat, attributes });
}

onMounted(() => {
  if (!mapRef.value) return;

  viewInstance = new View({
    center: fromLonLat(props.center),
    zoom: props.zoom
  });

  const baseLayer = new TileLayer({
    source: new OSM()
  });

  geojsonLayer = new VectorLayer({
    source: new VectorSource(),
    style: new Style({
      fill: new Fill({ color: 'rgba(255, 255, 255, 0.3)' }),
      stroke: new Stroke({ color: '#0075ff', width: 2 }),
      image: new CircleStyle({ radius: 5, fill: new Fill({ color: '#0075ff' }) })
    }),
    zIndex: 50
  });

  mapInstance = new Map({
    target: mapRef.value,
    layers: [baseLayer, geojsonLayer],
    view: viewInstance,
    controls: defaultControls({ attribution: false }).extend([
      new ScaleLine({ units: 'metric' })
    ])
  });

  mapInstance.on('singleclick', handleMapClick);
  mapInstance.on('pointermove', (event) => {
    if (event.dragging) return;
    const [lon, lat] = toLonLat(event.coordinate);
    updateCursorCoordinate([lon, lat]);
  });
  mapInstance.on('moveend', () => {
    const zoom = viewInstance?.getZoom();
    if (typeof zoom === 'number') {
      currentZoom.value = Number(zoom.toFixed(1));
    }
  });

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      mapInstance?.updateSize();
    });
    resizeObserver.observe(mapRef.value);
  }

  syncLayerStates();
  rebuildDynamicLayers();
  updateGeojsonLayer();
  currentZoom.value = typeof viewInstance.getZoom() === 'number'
    ? Number((viewInstance.getZoom() ?? props.zoom).toFixed(1))
    : props.zoom;

  emit('view-ready', mapInstance);
});

watch(
  () => props.layersConfig,
  () => {
    syncLayerStates();
    rebuildDynamicLayers();
  },
  { deep: true }
);

watch(
  layerStates,
  () => {
    applyLayerStateToMap();
  },
  { deep: true }
);

watch(
  () => props.geojson,
  () => {
    updateGeojsonLayer();
  },
  { deep: true }
);

watch(
  () => props.center,
  (center) => {
    if (!center || !viewInstance) return;
    viewInstance.setCenter(fromLonLat(center));
  },
  { deep: true }
);

watch(() => props.zoom, (zoom) => {
  if (typeof zoom === 'number' && viewInstance) {
    viewInstance.setZoom(zoom);
    currentZoom.value = Number(zoom.toFixed(1));
  }
});

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.un('singleclick', handleMapClick);
    mapInstance.setTarget(null);
  }

  if (resizeObserver && mapRef.value) {
    resizeObserver.unobserve(mapRef.value);
  }

  dynamicLayers = [];
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.map-root {
  width: 100%;
  height: 100%;
}

.map-panel {
  position: absolute;
  z-index: 80;
  background: rgba(10, 22, 40, 0.82);
  color: #eef6ff;
  border: 1px solid rgba(95, 158, 255, 0.28);
  border-radius: 12px;
  padding: 12px;
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.24);
}

.map-panel-layer {
  top: 12px;
  left: 12px;
  width: 260px;
}

.map-panel-coord {
  top: 12px;
  right: 12px;
  min-width: 160px;
}

.map-panel-legend {
  left: 12px;
  bottom: 12px;
  min-width: 180px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
}

.panel-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(64, 158, 255, 0.18);
  color: #8dc6ff;
  font-size: 12px;
}

.layer-list,
.legend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.layer-item {
  padding: 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
}

.layer-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  margin-bottom: 8px;
}

.layer-opacity {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.layer-opacity input {
  flex: 1;
}

.coord-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  margin-bottom: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.legend-swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex: 0 0 12px;
}
</style>

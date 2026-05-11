<template>
  <div class="map-container">
    <div ref="mapRef" class="map-root"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import ImageLayer from 'ol/layer/Image';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import ImageWMS from 'ol/source/ImageWMS';
import GeoJSON from 'ol/format/GeoJSON';
import { defaults as defaultControls } from 'ol/control';
import { fromLonLat, toLonLat } from 'ol/proj';
import { Fill, Stroke, Style, Circle as CircleStyle } from 'ol/style';
import type { MapBrowserEvent } from 'ol';

interface SubLayerConfig {
  title?: string;
  visible?: boolean;
}

interface LayerConfig {
  url: string;
  subLayers?: SubLayerConfig[];
  opacity?: number;
  params?: Record<string, unknown>;
}

const props = defineProps<{
  layersConfig: LayerConfig[];
  center?: [number, number];
  zoom?: number;
  geojson?: any;
}>();

const emit = defineEmits<{
  (event: 'map-click', payload: { longitude: number; latitude: number; attributes?: Record<string, unknown> | null }): void;
  (event: 'view-ready', map: Map): void;
}>();

const mapRef = ref<HTMLDivElement | null>(null);
let mapInstance: Map | null = null;
let viewInstance: View | null = null;
let geojsonLayer: VectorLayer<VectorSource> | null = null;
let dynamicLayers: ImageLayer[] = [];
let resizeObserver: ResizeObserver | null = null;
const geojsonFormat = new GeoJSON();
const defaultCenter: [number, number] = [116.25, 29.05];

function getLayerTitle(config: LayerConfig) {
  if (!config.subLayers || config.subLayers.length === 0) return '';
  const visibleLayer = config.subLayers.find(sl => sl.visible ?? true);
  return visibleLayer?.title ?? config.subLayers[0].title ?? '';
}

function buildLayerFromConfig(config: LayerConfig) {
  if (!config?.url) return null;

  const layerName = config.params?.LAYERS as string ?? getLayerTitle(config);
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

function applyLayerConfig() {
  if (!mapInstance) return;
  dynamicLayers.forEach(layer => mapInstance?.removeLayer(layer));
  dynamicLayers = [];

  props.layersConfig.forEach(config => {
    const layer = buildLayerFromConfig(config);
    if (layer) {
      mapInstance?.addLayer(layer);
      dynamicLayers.push(layer);
    }
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

function handleMapClick(event: MapBrowserEvent<any>) {
  if (!mapInstance) return;
  const [lon, lat] = toLonLat(event.coordinate);
  let attributes: Record<string, unknown> | null = null;
  mapInstance.forEachFeatureAtPixel(event.pixel, (feature) => {
    const props = feature.getProperties();
    const { geometry, ...rest } = props;
    attributes = (rest as any).properties ?? rest;
    return true;
  });
  emit('map-click', { longitude: lon, latitude: lat, attributes });
}

onMounted(() => {
  if (!mapRef.value) return;

  viewInstance = new View({
    center: fromLonLat(props.center ?? defaultCenter),
    zoom: props.zoom ?? 9
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
    controls: defaultControls({ attribution: false })
  });

  mapInstance.on('singleclick', handleMapClick);

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      mapInstance?.updateSize();
    });
    resizeObserver.observe(mapRef.value);
  }

  applyLayerConfig();
  updateGeojsonLayer();
  emit('view-ready', mapInstance);
});

watch(
  () => props.layersConfig,
  () => {
    applyLayerConfig();
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
}

.map-root {
  width: 100%;
  height: 100%;
}
</style>

<template>
  <div class="container">
    <div class="gis-summary-row">
      <div class="gis-summary-card">
        <span class="label">当前步骤</span>
        <strong>{{ steps[currentStep]?.label }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">分析区域</span>
        <strong>{{ activeRegionLabel }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">结果模型</span>
        <strong>{{ resolvedModelLabel }}</strong>
      </div>
      <div class="gis-summary-card">
        <span class="label">结果状态</span>
        <strong>{{ resultStatusLabel }}</strong>
      </div>
    </div>
   
    <div class="main-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 步骤指示器 -->
        <div class="process-indicator">
          <div
            v-for="(step, idx) in steps"
            :key="step.value"
            :class="['step', {active: currentStep===idx, completed: idx < currentStep, disabled: idx > currentStep}]"
            @click="idx <= currentStep && switchToStep(idx)"
          >
            <div class="step-circle">{{ idx+1 }}</div>
            <div class="step-label">{{ step.label }}</div>
          </div>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{width: ((currentStep)/(steps.length-1)*100)+'%'}"></div>
        </div>
        <!-- 地图区域 -->
        <div class="card map-section">
          <div class="map-container">
            <div class="map-toolbar">
              <button type="button" class="btn btn-secondary btn-sm" @click="exportMapGeojson" :disabled="!hasGeojsonResult">导出GeoJSON</button>
              <button type="button" class="btn btn-secondary btn-sm" @click="exportAnalysisJson" :disabled="!hasAnyAnalysis">导出分析JSON</button>
            </div>
            <div class="map-status-panel">
              <div class="status-head">
                <span>GIS状态</span>
                <strong>{{ resolvedModelLabel }}</strong>
              </div>
              <div class="status-line">
                <span>区域</span>
                <strong>{{ activeRegionLabel }}</strong>
              </div>
              <div class="status-line">
                <span>空间结果</span>
                <strong>{{ geojsonFeatureCountLabel }}</strong>
              </div>
              <div class="status-line">
                <span>主导因素</span>
                <strong>{{ mainFactorLabel }}</strong>
              </div>
            </div>
            <BaseMap
              style="flex: 1 1 auto; min-height: 360px; width: 100%; border-radius: 8px; border: 1px solid #e0e0e0;"
              :layers-config="layersConfig"
              :center="[115.9, 28.7]"
              :zoom="7"
              :geojson="displayGeojson"
              :legend-title="legendTitle"
              :legend-items="legendItems"
              @map-click="onMapClick"
              @view-ready="onViewReady"
            />
          </div>
          <div class="feature-info">
            <h3>地图结果属性</h3>
            <div v-if="featureInfoEntries.length" class="feature-grid">
              <div v-for="item in featureInfoEntries" :key="item.key" class="feature-item">
                <span>{{ item.key }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div v-else class="empty-tip">点击地图结果后显示属性摘要</div>
          </div>
        </div>
       
      </div>
      <!-- 右侧面板 -->
      <div class="right-panel">
        <!-- 步骤内容 -->
        <div v-for="(tab, idx) in tabs" :key="tab.value" class="step-content" :class="{active: currentStep===idx}">
          <div class="card">
            <div class="step-header">
              <h2 class="step-title">{{ tab.label }}</h2>
              <p class="step-description">{{ stepDescriptions[tab.value] }}</p>
            </div>
            <!-- 步骤表单内容 -->
            <template v-if="tab.value === 'preprocess'">
              <form @submit.prevent="onPreprocess">
                <div class="param-meaning">
                  <div class="param-item" v-for="item in preprocessNotes" :key="item.label">
                    <strong>{{ item.label }}</strong>
                    <span>{{ item.value }}</span>
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">分析年份</label>
                  <select class="form-select" v-model="preprocessForm.year">
                    <option v-for="y in years" :key="y" :value="y">{{ y }}年</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">目标区域</label>
                  <select class="form-select" v-model="preprocessForm.region">
                    <option v-for="c in regionOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">空间分辨率</label>
                  <select class="form-select" v-model="preprocessForm.res">
                    <option v-for="r in resOptions" :key="r" :value="r">{{ r }}</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">坐标系统</label>
                  <select class="form-select" v-model="preprocessForm.src">
                    <option value="WGS 1984">WGS 1984</option>
                    <option value="CGCS 2000">CGCS 2000</option>
                    <option value="other">其他坐标系</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">重采样方法</label>
                  <select class="form-select" v-model="preprocessForm.resuml">
                    <option v-for="m in resampleMethods" :key="m" :value="m">{{ m }}</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">上传区域文件（shp/geojson）</label>
                  <div class="file-upload">
                    <input type="file" multiple @change="onPreprocessFileChange" accept=".shp,.shx,.dbf,.prj,.geojson,.json">
                    <div class="file-upload-button">
                      <span>📁</span>
                      选择文件
                    </div>
                  </div>
                  <div class="file-upload-tip">支持单个 GeoJSON，或一次性选择同名的 `.shp + .shx + .dbf (+ .prj)` 文件组。</div>
                  <div v-if="selectedRegionFileNames.length" class="selected-file-list">
                    <span v-for="name in selectedRegionFileNames" :key="name" class="file-chip">{{ name }}</span>
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">自定义区域编码</label>
                  <input type="text" class="form-input" v-model="customRegionCode" placeholder="留空则根据文件名自动生成，如 CUSTOM_NC_01">
                </div>
                <div class="form-group">
                  <label class="form-label">自定义区域名称</label>
                  <input type="text" class="form-input" v-model="customRegionName" placeholder="例如：核心保护区 / 自定义研究区">
                </div>
                <div class="upload-action-row">
                  <button type="button" class="btn btn-secondary" @click="onUploadRegion" :disabled="!selectedRegionFiles.length">
                    上传并应用区域
                  </button>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="stepStatus[0]">
                  <span>🔄</span>
                  开始预处理
                </button>
              </form>
              <div class="summary-box" v-if="regionUploadRows.length">
                <div class="summary-title">自定义区域回显</div>
                <div class="summary-grid">
                  <div v-for="item in regionUploadRows" :key="item.label" class="summary-item">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div class="summary-box" v-if="preprocessSummaryRows.length">
                <div class="summary-title">预处理参数回显</div>
                <div class="summary-grid">
                  <div v-for="item in preprocessSummaryRows" :key="item.label" class="summary-item">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div class="response-area"><pre>{{ regionUploadResp }}</pre></div>
              <div class="response-area"><pre>{{ preprocessResp }}</pre></div>
            </template>
            <template v-else-if="tab.value === 'regression'">
              <form @submit.prevent="onRegression">
                <div class="form-group">
                  <label class="form-label">因变量</label>
                  <input type="text" class="form-input" v-model="regressionForm.dependent_var" placeholder="输入因变量名称">
                </div>
                <div class="form-group">
                  <label class="form-label">自变量选择</label>
                  <div class="checkbox-group">
                    <div class="checkbox-item" v-for="v in independentVars" :key="v.value">
                      <input type="checkbox" :id="'var-'+v.value" :value="v.value" v-model="regressionForm.independent_vars">
                      <label :for="'var-'+v.value">{{ v.label }}</label>
                    </div>
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">回归模型</label>
                  <select class="form-select" v-model="regressionForm.model">
                    <option value="best">自动选择最佳模型</option>
                    <option value="OLS">普通最小二乘法 (OLS)</option>
                    <option value="SLM">空间滞后模型 (SLM)</option>
                    <option value="SEM">空间误差模型 (SEM)</option>
                  </select>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="!stepStatus[0] || stepStatus[1]">
                  <span>📊</span>
                  执行回归分析
                </button>
              </form>
              <div class="summary-box" v-if="regressionSummaryRows.length">
                <div class="summary-title">回归结果摘要</div>
                <div class="summary-grid">
                  <div v-for="item in regressionSummaryRows" :key="item.label" class="summary-item">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div class="response-area"><pre>{{ regressionResp }}</pre></div>
            </template>
            <template v-else-if="tab.value === 'download'">
              <div class="summary-box" v-if="downloadSummaryRows.length">
                <div class="summary-title">结果交付清单</div>
                <div class="summary-grid">
                  <div v-for="item in downloadSummaryRows" :key="item.label" class="summary-item">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div style="display: grid; gap: 20px;">
                <div style="padding: 20px; border: 2px solid #e5e7eb; border-radius: 12px;">
                  <h4 style="margin-bottom: 15px; color: #374151;">空间数据文件</h4>
                  <form @submit.prevent="onDownload('shapefile')">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                      <div>
                        <label class="form-label">年份</label>
                        <input type="text" class="form-input" v-model="downloadForm.year">
                      </div>
                      <div>
                        <label class="form-label">区域</label>
                        <input type="text" class="form-input" v-model="downloadForm.region">
                      </div>
                    </div>
                    <div style="margin-bottom: 15px;">
                      <label class="form-label">模型类型</label>
                      <select class="form-select" v-model="downloadForm.model">
                        <option value="OLS">OLS</option>
                        <option value="SLM">SLM</option>
                        <option value="SEM">SEM</option>
                      </select>
                    </div>
                    <button type="submit" class="btn btn-primary" :disabled="!stepStatus[1]">
                      <span>📦</span>
                      下载Shapefile
                    </button>
                  </form>
                </div>
                <div style="padding: 20px; border: 2px solid #e5e7eb; border-radius: 12px;">
                  <h4 style="margin-bottom: 15px; color: #374151;">数据表格文件</h4>
                  <form @submit.prevent="onDownload('csv')">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                      <div>
                        <label class="form-label">年份</label>
                        <input type="text" class="form-input" v-model="downloadForm.year">
                      </div>
                      <div>
                        <label class="form-label">区域</label>
                        <input type="text" class="form-input" v-model="downloadForm.region">
                      </div>
                    </div>
                    <button type="submit" class="btn btn-primary">
                      <span>📋</span>
                      下载CSV文件
                    </button>
                  </form>
                </div>
              </div>
              <div class="response-area"><pre>{{ downloadResp }}{{ csvResp }}</pre></div>
            </template>
            <template v-else-if="tab.value === 'visualize'">
              <form @submit.prevent="onVisualize">
                <div class="form-group">
                  <label class="form-label">可视化年份</label>
                  <input type="text" class="form-input" v-model="visualizeForm.year" placeholder="输入年份">
                </div>
                <div class="form-group">
                  <label class="form-label">区域范围</label>
                  <input type="text" class="form-input" v-model="visualizeForm.region" placeholder="区域代码">
                </div>
                <div class="form-group">
                  <label class="form-label">选择模型结果</label>
                  <select class="form-select" v-model="visualizeForm.model">
                    <option value="OLS">OLS模型结果</option>
                    <option value="SLM">SLM模型结果</option>
                    <option value="SEM">SEM模型结果</option>
                  </select>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="!stepStatus[1]">
                  <span>🎨</span>
                  生成可视化地图
                </button>
                <button type="button" class="btn btn-secondary" style="margin-left: 12px;" @click="runMechanismAnalysis" :disabled="!stepStatus[1]">
                  生成机制解读
                </button>
              </form>
              <div class="summary-box" v-if="visualSummaryRows.length">
                <div class="summary-title">地图回显摘要</div>
                <div class="summary-grid">
                  <div v-for="item in visualSummaryRows" :key="item.label" class="summary-item">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div class="summary-box" v-if="analysisSummaryRows.length">
                <div class="summary-title">机制分析结论</div>
                <div class="summary-grid">
                  <div v-for="item in analysisSummaryRows" :key="item.label" class="summary-item">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div class="response-area"><pre>{{ visualizeResp }}</pre></div>
            </template>
            <div class="form-mask" v-if="currentStep < idx">
              <div class="mask-text">请先完成前置步骤</div>
            </div>
            <div class="step-btns">
              <button type="button" class="btn btn-secondary" @click="goToPrevStep" v-if="currentStep > 0">上一步</button>
              <button type="button" class="btn btn-primary" @click="goToNextStep" v-if="currentStep < steps.length-1">下一步</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import api from '@/utils/request'
import { computed, reactive, ref } from 'vue'
import BaseMap from '@/components/baseMap.vue'

const tabs = [
  { label: '数据预处理', value: 'preprocess' },
  { label: '空间回归分析', value: 'regression' },
  { label: '结果下载', value: 'download' },
  { label: '结果可视化', value: 'visualize' }
]
const stepDescriptions = {
  preprocess: '设置分析参数并准备数据源，为后续分析做准备',
  regression: '配置回归模型参数，执行空间统计分析',
  download: '下载分析结果和相关数据文件',
  visualize: '将分析结果以地图形式展示，支持交互式探索'
}
const currentTab = ref('preprocess')

const years = Array.from({length: 2023-2000+1}, (_,i)=>(2000+i).toString())
const resOptions = ['250m', '500m', '1000m', '2000m']
const cities = [
  { label: '南昌市', value: 'NC' },
  { label: '九江市', value: 'JJ' },
  { label: '景德镇市', value: 'JDZ' },
  { label: '抚州市', value: 'FZ' },
  { label: '上饶市', value: 'SR' },
  { label: '鹰潭市', value: 'YT' }
]
const customRegionOptions = ref([])
const selectedRegionFiles = ref([])
const customRegionCode = ref('')
const customRegionName = ref('')
const regionUploadResp = ref('')
const resampleMethods = [
  'nearest', 'bilinear', 'cubic', 'lanczos', 'average', 'mode', 'max', 'min', 'med', 'q1', 'q3', 'linear'
]
const independentVars = [
  { label: '土地利用', value: 'lucc_numeric' },
  { label: '温度', value: 'temperature' },
  { label: '降水', value: 'rainfall' },
  { label: '植被覆盖度', value: 'fvc' }
]

const preprocessForm = reactive({
  year: '2020',
  region: 'NC',
  res: '500m',
  src: 'WGS 1984',
  resuml: 'linear',
  file: null
})
const preprocessResp = ref('')
const regressionForm = reactive({
  year: '2020',
  region: 'NC',
  model: 'best',
  dependent_var: 'rsei',
  independent_vars: []
})
const regressionResp = ref('')
const downloadForm = reactive({ year: '2020', region: 'NC', model: 'OLS' })
const downloadResp = ref('')
const csvResp = ref('')
const visualizeForm = reactive({ year: '2020', region: 'NC', model: 'OLS' })
const visualizeResp = ref('')
const geojsonData = ref(null)
const selectedFeature = ref(null)
const mechanismAnalysis = ref(null)
const preprocessedPayload = ref(null)
const regressionPayload = ref(null)
const preprocessResultMeta = ref(null)
const regressionResolvedModel = ref('')
const exportRegionGeojson = ref(null)
const uploadedRegionMeta = ref(null)
const uploadedRegionGeojson = ref(null)

const steps = [
  { label: '数据预处理', value: 'preprocess' },
  { label: '空间回归分析', value: 'regression' },
  { label: '结果下载', value: 'download' },
  { label: '结果可视化', value: 'visualize' }
]
const currentStep = ref(0)
const stepStatus = reactive([false, false, false, false])

function onViewReady() {}
const layersConfig = []

const regionOptions = computed(() => [...cities, ...customRegionOptions.value])
const modelLabelMap = {
  best: '自动选择最佳模型',
  OLS: '普通最小二乘法 (OLS)',
  SLM: '空间滞后模型 (SLM)',
  SEM: '空间误差模型 (SEM)'
}
const factorLabelMap = {
  lucc_numeric: '土地利用',
  temperature: '温度',
  rainfall: '降水',
  fvc: '植被覆盖度',
  rsei: 'RSEI',
  x: '经度',
  y: '纬度',
  resid_class: '残差等级',
  std_resid: '标准残差',
  predicted: '预测值',
  residuals: '残差'
}
const legendClassItems = [
  { label: '极低残差 (≤ -3)', color: '#08306b' },
  { label: '较低残差 (-3 ~ -2)', color: '#2171b5' },
  { label: '偏低残差 (-2 ~ -1)', color: '#6baed6' },
  { label: '中等残差 (-1 ~ 1)', color: '#f7f7f7' },
  { label: '偏高残差 (1 ~ 2)', color: '#fdae6b' },
  { label: '较高残差 (2 ~ 3)', color: '#fb6a4a' },
  { label: '极高残差 (≥ 3)', color: '#cb181d' }
]

function formatValue(value) {
  if (value === null || value === undefined || value === '') return '--'
  if (Array.isArray(value)) return value.map((item) => formatValue(item)).join(', ')
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(4)))
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch (error) {
      return String(value)
    }
  }
  return String(value)
}

function displayFactorName(name) {
  return factorLabelMap[name] || name || '--'
}

function sanitizeRegionCode(value) {
  return String(value || '')
    .toUpperCase()
    .replace(/[^A-Z0-9_]/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 24)
}

function getSelectedFileList(files) {
  return Array.from(files || [])
}

function getUploadedRegionCode() {
  const firstFile = selectedRegionFiles.value[0]
  const baseName = firstFile?.name ? firstFile.name.replace(/\.[^.]+$/, '') : ''
  const raw = customRegionCode.value || baseName || `CUSTOM_${Date.now().toString().slice(-6)}`
  return sanitizeRegionCode(raw) || `CUSTOM_${Date.now().toString().slice(-6)}`
}

function getUploadedRegionName() {
  const firstFile = selectedRegionFiles.value[0]
  const baseName = firstFile?.name ? firstFile.name.replace(/\.[^.]+$/, '') : ''
  return (customRegionName.value || baseName || getUploadedRegionCode()).trim()
}

const displayGeojson = computed(() => geojsonData.value || uploadedRegionGeojson.value)
const selectedRegionFileNames = computed(() => selectedRegionFiles.value.map((file) => file.name))
const activeRegionLabel = computed(() => regionOptions.value.find((item) => item.value === preprocessForm.region)?.label || preprocessForm.region || '--')
const resolvedModelLabel = computed(() => modelLabelMap[regressionResolvedModel.value || regressionForm.model] || (regressionResolvedModel.value || regressionForm.model || '--'))
const hasGeojsonResult = computed(() => geojsonData.value?.type === 'FeatureCollection' && Array.isArray(geojsonData.value.features))
const hasAnyAnalysis = computed(() => !!(preprocessedPayload.value || regressionPayload.value || mechanismAnalysis.value || hasGeojsonResult.value || uploadedRegionMeta.value))
const geojsonFeatureCountLabel = computed(() => {
  if (hasGeojsonResult.value) return `${geojsonData.value.features.length} 个要素`
  if (uploadedRegionGeojson.value?.type === 'FeatureCollection' && Array.isArray(uploadedRegionGeojson.value.features)) {
    return `${uploadedRegionGeojson.value.features.length} 个边界要素`
  }
  return '未生成'
})
const mainFactorLabel = computed(() => {
  const factor = mechanismAnalysis.value?.main_conclusion?.primary_influence_factor
  return displayFactorName(factor)
})
const resultStatusLabel = computed(() => {
  if (mechanismAnalysis.value) return '机制分析完成'
  if (hasGeojsonResult.value) return '空间结果已生成'
  if (regressionPayload.value) return '回归完成'
  if (preprocessedPayload.value) return '预处理完成'
  if (uploadedRegionMeta.value) return '自定义区域已加载'
  return '待开始'
})
const legendTitle = computed(() => (hasGeojsonResult.value ? '标准化残差分级' : '空间分析图例'))
const legendItems = computed(() => (hasGeojsonResult.value ? legendClassItems : []))
const preprocessNotes = computed(() => [
  { label: '分析年份', value: `${preprocessForm.year} 年` },
  { label: '目标区域', value: activeRegionLabel.value },
  { label: '区域来源', value: uploadedRegionMeta.value?.source_type ? (uploadedRegionMeta.value.source_type === 'geojson' ? 'GeoJSON' : 'Shapefile') : '预设区域' },
  { label: '空间分辨率', value: `${preprocessResultMeta.value?.resolution || preprocessForm.res}` },
  { label: '坐标系统', value: preprocessResultMeta.value?.coordinate_system || preprocessForm.src },
  { label: '重采样', value: preprocessResultMeta.value?.reclass_method || preprocessForm.resuml }
])
const regionUploadRows = computed(() => {
  if (!uploadedRegionMeta.value) return []
  return [
    { label: '区域编码', value: uploadedRegionMeta.value.region_code || '--' },
    { label: '区域名称', value: uploadedRegionMeta.value.region_name || '--' },
    { label: '文件类型', value: uploadedRegionMeta.value.source_type === 'geojson' ? 'GeoJSON' : 'Shapefile' },
    { label: '边界要素', value: uploadedRegionMeta.value.geojson?.features?.length || 0 }
  ]
})
const preprocessSummaryRows = computed(() => {
  if (!preprocessResp.value) return []
  return [
    { label: '年份', value: `${preprocessForm.year} 年` },
    { label: '区域', value: activeRegionLabel.value },
    { label: '区域编码', value: preprocessForm.region },
    { label: '分辨率', value: preprocessResultMeta.value?.resolution || preprocessForm.res },
    { label: '坐标系', value: preprocessResultMeta.value?.coordinate_system || preprocessForm.src },
    { label: '重采样', value: preprocessResultMeta.value?.reclass_method || preprocessForm.resuml },
    { label: '返回行数', value: Array.isArray(preprocessedPayload.value) ? preprocessedPayload.value.length : 0 }
  ]
})
const regressionSummaryRows = computed(() => {
  const bestModel = regressionPayload.value?.best_model || {}
  if (!regressionResp.value) return []
  return [
    { label: '模型', value: resolvedModelLabel.value },
    { label: 'R²', value: formatValue(bestModel.r_squared) },
    { label: '因变量', value: displayFactorName(bestModel.parameters?.dependent) },
    { label: '自变量', value: Array.isArray(bestModel.parameters?.independent) ? bestModel.parameters.independent.map(displayFactorName).join('、') : '--' },
    { label: '样本量', value: formatValue(bestModel.diagnostics?.sample_size) }
  ]
})
const downloadSummaryRows = computed(() => {
  if (!regressionPayload.value) return []
  return [
    { label: '当前模型', value: resolvedModelLabel.value },
    { label: '输出年份', value: `${downloadForm.year} 年` },
    { label: '输出区域', value: activeRegionLabel.value },
    { label: '空间文件', value: 'Shapefile' },
    { label: '表格文件', value: 'CSV' }
  ]
})
const visualSummaryRows = computed(() => {
  if (!hasGeojsonResult.value) return []
  return [
    { label: '输出模型', value: resolvedModelLabel.value },
    { label: '年份', value: `${visualizeForm.year} 年` },
    { label: '区域', value: activeRegionLabel.value },
    { label: '要素数量', value: geojsonFeatureCountLabel.value },
    { label: '图例', value: legendTitle.value }
  ]
})
const analysisSummaryRows = computed(() => {
  const analysis = mechanismAnalysis.value
  if (!analysis?.main_conclusion) return []
  const factors = analysis.factors_analysis || {}
  const sortedFactors = Object.entries(factors)
    .sort((a, b) => (Number(b[1]?.abs_mean || 0) - Number(a[1]?.abs_mean || 0)))
    .slice(0, 3)
    .map(([name, stats]) => `${displayFactorName(name)} (${formatValue(stats?.abs_mean)})`)
    .join('、')
  return [
    { label: '主导因素', value: displayFactorName(analysis.main_conclusion.primary_influence_factor) },
    { label: '影响强度', value: formatValue(analysis.main_conclusion.influence_strength) },
    { label: '分析精度', value: `${Number((Number(analysis.main_conclusion.precision || 0) * 100).toFixed(2))}%` },
    { label: '机制解读', value: analysis.main_conclusion.interpretation || '--' },
    { label: 'Top3 因子', value: sortedFactors || '--' }
  ]
})
const featureInfoEntries = computed(() => {
  const attrs = selectedFeature.value
  if (!attrs || typeof attrs !== 'object') return []

  const preferredOrder = ['name', 'id', 'region', 'year', 'rsei', 'predicted', 'residuals', 'std_resid', 'resid_class', 'x', 'y']
  return Object.entries(attrs)
    .filter(([key]) => key !== 'geometry')
    .sort((a, b) => {
      const ai = preferredOrder.indexOf(a[0])
      const bi = preferredOrder.indexOf(b[0])
      const av = ai === -1 ? preferredOrder.length : ai
      const bv = bi === -1 ? preferredOrder.length : bi
      return av - bv
    })
    .slice(0, 10)
    .map(([key, value]) => ({
      key: displayFactorName(key),
      value: formatValue(value)
    }))
})

function downloadTextFile(filename, content, mimeType = 'application/json;charset=utf-8') {
  const blob = new Blob([content], { type: mimeType })
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  window.URL.revokeObjectURL(url)
}

function resetResultState() {
  stepStatus[1] = false
  stepStatus[2] = false
  stepStatus[3] = false
  regressionResp.value = ''
  downloadResp.value = ''
  csvResp.value = ''
  visualizeResp.value = ''
  mechanismAnalysis.value = null
  regressionPayload.value = null
  geojsonData.value = null
  exportRegionGeojson.value = null
  selectedFeature.value = null
  regressionResolvedModel.value = ''
}

function resetPreprocessState() {
  stepStatus[0] = false
  preprocessResp.value = ''
  preprocessedPayload.value = null
  preprocessResultMeta.value = null
}

function exportMapGeojson() {
  const payload = exportRegionGeojson.value || geojsonData.value
  if (!payload) return
  downloadTextFile('机制分析结果.geojson', JSON.stringify(payload, null, 2), 'application/geo+json;charset=utf-8')
}

function exportAnalysisJson() {
  const payload = {
    preprocess: {
      form: { ...preprocessForm },
      meta: preprocessResultMeta.value,
      data: preprocessedPayload.value
    },
    uploadedRegion: {
      meta: uploadedRegionMeta.value,
      previewGeojson: uploadedRegionGeojson.value
    },
    regression: regressionPayload.value,
    visualization: exportRegionGeojson.value,
    mechanism: mechanismAnalysis.value,
    selectedFeature: selectedFeature.value,
    exportedAt: new Date().toISOString()
  }
  downloadTextFile('机制分析汇总.json', JSON.stringify(payload, null, 2))
}

function onPreprocessFileChange(e) {
  const files = getSelectedFileList(e.target.files)
  selectedRegionFiles.value = files
  preprocessForm.file = files[0] || null
  regionUploadResp.value = ''
  uploadedRegionMeta.value = null
  uploadedRegionGeojson.value = null
}

async function onUploadRegion(options = {}) {
  try {
    if (!selectedRegionFiles.value.length) {
      throw new Error('请先选择区域文件')
    }

    const fileMap = Object.fromEntries(selectedRegionFiles.value.map((file) => {
      const ext = file.name.split('.').pop()?.toLowerCase() || ''
      return [ext, file]
    }))
    const regionCode = getUploadedRegionCode()
    const regionName = getUploadedRegionName()
    const formData = new FormData()
    formData.append('region_code', regionCode)
    formData.append('region_name', regionName)

    if (fileMap.geojson || fileMap.json) {
      formData.append('geojson_file', fileMap.geojson || fileMap.json)
    } else {
      if (!fileMap.shp || !fileMap.shx || !fileMap.dbf) {
        throw new Error('Shapefile 上传至少需要同时选择 .shp、.shx、.dbf 文件')
      }
      formData.append('shp_file', fileMap.shp)
      formData.append('shx_file', fileMap.shx)
      formData.append('dbf_file', fileMap.dbf)
      if (fileMap.prj) formData.append('prj_file', fileMap.prj)
    }

    const data = await api.post('/api/upload/region', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    uploadedRegionMeta.value = data
    uploadedRegionGeojson.value = data.geojson || null
    regionUploadResp.value = JSON.stringify(data, null, 2)
    selectedFeature.value = null
    resetPreprocessState()
    resetResultState()

    const option = {
      label: data.region_name || regionName,
      value: data.region_code || regionCode
    }
    const existingIndex = customRegionOptions.value.findIndex((item) => item.value === option.value)
    if (existingIndex === -1) customRegionOptions.value = [...customRegionOptions.value, option]
    else customRegionOptions.value[existingIndex] = option

    preprocessForm.region = option.value
    regressionForm.region = option.value
    downloadForm.region = option.value
    visualizeForm.region = option.value

    if (!options.silent) {
      currentStep.value = 0
      currentTab.value = tabs[0].value
    }

    return data
  } catch (e) {
    const message = e?.response?.data?.message || e?.message || String(e)
    regionUploadResp.value = message
    throw e
  }
}

async function onPreprocess() {
  try {
    if (selectedRegionFiles.value.length) {
      await onUploadRegion({ silent: true })
    } else {
      resetResultState()
    }
    const payload = {
      year: preprocessForm.year,
      region: preprocessForm.region,
      res: preprocessForm.res,
      src: preprocessForm.src,
      resuml: preprocessForm.resuml
    }
    const data = await api.post('/api/preprocess', payload, {
      headers: { 'Content-Type': 'application/json' },
      transformRequest: [(data) => JSON.stringify(data)]
    })
    preprocessResp.value = JSON.stringify(data, null, 2)
    preprocessedPayload.value = data.data || null
    preprocessResultMeta.value = data.parameters || null
    // 同步到后续步骤的表单
    regressionForm.year = payload.year
    regressionForm.region = payload.region
    downloadForm.year = payload.year
    downloadForm.region = payload.region
    visualizeForm.year = payload.year
    visualizeForm.region = payload.region
    downloadForm.model = regressionForm.model === 'best' ? 'OLS' : regressionForm.model
    visualizeForm.model = regressionForm.model === 'best' ? 'OLS' : regressionForm.model
    stepStatus[0] = true
    currentStep.value = 1
    currentTab.value = tabs[1].value
  } catch (e) {
    preprocessResp.value = e?.response?.data?.message || e?.message || String(e)
  }
}
async function onRegression() {
  try {
    resetResultState()
    stepStatus[0] = true
    if (regressionForm.independent_vars.length === 0) {
      regressionForm.independent_vars = ['lucc_numeric', 'temperature', 'rainfall', 'fvc'];
    }

    const payload = {
      year: regressionForm.year,
      region: regressionForm.region,
      model: regressionForm.model,
      dependent_var: regressionForm.dependent_var || 'rsei',
      independent_vars: regressionForm.independent_vars
    }

    const data = await api.post('/api/spatial-regression', payload, {
      headers: { 'Content-Type': 'application/json' }
    })
    regressionResp.value = JSON.stringify(data, null, 2)
    regressionPayload.value = data
    const resolvedModel = data?.best_model?.type || payload.model
    regressionResolvedModel.value = resolvedModel
    downloadForm.model = resolvedModel
    visualizeForm.model = resolvedModel
    stepStatus[1] = true
    currentStep.value = 2
    currentTab.value = tabs[2].value
  } catch (e) {
    console.error('Regression error:', e);
    regressionResp.value = e?.response?.data?.message || e?.message || String(e)
  }
}
async function onDownload(type) {
  try {
    const resolvedModel = regressionResolvedModel.value || downloadForm.model
    if(type==='shapefile') {
      const { year, region } = downloadForm;
      const res = await api.get(`/api/download-shapefile?year=${year}&region=${region}&model=${resolvedModel}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(res)
      const a = document.createElement('a')
      a.href = url
      a.download = `${resolvedModel}_results.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      downloadResp.value = 'Shapefile下载成功'
    } else {
      const { year, region } = downloadForm;
      const res = await api.get(`/api/download-csv?year=${year}&region=${region}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(res)
      const a = document.createElement('a')
      a.href = url
      a.download = `result_${year}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      csvResp.value = 'CSV下载成功'
    }
  } catch (e) {
    if(type==='shapefile') downloadResp.value = e?.message || String(e)
    else csvResp.value = e?.message || String(e)
  }
}
async function onVisualize() {
  try {
    const model = regressionResolvedModel.value || visualizeForm.model
    visualizeForm.model = model
    const { year, region } = visualizeForm;
    const data = await api.get(`/api/results/visualize?year=${year}&region=${region}&model=${model}`)
    visualizeResp.value = JSON.stringify(data, null, 2)
    mechanismAnalysis.value = null
    selectedFeature.value = null
    stepStatus[2] = true
    stepStatus[3] = true
    currentStep.value = 3
    currentTab.value = tabs[3].value
    const geo = data.geojson || data;
    if (geo && geo.type === 'FeatureCollection' && Array.isArray(geo.features)) {
      geo.features.forEach((feature) => {
        const properties = feature.properties || {}
        const value = Number.parseFloat(properties.std_resid)
        if (Number.isNaN(value)) properties.resid_class = '4'
        else if (value < -3) properties.resid_class = '1'
        else if (value < -2) properties.resid_class = '2'
        else if (value < -1) properties.resid_class = '3'
        else if (value < 1) properties.resid_class = '4'
        else if (value < 2) properties.resid_class = '5'
        else if (value < 3) properties.resid_class = '6'
        else properties.resid_class = '7'
        feature.properties = properties
      })
      geojsonData.value = geo;
      exportRegionGeojson.value = geo
    } else {
      geojsonData.value = null;
      visualizeResp.value += '\n[未检测到标准GeoJSON，无法渲染地图]';
    }
  } catch (e) {
    visualizeResp.value = e?.message || String(e)
  }
}
async function runMechanismAnalysis() {
  try {
    const payload = {
      year: visualizeForm.year,
      region: visualizeForm.region
    }
    const data = await api.post('/api/SRanalysis', payload, {
      headers: { 'Content-Type': 'application/json' }
    })
    mechanismAnalysis.value = data
    const current = visualizeResp.value ? `${visualizeResp.value}\n\n` : ''
    visualizeResp.value = `${current}${JSON.stringify(data, null, 2)}`
  } catch (e) {
    const message = e?.response?.data?.message || e?.message || String(e)
    visualizeResp.value = `${visualizeResp.value}\n\n机制分析失败：${message}`
  }
}
function onMapClick(event) {
  if (event && event.attributes) {
    selectedFeature.value = event.attributes
  } else {
    selectedFeature.value = null
  }
}
function goToNextStep() {
  if(currentStep.value < steps.length-1) {
    currentStep.value++;
    currentTab.value = tabs[currentStep.value].value;
  }
}
function goToPrevStep() {
  if(currentStep.value > 0) {
    currentStep.value--;
    currentTab.value = tabs[currentStep.value].value;
  }
}
function switchToStep(idx) {
  currentStep.value = idx
  currentTab.value = tabs[idx].value
}
</script>

<style scoped>
/* 复制 login/1.html 的 <style> 内容到这里，覆盖原有样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: #2d3748;
}
.container {
  max-width: 100vw;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}
.gis-summary-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.gis-summary-card {
  padding: 18px 20px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(49, 130, 206, 0.92) 0%, rgba(37, 99, 235, 0.92) 100%);
  color: #fff;
  box-shadow: 0 16px 30px rgba(37, 99, 235, 0.22);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.gis-summary-card .label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.78);
}
.gis-summary-card strong {
  font-size: 1.05rem;
}
.header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}
.header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
.header p {
  font-size: 1.1rem;
  opacity: 0.9;
}
.main-content {
  display: grid;
  grid-template-columns: 2.5fr 1fr;
  gap: 30px;
  height: calc(100vh - 120px);
}
.left-panel, .right-panel {
  height: 100%;
  min-height: 0;
}
.left-panel {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
}
.right-panel {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  overflow-y: auto;
}
.process-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  position: relative;
}
.process-indicator::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 40px;
  right: 40px;
  height: 2px;
  background: #e2e8f0;
  z-index: 1;
}
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  cursor: pointer;
  transition: all 0.3s ease;
}
.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #a0aec0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}
.step.active .step-circle {
  background: #6188e4;
  color: white;
  transform: scale(1.1);
}
.step.completed .step-circle {
  background: #10b981;
  color: white;
}
.step.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.step-label {
  font-size: 0.85rem;
  font-weight: 500;
  text-align: center;
  color: #64748b;
  transition: color 0.3s ease;
}
.step.active .step-label {
  color: #4666e5;
  font-weight: 600;
}
.map-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}
.map-container {
  flex: 1;
  background: #f8fafc;
  border-radius: 15px;
  border: 1px solid #dbeafe;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  position: relative;
  overflow: hidden;
  min-height: 0;
}
.map-toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.map-status-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #eef2ff 100%);
  border: 1px solid #c7d2fe;
}
.status-head {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #1e3a8a;
  font-weight: 700;
}
.status-line {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.78);
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #475569;
}
.status-line strong {
  color: #0f172a;
}
.feature-info {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 20px;
  min-height: 120px;
}
.feature-info h3 {
  color: #1e293b;
  margin-bottom: 15px;
  font-size: 1.1rem;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.feature-item {
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #dbeafe;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.feature-item span {
  color: #64748b;
  font-size: 0.82rem;
}
.feature-item strong {
  color: #0f172a;
  word-break: break-word;
}
.empty-tip {
  color: #64748b;
  font-size: 0.92rem;
}
.step-content {
  display: none;
  animation: fadeIn 0.3s ease;
}
.step-content.active {
  display: block;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.step-header {
  margin-bottom: 25px;
}
.step-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}
.step-description {
  color: #64748b;
  font-size: 0.95rem;
  line-height: 1.5;
}
.form-group {
  margin-bottom: 20px;
}
.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 0.9rem;
}
.form-input, .form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: white;
}
.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #4651e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}
.file-upload {
  position: relative;
  display: inline-block;
  width: 100%;
}
.file-upload input[type="file"] {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}
.file-upload-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  border: 2px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  color: #64748b;
  transition: all 0.3s ease;
  cursor: pointer;
}
.file-upload-button:hover {
  border-color: #4f46e5;
  background: #f0f4ff;
  color: #4f46e5;
}
.file-upload-tip {
  margin-top: 10px;
  color: #64748b;
  font-size: 0.82rem;
  line-height: 1.5;
}
.selected-file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.file-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.8rem;
  border: 1px solid #bfdbfe;
}
.upload-action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 8px;
}
.checkbox-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.checkbox-item:hover {
  border-color: #4666e5;
  background: #f0f4ff;
}
.checkbox-item input[type="checkbox"] {
  margin-right: 8px;
  width: 16px;
  height: 16px;
}
.checkbox-item.checked {
  border-color: #4676e5;
  background: #f0f4ff;
  color: #4683e5;
}
.btn {
  padding: 14px 28px;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-primary {
  background: linear-gradient(135deg, #6188e4 0%, #3a8bed 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
}
.btn-secondary {
  background: #f1f5f9;
  color: #64748b;
  border: 2px solid #e2e8f0;
}
.btn-secondary:hover {
  background: #e2e8f0;
  color: #475569;
}
.btn-sm {
  padding: 9px 14px;
  font-size: 0.85rem;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}
.response-area {
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  border-left: 4px solid #c6dff4;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.85rem;
  max-height: 200px;
  overflow-y: auto;
}
.response-area pre {
  white-space: pre-wrap;
  word-break: break-word;
}
.response-area:empty {
  display: none;
}
.param-meaning {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.param-item {
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
  border: 1px solid #dbeafe;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.param-item strong {
  color: #1d4ed8;
  font-size: 0.88rem;
}
.param-item span {
  color: #475569;
  font-size: 0.88rem;
  line-height: 1.5;
}
.summary-box {
  margin-top: 18px;
  padding: 16px;
  border-radius: 16px;
  background: #f8fbff;
  border: 1px solid #dbeafe;
}
.summary-title {
  margin-bottom: 12px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e3a8a;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}
.summary-item {
  padding: 12px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.summary-item span {
  color: #64748b;
  font-size: 0.82rem;
}
.summary-item strong {
  color: #0f172a;
  word-break: break-word;
}
.progress-bar {
  width: 100%;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  margin: 20px 0;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4669e5, #3a49ed);
  width: 0%;
  transition: width 0.3s ease;
}
.status-success {
  color: #10b981;
  background: #ecfdf5;
  border-color: #10b981;
}
.status-error {
  color: #ef4444;
  background: #fef2f2;
  border-color: #ef4444;
}
@media (max-width: 1024px) {
  .gis-summary-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(520px, 56vh) 1fr;
    height: auto;
  }
  .process-indicator {
    flex-wrap: wrap;
    gap: 15px;
  }
  .step {
    flex: 1;
    min-width: 80px;
  }
  .left-panel, .right-panel {
    height: auto;
  }
}
@media (max-width: 768px) {
  .container {
    padding: 15px;
  }
  .gis-summary-row {
    grid-template-columns: 1fr;
  }
  .header h1 {
    font-size: 2rem;
  }
  .left-panel, .right-panel {
    padding: 20px;
  }
  .map-status-panel,
  .summary-grid,
  .param-meaning,
  .feature-grid {
    grid-template-columns: 1fr;
  }
}
.card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(79,70,229,0.07);
  padding: 28px 24px 20px 24px;
  position: relative;
  margin-bottom: 18px;
}
.form-mask {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.7);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  color: #467be5;
  border-radius: 16px;
  pointer-events: all;
}
.step-btns {
  display: flex;
  justify-content: space-between;
  margin-top: 18px;
}
@media (max-width: 768px) {
  .process-indicator {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .step {
    flex-direction: row;
    align-items: center;
  }
}
</style>

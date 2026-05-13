<template>
  <div class="analysis-page">
    <section class="hero-card">
      <div class="hero-main">
        <span class="hero-badge">GIS Mechanism</span>
        <h1>空间回归机制分析</h1>
        <p>
          以“研究区边界、栅格预处理、空间回归、结果落图、机制解读”五个动作组织页面。
          地图是主工作区，右侧只保留流程控制和必要参数。
        </p>
      </div>
      <div class="hero-stats">
        <div class="hero-stat">
          <span>当前步骤</span>
          <strong>{{ activeTab.label }}</strong>
        </div>
        <div class="hero-stat">
          <span>研究区域</span>
          <strong>{{ activeRegionLabel }}</strong>
        </div>
        <div class="hero-stat">
          <span>分析模型</span>
          <strong>{{ resolvedModelLabel }}</strong>
        </div>
        <div class="hero-stat">
          <span>结果状态</span>
          <strong>{{ resultStatusLabel }}</strong>
        </div>
      </div>
    </section>

    <div class="page-grid">
      <section class="workspace-column">
        <div class="workspace-card">
          <div class="section-head">
            <div>
              <h2>空间分析视图</h2>
              <p>左侧只承担地图、要素查询和当前结果的核心解读。</p>
            </div>
            <div class="action-row">
              <button type="button" class="btn btn-secondary btn-sm" @click="exportMapGeojson" :disabled="!hasGeojsonResult">导出 GeoJSON</button>
              <button type="button" class="btn btn-secondary btn-sm" @click="exportAnalysisJson" :disabled="!hasAnyAnalysis">导出分析 JSON</button>
            </div>
          </div>

          <div class="status-grid">
            <div class="status-card">
              <span>区域</span>
              <strong>{{ activeRegionLabel }}</strong>
            </div>
            <div class="status-card">
              <span>输出要素</span>
              <strong>{{ geojsonFeatureCountLabel }}</strong>
            </div>
            <div class="status-card">
              <span>回归模型</span>
              <strong>{{ resolvedModelLabel }}</strong>
            </div>
            <div class="status-card">
              <span>主导因素</span>
              <strong>{{ mainFactorLabel }}</strong>
            </div>
          </div>

          <div class="map-stage">
            <BaseMap
              style="height: 100%; width: 100%; border-radius: 18px; border: 1px solid #dbe3ef;"
              :layers-config="layersConfig"
              :center="[115.9, 28.7]"
              :zoom="7"
              :geojson="displayGeojson"
              :legend-title="legendTitle"
              :legend-items="legendItems"
              :feature-style-config="featureStyleConfig"
              @map-click="onMapClick"
              @view-ready="onViewReady"
            />
          </div>
        </div>

        <div class="detail-grid">
          <article class="detail-card">
            <div class="section-head compact">
              <div>
                <h3>地图属性</h3>
                <p>点击地图结果后查看该要素的关键字段。</p>
              </div>
            </div>
            <div v-if="featureInfoEntries.length" class="feature-grid">
              <div v-for="item in featureInfoEntries" :key="item.key" class="feature-item">
                <span>{{ item.key }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div v-else class="empty-tip">当前没有选中的空间要素。</div>
          </article>

          <article class="detail-card">
            <div class="section-head compact">
              <div>
                <h3>{{ insightPanelTitle }}</h3>
                <p>只显示当前阶段最重要的结果摘要，不再堆叠多个回显卡片。</p>
              </div>
            </div>
            <div v-if="insightPanelRows.length" class="summary-grid">
              <div v-for="item in insightPanelRows" :key="item.label" class="summary-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div v-else class="empty-tip">完成当前步骤后，这里会出现对应的摘要结果。</div>
          </article>
        </div>
      </section>

      <aside class="control-column">
        <div class="workflow-card">
          <div class="section-head compact">
            <div>
              <h2>分析流程</h2>
              <p>按步骤推进，避免同时操作多个区块。</p>
            </div>
          </div>
          <div class="workflow-list">
            <button
              v-for="(step, idx) in steps"
              :key="step.value"
              type="button"
              :class="['workflow-step', { active: currentStep === idx, done: stepStatus[idx], locked: idx > currentStep }]"
              :disabled="idx > currentStep"
              @click="switchToStep(idx)"
            >
              <span class="workflow-index">{{ String(idx + 1).padStart(2, '0') }}</span>
              <span class="workflow-copy">
                <strong>{{ step.label }}</strong>
                <small>{{ getStepStateText(idx) }}</small>
              </span>
            </button>
          </div>
        </div>

        <div class="control-card">
          <div class="section-head">
            <div>
              <h2>{{ activeTab.label }}</h2>
              <p>{{ stepDescriptions[activeTab.value] }}</p>
            </div>
          </div>

          <template v-if="activeTab.value === 'preprocess'">
            <div class="summary-strip">
              <div v-for="item in preprocessNotes" :key="item.label" class="strip-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>

            <form class="control-form" @submit.prevent="onPreprocess">
              <div class="form-grid">
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
              </div>

              <div class="form-group">
                <label class="form-label">重采样方法</label>
                <select class="form-select" v-model="preprocessForm.resuml">
                  <option v-for="m in resampleMethods" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>

              <div class="upload-box">
                <div class="upload-head">
                  <div>
                    <h3>自定义研究区</h3>
                    <p>支持单个 GeoJSON，或同名的 `.shp + .shx + .dbf (+ .prj)` 文件组。</p>
                  </div>
                </div>
                <div class="file-upload">
                  <input type="file" multiple @change="onPreprocessFileChange" accept=".shp,.shx,.dbf,.prj,.geojson,.json">
                  <div class="file-upload-button">选择区域文件</div>
                </div>
                <div v-if="selectedRegionFileNames.length" class="selected-file-list">
                  <span v-for="name in selectedRegionFileNames" :key="name" class="file-chip">{{ name }}</span>
                </div>
                <div class="form-grid compact-grid">
                  <div class="form-group">
                    <label class="form-label">区域编码</label>
                    <input type="text" class="form-input" v-model="customRegionCode" placeholder="留空则自动生成">
                  </div>
                  <div class="form-group">
                    <label class="form-label">区域名称</label>
                    <input type="text" class="form-input" v-model="customRegionName" placeholder="例如：核心保护区">
                  </div>
                </div>
              </div>

              <div class="action-row split">
                <button type="button" class="btn btn-secondary" @click="onUploadRegion" :disabled="!selectedRegionFiles.length">
                  上传并应用区域
                </button>
                <button type="submit" class="btn btn-primary">
                  开始预处理
                </button>
              </div>
            </form>
          </template>

          <template v-else-if="activeTab.value === 'regression'">
            <form class="control-form" @submit.prevent="onRegression">
              <div class="form-group">
                <label class="form-label">因变量</label>
                <input type="text" class="form-input" v-model="regressionForm.dependent_var" placeholder="输入因变量名称">
              </div>
              <div class="form-group">
                <label class="form-label">自变量选择</label>
                <div class="checkbox-group">
                  <label class="checkbox-item" v-for="v in independentVars" :key="v.value">
                    <input type="checkbox" :value="v.value" v-model="regressionForm.independent_vars">
                    <span>{{ v.label }}</span>
                  </label>
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
              <div class="action-row end">
                <button type="submit" class="btn btn-primary" :disabled="!stepStatus[0] || stepStatus[1]">
                  执行回归分析
                </button>
              </div>
            </form>
          </template>

          <template v-else-if="activeTab.value === 'download'">
            <div class="download-grid">
              <div class="mini-card">
                <h3>空间成果</h3>
                <p>导出当前模型的 Shapefile 结果。</p>
                <div class="mini-meta">
                  <span>{{ downloadForm.year }} 年</span>
                  <span>{{ downloadForm.region }}</span>
                  <span>{{ downloadForm.model }}</span>
                </div>
                <button type="button" class="btn btn-primary" :disabled="!stepStatus[1]" @click="onDownload('shapefile')">
                  下载 Shapefile
                </button>
              </div>
              <div class="mini-card">
                <h3>属性表格</h3>
                <p>导出预处理后的 CSV 表格结果。</p>
                <div class="mini-meta">
                  <span>{{ downloadForm.year }} 年</span>
                  <span>{{ downloadForm.region }}</span>
                </div>
                <button type="button" class="btn btn-secondary" :disabled="!stepStatus[0]" @click="onDownload('csv')">
                  下载 CSV
                </button>
              </div>
            </div>
          </template>

          <template v-else-if="activeTab.value === 'visualize'">
            <form class="control-form" @submit.prevent="onVisualize">
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">可视化年份</label>
                  <input type="text" class="form-input" v-model="visualizeForm.year" placeholder="输入年份">
                </div>
                <div class="form-group">
                  <label class="form-label">区域范围</label>
                  <input type="text" class="form-input" v-model="visualizeForm.region" placeholder="区域代码">
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">模型结果</label>
                <select class="form-select" v-model="visualizeForm.model">
                  <option value="OLS">OLS模型结果</option>
                  <option value="SLM">SLM模型结果</option>
                  <option value="SEM">SEM模型结果</option>
                </select>
              </div>
              <div class="action-row split">
                <button type="submit" class="btn btn-primary" :disabled="!stepStatus[1]">
                  生成可视化地图
                </button>
                <button type="button" class="btn btn-secondary" @click="runMechanismAnalysis" :disabled="!stepStatus[1]">
                  生成机制解读
                </button>
              </div>
            </form>
          </template>

          <details class="response-panel" v-if="currentResponseText">
            <summary>{{ currentResponseTitle }}</summary>
            <pre>{{ currentResponseText }}</pre>
          </details>
        </div>
      </aside>
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
const residualClassColorMap = {
  1: '#08306b',
  2: '#2171b5',
  3: '#6baed6',
  4: '#f7f7f7',
  5: '#fdae6b',
  6: '#fb6a4a',
  7: '#cb181d'
}
const legendClassItems = [
  { label: '极低残差 (≤ -3)', color: residualClassColorMap[1] },
  { label: '较低残差 (-3 ~ -2)', color: residualClassColorMap[2] },
  { label: '偏低残差 (-2 ~ -1)', color: residualClassColorMap[3] },
  { label: '中等残差 (-1 ~ 1)', color: residualClassColorMap[4] },
  { label: '偏高残差 (1 ~ 2)', color: residualClassColorMap[5] },
  { label: '较高残差 (2 ~ 3)', color: residualClassColorMap[6] },
  { label: '极高残差 (≥ 3)', color: residualClassColorMap[7] }
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
const activeTab = computed(() => tabs[currentStep.value] || tabs[0])
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
const featureStyleConfig = computed(() => {
  if (!displayGeojson.value?.type) return null
  return hasGeojsonResult.value
    ? {
        property: 'resid_class',
        colors: residualClassColorMap,
        defaultColor: residualClassColorMap[4],
        strokeColor: '#0f172a',
        fillOpacity: 0.72,
        strokeWidth: 1.4
      }
    : {
        defaultColor: '#2563eb',
        strokeColor: '#1d4ed8',
        fillOpacity: 0.18,
        strokeWidth: 2
      }
})
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
const insightPanelTitle = computed(() => {
  if (analysisSummaryRows.value.length) return '机制解读'
  if (visualSummaryRows.value.length) return '地图输出摘要'
  if (regressionSummaryRows.value.length) return '回归结果摘要'
  if (preprocessSummaryRows.value.length || regionUploadRows.value.length) return '数据准备摘要'
  return '阶段摘要'
})
const insightPanelRows = computed(() => {
  if (analysisSummaryRows.value.length) return analysisSummaryRows.value
  if (visualSummaryRows.value.length) return visualSummaryRows.value
  if (regressionSummaryRows.value.length) return regressionSummaryRows.value
  if (preprocessSummaryRows.value.length) return preprocessSummaryRows.value
  if (regionUploadRows.value.length) return regionUploadRows.value
  return []
})
const currentResponseTitle = computed(() => {
  if (activeTab.value.value === 'preprocess') return '预处理与区域上传响应'
  if (activeTab.value.value === 'regression') return '空间回归响应'
  if (activeTab.value.value === 'download') return '下载响应'
  return '可视化与机制分析响应'
})
const currentResponseText = computed(() => {
  if (activeTab.value.value === 'preprocess') {
    return [regionUploadResp.value, preprocessResp.value].filter(Boolean).join('\n\n')
  }
  if (activeTab.value.value === 'regression') {
    return regressionResp.value
  }
  if (activeTab.value.value === 'download') {
    return [downloadResp.value, csvResp.value].filter(Boolean).join('\n\n')
  }
  return visualizeResp.value
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

function getStepStateText(idx) {
  if (stepStatus[idx]) return '已完成'
  if (idx === currentStep.value) return '当前进行中'
  return '等待前序完成'
}

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
.analysis-page {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.14), transparent 24%),
    linear-gradient(180deg, #f4f7fb 0%, #edf2f7 100%);
  color: #142033;
}

.hero-card,
.workspace-card,
.detail-card,
.workflow-card,
.control-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(207, 217, 229, 0.9);
  border-radius: 24px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 24px;
  padding: 28px;
  margin-bottom: 24px;
}

.hero-main h1 {
  margin: 12px 0 10px;
  font-size: 2rem;
  line-height: 1.15;
  color: #10233f;
}

.hero-main p {
  max-width: 760px;
  color: #526176;
  line-height: 1.7;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.hero-stat,
.status-card,
.strip-item,
.summary-item,
.feature-item,
.mini-card {
  background: #f8fafc;
  border: 1px solid #dce5f0;
  border-radius: 18px;
}

.hero-stat {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-stat span,
.status-card span,
.strip-item span,
.summary-item span,
.feature-item span,
.mini-meta span {
  font-size: 0.82rem;
  color: #637287;
}

.hero-stat strong,
.status-card strong,
.strip-item strong,
.summary-item strong,
.feature-item strong {
  color: #10233f;
  font-size: 1rem;
  word-break: break-word;
}

.page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(360px, 0.9fr);
  gap: 24px;
  align-items: start;
}

.workspace-column,
.control-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.workspace-card,
.detail-card,
.workflow-card,
.control-card {
  padding: 24px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-head.compact {
  margin-bottom: 14px;
}

.section-head h2,
.section-head h3 {
  margin: 0 0 6px;
  color: #10233f;
}

.section-head p,
.upload-head p,
.mini-card p {
  margin: 0;
  color: #637287;
  line-height: 1.6;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.action-row.split {
  justify-content: space-between;
}

.action-row.end {
  justify-content: flex-end;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.status-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.map-stage {
  min-height: 620px;
  padding: 12px;
  border-radius: 22px;
  background: linear-gradient(180deg, #edf4fb 0%, #f8fafc 100%);
  border: 1px solid #d8e4f2;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.feature-grid,
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.feature-item,
.summary-item {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-tip {
  padding: 18px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px dashed #c7d4e3;
  color: #637287;
  line-height: 1.6;
}

.workflow-list {
  display: grid;
  gap: 12px;
}

.workflow-step {
  width: 100%;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid #dbe3ef;
  background: #f8fafc;
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
  cursor: pointer;
  transition: 0.2s ease;
}

.workflow-step:hover:not(:disabled) {
  border-color: #93c5fd;
  background: #eff6ff;
}

.workflow-step.active {
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  border-color: #60a5fa;
}

.workflow-step.done {
  border-color: #86efac;
}

.workflow-step.locked {
  opacity: 0.55;
}

.workflow-step:disabled {
  cursor: not-allowed;
}

.workflow-index {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #10233f;
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 700;
  flex-shrink: 0;
}

.workflow-step.active .workflow-index {
  background: #2563eb;
}

.workflow-step.done .workflow-index {
  background: #16a34a;
}

.workflow-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.workflow-copy strong {
  color: #10233f;
  font-size: 0.95rem;
}

.workflow-copy small {
  color: #637287;
  font-size: 0.8rem;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.strip-item {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.compact-grid {
  margin-top: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.88rem;
  color: #334155;
  font-weight: 600;
}

.form-input,
.form-select {
  width: 100%;
  min-height: 46px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #ced8e5;
  background: #ffffff;
  color: #10233f;
  font-size: 0.94rem;
  transition: 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #60a5fa;
  box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.16);
}

.upload-box {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f8fbff 0%, #f1f6fb 100%);
  border: 1px solid #d8e4f2;
}

.upload-head {
  margin-bottom: 14px;
}

.upload-head h3,
.mini-card h3 {
  margin: 0 0 6px;
  color: #10233f;
}

.file-upload {
  position: relative;
}

.file-upload input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.file-upload-button {
  min-height: 48px;
  padding: 12px 16px;
  border: 1px dashed #94a3b8;
  border-radius: 14px;
  background: #ffffff;
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
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
  background: #e0ecff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  font-size: 0.8rem;
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dbe3ef;
  background: #f8fafc;
}

.checkbox-item input {
  margin: 0;
}

.download-grid {
  display: grid;
  gap: 14px;
}

.mini-card {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mini-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mini-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #eef2f7;
}

.response-panel {
  margin-top: 18px;
  padding: 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #dbe3ef;
}

.response-panel summary {
  cursor: pointer;
  color: #10233f;
  font-weight: 700;
}

.response-panel pre {
  margin: 14px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
  font-size: 0.83rem;
  line-height: 1.6;
  color: #334155;
  font-family: 'Consolas', 'Monaco', monospace;
}

.btn {
  min-height: 44px;
  padding: 10px 18px;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  font-size: 0.92rem;
  font-weight: 600;
  transition: 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #ffffff;
}

.btn-secondary {
  background: #eef2f7;
  color: #334155;
  border: 1px solid #d5dee8;
}

.btn-sm {
  min-height: 40px;
  padding: 8px 14px;
  font-size: 0.85rem;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1180px) {
  .hero-card,
  .page-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .analysis-page {
    padding: 16px;
  }

  .hero-card,
  .workspace-card,
  .detail-card,
  .workflow-card,
  .control-card {
    padding: 18px;
    border-radius: 20px;
  }

  .hero-stats,
  .status-grid,
  .feature-grid,
  .summary-grid,
  .summary-strip,
  .form-grid,
  .checkbox-group {
    grid-template-columns: 1fr;
  }

  .action-row.split,
  .action-row.end {
    justify-content: stretch;
  }

  .action-row.split .btn,
  .action-row.end .btn,
  .mini-card .btn {
    width: 100%;
  }

  .map-stage {
    min-height: 420px;
  }
}
</style>

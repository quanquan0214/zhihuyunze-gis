<template>
  <div class="container">
   
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
            <BaseMap
              style="height: 100%; width: 100%; border-radius: 8px; border: 1px solid #e0e0e0;"
              :layers-config="layersConfig"
              :center="[115.9, 28.7]"
              :zoom="7"
              :geojson="geojsonData"
              @map-click="onMapClick"
              @view-ready="onViewReady"
            />
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
                <div class="form-group">
                  <label class="form-label">分析年份</label>
                  <select class="form-select" v-model="preprocessForm.year">
                    <option v-for="y in years" :key="y" :value="y">{{ y }}年</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">目标区域</label>
                  <select class="form-select" v-model="preprocessForm.region">
                    <option v-for="c in cities" :key="c.value" :value="c.value">{{ c.label }}</option>
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
                    <input type="file" @change="onPreprocessFileChange" accept=".shp,.geojson">
                    <div class="file-upload-button">
                      <span>📁</span>
                      选择文件
                    </div>
                  </div>
                </div>
                <button type="submit" class="btn btn-primary" :disabled="stepStatus[0]">
                  <span>🔄</span>
                  开始预处理
                </button>
              </form>
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
              <div class="response-area"><pre>{{ regressionResp }}</pre></div>
            </template>
            <template v-else-if="tab.value === 'download'">
              <div style="display: grid; gap: 20px;">
                <div style="padding: 20px; border: 2px solid #e5e7eb; border-radius: 12px;">
                  <h4 style="margin-bottom: 15px; color: #374151;">空间数据文件</h4>
                  <form @submit.prevent="onDownload('shapefile')">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                      <div>
                        <label class="form-label">年份</label>
                        <input
                          type="text"
                          class="form-input"
                          v-model="downloadForm.year"
                        >
                      </div>
                      <div>
                        <label class="form-label">区域</label>
                        <input
                          type="text"
                          class="form-input"
                          v-model="downloadForm.region"
                        >
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
              </form>
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
import { ref, reactive } from 'vue'
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
const csvResp = ref('') // 补充定义，解决 Vue warn
const visualizeForm = reactive({ year: '2020', region: 'NC', model: 'OLS' })
const visualizeResp = ref('')
const geojsonData = ref(null)
const selectedFeature = ref(null)

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

function onPreprocessFileChange(e) {
  preprocessForm.file = e.target.files[0]
}

async function onPreprocess() {
  try {
    const payload = {
      year: preprocessForm.year,
      region: preprocessForm.region,
      res: preprocessForm.res,
      src: preprocessForm.src,
      resuml: preprocessForm.resuml
    }
    // 先打印日志，再发请求
    console.log('Preprocess payload:', JSON.parse(JSON.stringify(preprocessForm)));
    const data = await api.post('/api/preprocess', payload, {
      headers: { 'Content-Type': 'application/json' },
      transformRequest: [(data) => JSON.stringify(data)]
    })
    preprocessResp.value = JSON.stringify(data, null, 2)
    regressionForm.year = payload.year
    regressionForm.region = payload.region
    // 同步到后续步骤的表单
    downloadForm.year = payload.year
    downloadForm.region = payload.region
    visualizeForm.year = payload.year
    visualizeForm.region = payload.region
    console.log('Preprocess response:', regressionForm);
    stepStatus[0] = true
    currentStep.value = 1
    currentTab.value = tabs[1].value
  } catch (e) {
    preprocessResp.value = e?.message || String(e)
  }
}
async function onRegression() {
  try {
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

    console.log('Regression payload:', payload);

    const data = await api.post('/api/spatial-regression', payload, {
      headers: { 'Content-Type': 'application/json' }
    })
    regressionResp.value = JSON.stringify(data, null, 2)
    // 回归分析成功后，同步后续步骤参数
    downloadForm.year = regressionForm.year
    downloadForm.region = regressionForm.region
    downloadForm.model = regressionForm.model
    visualizeForm.year = regressionForm.year
    visualizeForm.region = regressionForm.region
    visualizeForm.model = regressionForm.model
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
    if(type==='shapefile') {
      const { year, region, model } = downloadForm;
      const res = await api.get(`/api/download-shapefile?year=${year}&region=${region}&model=${model}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(res)
      const a = document.createElement('a')
      a.href = url
      a.download = `${model}_results.zip`
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
    const { year, region, model } = visualizeForm;
    const data = await api.get(`/api/results/visualize?year=${year}&region=${region}&model=${model}`)
    visualizeResp.value = JSON.stringify(data, null, 2)
    stepStatus[2] = true
    currentStep.value = 3
    currentTab.value = tabs[3].value
    const geo = data.geojson || data;
    if (geo && geo.type === 'FeatureCollection' && Array.isArray(geo.features)) {
      geo.features.forEach(f => {
        const v = parseFloat(f.properties.std_resid);
        if (v < -3) f.properties.resid_class = '1';
        else if (v < -2) f.properties.resid_class = '2';
        else if (v < -1) f.properties.resid_class = '3';
        else if (v < 1) f.properties.resid_class = '4';
        else if (v < 2) f.properties.resid_class = '5';
        else if (v < 3) f.properties.resid_class = '6';
        else f.properties.resid_class = '7';
        
        console.log(`Feature ${f.id}: std_resid = ${v}, resid_class = ${f.properties.resid_class}`);
      });
      geojsonData.value = geo;
    } else {
      geojsonData.value = null;
      visualizeResp.value += '\n[未检测到标准GeoJSON，无法渲染地图]';
    }
  } catch (e) {
    visualizeResp.value = e?.message || String(e)
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
.container {
  max-width: 100vw;
  margin: 0;
  padding: 0;
  min-height: 100vh;
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
  height: 100vh;
}
.left-panel, .right-panel {
  height: 100vh;
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
}
.map-container {
  flex: 1;
  background: #f8fafc;
  border-radius: 15px;
  border: 2px dashed #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
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
.response-area:empty {
  display: none;
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
  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: 300px 1fr;
  }
  .process-indicator {
    flex-wrap: wrap;
    gap: 15px;
  }
  .step {
    flex: 1;
    min-width: 80px;
  }
}
@media (max-width: 768px) {
  .container {
    padding: 15px;
  }
  .header h1 {
    font-size: 2rem;
  }
  .left-panel, .right-panel {
    padding: 20px;
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

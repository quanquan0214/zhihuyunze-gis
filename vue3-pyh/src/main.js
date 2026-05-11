import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import '@/styles/reset.css'
import '@/styles/common.css'
import 'ol/ol.css'
import axios from 'axios'
import api from '@/utils/request';

const app = createApp(App)

app.use(router)
app.config.globalProperties.$axios = axios
app.config.globalProperties.$api = api
app.mount('#app')
// 确保 Element Plus 的样式已全局引入
import 'element-plus/dist/index.css'

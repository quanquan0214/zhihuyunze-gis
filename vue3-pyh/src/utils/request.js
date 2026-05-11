// src/utils/request.js
import axios from 'axios';
import { ElLoading } from 'element-plus';

// 创建一个简单的 loading 状态管理器
let loadingCount = 0;
let loadingInstance = null;

const showLoading = () => {
  if (loadingCount === 0) {
    loadingInstance = ElLoading.service({
      lock: true,
      text: '加载中...',
      background: 'rgba(0, 0, 0, 0.7)',
      spinner: 'el-icon-loading',
      fullscreen: true
    });
  }
  loadingCount++;
};

const hideLoading = () => {
  loadingCount--;
  if (loadingCount === 0) {
    loadingInstance?.close();
    loadingInstance = null;
  }
};

const api = axios.create({
  // 所有业务请求都显式使用 /api 前缀，避免 baseURL 与代理重写叠加导致路径歧义
  baseURL: '',
  timeout: 52000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    showLoading(); // 显示 loading
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    hideLoading(); // 请求错误时也要隐藏 loading
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  response => {
    hideLoading(); // 隐藏 loading
    // 只返回响应体内容
    return response.data;
  },
  error => {
    hideLoading(); // 响应错误时也要隐藏 loading
    // 统一处理401未授权
    if (error.response && error.response.status === 401) {
      // 可选：清除token并跳转到登录页
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

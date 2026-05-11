<template>
  <div class="app-container">
    <!-- 背景遮罩 -->
    <div class="bg-overlay"></div>
    
    <div class="main-content">
      <!-- 左侧内容 -->
      <div class="left-content">
        <div class="intro-section">
          <h1 class="main-title">智护云泽-环鄱阳湖区域空天地一体化生态环境质量监测系统</h1>
          <p class="subtitle">Poyang Lake Ecological Environment Quality Monitoring and Assessment System</p>
          <div class="divider"></div>
          <p class="description">
            本系统提供全面的鄱阳湖生态环境数据监测、分析与评估功能，助力环保决策与生态保护。
          </p>
        </div>
      </div>
      
      <!-- 右侧登录/注册表单 -->
      <div class="form-container">
        <!-- 表单选项卡 -->
        <div class="tab-header">
          <button 
            @click="activeTab = 'login'"
            :class="['tab-button', { active: activeTab === 'login' }]"
          >
            登录
          </button>
          <button 
            @click="activeTab = 'register'"
            :class="['tab-button', { active: activeTab === 'register' }]"
          >
            注册
          </button>
        </div>
        
        <!-- 登录表单 -->
        <div v-show="activeTab === 'login'" class="form-content">
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label class="form-label">用户名</label>
              <div class="input-wrapper">
                <i class="fas fa-user input-icon"></i>
                <input 
                  type="text" 
                  v-model="loginForm.username"
                  class="form-input" 
                  placeholder="请输入用户名" 
                  required
                >
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">密码</label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input 
                  :type="showLoginPassword ? 'text' : 'password'"
                  v-model="loginForm.password"
                  class="form-input" 
                  placeholder="请输入密码" 
                  required
                >
                <button 
                  type="button" 
                  @click="showLoginPassword = !showLoginPassword"
                  class="password-toggle"
                >
                  <i :class="showLoginPassword ? 'fas fa-eye' : 'fas fa-eye-slash'"></i>
                </button>
              </div>
            </div>
            
            <div class="form-options">
              <div class="checkbox-wrapper">
                <input 
                  id="remember-me" 
                  type="checkbox" 
                  v-model="loginForm.rememberMe"
                  class="checkbox"
                >
                <label for="remember-me" class="checkbox-label">记住我</label>
              </div>
            </div>
            
            <button type="submit" class="submit-button">
              <span>登录</span>
              <i class="fas fa-arrow-right"></i>
            </button>
          </form>
        </div>
        
        <!-- 注册表单 -->
        <div v-show="activeTab === 'register'" class="form-content">
          <form @submit.prevent="handleRegister">
            <div class="form-group">
              <label class="form-label">用户名</label>
              <div class="input-wrapper">
                <i class="fas fa-user input-icon"></i>
                <input 
                  type="text" 
                  v-model="registerForm.username"
                  class="form-input" 
                  placeholder="请输入用户名" 
                  required
                >
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">邮箱</label>
              <div class="input-wrapper">
                <i class="fas fa-envelope input-icon"></i>
                <input 
                  type="email" 
                  v-model="registerForm.email"
                  class="form-input" 
                  placeholder="请输入邮箱" 
                  required
                >
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">密码</label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input 
                  :type="showRegisterPassword ? 'text' : 'password'"
                  v-model="registerForm.password"
                  class="form-input" 
                  placeholder="请输入密码" 
                  required
                >
                <button 
                  type="button" 
                  @click="showRegisterPassword = !showRegisterPassword"
                  class="password-toggle"
                >
                  <i :class="showRegisterPassword ? 'fas fa-eye' : 'fas fa-eye-slash'"></i>
                </button>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">确认密码</label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input 
                  :type="showConfirmPassword ? 'text' : 'password'"
                  v-model="registerForm.confirmPassword"
                  class="form-input" 
                  placeholder="请再次输入密码" 
                  required
                >
                <button 
                  type="button" 
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="password-toggle"
                >
                  <i :class="showConfirmPassword ? 'fas fa-eye' : 'fas fa-eye-slash'"></i>
                </button>
              </div>
            </div>
            
            <button type="submit" class="submit-button">
              <span>注册</span>
              <i class="fas fa-user-plus"></i>
            </button>
          </form>
        </div>
        
        <!-- 底部信息 -->
        <div class="form-footer">
          <p v-if="activeTab === 'register'" class="footer-text">
            已有账号? 
            <a href="#" @click.prevent="activeTab = 'login'" class="footer-link">立即登录</a>
          </p>
        </div>
      </div>
    </div>
    <!-- 页脚 -->
    <footer class="page-footer">
      <div class="container">
        <p class="copyright">© 2025 智护云泽-环鄱阳湖区域空天地一体化生态环境质量监测系统 | 保留所有权利</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router';

// 响应式数据
const activeTab = ref('login')
const showLoginPassword = ref(false)
const showRegisterPassword = ref(false)
const showConfirmPassword = ref(false)

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 方法
const handleLogin = () => {
  console.log('登录提交:', loginForm)
  // 模拟登录成功，设置token
  localStorage.setItem('token', 'mock-token')
  // 保存用户名到本地
  localStorage.setItem('username', loginForm.username)
  router.push('/')
}

const handleRegister = () => {
  if (registerForm.password !== registerForm.confirmPassword) {
    alert('密码不一致！')
    return
  }
  console.log('注册提交:', registerForm)
  // 这里可以添加注册逻辑
  // 模拟注册成功，设置token
  localStorage.setItem('token', 'mock-token')
  localStorage.setItem('username', registerForm.username)
  router.push('/')
}

const router = useRouter();
</script>

<style lang="less" scoped>
// 变量定义
@primary-color: #165DFF;
@secondary-color: #0E42B3;
@neutral-100: #F3F4F6;
@neutral-200: #E5E7EB;
@neutral-700: #374151;
@neutral-800: #1F2937;
@neutral-900: #111827;

// 混合器
.transition-custom() {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.text-shadow() {
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.bg-glass() {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

// 基础样式
.app-container {
  font-family: 'Inter', system-ui, sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
  background: linear-gradient(135deg, #165DFF 0%, #0E42B3 100%);
  background-image: url('https://n.sinaimg.cn/spider20211124/214/w2048h1366/20211124/c85c-80c09d5d88886aff186cb22e5562ebc1.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
}

.bg-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 0;
}

.main-content {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

// 左侧内容样式
.left-content {
  display: none;
  position: absolute;
  left:0;
  width: 66.666667%;
  height: 50%;
  align-items: center;
  justify-content: center;
  padding: 0 48px;

  @media (min-width: 768px) {
    display: flex;
  }
}

.intro-section {
  color: white;
  max-width: 596px;
}

.main-title {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: bold;
  margin-bottom: 12px;
  .text-shadow();
  line-height: 1.25;
    text-align: center;

}

.subtitle {
  font-size: clamp(1rem, 2vw, 1.25rem);
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 18px;
  opacity: 0.9;
  text-align: center;
}

.divider {
  width: 80px;
  height: 4px;
  background: @primary-color;
  margin: 0 auto 32px;
  border-radius: 9999px;
}

.description {
  font-size: clamp(1rem, 1.5vw, 1.1rem);
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  opacity: 0.9;
}

// 表单容器样式
.form-container {
  width: 100%;
  max-width: 448px;
  margin: 0 auto;
  background: rgba(255,255,255,0.13);
  border-radius: 20px;
  border: 1.5px solid rgba(255,255,255,0.18);
  box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  overflow: hidden;

  @media (min-width: 768px) {
    max-width: 512px;
    margin-right: 150px;
  }
}

// 标签头部样式
.tab-header {
  display: flex;
  border-bottom: 1.5px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.04);
}

.tab-button {
  flex: 1;
  padding: 20px 16px;
  font-weight: 600;
  border-bottom: 2.5px solid transparent;
  color: rgba(255,255,255,0.85);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  letter-spacing: 1px;
  .transition-custom();

  &:hover {
    color: #fff;
    background: rgba(22,93,255,0.08);
  }

  &.active {
    color: #fff;
    border-bottom-color: @primary-color;
    background: rgba(22,93,255,0.13);
  }
}

// 表单内容样式
.form-content {
  padding: 36px 32px 16px 32px;
}

.form-group {
  margin-bottom: 26px;
}

.form-label {
  display: block;
  color: rgba(255,255,255,0.92);
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: rgba(22,93,255,0.6);
  pointer-events: none;
  font-size: 18px;
}

.form-input {
  display: block;
  width: 88%;
  padding: 12px 12px 12px 40px;
  background: rgba(255,255,255,0.18);
  border: 1.5px solid rgba(22,93,255,0.13);
  border-radius: 10px;
  color: #fff;
  font-size: 16px;
  .transition-custom();

  &::placeholder {
    color: rgba(255,255,255,0.45);
  }

  &:focus {
    outline: none;
    border-color: @primary-color;
    box-shadow: 0 0 0 2px rgba(22,93,255,0.18);
    background: rgba(255,255,255,0.22);
  }
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  color: rgba(22,93,255,0.6);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  .transition-custom();

  &:hover {
    color: #fff;
  }
}

// 表单选项样式
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
}

.checkbox {
  height: 16px;
  width: 16px;
  color: @primary-color;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.checkbox-label {
  margin-left: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.forgot-link {
  font-size: 14px;
  color: @primary-color;
  text-decoration: none;
  .transition-custom();

  &:hover {
    color: rgba(22, 93, 255, 0.8);
  }
}

// 提交按钮样式
.submit-button {
  width: 100%;
  background: linear-gradient(90deg, @primary-color 60%, @secondary-color 100%);
  color: #fff;
  font-weight: 600;
  padding: 13px 0;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-size: 17px;
  letter-spacing: 1px;
  .transition-custom();
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 4px 16px 0 rgba(22,93,255,0.10);

  &:hover {
    background: linear-gradient(90deg, @secondary-color 0%, @primary-color 100%);
    transform: translateY(-2px) scale(1.03);
    box-shadow: 0 10px 24px -3px rgba(22,93,255,0.18);
  }
}

// 表单底部样式
.form-footer {
  padding: 24px;
  background: rgba(255,255,255,0.07);
  border-top: 1.5px solid rgba(255,255,255,0.13);
}

.footer-text {
  text-align: center;
  color: rgba(255,255,255,0.8);
  font-size: 15px;
}

.footer-link {
  color: @primary-color;
  text-decoration: underline;
  font-weight: 600;
  .transition-custom();

  &:hover {
    color: #fff;
    text-shadow: 0 2px 8px @primary-color;
  }
}

// 页脚样式
.page-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 0;
  z-index: 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}

.copyright {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}
</style>
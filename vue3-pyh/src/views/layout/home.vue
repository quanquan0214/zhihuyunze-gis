<template>
  <div class="layout">
    <!-- 顶部信息栏 -->
    <header class="header">
      <div class="header-title">
        <h2>智护云泽-环鄱阳湖区域空天地一体化生态环境质量监测系统</h2>
      </div>
      <div class="user-avatar">
        <span :style="avatarFontStyle">{{ avatarText }}</span>
      </div>
    </header>
    <div class="main-content">
      <Leftnav />
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Leftnav from '@/components/leftnav.vue'

const router = useRouter()
const username = ref(localStorage.getItem('username') || '')
const avatarText = computed(() => username.value ? username.value[0].toUpperCase() : 'U')

// 根据用户名长度自适应字体大小，最大为22px，最小为14px
const avatarFontStyle = computed(() => {
  const len = avatarText.value.length
  let size = 22
  if (len > 1) size = 18
  if (len > 2) size = 14
  return {
    fontSize: size + 'px',
    display: 'block',
    width: '40px',
    height: '40px',
    lineHeight: '40px',
    textAlign: 'center',
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis'
  }
})

onMounted(() => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.replace('/login')
  }
})

// 模拟登录逻辑（仅供参考，实际应在登录页实现）
/*
function login(usernameInput) {
  localStorage.setItem('token', 'mock-token')
  localStorage.setItem('username', usernameInput)
  username.value = usernameInput
}
*/
</script>

<style lang="less" scoped>
@font-face {
  font-family: 'SIMKAI';
  src: url('/SIMKAI.TTF');
}

.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;

  .header {
    width: 100%;
    height: 60px;
    background-color: var(--primary-dark);
    padding: 0 10px;
    display: flex;
    align-items: center;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
    position: relative;
    margin-bottom: 10px;

    .header-title h2 {
      margin: 0;
      color: #333;
      font-family: 'SIMKAI';
    }

    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-color: #b7e6f5;
      color: #131313;
      overflow: hidden;
      position: absolute;
      right: 50px;
      display: flex;
      align-items: center;
      justify-content: center;

      span {
        // 字体大小由js控制
        font-weight: bold;
        width: 100%;
        height: 100%;
        display: block;
      }
    }
  }

  .main-content {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
}
</style>
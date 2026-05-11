<template>
    <div class="content">
        <div class="tab-btns">
            <button @click="activeTab = 'drone'" :class="{ active: activeTab === 'drone' }">无人机实时监测数据</button>
            <button @click="activeTab = 'field'" :class="{ active: activeTab === 'field' }">实地考察监测数据</button>
        </div>
        <div v-if="activeTab === 'drone'" class="video-wrapper">
            <video controls>
                <source src="/src/assets//images/无人机.mp4" type="video/mp4">
                您的浏览器不支持 video 标签。
            </video>
        </div>
        <div v-else class="img-list">
            <!-- 图片页面，展示三张图片 -->
            <el-carousel height="400px" style="width:100%">
                <el-carousel-item v-for="(img, idx) in fieldImages" :key="idx">
                    <img :src="img" alt="实地考察图片" class="carousel-img" />
                </el-carousel-item>
            </el-carousel>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const fieldImages = [
    '/images/实地考察1.jpg',
    '/images/实地考察2.jpg',
    '/images/实地考察3.jpg',
]

const activeTab = ref<'drone' | 'field'>('drone')
</script>

<style scoped>
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow: hidden;
  background: #f5f6fa;
  padding: 15px 20px;
}

.tab-btns {
  margin-bottom: 16px;
}
button {
  padding: 8px 20px;
  margin-right: 8px;
  border: none;
  background: #f0f0f0;
  cursor: pointer;
  border-radius: 4px;
  font-size: 16px;
  transition: background 0.2s;
}
button.active {
  background: #409eff;
  color: #fff;
}
button:focus {
  outline: none;
}
.video-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}
.video-wrapper video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.img-list {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  align-content: flex-start;
  overflow-y: auto;
  padding: 10px 0;
}
.carousel-img {
  width: 100vw;
  max-width: 100%;
  height: 80vh;
  max-height: 100%;
  display: block;
  margin: 0 auto;
  object-fit: contain;
}
/* .img-list img {
  width: 450px;
  height: 300px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
} */
@media (max-width: 980px) {
  .carousel-img {
    width: 100vw;
    height: 50vh;
  }
  /* .img-list img {
    width: calc(50% - 10px);
    height: auto;
  } */
}
@media (max-width: 600px) {
  .carousel-img {
    width: 100vw;
    height: 30vh;
  }
  .video-wrapper {
    height: auto;
  }
  .video-wrapper video {
    width: 100%;
    height: auto;
  }
  .img-list {
    flex-direction: column;
    align-items: center;
  }
  /* .img-list img {
    width: 100%;
    height: auto;
  } */
}
</style>
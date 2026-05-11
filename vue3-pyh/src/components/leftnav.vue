<template>
    <div class="leftnav">
        <el-menu :default-active="activeIndex" class="el-menu-vertical-demo" :collapse="false"
            background-color="var(--primary-dark)" text-color="var(--text-secondary)"  router>
            <el-menu-item index="/introduce" :route="{ path: '/introduce' }">
                <el-icon><icon-menu /></el-icon>
                <span>介绍</span>
            </el-menu-item>
            <el-sub-menu index="2">
                <template #title>
                    <el-icon>
                        <location />
                    </el-icon>
                    <span>生态要素</span>
                </template>
                <el-menu-item index="/waterstatistics" :route="{ path: '/waterstatistics' }">
                    <span>水文统计</span>
                </el-menu-item>
                <el-menu-item index="/landcoverage" :route="{ path: '/landcoverage' }">
                    <span>土壤覆盖</span>
                </el-menu-item>
                <el-menu-item index="/temperature" :route="{ path: '/temperature' }">
                    <span>温度和降水</span>
                </el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/rsei" :route="{ path: '/rsei' }">
                <el-icon>
                    <document />
                </el-icon>
                <span>生态评价指数</span>
            </el-menu-item>
            <el-menu-item index="/monitor" :route="{ path: '/monitor' }">
                <el-icon><Monitor /></el-icon>
                <span>监测数据</span>
            </el-menu-item>
            <el-menu-item index="/pattern" :route="{ path: '/pattern' }">
                <el-icon>
                    <Setting />
                </el-icon>
                <span>机制分析</span>
            </el-menu-item>
        </el-menu>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
    Document,
    Menu as IconMenu,
    Location,
    Setting,
    Monitor, // 添加 Monitor 图标
} from '@element-plus/icons-vue';

const route = useRoute();
const activeIndex = ref(route.path);

// 监听路由变化，更新激活的菜单项
watch(() => route.path, (newPath) => {
    activeIndex.value = newPath;
});
</script>

<style scoped lang="less">
.leftnav {
    height: 100vh;
    color: var(--text-secondary);
    background-color: var(--primary-dark);
    width: 250px;
}
.el-menu-vertical-demo {
    width: 100%;
    min-height: 100%;
    border-right: none;

    :deep(.el-menu-item) {
        &:hover, &.is-active {
            background-color: var(--panel-bg);
            color: var(--text-secondary);
        }
    }

    :deep(.el-sub-menu) {
        .el-sub-menu__title {
            &:hover {
                background-color: var(--panel-bg);
            }
        }

        .el-menu {
            background-color: var(--primary-dark);
        }

        .el-menu-item {
            min-width: unset;
            
            &:hover, &.is-active {
                background-color: var(--panel-bg);
                color: var(--text-secondary);
            }
        }
    }
}
</style>

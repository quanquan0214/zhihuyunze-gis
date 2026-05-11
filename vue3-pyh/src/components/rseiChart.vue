<template>
    <div>
        <div id="RadarChart" ref="RadarRef"></div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import * as echarts from 'echarts';

// 定义一个 ref 来绑定图表容器
const RadarRef = ref(null);

onMounted(() => {
    const RadarInit = () => {
        const RadarChart = echarts.init(RadarRef.value);
        const option = {
            legend: {
                data: ['RSEI', 'NDVI', 'LST', 'NDBSI', 'WET'],
                left: 0
            },
            tooltip: {},
            radar: {
                // shape: 'circle',
                indicator: [
                    { name: '2000', max: 1 },
                    { name: '2005', max: 1 },
                    { name: '2010', max: 1 },
                    { name: '2015', max: 1 },
                    { name: '2020', max: 1 },
                    { name: '2022', max: 1 }
                ],
                radius: ["0%", "52%"],
                nameGap: 4,
                axisName: {
                    color: "rgba(39, 8, 8, 1)"
                }
            },
            grid: {
                left: '0%', // 左边距
                right: '10%', // 右边距
                top: '98%', // 上边距
                containLabel: true // 是否包含坐标轴标签
            },
            series: [
                {
                    name: 'RSEI',
                    type: 'radar',
                    data: [
                        {
                            value: [0.63, 0.51, 0.49, 0.63, 0.62, 0.69],
                            name: 'RSEI'
                        },
                        {
                            value: [0.56, 0.56, 0.55, 0.55, 0.48, 0.51],
                            name: 'LST'
                        },
                        {
                            value: [0.54, 0.48, 0.67, 0.41, 0.46, 0.34],
                            name: 'NDBSI'
                        },
                        {
                            value: [0.76, 0.65, 0.66, 0.77, 0.78, 0.79],
                            name: 'NDVI'
                        },
                        {
                            value: [0.65, 0.24, 0.23, 0.60, 0.33, 0.74],
                            name: 'WET'
                        },
                    ]
                }
            ]
        };
        // 设置图表选项
        RadarChart.setOption(option);

        // 监听窗口大小变化，自动调整图表大小
        window.addEventListener('resize', () => {
            RadarChart.resize();
        });
    }
    if (RadarRef.value) {
        RadarInit()
    } else {
        console.error('RadarRef is null');
    }

});
</script>

<style scoped>
#RadarChart {
    width: 100%;
    height: 200px;
    margin-bottom: 1rem;
    border-radius: 4px;
    background: transparent;
    /* border: 1px solid var(--accent-blue); */
}
</style>
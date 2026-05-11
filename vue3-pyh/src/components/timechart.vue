<template>
    <div>
        <div id="timeChart" ref="timeRef"></div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
    data: { type: Array, default: () => [] } // [{value, name}]
});

const timeRef = ref(null);

let timeChart = null;

function renderTime() {
    if (!timeRef.value) return;
    if (!timeChart) timeChart = echarts.init(timeRef.value);

    const option = {
        tooltip: {
            trigger: 'axis'
        },
        title: {
            left: 'center',
            top: 10,
            text: '水储量变化趋势',
            textStyle: {
                fontSize: 14,
                color: 'rgb(54, 74, 98)'
            }
        },
        grid: {
            top: '30%',
            left: '8%',
            right: '5%',
            bottom: '12%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: props.data.map(item => item.name),
            name: '年份',
            axisLabel: {
                fontSize: 11,
                interval: 0,
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            name: '水储量(亿m³)',
            nameTextStyle: {
                fontSize: 12
            },
            axisLabel: {
                fontSize: 11
            }
        },
        series: [
            {
                name: '水储量',
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: {
                    width: 2
                },
                itemStyle: {
                    color: '#1890ff'
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(24,144,255,0.3)' },
                        { offset: 1, color: 'rgba(24,144,255,0.1)' }
                    ])
                },
                data: props.data.map(item => item.value)
            }
        ]
    };

    timeChart.setOption(option);
    timeChart.resize();
}

onMounted(() => {
    renderTime();
    window.addEventListener('resize', () => {
        timeChart && timeChart.resize();
    });
});

watch(() => props.data, () => {
    renderTime();
}, { deep: true });
</script>

<style scoped>
#timeChart {
    width: 100%;
    height: 220px;
    margin-bottom: 1rem;
    border-radius: 4px;
    /* border: 1px solid var(--accent-blue); */
    background: transparent;
}
</style>
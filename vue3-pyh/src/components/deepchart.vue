<template>
    <div>
        <div id="pieChart" ref="pieRef"></div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
    data: { type: Array, default: () => [] }
});

const pieRef = ref(null);
let pieChart = null;

function renderPie() {
    if (!pieRef.value) return;
    if (!pieChart) pieChart = echarts.init(pieRef.value);
    
    pieChart.setOption({
        backgroundColor: 'rgba(255,255,255,0.2)',
        title: {
            text: '水深等级分布',
            left: 'center',
            top: 10,
            textStyle: {
                color: 'rgb(54, 74, 98)',
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c}%'
        },
        legend: {
            orient: 'horizontal',
            bottom: '5%',
            left: 'center',
            itemWidth: 12,
            itemHeight: 12,
            textStyle: {
                fontSize: 12
            }
        },
        series: [
            {
                name: '水深等级',
                type: 'pie',
                radius: ['30%', '55%'],
                center: ['50%', '50%'],
                avoidLabelOverlap: true,
                data: props.data,
                label: {
                    show: true,
                    position: 'outside',
                    formatter: '{b}: {d}%',
                    fontSize: 11,
                    color: 'rgb(54, 74, 98)'
                },
                labelLine: {
                    show: true,
                    length: 10,
                    length2: 10,
                    lineStyle: {
                        color: '#666'
                    }
                },
                itemStyle: {
                    borderRadius: 4,
                    borderWidth: 2,
                    borderColor: '#fff'
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }
        ]
    });
    pieChart.resize();
}

onMounted(() => {
    renderPie();
    window.addEventListener('resize', () => {
        pieChart && pieChart.resize();
    });
});

watch(() => props.data, () => {
    renderPie();
}, { deep: true });
</script>

<style scoped>
#pieChart {
    width: 100%;
    height: 220px;
    margin-bottom: 1rem;
    border-radius: 4px;
    background: transparent;
}
</style>
<template>
    <div>
        <div id="pieChart" ref="pieRef"></div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
    data: { type: Array, default: () => [] } // [{value, name}]
});

const pieRef = ref(null);

let pieChart = null;

function renderPie() {
    if (!pieRef.value) return;
    if (!pieChart) pieChart = echarts.init(pieRef.value);
    pieChart.setOption({
        title:{ 
            text: 'RESI等级',
            top: '5%',
            textStyle:{
                color : '#333'
            }
        },
        tooltip: { trigger: 'item' },
        legend: { bottom: '5%', left: 'center' },
        series: [
            {
                name: '组成',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: { show: false, position: 'center' },
                emphasis: {
                    label: { show: true, fontSize: 20, fontWeight: 'bold' }
                },
                labelLine: { show: false },
                data: props.data
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
    /* border: 1px solid var(--accent-blue); */
    background: transparent;
}
</style>
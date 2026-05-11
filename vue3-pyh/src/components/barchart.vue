<template>
    <div>
        <div id="barChart" ref="barRef"></div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
    data: { type: Array, default: () => [] } // [{value, name}]
});

const barRef = ref(null);

let barChart = null;


function renderBar() {
    if (!barRef.value) return;
    if (!barChart) barChart = echarts.init(barRef.value);
    barChart.setOption({
        title: { text: 'RSEI各项值' ,top: '5%'},
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'value', boundaryGap: [0, 0.01] },
        yAxis: {
            type: 'category',
            data: props.data.map(item => item.name)
        },
        series: [
            {
                name: '值',
                type: 'bar',
                data: props.data.map(item => item.value)
            }
        ]
    });
    barChart.resize();
}

onMounted(() => {
    renderBar();
    window.addEventListener('resize', () => {
        barChart && barChart.resize();
    });
});

watch(() => props.data, () => {
    renderBar();
}, { deep: true });
</script>

<style scoped>
#barChart {
    width: 100%;
    height: 220px;
    margin-bottom: 1rem;
    border-radius: 4px;
    /* border: 1px solid var(--accent-blue); */
    background: transparent;
}
</style>
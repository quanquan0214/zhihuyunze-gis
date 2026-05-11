<template>
    <Teleport to="body">
        <div v-if="showAlert" class="global-alert-overlay">
            <div class="global-alert">
                <div class="dialog-header">
                    <h3>区域分析</h3>
                    <button class="close-btn" @click="closeAlert">&times;</button>
                </div>

                <div class="dialog-content">
                    <div class="location-info">
                        <div><strong>选择位置:</strong> {{ formatCoordinates(alertConfig.popupData?.coordinates) }}</div>
                        <div><strong>最近更新:</strong> {{ getCurrentDateTime() }}</div>
                    </div>

                    <div class="chart-tabs">
                        <button v-for="tab in tabs" :key="tab.key" class="chart-tab-btn"
                            :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
                            {{ tab.label }}
                        </button>
                    </div>

                    <!-- 历史趋势 -->
                    <div v-if="activeTab === 'history'" class="chart-container">
                        <div ref="historyChartRef" style="width: 100%; height: 300px;"></div>
                    </div>

                    <!-- 预测分析 -->
                    <div v-if="activeTab === 'prediction'" class="chart-container">
                        <div class="trend-buttons">
                            <button class="trend-btn upward">
                                {{ alertConfig.popupData?.trend_analysis?.trend_type || '趋势类型' }}<br>
                                <small>趋势类型</small>
                            </button>
                            <button class="trend-btn moderate">
                                {{ alertConfig.popupData?.trend_analysis?.trend_strength || '趋势强度' }}<br>
                                <small>趋势强度</small>
                            </button>
                        </div>
                        <div ref="predictionChartRef" style="width: 100%; height: 300px;"></div>
                    </div>

                    <!-- 异常检测 -->
                    <div v-if="activeTab === 'anomaly'" class="chart-container">
                        <div ref="anomalyChartRef" style="width: 100%; height: 300px;"></div>
                        <div class="anomaly-title">异常值检测</div>
                        <div v-if="alertConfig.popupData?.anomalies?.length">
                            <div v-for="anomaly in alertConfig.popupData.anomalies" :key="anomaly.date"
                                class="anomaly-item" :class="`severity-${anomaly.severity}`">
                                <div>
                                    <div class="anomaly-date">{{ formatDate(anomaly.date) }}</div>
                                    <div class="anomaly-value">值: {{ anomaly.value?.toFixed(3) }}</div>
                                </div>
                                <div class="anomaly-severity">
                                    {{ getSeverityText(anomaly.severity) }}
                                </div>
                            </div>
                        </div>
                        <div v-else class="no-anomaly">
                            暂无异常数据
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import * as echarts from 'echarts';

const showAlert = ref(false);
const alertConfig = ref({
    title: '',
    message: '',
    popupData: null
});

const tabs = [
    { key: 'history', label: '历史趋势' },
    { key: 'prediction', label: '预测分析' },
    { key: 'anomaly', label: '异常检测' }
];

const activeTab = ref('history');

// 图表引用
const historyChartRef = ref<HTMLDivElement | null>(null);
const predictionChartRef = ref<HTMLDivElement | null>(null);
const anomalyChartRef = ref<HTMLDivElement | null>(null);

// 图表实例
let historyChart: echarts.ECharts | null = null;
let predictionChart: echarts.ECharts | null = null;
let anomalyChart: echarts.ECharts | null = null;

const openAlert = (config: any) => {
    alertConfig.value = { ...config };
    showAlert.value = true;
    nextTick(() => {
        createCharts();
    });
};

const closeAlert = () => {
    showAlert.value = false;
    destroyCharts();
};

// 创建图表
const createCharts = () => {
    if (!alertConfig.value.popupData) return;
    destroyCharts();
    if (historyChartRef.value && alertConfig.value.popupData.time_series?.values) {
        createHistoryChart();
    }
    if (predictionChartRef.value && alertConfig.value.popupData.ml_prediction?.predictions) {
        createPredictionChart();
    }
    if (anomalyChartRef.value && alertConfig.value.popupData.anomalies?.length) {
        createAnomalyChart();
    }
};

// 创建历史趋势图表
const createHistoryChart = () => {
    if (!historyChartRef.value) return;
    historyChart = echarts.init(historyChartRef.value);
    const timeSeriesData = alertConfig.value.popupData.time_series.values;
    const labels = timeSeriesData.map((_: any, index: number) => {
        const year = 2000 + index;
        return `${year}年`;
    });
    const option = {
        title: { text: '历史趋势', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: {
            trigger: 'axis',
            formatter: function (params: any) {
                return `${params[0].name}<br/>${params[0].seriesName}: ${params[0].value.toFixed(3)}`;
            }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: labels,
            axisLabel: { rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 1,
            interval: 0.2,
            axisLabel: {
                formatter: (value: number) => value.toFixed(2)
            }
        },
        series: [{
            name: '历史数据',
            type: 'line',
            data: timeSeriesData,
            smooth: true,
            lineStyle: { color: '#667eea', width: 2 },
            itemStyle: { color: '#667eea' },
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [
                        { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
                        { offset: 1, color: 'rgba(102, 126, 234, 0.1)' }
                    ]
                }
            }
        }]
    };
    historyChart.setOption(option);
};

// 创建预测分析图表
const createPredictionChart = () => {
    if (!predictionChartRef.value) return;
    predictionChart = echarts.init(predictionChartRef.value);
    const predictions = alertConfig.value.popupData.ml_prediction.predictions;
    const historicalValues = alertConfig.value.popupData.time_series?.values?.slice(-6) || [];
    const allLabels = [];
    const historicalData = [];
    const predictionData = [];

    // 历史数据（假设历史数据为2017-2022年）
    for (let i = 0; i < historicalValues.length; i++) {
        const year = 2023 - historicalValues.length + i;
        allLabels.push(`${year}年`);
        historicalData.push(historicalValues[i]);
        predictionData.push(null);
    }

    // 预测数据（2023-2025年）
    for (let i = 0; i < predictions.length; i++) {
        const year = 2023 + i;
        allLabels.push(`${year}年`);
        historicalData.push(null);
        predictionData.push(predictions[i].predicted_value);
    }

    const option = {
        title: { text: '预测分析', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: {
            trigger: 'axis',
            // 修正formatter，保证所有series都显示
            formatter: function (params: any) {
                let result = params[0]?.name || '';
                params.forEach((param: any) => {
                    // 只显示有值的series
                    if (param.value !== null && param.value !== undefined) {
                        result += `<br/>${param.seriesName}: ${Number(param.value).toFixed(3)}`;
                    }
                });
                return result;
            }
        },
        legend: { data: ['历史数据', '预测值'], bottom: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: {
            type: 'category',
            data: allLabels,
            axisLabel: { rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 1,
            interval: 0.2,
            axisLabel: {
                formatter: (value: number) => value.toFixed(2)
            }
        },
        series: [
            {
                name: '历史数据',
                type: 'line',
                data: historicalData,
                smooth: true,
                lineStyle: { color: '#667eea', width: 2 },
                itemStyle: { color: '#667eea' },
                connectNulls: false
            },
            {
                name: '预测值',
                type: 'line',
                data: predictionData,
                smooth: true,
                lineStyle: { color: '#f093fb', width: 2, type: 'dashed' },
                itemStyle: { color: '#f093fb' },
                connectNulls: false
            }
        ]
    };
    predictionChart.setOption(option);
};

// 创建异常检测图表
const createAnomalyChart = () => {
    if (!anomalyChartRef.value) return;
    anomalyChart = echarts.init(anomalyChartRef.value);

    // 构造2000-2022年所有数据
    const timeSeriesData = alertConfig.value.popupData.time_series.values;
    const labels = timeSeriesData.map((_: any, index: number) => `${2000 + index}年`);
    // 构造异常点索引
    const anomalyMap: Record<number, any> = {};
    (alertConfig.value.popupData.anomalies || []).forEach((anomaly: any) => {
        // 假设anomaly.date为"2022-07-01"格式，取年份
        const year = parseInt(anomaly.date.slice(0, 4));
        anomalyMap[year] = anomaly;
    });

    // 构造标记点数据
    const markPointData = Object.entries(anomalyMap).map(([year, anomaly]: any) => ({
        xAxis: `${year}年`,
        yAxis: anomaly.value,
        symbol: 'circle',
        symbolSize: 14,
        itemStyle: { color: '#f5576c' }
    }));

    const option = {
        title: { text: '异常值', left: 'center', textStyle: { fontSize: 14 } },
        tooltip: {
            trigger: 'axis',
            formatter: function (params: any) {
                let result = params[0].name;
                params.forEach((param: any) => {
                    if (param.value !== null) {
                        // 判断是否为异常点
                        const year = parseInt(param.name);
                        if (anomalyMap[year]) {
                            result += `<br/><span style="color:#f5576c;">异常值: ${param.value.toFixed(3)}</span>`;
                        } else {
                            result += `<br/>正常值: ${param.value.toFixed(3)}`;
                        }
                    }
                });
                return result;
            }
        },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: {
            type: 'category',
            data: labels,
            axisLabel: { rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 1,
            interval: 0.2,
            axisLabel: {
                formatter: (value: number) => value.toFixed(2)
            }
        },
        series: [{
            name: '异常值',
            type: 'line',
            data: timeSeriesData,
            lineStyle: { color: '#667eea', width: 2 },
            itemStyle: {
                color: (params: any) => {
                    const year = 2000 + params.dataIndex;
                    return anomalyMap[year] ? '#f5576c' : '#667eea';
                }
            },
            markPoint: {
                symbol: 'circle',
                symbolSize: 14,
                data: markPointData
            }
        }]
    };
    anomalyChart.setOption(option);
};

// 销毁图表
const destroyCharts = () => {
    if (historyChart) {
        historyChart.dispose();
        historyChart = null;
    }
    if (predictionChart) {
        predictionChart.dispose();
        predictionChart = null;
    }
    if (anomalyChart) {
        anomalyChart.dispose();
        anomalyChart = null;
    }
};

// 格式化坐标
const formatCoordinates = (coords: any) => {
    if (!coords) return '';
    return `${coords.lat?.toFixed(4)}°N, ${coords.lon?.toFixed(4)}°E`;
};

// 获取当前时间
const getCurrentDateTime = () => {
    return new Date().toLocaleString('zh-CN');
};

// 格式化日期
const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN');
};

// 获取严重程度文本
const getSeverityText = (severity: string) => {
    const textMap: Record<string, string> = {
        'mild': '轻微',
        'moderate': '中等',
        'severe': '严重'
    };
    return textMap[severity] || severity;
};

// 监听标签页切换，重新渲染图表
watch(activeTab, async () => {
    if (showAlert.value && alertConfig.value.popupData) {
        await nextTick();
        createCharts();
    }
});

defineExpose({
    openAlert
});
</script>

<style scoped>
.global-alert-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 10000;
    display: flex;
    justify-content: center;
    align-items: center;
}

.global-alert {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 800px;
    max-height: 80vh;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    z-index: 1000;
}

.dialog-header {
    padding: 16px 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.dialog-header h3 {
    margin: 0;
    font-size: 18px;
    color: #333;
}

.dialog-content {
    padding: 20px;
    overflow-y: auto;
    max-height: calc(80vh - 60px);
}

.chart-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
}

.chart-tab-btn {
    padding: 8px 16px;
    border: none;
    background: #f0f2f5;
    color: #666;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.3s;
}

.chart-tab-btn.active {
    background: #1890ff;
    color: #fff;
    font-weight: 500;
}

.chart-container {
    background: white;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #666;
}

.location-info {
    margin-bottom: 16px;
    font-size: 14px;
    color: #666;
}

.trend-buttons {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
}

.trend-btn {
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
    text-align: center;
}

.trend-btn.upward {
    background: linear-gradient(135deg, #1890ff, #36cfc9);
}

.trend-btn.moderate {
    background: linear-gradient(135deg, #36cfc9, #52c41a);
}

.anomaly-section {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
}

.anomaly-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    margin-bottom: 8px;
    border-radius: 6px;
    font-size: 14px;
}

.anomaly-severity {
    font-weight: bold;
    margin-left: auto;
}

.severity-severe {
    background: #ffebee;
    color: #c62828;
}

.severity-moderate {
    background: #fff3e0;
    color: #ef6c00;
}

.severity-mild {
    background: #f3e5f5;
    color: #7b1fa2;
}

.anomaly-title {
    margin: 16px 0;
    font-size: 16px;
    font-weight: 500;
    color: #333;
}

.no-anomaly {
    text-align: center;
    color: #999;
    padding: 20px;
}
</style>

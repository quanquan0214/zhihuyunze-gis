<template>
    <div class="introduce">
        <!-- 主地图区域 -->
        <div class="map-container">
            <Basemap :zoom='9' :center="[116.555774, 29.069983]" />
        </div>
        <!-- 悬浮的介绍内容 -->
        <div class="info-cards">
            <!-- 研究区概况卡片 -->
            <div class="info-card">
                <h3>研究区概况</h3>
                <p>地处江西省北部，长江中下游南岸。</p>
                <div class="divider"></div>
                <div class="location-images">
                    <div class="image-item">
                        <img src="/src/assets/images/洪水期.png" alt="洪水期">
                        <span>洪水期</span>
                    </div>
                    <div class="image-item">
                        <img src="/src/assets/images/枯水期.png" alt="枯水期">
                        <span>枯水期</span>
                    </div>
                </div>
            </div>

            <!-- 自然特征卡片 -->
            <div class="info-card">
                <h3>自然特征</h3>
                <ul>
                    <li>
                        <strong>湖泊面积：</strong>
                        正常水位情况下，面积约有3914平方公里，容积达300亿立方米。
                    </li>
                    <li>
                        <strong>地形地貌：</strong>
                        流域地势高北低，由周边向内倾斜，形成以鄱阳湖区平原为底部向北开口的漏斗型大盆地。
                    </li>
                    <li>
                        <strong>水系：</strong>
                        湖水主要来自赣江、抚河、信江、饶河、修水五大水系，上承五河之水，下接长江。
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script setup>
import Basemap from "@/components/baseMap.vue";
</script>

<style lang="less" scoped>
.introduce {
    position: relative;
    width: calc(100vw - 250px);
    height: 100%;

    .map-container {
        width: 100%;
        height: 100%;
    }

    .info-cards {
        position: absolute;
        top: 20px;
        right: 20px;
        display: flex;
        flex-direction: column;
        gap: 20px;
        max-width: 400px;

        .info-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px 10px 10px 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

            h3 {
                color: #1890ff;
                font-size: 18px;
                margin-bottom: 12px;
                font-weight: bold;
            }

            p {
                color: #333;
                line-height: 1.6;
                margin-bottom: 12px;
            }

            .divider {
                height: 1px;
                background: #e8e8e8;
                margin: 12px 0;
            }

            .location-images {
                display: flex;
                gap: 16px;
                justify-content: center;
                margin-top: 12px;

                .image-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;

                    img {
                        width: 120px;
                        height: 120px;
                        object-fit: cover;
                        border-radius: 8px;
                    }

                    span {
                        font-size: 14px;
                        color: #666;
                    }
                }
            }

            ul {
                list-style: none;
                padding: 0;

                li {
                    margin-bottom: 12px;
                    line-height: 1.6;
                    color: #333;

                    strong {
                        color: #1890ff;
                        margin-right: 8px;
                    }
                }
            }
        }
    }
}
</style>
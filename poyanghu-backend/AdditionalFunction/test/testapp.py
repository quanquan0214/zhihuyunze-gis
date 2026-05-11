import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
import os
import pandas as pd
import chart
from Trend import TrendAnalyzer
from PredictTool import EnvironmentalPredictor

# ===== 设置路径 =====
DATA_DIR = 'D:/Google/RSEI_2000_2022'  #测试数据路径
RASTER_FILE = os.path.join(DATA_DIR, 'RSEI_2022.tif') #显示影像路径
PREDICT_YEARS = 5

# ===== 加载2022影像 =====
src = rasterio.open(RASTER_FILE)
rsei_img = src.read(1)
transform = src.transform

# ===== 点击事件处理函数 =====
def on_click(event):
    if event.inaxes:
        col, row = int(event.xdata), int(event.ydata)
        value = rsei_img[row, col]
        if np.isnan(value) or value == src.nodata:
            print(f"❌ 该像素无值 (row={row}, col={col})")
            return

        # 像素坐标 → 经纬度
        lon, lat = rasterio.transform.xy(transform, row, col)
        print(f"\n🟢 选中像素值: {value:.4f}")
        print(f"🌍 经纬度: ({lat:.6f}, {lon:.6f})")

        # ===== 提取时间序列数据并预测趋势 =====
        df = load_rsei_series(DATA_DIR, (col, row))
        print(f"📈 有效时间序列年份: {df['date'].dt.year.tolist()}")

        # 趋势分析
        trend_analyzer = TrendAnalyzer()
        trend_result = trend_analyzer.analyze_trend(df)

        print(f"📊 趋势类型: {trend_result['trend_type']}, R²={trend_result['r_squared']:.3f}, 强度={trend_result['trend_strength']}")

        # 趋势预测图 !!!!(新加的，可视化)
        chart.plot_trend_with_strength(df, trend_result['trend_type'], trend_result['r_squared'], trend_result['predictions'], title=f"RSEI 2022 像素 ({lat:.6f}, {lon:.6f})")

        # 机器学习预测
        predictor = EnvironmentalPredictor()
        prepared = predictor.prepare_features(df)
        best_model, _ = predictor.train_models(prepared)
        predictions = predictor.predict_future(prepared.iloc[-1], periods=PREDICT_YEARS)

        print(f"🔮 模型: {best_model}")
        for p in predictions[:3]:
            print(f"  第{p['period']}年: 预测值={p['predicted_value']:.4f}")

# ===== 时间序列读取函数 =====
def load_rsei_series(data_dir, coords):
    time_series = []
    for file in sorted(os.listdir(data_dir)):
        if not file.endswith('.tif') or not file.startswith('RSEI_'):  # 过滤非tif文件，运行的是RSEI系列影像
            continue
        year = int(file.split('_')[1].split('.')[0])
        date = pd.Timestamp(f"{year}-07-01")
        with rasterio.open(os.path.join(data_dir, file)) as f:
            val = float(f.read(1)[coords[1], coords[0]])
            if np.isnan(val) or val == f.nodata:
                continue
        time_series.append({'date': date, 'value': val})
    df = pd.DataFrame(time_series)
    return df.sort_values('date')


# ===== 图像可视化 =====
plt.figure(figsize=(10, 8))
plt.imshow(rsei_img, cmap='viridis')
plt.title('点击 RSEI_2022.tif 栅格获取趋势预测')
plt.xlabel('列 (x)')
plt.ylabel('行 (y)')
cursor = Cursor(plt.gca(), useblit=True, color='red', linewidth=1)
plt.colorbar(label='RSEI')
plt.connect('button_press_event', on_click)
plt.show()

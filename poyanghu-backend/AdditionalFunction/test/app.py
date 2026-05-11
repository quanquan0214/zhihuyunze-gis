import os
import rasterio
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from Trend import TrendAnalyzer
from PredictTool import EnvironmentalPredictor
from Annormal import AnomalyDetector

# 初始化Flask应用并配置CORS
app = Flask(__name__)
# 配置CORS：允许所有来源、支持POST/GET/OPTIONS、允许Content-Type头
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# 配置
DATA_DIR = 'D:/Google/RSEI_2000_2022'
PREDICT_YEARS = 5

def load_rsei_series(data_dir, coords):
    time_series = []
    for file in sorted(os.listdir(data_dir)):
        if not file.endswith('.tif') or not file.startswith('RSEI_'):
            continue
        year = int(file.split('_')[1].split('.')[0])
        date = pd.Timestamp(f"{year}-07-01")
        with rasterio.open(os.path.join(data_dir, file)) as f:
            val = float(f.read(1)[coords[1], coords[0]])
            if np.isnan(val) or val == f.nodata:
                continue
        time_series.append({'date': date, 'value': val})
    return pd.DataFrame(time_series).sort_values('date')

@app.route('/predict', methods=['OPTIONS'])
def handle_options():
    response = jsonify({
        "message": "Preflight check passed",
        "allowed_methods": ["POST", "OPTIONS"]
    })
    return response

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    year = data.get('year', 2022)

    if not all([lat, lon]):
        return jsonify({'message': '缺少经纬度参数'}), 400

    try:
        raster_file = os.path.join(DATA_DIR, f'RSEI_{year}.tif')
        with rasterio.open(raster_file) as src:
            row, col = src.index(lon, lat)
            data_array = src.read(1)
            value = data_array[row, col]

            if np.isnan(value) or value == src.nodata:
                return jsonify({'message': '所选像素无有效数据'}), 400

            df = load_rsei_series(DATA_DIR, (col, row))
            valid_years = df['date'].dt.year.tolist()

            detector = AnomalyDetector()
            anomalies = detector.detect_anomalies(df.to_dict('records'))

            values_data = df['value'].tolist()
            dates_data = df['date'].dt.strftime('%Y-%m-%d').tolist()

            trend_analyzer = TrendAnalyzer()
            trend_result = trend_analyzer.analyze_trend(df)

            predictor = EnvironmentalPredictor()
            prepared = predictor.prepare_features(df)
            best_model, _ = predictor.train_models(prepared)
            predictions = predictor.predict_future(prepared.iloc[-1], periods=PREDICT_YEARS)

            # 安全处理数值转换
            def safe_round(val, digits=4):
                try:
                    if isinstance(val, (int, float, np.number)):
                        return round(float(val), digits)
                    return 0.0
                except:
                    return 0.0

            response_data = {
                'pixel_value': safe_round(value),
                'coordinates': {'lat': lat, 'lon': lon},
                'time_series': {
                    'values': [safe_round(x, 6) for x in values_data]
                },
                'anomalies': [{
                    'date': a['date'].strftime('%Y-%m-%d') if hasattr(a['date'], 'strftime') else a['date'],
                    'value': safe_round(a['value']),
                    'severity': a['severity']
                } for a in anomalies],
                'trend_analysis': {
                    'trend_type': trend_result.get('trend_type', 'unknown'),
                    'r_squared': safe_round(trend_result.get('r_squared', 0), 3),
                    'trend_strength': trend_result.get('trend_strength', 'unknown'),
                    'predictions': []  # Changed to empty list as requested
                },
                'ml_prediction': {
                    'predictions': [{
                        'period': p.get('period', ''),
                        'predicted_value': safe_round(p.get('predicted_value', 0))
                    } for p in predictions[:3]]
                }
            }
            return jsonify(response_data)

    except Exception as e:
        return jsonify({'message': f'服务器错误: {str(e)}'}), 500

@app.route('/')
def index():
    return 'RSEI预测API服务已运行（包含异常检测版）'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6419, debug=True)


import os
import rasterio
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from Trend import TrendAnalyzer
from PredictTool import EnvironmentalPredictor
from Annormal import AnomalyDetector

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

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
    test_case = data.get('test_case', 0)  # 0=默认, 1=测试时间戳, 2=测试舍入, 3=测试模型

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

            # 根据测试用例修改数据预处理方式
            if test_case == 1:
                # 测试方案1：改用年份偏移替代时间戳
                df['time_numeric'] = df['date'].dt.year - df['date'].dt.year.min()
                test_description = "使用年份偏移(2000=0,2001=1...)替代时间戳"
            else:
                # 默认情况：使用原始时间戳转换
                df['time_numeric'] = pd.to_datetime(df['date']).map(pd.Timestamp.timestamp)
                test_description = "使用原始时间戳转换"

            valid_years = df['date'].dt.year.tolist()

            detector = AnomalyDetector()
            anomalies = detector.detect_anomalies(df.to_dict('records'))

            values_data = df['value'].tolist()
            dates_data = df['date'].dt.strftime('%Y-%m-%d').tolist()

            trend_analyzer = TrendAnalyzer()

            # 测试方案3：强制使用线性模型
            if test_case == 3:
                # 临时修改TrendAnalyzer使用线性模型
                trend_analyzer.models['polynomial'] = trend_analyzer.models['linear']
                test_description = "强制使用线性模型替代多项式模型"

            trend_result = trend_analyzer.analyze_trend(df)

            # 获取原始预测值用于诊断
            raw_predictions = trend_result.get('predictions', [])
            if test_case == 2:
                # 测试方案2：禁用舍入，显示原始值
                trend_result['raw_predictions'] = [float(x['predicted_value']) for x in raw_predictions]
                test_description = "禁用舍入，显示原始预测值"
            else:
                # 默认情况：应用safe_round
                def safe_round(val, digits=4):
                    try:
                        if isinstance(val, (int, float, np.number)):
                            return round(float(val), digits)
                        return 0.0
                    except:
                        return 0.0

                trend_result['predictions_rounded'] = [safe_round(x['predicted_value']) for x in raw_predictions]

            predictor = EnvironmentalPredictor()
            prepared = predictor.prepare_features(df)
            best_model, _ = predictor.train_models(prepared)
            predictions = predictor.predict_future(prepared.iloc[-1], periods=PREDICT_YEARS)

            response_data = {
                'test_case': test_description,
                'pixel_value': float(value),
                'coordinates': {'lat': lat, 'lon': lon},
                'valid_years': valid_years,
                'time_series': {
                    'dates': dates_data,
                    'values': [float(x) for x in values_data]
                },
                'anomalies': [{
                    'date': a['date'].strftime('%Y-%m-%d') if hasattr(a['date'], 'strftime') else a['date'],
                    'value': float(a['value']),
                    'severity': a['severity'],
                    'method': a['method'],
                    'score': float(a.get('anomaly_score', a.get('z_score', a.get('distance_from_median', 0))))
                } for a in anomalies],
                'trend_analysis': {
                    'trend_type': trend_result.get('trend_type', 'unknown'),
                    'r_squared': float(trend_result.get('r_squared', 0)),
                    'trend_strength': trend_result.get('trend_strength', 'unknown'),
                    'predictions': [float(x['predicted_value']) for x in raw_predictions],
                    'raw_predictions': trend_result.get('raw_predictions', None),
                    'predictions_rounded': trend_result.get('predictions_rounded', None)
                },
                'ml_prediction': {
                    'model': best_model,
                    'predictions': [{
                        'period': p.get('period', ''),
                        'predicted_value': float(p.get('predicted_value', 0))
                    } for p in predictions[:3]]
                }
            }
            return jsonify(response_data)

    except Exception as e:
        return jsonify({'message': f'服务器错误: {str(e)}'}), 500


@app.route('/')
def index():
    return 'RSEI预测API服务已运行（带诊断测试版）'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6419, debug=True)
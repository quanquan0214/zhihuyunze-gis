from flask import Flask, request, jsonify
import pandas as pd
from scipy.spatial import cKDTree
import numpy as np


class PointDataService:
    def __init__(self):
        self.data_cache = {}
        self.spatial_index = None

    def get_point_data(self, lat, lng, radius=500):
        """获取指定坐标附近的历史数据"""

        # 使用空间索引查找附近数据点
        if self.spatial_index is None:
            self._build_spatial_index()

        # 查找半径范围内的数据点
        distances, indices = self.spatial_index.query(
            [lat, lng],
            k=10,
            distance_upper_bound=radius / 111000  # 转换为度
        )

        # 获取数据并按时间排序
        nearby_data = []
        for idx in indices:
            if idx < len(self.all_data):
                nearby_data.append(self.all_data.iloc[idx])

        # 按时间聚合数据
        df = pd.DataFrame(nearby_data)
        return self._aggregate_temporal_data(df)

    def _aggregate_temporal_data(self, df):
        """按时间期间聚合数据"""
        return df.groupby(['year', 'period']).agg({
            'water_quality': 'mean',
            'depth': 'mean',
            'vegetation_cover': 'mean'
        }).reset_index()


# API接口集成
@app.route('/api/ml-analysis', methods=['POST'])
def ml_analysis():
    data = request.json
    coordinates = data['coordinates']
    analysis_type = data['analysis_type']

    # 获取历史数据
    historical_data = point_data_service.get_point_data(
        coordinates['lat'], coordinates['lng']
    )

    results = {}

    if 'trend' in analysis_type:
        trend_analyzer = TrendAnalyzer()
        results['trend_analysis'] = trend_analyzer.analyze_trend(historical_data)

        anomaly_detector = AnomalyDetector()
        results['anomalies'] = anomaly_detector.detect_anomalies(historical_data)

    if 'prediction' in analysis_type:
        predictor = EnvironmentalPredictor()
        prepared_data = predictor.prepare_features(historical_data)
        model_name, scores = predictor.train_models(prepared_data)
        results['predictions'] = predictor.predict_future(prepared_data.iloc[-1])
        results['model_performance'] = {'best_model': model_name, 'scores': scores}

    if 'seasonal' in analysis_type:
        seasonal_analyzer = SeasonalAnalyzer()
        results['seasonal_analysis'] = seasonal_analyzer.decompose_seasonal_patterns(historical_data)
        results['seasonal_forecast'] = seasonal_analyzer.generate_seasonal_forecast(historical_data)

    if 'risk' in analysis_type:
        risk_system = RiskAssessmentSystem()
        current_data = historical_data[-1] if historical_data else {}
        predictions = results.get('predictions', [])
        results['risk_assessment'] = risk_system.assess_current_risk(current_data, predictions)

    return jsonify(results)
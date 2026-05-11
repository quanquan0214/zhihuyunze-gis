from flask import Flask, request, jsonify
from flask_cors import CORS  # 新增这行
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from datetime import datetime
import json
import os
import pandas as pd
import rasterio
from rasterio.transform import xy

# class PointDataService:
#     def __init__(self):
#         self.data_cache = {}
#         self.spatial_index = None
#         self.data_dir = 'D:/Google/RSEI_2000_2022/'
#         self.all_data = self._load_rsei_data()
#
#     # def _load_rsei_data(self):
#     #     """Load RSEI time series data"""
#     #     data_list = []
#     #     for year in range(2000, 2023):
#     #         file_path = os.path.join(self.data_dir, f'RSEI_{year}.tif')
#     #         print(f'Loading {file_path}')
#     #
#     #         if os.path.exists(file_path):
#     #             # Load raster data and convert to points
#     #             # This is a simplified example - you'll need to implement proper raster reading
#     #             pass
#     #
#     #     print(len(data_list))
#     #     return pd.DataFrame(data_list)
#     def _load_rsei_data(self):
#         """Load RSEI time series data from TIFF files and convert to point data"""
#         data_list = []
#
#         for year in range(2000, 2023):
#             file_path = os.path.join(self.data_dir, f'RSEI_{year}.tif')
#             print(f'Loading {file_path}')
#
#             if os.path.exists(file_path):
#                 try:
#                     with rasterio.open(file_path) as src:
#                         data = src.read(1)  # 读取单波段数据
#                         transform = src.transform
#                         nodata = src.nodatavals[0] if src.nodatavals[0] is not None else np.nan
#
#                         # 遍历所有像素
#                         rows, cols = data.shape
#                         for row in range(rows):
#                             for col in range(cols):
#                                 value = data[row, col]
#                                 if np.isnan(value) or value == nodata:
#                                     continue
#                                 x, y = xy(transform, col, row)  # 注意行列顺序
#                                 data_list.append({
#                                     'lat': y,
#                                     'lng': x,
#                                     'year': year,
#                                     'rsei_value': float(value)
#                                 })
#                 except Exception as e:
#                     print(f"Error loading {file_path}: {str(e)}")
#                     continue
#
#         print(f"Loaded {len(data_list)} data points")
#         return pd.DataFrame(data_list)
#
#     def _build_spatial_index(self):
#         """Build spatial index for efficient querying"""
#         if len(self.all_data) > 0:
#             coords = self.all_data[['lat', 'lng']].values
#             self.spatial_index = cKDTree(coords)
#
#
#     def get_point_data(self, lat, lng, radius=500):
#         """获取指定坐标附近的历史数据"""
#
#         # 使用空间索引查找附近数据点
#         if self.spatial_index is None:
#             self._build_spatial_index()
#
#         # 查找半径范围内的数据点
#         distances, indices = self.spatial_index.query(
#             [lat, lng],
#             k=10,
#             distance_upper_bound=radius/111000  # 转换为度
#         )
#
#         # 获取数据并按时间排序
#         nearby_data = []
#         for idx in indices:
#             if idx < len(self.all_data):
#                 nearby_data.append(self.all_data.iloc[idx])
#
#         # 按时间聚合数据
#         df = pd.DataFrame(nearby_data)
#         return self._aggregate_temporal_data(df)
#
#     def _aggregate_temporal_data(self, df):
#         """按时间期间聚合数据"""
#         return df.groupby(['year', 'period']).agg({
#             'water_quality': 'mean',
#             'depth': 'mean',
#             'vegetation_cover': 'mean'
#         }).reset_index()





class PointDataService:
    def __init__(self, data_dir='D:/Google/RSEI_2000_2022/'):
        """
        初始化RSEI数据服务
        Args:
            data_dir: 存储RSEI TIFF文件的目录路径
        """
        self.data_cache = {}
        self.spatial_index = None
        self.data_dir = data_dir
        self.all_data = self._load_rsei_data()
        self._build_spatial_index()

    def _load_rsei_data(self):
        """从TIFF文件加载RSEI时序数据并转换为点数据"""
        data_list = []

        for year in range(2000, 2005):
            file_path = os.path.join(self.data_dir, f'RSEI_{year}.tif')
            print(f'Loading {file_path}')

            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                continue

            try:
                with rasterio.open(file_path) as src:
                    data = src.read(1)  # 读取单波段数据
                    transform = src.transform
                    nodata = src.nodatavals[0] if src.nodatavals[0] is not None else np.nan

                    # 遍历所有有效像素
                    rows, cols = data.shape
                    for row in range(rows):
                        for col in range(cols):
                            value = data[row, col]
                            if np.isnan(value) or value == nodata:
                                continue

                            # 转换坐标
                            x, y = xy(transform, col, row)

                            # 模拟其他环境指标（实际应用中应从其他数据源加载）
                            temperature = 20 + 10 * np.sin(year % 10)  # 模拟温度年际变化
                            vegetation_cover = 0.5 + 0.3 * np.cos(col / 1000)  # 模拟空间变化

                            data_list.append({
                                'lat': y,  # 纬度
                                'lng': x,  # 经度
                                'year': year,
                                'month': 6,  # 默认6月（可根据实际数据修改）
                                'date': datetime(year, 6, 1),  # 标准化日期
                                'rsei_value': float(value),
                                'temperature': temperature,
                                'vegetation_cover': vegetation_cover,
                                'water_quality': max(0, min(100, value * 100))
                            })  # 模拟水质指标
            except Exception as e:
                print(f"加载 {file_path} 失败: {str(e)}")
                continue

        print(f"成功加载 {len(data_list)} 个数据点")
        return pd.DataFrame(data_list)

    def _build_spatial_index(self):
        """构建空间索引以加速查询"""
        if len(self.all_data) > 0:
            try:
                coords = self.all_data[['lat', 'lng']].values
                self.spatial_index = cKDTree(coords)
                print("空间索引构建完成")
            except Exception as e:
                print(f"构建空间索引失败: {str(e)}")
                self.spatial_index = None

    def get_point_data(self, lat, lng, radius=500, max_points=1000):
        """
        获取指定坐标附近的历史数据
        Args:
            lat: 纬度
            lng: 经度
            radius: 搜索半径（米）
            max_points: 最大返回点数
        Returns:
            list: 包含标准化字段的字典列表
        """
        if self.spatial_index is None:
            self._build_spatial_index()
            if self.spatial_index is None:
                return []

        try:
            # 查询附近点（半径转换为度，近似值）
            point = np.array([lat, lng])
            radius_deg = radius / 111000  # 1度≈111km
            distances, indices = self.spatial_index.query(
                point,
                k=min(max_points, len(self.all_data)),
                distance_upper_bound=radius_deg
            )

            # 过滤无效结果
            valid_mask = distances < np.inf
            nearby_data = self.all_data.iloc[indices[valid_mask]].copy()

            if nearby_data.empty:
                print(f"坐标 ({lat}, {lng}) 附近 {radius} 米内未找到数据")
                return []

            # 标准化输出格式
            nearby_data['value'] = nearby_data['rsei_value']  # 统一value字段
            return nearby_data.to_dict('records')

        except Exception as e:
            print(f"查询数据失败: {str(e)}")
            return []

    def get_area_stats(self, lat, lng, radius=1000):
        """获取区域统计信息（扩展功能示例）"""
        nearby_data = self.get_point_data(lat, lng, radius)
        if not nearby_data:
            return None

        df = pd.DataFrame(nearby_data)
        return {
            'rsei_mean': df['rsei_value'].mean(),
            'temperature_range': (df['temperature'].min(), df['temperature'].max()),
            'vegetation_cover_avg': df['vegetation_cover'].mean(),
            'data_points': len(df)
        }


from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

class TrendAnalyzer:
    def __init__(self):
        self.models = {
            'linear': LinearRegression(),
            'polynomial': Pipeline([
                ('poly', PolynomialFeatures(degree=2)),
                ('linear', LinearRegression())
            ]),
            'seasonal': None  # 季节性模型
        }

    def analyze_trend(self, time_series_data):
        """分析时间序列趋势"""

        # 数据预处理
        df = pd.DataFrame(time_series_data)
        df['time_numeric'] = pd.to_datetime(df['date']).map(pd.Timestamp.timestamp)

        X = df[['time_numeric']].values
        y = df['value'].values

        results = {}

        # 线性趋势
        linear_model = self.models['linear'].fit(X, y)
        linear_pred = linear_model.predict(X)
        linear_r2 = r2_score(y, linear_pred)

        # 多项式趋势
        poly_model = self.models['polynomial'].fit(X, y)
        poly_pred = poly_model.predict(X)
        poly_r2 = r2_score(y, poly_pred)

        # 选择最佳模型
        best_model = 'linear' if linear_r2 > poly_r2 else 'polynomial'
        best_r2 = max(linear_r2, poly_r2)

        # 生成未来预测
        future_predictions = self._generate_predictions(
            self.models[best_model], X, df['time_numeric'].max()
        )

        return {
            'trend_type': best_model,
            'r_squared': best_r2,
            'slope': linear_model.coef_[0] if best_model == 'linear' else None,
            'predictions': future_predictions,
            'trend_strength': self._classify_trend_strength(best_r2)
        }

    def _generate_predictions(self, model, X, last_time, periods=12):
        """生成未来预测"""
        time_interval = np.mean(np.diff(X.flatten()))
        future_times = np.array([
            last_time + (i + 1) * time_interval
            for i in range(periods)
        ]).reshape(-1, 1)

        future_values = model.predict(future_times)

        return [
            {
                'time': time,
                'predicted_value': value,
                'confidence_interval': self._calculate_confidence_interval(model, time)
            }
            for time, value in zip(future_times.flatten(), future_values)
        ]

    def _classify_trend_strength(self, r2):
        """趋势强度分类"""
        if r2 > 0.8:
            return 'strong'
        elif r2 > 0.5:
            return 'moderate'
        elif r2 > 0.3:
            return 'weak'
        else:
            return 'no_trend'


from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import scipy.stats as stats

class AnomalyDetector:
    def __init__(self):
        self.methods = {
            'isolation_forest': IsolationForest(contamination=0.1, random_state=42),
            'z_score': None,
            'iqr': None,
            'seasonal': None
        }

    def detect_anomalies(self, time_series_data, method='isolation_forest'):
        """检测时间序列中的异常值"""

        df = pd.DataFrame(time_series_data)
        values = df['value'].values.reshape(-1, 1)

        anomalies = []

        if method == 'isolation_forest':
            # 隔离森林方法
            scaler = StandardScaler()
            scaled_values = scaler.fit_transform(values)

            outliers = self.methods['isolation_forest'].fit_predict(scaled_values)
            anomaly_scores = self.methods['isolation_forest'].decision_function(scaled_values)

            for i, (outlier, score) in enumerate(zip(outliers, anomaly_scores)):
                if outlier == -1:  # 异常值
                    anomalies.append({
                        'index': i,
                        'date': df.iloc[i]['date'],
                        'value': df.iloc[i]['value'],
                        'anomaly_score': abs(score),
                        'severity': self._classify_anomaly_severity(abs(score)),
                        'method': 'isolation_forest'
                    })

        elif method == 'z_score':
            # Z-score方法
            z_scores = np.abs(stats.zscore(values.flatten()))
            threshold = 2.5

            for i, z_score in enumerate(z_scores):
                if z_score > threshold:
                    anomalies.append({
                        'index': i,
                        'date': df.iloc[i]['date'],
                        'value': df.iloc[i]['value'],
                        'z_score': z_score,
                        'severity': self._classify_anomaly_severity(z_score),
                        'method': 'z_score'
                    })

        elif method == 'iqr':
            # IQR方法
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            for i, value in enumerate(values.flatten()):
                if value < lower_bound or value > upper_bound:
                    severity = abs(value - np.median(values)) / np.std(values)
                    anomalies.append({
                        'index': i,
                        'date': df.iloc[i]['date'],
                        'value': value,
                        'distance_from_median': abs(value - np.median(values)),
                        'severity': self._classify_anomaly_severity(severity),
                        'method': 'iqr'
                    })

        return sorted(anomalies, key=lambda x: x.get('anomaly_score', x.get('z_score', 0)), reverse=True)

    def _classify_anomaly_severity(self, score):
        """异常值严重程度分类"""
        if score > 3:
            return 'severe'
        elif score > 2:
            return 'moderate'
        else:
            return 'mild'


from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import joblib

class EnvironmentalPredictor:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
        }
        self.best_model = None
        self.feature_importance = {}

    def prepare_features(self, historical_data):
        """特征工程"""
        df = pd.DataFrame(historical_data)

        # 时间特征
        df['year'] = pd.to_datetime(df['date']).dt.year
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['season'] = df['month'].map(self._get_season)

        # 滞后特征
        for lag in [1, 2, 3, 6, 12]:
            df[f'lag_{lag}'] = df['value'].shift(lag)

        # 滚动统计特征
        for window in [3, 6, 12]:
            df[f'rolling_mean_{window}'] = df['value'].rolling(window=window).mean()
            df[f'rolling_std_{window}'] = df['value'].rolling(window=window).std()

        # 趋势特征
        df['linear_trend'] = np.arange(len(df))
        df['value_diff'] = df['value'].diff()
        df['value_pct_change'] = df['value'].pct_change()

        # 外部特征（如果有的话）
        if 'temperature' in df.columns:
            df['temp_anomaly'] = df['temperature'] - df['temperature'].rolling(12).mean()
        if 'precipitation' in df.columns:
            df['precip_anomaly'] = df['precipitation'] - df['precipitation'].rolling(12).mean()

        return df.dropna()

    def train_models(self, prepared_data):
        """训练多个模型并选择最佳模型"""

        feature_columns = [col for col in prepared_data.columns
                          if col not in ['date', 'value']]
        X = prepared_data[feature_columns]
        y = prepared_data['value']

        # 时间序列交叉验证
        tscv = TimeSeriesSplit(n_splits=5)

        model_scores = {}
        for name, model in self.models.items():
            scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_squared_error')
            model_scores[name] = -scores.mean()
            print(f"{name}: RMSE = {np.sqrt(-scores.mean()):.4f}")

        # 选择最佳模型
        best_model_name = min(model_scores, key=model_scores.get)
        self.best_model = self.models[best_model_name]
        self.best_model.fit(X, y)

        # 特征重要性
        if hasattr(self.best_model, 'feature_importances_'):
            self.feature_importance = dict(zip(feature_columns, self.best_model.feature_importances_))

        return best_model_name, model_scores

    def predict_future(self, last_data, periods=12):
        """预测未来值"""
        predictions = []
        current_data = last_data.copy()

        for i in range(periods):
            # 准备预测特征
            features = self._prepare_prediction_features(current_data, i)

            # 预测
            pred_value = self.best_model.predict([features])[0]

            # 计算预测区间
            confidence_interval = self._calculate_prediction_interval(features, pred_value)

            predictions.append({
                'period': i + 1,
                'predicted_value': pred_value,
                'lower_bound': confidence_interval[0],
                'upper_bound': confidence_interval[1],
                'confidence_level': 0.95
            })

            # 更新当前数据用于下一次预测
            current_data = self._update_data_for_next_prediction(current_data, pred_value)

        return predictions

    def _get_season(self, month):
        """获取季节"""
        if month in [12, 1, 2]:
            return 0  # 冬季
        elif month in [3, 4, 5]:
            return 1  # 春季
        elif month in [6, 7, 8]:
            return 2  # 夏季
        else:
            return 3  # 秋季



import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

class RiskAssessmentSystem:
    def __init__(self):
        self.risk_classifier = RandomForestClassifier(n_estimators=200, random_state=42)
        self.risk_levels = ['low', 'medium', 'high', 'critical']
        self.threshold_config = {
            'water_quality': {'low': 80, 'medium': 60, 'high': 40, 'critical': 20},
            'vegetation_cover': {'low': 80, 'medium': 60, 'high': 40, 'critical': 20},
            'biodiversity_index': {'low': 0.8, 'medium': 0.6, 'high': 0.4, 'critical': 0.2}
        }

    def assess_current_risk(self, current_data, predictions):
        """评估当前和未来风险等级"""

        risk_assessment = {
            'current_risk': {},
            'future_risk': {},
            'risk_factors': [],
            'recommendations': []
        }

        # 当前风险评估
        for parameter, thresholds in self.threshold_config.items():
            if parameter in current_data:
                current_value = current_data[parameter]
                risk_level = self._classify_risk_level(current_value, thresholds)
                risk_assessment['current_risk'][parameter] = {
                    'value': current_value,
                    'risk_level': risk_level,
                    'trend': self._calculate_trend(parameter, current_data)
                }

        # 未来风险预测
        for prediction in predictions:
            period = prediction['period']
            for parameter in self.threshold_config.keys():
                if parameter in prediction:
                    future_value = prediction['predicted_value']
                    risk_level = self._classify_risk_level(future_value, self.threshold_config[parameter])

                    if period not in risk_assessment['future_risk']:
                        risk_assessment['future_risk'][period] = {}

                    risk_assessment['future_risk'][period][parameter] = {
                        'predicted_value': future_value,
                        'risk_level': risk_level,
                        'confidence_interval': [prediction['lower_bound'], prediction['upper_bound']]
                    }

        # 识别风险因子
        risk_assessment['risk_factors'] = self._identify_risk_factors(current_data, predictions)

        # 生成建议
        risk_assessment['recommendations'] = self._generate_recommendations(risk_assessment)

        return risk_assessment

    def setup_alert_system(self, thresholds, contact_info):
        """设置预警系统"""

        alert_config = {
            'thresholds': thresholds,
            'contacts': contact_info,
            'alert_methods': ['email', 'sms', 'dashboard'],
            'escalation_rules': {
                'medium': {'delay': 24, 'recipients': ['operator']},
                'high': {'delay': 6, 'recipients': ['operator', 'supervisor']},
                'critical': {'delay': 1, 'recipients': ['operator', 'supervisor', 'emergency']}
            }
        }

        return alert_config

    def check_alerts(self, current_data, predictions, alert_config):
        """检查是否需要发送预警"""

        alerts = []

        # 检查当前数据
        for parameter, value in current_data.items():
            if parameter in alert_config['thresholds']:
                threshold = alert_config['thresholds'][parameter]
                if value > threshold['critical']:
                    alerts.append({
                        'type': 'current_critical',
                        'parameter': parameter,
                        'value': value,
                        'threshold': threshold['critical'],
                        'severity': 'critical',
                        'message': f"{parameter}当前值{value}超过临界阈值{threshold['critical']}"
                    })

        # 检查预测数据
        for prediction in predictions[:3]:  # 检查未来3期
            for parameter, pred_data in prediction.items():
                if parameter in alert_config['thresholds']:
                    threshold = alert_config['thresholds'][parameter]
                    pred_value = pred_data['predicted_value']

                    if pred_value > threshold['high']:
                        alerts.append({
                            'type': 'future_risk',
                            'parameter': parameter,
                            'predicted_value': pred_value,
                            'period': prediction['period'],
                            'severity': 'high',
                            'message': f"预测{parameter}在第{prediction['period']}期将达到{pred_value}，存在高风险"
                        })

        return alerts

    def _classify_risk_level(self, value, thresholds):
        """风险等级分类"""
        if value >= thresholds['low']:
            return 'low'
        elif value >= thresholds['medium']:
            return 'medium'
        elif value >= thresholds['high']:
            return 'high'
        else:
            return 'critical'



from scipy import signal
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt

class SeasonalAnalyzer:
    def __init__(self):
        self.seasonal_components = {}
        self.dominant_frequencies = {}

    def decompose_seasonal_patterns(self, time_series_data):
        """分解季节性模式"""

        df = pd.DataFrame(time_series_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').resample('M').mean()  # 月度重采样

        # STL分解（季节和趋势分解）
        from statsmodels.tsa.seasonal import STL

        stl = STL(df['value'], seasonal=13)  # 13个月的季节周期
        decomposition = stl.fit()

        seasonal_component = decomposition.seasonal
        trend_component = decomposition.trend
        residual_component = decomposition.resid

        # 频谱分析识别周期性
        frequencies, power_spectrum = self._frequency_analysis(df['value'].values)
        dominant_periods = self._find_dominant_periods(frequencies, power_spectrum)

        # 季节性强度计算
        seasonal_strength = np.var(seasonal_component) / np.var(df['value'])

        return {
            'seasonal_component': seasonal_component.tolist(),
            'trend_component': trend_component.tolist(),
            'residual_component': residual_component.tolist(),
            'seasonal_strength': seasonal_strength,
            'dominant_periods': dominant_periods,
            'seasonal_patterns': self._identify_seasonal_patterns(seasonal_component)
        }

    def _frequency_analysis(self, values):
        """频谱分析"""
        n = len(values)
        fft_values = fft(values)
        frequencies = fftfreq(n, d=1)  # 假设月度数据
        power_spectrum = np.abs(fft_values) ** 2

        # 只保留正频率
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        power_spectrum = power_spectrum[positive_freq_idx]

        return frequencies, power_spectrum

    def _find_dominant_periods(self, frequencies, power_spectrum, top_n=5):
        """找出主要周期"""
        # 找出功率谱峰值
        peaks, _ = signal.find_peaks(power_spectrum, height=np.mean(power_spectrum))

        # 按功率大小排序
        peak_powers = power_spectrum[peaks]
        sorted_indices = np.argsort(peak_powers)[::-1]

        dominant_periods = []
        for i in sorted_indices[:top_n]:
            peak_idx = peaks[i]
            frequency = frequencies[peak_idx]
            period = 1 / frequency if frequency > 0 else np.inf
            power = peak_powers[i]

            dominant_periods.append({
                'period_months': period,
                'frequency': frequency,
                'power': power,
                'description': self._interpret_period(period)
            })

        return dominant_periods

    def _identify_seasonal_patterns(self, seasonal_component):
        """识别季节性模式"""
        patterns = {}

        # 按月份分组分析
        monthly_values = {}
        for i, value in enumerate(seasonal_component):
            month = (i % 12) + 1
            if month not in monthly_values:
                monthly_values[month] = []
            monthly_values[month].append(value)

        # 计算各月份的平均季节性效应
        monthly_effects = {}
        for month, values in monthly_values.items():
            monthly_effects[month] = {
                'mean_effect': np.mean(values),
                'std_effect': np.std(values),
                'month_name': self._get_month_name(month)
            }

        # 识别季节性特征
        patterns['monthly_effects'] = monthly_effects
        patterns['peak_months'] = self._find_peak_months(monthly_effects)
        patterns['trough_months'] = self._find_trough_months(monthly_effects)
        patterns['seasonal_amplitude'] = max(monthly_effects.values(), key=lambda x: x['mean_effect'])['mean_effect'] - \
                                        min(monthly_effects.values(), key=lambda x: x['mean_effect'])['mean_effect']

        return patterns

    def generate_seasonal_forecast(self, historical_data, forecast_periods=12):
        """基于季节性模式生成预测"""

        decomposition = self.decompose_seasonal_patterns(historical_data)
        seasonal_component = np.array(decomposition['seasonal_component'])
        trend_component = np.array(decomposition['trend_component'])

        # 提取最后一个完整年的季节性模式
        if len(seasonal_component) >= 12:
            recent_seasonal_pattern = seasonal_component[-12:]
        else:
            recent_seasonal_pattern = seasonal_component

        # 趋势外推
        if len(trend_component) >= 3:
            trend_slope = np.mean(np.diff(trend_component[-12:]))  # 最近12个月的趋势
            last_trend = trend_component[-1]
        else:
            trend_slope = 0
            last_trend = np.mean(trend_component)

        # 生成预测
        forecasts = []
        for i in range(forecast_periods):
            # 季节性分量（循环使用）
            seasonal_idx = i % len(recent_seasonal_pattern)
            seasonal_value = recent_seasonal_pattern[seasonal_idx]

            # 趋势分量
            trend_value = last_trend + (i + 1) * trend_slope

            # 组合预测
            forecast_value = trend_value + seasonal_value

            forecasts.append({
                'period': i + 1,
                'forecast_value': forecast_value,
                'trend_component': trend_value,
                'seasonal_component': seasonal_value,
                'confidence_interval': self._calculate_seasonal_confidence_interval(
                    decomposition['residual_component'], forecast_value
                )
            })

        return forecasts

    def _get_month_name(self, month_num):
        """获取月份名称"""
        months = ['一月', '二月', '三月', '四月', '五月', '六月',
                 '七月', '八月', '九月', '十月', '十一月', '十二月']
        return months[month_num - 1]

    def _interpret_period(self, period_months):
        """解释周期含义"""
        if 11 <= period_months <= 13:
            return '年度周期'
        elif 5.5 <= period_months <= 6.5:
            return '半年周期'
        elif 2.8 <= period_months <= 3.2:
            return '季度周期'
        elif period_months < 2:
            return '短期波动'
        else:
            return f'{period_months:.1f}个月周期'



# 修改Flask应用初始化部分
app = Flask(__name__)

CORS(app)  # 新增这行，允许所有跨域请求

# 或者更安全的方式，只允许特定域名
# CORS(app, origins=['http://localhost:*', 'file://*'])

@app.route('/')
def first_page():
    return 'Hello, this in null!'


@app.route('/hello')
def hello_world():
    return 'Hello, World!'

point_data_service = PointDataService()

# API接口集成
@app.route('/api/ml-analysis', methods=['POST'])
def ml_analysis():
    data = request.json
    coordinates = {'lat': 28.85967723955063, 'lng': 116.21337890625001} #data['coordinates']
    analysis_type = data['analysis_type']
    print(coordinates)

    # 获取历史数据
    historical_data = point_data_service.get_point_data(
        coordinates['lat'], coordinates['lng']
    )
    print(historical_data)

    results = {}

    if 'trend' in analysis_type:
        trend_analyzer = TrendAnalyzer()
        results['trend_analysis'] = trend_analyzer.analyze_trend(historical_data)

        anomaly_detector = AnomalyDetector()
        results['anomalies'] = anomaly_detector.detect_anomalies(historical_data)
        # print(results['anomalies'])


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

    response = jsonify(results)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response



# def ml1():
#     # 固定坐标（江西省南昌市附近）
#     fixed_coordinates = {'lat': 28.676470, 'lng': 117.452478}
#     #28.676470, 117.452478
#     # 模拟请求数据（避免依赖前端传入）
#     data = {
#         'analysis_type': ['trend', 'prediction', 'seasonal', 'risk']  # 默认启用所有分析类型
#     }
#
#     print(f"正在分析固定坐标: {fixed_coordinates}")
#
#     # 获取历史数据
#     historical_data = point_data_service.get_point_data(
#         fixed_coordinates['lat'], fixed_coordinates['lng']
#     )
#     print("\n历史数据摘要:")
#     print(historical_data)  # 打印前几行数据
#
#     results = {}
#
#     # 趋势分析
#     if 'trend' in data['analysis_type']:
#         trend_analyzer = TrendAnalyzer()
#         results['trend_analysis'] = trend_analyzer.analyze_trend(historical_data)
#         print("\n趋势分析结果:")
#         print(json.dumps(results['trend_analysis'], indent=2, ensure_ascii=False))
#
#     # 异常检测
#     if 'anomaly' in data['analysis_type']:
#         anomaly_detector = AnomalyDetector()
#         results['anomalies'] = anomaly_detector.detect_anomalies(historical_data)
#         print("\n异常检测结果:")
#         print(json.dumps(results['anomalies'], indent=2, ensure_ascii=False))
#
#     # 预测未来值
#     if 'prediction' in data['analysis_type']:
#         predictor = EnvironmentalPredictor()
#         prepared_data = predictor.prepare_features(historical_data)
#         model_name, scores = predictor.train_models(prepared_data)
#         results['predictions'] = predictor.predict_future(prepared_data.iloc[-1])
#         print("\n未来预测结果:")
#         for pred in results['predictions']:
#             print(f"周期 {pred['period']}: 预测值={pred['predicted_value']:.2f}")
#
#     # 季节性分析
#     if 'seasonal' in data['analysis_type']:
#         seasonal_analyzer = SeasonalAnalyzer()
#         results['seasonal_analysis'] = seasonal_analyzer.decompose_seasonal_patterns(historical_data)
#         print("\n季节性分析结果:")
#         print(f"主要周期: {results['seasonal_analysis']['dominant_periods'][0]['description']}")
#
#     # 风险评估
#     if 'risk' in data['analysis_type']:
#         risk_system = RiskAssessmentSystem()
#         current_data = historical_data.iloc[-1].to_dict() if not historical_data.empty else {}
#         predictions = results.get('predictions', [])
#         results['risk_assessment'] = risk_system.assess_current_risk(current_data, predictions)
#         print("\n风险评估结果:")
#         for param, risk in results['risk_assessment']['current_risk'].items():
#             print(f"{param}: 风险等级={risk['risk_level']}")
#
#     return jsonify({"status": "分析完成", "fixed_coordinates": fixed_coordinates})
#
# ml1()
# 初始化服务
service = PointDataService()

# 查询单点数据
point_data = service.get_point_data(28.86, 116.21, radius=500)
print(f"获取到 {len(point_data)} 条数据")

# 传递给分析类
trend_analyzer = TrendAnalyzer()
trend_result = trend_analyzer.analyze_trend(point_data)  # 无需额外转换

# 获取区域统计
stats1 = service.get_area_stats(28.86, 116.21, radius=1000)
print(f"区域RSEI均值: {stats1['rsei_mean']:.2f}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6433, debug=True)
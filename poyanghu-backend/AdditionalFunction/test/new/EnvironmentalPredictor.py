from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import joblib
import pandas as pd
import numpy as np

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
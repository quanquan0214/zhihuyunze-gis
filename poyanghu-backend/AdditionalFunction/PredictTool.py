## 二、机器学习预测功能实现
### 2.1 基于历史数据的趋势预测

#### 时间序列预测模型
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
        # if 'temperature' in df.columns:
        #     df['temp_anomaly'] = df['temperature'] - df['temperature'].rolling(12).mean()
        # if 'precipitation' in df.columns:
        #     df['precip_anomaly'] = df['precipitation'] - df['precipitation'].rolling(12).mean()

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

    def _prepare_prediction_features(self, current_data, i):
        """
        构造下一期预测所需特征（与训练时使用的特征结构一致）
        """
        year = current_data['year'] + 1
        month = 7  # 模拟年中月份
        season = self._get_season(month)

        lag_1 = current_data['value']
        lag_2 = current_data.get('lag_1', lag_1)
        lag_3 = current_data.get('lag_2', lag_2)
        lag_6 = current_data.get('lag_3', lag_3)
        lag_12 = current_data.get('lag_6', lag_6)

        rolling_mean_3 = np.mean([lag_1, lag_2, lag_3])
        rolling_mean_6 = np.mean([lag_1, lag_2, lag_3, lag_6])
        rolling_mean_12 = rolling_mean_6  # 简化处理

        rolling_std_3 = np.std([lag_1, lag_2, lag_3])
        rolling_std_6 = np.std([lag_1, lag_2, lag_3, lag_6])
        rolling_std_12 = rolling_std_6

        linear_trend = current_data['linear_trend'] + 1
        value_diff = lag_1 - lag_2
        value_pct_change = (lag_1 - lag_2) / lag_2 if lag_2 != 0 else 0

        # temp_anomaly = current_data.get('temp_anomaly', 0)
        # precip_anomaly = current_data.get('precip_anomaly', 0)

        return [
            year, month, season,
            lag_1, lag_2, lag_3, lag_6, lag_12,
            rolling_mean_3, rolling_mean_6, rolling_mean_12,
            rolling_std_3, rolling_std_6, rolling_std_12,
            linear_trend,
            value_diff,
            value_pct_change
        ]
            # temp_anomaly,
            # precip_anomaly

    def _update_data_for_next_prediction(self, current_data, predicted_value):
        """将预测结果添加到当前数据结构中，用于下一轮特征构造"""
        updated = current_data.copy()

        # 更新滞后值
        updated['lag_3'] = updated.get('lag_2', updated['value'])
        updated['lag_2'] = updated.get('lag_1', updated['value'])
        updated['lag_1'] = updated['value']
        updated['value'] = predicted_value

        # 时间推进
        updated['year'] += 1
        updated['linear_trend'] += 1

        # 差分更新
        updated['value_diff'] = updated['value'] - updated['lag_1']
        updated['value_pct_change'] = (
            (updated['value'] - updated['lag_1']) / updated['lag_1']
            if updated['lag_1'] != 0 else 0
        )

        # 可保留气候异常值不变，或设为0
        return updated

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

    # def _calculate_prediction_interval(self, features, prediction, confidence_level=0.95):
    #     """
    #     基于回归模型的集成方法估计预测区间。
    #     对于随机森林和梯度提升方法，通过子模型的预测分布估计置信区间。
    #     对于神经网络，返回固定误差范围。
    #     """
    #     import scipy.stats as st
    #
    #     # 如果是集成模型，可以从多个子模型中获取预测分布
    #     if hasattr(self.best_model, 'estimators_'):
    #         all_preds = np.array([tree.predict([features])[0] for tree in self.best_model.estimators_])
    #         mean = np.mean(all_preds)
    #         std = np.std(all_preds)
    #
    #         # 计算置信区间
    #         z = st.norm.ppf(0.5 + confidence_level / 2)
    #         lower = mean - z * std
    #         upper = mean + z * std
    #         return lower, upper
    #
    #     # 对于不支持估计不确定性的模型（如神经网络），使用固定宽度区间
    #     fixed_margin = 0.05 * prediction
    #     return prediction - fixed_margin, prediction + fixed_margin

    def _calculate_prediction_interval(self, features, prediction, alpha=0.05):
        """
        计算预测值的置信区间，仅适用于集成模型（如 RandomForest、GradientBoosting）
        对于神经网络模型则返回 ±5% 区间作为近似
        """
        import scipy.stats as st

        if hasattr(self.best_model, 'estimators_'):
            # 对于 RandomForest 和 GradientBoosting
            try:
                if isinstance(self.best_model.estimators_, np.ndarray):
                    # GradientBoosting 返回的是二维数组（[n_estimators, n_outputs]）
                    preds = np.array([
                        est[0].predict([features])[0]
                        for est in self.best_model.estimators_
                        if hasattr(est[0], 'predict')
                    ])
                else:
                    # RandomForest 通常是列表形式
                    preds = np.array([
                        tree.predict([features])[0]
                        for tree in self.best_model.estimators_
                        if hasattr(tree, 'predict')
                    ])
            except Exception as e:
                print("⚠️ Error during interval calculation:", e)
                return prediction * 0.95, prediction * 1.05

            lower = np.percentile(preds, 100 * alpha / 2)
            upper = np.percentile(preds, 100 * (1 - alpha / 2))
            return lower, upper

        else:
            # 对于不支持 estimators_ 的模型，返回 ±5%
            margin = prediction * 0.05
            return prediction - margin, prediction + margin




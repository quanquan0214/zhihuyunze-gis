import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score
import warnings
import pandas as pd

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

    # def analyze_trend(self, time_series_data):
    #     """分析时间序列趋势"""
    #
    #     # 数据预处理
    #     df = pd.DataFrame(time_series_data)
    #     df['time_numeric'] = pd.to_datetime(df['date']).map(pd.Timestamp.timestamp)
    #
    #     X = df[['time_numeric']].values
    #     y = df['value'].values
    #
    #     results = {}
    #
    #     # 线性趋势
    #     linear_model = self.models['linear'].fit(X, y)
    #     linear_pred = linear_model.predict(X)
    #     linear_r2 = r2_score(y, linear_pred)
    #
    #     # 多项式趋势
    #     poly_model = self.models['polynomial'].fit(X, y)
    #     poly_pred = poly_model.predict(X)
    #     poly_r2 = r2_score(y, poly_pred)
    #
    #     # 选择最佳模型
    #     best_model = 'linear' if linear_r2 > poly_r2 else 'polynomial'
    #     best_r2 = max(linear_r2, poly_r2)
    #
    #     # 生成未来预测
    #     future_predictions = self._generate_predictions(
    #         self.models[best_model], X, df['time_numeric'].max()
    #     )
    #
    #     return {
    #         'trend_type': best_model,
    #         'r_squared': best_r2,
    #         'slope': linear_model.coef_[0] if best_model == 'linear' else None,
    #         'predictions': future_predictions,
    #         'trend_strength': self._classify_trend_strength(best_r2)
    #     }
    #
    # def _generate_predictions(self, model, X, last_time, periods=12):
    #     """生成未来预测"""
    #
    #     time_interval = np.mean(np.diff(X.flatten()))
    #     future_times = np.array([
    #         last_time + (i + 1) * time_interval
    #         for i in range(periods)
    #     ]).reshape(-1, 1)
    #
    #     future_values = model.predict(future_times)
    #
    #     return [
    #         {
    #             'time': time,
    #             'predicted_value': value,
    #             'confidence_interval': self._calculate_confidence_interval(model, time)
    #         }
    #         for time, value in zip(future_times.flatten(), future_values)
    #     ]

    def analyze_trend(self, time_series_data):
        """
        分析时间序列的趋势，选择最佳趋势模型（线性或多项式），
        并预测未来若干期的值及其置信区间。

        参数:
            time_series_data: 包含 'date' 和 'value' 的字典或DataFrame格式的时间序列数据

        返回:
            包含趋势类型、R²、斜率（如果是线性）、预测结果和趋势强度的字典
        """
        # 数据预处理
        df = pd.DataFrame(time_series_data)
        df['time_numeric'] = pd.to_datetime(df['date']).map(pd.Timestamp.timestamp)

        X = df[['time_numeric']].values
        y = df['value'].values

        # 线性趋势模型拟合
        linear_model = self.models['linear'].fit(X, y)
        linear_pred = linear_model.predict(X)
        linear_r2 = r2_score(y, linear_pred)

        # 多项式趋势模型拟合
        poly_model = self.models['polynomial'].fit(X, y)
        poly_pred = poly_model.predict(X)
        poly_r2 = r2_score(y, poly_pred)

        # 选择最佳模型
        if linear_r2 >= poly_r2:
            best_model_name = 'linear'
            best_model = linear_model
            best_r2 = linear_r2
            slope = linear_model.coef_[0]
        else:
            best_model_name = 'polynomial'
            best_model = poly_model
            best_r2 = poly_r2
            slope = None  # 多项式没有线性斜率

        # 生成未来预测值
        future_predictions = self._generate_predictions(
            model=best_model,
            X=X,
            last_time=df['time_numeric'].max(),
            periods=12  # 可根据需要调整
        )

        return {
            'trend_type': best_model_name,
            'r_squared': best_r2,
            'slope': slope,
            'predictions': future_predictions,
            'trend_strength': self._classify_trend_strength(best_r2)
        }

    def _generate_predictions(self, model, X, last_time, periods=12):
        """
        基于拟合后的模型生成未来若干期的预测值，并构造置信区间（±5%）。

        参数：
            model: 拟合后的回归模型（如 LinearRegression、Pipeline）
            X: 原始时间序列的时间特征数组
            last_time: 上一个时间点（float，时间戳）
            periods: 预测的未来期数（默认为12）

        返回：
            一个包含预测值和置信区间的列表
        """
        import scipy.stats as st

        # 计算时间间隔（假设等间隔）
        time_interval = np.mean(np.diff(X.flatten()))

        # 构造未来时间点
        future_times = np.array([
            last_time + (i + 1) * time_interval
            for i in range(periods)
        ]).reshape(-1, 1)

        # 预测未来值
        future_values = model.predict(future_times)

        # 构造预测结果
        predictions = []
        for t, val in zip(future_times.flatten(), future_values):
            margin = val * 0.05  # ±5% 置信区间
            predictions.append({
                'time': t,
                'predicted_value': val,
                'confidence_interval': (val - margin, val + margin)
            })

        return predictions

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

    def _calculate_confidence_interval(self, model, time_numeric, alpha=0.05):
        """为趋势预测值构造一个简单的置信区间（假设 ±5%）"""
        try:
            prediction = model.predict([[time_numeric]])[0]
            margin = prediction * 0.05  # ±5%
            return prediction - margin, prediction + margin
        except:
            return None, None


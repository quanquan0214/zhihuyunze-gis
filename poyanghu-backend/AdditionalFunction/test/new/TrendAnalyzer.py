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
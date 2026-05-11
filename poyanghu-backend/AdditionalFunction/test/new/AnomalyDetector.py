from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import scipy.stats as stats
import pandas as pd
import numpy as np


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
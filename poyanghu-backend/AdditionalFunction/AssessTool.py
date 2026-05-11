### 2.2 环境质量风险评估和预警
#### 风险评估模型

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



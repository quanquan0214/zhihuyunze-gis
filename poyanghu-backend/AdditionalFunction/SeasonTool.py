### 2.3 季节性模式识别

#### 季节性分析算法
from statsmodels.tsa.seasonal import STL
from scipy import signal
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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



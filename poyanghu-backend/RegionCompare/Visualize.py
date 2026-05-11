"""
可视化生成器 - 专门处理图表和可视化生成
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any
import io
import base64


class VisualizationGenerator:
    """可视化生成器"""

    def __init__(self):
        """初始化可视化生成器"""
        # 设置matplotlib样式
        plt.style.use('seaborn-v0_8')
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.facecolor'] = 'white'

        # 设置颜色调色板
        self.color_palette = plt.cm.Set3(np.linspace(0, 1, 12))

    def create_comprehensive_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """
        创建综合仪表板

        Args:
            analysis_results: 分析结果

        Returns:
            仪表板图表的base64编码
        """
        fig = plt.figure(figsize=(20, 12))

        # 创建网格布局
        gs = fig.add_gridspec(3, 4, height_ratios=[1, 1, 1], width_ratios=[1, 1, 1, 1])

        # 1. 时间序列对比图 (占据上方2x2)
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_time_series_comparison(ax1, analysis_results)

        # 2. 面积对比图
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_area_comparison(ax2, analysis_results)

        # 3. 最新年份数值对比
        ax3 = fig.add_subplot(gs[0, 3])
        self._plot_latest_values(ax3, analysis_results)

        # 4. 变化趋势对比
        ax4 = fig.add_subplot(gs[1, :2])
        self._plot_change_trends(ax4, analysis_results)

        # 5. 归一化指标散点图
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_normalized_scatter(ax5, analysis_results)

        # 6. 波动性分析
        ax6 = fig.add_subplot(gs[1, 3])
        self._plot_volatility_analysis(ax6, analysis_results)

        # 7. 数据统计摘要表格
        ax7 = fig.add_subplot(gs[2, :])
        self._plot_summary_table(ax7, analysis_results)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def create_detailed_time_series(self, analysis_results: Dict[str, Any]) -> str:
        """创建详细的时间序列图"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        axes = axes.flatten()

        # 1. 平均值时间序列
        self._plot_time_series_comparison(axes[0], analysis_results, metric='mean')
        axes[0].set_title('RSEI平均值时间序列')

        # 2. 中位数时间序列
        self._plot_time_series_comparison(axes[1], analysis_results, metric='median')
        axes[1].set_title('RSEI中位数时间序列')

        # 3. 标准差时间序列
        self._plot_time_series_comparison(axes[2], analysis_results, metric='std')
        axes[2].set_title('RSEI标准差时间序列')

        # 4. 归一化总值时间序列
        self._plot_normalized_time_series(axes[3], analysis_results)
        axes[3].set_title('归一化总值时间序列')

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def create_change_analysis_chart(self, analysis_results: Dict[str, Any]) -> str:
        """创建变化分析图表"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        # 1. 总变化百分比
        self._plot_total_change_bars(axes[0, 0], analysis_results)

        # 2. 年均变化率
        self._plot_annual_change_bars(axes[0, 1], analysis_results)

        # 3. 变化趋势斜率
        self._plot_trend_slopes(axes[1, 0], analysis_results)

        # 4. 波动性对比
        self._plot_volatility_bars(axes[1, 1], analysis_results)

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _plot_time_series_comparison(self, ax, results: Dict, metric: str = 'mean'):
        """绘制时间序列对比"""
        for i, (region_id, time_series) in enumerate(results['time_series_data'].items()):
            if not time_series:
                continue

            years = sorted(time_series.keys())
            values = [time_series[year][metric] for year in years]

            region_name = results['regions_info'][region_id]['name']
            color = self.color_palette[i % len(self.color_palette)]

            ax.plot(years, values, marker='o', label=region_name,
                    linewidth=2.5, color=color, markersize=6)

        ax.set_xlabel('年份')
        ax.set_ylabel(f'RSEI {metric}')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_area_comparison(self, ax, results: Dict):
        """绘制面积对比图"""
        region_names = []
        areas = []

        for region_id, region_info in results['regions_info'].items():
            region_names.append(region_info['name'])
            areas.append(region_info['area_km2'])

        colors = self.color_palette[:len(region_names)]
        bars = ax.bar(range(len(region_names)), areas, color=colors, alpha=0.7)

        ax.set_xticks(range(len(region_names)))
        ax.set_xticklabels(region_names, rotation=45, ha='right')
        ax.set_ylabel('面积 (km²)')
        ax.set_title('区域面积对比')

        # 添加数值标签
        for bar, area in zip(bars, areas):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{area:.1f}', ha='center', va='bottom')

    def _plot_latest_values(self, ax, results: Dict):
        """绘制最新年份数值对比"""
        # 获取最新年份
        all_years = set()
        for time_series in results['time_series_data'].values():
            all_years.update(time_series.keys())

        if not all_years:
            ax.text(0.5, 0.5, '无可用数据', ha='center', va='center', transform=ax.transAxes)
            return

        latest_year = max(all_years)

        region_names = []
        latest_values = []

        for region_id, region_info in results['regions_info'].items():
            time_series = results['time_series_data'].get(region_id, {})
            if latest_year in time_series:
                region_names.append(region_info['name'])
                latest_values.append(time_series[latest_year]['mean'])

        if region_names:
            colors = self.color_palette[:len(region_names)]
            bars = ax.bar(range(len(region_names)), latest_values, color=colors, alpha=0.7)

            ax.set_xticks(range(len(region_names)))
            ax.set_xticklabels(region_names, rotation=45, ha='right')
            ax.set_ylabel('RSEI平均值')
            ax.set_title(f'{latest_year}年RSEI对比')

            # 添加数值标签
            for bar, value in zip(bars, latest_values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{value:.3f}', ha='center', va='bottom')

    def _plot_change_trends(self, ax, results: Dict):
        """绘制变化趋势"""
        region_names = []
        change_percentages = []

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})
            if change_metrics and 'total_change_percent' in change_metrics:
                region_names.append(region_info['name'])
                change_percentages.append(change_metrics['total_change_percent'])

        if region_names:
            colors = ['green' if x >= 0 else 'red' for x in change_percentages]
            bars = ax.bar(range(len(region_names)), change_percentages, color=colors, alpha=0.7)

            ax.set_xticks(range(len(region_names)))
            ax.set_xticklabels(region_names, rotation=45, ha='right')
            ax.set_ylabel('总变化百分比 (%)')
            ax.set_title('各区域RSEI总变化百分比')
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            # 添加数值标签
            for bar, value in zip(bars, change_percentages):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + (0.5 if height >= 0 else -1.5),
                        f'{value:.1f}%', ha='center', va='bottom' if height >= 0 else 'top')

    def _plot_normalized_scatter(self, ax, results: Dict):
        """绘制归一化指标散点图"""
        # 获取最新年份的归一化数据
        all_years = set()
        for normalized_series in results['normalized_data'].values():
            all_years.update(normalized_series.keys())

        if not all_years:
            ax.text(0.5, 0.5, '无归一化数据', ha='center', va='center', transform=ax.transAxes)
            return

        latest_year = max(all_years)

        normalized_sums = []
        densities = []
        region_names = []

        for region_id, normalized_series in results['normalized_data'].items():
            if latest_year in normalized_series:
                stats = normalized_series[latest_year]
                normalized_sums.append(stats.get('normalized_sum', 0))
                densities.append(stats.get('density', 0))
                region_names.append(results['regions_info'][region_id]['name'])

        if normalized_sums:
            scatter = ax.scatter(normalized_sums, densities, s=100, alpha=0.7,
                                 c=range(len(normalized_sums)), cmap='viridis')

            # 添加标签
            for i, name in enumerate(region_names):
                ax.annotate(name, (normalized_sums[i], densities[i]),
                            xytext=(5, 5), textcoords='offset points', fontsize=8)

            ax.set_xlabel('归一化总值')
            ax.set_ylabel('密度')
            ax.set_title('归一化指标关系')
            ax.grid(True, alpha=0.3)

    def _plot_volatility_analysis(self, ax, results: Dict):
        """绘制波动性分析"""
        volatilities = []
        trend_slopes = []
        region_names = []

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})
            if change_metrics:
                volatilities.append(change_metrics.get('volatility', 0))
                trend_slopes.append(change_metrics.get('trend_slope', 0))
                region_names.append(region_info['name'])

        if volatilities:
            colors = ['green' if x >= 0 else 'red' for x in trend_slopes]
            scatter = ax.scatter(volatilities, trend_slopes, c=colors, s=80, alpha=0.7)

            # 添加标签
            for i, name in enumerate(region_names):
                ax.annotate(name, (volatilities[i], trend_slopes[i]),
                            xytext=(3, 3), textcoords='offset points', fontsize=8)

            ax.set_xlabel('波动性')
            ax.set_ylabel('趋势斜率')
            ax.set_title('波动性vs趋势')
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax.grid(True, alpha=0.3)

    def _plot_summary_table(self, ax, results: Dict):
        """绘制摘要表格"""
        ax.axis('tight')
        ax.axis('off')

        # 准备表格数据
        table_data = []
        headers = ['区域名称', '面积(km²)', '总变化(%)', '年均变化率', '波动性', '最新值']

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})

            # 获取最新值
            time_series = results['time_series_data'].get(region_id, {})
            latest_value = 0
            if time_series:
                latest_year = max(time_series.keys())
                latest_value = time_series[latest_year]['mean']

            row = [
                region_info['name'],
                f"{region_info['area_km2']:.1f}",
                f"{change_metrics.get('total_change_percent', 0):.1f}%",
                f"{change_metrics.get('annual_change_rate', 0):.4f}",
                f"{change_metrics.get('volatility', 0):.3f}",
                f"{latest_value:.3f}"
            ]
            table_data.append(row)

        if table_data:
            table = ax.table(cellText=table_data, colLabels=headers,
                             cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # 设置表格样式
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')

            for i in range(1, len(table_data) + 1):
                for j in range(len(headers)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#f0f0f0')

        ax.set_title('区域对比摘要表', pad=20, fontsize=12, weight='bold')

    def _plot_normalized_time_series(self, ax, results: Dict):
        """绘制归一化时间序列"""
        for i, (region_id, normalized_series) in enumerate(results['normalized_data'].items()):
            if not normalized_series:
                continue

            years = sorted(normalized_series.keys())
            values = [normalized_series[year].get('normalized_sum', 0) for year in years]

            region_name = results['regions_info'][region_id]['name']
            color = self.color_palette[i % len(self.color_palette)]

            ax.plot(years, values, marker='s', label=region_name,
                    linewidth=2, color=color, markersize=5)

        ax.set_xlabel('年份')
        ax.set_ylabel('归一化总值')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

    def _plot_total_change_bars(self, ax, results: Dict):
        """绘制总变化百分比柱状图"""
        region_names = []
        change_percentages = []

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})
            if change_metrics:
                region_names.append(region_info['name'])
                change_percentages.append(change_metrics.get('total_change_percent', 0))

        if region_names:
            colors = ['green' if x >= 0 else 'red' for x in change_percentages]
            bars = ax.bar(region_names, change_percentages, color=colors, alpha=0.7)

            ax.set_ylabel('总变化百分比 (%)')
            ax.set_title('总变化百分比对比')
            ax.tick_params(axis='x', rotation=45)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            for bar, value in zip(bars, change_percentages):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + (0.5 if height >= 0 else -1.5),
                        f'{value:.1f}%', ha='center', va='bottom' if height >= 0 else 'top')

    def _plot_annual_change_bars(self, ax, results: Dict):
        """绘制年均变化率柱状图"""
        region_names = []
        annual_rates = []

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})
            if change_metrics:
                region_names.append(region_info['name'])
                annual_rates.append(change_metrics.get('annual_change_rate', 0))

        if region_names:
            colors = ['darkgreen' if x >= 0 else 'darkred' for x in annual_rates]
            bars = ax.bar(region_names, annual_rates, color=colors, alpha=0.7)

            ax.set_ylabel('年均变化率')
            ax.set_title('年均变化率对比')
            ax.tick_params(axis='x', rotation=45)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            for bar, value in zip(bars, annual_rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + (0.001 if height >= 0 else -0.003),
                        f'{value:.3f}', ha='center', va='bottom' if height >= 0 else 'top')

    def _plot_trend_slopes(self, ax, results: Dict):
        """绘制趋势斜率图"""
        region_names = []
        slopes = []

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})
            if change_metrics:
                region_names.append(region_info['name'])
                slopes.append(change_metrics.get('trend_slope', 0))

        if region_names:
            colors = ['blue' if x >= 0 else 'orange' for x in slopes]
            bars = ax.bar(region_names, slopes, color=colors, alpha=0.7)

            ax.set_ylabel('趋势斜率')
            ax.set_title('趋势斜率对比')
            ax.tick_params(axis='x', rotation=45)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            for bar, value in zip(bars, slopes):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height + (0.001 if height >= 0 else -0.003),
                        f'{value:.4f}', ha='center', va='bottom' if height >= 0 else 'top')

    def _plot_volatility_bars(self, ax, results: Dict):
        """绘制波动性柱状图"""
        region_names = []
        volatilities = []

        for region_id, region_info in results['regions_info'].items():
            change_metrics = results['change_metrics'].get(region_id, {})
            if change_metrics:
                region_names.append(region_info['name'])
                volatilities.append(change_metrics.get('volatility', 0))

        if region_names:
            bars = ax.bar(region_names, volatilities, color='purple', alpha=0.7)

            ax.set_ylabel('波动性（标准差）')
            ax.set_title('波动性对比')
            ax.tick_params(axis='x', rotation=45)

            for bar, value in zip(bars, volatilities):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{value:.3f}', ha='center', va='bottom')

    def _fig_to_base64(self, fig):
        """将matplotlib图形转换为base64编码"""
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=150, facecolor='white')
        img.seek(0)
        plt.close(fig)
        return base64.b64encode(img.getvalue()).decode('utf-8')
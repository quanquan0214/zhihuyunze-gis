import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import json
import io
import base64
from matplotlib.patches import Rectangle


class VisualizationGenerator:
    """可视化图表生成类"""

    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 土地类型颜色映射
        self.land_type_colors = {
            '耕地': '#FFE135',
            '草本': '#90EE90',
            '阔叶林': '#228B22',
            '针叶林': '#006400',
            '混交林': '#32CD32',
            '灌木': '#9ACD32',
            '草地': '#ADFF2F',
            '稀疏植被': '#F0E68C',
            '湿地': '#40E0D0',
            '建设用地': '#FF6347',
            '裸地': '#D2B48C',
            '水体': '#4169E1'
        }

    def generate_relative_change_chart(self, region_data: Dict[int, Dict[str, float]],
                                       region_name: str = "区域") -> str:
        """
        生成相对变化图

        Args:
            region_data: 相对变化数据 {year: {land_type: change_percentage}}
            region_name: 区域名称

        Returns:
            str: Base64编码的图像
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # 准备数据
        years = sorted(region_data.keys())
        land_types = set()
        for year_data in region_data.values():
            land_types.update(year_data.keys())
        land_types = sorted(land_types)

        # 绘制每种土地类型的变化线
        for land_type in land_types:
            changes = []
            for year in years:
                changes.append(region_data[year].get(land_type, 0))

            color = self.land_type_colors.get(land_type, '#666666')
            ax.plot(years, changes, marker='o', linewidth=2, label=land_type,
                    color=color, markersize=4)

        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax.set_xlabel('年份', fontsize=12)
        ax.set_ylabel('相对变化 (%)', fontsize=12)
        ax.set_title(f'{region_name} - 土地覆盖相对变化趋势 (以2000年为基准)', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        # 设置x轴标签
        ax.set_xticks(years[::3])  # 每3年显示一个标签
        ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # 转换为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return image_base64

    def generate_heatmap(self, annual_changes: Dict[str, List[Dict]],
                         region_name: str = "区域") -> str:
        """
        生成变化率热力图

        Args:
            annual_changes: 年际变化数据 {land_type: [{'year': year, 'change_rate': rate}]}
            region_name: 区域名称

        Returns:
            str: Base64编码的图像
        """
        # 准备数据矩阵
        land_types = list(annual_changes.keys())
        if not land_types:
            return ""

        years = sorted(set(item['year'] for changes in annual_changes.values() for item in changes))

        # 创建数据矩阵
        data_matrix = np.zeros((len(land_types), len(years)))
        print(type(data_matrix))
        # 应该输出numpy.ndarray类型

        for i, land_type in enumerate(land_types):
            year_to_change = {item['year']: item['change_rate'] for item in annual_changes[land_type]}
            for j, year in enumerate(years):
                data_matrix[i, j] = year_to_change.get(year, 0)

        # 创建DataFrame
        df = pd.DataFrame(data_matrix, index=land_types, columns=years)

        # 绘制热力图
        fig, ax = plt.subplots(figsize=(14, 8))

        # 设置色彩映射，突出变化
        max_abs_change = np.max(np.abs(data_matrix))
        vmin, vmax = -max_abs_change, max_abs_change

        sns.heatmap(df, annot=True, fmt='.2f', cmap='RdYlBu_r', center=0,
                    vmin=vmin, vmax=vmax, ax=ax, cbar_kws={'label': '年际变化率 (%)'})

        ax.set_title(f'{region_name} - 土地覆盖年际变化率热力图', fontsize=14, fontweight='bold')
        ax.set_xlabel('年份', fontsize=12)
        ax.set_ylabel('土地类型', fontsize=12)

        plt.tight_layout()

        # 转换为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return image_base64

    def generate_anomaly_chart(self, anomalies: Dict[str, List[Dict]],
                               region_name: str = "区域") -> str:
        """
        生成异常年份标注图

        Args:
            anomalies: 异常数据 {land_type: [{'year': year, 'change_rate': rate, 'type': 'increase/decrease'}]}
            region_name: 区域名称

        Returns:
            str: Base64编码的图像
        """
        if not anomalies:
            return ""

        fig, ax = plt.subplots(figsize=(12, 8))

        # 准备数据
        all_anomalies = []
        for land_type, type_anomalies in anomalies.items():
            for anomaly in type_anomalies:
                all_anomalies.append({
                    'land_type': land_type,
                    'year': anomaly['year'],
                    'change_rate': anomaly['change_rate'],
                    'type': anomaly['type']
                })

        if not all_anomalies:
            return ""

        df = pd.DataFrame(all_anomalies)

        # 按土地类型分组绘制
        land_types = df['land_type'].unique()
        colors = {'increase': '#FF6B6B', 'decrease': '#4ECDC4'}

        for i, land_type in enumerate(land_types):
            type_data = df[df['land_type'] == land_type]

            for _, row in type_data.iterrows():
                color = colors[row['type']]
                ax.scatter(row['year'], i, s=abs(row['change_rate']) * 20,
                           c=color, alpha=0.7, edgecolors='black', linewidth=1)

                # 添加数值标签
                ax.annotate(f"{row['change_rate']:.1f}%",
                            (row['year'], i),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, alpha=0.8)

        ax.set_yticks(range(len(land_types)))
        ax.set_yticklabels(land_types)
        ax.set_xlabel('年份', fontsize=12)
        ax.set_ylabel('土地类型', fontsize=12)
        ax.set_title(f'{region_name} - 异常变化年份标注图', fontsize=14, fontweight='bold')

        # 添加图例
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
                   markersize=8, label='增加异常'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#4ECDC4',
                   markersize=8, label='减少异常')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        # 转换为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return image_base64

    def generate_multi_region_comparison(self, comparison_data: Dict[str, Any]) -> str:
        """
        生成多区域对比图

        Args:
            comparison_data: 多区域对比数据

        Returns:
            str: Base64编码的图像
        """
        region_names = list(comparison_data.keys())
        if len(region_names) < 2:
            return ""

        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()

        # 1. 总面积对比
        ax1 = axes[0]
        for region_name in region_names:
            total_areas = comparison_data[region_name]['total_area']
            years = sorted(total_areas.keys())
            areas = [total_areas[year] for year in years]
            ax1.plot(years, areas, marker='o', label=region_name, linewidth=2)

        ax1.set_title('区域总面积对比', fontsize=12, fontweight='bold')
        ax1.set_xlabel('年份')
        ax1.set_ylabel('面积 (km²)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. 主要土地类型占比对比（以2022年为例）
        ax2 = axes[1]
        latest_year = max(comparison_data[region_names[0]]['raw_data'].keys())

        land_types = set()
        for region_name in region_names:
            if latest_year in comparison_data[region_name]['raw_data']:
                land_types.update(comparison_data[region_name]['raw_data'][latest_year].keys())

        x = np.arange(len(region_names))
        width = 0.8 / len(land_types)

        for i, land_type in enumerate(sorted(land_types)):
            areas = []
            for region_name in region_names:
                region_data = comparison_data[region_name]['raw_data'].get(latest_year, {})
                areas.append(region_data.get(land_type, 0))

            color = self.land_type_colors.get(land_type, '#666666')
            ax2.bar(x + i * width, areas, width, label=land_type, color=color, alpha=0.8)

        ax2.set_title(f'{latest_year}年土地类型面积对比', fontsize=12, fontweight='bold')
        ax2.set_xlabel('区域')
        ax2.set_ylabel('面积 (km²)')
        ax2.set_xticks(x + width * (len(land_types) - 1) / 2)
        ax2.set_xticklabels(region_names)
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        # 3. 异常年份数量对比
        ax3 = axes[2]
        anomaly_counts = {}
        for region_name in region_names:
            count = sum(len(anomalies) for anomalies in comparison_data[region_name]['anomalies'].values())
            anomaly_counts[region_name] = count

        ax3.bar(anomaly_counts.keys(), anomaly_counts.values(), color='coral', alpha=0.7)
        ax3.set_title('异常变化年份数量对比', fontsize=12, fontweight='bold')
        ax3.set_xlabel('区域')
        ax3.set_ylabel('异常年份数量')

        # 4. 平均变化幅度对比
        ax4 = axes[3]
        avg_changes = {}
        for region_name in region_names:
            relative_changes = comparison_data[region_name]['relative_changes']
            all_changes = []
            for year_data in relative_changes.values():
                all_changes.extend([abs(change) for change in year_data.values()])
            avg_changes[region_name] = np.mean(all_changes) if all_changes else 0

        ax4.bar(avg_changes.keys(), avg_changes.values(), color='lightblue', alpha=0.7)
        ax4.set_title('平均变化幅度对比', fontsize=12, fontweight='bold')
        ax4.set_xlabel('区域')
        ax4.set_ylabel('变化幅度 (%)')

        # 调整子图间距和布局
        plt.tight_layout()

        # 为第二个子图的图例预留更多空间
        plt.subplots_adjust(right=0.85)

        # 添加总标题
        fig.suptitle('多区域土地利用对比分析', fontsize=16, fontweight='bold', y=0.98)

        # 将图像保存到内存缓冲区
        buffer = io.BytesIO()
        try:
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
            buffer.seek(0)

            # 将图像编码为base64字符串
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        finally:
            # 清理资源
            buffer.close()
            plt.close(fig)

        return image_base64


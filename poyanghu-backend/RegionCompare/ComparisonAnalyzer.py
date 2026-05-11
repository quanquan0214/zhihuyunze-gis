"""
对比分析器 - 实现多区域并行对比分析功能
"""
import csv
import os

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from RegionCompare.RegionProcessor import RegionProcessor
from RegionCompare.RasterAnalyzer import RasterAnalyzer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
from collections import defaultdict
import io
import base64
from typing import Dict, List, Any
import tempfile
from shapely.geometry import Polygon
import geopandas as gpd


class ComparisonAnalyzer:
    """多区域对比分析器"""

    def __init__(self, data_directory: str = "F:/pylake/totaldata/RSEI_full/"):
        """
        初始化对比分析器

        Args:
            data_directory: RSEI数据目录路径
        """
        self.region_processor = RegionProcessor()
        self.raster_analyzer = RasterAnalyzer(data_directory)

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def add_analysis_region(self, region_data: Dict, region_type: str = 'points') -> str:
        """
        添加分析区域

        Args:
            region_data: 区域数据
            region_type: 区域类型 ('points' 或 'vector')

        Returns:
            region_id: 区域ID
        """
        if region_type == 'points':
            return self.region_processor.add_region_from_points(
                points=region_data['points'],
                region_name=region_data.get('name'),
                crs=region_data.get('crs', 'EPSG:4326')
            )
        elif region_type == 'vector':
            return self.region_processor.add_region_from_vector(
                vector_data=region_data['data'],
                region_name=region_data.get('name')
            )
        else:
            raise ValueError(f"不支持的区域类型: {region_type}")

    def parallel_comparison_analysis(self, region_ids: List[str],
                                     years: List[int]) -> Dict[str, Any]:
        """
        并行多区域对比分析

        Args:
            region_ids: 区域ID列表
            years: 分析年份列表

        Returns:
            对比分析结果
        """
        results = {
            'regions_info': {},
            'time_series_data': {},
            'normalized_data': {},
            'change_metrics': {},
            'comparison_summary': {},
            'available_years': sorted(self.raster_analyzer.available_years)
        }

        # 收集所有区域的信息和数据
        all_areas = []
        for region_id in region_ids:
            region_info = self.region_processor.get_region(region_id)
            if not region_info:
                continue

            # 存储区域基本信息
            results['regions_info'][region_id] = {
                'name': region_info['name'],
                'area_km2': region_info['area_km2']
            }
            all_areas.append(region_info['area_km2'])

            # 提取时间序列数据
            geometry = region_info['geometry']
            time_series = self.raster_analyzer.extract_multi_year_statistics(
                geometry, years
            )
            results['time_series_data'][region_id] = time_series

            # 计算变化趋势指标
            change_metrics = self.raster_analyzer.calculate_change_metrics(time_series)
            results['change_metrics'][region_id] = change_metrics

        # 计算归一化数据
        max_area = max(all_areas) if all_areas else 1.0

        for region_id in region_ids:
            if region_id not in results['time_series_data']:
                continue

            normalized_series = {}
            for year, stats in results['time_series_data'][region_id].items():
                normalized_stats = self.raster_analyzer.calculate_normalized_metrics(
                    stats, max_area
                )
                normalized_series[year] = normalized_stats

            results['normalized_data'][region_id] = normalized_series

        # 生成对比摘要
        results['comparison_summary'] = self._generate_comparison_summary(
            results['regions_info'],
            results['change_metrics'],
            results['normalized_data']
        )

        return results



    def generate_comparison_charts(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """
        生成对比图表

        Args:
            analysis_results: 分析结果

        Returns:
            图表的base64编码字典
        """
        charts = {}

        # 1. 时间序列对比图
        charts['time_series'] = self._create_time_series_chart(analysis_results)

        # 2. 面积统计对比图
        charts['area_statistics'] = self._create_area_statistics_chart(analysis_results)

        # 3. 归一化指标对比图
        charts['normalized_comparison'] = self._create_normalized_chart(analysis_results)

        # 4. 变化趋势对比图
        charts['change_trends'] = self._create_change_trends_chart(analysis_results)

        return charts

    def export_comparison_data(self, analysis_results: Dict[str, Any]) -> pd.DataFrame:
        """
        导出对比数据为DataFrame

        Args:
            analysis_results: 分析结果

        Returns:
            包含所有对比数据的DataFrame
        """
        data_rows = []

        for region_id, region_info in analysis_results['regions_info'].items():
            if region_id not in analysis_results['time_series_data']:
                continue

            time_series = analysis_results['time_series_data'][region_id]
            normalized_series = analysis_results['normalized_data'].get(region_id, {})

            for year, stats in time_series.items():
                normalized_stats = normalized_series.get(year, {})

                row = {
                    'region_id': region_id,
                    'region_name': region_info['name'],
                    'year': year,
                    'area_km2': region_info['area_km2'],
                    'mean_value': stats['mean'],
                    'median_value': stats['median'],
                    'std_value': stats['std'],
                    'min_value': stats['min'],
                    'max_value': stats['max'],
                    'sum_value': stats['sum'],
                    'pixel_count': stats['count'],
                    'normalized_sum': normalized_stats.get('normalized_sum', 0),
                    'density': normalized_stats.get('density', 0),
                    'area_ratio': normalized_stats.get('area_ratio', 0)
                }
                data_rows.append(row)

        return pd.DataFrame(data_rows)

    def _generate_comparison_summary(self, regions_info: Dict,
                                     change_metrics: Dict,
                                     normalized_data: Dict) -> Dict:
        """生成对比摘要"""
        summary = {
            'total_regions': len(regions_info),
            'region_rankings': {},
            'overall_trends': {},
            'area_comparison': {}
        }

        # 区域面积对比
        areas = {rid: info['area_km2'] for rid, info in regions_info.items()}
        sorted_areas = sorted(areas.items(), key=lambda x: x[1], reverse=True)

        summary['area_comparison'] = {
            'largest_region': sorted_areas[0] if sorted_areas else None,
            'smallest_region': sorted_areas[-1] if sorted_areas else None,
            'area_ratios': {rid: areas[rid] / sorted_areas[0][1]
                            for rid, _ in sorted_areas} if sorted_areas else {}
        }

        # 变化趋势对比
        if change_metrics:
            trend_comparison = {}
            for region_id, metrics in change_metrics.items():
                if 'total_change_percent' in metrics:
                    trend_comparison[region_id] = metrics['total_change_percent']

            if trend_comparison:
                sorted_trends = sorted(trend_comparison.items(),
                                       key=lambda x: x[1], reverse=True)
                summary['overall_trends'] = {
                    'highest_increase': sorted_trends[0] if sorted_trends else None,
                    'highest_decrease': sorted_trends[-1] if sorted_trends else None,
                    'average_change': np.mean(list(trend_comparison.values()))
                }

        return summary

    def _create_time_series_chart(self, results: Dict) -> str:
        """创建时间序列对比图"""
        fig, ax = plt.subplots(figsize=(12, 6))

        for region_id, time_series in results['time_series_data'].items():
            if not time_series:
                continue

            years = sorted(time_series.keys())
            values = [time_series[year]['mean'] for year in years]

            region_name = results['regions_info'][region_id]['name']
            ax.plot(years, values, marker='o', label=region_name, linewidth=2)

        ax.set_xlabel('年份')
        ax.set_ylabel('RSEI平均值')
        ax.set_title('多区域RSEI时间序列对比')
        ax.legend()
        ax.grid(True, alpha=0.3)

        return self._fig_to_base64(fig)

    def _create_area_statistics_chart(self, results: Dict) -> str:
        """创建面积统计对比图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 面积对比柱状图
        region_names = []
        areas = []

        for region_id, region_info in results['regions_info'].items():
            region_names.append(region_info['name'])
            areas.append(region_info['area_km2'])

        ax1.bar(region_names, areas, color='skyblue', alpha=0.7)
        ax1.set_ylabel('面积 (km²)')
        ax1.set_title('区域面积对比')
        ax1.tick_params(axis='x', rotation=45)

        # 修改最新年份逻辑：从实际分析的年份中取最大值
        if results['time_series_data']:
            # 获取所有区域共有的年份（避免某些区域缺少某些年份）
            all_years = set()
            for region_data in results['time_series_data'].values():
                all_years.update(region_data.keys())
            latest_year = max(all_years) if all_years else None
        else:
            latest_year = None

        if latest_year:
            # 绘制最新年份对比图
            latest_means = []
            for region_id in results['regions_info'].keys():
                time_series = results['time_series_data'].get(region_id, {})
                if latest_year in time_series:
                    latest_means.append(time_series[latest_year]['mean'])
                else:
                    # 使用最后可用年份的数据
                    available_years = sorted(time_series.keys())
                    if available_years:
                        latest_means.append(time_series[available_years[-1]]['mean'])
                    else:
                        latest_means.append(0)

            ax2.bar(region_names, latest_means, color='lightcoral', alpha=0.7)
            ax2.set_ylabel('RSEI平均值')
            ax2.set_title(f'{latest_year}年RSEI对比')  # 动态显示实际年份
        else:
            ax2.set_title('无有效年份数据')

        plt.tight_layout()
        plt.close('all')
        return self._fig_to_base64(fig)


    def _create_normalized_chart(self, results: Dict) -> str:
        """创建归一化指标对比图"""
        fig, ax = plt.subplots(figsize=(12, 6))

        # 获取所有归一化数据
        all_normalized_data = []
        for region_id, normalized_series in results['normalized_data'].items():
            for year, stats in normalized_series.items():
                if 'normalized_sum' in stats and 'std' in stats:
                    all_normalized_data.append((stats['normalized_sum'], stats['std']))

        if not all_normalized_data:
            plt.close(fig)
            return ""

        # 提取x,y值
        mean_values, std_values = zip(*all_normalized_data)

        # 绘制散点图
        ax.scatter(mean_values, std_values, marker='o', alpha=0.7)

        # 计算并存储拟合参数
        k, b = 0, 0  # 默认值
        if len(mean_values) > 1:
            try:
                k, b = np.polyfit(mean_values, std_values, 1)
                x = np.linspace(min(mean_values), max(mean_values), 100)
                y = k * x + b
                ax.plot(x, y, color='red', alpha=0.7)

                # 在图表右上角标注k和b
                text_str = f'y = {k:.4f}x + {b:.4f}'
                ax.text(0.95, 0.95, text_str, transform=ax.transAxes,
                        fontsize=10, verticalalignment='top', horizontalalignment='right',
                        bbox=dict(facecolor='white', alpha=0.5))

                # 将k和b存入results以便后续使用
                results['normalized_fit_params'] = {'k': k, 'b': b}
            except Exception as e:
                print(f"拟合直线时出错: {e}")

        ax.set_xlabel('归一化总值')
        ax.set_ylabel('归一化标准差')
        ax.set_title('归一化指标对比')
        ax.grid(True, alpha=0.3)
        plt.close('all')

        return self._fig_to_base64(fig)

    def _create_change_trends_chart(self, results: Dict) -> str:
        """创建变化趋势对比图

        生成展示各区域RSEI变化趋势的对比图表，包括：
        1. 各区域RSEI变化百分比柱状图
        2. 各区域RSEI年均变化率对比

        Args:
            results: 分析结果字典

        Returns:
            图表的base64编码字符串
        """
        if not results.get('change_metrics'):
            return ""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 1. 各区域总变化百分比柱状图
        region_names = []
        total_changes = []

        for region_id, metrics in results['change_metrics'].items():
            if 'total_change_percent' not in metrics:
                continue

            region_name = results['regions_info'][region_id]['name']
            region_names.append(region_name)
            total_changes.append(metrics['total_change_percent'])

        # 按变化百分比排序
        sorted_data = sorted(zip(region_names, total_changes),
                             key=lambda x: x[1], reverse=True)
        region_names = [x[0] for x in sorted_data]
        total_changes = [x[1] for x in sorted_data]

        colors = ['green' if x >= 0 else 'red' for x in total_changes]
        ax1.bar(region_names, total_changes, color=colors, alpha=0.7)
        ax1.axhline(0, color='black', linewidth=0.8)
        ax1.set_ylabel('变化百分比 (%)')
        ax1.set_title('各区域RSEI总变化百分比')
        ax1.tick_params(axis='x', rotation=45)

        # 2. 各区域年均变化率对比
        region_names = []
        annual_rates = []

        for region_id, metrics in results['change_metrics'].items():
            if 'annual_change_rate' not in metrics:
                continue

            region_name = results['regions_info'][region_id]['name']
            region_names.append(region_name)
            annual_rates.append(metrics['annual_change_rate'])

        # 按年均变化率排序
        sorted_data = sorted(zip(region_names, annual_rates),
                             key=lambda x: x[1], reverse=True)
        region_names = [x[0] for x in sorted_data]
        annual_rates = [x[1] for x in sorted_data]

        colors = ['green' if x >= 0 else 'red' for x in annual_rates]
        ax2.bar(region_names, annual_rates, color=colors, alpha=0.7)
        ax2.axhline(0, color='black', linewidth=0.8)
        ax2.set_ylabel('年均变化率')
        ax2.set_title('各区域RSEI年均变化率')
        ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.close('all')
        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig):
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        plt.close(fig)
        return base64.b64encode(img.getvalue()).decode('utf-8')

    def get_points_mapping(self, point_groups: List[Dict]) -> Dict[str, Dict[str, str]]:
        """
        将点位组转换为临时的geojson文件映射

        Args:
            point_groups: 点位组列表，每个元素包含:
                - id: 区域唯一标识
                - name: 区域名称
                - points: 点位列表，每个点包含 [lon, lat]

        Returns:
            Dict: 映射字典，格式类似于 get_city_mapping()
        """
        mapping = {}

        for group in point_groups:
            region_id = group.get('id')
            region_name = group.get('name', f'区域_{region_id}')
            points = group.get('points', [])

            # 验证点位数量（至少3个点才能构成封闭图形）
            if len(points) < 3:
                continue

            # 确保首尾点相同以形成封闭图形
            if points[0] != points[-1]:
                points.append(points[0])

            # 创建Shapely多边形
            try:
                polygon = Polygon(points)
                if not polygon.is_valid:
                    continue
            except Exception as e:
                print(f"创建多边形失败 {region_id}: {e}")
                continue

            # 创建GeoDataFrame
            gdf = gpd.GeoDataFrame([{'name': region_name}], geometry=[polygon])
            gdf.crs = "EPSG:4326"  # WGS84坐标系

            # 创建临时geojson文件 - 使用更安全的方法
            import time
            import uuid
            temp_filename = f"temp_region_{uuid.uuid4().hex}_{int(time.time())}.geojson"
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, temp_filename)

            try:
                gdf.to_file(temp_path, driver='GeoJSON')
                mapping[region_id] = {
                    'name': region_name,
                    'path': temp_path
                }
            except Exception as e:
                print(f"创建临时文件失败 {region_id}: {e}")
                continue

        return mapping

    def validate_point_groups(self,point_groups: List[Dict]) -> bool:
        """验证点位组数据"""
        if not isinstance(point_groups, list) or len(point_groups) < 2 or len(point_groups) > 6:
            return False

        for group in point_groups:
            if not isinstance(group, dict):
                return False
            if 'id' not in group or 'points' not in group:
                return False
            if not isinstance(group['points'], list) or len(group['points']) < 3:
                return False

            # 验证每个点的格式
            for point in group['points']:
                if not isinstance(point, list) or len(point) != 2:
                    return False
                try:
                    float(point[0])  # 经度
                    float(point[1])  # 纬度
                except (ValueError, TypeError):
                    return False

        return True

    def csv_to_json_chart_data(self,csv_file_path):
        # 初始化数据结构
        data = {

            "Time_Series": {},  # 时间序列数据
            "Area_Statistics": {  # 区域统计数据
                "part1": {},
                "part2": {}
            },
            "Change_Trend": {},  # 变化趋势数据，内容是总变化值和年平均变化率
            "Normalize": {}  # 归一化数据，格式为[[normalized_sum, std_value], [normalized_sum, std_value],...]

        }

        # 读取CSV文件（使用utf-8-sig自动去除BOM头）
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            rows = list(csv_reader)

        # 按区域分组（直接使用'region_id'，因为BOM已被去除）
        regions = defaultdict(list)
        for row in rows:
            regions[row['region_id']].append(row)

        # 处理每个区域的数据
        for region_id, region_data in regions.items():
            # 按年份排序
            region_data.sort(key=lambda x: int(x['year']))

            # 提取基本信息
            region_name = region_data[0]['region_name']
            area_km2 = region_data[0]['area_km2']

            # Time_Series数据
            data["Time_Series"][region_id] = {
                "region_name": region_name,
                "value": [float(row['mean_value']) for row in region_data]
            }

            # Area_Statistics数据
            data["Area_Statistics"]["part1"][region_id] = {
                "region_name": region_name,
                "area_km2": float(area_km2)
            }
            data["Area_Statistics"]["part2"][region_id] = float(region_data[-1]['mean_value'])

            # Change_Trend数据
            first_value = float(region_data[0]['mean_value'])
            last_value = float(region_data[-1]['mean_value'])
            total_change = last_value - first_value
            annual_avg_change = total_change / (len(region_data) - 1) if len(region_data) > 1 else 0

            data["Change_Trend"][region_id] = {
                "Total of change": total_change,
                "Annual average rate of change": annual_avg_change
            }

            # Normalize数据
            data["Normalize"][region_id] = {
                "region_name": region_name,
                "value": [[float(row['normalized_sum']), float(row['std_value'])] for row in region_data]
            }
        return data


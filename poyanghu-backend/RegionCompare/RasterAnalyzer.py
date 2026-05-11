"""
栅格数据分析器 - 处理RSEI等栅格数据的统计分析
"""
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from typing import Dict, List, Optional, Tuple, Union
import os
from pathlib import Path


class RasterAnalyzer:
    """栅格数据分析器"""

    def __init__(self, data_directory: str = "F:/pylake/totaldata/RSEI_full/"):
        """
        初始化栅格分析器

        Args:
            data_directory: RSEI数据目录路径
        """
        self.data_directory = Path(data_directory)
        self.available_years = self._scan_available_data()

    def _scan_available_data(self) -> List[int]:
        """扫描可用的RSEI数据年份"""
        years = []
        if self.data_directory.exists():
            for file in self.data_directory.glob("RSEI_*.tif"):
                try:
                    year_str = file.stem.split('_')[-1]
                    year = int(year_str)
                    years.append(year)
                except (ValueError, IndexError):
                    continue
        return sorted(years)

    def get_raster_path(self, year: int) -> Optional[str]:
        """获取指定年份的栅格文件路径"""
        if year not in self.available_years:
            return None

        raster_path = self.data_directory / f"RSEI_{year}.tif"
        return str(raster_path) if raster_path.exists() else None

    def extract_region_statistics(self, geometry: gpd.GeoDataFrame,
                                  raster_path: str) -> Dict:
        """
        提取区域内的栅格统计信息

        Args:
            geometry: 区域几何
            raster_path: 栅格文件路径

        Returns:
            统计信息字典
        """
        try:
            with rasterio.open(raster_path) as src:
                # 确保坐标系统匹配
                if geometry.crs != src.crs:
                    geometry = geometry.to_crs(src.crs)

                # 裁剪栅格数据
                out_image, out_transform = mask(src, geometry.geometry, crop=True)
                out_image = out_image[0]  # 取第一个波段

                # 过滤无效值
                valid_mask = ~np.isnan(out_image) & (out_image != src.nodata)
                valid_data = out_image[valid_mask]

                if len(valid_data) == 0:
                    return self._empty_statistics()

                # 计算统计信息
                stats = {
                    'mean': float(np.mean(valid_data)),
                    'median': float(np.median(valid_data)),
                    'std': float(np.std(valid_data)),
                    'min': float(np.min(valid_data)),
                    'max': float(np.max(valid_data)),
                    'count': int(len(valid_data)),
                    'sum': float(np.sum(valid_data)),
                    'percentile_25': float(np.percentile(valid_data, 25)),
                    'percentile_75': float(np.percentile(valid_data, 75))
                }

                # 计算像元面积（平方公里）
                pixel_area_km2 = abs(src.transform[0] * src.transform[4]) / 1e6
                stats['area_km2'] = stats['count'] * pixel_area_km2
                stats['pixel_area_km2'] = pixel_area_km2

                return stats

        except Exception as e:
            print(f"提取区域统计信息时发生错误: {e}")
            return self._empty_statistics()

    def get_time_series_data(self, stat_type: str = 'mean') -> Dict[int, float]:
        """
        获取时间序列数据：按年份提取指定统计类型（如 mean）

        Args:
            stat_type: 统计类型，如 'mean', 'median', 'std', 'sum' 等

        Returns:
            dict[int, float]：{年份: 值}
        """
        results = {}
        for year in self.available_years:
            raster_path = self.get_raster_path(year)
            if raster_path is None:
                continue

            # 构造一个全国范围的伪区域（跳过 geometry 裁剪）
            try:
                with rasterio.open(raster_path) as src:
                    data = src.read(1)
                    nodata = src.nodata
                    valid_mask = ~np.isnan(data) & (data != nodata)
                    valid_data = data[valid_mask]

                    if len(valid_data) == 0:
                        results[year] = 0.0
                    else:
                        if stat_type == 'mean':
                            results[year] = float(np.mean(valid_data))
                        elif stat_type == 'median':
                            results[year] = float(np.median(valid_data))
                        elif stat_type == 'std':
                            results[year] = float(np.std(valid_data))
                        elif stat_type == 'sum':
                            results[year] = float(np.sum(valid_data))
                        elif stat_type == 'min':
                            results[year] = float(np.min(valid_data))
                        elif stat_type == 'max':
                            results[year] = float(np.max(valid_data))
                        else:
                            results[year] = 0.0  # 未知类型返回0
            except Exception as e:
                print(f"处理年份 {year} 的栅格数据时出错: {e}")
                results[year] = 0.0

        return results

    def extract_multi_year_statistics(self, geometry: gpd.GeoDataFrame,
                                      years: List[int]) -> Dict[int, Dict]:
        """
        提取多年份的区域统计信息

        Args:
            geometry: 区域几何
            years: 年份列表

        Returns:
            按年份组织的统计信息
        """
        results = {}

        for year in years:
            if year not in self.available_years:
                print(f"警告: {year}年的数据不可用")
                continue

            raster_path = self.get_raster_path(year)
            if raster_path:
                stats = self.extract_region_statistics(geometry, raster_path)
                results[year] = stats

        return results

    def calculate_normalized_metrics(self, statistics: Dict,
                                     reference_area_km2: float) -> Dict:
        """
        计算归一化指标

        Args:
            statistics: 原始统计信息
            reference_area_km2: 参考面积（平方公里）

        Returns:
            归一化后的指标
        """
        if statistics['count'] == 0 or reference_area_km2 <= 0:
            return statistics.copy()

        normalized = statistics.copy()

        # 按单位面积归一化
        area_ratio = statistics['area_km2'] / reference_area_km2

        normalized.update({
            'normalized_sum': statistics['sum'] / reference_area_km2,
            'normalized_mean': statistics['mean'],  # 平均值不需要面积归一化
            'area_ratio': area_ratio,
            'density': statistics['sum'] / statistics['area_km2'] if statistics['area_km2'] > 0 else 0
        })

        return normalized

    def calculate_change_metrics(self, time_series: Dict[int, Dict]) -> Dict:
        """
        计算变化趋势指标

        Args:
            time_series: 时间序列统计数据

        Returns:
            变化趋势指标
        """
        if len(time_series) < 2:
            return {}

        years = sorted(time_series.keys())
        values = [time_series[year]['mean'] for year in years]

        # 计算总体变化
        total_change = values[-1] - values[0]
        total_change_percent = (total_change / values[0] * 100) if values[0] != 0 else 0

        # 计算年均变化率
        year_span = years[-1] - years[0]
        annual_change_rate = total_change / year_span if year_span > 0 else 0

        # 计算变化趋势（简单线性回归斜率）
        n = len(values)
        x = np.array(range(n))
        y = np.array(values)

        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x ** 2) - np.sum(x) ** 2)

        # 计算波动性（标准差）
        volatility = np.std(values)

        return {
            'total_change': total_change,
            'total_change_percent': total_change_percent,
            'annual_change_rate': annual_change_rate,
            'trend_slope': slope,
            'volatility': volatility,
            'start_value': values[0],
            'end_value': values[-1],
            'min_value': min(values),
            'max_value': max(values),
            'years_analyzed': years
        }

    def get_value_distribution(self, geometry: gpd.GeoDataFrame,
                               raster_path: str, bins: int = 10) -> Dict:
        """
        获取区域内数值分布

        Args:
            geometry: 区域几何
            raster_path: 栅格文件路径
            bins: 直方图分箱数量

        Returns:
            数值分布信息
        """
        try:
            with rasterio.open(raster_path) as src:
                if geometry.crs != src.crs:
                    geometry = geometry.to_crs(src.crs)

                out_image, _ = mask(src, geometry.geometry, crop=True)
                out_image = out_image[0]

                valid_mask = ~np.isnan(out_image) & (out_image != src.nodata)
                valid_data = out_image[valid_mask]

                if len(valid_data) == 0:
                    return {'counts': [], 'bin_edges': [], 'bin_centers': []}

                counts, bin_edges = np.histogram(valid_data, bins=bins)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                return {
                    'counts': counts.tolist(),
                    'bin_edges': bin_edges.tolist(),
                    'bin_centers': bin_centers.tolist()
                }

        except Exception as e:
            print(f"获取数值分布时发生错误: {e}")
            return {'counts': [], 'bin_edges': [], 'bin_centers': []}

    def _empty_statistics(self) -> Dict:
        """返回空的统计信息"""
        return {
            'mean': 0.0,
            'median': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0,
            'sum': 0.0,
            'area_km2': 0.0,
            'pixel_area_km2': 0.0,
            'percentile_25': 0.0,
            'percentile_75': 0.0
        }


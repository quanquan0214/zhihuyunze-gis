import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import json
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import rasterio
from ClimateData import ClimateDataService


class GeodetectorService:
    """
    地理探测器服务类
    功能：返回地理探测器Q值结果图（GeoJSON）和定量数据
    用途：前端绘制图层与热度区域图
    """

    def __init__(self, data_path: str = "data/geodetector/",
                 climate_service: Optional[ClimateDataService] = None):
        """
        初始化地理探测器服务

        Args:
            data_path: 地理探测器数据存储路径
            climate_service: 气候数据服务实例，如果为None则创建默认实例
        """
        self.data_path = Path(data_path)
        self.logger = logging.getLogger(__name__)

        # 确保数据目录存在
        self.data_path.mkdir(parents=True, exist_ok=True)

        # 初始化气候数据服务
        if climate_service is None:
            self.climate_service = ClimateDataService()
        else:
            self.climate_service = climate_service

        # 缓存数据
        self._cache = {}

        # 预定义因子名称和描述（与ClimateDataService中的数据类型对应）
        self.factor_info = {
            'temperature': {'name': '温度', 'unit': '°C'},
            'rainfall': {'name': '降水', 'unit': 'mm'},
            'rsei': {'name': 'RSEI指数', 'unit': ''},
            'lucc': {'name': '土地覆盖', 'unit': ''},
        }

    def calculate_q_statistic(self, y_data: np.ndarray, stratification: np.ndarray) -> float:
        """
        计算地理探测器Q统计量

        Args:
            y_data: 因变量数据 (RSEI值)
            stratification: 分层数据 (某个影响因子的分层结果)

        Returns:
            Q统计量值 (0-1之间)
        """
        try:
            # 去除无效值
            valid_mask = ~(np.isnan(y_data) | np.isnan(stratification))
            y_clean = y_data[valid_mask]
            strat_clean = stratification[valid_mask]

            if len(y_clean) == 0:
                return 0.0

            # 计算总体方差
            total_variance = np.var(y_clean)
            if total_variance == 0:
                return 0.0

            # 计算各层内方差
            unique_strata = np.unique(strat_clean)
            weighted_within_variance = 0.0
            total_n = len(y_clean)

            for stratum in unique_strata:
                stratum_mask = strat_clean == stratum
                stratum_y = y_clean[stratum_mask]
                stratum_n = len(stratum_y)

                if stratum_n > 1:
                    stratum_variance = np.var(stratum_y)
                    weight = stratum_n / total_n
                    weighted_within_variance += weight * stratum_variance

            # 计算Q值
            q_value = 1 - (weighted_within_variance / total_variance)
            return max(0.0, min(1.0, q_value))  # 确保Q值在[0,1]范围内

        except Exception as e:
            self.logger.error(f"计算Q统计量时出错: {e}")
            return 0.0

    def generate_stratification(self, factor_data: np.ndarray, n_strata: int = 5) -> np.ndarray:
        """
        生成分层数据（基于分位数）

        Args:
            factor_data: 影响因子数据
            n_strata: 分层数量

        Returns:
            分层结果数组
        """
        try:
            valid_data = factor_data[~np.isnan(factor_data)]
            if len(valid_data) == 0:
                return np.full_like(factor_data, np.nan)

            # 计算分位数边界
            percentiles = np.linspace(0, 100, n_strata + 1)
            boundaries = np.percentile(valid_data, percentiles)

            # 分层
            stratification = np.digitize(factor_data, boundaries[1:-1])
            return stratification.astype(float)

        except Exception as e:
            self.logger.error(f"生成分层数据时出错: {e}")
            return np.full_like(factor_data, np.nan)

    def extract_spatial_data(self, year: int, sample_points: Optional[List[Tuple[float, float]]] = None) -> Dict[
        str, np.ndarray]:
        """
        从本地数据提取空间数据用于地理探测器分析

        Args:
            year: 分析年份
            sample_points: 采样点坐标列表，如果为None则自动生成

        Returns:
            包含各影响因子数据的字典
        """
        try:
            # 获取RSEI数据作为因变量
            rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)

            # 如果没有提供采样点，则根据RSEI数据生成采样点
            if sample_points is None:
                sample_points = self._generate_sample_points(rsei_data, rsei_profile)

            # 提取各因子数据
            factor_data = {}
            coordinates = []

            for lat, lng in sample_points:
                try:
                    # 获取该点的气候和土地覆盖数据
                    point_data = self.climate_service.get_point_climate_data(lat, lng, year)

                    # 检查数据是否有效
                    if all(point_data[key] is not None for key in ['temperature', 'rainfall', 'rsei', 'lucc']):
                        coordinates.append((lat, lng))

                        # 收集各因子数据
                        for factor in ['temperature', 'rainfall', 'rsei', 'lucc']:
                            if factor not in factor_data:
                                factor_data[factor] = []
                            factor_data[factor].append(point_data[factor])

                except Exception as e:
                    self.logger.warning(f"提取点位数据失败: lat={lat}, lng={lng}, 错误: {str(e)}")
                    continue

            # 转换为numpy数组
            for factor in factor_data:
                factor_data[factor] = np.array(factor_data[factor])

            # 添加坐标信息
            factor_data['coordinates'] = coordinates

            self.logger.info(f"成功提取 {len(coordinates)} 个有效采样点的数据")
            return factor_data

        except Exception as e:
            self.logger.error(f"提取空间数据失败: {str(e)}")
            return {}

    def _generate_sample_points(self, rsei_data: np.ndarray,
                                rsei_profile: rasterio.profiles.Profile,
                                max_points: int = 500) -> List[Tuple[float, float]]:
        """
        基于RSEI数据生成采样点

        Args:
            rsei_data: RSEI数据数组
            rsei_profile: RSEI栅格配置
            max_points: 最大采样点数量

        Returns:
            采样点坐标列表
        """
        try:
            transform = rsei_profile['transform']
            height, width = rsei_data.shape

            # 找到有效数据点
            valid_mask = ~np.isnan(rsei_data)
            valid_indices = np.where(valid_mask)

            if len(valid_indices[0]) == 0:
                self.logger.warning("RSEI数据中没有有效像素")
                return []

            # 如果有效点太多，进行采样
            total_valid = len(valid_indices[0])
            if total_valid > max_points:
                # 随机采样
                sample_indices = np.random.choice(total_valid, max_points, replace=False)
                rows = valid_indices[0][sample_indices]
                cols = valid_indices[1][sample_indices]
            else:
                rows = valid_indices[0]
                cols = valid_indices[1]

            # 转换为地理坐标
            sample_points = []
            for row, col in zip(rows, cols):
                # 栅格坐标转地理坐标
                lng, lat = transform * (col + 0.5, row + 0.5)  # 取像素中心
                sample_points.append((lat, lng))

            self.logger.info(f"生成 {len(sample_points)} 个采样点")
            return sample_points

        except Exception as e:
            self.logger.error(f"生成采样点失败: {str(e)}")
            return []

    def run_geodetector_analysis(self, year: int,
                                 sample_points: Optional[List[Tuple[float, float]]] = None) -> Dict[str, Any]:
        """
        运行地理探测器分析

        Args:
            year: 分析年份
            sample_points: 采样点坐标列表，如果为None则自动生成

        Returns:
            分析结果字典
        """
        results = {
            'q_values': {},
            'factor_importance': [],
            'interaction_results': {},
            'summary_stats': {},
            'year': year,
            'sample_points_count': 0
        }

        try:
            # 提取空间数据
            spatial_data = self.extract_spatial_data(year, sample_points)

            if not spatial_data or 'rsei' not in spatial_data:
                self.logger.error("未能获取有效的空间数据")
                return results

            coordinates = spatial_data.pop('coordinates', [])
            results['sample_points_count'] = len(coordinates)

            # RSEI作为因变量
            rsei_data = spatial_data.pop('rsei')

            # 其他因子作为自变量
            factor_data_dict = spatial_data

            # 单因子探测
            for factor_name, factor_data in factor_data_dict.items():
                if len(factor_data) == 0:
                    continue

                stratification = self.generate_stratification(factor_data)
                q_value = self.calculate_q_statistic(rsei_data, stratification)

                results['q_values'][factor_name] = {
                    'q_value': round(q_value, 4),
                    'explanation_power': round(q_value * 100, 2),
                    'factor_info': self.factor_info.get(factor_name, {'name': factor_name, 'unit': ''}),
                    'data_range': {
                        'min': float(np.min(factor_data)),
                        'max': float(np.max(factor_data)),
                        'mean': float(np.mean(factor_data)),
                        'std': float(np.std(factor_data))
                    }
                }

            # 按Q值排序因子重要性
            sorted_factors = sorted(results['q_values'].items(),
                                    key=lambda x: x[1]['q_value'], reverse=True)
            results['factor_importance'] = [
                {
                    'factor': factor,
                    'q_value': data['q_value'],
                    'explanation_power': data['explanation_power'],
                    'rank': i + 1
                }
                for i, (factor, data) in enumerate(sorted_factors)
            ]

            # 交互探测（选择前4个重要因子，避免计算量过大）
            top_factors = [item[0] for item in sorted_factors[:4]]
            for i, factor1 in enumerate(top_factors):
                for factor2 in top_factors[i + 1:]:
                    if factor1 in factor_data_dict and factor2 in factor_data_dict:
                        interaction_q = self._calculate_interaction(
                            rsei_data,
                            factor_data_dict[factor1],
                            factor_data_dict[factor2]
                        )

                        results['interaction_results'][f"{factor1}_{factor2}"] = {
                            'q_value': round(interaction_q, 4),
                            'factor1': factor1,
                            'factor2': factor2,
                            'factor1_q': results['q_values'][factor1]['q_value'],
                            'factor2_q': results['q_values'][factor2]['q_value'],
                            'interaction_type': self._classify_interaction(
                                results['q_values'][factor1]['q_value'],
                                results['q_values'][factor2]['q_value'],
                                interaction_q
                            )
                        }

            # 汇总统计
            if results['q_values']:
                q_values_list = [data['q_value'] for data in results['q_values'].values()]
                results['summary_stats'] = {
                    'mean_q': round(np.mean(q_values_list), 4),
                    'max_q': round(np.max(q_values_list), 4),
                    'min_q': round(np.min(q_values_list), 4),
                    'total_factors': len(factor_data_dict),
                    'data_points': len(rsei_data),
                    'dominant_factor': sorted_factors[0][0] if sorted_factors else None,
                    'dominant_factor_q': sorted_factors[0][1]['q_value'] if sorted_factors else 0
                }

            self.logger.info(f"地理探测器分析完成，处理了 {len(coordinates)} 个采样点")

        except Exception as e:
            self.logger.error(f"地理探测器分析出错: {e}")

        return results

    def _calculate_interaction(self, y_data: np.ndarray,
                               factor1_data: np.ndarray,
                               factor2_data: np.ndarray) -> float:
        """
        计算两个因子的交互作用Q值
        """
        try:
            strat1 = self.generate_stratification(factor1_data)
            strat2 = self.generate_stratification(factor2_data)

            # 创建交互分层
            combined_strat = strat1 * 10 + strat2  # 简单的组合方法

            return self.calculate_q_statistic(y_data, combined_strat)
        except:
            return 0.0

    def _classify_interaction(self, q1: float, q2: float, q_interaction: float) -> str:
        """
        分类交互作用类型
        """
        if q_interaction > max(q1, q2):
            if q_interaction > q1 + q2:
                return "非线性增强"
            else:
                return "双因子增强"
        elif q_interaction > min(q1, q2):
            return "单因子非线性减弱"
        else:
            return "独立"

    def create_q_value_geojson(self, year: int, factor_name: str,
                               sample_points: Optional[List[Tuple[float, float]]] = None) -> Dict[str, Any]:
        """
        创建Q值热力图的GeoJSON数据

        Args:
            year: 分析年份
            factor_name: 因子名称
            sample_points: 采样点坐标列表

        Returns:
            GeoJSON格式数据
        """
        features = []

        try:
            # 获取空间数据
            spatial_data = self.extract_spatial_data(year, sample_points)

            if not spatial_data or factor_name not in spatial_data:
                self.logger.error(f"未找到因子 {factor_name} 的数据")
                return self._get_empty_geojson(factor_name)

            coordinates = spatial_data['coordinates']
            factor_data = spatial_data[factor_name]
            rsei_data = spatial_data['rsei']

            # 计算该因子的整体Q值
            stratification = self.generate_stratification(factor_data)
            overall_q = self.calculate_q_statistic(rsei_data, stratification)

            # 为每个采样点创建GeoJSON特征
            for i, (lat, lng) in enumerate(coordinates):
                # 创建小的正方形区域来表示热力图点
                offset = 0.005  # 约500m的偏移，可根据数据密度调整
                polygon_coords = [
                    [lng - offset, lat - offset],
                    [lng + offset, lat - offset],
                    [lng + offset, lat + offset],
                    [lng - offset, lat + offset],
                    [lng - offset, lat - offset]
                ]

                # 计算局部Q值（使用滑动窗口方法）
                local_q = self._calculate_local_q_value(
                    i, coordinates, factor_data, rsei_data, window_size=20
                )

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon_coords]
                    },
                    "properties": {
                        "q_value": round(local_q, 4),
                        "factor": factor_name,
                        "factor_value": float(factor_data[i]),
                        "rsei_value": float(rsei_data[i]),
                        "explanation_power": round(local_q * 100, 2),
                        "point_id": i,
                        "lat": lat,
                        "lng": lng,
                        "color_intensity": min(255, int(local_q * 255)),  # 用于前端着色
                        "year": year
                    }
                }
                features.append(feature)

        except Exception as e:
            self.logger.error(f"创建GeoJSON时出错: {e}")
            return self._get_empty_geojson(factor_name)

        # 计算Q值范围用于图例
        q_values = [f["properties"]["q_value"] for f in features]

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "factor": factor_name,
                "factor_info": self.factor_info.get(factor_name, {'name': factor_name, 'unit': ''}),
                "year": year,
                "total_features": len(features),
                "overall_q_value": round(overall_q, 4),
                "q_range": {
                    "min": min(q_values) if q_values else 0,
                    "max": max(q_values) if q_values else 0,
                    "mean": round(np.mean(q_values), 4) if q_values else 0
                },
                "color_scheme": "viridis",  # 推荐的颜色方案
                "legend_breaks": self._calculate_legend_breaks(q_values)
            }
        }

    def _calculate_local_q_value(self, center_idx: int, coordinates: List[Tuple[float, float]],
                                 factor_data: np.ndarray, rsei_data: np.ndarray,
                                 window_size: int = 20) -> float:
        """
        计算局部Q值（基于邻近点的窗口）

        Args:
            center_idx: 中心点索引
            coordinates: 所有坐标点
            factor_data: 因子数据
            rsei_data: RSEI数据
            window_size: 窗口大小

        Returns:
            局部Q值
        """
        try:
            if len(coordinates) <= window_size:
                # 如果总点数少于窗口大小，使用全部数据
                stratification = self.generate_stratification(factor_data)
                return self.calculate_q_statistic(rsei_data, stratification)

            # 计算中心点到所有其他点的距离
            center_lat, center_lng = coordinates[center_idx]
            distances = []

            for i, (lat, lng) in enumerate(coordinates):
                # 简单的欧几里得距离（对于小范围区域近似有效）
                dist = np.sqrt((lat - center_lat) ** 2 + (lng - center_lng) ** 2)
                distances.append((dist, i))

            # 选择最近的点（包括中心点）
            distances.sort()
            selected_indices = [idx for _, idx in distances[:window_size]]

            # 提取窗口内的数据
            window_factor_data = factor_data[selected_indices]
            window_rsei_data = rsei_data[selected_indices]

            # 计算局部Q值
            stratification = self.generate_stratification(window_factor_data)
            return self.calculate_q_statistic(window_rsei_data, stratification)

        except Exception as e:
            self.logger.warning(f"计算局部Q值失败: {e}")
            return 0.0

    def _calculate_legend_breaks(self, q_values: List[float], n_breaks: int = 5) -> List[float]:
        """
        计算图例分级断点
        """
        if not q_values:
            return [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

        try:
            # 使用分位数方法
            percentiles = np.linspace(0, 100, n_breaks + 1)
            breaks = np.percentile(q_values, percentiles)
            return [round(b, 3) for b in breaks]
        except:
            return [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    def _get_empty_geojson(self, factor_name: str) -> Dict[str, Any]:
        """
        获取空的GeoJSON结构
        """
        return {
            "type": "FeatureCollection",
            "features": [],
            "metadata": {
                "factor": factor_name,
                "factor_info": self.factor_info.get(factor_name, {'name': factor_name, 'unit': ''}),
                "total_features": 0,
                "error": "无有效数据"
            }
        }

    def get_geodetector_results(self, year: Optional[int] = None,
                                factor: Optional[str] = None) -> Dict[str, Any]:
        """
        获取地理探测器结果数据

        Args:
            year: 年份（可选）
            factor: 特定因子（可选）

        Returns:
            地理探测器结果数据
        """
        cache_key = f"geodetector_{year}_{factor}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # 这里应该从实际数据源加载数据
            # 目前使用模拟数据进行演示
            results = self._generate_sample_data(year, factor)

            # 缓存结果
            self._cache[cache_key] = results

            return results

        except Exception as e:
            self.logger.error(f"获取地理探测器结果时出错: {e}")
            return self._get_default_results()

    def _generate_sample_data(self, year: Optional[int] = None,
                              factor: Optional[str] = None) -> Dict[str, Any]:
        """
        生成示例数据（实际应用中应从数据库或文件加载）
        """
        # 生成示例坐标点（江西省范围）
        np.random.seed(42)
        n_points = 100

        # 江西省大致范围
        lat_range = (27.5, 28.0)
        lng_range = (117.5, 118.5)

        coordinates = [
            (
                np.random.uniform(*lat_range),
                np.random.uniform(*lng_range)
            )
            for _ in range(n_points)
        ]

        # 生成模拟的RSEI和因子数据
        rsei_data = np.random.normal(0.6, 0.2, n_points)
        rsei_data = np.clip(rsei_data, 0, 1)

        factor_data_dict = {
            'temperature': np.random.normal(18, 5, n_points),
            'precipitation': np.random.normal(1500, 300, n_points),
            'elevation': np.random.uniform(50, 2000, n_points),
            'slope': np.random.uniform(0, 45, n_points),
            'ndvi': np.random.uniform(0.2, 0.9, n_points),
            'population': np.random.lognormal(4, 1, n_points)
        }

        # 运行地理探测器分析
        analysis_results = self.run_geodetector_analysis(
            rsei_data, factor_data_dict, coordinates
        )

        # 如果指定了特定因子，生成该因子的GeoJSON
        if factor and factor in factor_data_dict:
            # 为每个点计算该因子的局部Q值（模拟）
            local_q_values = {}
            base_q = analysis_results['q_values'].get(factor, {}).get('q_value', 0.5)

            for i in range(n_points):
                # 添加一些随机变化
                local_q = base_q + np.random.normal(0, 0.1)
                local_q = max(0, min(1, local_q))
                local_q_values[f"point_{i}"] = local_q

            geojson_data = self.create_q_value_geojson(
                coordinates, local_q_values, factor
            )

            return {
                'geojson': geojson_data,
                'analysis_results': analysis_results,
                'year': year,
                'factor': factor
            }

        # 返回整体分析结果
        return {
            'analysis_results': analysis_results,
            'coordinates': coordinates,
            'year': year,
            'available_factors': list(factor_data_dict.keys())
        }

    def _get_default_results(self) -> Dict[str, Any]:
        """
        获取默认结果（错误情况下使用）
        """
        return {
            'analysis_results': {
                'q_values': {},
                'factor_importance': [],
                'interaction_results': {},
                'summary_stats': {
                    'mean_q': 0.0,
                    'max_q': 0.0,
                    'min_q': 0.0,
                    'total_factors': 0,
                    'data_points': 0
                }
            },
            'coordinates': [],
            'year': None,
            'available_factors': []
        }

    def get_available_years(self) -> List[int]:
        """
        获取可用的年份列表
        """
        # 实际应用中应从数据源获取
        return list(range(2000, 2021))

    def get_available_factors(self) -> List[Dict[str, str]]:
        """
        获取可用的影响因子列表
        """
        return [
            {
                'factor': factor,
                'name': info['name'],
                'unit': info['unit']
            }
            for factor, info in self.factor_info.items()
        ]


# 使用示例
if __name__ == "__main__":
    # 初始化服务
    service = GeodetectorService()

    # 获取整体分析结果
    results = service.get_geodetector_results(year=2020)
    print("整体分析结果:")
    print(f"因子数量: {len(results['analysis_results']['q_values'])}")
    print(f"平均Q值: {results['analysis_results']['summary_stats']['mean_q']}")

    # 获取特定因子的GeoJSON数据
    temperature_results = service.get_geodetector_results(year=2020, factor='temperature')
    print(f"\n温度因子GeoJSON特征数量: {len(temperature_results['geojson']['features'])}")

    # 获取可用因子
    factors = service.get_available_factors()
    print(f"\n可用因子: {[f['name'] for f in factors]}")
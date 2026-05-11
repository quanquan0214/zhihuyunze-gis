import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import json
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import logging

'''
核心功能：
1. 地理加权回归计算：实现了完整的GWR算法，支持多种空间权重核函数
2. 热力图数据生成：将GWR结果转换为GeoJSON格式，便于前端地图叠加
3. 网格化分析：在指定区域生成网格点，为每个点计算局部回归系数
主要方法：
• calculate_gwr_results(): 核心计算方法，返回完整的GWR分析结果
• get_gwr_geojson(): 生成前端需要的GeoJSON格式热力图数据
• get_diagnostic_info(): 提供模型诊断信息
配置选项：
• 支持多种核函数（gaussian、exponential、bisquare）
• 可调节带宽参数控制空间权重衰减
• 可选择特定年份和特征变量进行分析
返回数据格式：
返回的GeoJSON包含每个网格点的：
• 回归系数值（用于热力图着色）
• R²值（拟合优度）
• 统计信息（最值、均值、分位数等）
'''
class GWRService:
    """
    地理加权回归服务类
    功能：返回某一年份/区域的 GWR 回归结果热力图数据（GeoJSON）
    用途：前端叠加地图用
    """

    def __init__(self, bandwidth: float = 0.5, kernel: str = 'gaussian'):
        """
        初始化GWR服务

        Args:
            bandwidth: 带宽参数，控制空间权重的衰减速度
            kernel: 核函数类型，支持 'gaussian', 'exponential', 'bisquare'
        """
        self.bandwidth = bandwidth
        self.kernel = kernel
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)

    def _calculate_spatial_weights(self, coords: np.ndarray, target_coord: np.ndarray) -> np.ndarray:
        """
        计算空间权重矩阵

        Args:
            coords: 所有观测点坐标 (n, 2)
            target_coord: 目标点坐标 (2,)

        Returns:
            权重向量 (n,)
        """
        # 计算欧氏距离
        distances = np.sqrt(np.sum((coords - target_coord) ** 2, axis=1))

        # 根据核函数类型计算权重
        if self.kernel == 'gaussian':
            weights = np.exp(-(distances / self.bandwidth) ** 2)
        elif self.kernel == 'exponential':
            weights = np.exp(-distances / self.bandwidth)
        elif self.kernel == 'bisquare':
            weights = np.where(distances <= self.bandwidth,
                               (1 - (distances / self.bandwidth) ** 2) ** 2, 0)
        else:
            raise ValueError(f"不支持的核函数类型: {self.kernel}")

        return weights

    def _fit_local_regression(self, X: np.ndarray, y: np.ndarray, weights: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        执行加权局部回归

        Args:
            X: 特征矩阵
            y: 目标变量
            weights: 权重向量

        Returns:
            回归系数和R²值
        """
        try:
            # 加权最小二乘回归
            W = np.diag(weights)
            XTW = X.T @ W
            XTWX_inv = np.linalg.inv(XTW @ X)
            coefficients = XTWX_inv @ XTW @ y

            # 计算局部R²
            y_pred = X @ coefficients
            ss_res = np.sum(weights * (y - y_pred) ** 2)
            ss_tot = np.sum(weights * (y - np.average(y, weights=weights)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            return coefficients, r_squared

        except np.linalg.LinAlgError:
            # 如果矩阵奇异，返回零系数
            self.logger.warning("矩阵奇异，返回零系数")
            return np.zeros(X.shape[1]), 0.0

    def _generate_grid_points(self, bounds: Dict[str, float], resolution: int = 50) -> np.ndarray:
        """
        生成网格点用于热力图

        Args:
            bounds: 边界范围 {'min_lng', 'max_lng', 'min_lat', 'max_lat'}
            resolution: 网格分辨率

        Returns:
            网格点坐标数组
        """
        lng_range = np.linspace(bounds['min_lng'], bounds['max_lng'], resolution)
        lat_range = np.linspace(bounds['min_lat'], bounds['max_lat'], resolution)
        lng_grid, lat_grid = np.meshgrid(lng_range, lat_range)

        grid_points = np.column_stack([lng_grid.ravel(), lat_grid.ravel()])
        return grid_points

    def calculate_gwr_results(self,
                              data: pd.DataFrame,
                              year: Optional[int] = None,
                              target_var: str = 'rsei',
                              feature_vars: List[str] = ['temperature', 'precipitation'],
                              bounds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        计算GWR回归结果

        Args:
            data: 包含坐标、目标变量和特征变量的数据框
            year: 年份筛选（可选）
            target_var: 目标变量名
            feature_vars: 特征变量名列表
            bounds: 地理边界范围

        Returns:
            GWR结果字典
        """
        try:
            # 数据筛选
            if year is not None:
                data = data[data['year'] == year].copy()

            if data.empty:
                raise ValueError(f"没有找到{year}年的数据")

            # 提取坐标和变量
            coords = data[['lng', 'lat']].values
            y = data[target_var].values
            X = data[feature_vars].values

            # 数据标准化
            X_scaled = self.scaler.fit_transform(X)
            X_with_intercept = np.column_stack([np.ones(len(X_scaled)), X_scaled])

            # 确定边界范围
            if bounds is None:
                bounds = {
                    'min_lng': coords[:, 0].min(),
                    'max_lng': coords[:, 0].max(),
                    'min_lat': coords[:, 1].min(),
                    'max_lat': coords[:, 1].max()
                }

            # 生成网格点
            grid_points = self._generate_grid_points(bounds)

            # 为每个网格点计算GWR结果
            grid_results = []
            for i, grid_point in enumerate(grid_points):
                # 计算空间权重
                weights = self._calculate_spatial_weights(coords, grid_point)

                # 执行局部回归
                coefficients, r_squared = self._fit_local_regression(X_with_intercept, y, weights)

                grid_results.append({
                    'lng': float(grid_point[0]),
                    'lat': float(grid_point[1]),
                    'intercept': float(coefficients[0]),
                    'coefficients': [float(c) for c in coefficients[1:]],
                    'r_squared': float(r_squared),
                    'feature_names': feature_vars
                })

            return {
                'grid_results': grid_results,
                'bounds': bounds,
                'year': year,
                'target_var': target_var,
                'feature_vars': feature_vars,
                'total_points': len(grid_results)
            }

        except Exception as e:
            self.logger.error(f"GWR计算失败: {str(e)}")
            raise

    def get_gwr_geojson(self,
                        data: pd.DataFrame,
                        year: Optional[int] = None,
                        coefficient_index: int = 0,
                        target_var: str = 'rsei',
                        feature_vars: List[str] = ['temperature', 'precipitation']) -> Dict[str, Any]:
        """
        获取GWR结果的GeoJSON格式数据

        Args:
            data: 输入数据
            year: 年份
            coefficient_index: 要可视化的系数索引（0表示第一个特征变量的系数）
            target_var: 目标变量名
            feature_vars: 特征变量名列表

        Returns:
            GeoJSON格式的热力图数据
        """
        try:
            # 计算GWR结果
            gwr_results = self.calculate_gwr_results(
                data=data,
                year=year,
                target_var=target_var,
                feature_vars=feature_vars
            )

            # 构建GeoJSON
            features = []
            coefficient_values = []

            for result in gwr_results['grid_results']:
                if coefficient_index < len(result['coefficients']):
                    coeff_value = result['coefficients'][coefficient_index]
                    coefficient_values.append(coeff_value)

                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [result['lng'], result['lat']]
                        },
                        "properties": {
                            "coefficient": coeff_value,
                            "r_squared": result['r_squared'],
                            "intercept": result['intercept'],
                            "all_coefficients": result['coefficients'],
                            "feature_name": feature_vars[coefficient_index] if coefficient_index < len(
                                feature_vars) else f"coeff_{coefficient_index}"
                        }
                    }
                    features.append(feature)

            # 计算统计信息
            if coefficient_values:
                coeff_array = np.array(coefficient_values)
                statistics = {
                    "min": float(np.min(coeff_array)),
                    "max": float(np.max(coeff_array)),
                    "mean": float(np.mean(coeff_array)),
                    "std": float(np.std(coeff_array)),
                    "quantiles": {
                        "25%": float(np.percentile(coeff_array, 25)),
                        "50%": float(np.percentile(coeff_array, 50)),
                        "75%": float(np.percentile(coeff_array, 75))
                    }
                }
            else:
                statistics = {}

            geojson = {
                "type": "FeatureCollection",
                "features": features,
                "properties": {
                    "year": year,
                    "target_variable": target_var,
                    "feature_variable": feature_vars[coefficient_index] if coefficient_index < len(
                        feature_vars) else f"coeff_{coefficient_index}",
                    "coefficient_index": coefficient_index,
                    "statistics": statistics,
                    "total_features": len(features),
                    "bounds": gwr_results['bounds']
                }
            }

            return geojson

        except Exception as e:
            self.logger.error(f"生成GWR GeoJSON失败: {str(e)}")
            raise

    def get_diagnostic_info(self, data: pd.DataFrame, year: Optional[int] = None) -> Dict[str, Any]:
        """
        获取GWR模型诊断信息

        Args:
            data: 输入数据
            year: 年份

        Returns:
            诊断信息字典
        """
        try:
            gwr_results = self.calculate_gwr_results(data, year)

            # 提取R²值
            r_squared_values = [result['r_squared'] for result in gwr_results['grid_results']]
            r_squared_array = np.array(r_squared_values)

            # 计算诊断统计
            diagnostics = {
                "bandwidth": self.bandwidth,
                "kernel": self.kernel,
                "total_points": len(r_squared_values),
                "r_squared_stats": {
                    "min": float(np.min(r_squared_array)),
                    "max": float(np.max(r_squared_array)),
                    "mean": float(np.mean(r_squared_array)),
                    "std": float(np.std(r_squared_array))
                },
                "model_performance": {
                    "good_fit_ratio": float(np.sum(r_squared_array > 0.7) / len(r_squared_array)),
                    "poor_fit_ratio": float(np.sum(r_squared_array < 0.3) / len(r_squared_array))
                }
            }

            return diagnostics

        except Exception as e:
            self.logger.error(f"获取诊断信息失败: {str(e)}")
            raise



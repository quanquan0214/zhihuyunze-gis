from shapely.geometry import Polygon

# 定义四个点的坐标 (x, y)
points = [(0, 0), (1, 0), (1, 1), (0, 1)]

# 创建多边形
polygon = Polygon(points)
print(polygon)  # 输出：POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))
if not polygon.is_valid:
    print("Invalid polygon geometry formed by points")
else:
    print("Valid polygon geometry formed by points")
#
# # 示例使用方法
# def example_usage():
#     """
#     示例使用方法
#     """
#     # 创建模拟数据
#     np.random.seed(42)
#     n_points = 100
#
#     data = pd.DataFrame({
#         'lng': np.random.uniform(113, 118, n_points),
#         'lat': np.random.uniform(25, 30, n_points),
#         'year': np.random.choice([2015, 2016, 2017, 2018, 2019], n_points),
#         'temperature': np.random.normal(25, 5, n_points),
#         'precipitation': np.random.normal(1200, 300, n_points),
#         'rsei': np.random.uniform(0.3, 0.8, n_points)
#     })
#     print(data.head())
#
#     # 创建GWR服务实例
#     gwr_service = GWRService(bandwidth=1.0, kernel='gaussian')
#
#     # 获取2015年温度系数的GeoJSON热力图
#     geojson_result = gwr_service.get_gwr_geojson(
#         data=data,
#         year=2015,
#         coefficient_index=0,  # 温度系数
#         feature_vars=['temperature', 'precipitation']
#     )
#
#     # 获取诊断信息
#     diagnostics = gwr_service.get_diagnostic_info(data, year=2015)
#
#     return geojson_result, diagnostics
#
#
# if __name__ == "__main__":
#     # 运行示例
#     geojson, diag = example_usage()
#     print(f"生成了 {len(geojson['features'])} 个网格点的GWR结果")
#     print(f"平均R²值: {diag['r_squared_stats']['mean']:.3f}")
#
#
#


# def calculate_morans_i(self, year: int, variable: str = 'rsei', threshold: float = 1000,
#                        lucc_encoding: str = 'continuous', sample_ratio: float = 0.1) -> Dict[str, float]:
#     """
#     计算指定变量的Moran’s I（空间自相关性）
#     Args:
#         year: 年份
#         variable: 变量名 ('rsei', 'temperature', 'rainfall', 'lucc')
#         threshold: 距离阈值（米，默认为1000）
#         lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
#         sample_ratio: 数据采样比例（默认0.1，即10%）
#     Returns:
#         包含Moran’s I和p值的字典
#     """
#     try:
#         coords, y, X = self.get_gwr_input_data(year, include_lucc=True, lucc_encoding=lucc_encoding)
#         # 采样数据以减少内存占用
#         n_points = coords.shape[0]
#         if n_points > 10000:  # 仅对大数据集采样
#             sample_size = max(1000, int(n_points * sample_ratio))
#             sample_indices = np.random.choice(n_points, size=sample_size, replace=False)
#             coords = coords[sample_indices]
#             y = y[sample_indices]
#             X = X[sample_indices]
#             self.logger.info(f"采样数据: 从 {n_points} 个点采样到 {sample_size} 个点")
#
#         if variable == 'rsei':
#             data = y.flatten()
#         elif variable == 'temperature':
#             data = X[:, 0]
#         elif variable == 'rainfall':
#             data = X[:, 1]
#         elif variable == 'lucc':
#             if lucc_encoding == 'dummy' and X.shape[1] > 3:
#                 raise ValueError("Moran's I不支持多列LUCC哑变量，请使用continuous编码或选择单一LUCC类别")
#             data = X[:, 2]  # 假设使用连续编码或单一类别
#         else:
#             raise ValueError(f"不支持的变量: {variable}")
#
#         # 使用较小的阈值减少邻居数量
#         w = DistanceBand(coords, threshold=threshold, binary=True, silence_warnings=True)
#         moran = Moran(data, w)
#         return {
#             'morans_i': float(moran.I),
#             'p_value': float(moran.p_sim),
#             'variable': variable,
#             'year': year,
#             'sample_size': coords.shape[0]
#         }
#     except MemoryError as e:
#         self.logger.error(
#             f"Moran’s I计算失败: year={year}, variable={variable}, 内存不足。尝试减小threshold或sample_ratio。错误: {str(e)}")
#         raise
#     except Exception as e:
#         self.logger.error(f"Moran’s I计算失败: year={year}, variable={variable}, 错误: {str(e)}")
#         raise
#
# def calculate_morans_i(self, year: int, variable: str = 'rsei', threshold: float = 500,
#                        lucc_encoding: str = 'continuous', sample_ratio: float = 0.01) -> Dict[str, float]:
#     """
#     计算指定变量的Moran’s I（空间自相关性）
#     Args:
#         year: 年份
#         variable: 变量名 ('rsei', 'temperature', 'rainfall', 'lucc')
#         threshold: 距离阈值（米，默认为500）
#         lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
#         sample_ratio: 数据采样比例（默认0.01，即1%）
#     Returns:
#         包含Moran’s I和p值的字典
#     """
#     try:
#         coords, y, X = self.get_gwr_input_data(year, include_lucc=True, lucc_encoding=lucc_encoding)
#         # 采样数据以减少内存占用
#         n_points = coords.shape[0]
#         if n_points > 5000:  # 仅对大数据集采样
#             sample_size = max(1000, int(n_points * sample_ratio))
#             sample_indices = np.random.choice(n_points, size=sample_size, replace=False)
#             coords = coords[sample_indices]
#             y = y[sample_indices]
#             X = X[sample_indices]
#             self.logger.info(f"采样数据: 从 {n_points} 个点采样到 {sample_size} 个点")
#         else:
#             self.logger.info(f"数据点数 {n_points} 小于5000，无需采样")
#
#         if variable == 'rsei':
#             data = y.flatten()
#         elif variable == 'temperature':
#             data = X[:, 0]
#         elif variable == 'rainfall':
#             data = X[:, 1]
#         elif variable == 'lucc':
#             if lucc_encoding == 'dummy' and X.shape[1] > 3:
#                 raise ValueError("Moran's I不支持多列LUCC哑变量，请使用continuous编码或选择单一LUCC类别")
#             data = X[:, 2]  # 假设使用连续编码或单一类别
#         else:
#             raise ValueError(f"不支持的变量: {variable}")
#
#         # 构建空间权重矩阵
#         w = DistanceBand(coords, threshold=threshold, binary=True, silence_warnings=True)
#         moran = Moran(data, w)
#         return {
#             'morans_i': float(moran.I),
#             'p_value': float(moran.p_sim),
#             'variable': variable,
#             'year': year,
#             'sample_size': coords.shape[0]
#         }
#     except MemoryError as e:
#         self.logger.error(
#             f"Moran’s I计算失败: year={year}, variable={variable}, 内存不足。尝试减小threshold（当前={threshold}）或sample_ratio（当前={sample_ratio}），或裁剪栅格范围。错误: {str(e)}")
#         raise
#     except Exception as e:
#         self.logger.error(f"Moran’s I计算失败: year={year}, variable={variable}, 错误: {str(e)}")
#         raise

# GWR服务类的完整实现
#
# class GWRService:
#     """
#     地理加权回归服务类
#     功能：返回某一年份/区域的 GWR 回归结果热力图数据（GeoJSON）
#     用途：前端叠加地图用
#     """
#
#     def __init__(self, bandwidth: float = 0.5, kernel: str = 'gaussian'):
#         self.bandwidth = bandwidth
#         self.kernel = kernel
#         self.scaler = StandardScaler()
#         self.logger = logging.getLogger(__name__)
#
#     def _calculate_spatial_weights(self, coords: np.ndarray, target_coord: np.ndarray) -> np.ndarray:
#         """计算空间权重矩阵"""
#         distances = np.sqrt(np.sum((coords - target_coord) ** 2, axis=1))
#
#         if self.kernel == 'gaussian':
#             weights = np.exp(-(distances / self.bandwidth) ** 2)
#         elif self.kernel == 'exponential':
#             weights = np.exp(-distances / self.bandwidth)
#         elif self.kernel == 'bisquare':
#             weights = np.where(distances <= self.bandwidth,
#                                (1 - (distances / self.bandwidth) ** 2) ** 2, 0)
#         else:
#             raise ValueError(f"不支持的核函数类型: {self.kernel}")
#
#         return weights
#
#     def _fit_local_regression(self, X: np.ndarray, y: np.ndarray, weights: np.ndarray) -> Tuple[np.ndarray, float]:
#         """执行加权局部回归"""
#         try:
#             W = np.diag(weights)
#             XTW = X.T @ W
#             XTWX_inv = np.linalg.inv(XTW @ X)
#             coefficients = XTWX_inv @ XTW @ y
#
#             y_pred = X @ coefficients
#             ss_res = np.sum(weights * (y - y_pred) ** 2)
#             ss_tot = np.sum(weights * (y - np.average(y, weights=weights)) ** 2)
#             r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
#
#             return coefficients, r_squared
#
#         except np.linalg.LinAlgError:
#             self.logger.warning("矩阵奇异，返回零系数")
#             return np.zeros(X.shape[1]), 0.0
#
#     def _generate_grid_points(self, bounds: Dict[str, float], resolution: int = 30) -> np.ndarray:
#         """生成网格点用于热力图"""
#         lng_range = np.linspace(bounds['min_lng'], bounds['max_lng'], resolution)
#         lat_range = np.linspace(bounds['min_lat'], bounds['max_lat'], resolution)
#         lng_grid, lat_grid = np.meshgrid(lng_range, lat_range)
#
#         grid_points = np.column_stack([lng_grid.ravel(), lat_grid.ravel()])
#         return grid_points
#
#     def get_combined_data(self, rsei_analyzer, rt_analyzer, year: Optional[int] = None) -> pd.DataFrame:
#         """
#         整合RSEI和气候数据用于GWR分析
#         使用实际的数据分析器获取数据
#         """
#         try:
#             # 获取RSEI数据 - 这里需要根据实际API调整
#             # 假设RasterAnalyzer有获取栅格数据的方法
#             rsei_data = rsei_analyzer.get_spatial_data(year=year)
#
#             # 获取气候数据
#             climate_data = rt_analyzer.get_spatial_data(year=year)
#
#             # # 如果没有实际的空间数据获取方法，使用模拟数据
#             # if not hasattr(rsei_analyzer, 'get_spatial_data'):
#             #     return self._generate_mock_data(year)
#
#             # 合并数据
#             combined_data = pd.merge(rsei_data, climate_data, on=['lng', 'lat', 'year'], how='inner')
#
#             return combined_data
#
#         except Exception as e:
#             self.logger.warning(f"获取实际数据失败，使用模拟数据: {str(e)}")
#             return self._generate_mock_data(year)
#
#     def _generate_mock_data(self, year: Optional[int] = None) -> pd.DataFrame:
#         """生成模拟数据用于测试"""
#         np.random.seed(42)
#         n_points = 150
#
#         if year is not None:
#             years = [year] * n_points
#         else:
#             years = np.random.choice([2015, 2016, 2017, 2018, 2019, 2020], n_points)
#
#         # 生成中国南方某区域的坐标范围
#         data = pd.DataFrame({
#             'lng': np.random.uniform(113, 118, n_points),
#             'lat': np.random.uniform(25, 30, n_points),
#             'year': years,
#             'temperature': np.random.normal(25, 5, n_points),
#             'precipitation': np.random.normal(1200, 300, n_points),
#             'rsei': np.random.uniform(0.3, 0.8, n_points)
#         })
#
#         return data
#
#     def get_gwr_geojson(self,
#                         data: pd.DataFrame,
#                         year: Optional[int] = None,
#                         coefficient_index: int = 0,
#                         target_var: str = 'rsei',
#                         feature_vars: List[str] = ['temperature', 'precipitation']) -> Dict[str, Any]:
#         """获取GWR结果的GeoJSON格式数据"""
#         try:
#             # 数据筛选
#             if year is not None:
#                 data = data[data['year'] == year].copy()
#
#             if data.empty:
#                 raise ValueError(f"没有找到{year}年的数据")
#
#             # 提取坐标和变量
#             coords = data[['lng', 'lat']].values
#             y = data[target_var].values
#             X = data[feature_vars].values
#
#             # 数据标准化
#             X_scaled = self.scaler.fit_transform(X)
#             X_with_intercept = np.column_stack([np.ones(len(X_scaled)), X_scaled])
#
#             # 确定边界范围
#             bounds = {
#                 'min_lng': float(coords[:, 0].min()),
#                 'max_lng': float(coords[:, 0].max()),
#                 'min_lat': float(coords[:, 1].min()),
#                 'max_lat': float(coords[:, 1].max())
#             }
#
#             # 生成网格点
#             grid_points = self._generate_grid_points(bounds, resolution=25)
#
#             # 为每个网格点计算GWR结果
#             features = []
#             coefficient_values = []
#
#             for grid_point in grid_points:
#                 # 计算空间权重
#                 weights = self._calculate_spatial_weights(coords, grid_point)
#
#                 # 执行局部回归
#                 coefficients, r_squared = self._fit_local_regression(X_with_intercept, y, weights)
#
#                 if coefficient_index < len(coefficients[1:]):
#                     coeff_value = float(coefficients[1 + coefficient_index])
#                     coefficient_values.append(coeff_value)
#
#                     feature = {
#                         "type": "Feature",
#                         "geometry": {
#                             "type": "Point",
#                             "coordinates": [float(grid_point[0]), float(grid_point[1])]
#                         },
#                         "properties": {
#                             "coefficient": coeff_value,
#                             "r_squared": float(r_squared),
#                             "intercept": float(coefficients[0]),
#                             "feature_name": feature_vars[coefficient_index] if coefficient_index < len(
#                                 feature_vars) else f"coeff_{coefficient_index}"
#                         }
#                     }
#                     features.append(feature)
#
#             # 计算统计信息
#             if coefficient_values:
#                 coeff_array = np.array(coefficient_values)
#                 statistics = {
#                     "min": float(np.min(coeff_array)),
#                     "max": float(np.max(coeff_array)),
#                     "mean": float(np.mean(coeff_array)),
#                     "std": float(np.std(coeff_array)),
#                     "quantiles": {
#                         "25%": float(np.percentile(coeff_array, 25)),
#                         "50%": float(np.percentile(coeff_array, 50)),
#                         "75%": float(np.percentile(coeff_array, 75))
#                     }
#                 }
#             else:
#                 statistics = {}
#
#             geojson = {
#                 "type": "FeatureCollection",
#                 "features": features,
#                 "properties": {
#                     "year": year,
#                     "target_variable": target_var,
#                     "feature_variable": feature_vars[coefficient_index] if coefficient_index < len(
#                         feature_vars) else f"coeff_{coefficient_index}",
#                     "coefficient_index": coefficient_index,
#                     "statistics": statistics,
#                     "total_features": len(features),
#                     "bounds": bounds
#                 }
#             }
#
#             return geojson
#
#         except Exception as e:
#             self.logger.error(f"生成GWR GeoJSON失败: {str(e)}")
#             raise













# import rasterio
#
#
# def check_raster_resolution(file_path):
#     """
#     检查栅格影像的空间分辨率并打印结果
#
#     参数:
#         file_path (str): 栅格影像文件路径
#
#     返回:
#         tuple: 包含x方向和y方向分辨率的元组
#     """
#     try:
#         # 打开栅格文件
#         with rasterio.open(file_path) as src:
#             # 获取分辨率（通常存储在transform中）
#             transform = src.transform
#             x_res = transform.a  # x方向分辨率（经度方向）
#             y_res = -transform.e  # y方向分辨率（纬度方向），取绝对值
#
#             # 打印结果
#             print(f"栅格影像文件: {file_path}")
#             print(f"X方向分辨率(经度方向): {x_res} 度/像素")
#             print(f"Y方向分辨率(纬度方向): {y_res} 度/像素")
#
#             # 如果影像使用投影坐标系（单位是米）
#             if src.crs and src.crs.is_projected:
#                 print(f"X方向分辨率: {x_res} 米/像素")
#                 print(f"Y方向分辨率: {y_res} 米/像素")
#
#             return (x_res, y_res)
#
#     except Exception as e:
#         print(f"无法读取文件 {file_path}: {str(e)}")
#         return None
#
#
# # 示例使用
# if __name__ == "__main__":
#     # 替换为你的栅格文件路径
#     raster_file = "D:/Google/rainfall/RF/2000.tif"
#     resolution = check_raster_resolution(raster_file)
#     raster_file2 = "D:/Google/temperture/tpt/tpt_2000.tif"
#     rl = check_raster_resolution(raster_file2)

#
# from osgeo import gdal
#
#
# def gdal_resample(input_path, output_path, target_resolution):
#     """
#     使用GDAL进行重采样
#
#     参数:
#         input_path (str): 输入栅格文件路径
#         output_path (str): 输出栅格文件路径
#         target_resolution (float): 目标分辨率(度/像素)
#     """
#     try:
#         # 设置GDAL选项
#         options = gdal.WarpOptions(
#             xRes=target_resolution,
#             yRes=target_resolution,
#             resampleAlg=gdal.GRA_Bilinear,  # 双线性插值
#             format='GTiff'
#         )
#
#         # 执行重采样
#         gdal.Warp(output_path, input_path, options=options)
#
#         print(f"重采样完成，结果已保存到: {output_path}")
#
#     except Exception as e:
#         print(f"处理过程中发生错误: {str(e)}")
#
# # 示例使用
# if __name__ == "__main__":
#     # 目标分辨率
#     target_res = 0.008333333333338086
#     i=2022
#     input_raster = "D:/Google/rainfall/Ave/{}_mean.tif".format(i)
#     output_raster = "D:/Google/rainfall/RF/{}.tif".format(i)
#     # 执行重采样
#     gdal_resample(input_raster, output_raster, target_res)


# from pyproj import datadir
# print(datadir.get_data_dir())
#
# import pyproj, rasterio
# print(pyproj.__version__)  # 应显示3.6.1
# print(rasterio.__version__)  # 应显示1.3.9

#
#
# from shutil import copytree
# from pyproj import datadir
# copytree(
#     datadir.get_data_dir(),
#     r"D:\Python312\Lib\site-packages\osgeo\data\proj",
#     dirs_exist_ok=True
# )
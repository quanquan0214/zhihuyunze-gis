# import os
# from shapely.geometry import box
# import rasterio
# from rasterio.mask import mask
# import numpy as np
#
# from ClimateData import ClimateDataService
# from GWRService import GWRService
#
# def clip_raster(data, profile, bounds):
#     """
#     根据边界裁剪栅格数据
#     """
#     geometry = [box(*bounds).__geo_interface__]
#     clipped, out_transform = mask(rasterio.io.MemoryFile().open(**profile, data=data), geometry, crop=True)
#     clipped = clipped[0]  # 去掉波段维度
#     out_profile = profile.copy()
#     out_profile.update({
#         'height': clipped.shape[0],
#         'width': clipped.shape[1],
#         'transform': out_transform
#     })
#     return clipped, out_profile
#
# def main():
#     # 初始化服务
#     climate_service = ClimateDataService()
#     gwr_service = GWRService(climate_service=climate_service, output_dir=r"D:/Google/gwr_results")
#
#     # 设置年份与测试范围（抚州市内的一个小矩形区域）
#     year = 2020
#     bbox = (116.25, 27.75, 116.35, 27.85)  # 抚州市内经纬度矩形
#
#     # 对齐栅格
#     # print("🔄 对齐栅格数据中...")
#     # gwr_service.align_rasters(reference_year=year)
#
#     # 获取并裁剪数据
#     print("✂️ 正在裁剪区域...")
#     clipped_data = {}
#     for name in ['rsei', 'temperature', 'rainfall', 'lucc']:
#         data, profile = getattr(climate_service, f"get_{name}_data")(year)
#         clipped, clipped_profile = clip_raster(data, profile, bbox)
#         clipped_data[name] = (clipped, clipped_profile)
#         # 用裁剪数据覆盖缓存（用于后续GWR分析）
#         getattr(climate_service, f"_{name}_cache")[year] = (clipped, clipped_profile)
#
#     # 运行GWR分析
#     print("⚙️ 正在运行GWR分析...")
#     results = gwr_service.run_gwr(year=year, include_lucc=True)
#
#     # 输出主要结果
#     print("✅ GWR完成。主要信息如下：")
#     print(f"带宽 (bandwidth): {results['bandwidth']}")
#     print(f"AICc: {results['aic']:.4f}")
#     print(f"局部系数数组形状: {results['local_coefficients'].shape}")
#     print(f"局部R²数组形状: {results['local_r2'].shape}")
#
#     # 保存结果
#     gwr_service.save_gwr_results(results, year=year)
#     print("📁 GWR结果已保存")
#
# if __name__ == "__main__":
#     main()

#
# import os
# import rasterio
# import matplotlib.pyplot as plt
# from ClimateData import ClimateDataService
#
#
# def validate_data_files(service):
#     """验证数据文件是否存在"""
#     print("\n=== 数据文件验证 ===")
#     validation = service.validate_data_files()
#
#     for data_type in ['temperature', 'rainfall', 'rsei', 'lucc']:
#         existing = len(validation[f'existing_{data_type}'])
#         missing = len(validation[f'missing_{data_type}'])
#         print(f"{data_type.upper()} - 存在: {existing}个, 缺失: {missing}个")
#
#     if any(missing > 0 for missing in
#            [len(validation[f'missing_{data_type}']) for data_type in ['temperature', 'rainfall', 'rsei', 'lucc']]):
#         print("\n警告: 存在缺失文件! 请检查路径或补充数据。")
#     else:
#         print("\n所有数据文件完整。")
#
#
# def show_raster_extent(service, year=2000):
#     """显示TIF文件的地理范围和图像"""
#     print("\n=== 数据空间范围可视化 ===")
#     try:
#         # 加载温度数据示例
#         temp_file = service._get_temperature_file_path(year)
#         with rasterio.open(temp_file) as src:
#             bounds = src.bounds
#             data = src.read(1)
#             transform = src.transform
#
#             # 显示图像
#             plt.figure(figsize=(10, 8))
#             plt.imshow(data, cmap='viridis', extent=[bounds.left, bounds.right, bounds.bottom, bounds.top])
#             plt.colorbar(label='Temperature (°C)')
#             plt.title(f"Temperature Data ({year})\nBounds: {bounds}")
#             plt.xlabel("Longitude")
#             plt.ylabel("Latitude")
#
#             # 标记中心点
#             center_lng = (bounds.left + bounds.right) / 2
#             center_lat = (bounds.bottom + bounds.top) / 2
#             plt.scatter(center_lng, center_lat, c='red', s=50, label='Center Point')
#             plt.legend()
#
#             plt.show()
#
#             print(f"地理范围 (min_lng, min_lat, max_lng, max_lat): {bounds}")
#             print(f"建议测试中心点: 经度={center_lng:.4f}, 纬度={center_lat:.4f}")
#
#             return bounds, center_lng, center_lat
#
#     except Exception as e:
#         print(f"无法显示TIF文件: {str(e)}")
#         return None, None, None
#
#
# def test_point_data(service, lat, lng, years=None):
#     """测试点数据提取"""
#     print("\n=== 点数据提取测试 ===")
#     if years is None:
#         years = [2000, 2005, 2010, 2015, 2020]  # 测试部分年份
#
#     for year in years:
#         try:
#             data = service.get_point_climate_data(lat, lng, year)
#             print(f"{year}年数据:")
#             print(f"  温度: {data['temperature']}°C")
#             print(f"  降水: {data['rainfall']}mm")
#             print(f"  RSEI: {data['rsei']}")
#             print(f"  LUCC: {data['lucc']}")
#         except Exception as e:
#             print(f"{year}年数据获取失败: {str(e)}")
#
#
# def test_statistics(service, year=2000):
#     """验证统计值"""
#     print("\n=== 数据统计验证 ===")
#     try:
#         stats = service.get_annual_statistics(year)
#         print(f"{year}年统计值:")
#         for key, values in stats.items():
#             if key != 'year':
#                 print(f"  {key.upper()}:")
#                 for stat, value in values.items():
#                     print(f"    {stat}: {value}")
#     except Exception as e:
#         print(f"统计值获取失败: {str(e)}")
#
#
# def test_time_series(service, data_type='temperature'):
#     """验证时间序列数据"""
#     print(f"\n=== {data_type.upper()}时间序列验证 ===")
#     series = service.get_time_series_data(data_type)
#     print(f"有效年份: {len(series['years'])}年 (2000-2022)")
#     print(f"示例数据:")
#     for year, value in zip(series['years'][:5], series['values'][:5]):
#         print(f"  {year}: {value}")
#     if len(series['years']) > 5:
#         print("  ...")
#
#
# def main():
#     # 初始化服务 (使用默认路径或自定义路径)
#     # service = ClimateDataService(
#     #     temperature_dir="YOUR_CUSTOM_PATH",
#     #     rainfall_dir="YOUR_CUSTOM_PATH",
#     #     rsei_dir="YOUR_CUSTOM_PATH",
#     #     lucc_dir="YOUR_CUSTOM_PATH"
#     # )
#     service = ClimateDataService()
#
#     # 1. 验证数据文件
#     validate_data_files(service)
#
#     # 2. 显示地理范围并获取测试点
#     bounds, center_lng, center_lat = show_raster_extent(service)
#     if bounds is None:
#         return
#
#     # 3. 测试点数据
#     test_point_data(service, center_lat, center_lng)
#
#     # 4. 验证统计值
#     test_statistics(service)
#
#     # 5. 验证时间序列
#     test_time_series(service, 'temperature')
#     test_time_series(service, 'rainfall')
#
#
# if __name__ == "__main__":
#     main()
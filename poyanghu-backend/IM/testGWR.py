# import numpy as np
# import rasterio
# from Climate import ClimateDataService
# from GWRService import GWRService

# # 创建 Mock 的 ClimateDataService 类
# class MockClimateDataService:
#     def __init__(self, width=10, height=10):
#         self.width = width
#         self.height = height
#         self.transform = rasterio.transform.from_origin(100.0, 30.0, 0.1, 0.1)  # 模拟地理坐标
#         self.profile = {
#             'transform': self.transform,
#             'crs': 'EPSG:4326',
#             'width': width,
#             'height': height,
#             'count': 1,
#             'dtype': 'float32'
#         }
#
#     def _gen_data(self, base=1.0, noise=0.1):
#         data = np.full((self.height, self.width), base, dtype='float32')
#         noise_matrix = np.random.normal(loc=0, scale=noise, size=(self.height, self.width))
#         data += noise_matrix
#         return np.clip(data, 0, 1)  # 保证值在0~1之间
#
#     def get_rsei_data(self, year):
#         return self._gen_data(0.5), self.profile
#
#     def get_temperature_data(self, year):
#         return self._gen_data(0.7), self.profile
#
#     def get_rainfall_data(self, year):
#         return self._gen_data(0.6), self.profile
#
#     def get_lucc_data(self, year):
#         lucc = np.random.randint(1, 6, size=(self.height, self.width))  # 模拟5类LUCC
#         return lucc.astype('float32'), self.profile
#
# # 测试
# if __name__ == '__main__':
#     climate_service = ClimateDataService()
#     gwr_service = GWRService(climate_service, output_dir="./mock_results")
#
#     year = 2020
#
#     # 提取输入数据
#     coords, y, X = gwr_service.get_gwr_input_data(year)
#     print("输入数据提取成功:")
#     print("坐标:", coords.shape)
#     print("因变量 (RSEI):", y.shape)
#     print("自变量 (温度、降水、LUCC):", X.shape)
#
#     # 计算 VIF
#     vif_result = gwr_service.calculate_vif(year)
#     print("\nVIF 计算结果:")
#     for key, val in vif_result.items():
#         print(f"{key}: {val:.4f}")
#
#     # 运行 GWR 分析
#     gwr_result = gwr_service.run_gwr(year)
#     print("\nGWR 分析完成:")
#     print("AIC:", gwr_result['aic'])
#     print("带宽:", gwr_result['bandwidth'])
#     print("局部系数形状:", gwr_result['local_coefficients'].shape)
#
#     # 保存结果（可选）
#     gwr_service.save_gwr_results(gwr_result, year)



# import numpy as np
# from Climate import ClimateDataService
# from GWRService import GWRService
#
# if __name__ == '__main__':
#     # 实例化真实的 ClimateDataService
#     real_service = ClimateDataService()
#     gwr_service = GWRService(real_service, output_dir="D:/Google/gwr_results")
#
#     year = 2020
#
#     # 提取输入数据
#     coords, y, X = gwr_service.get_gwr_input_data(year)
#     print("输入数据提取成功:")
#     print("坐标:", coords.shape)
#     print("因变量 (RSEI):", y.shape)
#     print("自变量 (温度、降水、LUCC):", X.shape)
#
#     # 计算 VIF
#     vif_result = gwr_service.calculate_vif(year)
#     print("\nVIF 计算结果:")
#     for key, val in vif_result.items():
#         print(f"{key}: {val:.4f}")
#
#     # 运行 GWR 分析
#     gwr_result = gwr_service.run_gwr(year)
#     print("\nGWR 分析完成:")
#     print("AIC:", gwr_result['aic'])
#     print("带宽:", gwr_result['bandwidth'])
#     print("局部系数形状:", gwr_result['local_coefficients'].shape)
#
#     # 保存结果（可选）
#     gwr_service.save_gwr_results(gwr_result, year)
#


from Climate import ClimateDataService
from GWR import GWRService
# Initialize ClimateDataService
climate_service = ClimateDataService(
    temperature_dir="D:/Google/temperture/tpt",
    rainfall_dir="D:/Google/rainfall/RF",
    rsei_dir="D:/Google/RSEI_full",
    lucc_dir="D:/Google/GLC_FCS30/merged"
)

# Initialize GWRService
gwr_service = GWRService(climate_service)

# Run GWR for a specific year
results = gwr_service.run_gwr(year=2020, sample_size=1000, random_state=42)

# Summarize results
summary = gwr_service.summarize_gwr_results(results)
print("Feature Names:", summary['feature_names'])
print("Mean Coefficients:", summary['mean_coefficients'])
print("Mean R-squared:", summary['mean_r_squared'])
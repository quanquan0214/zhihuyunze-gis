import os
from IM.Flexible_GWR import FlexibleRasterProcessor

# 定义测试用的 variables 和 config
variables = ['temp','rain','lucc']

config = {
    "temp_dir": "D:/Google/GWR",
    "target_res": (0.00449, 0.00449),  # 分辨率
    "target_bounds": (113.9, 26.5, 118.5, 30.1),  # 范围
    "target_shape": (796, 1010),  # 栅格形状
    "safe_nodata": 0,  # 无效值
    "resampling_method": "Resampling.nearest",  # 重采样方法,
    "standardize": True  # 是否标准化
}

# 确保路径存在
os.makedirs(config["temp_dir"], exist_ok=True)

# 初始化 FlexibleRasterProcessor 类
processor = FlexibleRasterProcessor(
    year=2020,
    region_shp="NC",
    variables=variables,
    config=config
)

# 调用 run 方法进行测试
output_csv = processor.run()
print(f"生成的 CSV 文件路径: {output_csv}")

# def __init__(self, year, region_shp, variables, config): # variables参数为字典, config参数包含所有配置选项
#     self.year = year
#     self.region_shp = region_shp
#     self.variables = variables
#     self.config = config
#
#     self.temp_dir = config.get("temp_dir", "D:/Google/GWR")
#     self.target_res = config.get("target_res", (0.00449, 0.00449)) # 默认分辨率。500m
#     self.target_bounds = config.get("target_bounds", (113.9, 26.5, 118.5, 30.1))    # 默认范围
#     self.target_shape = config.get("target_shape", (796, 1010)) # 默认形状
#     self.safe_nodata = config.get("safe_nodata", 0) # 默认安全的无效值为0
#     self.resampling_method = config.get("resampling_method", Resampling.bilinear)  # 默认双线性插值进行重采样
#     self.standardize = config.get("standardize", True)  # 是否标准化连续变量
#     self.output_dir = os.path.join(self.temp_dir, time.strftime("%Y-%m-%d"))    # 输出目录，按日期创建
#     os.makedirs(self.output_dir, exist_ok=True)  # 创建输出目录

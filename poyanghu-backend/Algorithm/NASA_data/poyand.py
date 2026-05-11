from pyproj import Transformer

# 定义BJ-54和WGS84的转换参数（示例参数，需根据实际区域调整）
transformer = Transformer.from_crs("EPSG:2414", "EPSG:4326")  # EPSG:2414为BJ-54，4326为WGS84

# 输入BJ-54坐标（东经116°11′，北纬29°16′）
lon_bj54, lat_bj54 = 116 + 11/60, 29 + 16/60  # 将度分秒转换为十进制

# 转换为WGS84
lon_wgs84, lat_wgs84 = transformer.transform(lon_bj54, lat_bj54)
print(f"WGS84坐标: {lon_wgs84}, {lat_wgs84}")

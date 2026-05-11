# 检查数据精度和参考
import rasterio

# 文件路径列表
file_paths = [
    "D:/Google/temperture/tpt/tpt_2000.tif",
    "D:/Google/rainfall/RF/2000.tif",
    "D:/Google/RSEI_full/RSEI_2000.tif",
    "D:/Google/GLC_FCS30/merged/poyang_2000.tif"
]

# 遍历文件并提取信息
for path in file_paths:
    try:
        with rasterio.open(path) as src:
            print(f"\n文件: {path}")
            print(f"1. 参考系 (CRS): {src.crs}")
            print(f"2. 分辨率 (Resolution): {src.res} (单位: CRS定义的坐标单位)")
            print(f"3. 栅格数目: 波段数 = {src.count}, 宽度 = {src.width}, 高度 = {src.height}")
            print(f"4. 空间范围 (Bounds): {src.bounds}")
    except Exception as e:
        print(f"读取文件 {path} 失败: {str(e)}")





# import rasterio
#
# # 文件路径列表
# file_paths = [
#     "D:/Google/GWR/tpt_2000_resampled.tif",
#     "D:/Google/GWR/2000_resampled.tif",
#     "D:/Google/GWR/RSEI_2000_resampled.tif",
#     "D:/Google/GWR/poyang_2000_resampled.tif"
# ]
#
# # 遍历文件并提取信息
# for path in file_paths:
#     try:
#         with rasterio.open(path) as src:
#             print(f"\n文件: {path}")
#             # print(f"1. 参考系 (CRS): {src.crs}")
#             # print(f"2. 分辨率 (Resolution): {src.res} (单位: CRS定义的坐标单位)")
#             # print(f"3. 栅格数目: 波段数 = {src.count}, 宽度 = {src.width}, 高度 = {src.height}")
#             # print(f"4. 空间范围 (Bounds): {src.bounds}")
#
#             # 输出每个波段的属性值范围
#             for i in range(1, src.count + 1):
#                 band = src.read(i)
#                 min_val = band.min()
#                 max_val = band.max()
#                 print(f"5. 波段 {i} 属性值范围: 最小值 = {min_val}, 最大值 = {max_val}")
#
#     except Exception as e:
#         print(f"读取文件 {path} 失败: {str(e)}")
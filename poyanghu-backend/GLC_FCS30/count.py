import os
import rasterio
import pandas as pd
from collections import Counter
import numpy as np

# 定义输入和输出路径
input_dir = r"D:/Google/GLC_FCS30/merged/"
output_csv = r"D:/Google/GLC_FCS30/merged/鄱阳湖土地覆盖统计_20250526.csv"

# 创建一个空的列表来存储所有文件的统计结果
all_results = []

# 获取所有匹配的文件
tif_files = [f for f in os.listdir(input_dir) if f.startswith("poyang_") and f.endswith(".tif")]

# 遍历每个TIF文件进行统计
for tif_file in tif_files:
    file_path = os.path.join(input_dir, tif_file)

    try:
        # 打开栅格文件
        with rasterio.open(file_path) as src:
            # 读取栅格数据
            data = src.read(1)  # 读取第一个波段（单波段影像）

            # 计算总栅格数
            total_pixels = data.size

            # 统计每个属性值的数量（忽略NaN值）
            valid_data = data[~np.isnan(data)]
            value_counts = Counter(valid_data)

            # 将统计结果转换为DataFrame
            for value, count in value_counts.items():
                all_results.append({
                    '文件名': tif_file,
                    '属性值': value,
                    '栅格数量': count,
                    '总栅格数': total_pixels,
                    '百分比(%)': (count / total_pixels) * 100
                })

            print(f"已处理: {tif_file}, 总栅格数: {total_pixels}")

    except Exception as e:
        print(f"处理文件 {tif_file} 时出错: {str(e)}")

# 将所有结果转换为DataFrame并保存为CSV
if all_results:
    results_df = pd.DataFrame(all_results)

    # 按照文件名和属性值排序
    results_df = results_df.sort_values(by=['文件名', '属性值'])

    # 保存结果到CSV文件
    results_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"统计结果已保存至: {output_csv}")
else:
    print("没有找到符合条件的栅格数据或处理过程中出现错误。")

# import numpy as np
# import rasterio
# from collections import Counter
#
# def count_pixel_values(raster_path):
#     """统计栅格图像中每个像素值的出现次数
#
#     参数:
#     raster_path (str): 栅格图像文件路径
#     返回:
#     dict: 像素值及其对应的频数，格式为 {像素值: 频数}
#     """
#     # 读取栅格数据
#     with rasterio.open(raster_path) as src:
#         # 读取第一个波段的数据
#         band = src.read(1)
#         # 获取无效值（如果有）
#         nodata = src.nodata
#     # 将无效值替换为NaN（如果存在）
#     if nodata is not None:
#         band = band.astype(np.float32)  # 转换为浮点数以便处理NaN
#         band[band == nodata] = np.nan
#     # 过滤掉NaN值并统计像素值
#     valid_pixels = band[~np.isnan(band)]
#     pixel_counts = Counter(valid_pixels.astype(int))
#     return dict(pixel_counts)
#
# # 使用示例
# if __name__ == "__main__":
#     raster_path = "D:/Google/GLC_FCS30/merged/poyang_2000.tif"  # 替换为实际栅格路径
#     counts = count_pixel_values(raster_path)
#
#     # 打印出现次数最多的前10个像素值
#     print("像素值统计结果（前10个最频繁的值）:")
#     for value, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]:
#         print(f"像素值: {value}, 频数: {count}")
#
#     # 保存结果到CSV文件
#     import csv
#
#     with open("D:/Google/GLC_FCS30/merged/2000_pixel_counts.csv", "w", newline="") as f:
#         writer = csv.writer(f)
#         writer.writerow(["像素值", "频数"])
#         for value, count in sorted(counts.items()):
#             writer.writerow([value, count])
# import os
# import numpy as np
# import rasterio
# import csv
# from tqdm import tqdm  # 用于显示进度条，可选
#
#
# def calculate_yearly_precipitation(input_folder, output_csv):
#     """
#     计算文件夹中每年TIFF文件的平均降水量并保存到CSV
#
#     参数:
#         input_folder: 包含TIFF文件的文件夹路径
#         output_csv: 输出CSV文件路径
#     """
#     # 准备存储结果的列表
#     results = []
#
#     # 遍历2000年到2022年
#     for year in tqdm(range(2000, 2023)):
#         filename = f"{year}.tif"
#         filepath = os.path.join(input_folder, filename)
#
#         # 检查文件是否存在
#         if not os.path.exists(filepath):
#             print(f"警告: 文件 {filename} 不存在，跳过")
#             continue
#
#         try:
#             # 打开TIFF文件
#             with rasterio.open(filepath) as src:
#                 # 读取第一个波段的数据
#                 data = src.read(1)
#
#                 # 计算有效数据的平均值（忽略NaN值）
#                 mean_value = np.nanmean(data)
#
#                 # 添加到结果列表
#                 results.append({
#                     '年份': year,
#                     '年降水量(mm)': round(mean_value, 2)  # 保留两位小数
#                 })
#         except Exception as e:
#             print(f"处理文件 {filename} 时出错: {str(e)}")
#             continue
#
#     # 将结果写入CSV文件
#     with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
#         fieldnames = ['年份', '年降水量(mm)']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#
#         writer.writeheader()
#         for row in results:
#             writer.writerow(row)
#
#     print(f"处理完成，结果已保存到 {output_csv}")
#
#
# # 使用示例
# input_folder = r"D:\Google\rainfall\RF"  # 替换为你的TIFF文件所在文件夹
# output_csv = "yearly_precipitation.csv"  # 输出CSV文件名
#
# calculate_yearly_precipitation(input_folder, output_csv)
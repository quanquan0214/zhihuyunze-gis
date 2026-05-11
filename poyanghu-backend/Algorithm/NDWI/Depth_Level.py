import pandas as pd

# 输入和输出文件路径
input_file = r"D:\Google\Table\深度分级统计结果.csv"
output_file = r"D:\Google\Table\Depth_Level.csv"

# 以 GBK 编码读取 CSV 文件
df = pd.read_csv(input_file, encoding='GBK')

# 删除`水深`列名称中的.tif
df['水深'] = df['水深'].str.replace('.tif', '')

# 将等级列中的数值保留两位小数
level_columns = ['极浅水', '浅水', '平水', '深水', '极深水']
for col in level_columns:
    df[col] = df[col].round(2)

# 保存修改后的文件
df.to_csv(output_file, index=False)






# import os
# import re
# import numpy as np
# import pandas as pd
# import rasterio
# from rasterio.plot import show
# import matplotlib.pyplot as plt
# from matplotlib.colors import LinearSegmentedColormap
#
# # 设置中文显示
# plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
#
# # 定义深度分级
# depth_bins = [0, 6, 12, 18, 24, 30]
# depth_labels = ["极浅水", "浅水", "平水", "深水", "极深水"]
#
# # 输入和输出路径
# input_dir = r"D:/Google/H5/Depth_mask"
# output_csv = r"D:/Google/H5/Depth_mask/深度分级统计结果.csv"
# output_plot_dir = r"D:/Google/H5/Depth_mask/分级统计图"
#
# # 创建输出图表目录
# os.makedirs(output_plot_dir, exist_ok=True)
#
# # 定义颜色映射
# colors = ['#FFFFCC', '#A1DAB4', '#41B6C4', '#2C7FB8', '#253494']
# cmap = LinearSegmentedColormap.from_list('depth_cmap', colors, N=len(depth_labels))
#
# # 初始化结果列表
# results = []
#
# # 获取所有栅格文件
# raster_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.tif', '.tiff'))]
#
# # 处理每个栅格文件
# for raster_file in raster_files:
#     file_path = os.path.join(input_dir, raster_file)
#
#     try:
#         # 读取栅格数据
#         with rasterio.open(file_path) as src:
#             depth_data = src.read(1)  # 读取第一个波段
#             nodata = src.nodata  # 获取nodata值
#
#         # 替换nodata值为NaN
#         if nodata is not None:
#             depth_data = depth_data.astype(float)
#             depth_data[depth_data == nodata] = np.nan
#
#         # 去除NaN值
#         valid_data = depth_data[~np.isnan(depth_data)]
#
#         # 计算分级统计
#         hist, _ = np.histogram(valid_data, bins=depth_bins)
#
#         # 计算占比
#         total_valid = valid_data.size
#         percentages = hist / total_valid * 100
#
#         # 获取日期信息
#         date_match = re.search(r'\d{8}|\d{6}', raster_file)
#         date_str = date_match.group(0) if date_match else raster_file
#
#         # 构建结果行
#         result_row = {'日期': date_str}
#         for label, percent in zip(depth_labels, percentages):
#             result_row[label] = percent
#
#         results.append(result_row)
#
#         # 可视化并保存图像
#         plt.figure(figsize=(10, 8))
#
#         # 绘制分级直方图
#         plt.subplot(2, 1, 1)
#         bars = plt.bar(depth_labels, percentages, color=colors)
#         plt.title(f'{date_str} 深度分级占比')
#         plt.xlabel('深度等级')
#         plt.ylabel('占比 (%)')
#
#         # 添加数值标签
#         for bar in bars:
#             height = bar.get_height()
#             plt.text(bar.get_x() + bar.get_width() / 2., height,
#                      f'{height:.2f}%',
#                      ha='center', va='bottom')
#
#         # 绘制栅格图像
#         plt.subplot(2, 1, 2)
#         # 将数据分级用于显示
#         depth_classified = np.digitize(depth_data, depth_bins)
#         depth_classified[np.isnan(depth_data)] = 0  # 将NaN设置为0级
#
#         # 显示分级后的栅格图像
#         im = plt.imshow(depth_classified, cmap=cmap, vmin=0, vmax=len(depth_labels))
#         plt.title(f'{date_str} 深度分级可视化')
#
#         # 添加颜色条
#         cbar = plt.colorbar(im, ticks=range(len(depth_labels) + 1))
#         cbar.set_ticklabels(['无数据'] + depth_labels)
#
#         plt.tight_layout()
#         plt.savefig(os.path.join(output_plot_dir, f'{date_str}_分级统计.png'), dpi=300)
#         plt.close()
#
#         print(f"已处理: {raster_file}")
#
#     except Exception as e:
#         print(f"处理文件 {raster_file} 时出错: {str(e)}")
#
# # 转换为DataFrame并保存为CSV
# if results:
#     df = pd.DataFrame(results)
#     # 按日期排序
#     date_columns = pd.to_datetime(df['日期'], errors='coerce')
#     if not date_columns.isnull().all.py():
#         df['日期排序'] = date_columns
#         df = df.sort_values('日期排序').drop('日期排序', axis=1)
#
#     df.to_csv(output_csv, index=False, encoding='utf-8-sig')
#     print(f"统计结果已保存至: {output_csv}")
# else:
#     print("未处理任何文件或处理过程中出现错误。")
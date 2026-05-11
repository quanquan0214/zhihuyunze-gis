import os
import numpy as np
import pandas as pd
from osgeo import gdal

# 设置输入路径
input_path = r'D:\Google\RSEI_2000_2022'
# 获取所有RSEI栅格影像文件
rsei_files = [f for f in os.listdir(input_path) if f.startswith('Wet') and f.endswith(('.tif', '.img'))]
# 定义等级分类区间和名称
class_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
class_names = ['一级', '二级', '三级', '四级', '五级']
# 创建结果数据框
results = []
# 遍历每个RSEI影像进行处理
for rsei_file in rsei_files:
    file_path = os.path.join(input_path, rsei_file)
    # 打开栅格影像
    ds = gdal.Open(file_path)
    if ds is None:
        print(f"无法打开文件: {file_path}")
        continue
    # 读取栅格数据
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    # 计算每个等级的像素数量
    hist, _ = np.histogram(data, bins=class_bins)
    # 计算总像素数（排除无效值）
    valid_pixels = np.sum(np.isfinite(data))
    # 计算各级占比（百分比）
    class_percentages = [f"{(count / valid_pixels) * 100:.2f}%" for count in hist]
    # 记录结果
    year = rsei_file.split('_')[1].split('.')[0]
    for i, class_name in enumerate(class_names):
        results.append({
            '名称': f'Wet_{year}',
            '等级': class_name,
            '占比': class_percentages[i]
        })
    # 关闭数据集
    ds = None

# 将结果转换为数据框
result_df = pd.DataFrame(results)
# 转换为"名称|等级"的表格形式
pivot_df = result_df.pivot(index='名称', columns='等级', values='占比')
# 保存结果为CSV文件
csv_output_path = r'D:\Google\Table\Wet_Classification.csv'
pivot_df.to_csv(csv_output_path)
print(f"结果已保存至: {csv_output_path}")



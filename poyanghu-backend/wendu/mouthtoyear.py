import os
import rasterio
import numpy as np
from tqdm import tqdm

# 输入和输出文件夹路径
input_folder = "D:/Google/temperture/data/"
output_folder = "D:/Google/temperture/tpt/"

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

# 处理的年份范围
start_year = 2000
end_year = 2023
years = list(range(start_year, end_year + 1))

# 遍历每一年
for year in years:
    print(f"\n正在处理 {year} 年的数据...")

    # 生成该年要处理的文件列表
    months = [f"{i:02d}" for i in range(1, 13)]
    input_files = [os.path.join(input_folder, f"{year}{month}.tif") for month in months]

    # 检查所有文件是否存在
    missing_files = [f for f in input_files if not os.path.exists(f)]
    if missing_files:
        print(f"警告: {year} 年缺少以下文件: {missing_files}")
        print(f"跳过 {year} 年的处理")
        continue

    # 读取第一个文件以获取元数据
    with rasterio.open(input_files[0]) as src:
        meta = src.meta
        first_band = src.read(1)
        # 创建一个与第一个波段相同形状的累加器
        sum_array = np.zeros_like(first_band, dtype=np.float64)

    # 累加所有月份的数据
    print(f"正在读取并累加 {year} 年的月度温度数据...")
    for file_path in tqdm(input_files):
        with rasterio.open(file_path) as src:
            band = src.read(1).astype(np.float64)  # 转换为浮点数进行计算
            sum_array += band

    # 计算平均值（注意处理可能的零值除数）
    count = len(input_files)
    average_array = np.divide(sum_array, count, out=np.zeros_like(sum_array), where=count != 0)

    # 将结果转换回原始数据类型
    if meta['dtype'] != 'float64':
        # 如果原始数据类型不是浮点数，需要进行四舍五入
        if np.issubdtype(meta['dtype'], np.integer):
            average_array = np.round(average_array).astype(meta['dtype'])
        else:
            average_array = average_array.astype(meta['dtype'])

    # 保存结果
    output_path = os.path.join(output_folder, f"tpt_{year}.tif")
    print(f"正在保存 {year} 年的结果到: {output_path}")
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(average_array, 1)

print("\n所有年份处理完成!")
import os
import rasterio
import numpy as np

# 输入和输出路径
input_dir = r'D:\Google\rainfall'
output_dir = r'D:\Google\rainfall\Ave'
os.makedirs(output_dir, exist_ok=True)

# 处理2000年到2022年
for year in range(2000, 2023):
    filename = f"{year}_precip.tif"
    input_path = os.path.join(input_dir, filename)

    # 读取影像
    with rasterio.open(input_path) as src:
        # 获取所有月份（12个波段）
        all_bands = src.read()  # shape: (12, height, width)

        # 计算12个月的平均值，忽略无效值
        annual_mean = np.nanmean(all_bands, axis=0)

        # 设置输出路径
        output_path = os.path.join(output_dir, f"{year}_mean.tif")

        # 使用原图的元数据来写入新文件
        out_meta = src.meta.copy()
        out_meta.update({
            "count": 1,  # 单波段
            "dtype": 'float32'  # 结果为浮点型
        })

        # 写入结果
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(annual_mean.astype('float32'), 1)

    print(f"{year}年平均降水已保存到: {output_path}")

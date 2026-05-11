import numpy as np
import rasterio
import os
from pathlib import Path

def filter_raster_by_valid_classes(input_path, output_path, valid_classes):
    """
    将栅格数据中不在有效类别列表中的像素值设置为NaN
    参数:
    input_path (str): 输入栅格文件路径
    output_path (str): 输出栅格文件路径
    valid_classes (list): 有效类别像素值列表
    """
    # 读取原始栅格数据
    with rasterio.open(input_path) as src:
        profile = src.profile
        band = src.read(1)
        # 保存原始nodata值
        original_nodata = profile.get('nodata')
        # 创建掩码：无效像素(True)，有效像素(False)
        invalid_mask = np.ones_like(band, dtype=bool)
        # 将有效类别对应的位置设为False
        for value in valid_classes:
            invalid_mask[band == value] = False
        # 将无效像素设为NaN
        band = band.astype(np.float32)  # 转换为浮点数以支持NaN
        band[invalid_mask] = np.nan
        # 更新输出栅格的元数据
        profile.update(
            dtype=np.float32,
            nodata=np.nan
        )
        # 写入处理后的栅格
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(band, 1)
    print(f"处理完成，输出文件: {output_path}")

# 参考文档中定义的有效类别列表（根据文档表格整理）
valid_classes = [
    10, 20, 30, 40, 50, 60, 61, 62, 70, 71, 72,
    80, 81, 82, 90, 100, 110, 120, 121, 122, 130,
    140, 150, 151, 152, 153, 160, 170, 180, 190,
    200, 201, 202, 210, 220
]
# 主函数
def main():
    # 输入栅格路径（修改为你的栅格路径）
    input_raster = "D:/Google/GLC_FCS30/merged/poyang_2000.tif"
    # 确保输入文件存在
    if not os.path.exists(input_raster):
        print(f"错误：文件 '{input_raster}' 不存在")
        return
    # 构建输出路径（在原文件名后加'_class'）
    input_dir = os.path.dirname(input_raster)
    file_name, ext = os.path.splitext(os.path.basename(input_raster))
    output_raster = os.path.join(input_dir, f"{file_name}_class{ext}")
    # 执行栅格处理
    filter_raster_by_valid_classes(input_raster, output_raster, valid_classes)

if __name__ == "__main__":
    main()
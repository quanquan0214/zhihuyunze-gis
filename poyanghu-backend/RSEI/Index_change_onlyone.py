import os
import numpy as np
import rasterio
import pandas as pd
from rasterio.transform import Affine


def raster_change_analysis(before_path, after_path, output_csv):
    """
    对两个单波段栅格影像进行分级和叠置分析，统计等级变化情况的占比。

    参数:
    before_path (str): 变化前的栅格影像路径
    after_path (str): 变化后的栅格影像路径
    output_csv (str): 输出CSV文件路径

    返回:
    dict: 包含三种变化类型占比的字典
    """
    # 读取栅格数据
    with rasterio.open(before_path) as src_before:
        before_data = src_before.read(1)
        profile = src_before.profile

    with rasterio.open(after_path) as src_after:
        after_data = src_after.read(1)

    # 检查两个栅格的尺寸是否一致
    if before_data.shape != after_data.shape:
        raise ValueError("两个栅格影像的尺寸不一致")

    # 定义分级阈值
    thresholds = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    classes = [1, 2, 3, 4, 5]

    # 对栅格数据进行分级
    def classify_raster(data):
        # 创建分类结果数组，初始化为0（代表未分类）
        classified = np.zeros_like(data, dtype=np.int8)
        # 标记有效数据区域（非NaN且在阈值范围内）
        valid_mask = ~np.isnan(data) & (data >= thresholds[0]) & (data <= thresholds[-1])

        # 对有效数据区域进行分级
        for i in range(len(classes)):
            mask = valid_mask & (data > thresholds[i]) & (data <= thresholds[i + 1])
            classified[mask] = classes[i]

        return classified, valid_mask

    # 执行分级并获取有效数据掩码
    before_classified, before_valid = classify_raster(before_data)
    after_classified, after_valid = classify_raster(after_data)

    # 打印before影像各等级占比
    print("\nBefore影像各等级占比:")
    total_pixels_before = np.count_nonzero(before_valid)
    class_counts_before = {}
    for c in classes:
        class_pixels = np.count_nonzero(before_classified == c)
        class_counts_before[c] = class_pixels

    # 确保占比总和为100%，最后一个等级使用差值计算
    sum_percent_before = 0
    for i, c in enumerate(classes[:-1]):
        percent = round((class_counts_before[c] / total_pixels_before) * 100, 2)
        sum_percent_before += percent
        print(f"等级{c}: {percent}%")

    # 最后一个等级使用差值计算，确保总和为100%
    last_class = classes[-1]
    last_percent = round(100 - sum_percent_before, 2)
    print(f"等级{last_class}: {last_percent}%")

    # 打印after影像各等级占比
    print("\nAfter影像各等级占比:")
    total_pixels_after = np.count_nonzero(after_valid)
    class_counts_after = {}
    for c in classes:
        class_pixels = np.count_nonzero(after_classified == c)
        class_counts_after[c] = class_pixels

    # 确保占比总和为100%，最后一个等级使用差值计算
    sum_percent_after = 0
    for i, c in enumerate(classes[:-1]):
        percent = round((class_counts_after[c] / total_pixels_after) * 100, 2)
        sum_percent_after += percent
        print(f"等级{c}: {percent}%")

    # 最后一个等级使用差值计算，确保总和为100%
    last_percent = round(100 - sum_percent_after, 2)
    print(f"等级{last_class}: {last_percent}%")

    # 进行叠置分析（只分析两个影像都有效的像素）
    valid_mask = before_valid & after_valid
    change = np.zeros_like(before_classified)
    change[valid_mask] = after_classified[valid_mask] - before_classified[valid_mask]

    # 统计变化情况
    total_pixels = np.count_nonzero(valid_mask)
    increase = np.count_nonzero((change > 0) & valid_mask)
    decrease = np.count_nonzero((change < 0) & valid_mask)
    no_change = np.count_nonzero((change == 0) & valid_mask)

    # 计算占比并保留两位小数
    increase_percent = round((increase / total_pixels) * 100, 2)
    decrease_percent = round((decrease / total_pixels) * 100, 2)
    no_change_percent = round((no_change / total_pixels) * 100, 2)

    # 保存结果到CSV
    results = {
        '变化类型': ['增长', '降低', '不变'],
        '像素数量': [increase, decrease, no_change],
        '占比(%)': [increase_percent, decrease_percent, no_change_percent]
    }

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)

    # 同时返回结果字典
    return {
        '增长占比(%)': increase_percent,
        '降低占比(%)': decrease_percent,
        '不变占比(%)': no_change_percent
    }


# 使用示例
if __name__ == "__main__":
    before_raster = "D:/Google/RSEI_2000_2022/RSEI_2010.tif"
    after_raster = "D:/Google/RSEI_2000_2022/RSEI_2011.tif"
    output_file = "D:/Google/RSEI_2000_2022/change1.csv"

    results = raster_change_analysis(before_raster, after_raster, output_file)
    print("\n分析完成，结果已保存到:", output_file)
    print(results)
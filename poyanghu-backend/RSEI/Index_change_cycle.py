import os
import numpy as np
import rasterio
import pandas as pd


def raster_change_analysis(before_path, after_path):
    """
    对两个单波段栅格影像进行分级和叠置分析，统计等级变化情况的占比。

    参数:
    before_path (str): 变化前的栅格影像路径
    after_path (str): 变化后的栅格影像路径

    返回:
    dict: 包含三种变化类型占比的字典
    """
    # 读取栅格数据
    with rasterio.open(before_path) as src_before:
        before_data = src_before.read(1)

    with rasterio.open(after_path) as src_after:
        after_data = src_after.read(1)

    # 检查两个栅格的尺寸是否一致
    if before_data.shape != after_data.shape:
        raise ValueError("两个栅格影像的尺寸不一致")

    # 定义分级阈值
    thresholds = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    classes = [1, 2, 3, 4, 5]  # 对应五个等级

    # 对栅格数据进行分级
    def classify_raster(data):
        classified = np.zeros_like(data, dtype=np.int8)
        for i in range(len(classes)):
            mask = (data > thresholds[i]) & (data <= thresholds[i + 1])
            classified[mask] = classes[i]
        return classified

    # 执行分级
    before_classified = classify_raster(before_data)
    after_classified = classify_raster(after_data)

    # 计算等级变化
    change = after_classified - before_classified

    # 统计变化情况（排除无效值，如NoData区域）
    valid_mask = (before_classified > 0) & (after_classified > 0)
    valid_pixels = np.count_nonzero(valid_mask)

    if valid_pixels == 0:
        raise ValueError("没有有效的像素用于分析")

    # 正确统计等级变化
    increase = np.count_nonzero((change > 0) & valid_mask)  # 等级增加
    decrease = np.count_nonzero((change < 0) & valid_mask)  # 等级降低
    no_change = np.count_nonzero((change == 0) & valid_mask)  # 等级不变

    # 计算占比并保留两位小数
    increase_percent = round((increase / valid_pixels) * 100, 2)
    decrease_percent = round((decrease / valid_pixels) * 100, 2)
    no_change_percent = round((no_change / valid_pixels) * 100, 2)

    # 返回结果字典
    return {
        '增长占比(%)': increase_percent,
        '降低占比(%)': decrease_percent,
        '不变占比(%)': no_change_percent
    }


# 使用示例
if __name__ == "__main__":
    input_path = 'D:/Google/RSEI_2000_2022'
    output_csv = "D:/Google/Table/NDVI_Change.csv"

    # 获取并排序栅格文件
    rsei_files = [f for f in os.listdir(input_path) if f.startswith('NDVI') and f.endswith(('.tif', '.img'))]
    rsei_files.sort()  # 确保按年份排序

    print(f"找到 {len(rsei_files)} 个栅格文件，开始逐年变化分析...")

    # 存储所有年份的分析结果
    all_results = []

    for i in range(len(rsei_files) - 1):
        before_file = rsei_files[i]
        after_file = rsei_files[i + 1]

        # 提取年份
        before_year = before_file.split('_')[1].split('.')[0]
        after_year = after_file.split('_')[1].split('.')[0]

        before_path = os.path.join(input_path, before_file)
        after_path = os.path.join(input_path, after_file)

        try:
            # 执行分析
            result = raster_change_analysis(before_path, after_path)

            # 记录结果
            result['起始年份'] = before_year
            result['结束年份'] = after_year
            all_results.append(result)

        except Exception as e:
            print(f"处理 {before_year} 到 {after_year} 时出错: {str(e)}")
            continue

    # 保存汇总结果
    if all_results:
        summary_df = pd.DataFrame(all_results)
        # 调整列顺序
        summary_df = summary_df[['起始年份', '结束年份', '增长占比(%)', '降低占比(%)', '不变占比(%)']]
        summary_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\n分析完成，汇总结果已保存到: {output_csv}")
        print(f"共分析了 {len(all_results)} 个年份变化")
    else:
        print("未生成有效结果，请检查输入数据")
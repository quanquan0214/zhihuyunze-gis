import os
import pandas as pd
from osgeo import gdal


def calculate_raster_mean(input_folder, output_table):
    """
    计算文件夹中所有单波段栅格影像的均值，并保存结果到表格
    参数:
    input_folder (str): 包含栅格影像的文件夹路径
    output_table (str): 输出表格的路径（支持.csv或.xlsx格式）
    返回:
    pandas.DataFrame: 包含影像名称和均值的DataFrame
    """
    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"输入文件夹不存在: {input_folder}")
    # 初始化结果列表
    results = []
    # 遍历文件夹中的所有文件
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        # 检查文件是否为栅格影像（简单检查扩展名）
        if not os.path.isfile(file_path):
            continue
        # 尝试打开栅格文件
        try:
            ds = gdal.Open(file_path)
            if ds is None:
                continue  # 不是有效栅格文件
            # 获取第一个波段
            band = ds.GetRasterBand(1)
            if band is None:
                continue  # 没有有效波段
            # 计算均值
            stats = band.GetStatistics(True, True)
            mean = stats[2]  # 均值在统计结果中的索引为2
            # 记录结果
            results.append({
                '影像名称': filename,
                '均值': mean
            })
            # 释放资源
            band = None
            ds = None
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {str(e)}")
            continue
    # 创建DataFrame
    df = pd.DataFrame(results)
    # 保存结果到表格
    if not results:
        print("警告: 未找到有效栅格影像")
        return df
    # 根据文件扩展名选择保存方法
    if output_table.lower().endswith('.csv'):
        df.to_csv(output_table, index=False, encoding='utf-8-sig')
    elif output_table.lower().endswith(('.xlsx', '.xls')):
        df.to_excel(output_table, index=False)
    else:
        print(f"警告: 不支持的输出格式，结果未保存到文件。支持的格式: .csv, .xlsx")
    return df

# 设置输入文件夹和输出表格路径
input_folder = "D:/Google/Table"  # 替换为实际文件夹路径
output_table = "D:/Google/Table/RESI_Statistics2.csv"  # 替换为实际输出路径
# 调用函数
result_df = calculate_raster_mean(input_folder, output_table)
# 打印结果
print(result_df)

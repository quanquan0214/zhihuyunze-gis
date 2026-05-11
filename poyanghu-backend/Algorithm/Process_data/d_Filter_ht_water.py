# 将相同时间的水位高程信息进行平均，内有删除异常高程的方法

# 将提取的时间和过滤后的水位平均值数据生成CSV文件
# 在这个修改后的代码中，我们在计算过滤后的水位平均值之前，添加了一个条件判断，
# 检查过滤后的数据是否为空。如果过滤后的数据非空，即存在过滤后的水位平均值数据，
# 才进行计算和添加到 data_list 列表中。这样可以剔除没有过滤后的水位平均值数据对应的记录。

import os
import pandas as pd
import matplotlib.pyplot as plt

# 创建空列表用于存储时间和水位平均值数据
data_list = []

# 遍历CSV文件夹中的所有文件
csv_folder = 'D:/Google/H5/Processed/Model/'  # 或者是 D:/Google/H5/Processed/FilteredCSV/
for filename in os.listdir(csv_folder):
    if filename.endswith('.csv'):
        csv_path = os.path.join(csv_folder, filename)

        # 从文件名中提取时间信息
        time = os.path.splitext(filename)[0]

        # 读取CSV文件
        df = pd.read_csv(csv_path)

        # 计算水位平均值和标准差
        average_water_level = df['ht_water_surf'].mean()
        std_water_level = df['ht_water_surf'].std()

        # 根据平均值和标准差过滤异常值
        filtered_df = df[
            (df['ht_water_surf'] >= average_water_level - 3 * std_water_level) &
            (df['ht_water_surf'] <= average_water_level + 3 * std_water_level)
            ]

        # 如果过滤后的数据非空，则计算过滤后的水位平均值
        if not filtered_df.empty:
            filtered_average_water_level = filtered_df['ht_water_surf'].mean()

            # 将时间和过滤后的水位平均值添加到列表中
            data_list.append([time, filtered_average_water_level])

# 创建DataFrame对象
df_data = pd.DataFrame(data_list, columns=['Time', 'Average Water Level'])

# 生成CSV文件
csv_output_path = 'D:/Google/H5/Processed/elevationData_Model.csv'
df_data.to_csv(csv_output_path, index=False)
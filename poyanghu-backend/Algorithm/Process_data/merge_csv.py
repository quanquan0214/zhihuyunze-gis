# 以2019-8月数据为例子，将其他时间段的数据整合起来，得到湖底地形数据。

# 定义一个函数，输入两个csv文件（A,B,A是不变化数据的文件，B是需要修改数据的文件），得到一个合成文件
# 首先读取AB文件，得到AB平均水位
# 间隔水位gap为A平均-B平均
# new_data=B+gap
# 输出new_data文件
# 将A文件和new_data文件合并，得到整合文件，输出整合文件New_A.csv


# 升级版：
# 定义一个函数，输入两个要素（A,B。A是不变化数据的csv文件，B是需要修改csv数据的文件夹），最终得到一个合成文件
# 首先读取A文件，得到A平均水位ea
# 遍历B文件夹，读取每个B文件，得到B平均水位eb,形成列表list_eb[]
# 遍历list_eb[]，计算gap=ea-eb，得到gap列表list_gap[]
# 遍历B文件夹，读取每个B文件，得到B数据，形成列表list_B[]
# 遍历list_B[]，计算new_data=B+gap，得到new_data列表list_new_data[]  (该列表的内容都相当于A时间段下的对应数据)
# 将A文件和list_new_data文件合并，其中遇到经纬度相同的点就使用第一个数据（即将后续重复经纬度的数据去掉），得到整合文件，输出整合文件New_A.csv


import pandas as pd
import os

def merge_csv_files(A, B, C):
    # 读取 A 文件
    df_A = pd.read_csv(A, usecols=[0, 1, 2])
    # 计算 A 文件的平均水位
    ea = df_A['ht_water_surf'].mean()

    list_eb = []
    list_B = []
    # 遍历 B 文件夹
    for file in os.listdir(B):
        if file.endswith('.csv'):
            df_B = pd.read_csv(os.path.join(B, file), usecols=[0, 1, 2])
            # 计算 B 文件的平均水位
            eb = df_B['ht_water_surf'].mean()
            list_eb.append(eb)
            list_B.append(df_B)
    # 计算 gap 列表
    list_gap = [ea - eb for eb in list_eb]

    list_new_data = []
    for i, df in enumerate(list_B):
        new_data = df.copy()
        new_data['ht_water_surf'] = df['ht_water_surf'] + list_gap[i]
        list_new_data.append(new_data)

        # 保存 new_data 到 C 文件夹，文件名与原文件相同
        # output_path = os.path.join(C, os.listdir(B)[i])
        # new_data.to_csv(output_path, index=False)

    # 合并 A 文件和 new_data 文件
    combined_df = df_A.copy()
    for new_data in list_new_data:
        combined_df = pd.concat([combined_df, new_data], ignore_index=True)
    # 去除重复经纬度的数据
    combined_df = combined_df.drop_duplicates(subset=['lon', 'lat'], keep='first')
    # 输出整合文件
    csvname = os.path.basename(A)
    output_path = os.path.join(C, csvname)
    combined_df.to_csv(output_path, index=False)
    return output_path

A = 'D:/Google/H5/Processed/OutputCSV/2019-08-07.csv'
B = 'D:/Google/H5/Processed/OutputCSV/'
C = 'D:/Google/H5/Processed/Model/'
merge_csv_files(A, B, C)


# 在经线上：纬度每隔0.0045度，距离相差约500米。
# 在纬线上：经度每隔0.009度，距离相差约500米。
# 在本函数生成的文件中，点位密度很大

# Delunay三角网插值

# 在经线上：纬度每隔0.0045度，距离相差约500米。
# 在纬线上：经度每隔0.009度，距离相差约500米。
# 将文件插值成每0.01度至少有一个点.


A='D:/Google/H5/Processed/model/New_20190807.csv'
edge='D:/Google/H5/Processed/2019/2019_max.shp'
precision=0.01
B='D:/Google/H5/Processed/model/Delaunay_20190807.csv'
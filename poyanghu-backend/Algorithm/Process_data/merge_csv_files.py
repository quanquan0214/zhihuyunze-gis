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

    # 合并 A 文件和 new_data 文件
    combined_df = df_A.copy()
    for new_data in list_new_data:
        combined_df = pd.concat([combined_df, new_data], ignore_index=True)

    # 处理重复经纬度的数据 - 改为计算平均值
    if not combined_df.empty:
        # 按经纬度分组，计算每组的平均水位
        grouped = combined_df.groupby(['lon', 'lat'])['ht_water_surf'].mean().reset_index()
        combined_df = grouped

    # 输出整合文件
    csvname = os.path.basename(A)
    output_path = os.path.join(C, csvname)
    combined_df.to_csv(output_path, index=False)
    return output_path


# 定义目录路径
output_csv_dir = 'D:/Google/H5/Processed/CorrectCSV/'
model_dir = 'D:/Google/H5/Processed/Model/'
# 创建输出目录（如果不存在）
os.makedirs(model_dir, exist_ok=True)
# 获取所有CSV文件列表
csv_files = [f for f in os.listdir(output_csv_dir) if f.endswith('.csv')]
# 循环处理每个CSV文件
for csv_file in csv_files:
    a_file = os.path.join(output_csv_dir, csv_file)
    merge_csv_files(a_file, output_csv_dir, model_dir)
print(f"已完成所有 {len(csv_files)} 个文件的处理")







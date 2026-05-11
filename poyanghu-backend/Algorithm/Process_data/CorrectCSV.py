import pandas as pd
import os

# 输入和输出目录
input_dir = 'D:/Google/H5/Processed/OutputCSV/'
output_dir = 'D:/Google/H5/Processed/CorrectCSV/'

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)
# 获取所有CSV文件
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
# 处理每个CSV文件
for csv_file in csv_files:
    # 构建完整的文件路径
    input_path = os.path.join(input_dir, csv_file)
    output_path = os.path.join(output_dir, csv_file)
    try:
        # 读取CSV文件
        df = pd.read_csv(input_path)
        # 过滤掉ht_water_surf列中值为负数的行
        filtered_df = df[df['ht_water_surf'] >= 0]
        # 保存过滤后的DataFrame
        filtered_df.to_csv(output_path, index=False)
        # 打印处理信息
        print(f"已处理文件: {csv_file} "
              f"(原始行数: {len(df)}, 过滤后行数: {len(filtered_df)}, "
              f"删除行数: {len(df) - len(filtered_df)})")
    except Exception as e:
        print(f"处理文件 {csv_file} 时出错: {str(e)}")
print(f"所有文件处理完成，共处理 {len(csv_files)} 个文件")
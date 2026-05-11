import pandas as pd

def filter_and_export_common_points(table_max_path, table_min_path, output_path="GWR_data.csv"):
    """
    从table_max中筛选出xy同时存在于table_min中的行，并导出为CSV

    参数:
        table_max_path: table_max文件路径(str)
        table_min_path: table_min文件路径(str)
        output_path: 输出文件路径(str, 默认为"GWR_data.csv")
    """
    try:
        # 1. 读取两个表格
        df_max = pd.read_csv(table_max_path)
        df_min = pd.read_csv(table_min_path)

        # 2. 创建xy坐标的集合用于快速查找
        # 将xy组合成元组（更精确的匹配）
        min_coords = set(zip(df_min['x'], df_min['y']))

        # 3. 筛选table_max中xy同时存在的行
        # 使用apply逐行检查是否在min_coords中
        mask = df_max.apply(lambda row: (row['x'], row['y']) in min_coords, axis=1)
        gwr_data = df_max[mask].copy()

        # 4. 导出结果
        gwr_data.to_csv(output_path, index=False)
        print(f"成功导出 {len(gwr_data)} 行数据到 {output_path}")

        return gwr_data

    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        raise


# 使用示例
if __name__ == "__main__":
    filter_and_export_common_points(
        table_max_path="table_max.csv",
        table_min_path="table_min.csv",
        output_path="GWR_data.csv"
    )
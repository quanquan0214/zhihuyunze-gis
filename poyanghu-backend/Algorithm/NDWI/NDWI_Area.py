# 从“D:\Google\H5\NDWI_shp”文件夹中读取shp文件，计算每个文件中所有面要素的面积总和，并保存成csv文件。格式是：（文件名）NDWI，(面积总和)AREA。

import os
import shapefile
import csv

def calculate_total_area(shp_path):
    """读取单个shp文件中属性表的area字段并求和"""
    total_area = 0
    with shapefile.Reader(shp_path) as sf:
        # 检查是否存在area字段
        fields = [field[0] for field in sf.fields[1:]]  # 跳过第一个字段（DeletionFlag）
        if 'Area' not in fields:
            print(f"警告：文件 {os.path.basename(shp_path)} 中未找到 'area' 字段")
            return 0
        # 获取area字段的索引
        area_index = fields.index('Area')
        # 遍历所有记录，累加area字段的值
        for record in sf.records():
            total_area += record[area_index]

    return total_area


def main():
    # 输入文件夹路径
    input_folder = r"D:/Google/H5/NDWI_shp"
    # 输出CSV文件路径
    output_csv = r"D:/Google/Table/NDWI_Area.csv"
    # 确保输出文件夹存在
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    # 准备数据列表
    data = []
    # 遍历文件夹中的shp文件
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.shp'):
            # 构建完整路径
            shp_path = os.path.join(input_folder, filename)
            # 计算面积总和
            total_area = calculate_total_area(shp_path)
            # 获取不含扩展名的文件名作为NDWI列的值
            ndwi_name = os.path.splitext(filename)[0]
            # 添加到数据列表
            data.append([ndwi_name, total_area])

    # 写入CSV文件
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        # 写入表头
        writer.writerow(['NDWI', 'AREA'])
        # 写入数据
        writer.writerows(data)
    print(f"面积统计已完成，结果保存在: {output_csv}")


if __name__ == "__main__":
    main()
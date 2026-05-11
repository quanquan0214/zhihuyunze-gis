# 读取D:\Google\H5\NDWI\2013_2018_2022_2024中的文件名，依次重命名。将NDWI_201803变成NDWI_201804，依次进行，其中NDWI_201812变成201901.
# 本文件是一个重命名的操作
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

def batch_rename_files(directory):
    """
    批量重命名指定目录中的文件，将文件名中的日期部分递增一个月
    参数:
    directory (str): 文件所在目录路径
    """
    try:
        # 检查目录是否存在
        if not os.path.exists(directory):
            print(f"错误: 目录 '{directory}' 不存在")
            return
        # 获取目录中的所有文件
        files = os.listdir(directory)
        for filename in files:
            # 跳过子目录
            if os.path.isdir(os.path.join(directory, filename)):
                continue
            # 检查文件名是否符合格式 "NDWI_YYYYMM.ext"
            parts = filename.split('I')
            if len(parts) != 2:
                print(f"跳过不符合格式的文件: {filename}")
                continue
            prefix, date_part = parts
            base, ext = os.path.splitext(date_part)
            try:
                # 解析日期部分
                date_obj = datetime.strptime(base, '%Y%m')
                # 计算下一个月的日期
                next_month = date_obj + relativedelta(months=1)
                # 构建新的文件名
                new_date_str = next_month.strftime('%Y%m')
                new_filename = f"{prefix}_{new_date_str}{ext}"
                # 构建完整路径
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename)
                # 执行重命名
                os.rename(old_path, new_path)
                print(f"已重命名: {filename} -> {new_filename}")
            except ValueError:
                print(f"跳过日期格式不正确的文件: {filename}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    # 指定文件目录
    path = 'D:/Google/H5/NDWI/2013_2018_2022_2024'

    # 执行批量重命名
    batch_rename_files(path)


import os


def rename_rsei_files(directory):
    """
    重命名D:\Google\RSEI_full目录下的F_RSEI_****.tif文件为RSEI_****.tif

    参数:
        directory (str): 包含要重命名文件的目录路径
    """
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        # 检查文件名是否以F_RSEI_开头并以.tif结尾
        if filename.startswith("F_RSEI_") and filename.endswith(".tif"):
            # 构建旧文件的完整路径
            old_path = os.path.join(directory, filename)

            # 创建新文件名(去掉开头的F_)
            new_filename = filename.replace("F_RSEI_", "RSEI_", 1)
            new_path = os.path.join(directory, new_filename)

            # 重命名文件
            os.rename(old_path, new_path)
            print(f"重命名: {filename} -> {new_filename}")


# 使用示例
target_directory = r"D:\Google\RSEI_full"
rename_rsei_files(target_directory)
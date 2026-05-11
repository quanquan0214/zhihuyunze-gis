# 将位于不同文件夹中的数据合并或转移。
import os
import shutil

def merge_folders(source_folder, destination_folder):
    # 检查目标文件夹是否存在，如果不存在则创建它
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # 遍历源文件夹及其子文件夹中的所有文件
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            # 构建源文件的完整路径
            source_path = os.path.join(root, file)
            # 构建目标文件的完整路径
            destination_path = os.path.join(destination_folder, file)
            # 将源文件复制到目标文件夹中
            shutil.copy2(source_path, destination_path)

    print("文件夹合并完成！")


# 指定源文件夹和目标文件夹的路径
source_folder = 'D:/ATL/icesat18-20'
destination_folder = 'D:/ATL/icesatALLH5'

# 调用函数进行文件夹合并
merge_folders(source_folder, destination_folder)

# 说明：请确保将 source_folder 和 destination_folder 的值替换为实际的文件夹路径。此代码将遍历源文件夹及其所有子文件夹，并将所有文件复制到目标文件夹中。
# 最后，它将输出"文件夹合并完成！"作为合并过程的确认.


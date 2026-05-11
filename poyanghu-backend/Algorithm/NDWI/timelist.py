import os

# 请将 road 替换为实际的文件夹路径
road = 'D:/Google/H5/Processed/OutputCSV/'

# 初始化一个空列表来存储文件名
filelist = []

# 检查路径是否存在
if os.path.exists(road):
    # 遍历文件夹中的所有文件和文件夹
    for root, dirs, files in os.walk(road):
        for file in files:
            # 将文件名添加到列表中
            f=file.replace('.csv', '')
            filelist.append(f)
else:
    print(f"指定的路径 {road} 不存在。")

# 打印文件名列表
print(filelist)

#将文件保存到txt文件中
with open('D:/Google/H5/Processed/timelist.csv', 'w') as f:
    for item in filelist:
        f.write(item+'\n')
    print('文件保存成功！')
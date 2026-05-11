# 2025/03/26 18:05 本文件可以使用

# 纬度范围：约 24°29′N - 30°05′N。
# 经度范围：约 113°34′E - 118°28′E。
# 打开.h5文件
import h5py
import numpy as np

def print_name(name):
    print(name)
# 打开.h5文件并读取经纬度数据
try:
    with h5py.File('D:/Google/H5/Data/ATL13_006_2019/ATL13_20190508092457_06130301_006_01_subsetted.h5', 'r') as f:

        f.visit(print_name)
        # 假设经纬度数据存储在如下路径中，需要根据实际情况调整
        dataset_lat = f['gt1l/segment_lat']
        latitudes = dataset_lat[:]

        dataset_lon = f['gt1l/segment_lon']
        longitudes = dataset_lon[:]

        # 打印经纬度数据
        print("波束的纬度：")
        print(latitudes)
        print("波束的经度：")
        print(longitudes)

        # 打印经纬度的范围
        print("纬度范围：", np.min(latitudes), "到", np.max(latitudes))
        print("经度范围：", np.min(longitudes), "到", np.max(longitudes))

except Exception as e:
    print(f"读取数据时出现错误：{e}")


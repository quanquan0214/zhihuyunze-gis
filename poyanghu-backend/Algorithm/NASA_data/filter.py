import h5py
import numpy as np
import os

def filter(path):
    # 指定经度范围（度）
    min_lon = 113 + 34 / 60  # 113°34′E
    max_lon = 118 + 28 / 60  # 118°28′E
    min_lat = 24 + 29 / 60  # 最小纬度
    max_lat = 31 + 5 / 60  # 最大纬度
    try:
        with h5py.File(path, 'r') as f:
            dataset_lat = f['gt1l/transect_lat']
            latitudes = np.array(dataset_lat[:])
            dataset_lon = f['gt1l/transect_lon']
            longitudes = np.array(dataset_lon[:])

            # 过滤数据
            filtered_lat = []
            filtered_lon = []
            for i in range(len(dataset_lat)):
                if dataset_lat[i]>=min_lat and dataset_lat[i]<=max_lat and dataset_lon[i]>=min_lon and dataset_lon[i]<=max_lon:
                    filtered_lat.append(latitudes[i])
                    filtered_lon.append(longitudes[i])
            #print(len(dataset_lat),len(dataset_lon))
            if len(filtered_lat)!= 0:
                print("文件名：",f.filename,'点数：',len(filtered_lat))
                #print("过滤后的波束的纬度：",filtered_lat)
                #print("过滤后的波束的经度：",filtered_lon)
    except Exception as e:
        print(f"读取数据时出现错误：{e}")

folder='D:/Google/H5/Data/ATL13_006-20250326_091838'
for file in os.listdir(folder):
    if file.endswith('.h5'):
        path=os.path.join(folder,file)
        filter(path)



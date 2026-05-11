import h5py
import pandas as pd
import os
import numpy as np

def cutdata():
    file_path = 'D:/Google/H5/Data/ATL13_006-20250326_091838'
    with h5py.File(file_path, 'r') as f:
        # 根据ATL13数据结构，提取你需要的组和数据集
        data_group = f['具体组名']
        # 比如湖泊水位数据可能在某个特定的子集中
        water_level_data = data_group['水位相关数据集名'][:]
        lat = data_group['latitude'][:]
        lon = data_group['longitude'][:]
        # 鄱阳湖大致经纬度范围（可根据实际精确调整）
        min_lat, max_lat = 28, 30
        min_lon, max_lon = 115, 117
        mask = (lat >= min_lat) & (lat <= max_lat) & (lon >= min_lon) & (lon <= max_lon)
        filtered_water_level = water_level_data[mask]
        # 保存数据
        np.save('D:/Google/H5/process/filtered_water_level.h5', filtered_water_level)


def extract_footprint_data(data_folder, output_csv):
    all_data = []

    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith('.h5'):
                file_path = os.path.join(root, file)
                try:
                    with h5py.File(file_path, 'r') as f:
                        # 假设不同的波束数据结构相同，这里以 gt1l 为例，你可以根据需要修改或遍历所有波束
                        group_name = '/gt1l/sea_surface/'
                        if group_name in f:
                            segment_lon = f[group_name + 'transect_lon'][:]
                            segment_lat = f[group_name + 'transect_lat'][:]
                            ht_water_surf = f[group_name + 'ht_water_surf'][:]
                            segment_geoid = f[group_name + 'segment_geoid'][:]

                            for lon, lat, height, geoid in zip(segment_lon, segment_lat, ht_water_surf, segment_geoid):
                                all_data.append([lon, lat, height, geoid])

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    # 创建 DataFrame
    df = pd.DataFrame(all_data, columns=['Longitude', 'Latitude', 'Reference_Ellipsoid_Height', 'Geoid_Offset'])

    # 保存为 CSV 文件
    df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")


if __name__ == "__main__":
    data_folder = 'path/to/your/ICESat-2/data'
    output_csv = 'footprint_data.csv'
    extract_footprint_data(data_folder, output_csv)

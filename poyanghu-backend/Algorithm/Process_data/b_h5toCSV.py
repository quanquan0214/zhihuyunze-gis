# 读取ATL13文件中的有效信息并保存为CSV文件
import os
import glob
import h5py
import numpy as np
import pandas as pd


def batch_process_atl13(input_folder, output_folder, bbox):
    """
    Batch process ATL13 files in the input folder and save output files in the specified output folder.
    """
    # 创建输出文件夹，如果它不存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取输入文件夹中所有 h5 文件的列表
    files = glob.glob(os.path.join(input_folder, '*.h5'))

    # 处理每个文件
    for file in files:
        # 获取不带路径的文件名
        filename = os.path.basename(file)

        # 每个波束是一个组
        groups = ['/gt1l', '/gt1r', '/gt2l', '/gt2r', '/gt3l', '/gt3r']

        # 遍历波束
        for group in groups:
            try:
                # 读取单个波束的数据
                with h5py.File(file, 'r') as fi:
                    lat = fi[group + '/segment_lat'][:]
                    lon = fi[group + '/segment_lon'][:]
                    ht_water_surf = fi[group + '/ht_water_surf'][:]
                    segment_geoid = fi[group + '/segment_geoid'][:]
                    ht_ortho = fi[group + '/ht_ortho'][:]

                # 将数据组合成元组列表
                data = list(zip(lon, lat, ht_water_surf, segment_geoid, ht_ortho))

                # 按经纬度范围筛选数据
                if bbox:
                    lonmin, lonmax, latmin, latmax = bbox
                    filtered_data = [
                        (lon_val, lat_val, ht_water_surf_val, segment_geoid_val, ht_ortho_val)
                        for lon_val, lat_val, ht_water_surf_val, segment_geoid_val, ht_ortho_val in data
                        if lonmin <= lon_val <= lonmax and latmin <= lat_val <= latmax
                    ]
                else:
                    filtered_data = data

                # 如果筛选后的数据不为空
                if filtered_data:
                    # 分离筛选后的数据
                    lon_filtered, lat_filtered, ht_water_surf_filtered, segment_geoid_filtered, ht_ortho_filtered = zip(
                        *filtered_data)

                    # 定义输出文件名
                    output_filename = filename.replace('.h5', f'_{group[1:]}.csv')
                    output_file = os.path.join(output_folder, output_filename)

                    # 创建 DataFrame 并保存为 CSV
                    result = pd.DataFrame({
                        'lon': lon_filtered,
                        'lat': lat_filtered,
                        'ht_water_surf': ht_water_surf_filtered,
                        'segment_geoid': segment_geoid_filtered,
                        'ht_ortho': ht_ortho_filtered
                    })
                    result.to_csv(output_file, index=None)
                    print('Output CSV:', output_file)
                else:
                    print(f'No data within bbox for {filename} {group}. Skipping...')

            except Exception as e:
                print(f'Error processing {filename} {group}: {e}')


# 指定输入文件夹，输出文件夹和 bbox 如果需要
input_folder = r'D:/Google/H5/Data/ATL13QL_006_2025'
output_folder = r'D:/Google/H5/pyRegion_Process/CSV/'

# 调用批量处理函数
bbox = [115.5, 117.0, 28.0, 30.0]  # 经纬度范围：[lonmin, lonmax, latmin, latmax]
batch_process_atl13(input_folder, output_folder, bbox)



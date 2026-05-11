# 转换坐标系可以用，但将shp转化成CSV不实用

# 将水体.shp（面文件）转化成vtk文件，然后和CSV结合，得到拥有水位信息和空间信息的vtk文件。最后计算水储量。
import os
import csv
import geopandas as gpd
from osgeo import gdal, ogr, osr

def shp_to_csv(shp_file, csv_file):
    # 打开SHP文件
    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source = driver.Open(shp_file, 0)
    if data_source is None:
        print(f"无法打开 {shp_file}")
        return
    # 获取图层
    layer = data_source.GetLayer()
    # 获取字段名
    layer_defn = layer.GetLayerDefn()
    field_names = []
    for i in range(layer_defn.GetFieldCount()):
        field_defn = layer_defn.GetFieldDefn(i)
        field_names.append(field_defn.GetName())
    # 添加几何字段
    field_names.append('geometry')
    # 打开CSV文件以写入
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        # 写入表头
        writer.writeheader()
        # 遍历要素
        for feature in layer:
            feature_data = {}
            # 获取属性数据
            for field_name in field_names[:-1]:
                feature_data[field_name] = feature.GetField(field_name)
            # 获取几何数据
            geometry = feature.GetGeometryRef()
            if geometry:
                feature_data['geometry'] = geometry.ExportToWkt()
            else:
                feature_data['geometry'] = ''
            # 写入一行数据
            writer.writerow(feature_data)
    # 关闭数据源
    data_source = None
    print(f"已将 {shp_file} 转换为 {csv_file}")

def convert_shp_to_wgs84(input_shp, output_shp):
    # 读取shp文件
    gdf = gpd.read_file(input_shp)
    # 转换为WGS84坐标系
    gdf = gdf.to_crs("EPSG:4326")
    # 保存转换后的shp文件
    gdf.to_file(output_shp)
    return output_shp

# 使用示例
shp_file = 'D:/Google/H5/Processed/2019/2019_max.shp'
csv_file = 'D:/Google/H5/Processed/2019/2019_output.csv'
shp_to_csv(shp_file, csv_file)


input_shp = r"D:\Google\H5\Processed\2019\2019_max.shp"
wgs84_shp = r"D:\Google\H5\Processed\2019\2019_max_wgs84.shp"
# 转换为WGS84坐标系
wgs84_shp = convert_shp_to_wgs84(input_shp, wgs84_shp)

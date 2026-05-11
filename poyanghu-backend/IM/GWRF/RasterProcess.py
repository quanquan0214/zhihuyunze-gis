# 将2000到2022年的基础数据按照需求对齐、裁剪、保存成csv
import time
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import os
import pandas as pd
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from rasterio.mask import mask

class RasterProcessor:
    # 目标分辨率和范围（基于RSEI）
    target_res = (0.0044915764205976155, 0.004491576420597607)
    target_bounds = (113.94231063772011, 26.504792457946483, 118.4788028225237, 30.080087288742178)
    target_shape = (796, 1010)  # 高度、宽度

    Date_dir = "D:/Google/GWR"
    current_time = time.strftime("%Y-%m-%d", time.localtime())
    index_dir = f"D:/Google/GWR/{current_time}"
    city_class = ["D:/Google/city/NC.shp", "D:/Google/city/JJ.shp", "D:/Google/city/YT.shp", "D:/Google/city/JDZ.shp", "D:/Google/city/FZ.shp", "D:/Google/city/SR.shp"]

    def __init__(self, year, region):
        self.year = year
        self.region = region
        self.temp_dir = "D:/Google/temperture/tpt/tpt_"+str(year)+".tif"
        self.rain_dir = "D:/Google/rainfall/RF/"+str(year)+".tif"
        self.rsei_dir = "D:/Google/RSEI_full/RSEI_"+str(year)+".tif"
        self.lucc_dir = "D:/Google/GLC_FCS30/merged/poyang_"+str(year)+".tif"
        self.fvc_dir = "D:/Google/FVC/FVC_"+str(year)+".tif"

        # 如果region是城市代码，则读取shp文件;如果是json文件，则创建临时shp文件，存进index_dir文件夹中
        if region in ["NC", "JJ", "YT", "JDZ", "FZ", "SR"]:
            self.city_shp = "D:/Google/city/" + str(region) + ".shp"
        else:
            self.city_shp="NC"  # 默认南昌市

    def process_tiff(self,input_path, output_path, city_shp, target_res, target_bounds, target_shape,
                      resampling_method=Resampling.bilinear, safe_nodata=0):
        # Step 1: Load the input raster
        with rasterio.open(input_path) as src:
            data = src.read(1)
            src_nodata = src.nodata

            # Replace nodata and NaN values with safe_nodata
            if src_nodata is not None:
                mask = (data == src_nodata) | np.isnan(data)
            else:
                mask = np.isnan(data)
            data = np.where(mask, safe_nodata, data)

            # Step 2: Resample the raster
            transform = src.transform
            dst_transform = rasterio.transform.from_bounds(*target_bounds, target_shape[1], target_shape[0])
            dst_data = np.full(target_shape, safe_nodata, dtype=data.dtype)

            reproject(
                source=data,
                destination=dst_data,
                src_transform=transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=src.crs,
                resampling=resampling_method,
                src_nodata=safe_nodata,
                dst_nodata=safe_nodata
            )

            # Step 3: Filter unreasonable values if needed
            if "RSEI" in input_path or "rsei" in input_path.lower():
                dst_data[(dst_data < 0) | (dst_data > 2)] = safe_nodata

            profile = src.profile.copy()
            profile.update({
                'height': target_shape[0],
                'width': target_shape[1],
                'transform': dst_transform,
                'nodata': safe_nodata,
                'driver': 'GTiff'
            })
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(dst_data, 1)

            # Step 4: Load the shapefile
            try:
                city_boundary = gpd.read_file(city_shp)
                city_boundary = city_boundary.to_crs("EPSG:4326")
                print("Successfully loaded vector data.")
            except Exception as e:
                print(f"Failed to load vector data: {str(e)}")
                exit()

            # Step 5: Crop the raster using the shapefile boundary
            out_image, out_transform = mask(dst_data, city_boundary.geometry, crop=True, all_touched=True)
            out_meta = profile.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "crs": city_boundary.crs
            })

            # Step 6: Save the cropped raster
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image, 1)
            print(f"Successfully cropped and saved: {output_path}")

    def get_csv(self, raster_files, output_csv):
        # 初始化DataFrame
        df = pd.DataFrame()
        # 读取第一个栅格文件（用于获取坐标）
        with rasterio.open(os.path.join(raster_files["lucc"])) as src:
            # 获取栅格坐标
            height, width = src.shape
            rows, cols = np.indices((height, width))
            xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten())

            # 添加坐标到DataFrame
            df["x"] = xs
            df["y"] = ys

        # 逐个读取栅格数据并添加到DataFrame
        for var, file in raster_files.items():
            with rasterio.open(os.path.join(file)) as src:
                data = src.read(1)  # 读取第一波段
                df[var] = data.flatten()  # 展平并添加到DataFrame

        # 移除无效值（NoData）
        df = df[~df.isna().any(axis=1)]  # 删除任何包含NaN的行
        df = df[df["RSEI"] != 0]

        # 将lucc转换为分类类型并独热编码
        data['lucc'] = data['lucc'].astype('category')
        lucc_dummies = pd.get_dummies(data['lucc'], prefix='lucc', drop_first=True)  # 避免多重共线性
        data = pd.concat([data.drop('lucc', axis=1), lucc_dummies], axis=1)

        # 确保独热编码后的lucc列已转换为0/1
        lucc_columns = [col for col in data.columns if col.startswith('lucc_')]
        data[lucc_columns] = data[lucc_columns].astype(int)

        # # 对连续变量标准化（解决尺度差异）
        scaler = StandardScaler()
        data[['temperature', 'rainfall', 'fvc']] = scaler.fit_transform(data[['temperature', 'rainfall', 'fvc']])

        # 保存为CSV
        df.to_csv(output_csv, index=False)
        print(f"数据已保存至 {output_csv}")

    def delete_temp_files(self):
        # 删除临时文件
        for file in self.index_dir:
            if os.path.exists(file):
                os.remove(file)
                print(f"已删除临时文件: {file}")
            else:
                print(f"临时文件不存在: {file}")

    def run(self):
        # 检查目录是否存在
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)

        # 裁剪并保存栅格数据
        rsei=self.index_dir+"/rsei_"+str(self.year)+".tif"
        lucc=self.index_dir+"/lucc_"+str(self.year)+".tif"
        rain=self.index_dir+"/rain_"+str(self.year)+".tif"
        temp=self.index_dir+"/temp_"+str(self.year)+".tif"
        fvc=self.index_dir+"/fvc_"+str(self.year)+".tif"
        self.process_tiff(self.temp_dir,temp, self.city_shp, self.target_res, self.target_bounds, self.target_shape, safe_nodata=0)
        self.process_tiff(self.rain_dir,rain, self.city_shp, self.target_res, self.target_bounds, self.target_shape, safe_nodata=0)
        self.process_tiff(self.rsei_dir,rsei, self.city_shp, self.target_res, self.target_bounds, self.target_shape, safe_nodata=0)
        self.process_tiff(self.lucc_dir,lucc, self.city_shp, self.target_res, self.target_bounds, self.target_shape, safe_nodata=0)
        self.process_tiff(self.fvc_dir,fvc, self.city_shp, self.target_res, self.target_bounds, self.target_shape, safe_nodata=0)
        # 准备CSV文件路径和栅格文件列表
        raster_dir = {"rsei": rsei, "lucc": lucc, "rainfall": rain, "temperature": temp, "fvc": fvc}
        output_csv = self.index_dir+"/result_"+str(self.year)+".csv"
        # 调用方法生成CSV
        self.get_csv(raster_dir, output_csv)
        # 删除临时文件
        self.delete_temp_files()

if __name__ == '__main__':
    # 实例化类
    processor = RasterProcessor(2022, "NC")
    # 运行程序
    processor.run()





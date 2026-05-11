# # 处理LUCC的问题
#
# import pandas as pd
# import rasterio
# import numpy as np
#
# # LUCC分类字典
# LUCC_CLASSES = {
#     10: "雨养耕地", 11: "草本植被覆盖", 20: "灌溉耕地",
#     51: "开阔常绿阔叶林", 52: "闭阔常绿阔叶林",
#     61: "开阔落叶阔叶林(0.15 < fc <0.4)", 62: "闭阔落叶阔叶林(fc > 0.4)",
#     71: "开阔常绿针叶林(0.15 < fc < 0.4)", 72: "闭阔常绿针叶林(fc > 0.4)",
#     91: "开阔混交叶片林(阔叶树和针叶树)",
#     120: "灌木林", 121: "常绿灌木林", 130: "草地",
#     150: "稀疏植被(fc < 0.15)", 181: "沼泽", 182: "沼泽地", 183: "水淹平地",
#     190: "不透水表面", 200: "裸地", 210: "水体"
# }
#
# # 读取并处理栅格数据
# with rasterio.open("D:/Google/GWR_k/poyang_2000_resampled.tif") as src:
#     lucc = src.read(1)
#     # 直接使用布尔索引过滤0值，效率更高
#     lucc_flat = lucc[lucc != 0]
#
# # 创建DataFrame
# lucc_df = pd.DataFrame({'lucc': lucc_flat})
#
# # 映射分类名称
# lucc_df['lucc_name'] = lucc_df['lucc'].map(LUCC_CLASSES).fillna('其他')
#
# # 选择样本量>100的类别
# value_counts = lucc_df['lucc_name'].value_counts()
# valid_classes = value_counts[value_counts > 100].index
#
# # 生成哑变量（优化版）
# lucc_filtered = lucc_df['lucc_name'].where(
#     lucc_df['lucc_name'].isin(valid_classes),
#     other='其他小类'  # 更明确的命名
# )
#
# lucc_dummy = pd.get_dummies(lucc_filtered, prefix='lucc', dtype=int)  # 直接指定int类型
#
# # 合并结果
# result_df = pd.concat([lucc_df, lucc_dummy], axis=1)
#
# # 输出结果
# print("转换结果示例：")
# print(result_df.head(10))
#
# print("\n类别统计（样本量>100）：")
# print(value_counts[value_counts > 100])
#
# print("\n被合并的小类别：")
# print(value_counts[value_counts <= 100])


# 使用城市矢量数据裁剪栅格数据
import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from pathlib import Path

# 输入输出路径配置
city_shp = "D:/Google/city/南昌.shp"  # 南昌市边界
input_raster_dir = "D:/Google/GWR/"  # 栅格数据目录
output_dir = "D:/Google/GWR/"  # 裁剪后输出目录

# 需要裁剪的栅格文件名列表（根据图片中的名称）
raster_files = ["2000_resampled.tif", "RSEI_2000_resampled.tif","poyang_2000_resampled.tif", "tpt_2000_resampled.tif"]

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 1. 读取南昌市边界
try:
    city_boundary = gpd.read_file(city_shp)
    # 确保几何有效并转换为WGS84坐标系统（如果栅格数据也是这个坐标系）
    city_boundary = city_boundary.to_crs("EPSG:4326")
    print("成功加载南昌市边界")
except Exception as e:
    print(f"加载南昌市边界失败: {str(e)}")
    exit()

# 2. 逐个处理栅格数据
for raster_file in raster_files:
    input_path = os.path.join(input_raster_dir, raster_file)
    output_path = os.path.join(output_dir, f"nanchang_{raster_file}")

    if not os.path.exists(input_path):
        print(f"警告: {input_path} 不存在，跳过")
        continue

    try:
        # 打开栅格文件
        with rasterio.open(input_path) as src:
            # 执行裁剪
            out_image, out_transform = mask(
                src,
                city_boundary.geometry,
                crop=True,
                all_touched=True  # 包含所有接触边界的像素
            )

            # 复制原文件的元数据
            out_meta = src.meta.copy()

            # 更新元数据
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "crs": city_boundary.crs  # 使用与边界相同的CRS
            })

            # 保存裁剪后的栅格
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)

            print(f"成功裁剪并保存: {output_path}")

    except Exception as e:
        print(f"处理 {raster_file} 时出错: {str(e)}")

print("所有栅格数据处理完成")
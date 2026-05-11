import geopandas as gpd
import rasterio
from rasterio.mask import mask
import json
import os

# 读取矢量文件
vector_file = "D:/Google/ESRI/poyangRegion.shp"
gdf = gpd.read_file(vector_file)
# 确保矢量数据为GeoJSON格式（rasterio需要）
geojson_geoms = json.loads(gdf.to_json())["features"]
geoms = [feature["geometry"] for feature in geojson_geoms]
# 读取栅格文件
raster_file = "D:/Google/GLC_FCS30/GLC_FCS30D_20002022_E115N30_Annual.tif"
output_dir = "D:/Google/GLC_FCS30/11530"  # 输出文件夹
# 创建输出目录（如果不存在）
os.makedirs(output_dir, exist_ok=True)
# 打开栅格文件并进行裁剪
with rasterio.open(raster_file) as src:
    # 获取元数据
    meta = src.meta
    # 裁剪栅格（所有波段）
    out_image, out_transform = mask(src, geoms, crop=True)
    # 更新元数据
    meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],  # 行数
        "width": out_image.shape[2],  # 列数
        "transform": out_transform,
        "count": src.count  # 保持原始波段数
    })
    # 输出裁剪后的栅格文件
    output_path = os.path.join(output_dir, "poyangRegion_clipped.tif")
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(out_image)

    print(f"成功裁剪栅格数据并保存至: {output_path}")

    # 如果栅格是多时间序列数据（如2000-2022每年一个波段）
    # 可以单独提取每年的裁剪结果
    if src.count > 1:
        print(f"栅格数据包含 {src.count} 个波段，正在提取各年份...")
        for band in range(1, src.count + 1):
            year = 1999 + band  # 假设第一个波段是2000年，依此类推
            year_dir = os.path.join(output_dir, str(year))
            os.makedirs(year_dir, exist_ok=True)

            # 创建单波段裁剪结果
            year_image = out_image[band - 1:band]  # 注意索引从0开始
            year_meta = meta.copy()
            year_meta.update({"count": 1})  # 设置为单波段

            year_path = os.path.join(year_dir, f"poyang_{year}.tif")
            with rasterio.open(year_path, "w", **year_meta) as dst:
                dst.write(year_image)

            print(f"已提取 {year} 年数据至: {year_path}")
'''
import os
import argparse
from pathlib import Path
import rasterio
from rasterio.merge import merge
from rasterio.enums import Resampling
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(description='拼接栅格影像')
    parser.add_argument('--input', '-i', nargs='+', required=True,
                        help='输入的栅格影像路径，可以是多个文件')
    parser.add_argument('--output', '-o', required=True,
                        help='输出的拼接影像路径')
    parser.add_argument('--resampling', '-r', default='nearest',
                        choices=['nearest', 'bilinear', 'cubic', 'cubic_spline',
                                 'lanczos', 'average', 'mode', 'gauss'],
                        help='重采样方法，默认为最近邻')
    parser.add_argument('--nodata', type=float, default=None,
                        help='设置输出影像的nodata值')
    parser.add_argument('--overwrite', action='store_true',
                        help='是否覆盖已存在的输出文件')
    return parser


def validate_args(args):
    """验证命令行参数"""
    # 检查输入文件是否存在
    for file in args.input:
        if not os.path.exists(file):
            raise FileNotFoundError(f"输入文件不存在: {file}")

    # 检查输出目录是否存在
    output_dir = os.path.dirname(args.output)
    if not os.path.exists(output_dir) and output_dir:
        os.makedirs(output_dir)

    # 检查输出文件是否存在且是否允许覆盖
    if os.path.exists(args.output) and not args.overwrite:
        raise FileExistsError(f"输出文件已存在: {args.output}，请使用 --overwrite 参数覆盖")

    # 检查输入文件数量
    if len(args.input) < 2:
        raise ValueError("至少需要两个输入文件进行拼接")

    # 检查所有输入文件是否为栅格数据
    for file in args.input:
        try:
            with rasterio.open(file) as src:
                pass
        except:
            raise ValueError(f"文件 {file} 不是有效的栅格数据")


def get_resampling_method(method_name):
    """获取重采样方法的枚举值"""
    resampling_methods = {
        'nearest': Resampling.nearest,
        'bilinear': Resampling.bilinear,
        'cubic': Resampling.cubic,
        'cubic_spline': Resampling.cubic_spline,
        'lanczos': Resampling.lanczos,
        'average': Resampling.average,
        'mode': Resampling.mode,
        'gauss': Resampling.gauss
    }
    return resampling_methods.get(method_name, Resampling.nearest)


def mosaic_rasters(input_files, output_file, resampling_method='nearest', nodata=None):
    """拼接栅格影像"""
    # 打开所有输入栅格
    src_files_to_mosaic = []
    for file in input_files:
        src = rasterio.open(file)
        src_files_to_mosaic.append(src)

    logger.info(f"开始拼接 {len(input_files)} 个栅格影像")

    # 获取重采样方法
    resampling = get_resampling_method(resampling_method)

    try:
        # 执行拼接
        mosaic, out_trans = merge(src_files_to_mosaic, resampling=resampling, nodata=nodata)

        # 获取输出影像的元数据
        out_meta = src_files_to_mosaic[0].meta.copy()

        # 更新元数据
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "nodata": nodata if nodata is not None else src.nodata
        })

        # 写入输出文件
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(mosaic)

        logger.info(f"拼接完成，输出文件: {output_file}")

    except Exception as e:
        logger.error(f"拼接过程中发生错误: {str(e)}")
        raise
    finally:
        # 关闭所有栅格文件
        for src in src_files_to_mosaic:
            src.close()


def main():
    """主函数"""
    try:
        # 解析命令行参数
        parser = create_parser()
        args = parser.parse_args()

        # 验证参数
        validate_args(args)

        # 执行拼接
        mosaic_rasters(
            input_files=args.input,
            output_file=args.output,
            resampling_method=args.resampling,
            nodata=args.nodata
        )

        logger.info("程序执行完毕")

    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        exit(1)


if __name__ == "__main__":
    main()


'''
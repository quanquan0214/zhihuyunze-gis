import rasterio
from rasterio.merge import merge
import os

# 设置年份
t = "2022"
# 设置输入和输出文件路径
input_files = [
    r"D:/Google/GLC_FCS30/11530/" + t + "/poyang_" + t + ".tif",
    r"D:/Google/GLC_FCS30/11030/" + t + "/poyang_" + t + ".tif"
]
print("输入文件列表:", input_files)

# 确保输出目录存在
output_dir = r"D:\Google\GLC_FCS30\merged"
os.makedirs(output_dir, exist_ok=True)
name = "poyang_" + t + ".tif"
output_file = os.path.join(output_dir, name)

# 设置拼接参数 - 使用最近邻重采样以保持原始值
resampling_method = 'nearest'  # 最近邻重采样，不改变原始值
nodata_value = None  # 设置NoData值，如果需要的话

def get_resampling_method(method_name):
    """获取重采样方法的枚举值"""
    from rasterio.enums import Resampling
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

def main():
    try:
        print(f"开始拼接栅格影像...")
        # 检查输入文件是否存在
        for file in input_files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"输入文件不存在: {file}")
        # 打开所有输入栅格
        src_files_to_mosaic = []
        for file in input_files:
            src = rasterio.open(file)
            src_files_to_mosaic.append(src)
        # 获取重采样方法
        resampling = get_resampling_method(resampling_method)
        # 执行拼接 - 使用指定的重采样方法
        print(f"正在执行拼接，使用 {resampling_method} 重采样方法...")
        mosaic, out_trans = merge(src_files_to_mosaic, resampling=resampling, nodata=nodata_value)
        # 获取输出影像的元数据
        out_meta = src_files_to_mosaic[0].meta.copy()
        # 更新元数据
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "nodata": nodata_value if nodata_value is not None else src_files_to_mosaic[0].nodata
        })
        # 写入输出文件
        print(f"正在写入输出文件: {output_file}")
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(mosaic)
        # 关闭所有栅格文件
        for src in src_files_to_mosaic:
            src.close()
        print(f"拼接完成！输出文件保存在: {output_file}")
    except Exception as e:
        print(f"拼接过程中发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
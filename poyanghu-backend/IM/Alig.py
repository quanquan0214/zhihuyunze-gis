import os
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
import tempfile
import shutil

class DataAlignmentManager:
    def __init__(self, temperature_dir, rainfall_dir, rsei_dir, lucc_dir, reference_year=2000):
        self.temperature_dir = temperature_dir
        self.rainfall_dir = rainfall_dir
        self.rsei_dir = rsei_dir
        self.lucc_dir = lucc_dir
        self.reference_year = reference_year
        self.reference_crs = None
        self.reference_transform = None
        self.reference_shape = None
        self.aligned_cache_dir = tempfile.mkdtemp(prefix="aligned_data_")

        # 初始化时设置参考数据
        self._initialize_reference_data()

    def _initialize_reference_data(self):
        """初始化参考年份的投影、分辨率和范围"""
        try:
            # 使用RSEI数据作为参考
            ref_file = self._find_year_file(self.rsei_dir, self.reference_year)
            with rasterio.open(ref_file) as src:
                self.reference_crs = src.crs
                self.reference_transform = src.transform
                self.reference_shape = src.shape
        except Exception as e:
            raise RuntimeError(f"初始化参考数据失败: {str(e)}")

    def _find_year_file(self, directory, year):
        """在目录中查找包含年份的文件"""
        for f in os.listdir(directory):
            if str(year) in f and f.endswith('.tif'):
                return os.path.join(directory, f)
        raise FileNotFoundError(f"未找到年份 {year} 的数据文件在目录 {directory}")

    def check_alignment(self, file_path):
        """检查单个文件是否与参考数据对齐"""
        try:
            with rasterio.open(file_path) as src:
                return (src.crs == self.reference_crs and
                        src.transform == self.reference_transform and
                        src.shape == self.reference_shape)
        except Exception as e:
            print(f"检查对齐状态失败 {file_path}: {str(e)}")
            return False

    def align_data(self, input_path):
        """对齐单个数据文件"""
        try:
            # 检查是否已对齐
            if self.check_alignment(input_path):
                return input_path

            # 创建输出路径
            filename = os.path.basename(input_path)
            output_path = os.path.join(self.aligned_cache_dir, filename)

            # 执行重投影和对齐
            with rasterio.open(input_path) as src:
                profile = src.profile
                data = src.read(1)

                destination = np.empty(self.reference_shape, dtype=data.dtype)
                reproject(
                    source=data,
                    destination=destination,
                    src_transform=profile['transform'],
                    src_crs=profile['crs'],
                    dst_crs=self.reference_crs,
                    dst_transform=self.reference_transform,
                    dst_shape=self.reference_shape,
                    resampling=Resampling.bilinear
                )

                # 更新元数据并保存
                profile.update({
                    'crs': self.reference_crs,
                    'transform': self.reference_transform,
                    'height': self.reference_shape[0],
                    'width': self.reference_shape[1],
                    'driver': 'GTiff'
                })

                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(destination, 1)

            return output_path
        except Exception as e:
            print(f"对齐数据失败 {input_path}: {str(e)}")
            return None

    def get_aligned_data_path(self, data_type, year):
        """获取对齐后的数据路径"""
        # 确定原始数据目录
        if data_type == 'temperature':
            base_dir = self.temperature_dir
        elif data_type == 'rainfall':
            base_dir = self.rainfall_dir
        elif data_type == 'rsei':
            base_dir = self.rsei_dir
        elif data_type == 'lucc':
            base_dir = self.lucc_dir
        else:
            raise ValueError(f"未知的数据类型: {data_type}")

        # 查找原始文件
        original_path = self._find_year_file(base_dir, year)

        # 检查是否需要对齐
        if self.check_alignment(original_path):
            return original_path

        # 对齐数据
        return self.align_data(original_path)

    def cleanup(self):
        """清理临时文件"""
        try:
            shutil.rmtree(self.aligned_cache_dir)
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 初始化对齐管理器
    aligner = DataAlignmentManager(
        temperature_dir=r"D:/Google/temperture/tpt",
        rainfall_dir=r"D:/Google/rainfall/RF",
        rsei_dir=r"D:/Google/RSEI_full",
        lucc_dir=r"D:/Google/GLC_FCS30/merged",
        reference_year=2000
    )

    try:
        # 获取对齐后的数据路径
        aligned_temp_2010 = aligner.get_aligned_data_path('temperature', 2010)
        aligned_rain_2010 = aligner.get_aligned_data_path('rainfall', 2010)
        aligned_rsei_2010 = aligner.get_aligned_data_path('rsei', 2010)
        aligned_lucc_2010 = aligner.get_aligned_data_path('lucc', 2010)

        print(f"对齐后的温度数据: {aligned_temp_2010}")
        print(f"对齐后的降水数据: {aligned_rain_2010}")
        print(f"对齐后的RSEI数据: {aligned_rsei_2010}")
        print(f"对齐后的LUCC数据: {aligned_lucc_2010}")

    finally:
        # 清理临时文件
        aligner.cleanup()
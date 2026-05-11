import os
import numpy as np
import rasterio
from typing import Dict, List, Tuple, Optional, Union
import logging

'''
逐年数据提取：
get_temperature_data(year) - 获取指定年份温度栅格数据
get_rainfall_data(year) - 获取指定年份降水栅格数据
get_rsei_data(year) - 获取指定年份RSEI栅格数据
get_lucc_data(year) - 获取指定年份LUCC栅格数据
逐点数据提取：
get_point_climate_data(lat, lng, year) - 获取指定坐标点的温度、降水、RSEI和LUCC值
get_multi_year_point_data(lat, lng, years) - 获取指定点位多年数据
统计分析：
get_annual_statistics(year) - 计算年度统计值（均值、中位数、标准差等）
get_climate_averages(start_year, end_year) - 计算多年平均值
时间序列数据：
get_time_series_data(data_type) - 获取用于折线图的时间序列数据
设计特点：
数据验证：validate_data_files() 检查文件完整性
与前端接口的对应关系：
/rsei/trend → get_time_series_data() 提供温度、RSEI、LUCC数组
/scatter → get_point_climate_data() 提供散点图横坐标数据
其他分析服务 → 提供基础气候和LUCC数据支持
'''

class ClimateDataService:
    """
    温度、降水、RSEI和土地覆盖数据服务类
    功能：提供温度、降水、RSEI和LUCC数据（逐年、逐点、均值等）
    用途：用于折线图、散点图横坐标（温度、RSEI、LUCC）等
    """

    def __init__(self, temperature_dir: str = r"D:/Google/temperture/tpt",
                 rainfall_dir: str = r"D:/Google/rainfall/RF",
                 rsei_dir: str = r"D:/Google/RSEI_full",
                 lucc_dir: str = r"D:/Google/GLC_FCS30/merged"):
        """
        初始化气候和土地覆盖数据服务
        Args:
            temperature_dir: 温度数据目录路径
            rainfall_dir: 降水数据目录路径
            rsei_dir: RSEI数据目录路径
            lucc_dir: 土地覆盖数据目录路径
        """
        self.temperature_dir = temperature_dir
        self.rainfall_dir = rainfall_dir
        self.rsei_dir = rsei_dir
        self.lucc_dir = lucc_dir
        self.years = list(range(2000, 2023))  # 2000-2022年

        # 缓存数据，避免重复读取
        self._temperature_cache = {}
        self._rainfall_cache = {}
        self._rsei_cache = {}
        self._lucc_cache = {}

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_temperature_file_path(self, year: int) -> str:
        """获取温度文件路径"""
        return os.path.join(self.temperature_dir, f"tpt_{year}.tif")


    def _get_rainfall_file_path(self, year: int) -> str:
        """获取降水文件路径"""
        return os.path.join(self.rainfall_dir, f"{year}.tif")

    def _get_rsei_file_path(self, year: int) -> str:
        """获取RSEI文件路径"""
        return os.path.join(self.rsei_dir, f"RSEI_{year}.tif")

    def _get_lucc_file_path(self, year: int) -> str:
        """获取LUCC文件路径"""
        return os.path.join(self.lucc_dir, f"poyang_{year}.tif")

    def _load_raster_data(self, file_path: str) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        """
        加载栅格数据
        Args:
            file_path: 文件路径
        Returns:
            Tuple[数据数组, 栅格配置信息]
        """
        try:
            with rasterio.open(file_path) as src:
                data = src.read(1)  # 读取第一个波段
                profile = src.profile
                # 处理NoData值
                if src.nodata is not None:
                    data = np.where(data == src.nodata, np.nan, data)
                return data, profile
        except Exception as e:
            self.logger.error(f"加载栅格数据失败: {file_path}, 错误: {str(e)}")
            raise

    def get_temperature_data(self, year: int) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        """
        获取指定年份的温度数据
        Args:
            year: 年份
        Returns:
            Tuple[温度数据数组, 栅格配置]
        """
        if year not in self.years:
            raise ValueError(f"年份 {year} 不在支持范围内 ({min(self.years)}-{max(self.years)})")

        if year in self._temperature_cache:
            return self._temperature_cache[year]

        file_path = self._get_temperature_file_path(year)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"温度数据文件不存在: {file_path}")

        data, profile = self._load_raster_data(file_path)
        self._temperature_cache[year] = (data, profile)
        return data, profile

    def get_rainfall_data(self, year: int) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        """
        获取指定年份的降水数据
        Args:
            year: 年份
        Returns:
            Tuple[降水数据数组, 栅格配置]
        """
        if year not in self.years:
            raise ValueError(f"年份 {year} 不在支持范围内 ({min(self.years)}-{max(self.years)})")

        if year in self._rainfall_cache:
            return self._rainfall_cache[year]

        file_path = self._get_rainfall_file_path(year)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"降水数据文件不存在: {file_path}")

        data, profile = self._load_raster_data(file_path)
        self._rainfall_cache[year] = (data, profile)
        return data, profile

    def get_rsei_data(self, year: int) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        """
        获取指定年份的RSEI数据
        Args:
            year: 年份
        Returns:
            Tuple[RSEI数据数组, 栅格配置]
        """
        if year not in self.years:
            raise ValueError(f"年份 {year} 不在支持范围内 ({min(self.years)}-{max(self.years)})")

        if year in self._rsei_cache:
            return self._rsei_cache[year]

        file_path = self._get_rsei_file_path(year)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"RSEI数据文件不存在: {file_path}")

        data, profile = self._load_raster_data(file_path)
        self._rsei_cache[year] = (data, profile)
        return data, profile

    def get_lucc_data(self, year: int) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        """
        获取指定年份的LUCC数据
        Args:
            year: 年份
        Returns:
            Tuple[LUCC数据数组, 栅格配置]
        """
        if year not in self.years:
            raise ValueError(f"年份 {year} 不在支持范围内 ({min(self.years)}-{max(self.years)})")

        if year in self._lucc_cache:
            return self._lucc_cache[year]

        file_path = self._get_lucc_file_path(year)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"LUCC数据文件不存在: {file_path}")

        data, profile = self._load_raster_data(file_path)
        self._lucc_cache[year] = (data, profile)
        return data, profile

    def get_point_climate_data(self, lat: float, lng: float, year: int) -> Dict[str, float]:
        """
        获取指定点位和年份的气候及LUCC数据
        Args:
            lat: 纬度
            lng: 经度
            year: 年份
        Returns:
            包含温度、降水、RSEI和LUCC的字典
        """
        try:
            temp_data, temp_profile = self.get_temperature_data(year)
            temp_value = self._extract_point_value(temp_data, temp_profile, lat, lng)

            rainfall_data, rainfall_profile = self.get_rainfall_data(year)
            rainfall_value = self._extract_point_value(rainfall_data, rainfall_profile, lat, lng)

            rsei_data, rsei_profile = self.get_rsei_data(year)
            rsei_value = self._extract_point_value(rsei_data, rsei_profile, lat, lng)

            lucc_data, lucc_profile = self.get_lucc_data(year)
            lucc_value = self._extract_point_value(lucc_data, lucc_profile, lat, lng)

            return {
                'temperature': float(temp_value) if not np.isnan(temp_value) else None,
                'rainfall': float(rainfall_value) if not np.isnan(rainfall_value) else None,
                'rsei': float(rsei_value) if not np.isnan(rsei_value) else None,
                'lucc': float(lucc_value) if not np.isnan(lucc_value) else None,
                'year': year,
                'lat': lat,
                'lng': lng
            }
        except Exception as e:
            self.logger.error(f"获取点位数据失败: lat={lat}, lng={lng}, year={year}, 错误: {str(e)}")
            return {
                'temperature': None,
                'rainfall': None,
                'rsei': None,
                'lucc': None,
                'year': year,
                'lat': lat,
                'lng': lng
            }

    def _extract_point_value(self, data: np.ndarray, profile: rasterio.profiles.Profile,
                             lat: float, lng: float) -> float:
        """
        从栅格数据中提取指定点位的值
        Args:
            data: 栅格数据数组
            profile: 栅格配置信息
            lat: 纬度
            lng: 经度
        Returns:
            点位对应的值
        """
        transform = profile['transform']
        col, row = ~transform * (lng, lat)
        col, row = int(col), int(row)

        if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
            return data[row, col]
        else:
            self.logger.warning(f"坐标超出数据范围: lat={lat}, lng={lng}")
            return np.nan

    def get_annual_statistics(self, year: int) -> Dict[str, Dict[str, float]]:
        """
        获取指定年份的统计数据
        Args:
            year: 年份
        Returns:
            包含温度、降水、RSEI和LUCC统计信息的字典
        """
        try:
            temp_data, _ = self.get_temperature_data(year)
            temp_stats = self._calculate_statistics(temp_data)

            rainfall_data, _ = self.get_rainfall_data(year)
            rainfall_stats = self._calculate_statistics(rainfall_data)

            rsei_data, _ = self.get_rsei_data(year)
            rsei_stats = self._calculate_statistics(rsei_data)

            lucc_data, _ = self.get_lucc_data(year)
            lucc_stats = self._calculate_statistics(lucc_data)

            return {
                'temperature': temp_stats,
                'rainfall': rainfall_stats,
                'rsei': rsei_stats,
                'lucc': lucc_stats,
                'year': year
            }
        except Exception as e:
            self.logger.error(f"获取年度统计数据失败: year={year}, 错误: {str(e)}")
            return {'temperature': {}, 'rainfall': {}, 'rsei': {}, 'lucc': {}, 'year': year}

    def _calculate_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """
        计算栅格数据的统计值
        Args:
            data: 栅格数据数组
        Returns:
            统计信息字典
        """
        valid_data = data[~np.isnan(data)]
        if len(valid_data) == 0:
            return {
                'mean': np.nan,
                'median': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'count': 0
            }
        return {
            'mean': float(np.mean(valid_data)),
            'median': float(np.median(valid_data)),
            'std': float(np.std(valid_data)),
            'min': float(np.min(valid_data)),
            'max': float(np.max(valid_data)),
            'count': len(valid_data)
        }

    def get_time_series_data(self, data_type: str = 'temperature') -> Dict[str, List]:
        """
        获取时间序列数据（用于折线图）
        Args:
            data_type: 数据类型，'temperature'、'rainfall'、'rsei' 或 'lucc'
        Returns:
            包含年份和对应统计值的字典
        """
        years = []
        values = []
        for year in self.years:
            try:
                stats = self.get_annual_statistics(year)
                if data_type in stats and 'mean' in stats[data_type]:
                    mean_value = stats[data_type]['mean']
                    if not np.isnan(mean_value):
                        years.append(year)
                        values.append(mean_value)
            except Exception as e:
                self.logger.warning(f"获取 {year} 年 {data_type} 数据失败: {str(e)}")
                continue
        return {
            'years': years,
            'values': values,
            'data_type': data_type
        }

    def get_multi_year_point_data(self, lat: float, lng: float,
                                  years: Optional[List[int]] = None) -> List[Dict]:
        """
        获取指定点位多年的气候和LUCC数据
        Args:
            lat: 纬度
            lng: 经度
            years: 年份列表，默认为全部年份
        Returns:
            多年数据列表
        """
        if years is None:
            years = self.years
        results = []
        for year in years:
            try:
                data = self.get_point_climate_data(lat, lng, year)
                if all(data[key] is not None for key in ['temperature', 'rainfall', 'rsei', 'lucc']):
                    results.append(data)
            except Exception as e:
                self.logger.warning(f"获取点位多年数据失败: lat={lat}, lng={lng}, year={year}, 错误: {str(e)}")
                continue
        return results

    def get_climate_averages(self, start_year: int = 2000, end_year: int = 2022) -> Dict[str, float]:
        """
        获取多年平均气候和LUCC数据
        Args:
            start_year: 起始年份
            end_year: 结束年份
        Returns:
            多年平均值字典
        """
        temp_series = self.get_time_series_data('temperature')
        rainfall_series = self.get_time_series_data('rainfall')
        rsei_series = self.get_time_series_data('rsei')
        lucc_series = self.get_time_series_data('lucc')
        temp_values = [v for y, v in zip(temp_series['years'], temp_series['values'])
                       if start_year <= y <= end_year]
        rainfall_values = [v for y, v in zip(rainfall_series['years'], rainfall_series['values'])
                           if start_year <= y <= end_year]
        rsei_values = [v for y, v in zip(rsei_series['years'], rsei_series['values'])
                       if start_year <= y <= end_year]
        lucc_values = [v for y, v in zip(lucc_series['years'], lucc_series['values'])
                       if start_year <= y <= end_year]
        return {
            'temperature_avg': float(np.mean(temp_values)) if temp_values else np.nan,
            'rainfall_avg': float(np.mean(rainfall_values)) if rainfall_values else np.nan,
            'rsei_avg': float(np.mean(rsei_values)) if rsei_values else np.nan,
            'lucc_avg': float(np.mean(lucc_values)) if lucc_values else np.nan,
            'temperature_std': float(np.std(temp_values)) if temp_values else np.nan,
            'rainfall_std': float(np.std(rainfall_values)) if rainfall_values else np.nan,
            'rsei_std': float(np.std(rsei_values)) if rsei_values else np.nan,
            'lucc_std': float(np.std(lucc_values)) if lucc_values else np.nan,
            'years_count': len(set(temp_series['years'] + rainfall_series['years'] +
                                  rsei_series['years'] + lucc_series['years'])),
            'start_year': start_year,
            'end_year': end_year
        }

    def clear_cache(self):
        """清空缓存"""
        self._temperature_cache.clear()
        self._rainfall_cache.clear()
        self._rsei_cache.clear()
        self._lucc_cache.clear()
        self.logger.info("缓存已清空")

    def get_available_years(self) -> List[int]:
        """获取可用年份列表"""
        return self.years.copy()

    def validate_data_files(self) -> Dict[str, List[str]]:
        """
        验证数据文件是否存在
        Returns:
            包含存在和缺失文件信息的字典
        """
        existing_temp_files = []
        missing_temp_files = []
        existing_rainfall_files = []
        missing_rainfall_files = []
        existing_rsei_files = []
        missing_rsei_files = []
        existing_lucc_files = []
        missing_lucc_files = []
        for year in self.years:
            temp_path = self._get_temperature_file_path(year)
            if os.path.exists(temp_path):
                existing_temp_files.append(temp_path)
            else:
                missing_temp_files.append(temp_path)
            rainfall_path = self._get_rainfall_file_path(year)
            if os.path.exists(rainfall_path):
                existing_rainfall_files.append(rainfall_path)
            else:
                missing_rainfall_files.append(rainfall_path)
            rsei_path = self._get_rsei_file_path(year)
            if os.path.exists(rsei_path):
                existing_rsei_files.append(rsei_path)
            else:
                missing_rsei_files.append(rsei_path)
            lucc_path = self._get_lucc_file_path(year)
            if os.path.exists(lucc_path):
                existing_lucc_files.append(lucc_path)
            else:
                missing_lucc_files.append(lucc_path)
        return {
            'existing_temperature': existing_temp_files,
            'missing_temperature': missing_temp_files,
            'existing_rainfall': existing_rainfall_files,
            'missing_rainfall': missing_rainfall_files,
            'existing_rsei': existing_rsei_files,
            'missing_rsei': missing_rsei_files,
            'existing_lucc': existing_lucc_files,
            'missing_lucc': missing_lucc_files
        }
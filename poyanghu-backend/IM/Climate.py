import os
import numpy as np
import rasterio
from typing import Tuple, Dict, List, Optional, Union
import logging
from typing import Tuple, Dict, List, Optional
from sklearn.preprocessing import OneHotEncoder
from Alig import DataAlignmentManager  # 导入数据对齐管理器

LUCC_CLASSES = {
    10: "雨养耕地", 11: "草本植被覆盖", 20: "灌溉耕地",
    51: "开阔常绿阔叶林", 52: "闭阔常绿阔叶林",
    61: "开阔落叶阔叶林(0.15 < fc <0.4)", 62: "闭阔落叶阔叶林(fc > 0.4)",
    71: "开阔常绿针叶林(0.15 < fc < 0.4)", 72: "闭阔常绿针叶林(fc > 0.4)",
    91: "开阔混交叶片林(阔叶树和针叶树)",
    120: "灌木林", 121: "常绿灌木林", 130: "草地",
    150: "稀疏植被(fc < 0.15)", 181: "沼泽", 182: "沼泽地", 183: "水淹平地",
    190: "不透水表面", 200: "裸地", 210: "水体"
}

class ClimateDataService:
    def __init__(self, temperature_dir: str = r"D:/Google/temperture/tpt",
                 rainfall_dir: str = r"D:/Google/rainfall/RF",
                 rsei_dir: str = r"D:/Google/RSEI_full",
                 lucc_dir: str = r"D:/Google/GLC_FCS30/merged"):
        self.temperature_dir = temperature_dir
        self.rainfall_dir = rainfall_dir
        self.rsei_dir = rsei_dir
        self.lucc_dir = lucc_dir
        self.years = list(range(2000, 2023))
        self.alignment_manager = DataAlignmentManager(
            temperature_dir, rainfall_dir, rsei_dir, lucc_dir)
        self._temperature_cache = {}
        self._rainfall_cache = {}
        self._rsei_cache = {}
        self._lucc_cache = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_temperature_file_path(self, year: int) -> str:
        return os.path.join(self.temperature_dir, f"tpt_{year}.tif")

    def _get_rainfall_file_path(self, year: int) -> str:
        return os.path.join(self.rainfall_dir, f"{year}.tif")

    def _get_rsei_file_path(self, year: int) -> str:
        return os.path.join(self.rsei_dir, f"RSEI_{year}.tif")

    def _get_lucc_file_path(self, year: int) -> str:
        return os.path.join(self.lucc_dir, f"poyang_{year}.tif")

    def _load_raster_data(self, file_path: str) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        try:
            with rasterio.open(file_path) as src:
                data = src.read(1)
                profile = src.profile
                if src.nodata is not None:
                    data = np.where(data == src.nodata, np.nan, data)
                data = np.where(np.abs(data) > 1e4, np.nan, data)
                return data, profile
        except Exception as e:
            self.logger.error(f"加载栅格数据失败: {file_path}, 错误: {str(e)}")
            raise

    def from_data_to_mask(self, data: np.ndarray, threshold: float = 0) -> np.ndarray:
        return (~np.isnan(data)) & (data > threshold)

    def from_bounds_to_mask(self, data: np.ndarray, bounds: Tuple[float, float]) -> np.ndarray:
        return (~np.isnan(data)) & (data >= bounds[0]) & (data <= bounds[1])

    def get_temperature_data(self, year: int,mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        if year in self._temperature_cache:
            return self._temperature_cache[year]
        aligned_path = self.alignment_manager.get_aligned_data_path('temperature', year)
        data, profile = self._load_raster_data(aligned_path)
        self._temperature_cache[year] = (data, profile)
        if mask is not None:
            realdata = data[mask]
        else:
            realdata = data.flatten()
        valid_mask = ~np.isnan(realdata)
        realdata = realdata[valid_mask].astype(int).reshape(-1, 1)
        return realdata, profile
        # return data, profile

    def get_rainfall_data(self, year: int,mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        if year in self._rainfall_cache:
            return self._rainfall_cache[year]
        aligned_path = self.alignment_manager.get_aligned_data_path('rainfall', year)
        data, profile = self._load_raster_data(aligned_path)
        self._rainfall_cache[year] = (data, profile)
        if mask is not None:
            realdata = data[mask]
        else:
            realdata = data.flatten()
        valid_mask = ~np.isnan(realdata)
        realdata = realdata[valid_mask].astype(int).reshape(-1, 1)
        return realdata, profile
        # return data, profile

    def get_rsei_data(self, year: int,mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        if year in self._rsei_cache:
            return self._rsei_cache[year]
        aligned_path = self.alignment_manager.get_aligned_data_path('rsei', year)
        data, profile = self._load_raster_data(aligned_path)
        self._rsei_cache[year] = (data, profile)
        if mask is not None:
            realdata = data[mask]
        else:
            realdata = data.flatten()
        valid_mask = ~np.isnan(realdata)
        realdata = realdata[valid_mask].astype(int).reshape(-1, 1)
        return realdata, profile
        # return data, profile

    def get_lucc_data(self, year: int, mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        if year in self._lucc_cache:
            data, profile = self._lucc_cache[year]
        else:
            aligned_path = self.alignment_manager.get_aligned_data_path('lucc', year)
            data, profile = self._load_raster_data(aligned_path)
            self._lucc_cache[year] = (data, profile)

        if mask is not None:
            realdata = data[mask]
        else:
            realdata = data.flatten()

        valid_mask = ~np.isnan(realdata)
        realdata = realdata[valid_mask].astype(int).reshape(-1, 1)

        encoder = OneHotEncoder(categories='auto', handle_unknown='ignore')
        encoded = encoder.fit_transform(realdata)

        return encoded, profile

    def get_sample_points_data(self, year: int, sample_strategy: str = 'grid',
                               sample_size: Optional[int] = None,
                               mask: Optional[np.ndarray] = None,
                               grid_spacing: int = 10) -> Dict[str, np.ndarray]:
        """
        获取用于GWR分析的样本点数据

        Args:
            year: 年份
            sample_strategy: 采样策略 ('grid', 'random', 'stratified')
            sample_size: 采样数量，如果为None则使用所有有效点
            mask: 可选的掩膜数组
            grid_spacing: 网格采样时的间隔（仅在sample_strategy='grid'时使用）

        Returns:
            包含坐标和各变量值的字典
        """
        try:
            # 获取基础数据和地理参考信息
            temp_data, temp_profile = self._get_cached_or_load_data('temperature', year)
            rainfall_data, _ = self._get_cached_or_load_data('rainfall', year)
            rsei_data, _ = self._get_cached_or_load_data('rsei', year)
            lucc_data, _ = self._get_cached_or_load_data('lucc', year)

            # 获取地理变换参数
            transform = temp_profile['transform']
            height, width = temp_data.shape

            # 生成坐标网格
            rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')

            # 将像素坐标转换为地理坐标
            x_coords, y_coords = rasterio.transform.xy(transform, rows.flatten(), cols.flatten())
            x_coords = np.array(x_coords)
            y_coords = np.array(y_coords)

            # 展平所有数据
            temp_flat = temp_data.flatten()
            rainfall_flat = rainfall_data.flatten()
            rsei_flat = rsei_data.flatten()
            lucc_flat = lucc_data.flatten()

            # 应用掩膜
            if mask is not None:
                mask_flat = mask.flatten()
                valid_mask = (~np.isnan(temp_flat)) & (~np.isnan(rainfall_flat)) & \
                             (~np.isnan(rsei_flat)) & (~np.isnan(lucc_flat)) & mask_flat
            else:
                valid_mask = (~np.isnan(temp_flat)) & (~np.isnan(rainfall_flat)) & \
                             (~np.isnan(rsei_flat)) & (~np.isnan(lucc_flat))

            # 筛选有效数据
            valid_indices = np.where(valid_mask)[0]

            if len(valid_indices) == 0:
                self.logger.warning(f"年份 {year} 没有有效的样本点数据")
                return {}

            # 根据采样策略选择样本点
            if sample_strategy == 'grid':
                sample_indices = self._grid_sampling(valid_indices, rows.flatten(),
                                                     cols.flatten(), height, width, grid_spacing)
            elif sample_strategy == 'random':
                sample_indices = self._random_sampling(valid_indices, sample_size)
            elif sample_strategy == 'stratified':
                sample_indices = self._stratified_sampling(valid_indices, lucc_flat, sample_size)
            else:
                sample_indices = valid_indices

            # 提取样本点数据
            sample_points = {
                'x_coords': x_coords[sample_indices],
                'y_coords': y_coords[sample_indices],
                'temperature': temp_flat[sample_indices],
                'rainfall': rainfall_flat[sample_indices],
                'rsei': rsei_flat[sample_indices],
                'lucc': lucc_flat[sample_indices],
                'pixel_row': rows.flatten()[sample_indices],
                'pixel_col': cols.flatten()[sample_indices]
            }

            self.logger.info(f"成功提取 {len(sample_indices)} 个样本点数据 (年份: {year})")
            return sample_points

        except Exception as e:
            self.logger.error(f"获取样本点数据失败 (年份: {year}): {str(e)}")
            raise

    def _get_cached_or_load_data(self, data_type: str, year: int) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
        """
        获取缓存的数据或加载新数据
        """
        cache_dict = getattr(self, f'_{data_type}_cache')
        if year in cache_dict:
            return cache_dict[year]

        aligned_path = self.alignment_manager.get_aligned_data_path(data_type, year)
        data, profile = self._load_raster_data(aligned_path)
        cache_dict[year] = (data, profile)
        return data, profile

    def _grid_sampling(self, valid_indices: np.ndarray, rows: np.ndarray,
                       cols: np.ndarray, height: int, width: int, spacing: int) -> np.ndarray:
        """
        网格采样策略
        """
        grid_rows = np.arange(0, height, spacing)
        grid_cols = np.arange(0, width, spacing)

        sample_indices = []
        for row in grid_rows:
            for col in grid_cols:
                # 找到最接近网格点的有效像素
                pixel_idx = row * width + col
                if pixel_idx in valid_indices:
                    sample_indices.append(pixel_idx)

        return np.array(sample_indices) if sample_indices else valid_indices[:1000]

    def _random_sampling(self, valid_indices: np.ndarray, sample_size: Optional[int]) -> np.ndarray:
        """
        随机采样策略
        """
        if sample_size is None or sample_size >= len(valid_indices):
            return valid_indices

        return np.random.choice(valid_indices, size=sample_size, replace=False)

    def _stratified_sampling(self, valid_indices: np.ndarray, lucc_data: np.ndarray,
                             sample_size: Optional[int]) -> np.ndarray:
        """
        基于土地利用类型的分层采样策略
        """
        if sample_size is None:
            return valid_indices

        # 获取各土地利用类型及其像素数量
        lucc_valid = lucc_data[valid_indices]
        unique_classes, class_counts = np.unique(lucc_valid, return_counts=True)

        # 计算每个类别的采样数量（按比例分配）
        total_pixels = len(valid_indices)
        sample_indices = []

        for lucc_class, count in zip(unique_classes, class_counts):
            class_ratio = count / total_pixels
            class_sample_size = max(1, int(sample_size * class_ratio))

            # 获取该类别的所有像素索引
            class_indices = valid_indices[lucc_valid == lucc_class]

            # 随机选择该类别的样本
            if len(class_indices) <= class_sample_size:
                sample_indices.extend(class_indices)
            else:
                selected = np.random.choice(class_indices, size=class_sample_size, replace=False)
                sample_indices.extend(selected)

        return np.array(sample_indices)

    def get_multivariate_sample_points(self, years: List[int],
                                       sample_strategy: str = 'grid',
                                       sample_size: Optional[int] = None,
                                       mask: Optional[np.ndarray] = None) -> Dict[int, Dict[str, np.ndarray]]:
        """
        获取多年份的样本点数据，用于时间序列GWR分析

        Args:
            years: 年份列表
            sample_strategy: 采样策略
            sample_size: 每年的采样数量
            mask: 可选的掩膜数组

        Returns:
            按年份组织的样本点数据字典
        """
        multivariate_data = {}

        for year in years:
            try:
                sample_data = self.get_sample_points_data(
                    year=year,
                    sample_strategy=sample_strategy,
                    sample_size=sample_size,
                    mask=mask
                )
                if sample_data:  # 确保数据不为空
                    multivariate_data[year] = sample_data
                    self.logger.info(f"成功获取年份 {year} 的样本点数据")
            except Exception as e:
                self.logger.error(f"获取年份 {year} 样本点数据失败: {str(e)}")
                continue

        return multivariate_data
    # def get_sample_points(self, year: int, variable: str, sample_size: Optional[int] = None,
    #                       random_state: Optional[int] = None) -> Dict[str, Union[np.ndarray, List]]:
    #     """
    #     获取样本点数据（x, y坐标及对应变量值）
    #
    #     参数:
    #         year: 年份
    #         variable: 变量名称 ('temperature', 'rainfall', 'rsei', 'lucc')
    #         sample_size: 采样点数，None表示全部有效点
    #         random_state: 随机种子
    #
    #     返回:
    #         包含以下键的字典:
    #             'x': x坐标数组
    #             'y': y坐标数组
    #             'values': 变量值数组
    #             'profile': 栅格profile信息
    #     """
    #     # 获取变量数据
    #     if variable == 'temperature':
    #         data, profile = self.get_temperature_data(year)
    #     elif variable == 'rainfall':
    #         data, profile = self.get_rainfall_data(year)
    #     elif variable == 'rsei':
    #         data, profile = self.get_rsei_data(year)
    #     elif variable == 'lucc':
    #         data, profile = self.get_lucc_data(year)
    #     else:
    #         raise ValueError(f"未知变量: {variable}")
    #
    #     # 获取原始数据（未展平）
    #     if variable in self._temperature_cache:
    #         raw_data = self._temperature_cache[year][0]
    #     elif variable in self._rainfall_cache:
    #         raw_data = self._rainfall_cache[year][0]
    #     elif variable in self._rsei_cache:
    #         raw_data = self._rsei_cache[year][0]
    #     elif variable in self._lucc_cache:
    #         raw_data = self._lucc_cache[year][0]
    #     else:
    #         raise ValueError("无法找到原始数据")
    #
    #     # 创建有效点掩码
    #     valid_mask = ~np.isnan(raw_data)
    #     rows, cols = np.where(valid_mask)
    #
    #     # 转换为地理坐标
    #     transform = profile['transform']
    #     x_coords = transform * (cols, rows)
    #     y_coords = transform * (cols, rows + 1)
    #     x = x_coords[0]
    #     y = y_coords[1]
    #
    #     # 获取有效点的值
    #     values = raw_data[valid_mask]
    #
    #     # 如果需要采样
    #     if sample_size is not None and sample_size < len(values):
    #         rng = np.random.default_rng(random_state)
    #         indices = rng.choice(len(values), size=sample_size, replace=False)
    #         x = x[indices]
    #         y = y[indices]
    #         values = values[indices]
    #
    #     return {
    #         'x': x,
    #         'y': y,
    #         'values': values,
    #         'profile': profile
    #     }
    #
    # def get_multi_variable_sample_points(self, year: int, variables: List[str],
    #                                      sample_size: Optional[int] = None,
    #                                      random_state: Optional[int] = None) -> Dict[str, Union[np.ndarray, List]]:
    #     """
    #     获取多个变量的样本点数据（x, y坐标及对应变量值）
    #
    #     参数:
    #         year: 年份
    #         variables: 变量名称列表 (['temperature', 'rainfall', 'rsei', 'lucc']中的组合)
    #         sample_size: 采样点数，None表示全部有效点
    #         random_state: 随机种子
    #
    #     返回:
    #         包含以下键的字典:
    #             'x': x坐标数组
    #             'y': y坐标数组
    #             'values': 变量值字典 {变量名: 值数组}
    #             'profile': 栅格profile信息
    #     """
    #     if not variables:
    #         raise ValueError("至少需要一个变量")
    #
    #     # 获取第一个变量的样本点作为基准
    #     base_points = self.get_sample_points(year, variables[0], sample_size, random_state)
    #     x = base_points['x']
    #     y = base_points['y']
    #     profile = base_points['profile']
    #
    #     # 获取所有变量的值
    #     values_dict = {}
    #     for var in variables:
    #         if var == variables[0]:
    #             values_dict[var] = base_points['values']
    #         else:
    #             var_data = self.get_sample_points(year, var, sample_size=None, random_state=None)
    #             # 确保坐标对齐
    #             if not np.allclose(x, var_data['x']) or not np.allclose(y, var_data['y']):
    #                 raise ValueError(f"变量{var}的坐标与{variables[0]}不匹配")
    #             values_dict[var] = var_data['values']
    #
    #     # 如果需要采样
    #     if sample_size is not None and sample_size < len(x):
    #         rng = np.random.default_rng(random_state)
    #         indices = rng.choice(len(x), size=sample_size, replace=False)
    #         x = x[indices]
    #         y = y[indices]
    #         for var in values_dict:
    #             values_dict[var] = values_dict[var][indices]
    #
    #     return {
    #         'x': x,
    #         'y': y,
    #         'values': values_dict,
    #         'profile': profile
    #     }

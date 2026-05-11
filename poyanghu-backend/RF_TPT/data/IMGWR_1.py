import os
import numpy as np
import rasterio
import rasterio.warp
from typing import Dict, List, Tuple, Optional
import logging
from IMData import ClimateDataService
from libpysal.weights import DistanceBand
from esda.moran import Moran
from statsmodels.stats.outliers_influence import variance_inflation_factor
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from sklearn.preprocessing import OneHotEncoder
import sklearn


class GWRService:
    """
    地理加权回归（GWR）分析服务类
    功能：分析RSEI与温度、降水和土地覆盖（LUCC）的空间关系
    依赖：ClimateDataService类提供数据
    """

    def __init__(self, climate_service: ClimateDataService, output_dir: str = r"D:/Google/gwr_results"):
        """
        初始化GWR服务
        Args:
            climate_service: ClimateDataService实例
            output_dir: GWR结果输出目录
        """
        self.climate_service = climate_service
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def align_rasters(self, reference_year: int = 2000) -> None:
        """
        对齐温度、降水、RSEI和LUCC栅格的投影、分辨率和范围，以参考年份为基准
        Args:
            reference_year: 参考年份（默认2000）
        """
        try:
            ref_data, ref_profile = self.climate_service.get_rsei_data(reference_year)
            ref_crs = ref_profile['crs']
            ref_transform = ref_profile['transform']
            ref_shape = ref_data.shape
            for year in self.climate_service.get_available_years():
                for data_type, cache in [
                    ('temperature', self.climate_service._temperature_cache),
                    ('rainfall', self.climate_service._rainfall_cache),
                    ('rsei', self.climate_service._rsei_cache),
                    ('lucc', self.climate_service._lucc_cache)
                ]:
                    data, profile = getattr(self.climate_service, f"get_{data_type}_data")(year)
                    file_path = getattr(self.climate_service, f"_get_{data_type}_file_path")(year)
                    self.logger.info(f"Processing {data_type} file: {file_path}")
                    if profile['crs'] != ref_crs or data.shape != ref_shape:
                        self.logger.info(f"Reprojecting {data_type} for year {year}")
                        destination = np.empty(ref_shape, dtype=data.dtype)
                        try:
                            rasterio.warp.reproject(
                                source=data,
                                destination=destination,
                                src_transform=profile['transform'],
                                src_crs=profile['crs'],
                                dst_crs=ref_crs,
                                dst_transform=ref_transform,
                                dst_shape=ref_shape,
                                resampling=rasterio.warp.Resampling.bilinear
                            )
                            data = destination
                            profile.update({
                                'crs': ref_crs,
                                'transform': ref_transform,
                                'height': ref_shape[0],
                                'width': ref_shape[1]
                            })
                            cache[year] = (data, profile)
                            self.logger.info(f"年份 {year} 的 {data_type} 数据已对齐")
                        except Exception as e:
                            self.logger.error(f"Reprojection failed for {data_type} file {file_path}: {str(e)}")
                            raise
                    else:
                        self.logger.info(f"年份 {year} 的 {data_type} 数据无需对齐")
            self.logger.info(f"所有栅格数据已对齐至 {reference_year} 年的投影和分辨率")
        except Exception as e:
            self.logger.error(f"栅格对齐失败: {str(e)}")
            raise

    # def get_gwr_input_data(self, year: int, include_lucc: bool = True, lucc_encoding: str = 'continuous') -> Tuple[
    #     np.ndarray, np.ndarray, np.ndarray]:
    #     """
    #     提取GWR输入数据（坐标、RSEI、温度、降水、LUCC）
    #     Args:
    #         year: 年份
    #         include_lucc: 是否包含LUCC作为自变量
    #         lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
    #     Returns:
    #         Tuple[坐标数组 (n, 2), 因变量数组 (n, 1), 自变量数组 (n, k)]
    #     """
    #     try:
    #         # 获取数据并检查形状一致性
    #         rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)
    #         temp_data, temp_profile = self.climate_service.get_temperature_data(year)
    #         rain_data, rain_profile = self.climate_service.get_rainfall_data(year)
    #         if not (rsei_data.shape == temp_data.shape == rain_data.shape):
    #             raise ValueError("栅格数据形状不一致，请先运行 align_rasters()")
    #
    #         # 创建初始有效掩码并记录有效像素索引
    #         valid_mask = (~np.isnan(rsei_data)) & (~np.isnan(temp_data)) & (~np.isnan(rain_data))
    #         valid_indices = np.where(valid_mask)
    #         valid_rows, valid_cols = valid_indices[0], valid_indices[1]
    #         n_valid = len(valid_rows)
    #
    #         # 提取有效像素数据
    #         rsei_valid = rsei_data[valid_mask].reshape(-1, 1)
    #         temp_valid = temp_data[valid_mask].reshape(-1, 1)
    #         rain_valid = rain_data[valid_mask].reshape(-1, 1)
    #         X = np.hstack([temp_valid, rain_valid])
    #
    #         if include_lucc:
    #             lucc_data, lucc_profile = self.climate_service.get_lucc_data(year)
    #             if lucc_data.shape != rsei_data.shape:
    #                 raise ValueError("LUCC栅格形状不一致")
    #             lucc_valid = lucc_data[valid_mask].reshape(-1, 1)
    #
    #             if lucc_encoding == 'continuous':
    #                 # 转换为连续变量（标准化到0-1）
    #                 max_lucc = np.nanmax(lucc_valid)
    #                 lucc_valid = lucc_valid / max_lucc if max_lucc != 0 else lucc_valid
    #             elif lucc_encoding == 'dummy':
    #                 # 使用OneHotEncoder进行哑变量编码
    #                 try:
    #                     if float(sklearn.__version__.split('.')[0]) >= 1 or \
    #                             (float(sklearn.__version__.split('.')[0]) == 1 and float(
    #                                 sklearn.__version__.split('.')[1]) >= 2):
    #                         encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    #                     else:
    #                         encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
    #                     lucc_valid = encoder.fit_transform(lucc_valid)
    #                 except Exception as e:
    #                     self.logger.error(f"LUCC编码失败: {str(e)}")
    #                     raise
    #
    #             # 更新有效像素掩码（处理LUCC的NaN值）
    #             lucc_non_nan = ~np.isnan(lucc_valid).any(axis=1)
    #             valid_indices = (valid_rows[lucc_non_nan], valid_cols[lucc_non_nan])
    #             rsei_valid = rsei_valid[lucc_non_nan]
    #             X = X[lucc_non_nan]
    #             lucc_valid = lucc_valid[lucc_non_nan]
    #             X = np.hstack([X, lucc_valid])
    #
    #             # 更新2D valid_mask
    #             valid_mask = np.zeros_like(valid_mask, dtype=bool)
    #             valid_mask[valid_indices] = True
    #
    #         # 生成坐标
    #         transform = rsei_profile['transform']
    #         coords = np.array(
    #             [rasterio.transform.xy(transform, r, c) for r, c in zip(valid_indices[0], valid_indices[1])])
    #
    #         self.logger.info(
    #             f"GWR输入数据提取完成: year={year}, coords={coords.shape}, y={rsei_valid.shape}, X={X.shape}")
    #         return coords, rsei_valid, X
    #     except Exception as e:
    #         self.logger.error(f"提取GWR输入数据失败: year={year}, 错误: {str(e)}")
    #         raise

    def clip_to_extent(self, data: np.ndarray, profile: dict, extent: Tuple[float, float, float, float]) -> Tuple[
        np.ndarray, np.ndarray, np.ndarray]:
        """
        根据地理范围裁剪栅格数据
        Args:
            data: 栅格数据
            profile: 栅格元数据（带 transform 和 crs）
            extent: 裁剪范围 (minx, miny, maxx, maxy)
        Returns:
            裁剪后的数据，裁剪后的行列索引（row_idx, col_idx），裁剪掩码
        """
        minx, miny, maxx, maxy = extent
        transform = profile['transform']
        height, width = data.shape

        # 地理坐标转换为行列索引
        row_min, col_min = ~transform * (minx, maxy)
        row_max, col_max = ~transform * (maxx, miny)

        row_min = int(max(0, np.floor(row_min)))
        col_min = int(max(0, np.floor(col_min)))
        row_max = int(min(height, np.ceil(row_max)))
        col_max = int(min(width, np.ceil(col_max)))

        clipped_data = data[row_min:row_max, col_min:col_max]
        return clipped_data, (row_min, col_min), (row_max - row_min, col_max - col_min)

    # def get_gwr_input_data_by_extent(self, year: int, extent: Tuple[float, float, float, float],
    #                                  include_lucc: bool = True, lucc_encoding: str = 'continuous') -> Tuple[
    #     np.ndarray, np.ndarray, np.ndarray]:
    #     """
    #     提取给定空间范围内的GWR输入数据
    #     Args:
    #         year: 年份
    #         extent: 空间范围 (minx, miny, maxx, maxy)
    #         include_lucc: 是否包含LUCC
    #         lucc_encoding: LUCC编码方式
    #     Returns:
    #         coords, y, X
    #     """
    #     try:
    #         # 加载并裁剪数据
    #         rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)
    #         rsei_clip, offset, shape = self.clip_to_extent(rsei_data, rsei_profile, extent)
    #
    #         temp_data, _ = self.climate_service.get_temperature_data(year)
    #         temp_clip = temp_data[offset[0]:offset[0] + shape[0], offset[1]:offset[1] + shape[1]]
    #
    #         rain_data, _ = self.climate_service.get_rainfall_data(year)
    #         rain_clip = rain_data[offset[0]:offset[0] + shape[0], offset[1]:offset[1] + shape[1]]
    #
    #         valid_mask = (~np.isnan(rsei_clip)) & (~np.isnan(temp_clip)) & (~np.isnan(rain_clip))
    #         valid_rows, valid_cols = np.where(valid_mask)
    #
    #         rsei_valid = rsei_clip[valid_mask].reshape(-1, 1)
    #         temp_valid = temp_clip[valid_mask].reshape(-1, 1)
    #         rain_valid = rain_clip[valid_mask].reshape(-1, 1)
    #         X = np.hstack([temp_valid, rain_valid])
    #
    #         if include_lucc:
    #             lucc_data, _ = self.climate_service.get_lucc_data(year)
    #             lucc_clip = lucc_data[offset[0]:offset[0] + shape[0], offset[1]:offset[1] + shape[1]]
    #             lucc_valid = lucc_clip[valid_mask].reshape(-1, 1)
    #
    #             if lucc_encoding == 'continuous':
    #                 max_lucc = np.nanmax(lucc_valid)
    #                 lucc_valid = lucc_valid / max_lucc if max_lucc != 0 else lucc_valid
    #             elif lucc_encoding == 'dummy':
    #                 if float(sklearn.__version__.split('.')[0]) >= 1 or \
    #                         (float(sklearn.__version__.split('.')[0]) == 1 and float(
    #                             sklearn.__version__.split('.')[1]) >= 2):
    #                     encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    #                 else:
    #                     encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
    #                 lucc_valid = encoder.fit_transform(lucc_valid)
    #
    #             X = np.hstack([X, lucc_valid])
    #
    #         # 生成坐标
    #         transform = rsei_profile['transform']
    #         coords = np.array([rasterio.transform.xy(transform, r + offset[0], c + offset[1])
    #                            for r, c in zip(valid_rows, valid_cols)])
    #
    #         self.logger.info(
    #             f"区域GWR数据提取完成: year={year}, extent={extent}, coords={coords.shape}, y={rsei_valid.shape}, X={X.shape}")
    #         return coords, rsei_valid, X
    #     except Exception as e:
    #         self.logger.error(f"区域GWR数据提取失败: year={year}, extent={extent}, 错误: {str(e)}")
    #         raise

    def calculate_morans_i(self, year: int, variable: str = 'rsei', threshold: float = 1000,
                           lucc_encoding: str = 'continuous') -> Dict[str, float]:
        """
        计算指定变量的Moran’s I（空间自相关性）
        Args:
            year: 年份
            variable: 变量名 ('rsei', 'temperature', 'rainfall', 'lucc')
            threshold: 距离阈值（米，默认为1000）
            lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
        Returns:
            包含Moran’s I和p值的字典
        """
        try:
            coords, y, X = self.get_gwr_input_data(year, include_lucc=True, lucc_encoding=lucc_encoding)
            if variable == 'rsei':
                data = y.flatten()
            elif variable == 'temperature':
                data = X[:, 0]
            elif variable == 'rainfall':
                data = X[:, 1]
            elif variable == 'lucc':
                if lucc_encoding == 'dummy' and X.shape[1] > 3:
                    raise ValueError("Moran's I不支持多列LUCC哑变量，请使用continuous编码或选择单一LUCC类别")
                data = X[:, 2]  # 假设使用连续编码或单一类别
            else:
                raise ValueError(f"不支持的变量: {variable}")
            w = DistanceBand(coords, threshold=threshold, binary=True)
            moran = Moran(data, w)
            return {
                'morans_i': float(moran.I),
                'p_value': float(moran.p_sim),
                'variable': variable,
                'year': year
            }
        except Exception as e:
            self.logger.error(f"Moran’s I计算失败: year={year}, variable={variable}, 错误: {str(e)}")
            raise



    def calculate_vif(self, year: int, include_lucc: bool = True, lucc_encoding: str = 'continuous') -> Dict[
        str, float]:
        """
        计算温度、降水和LUCC的VIF（方差膨胀因子）
        Args:
            year: 年份
            include_lucc: 是否包含LUCC
            lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
        Returns:
            包含VIF值的字典
        """
        try:
            _, _, X = self.get_gwr_input_data(year, include_lucc=include_lucc, lucc_encoding=lucc_encoding)
            vif_results = {}
            var_names = ['temperature', 'rainfall'] + (
                ['lucc'] if include_lucc and lucc_encoding == 'continuous' else [])
            if lucc_encoding == 'dummy' and include_lucc:
                for i in range(2, X.shape[1]):
                    var_names.append(f"lucc_category_{i - 2}")
            for i, var in enumerate(var_names):
                vif = variance_inflation_factor(X, i)
                vif_results[f"{var}_vif"] = float(vif)
            vif_results['year'] = year
            return vif_results
        except Exception as e:
            self.logger.error(f"VIF计算失败: year={year}, 错误: {str(e)}")
            raise

    # def run_gwr(self, year: int, include_lucc: bool = True, bw: Optional[float] = None,
    #             lucc_encoding: str = 'continuous', extent: Optional[Tuple[float, float, float, float]] = None) -> Dict:
    #     """
    #     运行GWR模型，分析RSEI与温度、降水和LUCC的关系
    #     Args:
    #         year: 年份
    #         include_lucc: 是否包含LUCC作为自变量
    #         bw: 带宽（可选，若为None则自动选择）
    #         lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
    #     Returns:
    #         包含GWR结果的字典（局部系数、R²、诊断统计）
    #     """
    #     try:
    #         if extent:
    #             coords, y, X = self.get_gwr_input_data_by_extent(year, extent, include_lucc, lucc_encoding)
    #         else:
    #             coords, y, X = self.get_gwr_input_data(year, include_lucc, lucc_encoding)
    #         # coords, y, X = self.get_gwr_input_data(year, include_lucc=include_lucc, lucc_encoding=lucc_encoding)
    #         X_mean, X_std = X.mean(axis=0), X.std(axis=0)
    #         y_mean, y_std = y.mean(), y.std()
    #         X_stdized = (X - X_mean) / X_std
    #         y_stdized = (y - y_mean) / y_std
    #         if bw is None:
    #             selector = Sel_BW(coords, y_stdized, X_stdized, kernel='gaussian')
    #             bw = selector.search(criterion='AICc')
    #         gwr_model = GWR(coords, y_stdized, X_stdized, bw=bw, kernel='gaussian')
    #         results = gwr_model.fit()
    #         return {
    #             'local_coefficients': results.params,  # 局部系数（截距、温度、降水、LUCC）
    #             'local_r2': results.localR2,  # 局部R²
    #             't_values': results.tvalues,  # t统计量
    #             'aic': results.aicc,  # AICc
    #             'bandwidth': bw,
    #             'coords': coords,
    #             'year': year
    #         }
    #     except Exception as e:
    #         self.logger.error(f"GWR分析失败: year={year}, 错误: {str(e)}")
    #         raise

    def run_gwr(self, year: int, include_lucc: bool = True, bw: Optional[float] = None,
                lucc_encoding: str = 'continuous', extent: Optional[Tuple[float, float, float, float]] = None) -> Dict:
        """
        运行GWR模型，分析RSEI与温度、降水和LUCC的关系
        Args:
            year: 年份
            include_lucc: 是否包含LUCC作为自变量
            bw: 带宽（可选，若为None则自动选择）
            lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
            extent: 可选的分析区域范围 (minx, miny, maxx, maxy)
        Returns:
            包含GWR结果的字典（局部系数、R²、诊断统计）
        """
        try:
            # Step 1: 获取输入数据
            if extent:
                coords, y, X = self.get_gwr_input_data_by_extent(year, extent, include_lucc, lucc_encoding)
            else:
                coords, y, X = self.get_gwr_input_data(year, include_lucc, lucc_encoding)

            # Step 2: Reshape 并过滤 NaN 和非法值
            y = y.reshape(-1, 1)
            X = X.reshape(-1, X.shape[-1])
            coords = coords.reshape(-1, 2)

            # 过滤含有 NaN 或 inf 的行
            valid_mask = (
                    ~np.isnan(y).flatten() &
                    ~np.isnan(X).any(axis=1) &
                    ~np.isinf(y).flatten() &
                    ~np.isinf(X).any(axis=1)
            )
            y = y[valid_mask]
            X = X[valid_mask]
            coords = coords[valid_mask]

            if len(y) == 0:
                raise ValueError("所有数据都被过滤，未找到有效样本点用于GWR分析")

            # Step 3: 标准化
            X_mean, X_std = X.mean(axis=0), X.std(axis=0)
            y_mean, y_std = y.mean(), y.std()
            X_stdized = (X - X_mean) / X_std
            y_stdized = (y - y_mean) / y_std

            # Step 4: 选择或使用指定的带宽
            if bw is None:
                selector = Sel_BW(coords, y_stdized, X_stdized, kernel='gaussian')
                bw = selector.search(criterion='AICc')

            # Step 5: 拟合 GWR 模型
            gwr_model = GWR(coords, y_stdized, X_stdized, bw=bw, kernel='gaussian')
            results = gwr_model.fit()

            return {
                'local_coefficients': results.params,  # 局部系数（截距、温度、降水、LUCC）
                'local_r2': results.localR2,  # 局部R²
                't_values': results.tvalues,  # t统计量
                'aic': results.aicc,  # AICc
                'bandwidth': bw,
                'coords': coords,
                'year': year
            }

        except Exception as e:
            self.logger.error(f"GWR分析失败: year={year}, 错误: {str(e)}")
            raise

    def save_gwr_results(self, gwr_results: Dict, year: int) -> None:
        """
        将GWR结果保存为栅格（局部系数、R²）
        Args:
            gwr_results: GWR结果字典
            year: 年份
        """
        try:
            _, ref_profile = self.climate_service.get_rsei_data(year)
            shape = (ref_profile['height'], ref_profile['width'])
            coef_temp = np.full(shape, np.nan)
            coef_rain = np.full(shape, np.nan)
            coef_lucc = np.full(shape, np.nan)
            local_r2 = np.full(shape, np.nan)
            coords = gwr_results['coords']
            rows, cols = [], []
            for coord in coords:
                col, row = ~ref_profile['transform'] * (coord[0], coord[1])
                rows.append(int(row))
                cols.append(int(col))
            for i, (r, c) in enumerate(zip(rows, cols)):
                coef_temp[r, c] = gwr_results['local_coefficients'][i, 1]  # 温度系数
                coef_rain[r, c] = gwr_results['local_coefficients'][i, 2]  # 降水系数
                if gwr_results['local_coefficients'].shape[1] > 3:  # 如果包含LUCC
                    coef_lucc[r, c] = gwr_results['local_coefficients'][i, 3]  # LUCC系数（第一类别）
                local_r2[r, c] = gwr_results['local_r2'][i]
            for name, data in [
                ('coef_temperature', coef_temp),
                ('coef_rainfall', coef_rain),
                ('coef_lucc', coef_lucc),
                ('local_r2', local_r2)
            ]:
                if name == 'coef_lucc' and np.all(np.isnan(data)):
                    continue
                output_path = os.path.join(self.output_dir, f"gwr_{name}_{year}.tif")
                with rasterio.open(output_path, 'w', **ref_profile) as dst:
                    dst.write(data, 1)
            self.logger.info(f"GWR结果已保存至: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"GWR结果保存失败: year={year}, 错误: {str(e)}")
            raise

    def get_gwr_input_data(self, year: int, include_lucc: bool = True, lucc_encoding: str = 'continuous') -> Tuple[
        np.ndarray, np.ndarray, np.ndarray]:
        """
        提取GWR输入数据（坐标、RSEI、温度、降水、LUCC）
        Args:
            year: 年份
            include_lucc: 是否包含LUCC作为自变量
            lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
        Returns:
            Tuple[坐标数组 (n, 2), 因变量数组 (n, 1), 自变量数组 (n, k)]
        """
        try:
            # Step 1: 获取基础数据并验证形状一致性
            rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)
            temp_data, _ = self.climate_service.get_temperature_data(year)
            rain_data, _ = self.climate_service.get_rainfall_data(year)
            if not (rsei_data.shape == temp_data.shape == rain_data.shape):
                raise ValueError("栅格数据形状不一致，请先运行 align_rasters()")

            # Step 2: 构造初始有效掩码
            valid_mask = (~np.isnan(rsei_data)) & (~np.isnan(temp_data)) & (~np.isnan(rain_data))
            valid_rows, valid_cols = np.where(valid_mask)

            # Step 3: 提取有效值并构造因变量和基础自变量
            rsei_valid = rsei_data[valid_mask].reshape(-1, 1)
            temp_valid = temp_data[valid_mask].reshape(-1, 1)
            rain_valid = rain_data[valid_mask].reshape(-1, 1)
            X = np.hstack([temp_valid, rain_valid])

            # Step 4: 添加 LUCC 数据（可选）
            if include_lucc:
                lucc_data, _ = self.climate_service.get_lucc_data(year)
                if lucc_data.shape != rsei_data.shape:
                    raise ValueError("LUCC栅格形状不一致")

                lucc_raw = lucc_data[valid_mask].reshape(-1, 1)

                # 将 LUCC 值为 0 的视为无效（设置为 NaN）
                lucc_raw[lucc_raw == 0] = 1

                if lucc_encoding == 'continuous':
                    max_lucc = np.nanmax(lucc_raw)
                    lucc_valid = lucc_raw / max_lucc if max_lucc != 0 else lucc_raw
                elif lucc_encoding == 'dummy':
                    try:
                        if float(sklearn.__version__.split('.')[0]) >= 1 and float(
                                sklearn.__version__.split('.')[1]) >= 2:
                            encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                        else:
                            encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
                        lucc_valid = encoder.fit_transform(lucc_raw)
                    except Exception as e:
                        self.logger.error(f"LUCC编码失败: {str(e)}")
                        raise
                else:
                    raise ValueError(f"不支持的LUCC编码方式: {lucc_encoding}")

                # 过滤掉LUCC中的NaN行
                non_nan_mask = ~np.isnan(lucc_valid).any(axis=1)
                rsei_valid = rsei_valid[non_nan_mask]
                X = X[non_nan_mask]
                lucc_valid = lucc_valid[non_nan_mask]
                valid_rows = valid_rows[non_nan_mask]
                valid_cols = valid_cols[non_nan_mask]

                # 合并LUCC为自变量
                X = np.hstack([X, lucc_valid])

            # Step 5: 去除 X 或 y 中含 NaN/inf 的所有数据行
            combined = np.hstack([rsei_valid, X])
            valid_final_mask = (~np.isnan(combined).any(axis=1)) & (~np.isinf(combined).any(axis=1))
            rsei_valid = rsei_valid[valid_final_mask]
            X = X[valid_final_mask]
            valid_rows = valid_rows[valid_final_mask]
            valid_cols = valid_cols[valid_final_mask]

            # Step 6: 构造坐标数组
            transform = rsei_profile['transform']
            coords = np.array([rasterio.transform.xy(transform, r, c) for r, c in zip(valid_rows, valid_cols)])

            self.logger.info(
                f"GWR输入数据提取完成: year={year}, coords={coords.shape}, y={rsei_valid.shape}, X={X.shape}")
            return coords, rsei_valid, X

        except Exception as e:
            self.logger.error(f"提取GWR输入数据失败: year={year}, 错误: {str(e)}")
            raise

    def get_gwr_input_data_by_extent(self, year: int, extent: Tuple[float, float, float, float],
                                     include_lucc: bool = True, lucc_encoding: str = 'continuous') -> Tuple[
        np.ndarray, np.ndarray, np.ndarray]:
        """
        提取给定空间范围内的GWR输入数据
        Args:
            year: 年份
            extent: 空间范围 (minx, miny, maxx, maxy)
            include_lucc: 是否包含LUCC
            lucc_encoding: LUCC编码方式
        Returns:
            coords, y, X
        """
        try:
            # 1. 加载原始数据
            rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)
            temp_data, _ = self.climate_service.get_temperature_data(year)
            rain_data, _ = self.climate_service.get_rainfall_data(year)
            lucc_data, _ = self.climate_service.get_lucc_data(year) if include_lucc else (None, None)

            # 2. 裁剪到范围
            rsei_clip, offset, shape = self.clip_to_extent(rsei_data, rsei_profile, extent)
            temp_clip = temp_data[offset[0]:offset[0] + shape[0], offset[1]:offset[1] + shape[1]]
            rain_clip = rain_data[offset[0]:offset[0] + shape[0], offset[1]:offset[1] + shape[1]]
            if include_lucc:
                lucc_clip = lucc_data[offset[0]:offset[0] + shape[0], offset[1]:offset[1] + shape[1]]

            # 3. 初步有效掩码
            valid_mask = (~np.isnan(rsei_clip)) & (~np.isnan(temp_clip)) & (~np.isnan(rain_clip))

            if include_lucc:
                lucc_valid = lucc_clip[valid_mask].reshape(-1, 1)
                lucc_valid[lucc_valid == 0] = np.nan  # 屏蔽LUCC为0的像素

                if lucc_encoding == 'continuous':
                    max_lucc = np.nanmax(lucc_valid)
                    lucc_valid = lucc_valid / max_lucc if max_lucc != 0 else lucc_valid
                elif lucc_encoding == 'dummy':
                    try:
                        if float(sklearn.__version__.split('.')[0]) >= 1 and float(
                                sklearn.__version__.split('.')[1]) >= 2:
                            encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                        else:
                            encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
                        lucc_valid = encoder.fit_transform(lucc_valid)
                    except Exception as e:
                        self.logger.error(f"LUCC编码失败: {str(e)}")
                        raise

            # 4. 提取有效像素值
            valid_rows, valid_cols = np.where(valid_mask)
            rsei_valid = rsei_clip[valid_mask].reshape(-1, 1)
            temp_valid = temp_clip[valid_mask].reshape(-1, 1)
            rain_valid = rain_clip[valid_mask].reshape(-1, 1)
            X = np.hstack([temp_valid, rain_valid])

            if include_lucc:
                # 去除包含 NaN 的样本行（来自LUCC）
                combined = np.hstack([rsei_valid, X, lucc_valid])
                non_nan_mask = (~np.isnan(combined).any(axis=1)) & (~np.isinf(combined).any(axis=1))
                rsei_valid = rsei_valid[non_nan_mask]
                X = X[non_nan_mask]
                lucc_valid = lucc_valid[non_nan_mask]
                valid_rows = valid_rows[non_nan_mask]
                valid_cols = valid_cols[non_nan_mask]
                X = np.hstack([X, lucc_valid])
            else:
                # 过滤掉包含 NaN/inf 的样本（无 LUCC 时）
                combined = np.hstack([rsei_valid, X])
                non_nan_mask = (~np.isnan(combined).any(axis=1)) & (~np.isinf(combined).any(axis=1))
                rsei_valid = rsei_valid[non_nan_mask]
                X = X[non_nan_mask]
                valid_rows = valid_rows[non_nan_mask]
                valid_cols = valid_cols[non_nan_mask]

            # 5. 生成坐标
            transform = rsei_profile['transform']
            coords = np.array([
                rasterio.transform.xy(transform, r + offset[0], c + offset[1])
                for r, c in zip(valid_rows, valid_cols)
            ])

            self.logger.info(
                f"区域GWR数据提取完成: year={year}, extent={extent}, coords={coords.shape}, y={rsei_valid.shape}, X={X.shape}")
            return coords, rsei_valid, X

        except Exception as e:
            self.logger.error(f"区域GWR数据提取失败: year={year}, extent={extent}, 错误: {str(e)}")
            raise

# import os
# import numpy as np
# import rasterio
# import rasterio.warp
# from typing import Dict, List, Tuple, Optional
# import logging
# from Climate import ClimateDataService
# from libpysal.weights import DistanceBand
# from esda.moran import Moran
# from statsmodels.stats.outliers_influence import variance_inflation_factor
# from mgwr.gwr import GWR
# from mgwr.sel_bw import Sel_BW
# from sklearn.preprocessing import OneHotEncoder
# import sklearn
#
#
# class GWRService:
#     """
#     地理加权回归（GWR）分析服务类
#     功能：分析RSEI与温度、降水和土地覆盖（LUCC）的空间关系
#     依赖：ClimateDataService类提供数据
#     """
#
#     def __init__(self, climate_service: ClimateDataService, output_dir: str = r"D:/Google/gwr_results"):
#         """
#         初始化GWR服务
#         Args:
#             climate_service: ClimateDataService实例
#             output_dir: GWR结果输出目录
#         """
#         self.climate_service = climate_service
#         self.output_dir = output_dir
#         os.makedirs(output_dir, exist_ok=True)
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
#
#     def align_rasters(self, reference_year: int = 2000) -> None:
#         """
#         对齐温度、降水、RSEI和LUCC栅格的投影、分辨率和范围，以参考年份为基准
#         Args:
#             reference_year: 参考年份（默认2000）
#         """
#         try:
#             ref_data, ref_profile = self.climate_service.get_rsei_data(reference_year)
#             ref_crs = ref_profile['crs']
#             ref_transform = ref_profile['transform']
#             ref_shape = ref_data.shape
#             for year in self.climate_service.get_available_years():
#                 for data_type, cache in [
#                     ('temperature', self.climate_service._temp_cache),
#                     ('rainfall', self.climate_service._rainfall_cache),
#                     ('rsei', self.climate_service._rsei_cache),
#                     ('lucc', self.climate_service._lucc_cache)
#                 ]:
#                     data, profile = getattr(self.climate_service, f"get_{data_type}_data")(year)
#                     file_path = getattr(self.climate_service, f"_get_{data_type}_file_path")(year)
#                     self.logger.info(f"Processing {data_type} file: {file_path}")
#                     if profile['crs'] != ref_crs or data.shape != ref_shape:
#                         self.logger.info(f"Reprojecting {data_type} for year {year}")
#                         destination = np.empty(ref_shape, dtype=data.dtype)
#                         try:
#                             rasterio.warp.reproject(
#                                 source=data,
#                                 destination=destination,
#                                 src_transform=profile['transform'],
#                                 src_crs=profile['crs'],
#                                 dst_crs=ref_crs,
#                                 dst_transform=ref_transform,
#                                 dst_shape=ref_shape,
#                                 resampling=rasterio.warp.Resampling.bilinear
#                             )
#                             data = destination
#                             profile.update({
#                                 'crs': ref_crs,
#                                 'transform': ref_transform,
#                                 'height': ref_shape[0],
#                                 'width': ref_shape[1]
#                             })
#                             cache[year] = (data, profile)
#                             self.logger.info(f"年份 {year} 的 {data_type} 数据已对齐")
#                         except Exception as e:
#                             self.logger.error(f"Reprojection failed for {data_type} file {file_path}: {str(e)}")
#                             raise
#                     else:
#                         self.logger.info(f"年份 {year} 的 {data_type} 数据无需对齐")
#             self.logger.info(f"所有栅格数据已对齐至 {reference_year} 年的投影和分辨率")
#         except Exception as e:
#             self.logger.error(f"栅格对齐失败: {str(e)}")
#             raise
#
#     # def get_gwr_input_data(self, year: int, include_lucc: bool = True, lucc_encoding: str = 'continuous') -> Tuple[
#     #     np.ndarray, np.ndarray, np.ndarray]:
#     #     """
#     #     提取GWR输入数据（坐标、RSEI、温度、降水、LUCC）
#     #     Args:
#     #         year: 年份
#     #         include_lucc: 是否包含LUCC作为自变量
#     #         lucc_encoding: LUCC编码方式 ('continuous' 或 'dummy')
#     #     Returns:
#     #         Tuple[坐标数组 (n, 2), 因变量数组 (n, 1), 自变量数组 (n, k)]
#     #     """
#     #     try:
#     #         rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)
#     #         temp_data, temp_profile = self.climate_service.get_temperature_data(year)
#     #         rain_data, rain_profile = self.climate_service.get_rainfall_data(year)
#     #         if not (rsei_data.shape == temp_data.shape == rain_data.shape):
#     #             raise ValueError("栅格数据形状不一致，请先运行 align_rasters()")
#     #         valid_mask = (~np.isnan(rsei_data)) & (~np.isnan(temp_data)) & (~np.isnan(rain_data))
#     #         rsei_valid = rsei_data[valid_mask].reshape(-1, 1)
#     #         temp_valid = temp_data[valid_mask].reshape(-1, 1)
#     #         rain_valid = rain_data[valid_mask].reshape(-1, 1)
#     #         X = np.hstack([temp_valid, rain_valid])
#     #         if include_lucc:
#     #             lucc_data, lucc_profile = self.climate_service.get_lucc_data(year)
#     #             if lucc_data.shape != rsei_data.shape:
#     #                 raise ValueError("LUCC栅格形状不一致")
#     #             lucc_valid = lucc_data[valid_mask].reshape(-1, 1)
#     #             if lucc_encoding == 'continuous':
#     #                 # 转换为连续变量（假设LUCC为整数分类，标准化到0-1）
#     #                 max_lucc = np.nanmax(lucc_valid)
#     #                 lucc_valid = lucc_valid / max_lucc if max_lucc != 0 else lucc_valid
#     #             elif lucc_encoding == 'dummy':
#     #                 # 使用OneHotEncoder进行哑变量编码
#     #                 try:
#     #                     # Check scikit-learn version for OneHotEncoder parameter
#     #                     if float(sklearn.__version__.split('.')[0]) >= 1 or \
#     #                             (float(sklearn.__version__.split('.')[0]) == 1 and float(
#     #                                 sklearn.__version__.split('.')[1]) >= 2):
#     #                         encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
#     #                     else:
#     #                         encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
#     #                     lucc_valid = encoder.fit_transform(lucc_valid)
#     #                 except Exception as e:
#     #                     self.logger.error(f"LUCC编码失败: {str(e)}")
#     #                     raise
#     #             valid_mask &= ~np.isnan(lucc_valid).any(axis=1)
#     #             X = np.hstack([X, lucc_valid])
#     #         rsei_valid = rsei_valid[valid_mask].reshape(-1, 1)
#     #         X = X[valid_mask]
#     #         rows, cols = np.where(valid_mask)
#     #         transform = rsei_profile['transform']
#     #         coords = np.array([rasterio.transform.xy(transform, r, c) for r, c in zip(rows, cols)])
#     #         return coords, rsei_valid, X
#     #     except Exception as e:
#     #         self.logger.error(f"提取GWR输入数据失败: year={year}, 错误: {str(e)}")
#     #         raise
#
#
#
#     def calculate_morans_i(self, year: int, variable: str = 'rsei', threshold: float = 1000) -> Dict[str, float]:
#         """
#         计算指定变量的Moran’s I（空间自相关性）
#         Args:
#             year: 年份
#             variable: 变量名 ('rsei', 'temperature', 'rainfall', 'lucc')
#             threshold: 距离阈值（米，默认为1000）
#         Returns:
#             包含Moran’s I和p值的字典
#         """
#         try:
#             coords, y, X = self.get_gwr_input_data(year, include_lucc=True, lucc_encoding='continuous')
#             if variable == 'rsei':
#                 data = y.flatten()
#             elif variable == 'temperature':
#                 data = X[:, 0]
#             elif variable == 'rainfall':
#                 data = X[:, 1]
#             elif variable == 'lucc':
#                 data = X[:, 2]  # 假设使用连续编码
#             else:
#                 raise ValueError(f"不支持的变量: {variable}")
#             w = DistanceBand(coords, threshold=threshold, binary=True)
#             moran = Moran(data, w)
#             return {
#                 'morans_i': float(moran.I),
#                 'p_value': float(moran.p_sim),
#                 'variable': variable,
#                 'year': year
#             }
#         except Exception as e:
#             self.logger.error(f"Moran’s I计算失败: year={year}, variable={variable}, 错误: {str(e)}")
#             raise
#
#     def calculate_vif(self, year: int, include_lucc: bool = True) -> Dict[str, float]:
#         """
#         计算温度、降水和LUCC的VIF（方差膨胀因子）
#         Args:
#             year: 年份
#             include_lucc: 是否包含LUCC
#         Returns:
#             包含VIF值的字典
#         """
#         try:
#             _, _, X = self.get_gwr_input_data(year, include_lucc=include_lucc, lucc_encoding='continuous')
#             vif_results = {}
#             for i, var in enumerate(['temperature', 'rainfall'] + (['lucc'] if include_lucc else [])):
#                 vif = variance_inflation_factor(X, i)
#                 vif_results[f"{var}_vif"] = float(vif)
#             vif_results['year'] = year
#             return vif_results
#         except Exception as e:
#             self.logger.error(f"VIF计算失败: year={year}, 错误: {str(e)}")
#             raise
#
#     def run_gwr(self, year: int, include_lucc: bool = True, bw: Optional[float] = None) -> Dict:
#         """
#         运行GWR模型，分析RSEI与温度、降水和LUCC的关系
#         Args:
#             year: 年份
#             include_lucc: 是否包含LUCC作为自变量
#             bw: 带宽（可选，若为None则自动选择）
#         Returns:
#             包含GWR结果的字典（局部系数、R²、诊断统计）
#         """
#         try:
#             coords, y, X = self.get_gwr_input_data(year, include_lucc=include_lucc, lucc_encoding='continuous')
#             X_mean, X_std = X.mean(axis=0), X.std(axis=0)
#             y_mean, y_std = y.mean(), y.std()
#             X_stdized = (X - X_mean) / X_std
#             y_stdized = (y - y_mean) / y_std
#             if bw is None:
#                 selector = Sel_BW(coords, y_stdized, X_stdized, kernel='gaussian')
#                 bw = selector.search(criterion='AICc')
#             gwr_model = GWR(coords, y_stdized, X_stdized, bw=bw, kernel='gaussian')
#             results = gwr_model.fit()
#             return {
#                 'local_coefficients': results.params,  # 局部系数（截距、温度、降水、LUCC）
#                 'local_r2': results.localR2,  # 局部R²
#                 't_values': results.tvalues,  # t统计量
#                 'aic': results.aicc,  # AICc
#                 'bandwidth': bw,
#                 'coords': coords,
#                 'year': year
#             }
#         except Exception as e:
#             self.logger.error(f"GWR分析失败: year={year}, 错误: {str(e)}")
#             raise
#
#     def save_gwr_results(self, gwr_results: Dict, year: int) -> None:
#         """
#         将GWR结果保存为栅格（局部系数、R²）
#         Args:
#             gwr_results: GWR结果字典
#             year: 年份
#         """
#         try:
#             _, ref_profile = self.climate_service.get_rsei_data(year)
#             shape = (ref_profile['height'], ref_profile['width'])
#             coef_temp = np.full(shape, np.nan)
#             coef_rain = np.full(shape, np.nan)
#             coef_lucc = np.full(shape, np.nan)
#             local_r2 = np.full(shape, np.nan)
#             coords = gwr_results['coords']
#             rows, cols = [], []
#             for coord in coords:
#                 col, row = ~ref_profile['transform'] * (coord[0], coord[1])
#                 rows.append(int(row))
#                 cols.append(int(col))
#             for i, (r, c) in enumerate(zip(rows, cols)):
#                 coef_temp[r, c] = gwr_results['local_coefficients'][i, 1]  # 温度系数
#                 coef_rain[r, c] = gwr_results['local_coefficients'][i, 2]  # 降水系数
#                 if gwr_results['local_coefficients'].shape[1] > 3:  # 如果包含LUCC
#                     coef_lucc[r, c] = gwr_results['local_coefficients'][i, 3]  # LUCC系数
#                 local_r2[r, c] = gwr_results['local_r2'][i]
#             for name, data in [
#                 ('coef_temperature', coef_temp),
#                 ('coef_rainfall', coef_rain),
#                 ('coef_lucc', coef_lucc),
#                 ('local_r2', local_r2)
#             ]:
#                 if name == 'coef_lucc' and np.all(np.isnan(data)):
#                     continue
#                 output_path = os.path.join(self.output_dir, f"gwr_{name}_{year}.tif")
#                 with rasterio.open(output_path, 'w', **ref_profile) as dst:
#                     dst.write(data, 1)
#             self.logger.info(f"GWR结果已保存至: {self.output_dir}")
#         except Exception as e:
#             self.logger.error(f"GWR结果保存失败: year={year}, 错误: {str(e)}")
#             raise


# import os
# import numpy as np
# import rasterio
# import rasterio.warp
# from typing import Dict, List, Tuple, Optional
# import logging
# from IMData import ClimateDataService
# from libpysal.weights import DistanceBand
# from esda.moran import Moran
# from statsmodels.stats.outliers_influence import variance_inflation_factor
# from mgwr.gwr import GWR
# from mgwr.sel_bw import Sel_BW
# from sklearn.preprocessing import OneHotEncoder
#
# class GWRService:
#     """
#     地理加权回归（GWR）分析服务类
#     功能：分析RSEI与温度、降水和土地覆盖（LUCC）的空间关系
#     依赖：ClimateDataService类提供数据
#     """
#
#     def __init__(self, climate_service: ClimateDataService, output_dir: str = r"D:/Google/gwr_results"):
#         """
#         初始化GWR服务
#         Args:
#             climate_service: ClimateDataService实例
#             output_dir: GWR结果输出目录
#         """
#         self.climate_service = climate_service
#         self.output_dir = output_dir
#         os.makedirs(output_dir, exist_ok=True)
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)
#
#     def align_rasters(self, reference_year: int = 2000) -> None:
#         """
#         对齐温度、降水、RSEI和LUCC栅格的投影、分辨率和范围，以参考年份为基准
#         Args:
#             reference_year: 参考年份（默认2000）
#         """
#         try:
#             # 获取参考年份的RSEI栅格作为基准
#             ref_data, ref_profile = self.climate_service.get_rsei_data(reference_year)
#             ref_crs = ref_profile['crs']
#             ref_transform = ref_profile['transform']
#             ref_shape = ref_data.shape
#
#             for year in self.climate_service.get_available_years():
#                 for data_type, cache in [
#                     ('temperature', self.climate_service._temp_cache),
#                     ('rainfall', self.climate_service._rainfall_cache),
#                     ('rsei', self.climate_service._rsei_cache),
#                     ('lucc', self.climate_service._lucc_cache)
#                 ]:
#                     data, profile = getattr(self.climate_service, f"get_{data_type}_data")(year)
#                     if profile['crs'] != ref_crs or data.shape != ref_shape:
#                         # 创建目标数组
#                         destination = np.empty(ref_shape, dtype=data.dtype)
#                         # 执行重投影
#                         rasterio.warp.reproject(
#                             source=data,
#                             destination=destination,
#                             src_transform=profile['transform'],
#                             src_crs=profile['crs'],
#                             dst_crs=ref_crs,
#                             dst_transform=ref_transform,
#                             dst_shape=ref_shape,
#                             resampling=rasterio.warp.Resampling.bilinear
#                         )
#                         # 更新数据和profile
#                         data = destination
#                         profile.update({
#                             'crs': ref_crs,
#                             'transform': ref_transform,
#                             'height': ref_shape[0],
#                             'width': ref_shape[1]
#                         })
#                         cache[year] = (data, profile)
#                         self.logger.info(f"年份 {year} 的 {data_type} 数据已对齐")
#                     else:
#                         self.logger.info(f"年份 {year} 的 {data_type} 数据无需对齐")
#             self.logger.info(f"所有栅格数据已对齐至 {reference_year} 年的投影和分辨率")
#         except Exception as e:
#             self.logger.error(f"栅格对齐失败: {str(e)}")
#             raise
#
#     # def align_rasters(self, reference_year: int = 2000) -> None:
#     #     """
#     #     对齐温度、降水、RSEI和LUCC栅格的投影、分辨率和范围，以参考年份为基准
#     #     Args:
#     #         reference_year: 参考年份（默认2000）
#     #     """
#     #     try:
#     #         ref_data, ref_profile = self.climate_service.get_rsei_data(reference_year)
#     #         ref_crs = ref_profile['crs']
#     #         ref_transform = ref_profile['transform']
#     #         ref_shape = ref_data.shape
#     #         for year in self.climate_service.get_available_years():
#     #             for data_type, cache in [
#     #                 ('temperature', self.climate_service._temp_cache),
#     #                 ('rainfall', self.climate_service._rainfall_cache),
#     #                 ('rsei', self.climate_service._rsei_cache),
#     #                 ('lucc', self.climate_service._lucc_cache)
#     #             ]:
#     #                 data, profile = getattr(self.climate_service, f"get_{data_type}_data")(year)
#     #                 if profile['crs'] != ref_crs or data.shape != ref_shape:
#     #                     data, new_transform = rasterio.warp.reproject(
#     #                         source=data,
#     #                         src_transform=profile['transform'],
#     #                         src_crs=profile['crs'],
#     #                         dst_crs=ref_crs,
#     #                         dst_transform=ref_transform,
#     #                         dst_shape=ref_shape,
#     #                         resampling=rasterio.warp.Resampling.bilinear
#     #                     )
#     #                     profile.update({
#     #                         'crs': ref_crs,
#     #                         'transform': new_transform,
#     #                         'height': ref_shape[0],
#     #                         'width': ref_shape[1]
#     #                     })
#     #                     cache[year] = (data, profile)
#     #             self.logger.info(f"年份 {year} 的栅格数据已对齐")
#     #     except Exception as e:
#     #         self.logger.error(f"栅格对齐失败: {str(e)}")
#     #         raise
#
#     def get_gwr_input_data(self, year: int, include_lucc: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
#         """
#         提取GWR输入数据（坐标、RSEI、温度、降水、LUCC）
#         Args:
#             year: 年份
#             include_lucc: 是否包含LUCC作为自变量
#         Returns:
#             Tuple[坐标数组 (n, 2), 因变量数组 (n, 1), 自变量数组 (n, k)]
#         """
#         try:
#             rsei_data, rsei_profile = self.climate_service.get_rsei_data(year)
#             temp_data, temp_profile = self.climate_service.get_temperature_data(year)
#             rain_data, rain_profile = self.climate_service.get_rainfall_data(year)
#             if not (rsei_data.shape == temp_data.shape == rain_data.shape):
#                 raise ValueError("栅格数据形状不一致，请先运行 align_rasters()")
#             valid_mask = (~np.isnan(rsei_data)) & (~np.isnan(temp_data)) & (~np.isnan(rain_data))
#             rsei_valid = rsei_data[valid_mask].reshape(-1, 1)
#             temp_valid = temp_data[valid_mask].reshape(-1, 1)
#             rain_valid = rain_data[valid_mask].reshape(-1, 1)
#             X = np.hstack([temp_valid, rain_valid])
#             # if include_lucc:
#             #     lucc_data, lucc_profile = self.climate_service.get_lucc_data(year)
#             #     if lucc_data.shape != rsei_data.shape:
#             #         raise ValueError("LUCC栅格形状不一致")
#             #     lucc_valid = lucc_data[valid_mask].reshape(-1, 1)
#             #     valid_mask &= ~np.isnan(lucc_valid)
#             #     X = np.hstack([X, lucc_valid])
#             if include_lucc:    # LUCC 是分类数据，添加哑变量编码
#                 lucc_data, _ = self.climate_service.get_lucc_data(year)
#                 lucc_valid = lucc_data[valid_mask].reshape(-1, 1)
#                 encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
#                 lucc_encoded = encoder.fit_transform(lucc_valid)
#                 X = np.hstack([X, lucc_encoded])
#             rsei_valid = rsei_valid[valid_mask].reshape(-1, 1)
#             X = X[valid_mask]
#             rows, cols = np.where(valid_mask)
#             transform = rsei_profile['transform']
#             coords = np.array([rasterio.transform.xy(transform, r, c) for r, c in zip(rows, cols)])
#             return coords, rsei_valid, X
#         except Exception as e:
#             self.logger.error(f"提取GWR输入数据失败: year={year}, 错误: {str(e)}")
#             raise
#
#     def calculate_morans_i(self, year: int, variable: str = 'rsei', threshold: float = 1000) -> Dict[str, float]:
#         """
#         计算指定变量的Moran’s I（空间自相关性）
#         Args:
#             year: 年份
#             variable: 变量名 ('rsei', 'temperature', 'rainfall', 'lucc')
#             threshold: 距离阈值（米，默认为1000）
#         Returns:
#             包含Moran’s I和p值的字典
#         """
#         try:
#             coords, y, X = self.get_gwr_input_data(year, include_lucc=True)
#             if variable == 'rsei':
#                 data = y.flatten()
#             elif variable == 'temperature':
#                 data = X[:, 0]
#             elif variable == 'rainfall':
#                 data = X[:, 1]
#             elif variable == 'lucc':
#                 data = X[:, 2]
#             else:
#                 raise ValueError(f"不支持的变量: {variable}")
#             w = DistanceBand(coords, threshold=threshold, binary=True)
#             moran = Moran(data, w)
#             return {
#                 'morans_i': float(moran.I),
#                 'p_value': float(moran.p_sim),
#                 'variable': variable,
#                 'year': year
#             }
#         except Exception as e:
#             self.logger.error(f"Moran’s I计算失败: year={year}, variable={variable}, 错误: {str(e)}")
#             raise
#
#     def calculate_vif(self, year: int, include_lucc: bool = True) -> Dict[str, float]:
#         """
#         计算温度、降水和LUCC的VIF（方差膨胀因子）
#         Args:
#             year: 年份
#             include_lucc: 是否包含LUCC
#         Returns:
#             包含VIF值的字典
#         """
#         try:
#             _, _, X = self.get_gwr_input_data(year, include_lucc=include_lucc)
#             vif_results = {}
#             for i, var in enumerate(['temperature', 'rainfall'] + (['lucc'] if include_lucc else [])):
#                 vif = variance_inflation_factor(X, i)
#                 vif_results[f"{var}_vif"] = float(vif)
#             vif_results['year'] = year
#             return vif_results
#         except Exception as e:
#             self.logger.error(f"VIF计算失败: year={year}, 错误: {str(e)}")
#             raise
#
#     def run_gwr(self, year: int, include_lucc: bool = True, bw: Optional[float] = None) -> Dict:
#         """
#         运行GWR模型，分析RSEI与温度、降水和LUCC的关系
#         Args:
#             year: 年份
#             include_lucc: 是否包含LUCC作为自变量
#             bw: 带宽（可选，若为None则自动选择）
#         Returns:
#             包含GWR结果的字典（局部系数、R²、诊断统计）
#         """
#         try:
#             coords, y, X = self.get_gwr_input_data(year, include_lucc=include_lucc)
#             X_mean, X_std = X.mean(axis=0), X.std(axis=0)
#             y_mean, y_std = y.mean(), y.std()
#             X_stdized = (X - X_mean) / X_std
#             y_stdized = (y - y_mean) / y_std
#             if bw is None:
#                 selector = Sel_BW(coords, y_stdized, X_stdized, kernel='gaussian')
#                 bw = selector.search(criterion='AICc')
#             gwr_model = GWR(coords, y_stdized, X_stdized, bw=bw, kernel='gaussian')
#             results = gwr_model.fit()
#             return {
#                 'local_coefficients': results.params,  # 局部系数（截距、温度、降水、LUCC）
#                 'local_r2': results.localR2,  # 局部R²
#                 't_values': results.tvalues,  # t统计量
#                 'aic': results.aicc,  # AICc
#                 'bandwidth': bw,
#                 'coords': coords,
#                 'year': year
#             }
#         except Exception as e:
#             self.logger.error(f"GWR分析失败: year={year}, 错误: {str(e)}")
#             raise
#
#     def run_multi_year_gwr(self, start_year: int, end_year: int, include_lucc: bool = True) -> Dict[int, Dict]:
#         results = {}
#         for year in range(start_year, end_year + 1):
#             results[year] = self.run_gwr(year, include_lucc=include_lucc)
#             self.save_gwr_results(results[year], year)
#         return results
#
#     def save_gwr_results(self, gwr_results: Dict, year: int) -> None:
#         """
#         将GWR结果保存为栅格（局部系数、R²）
#         Args:
#             gwr_results: GWR结果字典
#             year: 年份
#         """
#         try:
#             _, ref_profile = self.climate_service.get_rsei_data(year)
#             shape = (ref_profile['height'], ref_profile['width'])
#             coef_temp = np.full(shape, np.nan)
#             coef_rain = np.full(shape, np.nan)
#             coef_lucc = np.full(shape, np.nan)
#             local_r2 = np.full(shape, np.nan)
#             coords = gwr_results['coords']
#             rows, cols = [], []
#             for coord in coords:
#                 col, row = ~ref_profile['transform'] * (coord[0], coord[1])
#                 rows.append(int(row))
#                 cols.append(int(col))
#             for i, (r, c) in enumerate(zip(rows, cols)):
#                 coef_temp[r, c] = gwr_results['local_coefficients'][i, 1]  # 温度系数
#                 coef_rain[r, c] = gwr_results['local_coefficients'][i, 2]  # 降水系数
#                 if gwr_results['local_coefficients'].shape[1] > 3:  # 如果包含LUCC
#                     coef_lucc[r, c] = gwr_results['local_coefficients'][i, 3]  # LUCC系数
#                 local_r2[r, c] = gwr_results['local_r2'][i]
#             for name, data in [
#                 ('coef_temperature', coef_temp),
#                 ('coef_rainfall', coef_rain),
#                 ('coef_lucc', coef_lucc),
#                 ('local_r2', local_r2)
#             ]:
#                 if name == 'coef_lucc' and np.all(np.isnan(data)):
#                     continue
#                 output_path = os.path.join(self.output_dir, f"gwr_{name}_{year}.tif")
#                 with rasterio.open(output_path, 'w', **ref_profile) as dst:
#                     dst.write(data, 1)
#             self.logger.info(f"GWR结果已保存至: {self.output_dir}")
#         except Exception as e:
#             self.logger.error(f"GWR结果保存失败: year={year}, 错误: {str(e)}")
#             raise
#
# if __name__ == "__main__":
#     climate_service = ClimateDataService()
#     gwr_service = GWRService(climate_service)
#     gwr_service.align_rasters(reference_year=2000)
#     moran_result = gwr_service.calculate_morans_i(year=2020, variable='rsei')
#     print(f"RSEI Moran’s I: {moran_result['morans_i']}, p-value: {moran_result['p_value']}")
#     vif_result = gwr_service.calculate_vif(year=2020, include_lucc=True)
#     print(f"VIF: {vif_result}")
#     gwr_results = gwr_service.run_gwr(year=2020, include_lucc=True)
#     print(f"GWR AICc: {gwr_results['aic']}, Bandwidth: {gwr_results['bandwidth']}")
#     gwr_service.save_gwr_results(gwr_results, year=2020)
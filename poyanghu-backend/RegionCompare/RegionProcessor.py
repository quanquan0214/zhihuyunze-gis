"""
区域处理器 - 处理用户定义的区域和矢量数据
"""
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import rasterio
from rasterio import features
from rasterio.warp import transform_bounds
import pyproj
from typing import List, Dict, Union, Optional, Tuple


class RegionProcessor:
    """处理用户定义的区域和矢量数据"""

    def __init__(self):
        self.regions = {}
        self.region_counter = 0

    def add_region_from_points(self, points: List[Tuple[float, float]],
                               region_name: Optional[str] = None,
                               region_id: Optional[str] = None,
                               crs: str = 'EPSG:4326') -> str:
        """
        从点列表创建区域

        Args:
            points: 点坐标列表 [(lon, lat), ...]
            region_name: 区域名称，如果为None则自动生成
            region_id: 可选的自定义区域ID，如果为None则自动生成
            crs: 坐标参考系统

        Returns:
            region_id: 区域ID
        """
        if len(points) < 3:
            raise ValueError("至少需要3个点来构成封闭区域")

        # 确保多边形闭合
        if points[0] != points[-1]:
            points.append(points[0])

        # 创建多边形
        polygon = Polygon(points)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)  # 修复无效几何

        # 生成区域ID
        if region_id is None:
            region_id = f"region_{self.region_counter}"
            self.region_counter += 1

        if region_name is None:
            region_name = f"区域_{region_id}"

        # 创建GeoDataFrame
        gdf = gpd.GeoDataFrame(
            {'region_name': [region_name]},
            geometry=[polygon],
            crs=crs
        )
        # 计算边界
        bounds = list(polygon.bounds)  # 格式: [min_x, min_y, max_x, max_y]

        self.regions[region_id] = {
            'name': region_name,
            'geometry': gdf,
            'area_km2': self._calculate_area_km2(gdf),
            'bounds': bounds  # 新增边界字段
        }

        return region_id


    def add_region_from_vector(self, vector_data: Union[str, gpd.GeoDataFrame],
                               region_name: Optional[str] = None,
                               region_id: Optional[str] = None) -> str:
        """
        从矢量数据创建区域

        Args:
            vector_data: 矢量数据文件路径或GeoDataFrame
            region_name: 区域名称
            region_id: 可选的自定义区域ID

        Returns:
            region_id: 区域ID
        """
        if isinstance(vector_data, str):
            gdf = gpd.read_file(vector_data)
        else:
            gdf = vector_data.copy()

        # 合并所有几何为单一区域
        unified_geometry = unary_union(gdf.geometry)

        # 生成区域ID
        if region_id is None:
            region_id = f"region_{self.region_counter}"
            self.region_counter += 1

        if region_name is None:
            region_name = f"区域_{region_id}"

        # 创建新的GeoDataFrame
        result_gdf = gpd.GeoDataFrame(
            {'region_name': [region_name]},
            geometry=[unified_geometry],
            crs=gdf.crs
        )

        # 计算边界
        bounds = list(unified_geometry.bounds)

        self.regions[region_id] = {
            'name': region_name,
            'geometry': result_gdf,
            'area_km2': self._calculate_area_km2(result_gdf),
            'bounds': bounds  # 新增边界字段
        }
        return region_id

    def get_region(self, region_id: str) -> Optional[Dict]:
        """获取区域信息"""
        return self.regions.get(region_id)

    def get_all_regions(self) -> Dict:
        """获取所有区域信息"""
        return self.regions

    def remove_region(self, region_id: str) -> bool:
        """移除区域"""
        if region_id in self.regions:
            del self.regions[region_id]
            return True
        return False

    def _calculate_area_km2(self, gdf: gpd.GeoDataFrame) -> float:
        """计算区域面积（平方公里）"""
        # 转换到适合面积计算的投影坐标系
        if gdf.crs.to_string() != 'EPSG:3857':  # Web Mercator
            gdf_projected = gdf.to_crs('EPSG:3857')
        else:
            gdf_projected = gdf

        # 计算面积并转换为平方公里
        area_m2 = gdf_projected.geometry.area.sum()
        return area_m2 / 1e6

    def get_region_mask(self, region_id: str, raster_path: str) -> Optional[np.ndarray]:
        """
        为指定区域创建栅格掩膜

        Args:
            region_id: 区域ID
            raster_path: 栅格数据路径

        Returns:
            mask: 布尔掩膜数组
        """
        if region_id not in self.regions:
            return None

        region_info = self.regions[region_id]
        gdf = region_info['geometry']

        with rasterio.open(raster_path) as src:
            # 确保坐标系统匹配
            if gdf.crs != src.crs:
                gdf = gdf.to_crs(src.crs)

            # 创建掩膜
            mask = features.rasterize(
                gdf.geometry,
                out_shape=src.shape,
                transform=src.transform,
                fill=0,
                default_value=1,
                dtype='uint8'
            )

            return mask.astype(bool)

    def get_regions_intersection(self, region_ids: List[str]) -> Optional[gpd.GeoDataFrame]:
        """获取多个区域的交集"""
        if not region_ids or len(region_ids) < 2:
            return None

        geometries = []
        for region_id in region_ids:
            if region_id in self.regions:
                geometries.append(self.regions[region_id]['geometry'].geometry.iloc[0])

        if len(geometries) < 2:
            return None

        # 计算交集
        intersection = geometries[0]
        for geom in geometries[1:]:
            intersection = intersection.intersection(geom)

        if intersection.is_empty:
            return None

        # 使用第一个区域的CRS
        first_region = self.regions[region_ids[0]]
        result_gdf = gpd.GeoDataFrame(
            {'region_name': ['intersection']},
            geometry=[intersection],
            crs=first_region['geometry'].crs
        )

        return result_gdf
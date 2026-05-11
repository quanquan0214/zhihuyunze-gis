import sys
import os
import matplotlib
matplotlib.use('Agg')
from typing import Dict, List, Any
import tempfile
from shapely.geometry import Polygon
import geopandas as gpd

def get_city_mapping() -> Dict[str, Dict[str, str]]:
    """Return a dictionary mapping city codes to their full names and geojson paths"""
    return {
        'NC': {'name': '南昌市', 'path': "D:/Google/GLC_FCS30/南昌市_市.geojson"},
        'JDZ': {'name': '景德镇市', 'path': "D:/Google/GLC_FCS30/景德镇市_市.geojson"},
        'SR': {'name': '上饶市', 'path': "D:/Google/GLC_FCS30/上饶市_市.geojson"},
        'YT': {'name': '鹰潭市', 'path': "D:/Google/GLC_FCS30/鹰潭市_市.geojson"},
        'JJ': {'name': '九江市', 'path': "D:/Google/GLC_FCS30/九江市_市.geojson"},
        'FZ': {'name': '抚州市', 'path': "D:/Google/GLC_FCS30/抚州市_市.geojson"}
    }

def validate_city_codes(codes: List[str]) -> bool:
    """Validate the input city codes"""
    city_mapping = get_city_mapping()
    if len(codes) < 2 or len(codes) > 6:
        return False
    return all(code in city_mapping for code in codes)

def get_points_mapping(point_groups: List[Dict]) -> Dict[str, Dict[str, str]]:
    """
    将点位组转换为临时的geojson文件映射

    Args:
        point_groups: 点位组列表，每个元素包含:
            - id: 区域唯一标识
            - name: 区域名称
            - points: 点位列表，每个点包含 [lon, lat]

    Returns:
        Dict: 映射字典，格式类似于 get_city_mapping()
    """
    mapping = {}

    for group in point_groups:
        region_id = group.get('id')
        region_name = group.get('name', f'区域_{region_id}')
        points = group.get('points', [])

        # 验证点位数量（至少3个点才能构成封闭图形）
        if len(points) < 3:
            continue

        # 确保首尾点相同以形成封闭图形
        if points[0] != points[-1]:
            points.append(points[0])

        # 创建Shapely多边形
        try:
            polygon = Polygon(points)
            if not polygon.is_valid:
                continue
        except Exception as e:
            print(f"创建多边形失败 {region_id}: {e}")
            continue

        # 创建GeoDataFrame
        gdf = gpd.GeoDataFrame([{'name': region_name}], geometry=[polygon])
        gdf.crs = "EPSG:4326"  # WGS84坐标系

        # 创建临时geojson文件 - 使用更安全的方法
        import time
        import uuid
        temp_filename = f"temp_region_{uuid.uuid4().hex}_{int(time.time())}.geojson"
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, temp_filename)

        try:
            gdf.to_file(temp_path, driver='GeoJSON')
            mapping[region_id] = {
                'name': region_name,
                'path': temp_path
            }
        except Exception as e:
            print(f"创建临时文件失败 {region_id}: {e}")
            continue

    return mapping

def validate_point_groups(point_groups: List[Dict]) -> bool:
    """验证点位组数据"""
    if not isinstance(point_groups, list) or len(point_groups) < 2 or len(point_groups) > 6:
        return False

    for group in point_groups:
        if not isinstance(group, dict):
            return False
        if 'id' not in group or 'points' not in group:
            return False
        if not isinstance(group['points'], list) or len(group['points']) < 3:
            return False

        # 验证每个点的格式
        for point in group['points']:
            if not isinstance(point, list) or len(point) != 2:
                return False
            try:
                float(point[0])  # 经度
                float(point[1])  # 纬度
            except (ValueError, TypeError):
                return False

    return True










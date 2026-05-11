import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from typing import Dict, List, Tuple, Any
import os
from collections import defaultdict
import json


class LandCoverAnalyzer:
    """土地覆盖分析核心类"""

    def __init__(self, data_dir: str = "F:/pylake/totaldata/GLC_FCS30/merged"):
        self.data_dir = data_dir
        self.years = list(range(2000, 2023))

        # 土地覆盖类型映射
        self.land_cover_mapping = {
            10: "雨养耕地",
            11: "草本植被覆盖",
            20: "灌溉耕地",
            51: "开阔常绿阔叶林",
            52: "闭阔常绿阔叶林",
            61: "开阔落叶阔叶林(0.15 < fc <0.4)",
            62: "闭阔落叶阔叶林(fc > 0.4)",
            71: "开阔常绿针叶林(0.15 < fc < 0.4)",
            72: "闭阔常绿针叶林(fc > 0.4)",
            91: "开阔混交叶片林(阔叶树和针叶树)",
            120: "灌木林",
            121: "常绿灌木林",
            130: "草地",
            150: "稀疏植被(fc < 0.15)",
            181: "沼泽",
            182: "沼泽地",
            183: "水淹平地",
            190: "不透水表面",
            200: "裸地",
            210: "水体"
        }

        # 简化的类型映射（用于显示）
        self.simplified_mapping = {
            10: "耕地", 11: "草本", 20: "耕地",
            51: "阔叶林", 52: "阔叶林", 61: "阔叶林", 62: "阔叶林",
            71: "针叶林", 72: "针叶林", 91: "混交林",
            120: "灌木", 121: "灌木", 130: "草地", 150: "稀疏植被",
            181: "湿地", 182: "湿地", 183: "湿地",
            190: "建设用地", 200: "裸地", 210: "水体"
        }

    def get_file_path(self, year: int) -> str:
        """获取指定年份的文件路径"""
        return os.path.join(self.data_dir, f"poyang_{year}.tif")

    def extract_region_data(self, region_geojson_path: str) -> Dict[int, Dict[str, float]]:
        """
        提取指定区域的土地覆盖数据

        Args:
            region_geojson_path: 区域GeoJSON文件路径

        Returns:
            Dict: {year: {land_type: area_km2}}
        """
        # 读取区域几何
        region_gdf = gpd.read_file(region_geojson_path)
        region_geom = region_gdf.geometry.iloc[0]

        result = {}

        for year in self.years:
            file_path = self.get_file_path(year)
            if not os.path.exists(file_path):
                continue

            try:
                with rasterio.open(file_path) as src:
                    # 裁剪栅格数据
                    clipped_data, clipped_transform = mask(src, [region_geom], crop=True)
                    clipped_data = clipped_data[0]  # 取第一个波段

                    # 计算像素面积（假设像素大小为30m）
                    pixel_area_km2 = (30 * 30) / (1000 * 1000)  # 转换为平方千米

                    # 统计各类型面积
                    unique_values, counts = np.unique(clipped_data[clipped_data != src.nodata], return_counts=True)

                    year_data = {}
                    for value, count in zip(unique_values, counts):
                        if value in self.simplified_mapping:
                            land_type = self.simplified_mapping[value]
                            area_km2 = count * pixel_area_km2

                            if land_type in year_data:
                                year_data[land_type] += area_km2
                            else:
                                year_data[land_type] = area_km2

                    result[year] = year_data

            except Exception as e:
                print(f"处理年份 {year} 时出错: {e}")
                continue

        return result

    def calculate_percentage_of_total(self, region_data: Dict[int, Dict[str, float]]) -> Dict[int, Dict[str, float]]:
        """
        计算各年份中土地类型面积占当年区域总面积的百分比
        Args:
            region_data: 区域数据，结构为{年份: {土地类型: 面积}}
        Returns:
            Dict: {年份: {土地类型: 占比百分比}}
        """
        result = {}
        for year, year_data in region_data.items():
            # 计算当前年份的区域总面积
            total_area = sum(year_data.values())
            # print(f"年份 {year} 总面积: {total_area} 公顷")
            if total_area == 0:
                # 避免除零错误，总面积为0时所有占比设为0
                result[year] = {land_type: 0.0 for land_type in year_data.keys()}
            else:
                year_percentages = {}
                for land_type, area in year_data.items():
                    # 计算当前土地类型占当年总面积的百分比
                    percentage = (area / total_area) * 100
                    year_percentages[land_type] = round(percentage, 2)
                result[year] = year_percentages
        return result

    def calculate_annual_change_rates(self, region_data: Dict[int, Dict[str, float]]) -> Dict[str, List[Dict]]:
        """
        计算年际变化率（用于热力图）

        Returns:
            Dict: {land_type: [{'year': year, 'change_rate': rate}]}
        """
        result = defaultdict(list)

        # 获取所有土地类型
        all_land_types = set()
        for year_data in region_data.values():
            all_land_types.update(year_data.keys())

        # 按年份排序
        sorted_years = sorted(region_data.keys())

        for land_type in all_land_types:
            for i in range(1, len(sorted_years)):
                prev_year = sorted_years[i - 1]
                curr_year = sorted_years[i]

                prev_area = region_data[prev_year].get(land_type, 0)
                curr_area = region_data[curr_year].get(land_type, 0)

                if prev_area > 0:
                    change_rate = ((curr_area - prev_area) / prev_area) * 100
                else:
                    change_rate = 0.0

                result[land_type].append({
                    'year': curr_year,
                    'change_rate': round(change_rate, 3)
                })

        return dict(result)

    def detect_anomaly_years(self, region_data: Dict[int, Dict[str, float]],
                             threshold: float = 2.0) -> Dict[str, List[Dict]]:
        """
        检测异常年份（变化率超过阈值的年份）

        Args:
            region_data: 区域数据
            threshold: 异常阈值（百分比）

        Returns:
            Dict: {land_type: [{'year': year, 'change_rate': rate, 'type': 'increase/decrease'}]}
        """
        annual_changes = self.calculate_annual_change_rates(region_data)
        anomalies = defaultdict(list)

        for land_type, changes in annual_changes.items():
            for change_info in changes:
                change_rate = abs(change_info['change_rate'])
                if change_rate >= threshold:
                    anomaly_type = 'increase' if change_info['change_rate'] > 0 else 'decrease'
                    anomalies[land_type].append({
                        'year': change_info['year'],
                        'change_rate': change_info['change_rate'],
                        'type': anomaly_type
                    })

        return dict(anomalies)

    def create_transition_matrix(self, region_geojson_path: str,
                                 from_year: int, to_year: int) -> Dict[str, Any]:
        """
        创建土地类型转换矩阵（用于桑基图）

        Args:
            region_geojson_path: 区域GeoJSON文件路径
            from_year: 起始年份
            to_year: 结束年份

        Returns:
            Dict: 转换矩阵数据
        """
        # 读取区域几何
        region_gdf = gpd.read_file(region_geojson_path)
        region_geom = region_gdf.geometry.iloc[0]

        from_file = self.get_file_path(from_year)
        to_file = self.get_file_path(to_year)

        if not (os.path.exists(from_file) and os.path.exists(to_file)):
            return {}

        try:
            # 读取起始年份数据
            with rasterio.open(from_file) as src1:
                from_data, transform = mask(src1, [region_geom], crop=True)
                from_data = from_data[0]

            # 读取结束年份数据
            with rasterio.open(to_file) as src2:
                to_data, _ = mask(src2, [region_geom], crop=True)
                to_data = to_data[0]

            # 计算转换矩阵
            pixel_area_km2 = (30 * 30) / (1000 * 1000)
            transitions = defaultdict(float)

            # 创建有效数据掩码
            valid_mask = (from_data != src1.nodata) & (to_data != src2.nodata)

            from_valid = from_data[valid_mask]
            to_valid = to_data[valid_mask]

            for from_val, to_val in zip(from_valid, to_valid):
                if from_val in self.simplified_mapping and to_val in self.simplified_mapping:
                    from_type = self.simplified_mapping[from_val]
                    to_type = self.simplified_mapping[to_val]
                    transitions[(from_type, to_type)] += pixel_area_km2

            # 转换为桑基图格式
            sankey_data = {
                'nodes': [],
                'links': []
            }

            # 获取所有土地类型
            all_types = set()
            for (from_type, to_type) in transitions.keys():
                all_types.add(from_type)
                all_types.add(to_type)

            # 创建节点
            type_to_id = {}
            for i, land_type in enumerate(sorted(all_types)):
                sankey_data['nodes'].append({
                    'id': i,
                    'name': f"{land_type}_{from_year}",
                    'category': land_type
                })
                type_to_id[f"{land_type}_{from_year}"] = i

            for i, land_type in enumerate(sorted(all_types)):
                node_id = len(sankey_data['nodes'])
                sankey_data['nodes'].append({
                    'id': node_id,
                    'name': f"{land_type}_{to_year}",
                    'category': land_type
                })
                type_to_id[f"{land_type}_{to_year}"] = node_id

            # 创建连接
            for (from_type, to_type), area in transitions.items():
                if area > 0.1:  # 过滤掉面积太小的转换
                    sankey_data['links'].append({
                        'source': type_to_id[f"{from_type}_{from_year}"],
                        'target': type_to_id[f"{to_type}_{to_year}"],
                        'value': round(area, 2),
                        'from_type': from_type,
                        'to_type': to_type
                    })

            return sankey_data

        except Exception as e:
            print(f"创建转换矩阵时出错: {e}")
            return {}

    def compare_multiple_regions(self, region_paths: List[str],
                                 region_names: List[str] = None) -> Dict[str, Any]:
        """
        多区域对比分析

        Args:
            region_paths: 区域GeoJSON文件路径列表
            region_names: 区域名称列表

        Returns:
            Dict: 对比分析结果
        """
        if region_names is None:
            region_names = [f"区域{i + 1}" for i in range(len(region_paths))]

        comparison_data = {}

        for i, (path, name) in enumerate(zip(region_paths, region_names)):
            try:
                region_data = self.extract_region_data(path)
                relative_changes = self.calculate_percentage_of_total(region_data)
                anomalies = self.detect_anomaly_years(region_data)

                comparison_data[name] = {
                    'raw_data': region_data,
                    'relative_changes': relative_changes,
                    'anomalies': anomalies,
                    'total_area': self._calculate_total_area(region_data),
                    'dominant_types': self._get_dominant_land_types(region_data)
                }
            except Exception as e:
                print(f"处理区域 {name} 时出错: {e}")
                continue

        return comparison_data

    def _calculate_total_area(self, region_data: Dict[int, Dict[str, float]]) -> Dict[int, float]:
        """计算每年的总面积"""
        total_areas = {}
        for year, year_data in region_data.items():
            total_areas[year] = sum(year_data.values())
        return total_areas

    def _get_dominant_land_types(self, region_data: Dict[int, Dict[str, float]],
                                 top_n: int = 3) -> Dict[int, List[Tuple[str, float]]]:
        """获取每年的主要土地类型"""
        dominant_types = {}
        for year, year_data in region_data.items():
            sorted_types = sorted(year_data.items(), key=lambda x: x[1], reverse=True)
            dominant_types[year] = sorted_types[:top_n]
        return dominant_types



    def parse_polygon_coords(self,coords_str: str) -> Dict:
        """解析多边形坐标字符串为几何对象"""
        try:
            # 解析坐标字符串，格式如: "lng1,lat1,lng2,lat2,lng3,lat3,..."
            coords = [float(x.strip()) for x in coords_str.split(',')]
            if len(coords) < 6 or len(coords) % 2 != 0:
                raise ValueError("多边形至少需要3个点（6个坐标值），且坐标数量必须为偶数")

            # 将坐标对转换为点列表
            points = []
            for i in range(0, len(coords), 2):
                points.append([coords[i], coords[i + 1]])  # [lng, lat]

            # 确保多边形闭合（首尾点相同）
            if points[0] != points[-1]:
                points.append(points[0])

            # 创建GeoJSON多边形几何
            polygon_geom = {
                "type": "Polygon",
                "coordinates": [points]
            }

            return polygon_geom
        except Exception as e:
            raise ValueError(f"多边形坐标解析错误: {str(e)}")

    def parse_years(self,years_str: str) -> List[int]:
        """解析年份范围"""
        try:
            if '-' in years_str:
                start, end = years_str.split('-')
                return list(range(int(start), int(end) + 1))
            else:
                return [int(years_str)]
        except Exception as e:
            raise ValueError(f"年份解析错误: {str(e)}")

    def calculate_comparison_stats(self,comparison_data: Dict, metric: str) -> Dict:
        """计算对比统计数据"""
        stats = {
            'total_regions': len(comparison_data),
            'land_types': set(),
            'year_range': None
        }

        all_years = set()
        for region_data in comparison_data.values():
            if 'raw_data' in region_data:
                all_years.update(region_data['raw_data'].keys())
                for year_data in region_data['raw_data'].values():
                    stats['land_types'].update(year_data.keys())

        if all_years:
            stats['year_range'] = [min(all_years), max(all_years)]

        stats['land_types'] = list(stats['land_types'])

        if metric == 'area':
            # 计算面积统计
            stats['area_comparison'] = {}
            for region_name, region_data in comparison_data.items():
                if 'total_area' in region_data:
                    latest_year = max(region_data['total_area'].keys())
                    stats['area_comparison'][region_name] = region_data['total_area'][latest_year]

        return stats

    def calculate_transition_stats(self,transition_data: Dict) -> Dict:
        """计算转换统计数据"""
        stats = {
            'total_transitions': 0,
            'major_transitions': [],
            'by_land_type': {},
            'stability_ratio': 0
        }

        if 'links' not in transition_data:
            return stats

        links = transition_data['links']
        stats['total_transitions'] = len(links)

        # 计算主要转换和稳定性
        stable_area = 0
        total_area = 0

        for link in links:
            total_area += link['value']
            if link['from_type'] == link['to_type']:
                stable_area += link['value']

            # 记录主要转换（面积大于1平方千米）
            if link['value'] > 1.0 and link['from_type'] != link['to_type']:
                stats['major_transitions'].append({
                    'from': link['from_type'],
                    'to': link['to_type'],
                    'area': link['value']
                })

        # 计算稳定性比率
        if total_area > 0:
            stats['stability_ratio'] = round((stable_area / total_area) * 100, 2)

        # 按转换面积排序
        stats['major_transitions'].sort(key=lambda x: x['area'], reverse=True)
        stats['major_transitions'] = stats['major_transitions'][:10]  # 只保留前10个

        return stats

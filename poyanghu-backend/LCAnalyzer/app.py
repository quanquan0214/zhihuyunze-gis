import json
import sys
import os
import jwt
import csv
import matplotlib

matplotlib.use('Agg')
from collections import defaultdict
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS
import Connect.SQL_DB as DB
import rasterio
import numpy as np
import pandas as pd
from AdditionalFunction.Trend import TrendAnalyzer
from AdditionalFunction.PredictTool import EnvironmentalPredictor
from AdditionalFunction.Annormal import AnomalyDetector
from RegionCompare.ComparisonAnalyzer import ComparisonAnalyzer
from typing import Dict, List, Any
import tempfile
from shapely.geometry import Polygon
import geopandas as gpd
from LCAnalyzer.land_cover_analyzer import LandCoverAnalyzer
import traceback
# Get current directory and add Connect to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'Connect'))
sys.path.append(os.path.join(current_dir, 'AdditionalFunction'))
sys.path.append(os.path.join(current_dir, 'RegionCompare'))
sys.path.append(os.path.join(current_dir, 'LCAnalyzer'))

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 禁用 ASCII 转义
app.config['SECRET_KEY'] = 'pylake'
CORS(app)



def create_geojson_from_geometry(geometry_data: Dict, filename: str) -> str:
    """从几何数据创建临时GeoJSON文件"""
    filepath = os.path.join(UPLOAD_FOLDER, f"{filename}.geojson")

    # 创建GeoJSON结构
    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": geometry_data,
            "properties": {}
        }]
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)

    return filepath

@app.route('/api/timeseries', methods=['GET'])
def get_timeseries():
    """
    获取时间序列数据
    参数:
    - region: 区域几何(polygon GeoJSON字符串或bbox坐标)
    - years: 年份范围(如2000-2022或2020)
    """
    try:
        region = request.args.get('region')
        years_param = request.args.get('years', '2000-2022')

        if not region:
            return jsonify({
                'error': '缺少region参数',
                'status': 'error'
            }), 400

        # 解析年份
        years = LC_analyzer.parse_years(years_param)

        # 处理区域几何
        temp_filename = f"timeseries_{hash(region)}"

        try:
            # 尝试解析为GeoJSON
            region_geom = json.loads(region)
            if 'coordinates' not in region_geom:
                raise ValueError("无效的GeoJSON格式")
        except:
            # 尝试解析为多边形坐标
            try:
                region_geom = LC_analyzer.parse_polygon_coords(region)
            except:
                return jsonify({
                    'error': '无效的区域格式，请提供GeoJSON或多边形坐标（如: lng1,lat1,lng2,lat2,lng3,lat3）',
                    'status': 'error'
                }), 400

        # 创建临时GeoJSON文件
        geojson_path = create_geojson_from_geometry(region_geom, temp_filename)

        try:
            # 提取区域数据
            region_data = LC_analyzer.extract_region_data(geojson_path)
            # 过滤指定年份的数据
            filtered_data = {year: data for year, data in region_data.items() if year in years}
            # 计算年度变化
            relative_changes = LC_analyzer.calculate_percentage_of_total(filtered_data)
            # 计算年际变化率
            annual_changes = LC_analyzer.calculate_annual_change_rates(filtered_data)

            result = {
                'status': 'success',
                'data': {
                    'relative_changes': relative_changes,
                    'annual_change_rates': annual_changes,
                }
            }

            return jsonify(result)

        finally:
            # 清理临时文件
            if os.path.exists(geojson_path):
                os.remove(geojson_path)

    except Exception as e:
        return jsonify({
            'error': f'处理请求时出错: {str(e)}',
            'status': 'error',
            'traceback':traceback.format_exc()
        }), 500

@app.route('/api/compare', methods=['GET'])
def compare_regions():
    """
    多区域对比分析
    参数:
    - regions: 区域列表JSON字符串 [{"name": "区域1", "geometry": {...}}, ...]
    - metric: 对比指标(area, change, anomaly)
    """
    try:
        regions_param = request.args.get('regions')
        metric = request.args.get('metric', 'area')

        if not regions_param:
            return jsonify({
                'error': '缺少regions参数',
                'status': 'error'
            }), 400

        # 解析区域列表
        try:
            regions_data = json.loads(regions_param)
        except:
            return jsonify({
                'error': '无效的regions格式，请提供JSON数组',
                'status': 'error'
            }), 400

        if len(regions_data) < 2:
            return jsonify({
                'error': '至少需要2个区域进行对比',
                'status': 'error'
            }), 400

        # 处理每个区域
        region_paths = []
        region_names = []
        temp_files = []

        try:
            for i, region_info in enumerate(regions_data):
                region_name = region_info.get('name', f'区域{i + 1}')
                region_geom = region_info.get('geometry')

                if not region_geom:
                    raise ValueError(f"区域 {region_name} 缺少geometry字段")

                # 创建临时文件
                temp_filename = f"compare_{region_name}_{i}"
                geojson_path = create_geojson_from_geometry(region_geom, temp_filename)

                region_paths.append(geojson_path)
                region_names.append(region_name)
                temp_files.append(geojson_path)

            # 执行对比分析
            comparison_data = LC_analyzer.compare_multiple_regions(region_paths, region_names)

            # 根据metric过滤结果
            filtered_result = {}
            for region_name, region_data in comparison_data.items():
                if metric == 'area':
                    filtered_result[region_name] = {
                        'raw_data': region_data['raw_data'],
                        'total_area': region_data['total_area'],
                        'dominant_types': region_data['dominant_types']
                    }
                elif metric == 'change':
                    filtered_result[region_name] = {
                        'relative_changes': region_data['relative_changes'],
                        'total_area': region_data['total_area']
                    }
                elif metric == 'anomaly':
                    filtered_result[region_name] = {
                        'anomalies': region_data['anomalies'],
                        'total_area': region_data['total_area']
                    }
                else:
                    filtered_result[region_name] = region_data

            # 计算对比统计
            comparison_stats = LC_analyzer.calculate_comparison_stats(comparison_data, metric)

            result = {
                'status': 'success',
                'data': {
                    'regions': filtered_result,
                    'comparison_stats': comparison_stats,
                    'metric': metric
                },
                'metadata': {
                    'region_count': len(region_names),
                    'region_names': region_names,
                    'comparison_metric': metric
                }
            }

            return jsonify(result)

        finally:
            # 清理所有临时文件
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    except Exception as e:
        return jsonify({
            'error': f'处理对比请求时出错: {str(e)}',
            'status': 'error',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/transition', methods=['GET'])
def get_transition_matrix():
    """
    获取土地类型转换矩阵
    参数:
    - from_year: 起始年份
    - to_year: 结束年份
    - region: 区域几何(bbox坐标或GeoJSON)
    """
    try:
        from_year = request.args.get('from_year')
        to_year = request.args.get('to_year')
        region = request.args.get('region')

        if not all([from_year, to_year, region]):
            return jsonify({
                'error': '缺少必要参数: from_year, to_year, region',
                'status': 'error'
            }), 400

        try:
            from_year = int(from_year)
            to_year = int(to_year)
        except:
            return jsonify({
                'error': '年份必须为整数',
                'status': 'error'
            }), 400

        # 处理区域几何
        try:
            region_geom = json.loads(region)
        except:
            try:
                region_geom = LC_analyzer.parse_polygon_coords(region)
            except:
                return jsonify({
                    'error': '无效的区域格式',
                    'status': 'error'
                }), 400

        temp_filename = f"transition_{from_year}_{to_year}_{hash(region)}"
        geojson_path = create_geojson_from_geometry(region_geom, temp_filename)

        try:
            # 创建转换矩阵
            transition_data = LC_analyzer.create_transition_matrix(geojson_path, from_year, to_year)

            if not transition_data:
                return jsonify({
                    'error': f'无法创建 {from_year}-{to_year} 年的转换矩阵',
                    'status': 'error'
                }), 404

            # 计算转换统计
            transition_stats = LC_analyzer.calculate_transition_stats(transition_data)

            result = {
                'status': 'success',
                'data': {
                    'sankey_data': transition_data,
                    'transition_stats': transition_stats
                },
                'metadata': {
                    'from_year': from_year,
                    'to_year': to_year,
                    'years_span': to_year - from_year,
                    'node_count': len(transition_data.get('nodes', [])),
                    'link_count': len(transition_data.get('links', []))
                }
            }
            return jsonify(result)

        finally:
            if os.path.exists(geojson_path):
                os.remove(geojson_path)

    except Exception as e:
        return jsonify({
            'error': f'处理转换矩阵请求时出错: {str(e)}',
            'status': 'error',
            'traceback': traceback.format_exc()
        }), 500


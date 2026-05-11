import json
import sys
import os
import jwt
import matplotlib
matplotlib.use('Agg')
from flask import Flask, request, jsonify, send_file
from http import HTTPStatus
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS
import rasterio
import numpy as np
import pandas as pd
import zipfile
import shutil
import geopandas as gpd
from werkzeug.utils import secure_filename
import Connect.SQL_DB as DB
from AdditionalFunction.Trend import TrendAnalyzer
from AdditionalFunction.PredictTool import EnvironmentalPredictor
from AdditionalFunction.Annormal import AnomalyDetector
from RegionCompare.ComparisonAnalyzer import ComparisonAnalyzer
from RF_TPT.TPRFService import TPRFService
from typing import Dict, List, Any
from LCAnalyzer.land_cover_analyzer import LandCoverAnalyzer
from IM.SR import SRService
import traceback

# Get current directory and add Connect to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'Connect'))
sys.path.append(os.path.join(current_dir, 'AdditionalFunction'))
sys.path.append(os.path.join(current_dir, 'RegionCompare'))
sys.path.append(os.path.join(current_dir, 'LCAnalyzer'))
sys.path.append(os.path.join(current_dir, 'RF_TPT'))

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 禁用 ASCII 转义
app.config['SECRET_KEY'] = 'pylake'
CORS(app)

# Configuration for predict endpoint
DATA_DIR = 'F:/pylake/totaldata/RSEI_full'
PREDICT_YEARS = 5
RC_analyzer = ComparisonAnalyzer(data_directory=DATA_DIR)
LC_analyzer = LandCoverAnalyzer()
RT_analyzer = TPRFService()
# 配置参数
LUCC_DATA_DIR = 'F:/pylake/totaldata/GLC_FCS30/merged'
os.makedirs(LUCC_DATA_DIR, exist_ok=True)
# Configuration
UPLOAD_FOLDER_IM = 'F:/pylake/totaldata/city'
ALLOWED_EXTENSIONS = {'shp', 'shx', 'dbf', 'prj', 'geojson', 'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_IM

# Helper function for predict endpoint
def load_rsei_series(data_dir, coords):
    time_series = []
    for file in sorted(os.listdir(data_dir)):
        if not file.endswith('.tif') or not file.startswith('RSEI_'):
            continue
        year = int(file.split('_')[1].split('.')[0])
        date = pd.Timestamp(f"{year}-07-01")
        with rasterio.open(os.path.join(data_dir, file)) as f:
            val = float(f.read(1)[coords[1], coords[0]])
            if np.isnan(val) or val == f.nodata:
                continue
        time_series.append({'date': date, 'value': val})
    return pd.DataFrame(time_series).sort_values('date')

def get_city_mapping() -> Dict[str, Dict[str, str]]:
    """Return a dictionary mapping city codes to their full names and geojson paths"""
    return {
        'NC': {'name': '南昌市', 'path': "F:/pylake/totaldata/GLC_FCS30/南昌市_市.geojson"},
        'JDZ': {'name': '景德镇市', 'path': "F:/pylake/totaldata/GLC_FCS30/景德镇市_市.geojson"},
        'SR': {'name': '上饶市', 'path': "F:/pylake/totaldata/GLC_FCS30/上饶市_市.geojson"},
        'YT': {'name': '鹰潭市', 'path': "F:/pylake/totaldata/GLC_FCS30/鹰潭市_市.geojson"},
        'JJ': {'name': '九江市', 'path': "F:/pylake/totaldata/GLC_FCS30/九江市_市.geojson"},
        'FZ': {'name': '抚州市', 'path': "F:/pylake/totaldata/GLC_FCS30/抚州市_市.geojson"}
    }

def validate_city_codes(codes: List[str]) -> bool:
    """Validate the input city codes"""
    city_mapping = get_city_mapping()
    if len(codes) < 2 or len(codes) > 6:
        return False
    return all(code in city_mapping for code in codes)

def create_geojson_from_geometry(geometry_data: Dict, filename: str) -> str:
    """从几何数据创建临时GeoJSON文件"""
    filepath = os.path.join(LUCC_DATA_DIR, f"{filename}.geojson")

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

# Add CORS headers to response
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/hello')
def hello_world():
    return 'Hello, World!'

@app.route('/')
def index():
    return 'Welcome to Web_pylake.'

# Predict endpoint (unprotected)
@app.route('/predict', methods=['OPTIONS', 'POST'])
def predict():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight check passed'})
        return add_cors_headers(response)

    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    year = data.get('year', 2022)

    if not all([lat, lon]):
        return jsonify({'message': 'Missing latitude/longitude parameters'}), 400

    try:
        raster_file = os.path.join(DATA_DIR, f'RSEI_{year}.tif')
        with rasterio.open(raster_file) as src:
            row, col = src.index(lon, lat)
            data_array = src.read(1)
            value = data_array[row, col]

            if np.isnan(value) or value == src.nodata:
                return jsonify({'message': 'No valid data for selected pixel'}), 400

            df = load_rsei_series(DATA_DIR, (col, row))
            detector = AnomalyDetector()
            anomalies = detector.detect_anomalies(df.to_dict('records'))
            values_data = df['value'].tolist()

            trend_analyzer = TrendAnalyzer()
            trend_result = trend_analyzer.analyze_trend(df)

            predictor = EnvironmentalPredictor()
            prepared = predictor.prepare_features(df)
            _, _ = predictor.train_models(prepared)
            predictions = predictor.predict_future(prepared.iloc[-1], periods=PREDICT_YEARS)

            def safe_round(val, digits=4):
                try:
                    if isinstance(val, (int, float, np.number)):
                        return round(float(val), digits)
                    return 0.0
                except:
                    return 0.0

            response_data = {
                'pixel_value': safe_round(value),
                'coordinates': {'lat': lat, 'lon': lon},
                'time_series': {
                    'values': [safe_round(x, 6) for x in values_data]
                },
                'anomalies': [{
                    'date': a['date'].strftime('%Y-%m-%d') if hasattr(a['date'], 'strftime') else a['date'],
                    'value': safe_round(a['value']),
                    'severity': a['severity']
                } for a in anomalies],
                'trend_analysis': {
                    'trend_type': trend_result.get('trend_type', 'unknown'),
                    'r_squared': safe_round(trend_result.get('r_squared', 0), 3),
                    'trend_strength': trend_result.get('trend_strength', 'unknown'),
                    'predictions': []
                },
                'ml_prediction': {
                    'predictions': [{
                        'period': p.get('period', ''),
                        'predicted_value': safe_round(p.get('predicted_value', 0))
                    } for p in predictions[:3]]
                }
            }
            response = jsonify(response_data)
            return add_cors_headers(response)

    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@app.route('/api/RegionCompare/geojson/', methods=['POST'])
def region_compare():
    # Get city codes from request
    data = request.get_json()
    if not data or 'city_codes' not in data:
        return jsonify({"error": "Missing city_codes parameter"}), 400

    city_codes = data['city_codes']
    if not validate_city_codes(city_codes):
        return jsonify({"error": "Invalid city codes. Please provide 2-6 valid city codes."}), 400

    # Initialize analyzer
    analyzer = ComparisonAnalyzer(data_directory="F:/pylake/totaldata/RSEI_full/")
    city_mapping = get_city_mapping()

    # Add selected analysis regions
    region_ids = {}
    for code in city_codes:
        city_info = city_mapping[code]
        with open(city_info['path'], 'r', encoding='utf-8') as f:
            city_data = {'data': f.read(), 'name': city_info['name']}
            region_id = analyzer.add_analysis_region(city_data, region_type='vector')
            region_ids[code] = region_id
        print(f"Added region: {city_info['name']} (ID: {region_id})")

    # Define analysis years (2000-2022)
    analysis_years = list(range(2000, 2023))

    # Execute parallel comparison analysis
    results = analyzer.parallel_comparison_analysis(
        region_ids=list(region_ids.values()),
        years=analysis_years
    )

    # Generate and save comparison charts
    charts = analyzer.generate_comparison_charts(results)

    output_dir = "F:/pylake/totaldata/output/"
    os.makedirs(output_dir, exist_ok=True)

    # Export data to CSV
    df = analyzer.export_comparison_data(results)
    csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    # print(f"已保存数据文件: RSEI对比数据.csv")

    dataB = RC_analyzer.csv_to_json_chart_data('F:/pylake/totaldata/output/RSEI对比数据.csv')

    final_json = {
        "分析摘要": {
            "分析区域数量": results['comparison_summary']['total_regions'],
            "区域面积比较": {
                "最大区域": f"{results['comparison_summary']['area_comparison']['largest_region'][1]:.2f} km²",
                "最小区域": f"{results['comparison_summary']['area_comparison']['smallest_region'][1]:.2f} km²"
            },
            "归一化指标拟合": {
                "斜率(k)": f"{results['normalized_fit_params']['k']:.6f}",
                "截距(b)": f"{results['normalized_fit_params']['b']:.6f}",
                "拟合方程": f"y = {results['normalized_fit_params']['k']:.6f}x + {results['normalized_fit_params']['b']:.6f}"
            },
            "变化趋势": {
                "平均变化百分比": f"{results['comparison_summary']['overall_trends'].get('average_change', 0):.2f}%",
                "最大增长区域": f"{results['comparison_summary']['overall_trends']['highest_increase'][0]} ({results['comparison_summary']['overall_trends']['highest_increase'][1]:.2f}%)",
                "最大下降区域": f"{results['comparison_summary']['overall_trends']['highest_decrease'][0]} ({results['comparison_summary']['overall_trends']['highest_decrease'][1]:.2f}%)"
            }
        },
        "图表数据": dataB
    }

    return final_json

@app.route('/api/RegionCompare/point/', methods=['POST'])
def region_compare_point():
    """
    基于点位组的区域对比分析

    请求格式:
    {
        "point_groups": [
            {
                "id": "region1",
                "name": "区域1",
                "points": [[lon1, lat1], [lon2, lat2], [lon3, lat3], [lon1, lat1]]
            },
            {
                "id": "region2",
                "name": "区域2",
                "points": [[lon1, lat1], [lon2, lat2], [lon3, lat3], [lon1, lat1]]
            }
        ]
    }
    """
    # 获取点位组数据
    data = request.get_json()
    if not data or 'point_groups' not in data:
        return jsonify({"error": "Missing point_groups parameter"}), 400

    point_groups = data['point_groups']
    if not RC_analyzer.validate_point_groups(point_groups):
        return jsonify({
            "error": "Invalid point groups. Please provide 2-6 valid point groups, each with at least 3 coordinate points."
        }), 400

    points_mapping = {}
    temp_files = []  # 记录所有临时文件路径

    try:
        # 创建点位映射
        points_mapping = RC_analyzer.get_points_mapping(point_groups)
        temp_files = [info['path'] for info in points_mapping.values()]

        if not points_mapping:
            return jsonify({"error": "Failed to create valid polygons from point groups"}), 400

        # 初始化分析器
        analyzer = ComparisonAnalyzer(data_directory="F:/pylake/totaldata/RSEI_full/")

        # 添加分析区域
        region_ids = {}
        for group in point_groups:
            region_id = group['id']
            if region_id not in points_mapping:
                continue

            region_info = points_mapping[region_id]
            try:
                with open(region_info['path'], 'r', encoding='utf-8') as f:
                    region_data = {'data': f.read(), 'name': region_info['name']}
                    analysis_region_id = analyzer.add_analysis_region(region_data, region_type='vector')
                    region_ids[region_id] = analysis_region_id
                print(f"Added region: {region_info['name']} (ID: {analysis_region_id})")
            except Exception as e:
                print(f"Error processing region {region_id}: {e}")
                continue

        if not region_ids:
            return jsonify({"error": "No valid regions could be processed"}), 400

        # 定义分析年份 (2000-2022)
        analysis_years = list(range(2000, 2023))

        # 执行并行对比分析
        results = analyzer.parallel_comparison_analysis(
            region_ids=list(region_ids.values()),
            years=analysis_years
        )

        # 生成对比图表
        charts = analyzer.generate_comparison_charts(results)

        # 确保输出目录存在
        output_dir = "F:/pylake/totaldata/output/"
        os.makedirs(output_dir, exist_ok=True)

        # 导出数据到CSV
        df = analyzer.export_comparison_data(results)
        csv_path = os.path.join(output_dir, 'RSEI_Points_对比数据.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        # 转换CSV数据为图表数据
        dataB = RC_analyzer.csv_to_json_chart_data(csv_path)

        # 构建最终响应JSON
        final_json = {
            "分析摘要": {
                "分析区域数量": results['comparison_summary']['total_regions'],
                "区域面积比较": {
                    "最大区域": f"{results['comparison_summary']['area_comparison']['largest_region'][1]:.2f} km²",
                    "最小区域": f"{results['comparison_summary']['area_comparison']['smallest_region'][1]:.2f} km²"
                },
                "归一化指标拟合": {
                    "斜率(k)": f"{results['normalized_fit_params']['k']:.6f}",
                    "截距(b)": f"{results['normalized_fit_params']['b']:.6f}",
                    "拟合方程": f"y = {results['normalized_fit_params']['k']:.6f}x + {results['normalized_fit_params']['b']:.6f}"
                },
                "变化趋势": {
                    "平均变化百分比": f"{results['comparison_summary']['overall_trends'].get('average_change', 0):.2f}%",
                    "最大增长区域": f"{results['comparison_summary']['overall_trends']['highest_increase'][0]} ({results['comparison_summary']['overall_trends']['highest_increase'][1]:.2f}%)",
                    "最大下降区域": f"{results['comparison_summary']['overall_trends']['highest_decrease'][0]} ({results['comparison_summary']['overall_trends']['highest_decrease'][1]:.2f}%)"
                }
            },
            "图表数据": dataB
        }

        return jsonify(final_json)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

    finally:
        # 清理临时文件 - 使用更安全的清理方法
        import time
        def safe_remove_file(file_path, max_retries=3, delay=0.5):
            """安全地删除文件，带重试机制"""
            for attempt in range(max_retries):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"成功删除临时文件: {file_path}")
                    return True
                except (OSError, IOError) as e:
                    if attempt < max_retries - 1:
                        print(f"删除文件失败，{delay}秒后重试: {file_path}, 错误: {e}")
                        time.sleep(delay)
                    else:
                        print(f"最终删除失败: {file_path}, 错误: {e}")
                        return False
            return False

        # 清理所有临时文件
        for temp_file in temp_files:
            safe_remove_file(temp_file)

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

# 温度与降水
@app.route('/api/RT/avg', methods=['GET'])
def yearly_monthly_avg():
    # Get query parameters
    year = request.args.get('year', type=int)
    data_type = request.args.get('data_type', type=str)

    # Validate required parameters
    if year is None or data_type is None:
        return jsonify({
            'error': 'Both year and data_type parameters are required'
        }), HTTPStatus.BAD_REQUEST

    try:
        result = RT_analyzer.get_yearly_monthly_avg(year, data_type)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/geojson', methods=['POST'])
def geojson_yearly_monthly_stats():
    # Validate request has JSON data
    if not request.is_json:
        return jsonify({
            'error': 'Request must be JSON'
        }), HTTPStatus.BAD_REQUEST

    data = request.get_json()

    # Validate required fields
    if 'geojson' not in data or 'year' not in data or 'data_type' not in data:
        return jsonify({
            'error': 'geojson, year, and data_type are required fields'
        }), HTTPStatus.BAD_REQUEST

    # Get optional stats parameter
    stats = data.get('stats', 'mean')

    try:
        result = RT_analyzer.get_geojson_yearly_monthly_stats(
            data['geojson'], data['year'], data['data_type'], stats)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/code', methods=['GET'])
def code_yearly_monthly_stats():
    # Get query parameters
    code = request.args.get('code', type=str)
    year = request.args.get('year', type=int)
    data_type = request.args.get('data_type', type=str)
    stats = request.args.get('stats', type=str, default='mean')
    try:
        result = RT_analyzer.get_code_yearly_monthly_stats(
            code, year, data_type, stats)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/points', methods=['POST'])
def points_yearly_monthly_stats():
    # Validate request has JSON data
    if not request.is_json:
        return jsonify({
            'error': 'Request must be JSON'
        }), HTTPStatus.BAD_REQUEST

    data = request.get_json()

    # Validate required fields
    if 'points' not in data or 'year' not in data or 'data_type' not in data:
        return jsonify({
            'error': 'points, year, and data_type are required fields'
        }), HTTPStatus.BAD_REQUEST

    # Get optional stats parameter
    stats = data.get('stats', 'mean')
    try:
        result = RT_analyzer.get_points_yearly_monthly_stats(
            data['points'], data['year'], data['data_type'], stats)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/coodinate', methods=['GET'])
def point_yearly_monthly_values():
    # Get query parameters
    lon = request.args.get('lon', type=float)
    lat = request.args.get('lat', type=float)
    year = request.args.get('year', type=int)
    data_type = request.args.get('data_type', type=str)

    # Validate required parameters
    if None in (lon, lat, year, data_type):
        return jsonify({
            'error': 'lon, lat, year, and data_type parameters are required'
        }), HTTPStatus.BAD_REQUEST

    try:
        result = RT_analyzer.get_point_yearly_monthly_values(
            (lon, lat), year, data_type)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

# SR分析
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_shapefile(shp_path):
    """Validate if shapefile is readable"""
    try:
        gpd.read_file(shp_path)
        return True
    except Exception:
        return False

def zip_shapefile(shp_path, zip_path):
    """Zip shapefile and its associated files"""
    base_name = os.path.splitext(shp_path)[0]
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for ext in ['shp', 'shx', 'dbf', 'prj']:
            file_path = f"{base_name}.{ext}"
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
    return zip_path

@app.route('/api/preprocess', methods=['POST'])
def preprocess():
    """预处理栅格数据并生成CSV，返回前50行数据"""
    data = request.get_json()

    # 必选参数
    year = data.get('year')
    region = data.get('region')

    # 可选参数（带默认值）
    res = data.get('res', '500m')  # 精度
    src = data.get('src', 'WGS 1984')  # 坐标系
    resuml = data.get('resuml', 'linear')  # 重分类方式

    # 参数验证
    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    if res not in ['250m', '500m', '1000m', '2000m']:
        return jsonify({"status": "error", "message": "Invalid resolution value"}), 400

    try:
        year = int(year)
        if year < 1900 or year > datetime.now().year:
            return jsonify({"status": "error", "message": "Invalid year"}), 400

        # 初始化服务（需修改SRService以支持新参数）
        service = SRService(
            year=year,
            region=region
            # resolution=res,
            # coordinate_system=src,
            # reclass_method=resuml,
        )

        # 处理数据
        if not service.process_all_rasters():
            return jsonify({"status": "error", "message": "Raster processing failed"}), 500
        if not service.create_csv():
            return jsonify({"status": "error", "message": "CSV creation failed"}), 500

        # 读取CSV并限制返回50行
        df = pd.read_csv(service.csv_out)
        csv_data = df.head(50).to_dict(orient='records')

        return jsonify({
            "status": "success",
            "message": "Preprocessing completed successfully",
            "parameters": {  # 返回实际使用的参数
                "resolution": res,
                "coordinate_system": src,
                "reclass_method": resuml,
            },
            "data": csv_data  # 只返回前50行
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/download-shapefile', methods=['GET'])
def download_shapefile():
    """Download shapefile for a specified model"""
    year = request.args.get('year')
    region = request.args.get('region')
    model = request.args.get('model')

    if not all([year, region, model]) or model.upper() not in ['OLS', 'SLM', 'SEM']:
        return jsonify({"status": "error", "message": "Invalid or missing parameters"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")

        if not os.path.exists(shp_path):
            return jsonify({"status": "error", "message": "Shapefile not found"}), 404

        # Create temporary zip file
        temp_zip = os.path.join(service.work_dir, f"{model.lower()}_results.zip")
        zip_shapefile(shp_path, temp_zip)

        response = send_file(temp_zip, as_attachment=True, download_name=f"{model.lower()}_results.zip")

        # Clean up zip file after sending
        @response.call_on_close
        def cleanup():
            os.remove(temp_zip)

        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/shapefile-fields', methods=['GET'])
def shapefile_fields():
    """Return field descriptions for a model's shapefile"""
    year = request.args.get('year')
    region = request.args.get('region')
    model = request.args.get('model')

    if not all([year, region, model]) or model.upper() not in ['OLS', 'SLM', 'SEM']:
        return jsonify({"status": "error", "message": "Invalid or missing parameters"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")

        if not os.path.exists(shp_path):
            return jsonify({"status": "error", "message": "Shapefile not found"}), 404

        # Define field descriptions based on SRService.save_results()
        fields = [
            {"name": "x", "type": "float", "description": "Longitude coordinate"},
            {"name": "y", "type": "float", "description": "Latitude coordinate"},
            {"name": "rsei", "type": "float", "description": "Remote Sensing Ecological Index"},
            {"name": f"{model.lower()}_predicted", "type": "float",
             "description": f"Predicted RSEI values from {model}"},
            {"name": f"{model.lower()}_residuals", "type": "float", "description": f"Residuals from {model}"},
            {"name": f"{model.lower()}_std_resid", "type": "float",
             "description": f"Standardized residuals from {model}"}
        ]

        return jsonify({
            "status": "success",
            "fields": fields
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/spatial-regression', methods=['POST'])
def spatial_regression():
    """使用SRService的select_best_model方法获取最佳模型结果"""
    try:
        data = request.get_json()

        # 1. 参数验证
        required_params = ['year', 'region']
        if not all(param in data for param in required_params):
            missing = [p for p in required_params if p not in data]
            return jsonify({
                "status": "error",
                "message": f"缺少必要参数: {', '.join(missing)}"
            }), 400

        year = data['year']
        region = data['region']

        # 2. 初始化服务
        try:
            service = SRService(year=int(year), region=region)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"服务初始化失败: {str(e)}"
            }), 500

        # 3. 加载数据
        if not hasattr(service, 'csv_out') or not os.path.exists(service.csv_out):
            return jsonify({
                "status": "error",
                "message": "预处理数据文件不存在",
                "path": getattr(service, 'csv_out', '未指定')
            }), 404

        try:
            df = pd.read_csv(service.csv_out)
            # 验证必要的坐标列
            if not all(col in df.columns for col in ['x', 'y']):
                return jsonify({
                    "status": "error",
                    "message": "数据缺少必要的坐标列(x,y)"
                }), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"数据加载失败: {str(e)}"
            }), 500

        # 4. 处理变量
        y_var = data.get('dependent_var', 'rsei')
        if y_var not in df.columns:
            return jsonify({
                "status": "error",
                "message": f"指定的因变量'{y_var}'不存在",
                "available_variables": list(df.columns)
            }), 400

        default_x_vars = ['lucc_numeric', 'temperature', 'rainfall', 'fvc']
        requested_x_vars = data.get('independent_vars', default_x_vars)
        actual_x_vars = [var for var in requested_x_vars
                         if var in df.columns and var != 'dist']

        if not actual_x_vars:
            return jsonify({
                "status": "error",
                "message": "没有可用的自变量",
                "requested_vars": requested_x_vars,
                "available_vars": [v for v in df.columns if v != 'dist']
            }), 400

        # 5. 准备数据并运行模型
        try:
            X = df[actual_x_vars].values
            y = df[y_var].values.reshape(-1, 1)
            service.df = df  # 为shapefile生成设置df

            w = service.create_spatial_weights(df)
            models = service.run_regression_models(
                X=X, y=y, w=w,
                name_y=y_var,
                name_x=actual_x_vars
            )

            # 6. 使用服务类的方法选择最佳模型
            best_model, best_stats = service.select_best_model(
                models['OLS'], models['SLM'], models['SEM']
            )
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"模型计算失败: {str(e)}",
                "traceback": traceback.format_exc()
            }), 500

        # 7. 准备响应数据
        response = {
            "status": "success",
            "best_model": {
                "type": best_stats['name'],
                "r_squared": best_stats['r2'],
                "parameters": {
                    "dependent": y_var,
                    "independent": actual_x_vars
                },
                "diagnostics": {
                    "sample_size": len(df),
                    "coordinates_check": "valid" if all(col in df.columns for col in ['x', 'y']) else "invalid"
                }
            },
            "metadata": {
                "year": year,
                "region": region,
                "model_comparison": ["OLS", "SLM", "SEM"],
            }
        }

        # 8. 如果存在其他统计量，添加到响应中
        optional_stats = ['adj_r2', 'aic', 'logll']
        for stat in optional_stats:
            if hasattr(best_model, stat):
                response['best_model'][stat] = getattr(best_model, stat)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"未预期的错误: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/read-csv', methods=['GET'])
def read_csv():
    """Convert first 50 rows of CSV to JSON for frontend display"""
    year = request.args.get('year')
    region = request.args.get('region')

    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        csv_path = service.csv_out

        if not os.path.exists(csv_path):
            return jsonify({"status": "error", "message": "CSV file not found"}), 404

        df = pd.read_csv(csv_path)
        data = df.head(50).to_dict(orient='records')
        columns = [{"name": col, "type": str(df[col].dtype)} for col in df.columns]

        return jsonify({
            "status": "success",
            "data": data,
            "columns": columns,
            "total_rows": len(df)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/results/visualize', methods=['GET'])
def visualize_results():
    """Return GeoJSON for visualization"""
    year = request.args.get('year')
    region = request.args.get('region')
    model = request.args.get('model')

    if not all([year, region, model]) or model.upper() not in ['OLS', 'SLM', 'SEM']:
        return jsonify({"status": "error", "message": "Invalid or missing parameters"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")

        if not os.path.exists(shp_path):
            return jsonify({"status": "error", "message": "Shapefile not found"}), 404

        gdf = gpd.read_file(shp_path)
        geojson = gdf.to_crs(epsg=4326).to_json()  # Ensure WGS84 for frontend compatibility

        return jsonify({
            "status": "success",
            "geojson": json.loads(geojson)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/download-csv', methods=['GET'])
def download_csv():
    """Download the preprocessed CSV file"""
    year = request.args.get('year')
    region = request.args.get('region')

    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        csv_path = service.csv_out

        if not os.path.exists(csv_path):
            return jsonify({"status": "error", "message": "CSV file not found"}), 404

        return send_file(csv_path, as_attachment=True, download_name=f"result_{year}.csv")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload/region', methods=['POST'])
def upload_region():
    """Upload a shapefile set or GeoJSON and return its GeoJSON content"""
    region_code = request.form.get('region_code')
    region_name = request.form.get('region_name')
    region_dir = None
    if not region_code:
        return jsonify({"status": "error", "message": "Missing region_code"}), 400

    region_code = secure_filename(region_code)
    if not region_code:
        return jsonify({"status": "error", "message": "Invalid region_code"}), 400

    shp_file = request.files.get('shp_file')
    geojson_file = request.files.get('geojson_file')

    if not shp_file and not geojson_file:
        return jsonify({"status": "error", "message": "Missing shp_file or geojson_file"}), 400

    primary_file = geojson_file or shp_file
    if not primary_file or not allowed_file(primary_file.filename):
        return jsonify({"status": "error", "message": "Invalid region file format"}), 400

    try:
        # Create unique directory for region
        region_dir = os.path.join(app.config['UPLOAD_FOLDER'], region_code)
        os.makedirs(region_dir, exist_ok=True)

        if geojson_file:
            region_path = os.path.join(region_dir, f"{region_code}.geojson")
            geojson_file.save(region_path)
        else:
            # Save shapefile
            region_path = os.path.join(region_dir, f"{region_code}.shp")
            shp_file.save(region_path)

            # Save optional files
            for ext in ['shx', 'dbf', 'prj']:
                file = request.files.get(f"{ext}_file")
                if file and allowed_file(file.filename):
                    file.save(os.path.join(region_dir, f"{region_code}.{ext}"))

        # Validate vector file and convert to GeoJSON
        gdf = gpd.read_file(region_path)
        if gdf.empty:
            shutil.rmtree(region_dir)
            return jsonify({"status": "error", "message": "Empty region file"}), 400

        geojson_data = json.loads(gdf.to_crs(epsg=4326).to_json())

        # Dynamically update SRService.city_shapes
        SRService.city_shapes[region_code] = region_path

        return jsonify({
            "status": "success",
            "message": "Region uploaded and processed successfully",
            "region_code": region_code,
            "region_name": region_name or region_code,
            "source_type": "geojson" if geojson_file else "shapefile",
            "geojson": geojson_data  # 直接返回GeoJSON数据
        }), 200
    except Exception as e:
        if region_dir and os.path.exists(region_dir):
            shutil.rmtree(region_dir)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/SRanalysis", methods=['POST'])
def region_analysis():
    """
    区域生态环境分析API
    输入: JSON包含year和region参数
    输出: 包含主要影响因素和分析结果的JSON
    """
    try:
        # 1. 获取并验证请求数据
        data = request.get_json()
        if not data or 'year' not in data or 'region' not in data:
            return jsonify({
                "status": "error",
                "message": "必须提供year和region参数"
            }), 400

        year = data['year']
        region = data['region']

        # 2. 初始化服务
        try:
            service = SRService(year=int(year), region=region)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"服务初始化失败: {str(e)}"
            }), 500

        # 3. 执行分析
        try:
            # 构建SHP文件路径
            shp_path = os.path.join(service.work_dir, f"{region}_{year}_results.shp")
            if not os.path.exists(shp_path):
                return jsonify({
                    "status": "error",
                    "message": f"未找到{region}地区{year}年的分析结果文件"
                }), 404

            # 读取SHP文件
            gdf = gpd.read_file(shp_path)

            # 提取所有系数列 (coef_开头)
            coef_cols = [col for col in gdf.columns if col.startswith('coef_')]
            if not coef_cols:
                return jsonify({
                    "status": "error",
                    "message": "分析结果中未找到任何影响因素系数"
                }), 400

            # 计算各系数的统计指标
            results = {}
            for col in coef_cols:
                coef_values = gdf[col].dropna()
                factor_name = col.replace('coef_', '')

                results[factor_name] = {
                    'mean_coefficient': float(np.mean(coef_values)),
                    'std_deviation': float(np.std(coef_values)),
                    'min_value': float(np.min(coef_values)),
                    'max_value': float(np.max(coef_values)),
                    'abs_mean': float(np.mean(np.abs(coef_values)))  # 用于评估影响强度
                }

            # 确定最主要的影响因素
            if results:
                main_factor = max(
                    results.items(),
                    key=lambda x: x[1]['abs_mean']  # 使用绝对值的平均值判断主要因素
                )
                main_factor_name, main_factor_stats = main_factor

                # 计算精度指标 (1 - 变异系数)
                precision = 1 - (main_factor_stats['std_deviation'] /
                                 main_factor_stats['abs_mean'])
                precision = max(0, min(1, round(precision, 4)))  # 限定在0-1范围内
            else:
                main_factor_name = None
                precision = 0

            # 4. 构建响应JSON
            response = {
                "status": "success",
                "metadata": {
                    "year": year,
                    "region": region,
                    "data_source": shp_path,
                    "sample_size": len(gdf)
                },
                "factors_analysis": results,
                "main_conclusion": {
                    "primary_influence_factor": main_factor_name,
                    "influence_strength": main_factor_stats['abs_mean'] if main_factor_name else 0,
                    "precision": precision,
                    "interpretation": service._get_interpretation(main_factor_name, main_factor_stats[
                        'abs_mean']) if main_factor_name else "无显著影响因素"
                },
                "api_version": "1.0",
                "timestamp": datetime.now().isoformat()
            }

            return jsonify(response), 200

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"分析过程中出错: {str(e)}",
                "traceback": traceback.format_exc()
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"未预期的错误: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

def _get_interpretation(self, factor_name, strength):
    """生成对主要影响因素的解读文本(辅助函数)"""
    interpretations = {
        'temperature': [
            (0.8, "温度是主导因素，强烈影响生态环境"),
            (0.5, "温度是重要影响因素"),
            (0.3, "温度对生态环境有中等影响"),
            (0, "温度影响较小")
        ],
        'rainfall': [
            (0.8, "降雨量是主导因素，强烈影响生态环境"),
            (0.5, "降雨量是重要影响因素"),
            (0.3, "降雨量对生态环境有中等影响"),
            (0, "降雨量影响较小")
        ],
        'fvc': [
            (0.8, "植被覆盖是主导因素，强烈影响生态环境"),
            (0.5, "植被覆盖是重要影响因素"),
            (0, "植被覆盖影响较小")
        ]
    }

    default_msg = f"{factor_name}对生态环境有影响(强度: {round(strength, 2)})"
    thresholds = interpretations.get(factor_name, [(0, default_msg)])

    for threshold, msg in thresholds:
        if strength >= threshold:
            return msg
    return default_msg



# User registration (protected)
@app.route('/register', methods=['OPTIONS', 'POST'])
def register():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight request successful'})
        return add_cors_headers(response)

    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        response = jsonify({'message': 'Missing required fields'})
        return add_cors_headers(response), 400

    success = DB.register(username, email, password)
    if success == -1:
        response = jsonify({'message': 'Username already exists'})
        return add_cors_headers(response), 201
    elif success == 1:
        response = jsonify({'message': 'User registered successfully'})
        return add_cors_headers(response), 200
    else:
        response = jsonify({'message': 'Failed to register user'})
        return add_cors_headers(response), 400

# Token generation
def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# Token verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.replace('Bearer ', '')
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(*args, **kwargs)

    return decorated

# User login (protected)
@app.route('/login', methods=['OPTIONS', 'POST'])
def login_user():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight request successful'})
        return add_cors_headers(response)

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        response = jsonify({'message': 'Username and password are required!'})
        return add_cors_headers(response), 400

    user_id = DB.login(username, password)
    if user_id:
        token = generate_token(user_id)
        response = jsonify({'message': 'Login successful', 'token': token})
        return add_cors_headers(response), 200
    else:
        response = jsonify({'message': 'Invalid username or password'})
        return add_cors_headers(response), 401

# Protected route example
@app.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'This is a protected route!'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6419, debug=True)

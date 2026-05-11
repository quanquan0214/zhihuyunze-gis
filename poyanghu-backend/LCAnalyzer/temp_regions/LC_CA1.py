import sys
import os
import csv
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from RegionCompare.ComparisonAnalyzer import ComparisonAnalyzer
from typing import Dict, List, Any
import tempfile
from shapely.geometry import Polygon
import geopandas as gpd

# Get current directory and add Connect to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'Connect'))
sys.path.append(os.path.join(current_dir, 'AdditionalFunction'))
sys.path.append(os.path.join(current_dir, 'RegionCompare'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pylake'
CORS(app)

# Configuration for predict endpoint
# DATA_DIR = 'D:/Google/RSEI_2000_2022'
# PREDICT_YEARS = 5

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

def csv_to_json_chart_data(csv_file_path):
    # 初始化数据结构
    data = {

        "Time_Series": {},
        "Area_Statistics": {
            "part1": {},
            "part2": {}
        },
        "Change_Trend": {},
        "Normalize": {}

    }

    # 读取CSV文件（使用utf-8-sig自动去除BOM头）
    with open(csv_file_path, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows = list(csv_reader)

    # 按区域分组（直接使用'region_id'，因为BOM已被去除）
    regions = defaultdict(list)
    for row in rows:
        regions[row['region_id']].append(row)

    # 处理每个区域的数据
    for region_id, region_data in regions.items():
        # 按年份排序
        region_data.sort(key=lambda x: int(x['year']))

        # 提取基本信息
        region_name = region_data[0]['region_name']
        area_km2 = region_data[0]['area_km2']

        # Time_Series数据
        data["Time_Series"][region_id] = {
            "region_name": region_name,
            "value": [float(row['mean_value']) for row in region_data]
        }

        # Area_Statistics数据
        data["Area_Statistics"]["part1"][region_id] = {
            "region_name": region_name,
            "area_km2": float(area_km2)
        }
        data["Area_Statistics"]["part2"][region_id] = float(region_data[-1]['mean_value'])

        # Change_Trend数据
        first_value = float(region_data[0]['mean_value'])
        last_value = float(region_data[-1]['mean_value'])
        total_change = last_value - first_value
        annual_avg_change = total_change / (len(region_data) - 1) if len(region_data) > 1 else 0

        data["Change_Trend"][region_id] = {
            "Total of change": total_change,
            "Annual average rate of change": annual_avg_change
        }

        # Normalize数据
        data["Normalize"][region_id] = {
            "region_name": region_name,
            "value": [[float(row['normalized_sum']), float(row['std_value'])] for row in region_data]
        }
    return data

# Add CORS headers to response
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

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
    analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")
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

    output_dir = "D:/Google/output/"
    os.makedirs(output_dir, exist_ok=True)

    # Export data to CSV
    df = analyzer.export_comparison_data(results)
    csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    # print(f"已保存数据文件: RSEI对比数据.csv")

    dataB = csv_to_json_chart_data('D:/Google/output/RSEI对比数据.csv')

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
    if not validate_point_groups(point_groups):
        return jsonify({
            "error": "Invalid point groups. Please provide 2-6 valid point groups, each with at least 3 coordinate points."
        }), 400

    points_mapping = {}
    temp_files = []  # 记录所有临时文件路径

    try:
        # 创建点位映射
        points_mapping = get_points_mapping(point_groups)
        temp_files = [info['path'] for info in points_mapping.values()]

        if not points_mapping:
            return jsonify({"error": "Failed to create valid polygons from point groups"}), 400

        # 初始化分析器
        analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")

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
        output_dir = "D:/Google/output/"
        os.makedirs(output_dir, exist_ok=True)

        # 导出数据到CSV
        df = analyzer.export_comparison_data(results)
        csv_path = os.path.join(output_dir, 'RSEI_Points_对比数据.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        # 转换CSV数据为图表数据
        dataB = csv_to_json_chart_data(csv_path)

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

@app.route('/api/RegionCompare/LC/point', methods=['POST'])
def region_compare_LC_point():
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
    if not validate_point_groups(point_groups):
        return jsonify({
            "error": "Invalid point groups. Please provide 2-6 valid point groups, each with at least 3 coordinate points."
        }), 400

    points_mapping = {}
    temp_files = []  # 记录所有临时文件路径

    try:
        # 创建点位映射
        points_mapping = get_points_mapping(point_groups)
        temp_files = [info['path'] for info in points_mapping.values()]

        if not points_mapping:
            return jsonify({"error": "Failed to create valid polygons from point groups"}), 400

        # 初始化分析器
        analyzer = ComparisonAnalyzer(data_directory="D:/Google/GLC_FCS30/merged/")

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
        output_dir = "D:/Google/output/"
        os.makedirs(output_dir, exist_ok=True)

        # 导出数据到CSV
        df = analyzer.export_comparison_data(results)
        csv_path = os.path.join(output_dir, 'RSEI_Points_对比数据.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        # 转换CSV数据为图表数据
        dataB = csv_to_json_chart_data(csv_path)

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


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7891, debug=True)

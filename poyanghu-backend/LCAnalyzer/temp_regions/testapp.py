from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from typing import Dict, List, Any
import tempfile
import geopandas as gpd
from shapely.geometry import box, shape
from land_cover_analyzer import LandCoverAnalyzer
import traceback

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 初始化分析器
analyzer = LandCoverAnalyzer()

# 配置参数
UPLOAD_FOLDER = 'temp_regions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


def parse_bbox(bbox_str: str) -> Dict:
    """解析边界框字符串为几何对象"""
    try:
        coords = [float(x.strip()) for x in bbox_str.split(',')]
        if len(coords) != 4:
            raise ValueError("边界框需要4个坐标值")

        minx, miny, maxx, maxy = coords
        bbox_geom = box(minx, miny, maxx, maxy)
        return bbox_geom.__geo_interface__
    except Exception as e:
        raise ValueError(f"边界框解析错误: {str(e)}")


def parse_years(years_str: str) -> List[int]:
    """解析年份范围"""
    try:
        if '-' in years_str:
            start, end = years_str.split('-')
            return list(range(int(start), int(end) + 1))
        else:
            return [int(years_str)]
    except Exception as e:
        raise ValueError(f"年份解析错误: {str(e)}")


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
        years = parse_years(years_param)

        # 处理区域几何
        temp_filename = f"timeseries_{hash(region)}"

        try:
            # 尝试解析为GeoJSON
            region_geom = json.loads(region)
            if 'coordinates' not in region_geom:
                raise ValueError("无效的GeoJSON格式")
        except:
            # 尝试解析为边界框
            try:
                region_geom = parse_bbox(region)
            except:
                return jsonify({
                    'error': '无效的区域格式，请提供GeoJSON或边界框坐标',
                    'status': 'error'
                }), 400

        # 创建临时GeoJSON文件
        geojson_path = create_geojson_from_geometry(region_geom, temp_filename)

        try:
            # 提取区域数据
            region_data = analyzer.extract_region_data(geojson_path)

            # 过滤指定年份的数据
            filtered_data = {year: data for year, data in region_data.items() if year in years}

            # 计算相对变化
            relative_changes = analyzer.calculate_relative_change(filtered_data)

            # 计算年际变化率
            annual_changes = analyzer.calculate_annual_change_rates(filtered_data)

            # 检测异常年份
            anomalies = analyzer.detect_anomaly_years(filtered_data)

            # 计算总面积
            total_areas = analyzer._calculate_total_area(filtered_data)

            result = {
                'status': 'success',
                'data': {
                    'raw_data': filtered_data,
                    'relative_changes': relative_changes,
                    'annual_change_rates': annual_changes,
                    'anomalies': anomalies,
                    'total_areas': total_areas,
                    'years': sorted(filtered_data.keys()),
                    'land_types': list(set().union(*[year_data.keys() for year_data in filtered_data.values()]))
                },
                'metadata': {
                    'region_type': 'polygon' if 'coordinates' in str(region_geom) else 'bbox',
                    'years_requested': years,
                    'years_available': sorted(filtered_data.keys())
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
            'traceback': traceback.format_exc()
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
            comparison_data = analyzer.compare_multiple_regions(region_paths, region_names)

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
            comparison_stats = calculate_comparison_stats(comparison_data, metric)

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


@app.route('/api/hotspots', methods=['GET'])
def get_hotspots():
    """
    获取变化热点数据
    参数:
    - change_type: 变化类型(loss, gain, all)
    - land_type: 土地类型(可选)
    - region: 区域几何(可选)
    - threshold: 变化阈值(默认2.0)
    """
    try:
        change_type = request.args.get('change_type', 'all')
        land_type = request.args.get('land_type')
        region = request.args.get('region')
        threshold = float(request.args.get('threshold', 2.0))

        # 如果指定了区域，分析该区域；否则分析所有数据
        if region:
            try:
                region_geom = json.loads(region)
            except:
                try:
                    region_geom = parse_bbox(region)
                except:
                    return jsonify({
                        'error': '无效的区域格式',
                        'status': 'error'
                    }), 400

            temp_filename = f"hotspots_{hash(region)}"
            geojson_path = create_geojson_from_geometry(region_geom, temp_filename)

            try:
                region_data = analyzer.extract_region_data(geojson_path)
                anomalies = analyzer.detect_anomaly_years(region_data, threshold)

            finally:
                if os.path.exists(geojson_path):
                    os.remove(geojson_path)
        else:
            # 这里可以扩展为全局热点分析
            return jsonify({
                'error': '全局热点分析功能待实现，请指定region参数',
                'status': 'error'
            }), 501

        # 过滤结果
        filtered_anomalies = {}
        for ltype, anomaly_list in anomalies.items():
            if land_type and ltype != land_type:
                continue

            filtered_list = []
            for anomaly in anomaly_list:
                if change_type == 'all':
                    filtered_list.append(anomaly)
                elif change_type == 'loss' and anomaly['type'] == 'decrease':
                    filtered_list.append(anomaly)
                elif change_type == 'gain' and anomaly['type'] == 'increase':
                    filtered_list.append(anomaly)

            if filtered_list:
                filtered_anomalies[ltype] = filtered_list

        # 计算热点统计
        hotspot_stats = calculate_hotspot_stats(filtered_anomalies)

        result = {
            'status': 'success',
            'data': {
                'anomalies': filtered_anomalies,
                'hotspot_stats': hotspot_stats
            },
            'metadata': {
                'change_type': change_type,
                'land_type': land_type,
                'threshold': threshold,
                'has_region_filter': region is not None
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': f'处理热点请求时出错: {str(e)}',
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
                region_geom = parse_bbox(region)
            except:
                return jsonify({
                    'error': '无效的区域格式',
                    'status': 'error'
                }), 400

        temp_filename = f"transition_{from_year}_{to_year}_{hash(region)}"
        geojson_path = create_geojson_from_geometry(region_geom, temp_filename)

        try:
            # 创建转换矩阵
            transition_data = analyzer.create_transition_matrix(geojson_path, from_year, to_year)

            if not transition_data:
                return jsonify({
                    'error': f'无法创建 {from_year}-{to_year} 年的转换矩阵',
                    'status': 'error'
                }), 404

            # 计算转换统计
            transition_stats = calculate_transition_stats(transition_data)

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


def calculate_comparison_stats(comparison_data: Dict, metric: str) -> Dict:
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


def calculate_hotspot_stats(anomalies: Dict) -> Dict:
    """计算热点统计数据"""
    stats = {
        'total_anomalies': 0,
        'by_land_type': {},
        'by_change_type': {'increase': 0, 'decrease': 0},
        'most_active_years': {}
    }

    year_counts = {}

    for land_type, anomaly_list in anomalies.items():
        stats['by_land_type'][land_type] = len(anomaly_list)
        stats['total_anomalies'] += len(anomaly_list)

        for anomaly in anomaly_list:
            stats['by_change_type'][anomaly['type']] += 1
            year = anomaly['year']
            year_counts[year] = year_counts.get(year, 0) + 1

    # 找出最活跃的年份
    if year_counts:
        sorted_years = sorted(year_counts.items(), key=lambda x: x[1], reverse=True)
        stats['most_active_years'] = dict(sorted_years[:5])

    return stats


def calculate_transition_stats(transition_data: Dict) -> Dict:
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


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': 'land-cover-api',
        'version': '1.0.0',
        'available_years': analyzer.years
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': '接口不存在',
        'status': 'error',
        'available_endpoints': [
            '/api/timeseries',
            '/api/compare',
            '/api/hotspots',
            '/api/transition',
            '/api/health'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': '服务器内部错误',
        'status': 'error'
    }), 500


if __name__ == '__main__':
    print("启动土地覆盖分析API服务...")
    print("可用接口:")
    print("- GET /api/timeseries?region=<geometry>&years=<range>")
    print("- GET /api/compare?regions=<regions_json>&metric=<metric>")
    print("- GET /api/hotspots?change_type=<type>&land_type=<type>")
    print("- GET /api/transition?from_year=<year>&to_year=<year>&region=<geometry>")
    print("- GET /api/health")

    app.run(debug=True, host='0.0.0.0', port=7891)
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import tempfile
import traceback
from datetime import datetime
import base64
import io
import zipfile

# 导入功能类
from ComparisonAnalyzer import ComparisonAnalyzer
from RasterAnalyzer import RasterAnalyzer
from RegionProcessor import RegionProcessor
from Visualize import VisualizationGenerator

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量存储分析器实例
analyzers = {}
region_processors = {}


def get_analyzer_id():
    """生成唯一的分析器ID"""
    return f"analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

@app.route('/')
def index():
    return 'Welcome to Web_pylake.'

@app.errorhandler(Exception)
def handle_error(error):
    """全局错误处理"""
    return jsonify({
        'success': False,
        'error': str(error),
        'traceback': traceback.format_exc()
    }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': 'Regional Comparison Analysis API is running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/analyzer/create', methods=['POST'])
def create_analyzer():
    """创建新的分析器实例"""
    try:
        data = request.json
        raster_data_path = data.get('raster_data_path', './data')

        analyzer_id = get_analyzer_id()

        # 创建各个组件实例
        raster_analyzer = RasterAnalyzer(raster_data_path)
        region_processor = RegionProcessor()
        comparison_analyzer = ComparisonAnalyzer(raster_data_path)
        visualization_generator = VisualizationGenerator()

        # 存储实例
        analyzers[analyzer_id] = {
            'comparison': comparison_analyzer,
            'raster': raster_analyzer,
            'region': region_processor,
            'visualization': visualization_generator,
            'created_at': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'analyzer_id': analyzer_id,
            'message': 'Analyzer created successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# @app.route('/api/analyzer/<analyzer_id>/regions/add', methods=['POST'])
# def add_region(analyzer_id):
#     """添加分析区域"""
#     try:
#         if analyzer_id not in analyzers:
#             return jsonify({'success': False, 'error': 'Analyzer not found'}), 404
#
#         data = request.json
#         region_processor = analyzers[analyzer_id]['region']
#
#         region_id = data.get('region_id')
#         region_type = data.get('type', 'points')  # 'points' or 'vector'
#
#         if region_type == 'points':
#             # 从点坐标添加区域
#             points = data.get('points', [])  # [[lon, lat], [lon, lat], ...]
#             region_name = data.get('name', f'Region_{region_id}')
#
#             region_processor.add_region_from_points(
#                 points=points,
#                 name=region_name,
#                 region_id=region_id
#             )
#
#         elif region_type == 'vector':
#             # 从矢量文件添加区域
#             vector_path = data.get('vector_path')
#             layer_name = data.get('layer_name')
#
#             region_processor.add_region_from_vector(
#                 vector_path=vector_path,
#                 layer_name=layer_name,
#                 region_id=region_id
#             )
#
#         return jsonify({
#             'success': True,
#             'message': f'Region {region_id} added successfully'
#         })
#
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'traceback': traceback.format_exc()
#         }), 500
@app.route('/api/analyzer/<analyzer_id>/regions/add', methods=['POST'])
def add_region(analyzer_id):
    """添加分析区域"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        data = request.json
        region_processor = analyzers[analyzer_id]['region']

        region_id = data.get('region_id')  # 现在这个参数会被传递给方法
        region_type = data.get('type', 'points')

        if region_type == 'points':
            points = data.get('points', [])
            region_name = data.get('name', f'Region_{region_id}')

            # 修改后的调用方式
            added_region_id = region_processor.add_region_from_points(
                points=points,
                region_name=region_name,
                region_id=region_id,  # 传递自定义ID
                crs='EPSG:4326'
            )

        elif region_type == 'vector':
            vector_path = data.get('vector_path')
            layer_name = data.get('layer_name')
            region_name = data.get('name', f'Region_{region_id}')

            added_region_id = region_processor.add_region_from_vector(
                vector_data=vector_path,
                region_name=region_name,
                region_id=region_id
            )

        return jsonify({
            'success': True,
            'message': f'Region {added_region_id} added successfully',
            'region_id': added_region_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/analyzer/<analyzer_id>/regions', methods=['GET'])
def get_regions(analyzer_id):
    """获取所有区域信息"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        region_processor = analyzers[analyzer_id]['region']
        regions = region_processor.get_all_regions()

        # 转换为可序列化的格式
        regions_info = {}
        for region_id, region_data in regions.items():
            regions_info[region_id] = {
                'name': region_data.get('name', region_id),
                'area_km2': region_data.get('area_km2', 0),
                'bounds': region_data.get('bounds', []),
                'geometry_type': str(type(region_data.get('geometry', '')).__name__)
            }

        return jsonify({
            'success': True,
            'regions': regions_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/comparison/analyze', methods=['POST'])
def run_comparison_analysis(analyzer_id):
    """执行区域对比分析"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404
        data = request.json
        comparison_analyzer = analyzers[analyzer_id]['comparison']
        print("33333")
        # 添加要分析的区域
        region_ids = data.get('region_ids', [])
        for region_id in region_ids:
            print("region_id:",region_id)
            comparison_analyzer.add_analysis_region(region_id)
        print("44444")
        # 执行并行对比分析
        analysis_params = data.get('analysis_params', {})
        results = comparison_analyzer.parallel_comparison_analysis(**analysis_params)
        print("55555")
        # 转换结果为可序列化格式
        serializable_results = {}
        for region_id, result in results.items():
            serializable_results[region_id] = {
                'statistics': result.get('statistics', {}),
                'trends': result.get('trends', {}),
                'normalized_metrics': result.get('normalized_metrics', {}),
                'summary': result.get('summary', {})
            }

        return jsonify({
            'success': True,
            'results': serializable_results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/comparison/charts', methods=['POST'])
def generate_comparison_charts(analyzer_id):
    """生成对比图表"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        data = request.json
        comparison_analyzer = analyzers[analyzer_id]['comparison']

        # 添加要分析的区域
        region_ids = data.get('region_ids', [])
        for region_id in region_ids:
            comparison_analyzer.add_analysis_region(region_id)

        # 生成图表
        chart_params = data.get('chart_params', {})
        charts = comparison_analyzer.generate_comparison_charts(**chart_params)

        return jsonify({
            'success': True,
            'charts': charts  # 返回base64编码的图表
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/visualization/dashboard', methods=['POST'])
def create_dashboard(analyzer_id):
    """创建综合仪表板"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        data = request.json
        visualization_generator = analyzers[analyzer_id]['visualization']
        comparison_analyzer = analyzers[analyzer_id]['comparison']

        # 添加要分析的区域
        region_ids = data.get('region_ids', [])
        for region_id in region_ids:
            comparison_analyzer.add_analysis_region(region_id)

        # 执行分析获取数据
        analysis_results = comparison_analyzer.parallel_comparison_analysis()

        # 创建仪表板
        dashboard_params = data.get('dashboard_params', {})
        dashboard = visualization_generator.create_comprehensive_dashboard(
            analysis_results, **dashboard_params
        )

        return jsonify({
            'success': True,
            'dashboard': dashboard
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/visualization/time_series', methods=['POST'])
def create_time_series(analyzer_id):
    """创建详细时间序列图表"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        data = request.json
        visualization_generator = analyzers[analyzer_id]['visualization']
        comparison_analyzer = analyzers[analyzer_id]['comparison']

        # 添加要分析的区域
        region_ids = data.get('region_ids', [])
        for region_id in region_ids:
            comparison_analyzer.add_analysis_region(region_id)

        # 执行分析获取数据
        analysis_results = comparison_analyzer.parallel_comparison_analysis()

        # 创建时间序列图表
        time_series_params = data.get('time_series_params', {})
        time_series_chart = visualization_generator.create_detailed_time_series(
            analysis_results, **time_series_params
        )

        return jsonify({
            'success': True,
            'time_series_chart': time_series_chart
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/export', methods=['POST'])
def export_comparison_data(analyzer_id):
    """导出对比分析数据"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        data = request.json
        comparison_analyzer = analyzers[analyzer_id]['comparison']

        # 添加要分析的区域
        region_ids = data.get('region_ids', [])
        for region_id in region_ids:
            comparison_analyzer.add_analysis_region(region_id)

        # 导出数据
        export_params = data.get('export_params', {})
        export_format = export_params.get('format', 'json')  # 'json', 'csv', 'excel'

        exported_data = comparison_analyzer.export_comparison_data(
            format=export_format,
            **export_params
        )

        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': exported_data
            })
        else:
            # 对于文件格式，返回下载链接或base64编码
            return jsonify({
                'success': True,
                'download_data': exported_data,
                'format': export_format
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/regions/<region_id>/statistics', methods=['GET'])
def get_region_statistics(analyzer_id, region_id):
    """获取单个区域的统计信息"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        raster_analyzer = analyzers[analyzer_id]['raster']
        region_processor = analyzers[analyzer_id]['region']

        # 获取区域几何
        region = region_processor.get_region(region_id)
        if not region:
            return jsonify({'success': False, 'error': 'Region not found'}), 404

        # 提取统计信息
        years = request.args.getlist('years')  # 可选的年份列表
        if years:
            years = [int(year) for year in years]
            statistics = raster_analyzer.extract_multi_year_statistics(
                region['geometry'], years
            )
        else:
            statistics = raster_analyzer.extract_region_statistics(
                region['geometry']
            )

        return jsonify({
            'success': True,
            'region_id': region_id,
            'statistics': statistics
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/delete', methods=['DELETE'])
def delete_analyzer(analyzer_id):
    """删除分析器实例"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        del analyzers[analyzer_id]

        return jsonify({
            'success': True,
            'message': f'Analyzer {analyzer_id} deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzers', methods=['GET'])
def list_analyzers():
    """列出所有分析器实例"""
    try:
        analyzer_list = []
        for analyzer_id, analyzer_data in analyzers.items():
            analyzer_list.append({
                'analyzer_id': analyzer_id,
                'created_at': analyzer_data['created_at'],
                'regions_count': len(analyzer_data['region'].get_all_regions())
            })

        return jsonify({
            'success': True,
            'analyzers': analyzer_list
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyzer/<analyzer_id>/available_data', methods=['GET'])
def get_available_data(analyzer_id):
    """获取可用的栅格数据信息"""
    try:
        if analyzer_id not in analyzers:
            return jsonify({'success': False, 'error': 'Analyzer not found'}), 404

        raster_analyzer = analyzers[analyzer_id]['raster']

        # 获取可用数据信息（假设RasterAnalyzer有这个方法）
        if hasattr(raster_analyzer, 'get_available_data'):
            available_data = raster_analyzer.get_available_data()
        else:
            available_data = {
                'message': 'Available data scanning not implemented',
                'data_path': raster_analyzer.data_path if hasattr(raster_analyzer, 'data_path') else 'Unknown'
            }

        return jsonify({
            'success': True,
            'available_data': available_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # 创建临时目录用于存储导出文件
    os.makedirs('./temp', exist_ok=True)

    # 启动Flask应用
    app.run(host='0.0.0.0',port=7891,debug=True)




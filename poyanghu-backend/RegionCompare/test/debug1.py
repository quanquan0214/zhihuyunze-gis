import requests
import json
import traceback
from pathlib import Path


def debug_api_error():
    """调试API错误的详细脚本"""

    print("🔍 API错误调试分析")
    print("=" * 60)

    # API基础URL
    api_base_url = "http://localhost:7891"

    # 1. 测试健康检查
    print("\n1️⃣ 测试API健康状态...")
    try:
        response = requests.get(f"{api_base_url}/api/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return

    # 2. 创建分析器
    print("\n2️⃣ 创建分析器...")
    try:
        response = requests.post(f"{api_base_url}/api/analyzer/create",
                                 json={"raster_data_path": "./data"})
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {result}")

        if not result.get('success'):
            print("   ❌ 分析器创建失败")
            return

        analyzer_id = result['analyzer_id']
        print(f"   ✅ 分析器ID: {analyzer_id}")

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return

    # 3. 添加测试区域（简单的矩形区域）
    print("\n3️⃣ 添加测试区域...")
    test_points = [
        [115.0, 28.0],  # 左下角
        [116.0, 28.0],  # 右下角
        [116.0, 29.0],  # 右上角
        [115.0, 29.0],  # 左上角
        [115.0, 28.0]  # 闭合
    ]

    try:
        response = requests.post(f"{api_base_url}/api/analyzer/{analyzer_id}/regions/add",
                                 json={
                                     "region_id": "test_region",
                                     "type": "points",
                                     "points": test_points,
                                     "name": "测试区域"
                                 })
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {result}")

        if not result.get('success'):
            print("   ❌ 区域添加失败")
            return

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return

    # 4. 测试区域信息获取
    print("\n4️⃣ 获取区域信息...")
    try:
        response = requests.get(f"{api_base_url}/api/analyzer/{analyzer_id}/regions")
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {result}")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 5. 测试分析功能 - 这里是关键
    print("\n5️⃣ 测试对比分析功能...")
    try:
        # 简化的分析参数
        simple_params = {
            'start_year': 2020,
            'end_year': 2021,  # 只测试2年
            'metrics': ['mean'],  # 只测试一个指标
            'normalize': False
        }

        response = requests.post(f"{api_base_url}/api/analyzer/{analyzer_id}/comparison/analyze",
                                 json={
                                     "region_ids": ["test_region"],
                                     "analysis_params": simple_params
                                 })

        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")

        if response.status_code == 500:
            print("   ❌ 500内部服务器错误")
            print("   响应内容:")
            try:
                error_result = response.json()
                print(f"   错误信息: {error_result.get('error', 'Unknown')}")
                if 'traceback' in error_result:
                    print("   详细错误堆栈:")
                    print(error_result['traceback'])
            except:
                print(f"   原始响应: {response.text}")
        else:
            result = response.json()
            print(f"   响应: {result}")

    except Exception as e:
        print(f"   ❌ 请求错误: {e}")

    # 6. 测试可用数据接口
    print("\n6️⃣ 检查可用数据...")
    try:
        response = requests.get(f"{api_base_url}/api/analyzer/{analyzer_id}/available_data")
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {result}")

    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 7. 清理
    print("\n7️⃣ 清理分析器...")
    try:
        response = requests.delete(f"{api_base_url}/api/analyzer/{analyzer_id}/delete")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {result}")
    except Exception as e:
        print(f"   ❌ 清理错误: {e}")

    print("\n" + "=" * 60)
    print("🔍 调试完成")


def check_missing_components():
    """检查可能缺失的组件"""

    print("\n🔧 检查系统组件")
    print("-" * 40)

    # 检查必要的Python包
    required_packages = [
        'flask', 'flask_cors', 'requests', 'geopandas',
        'pandas', 'numpy', 'matplotlib', 'seaborn',
        'plotly', 'rasterio', 'shapely', 'fiona'
    ]

    missing_packages = []

    print("📦 检查Python包:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - 未安装")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️ 缺失的包: {', '.join(missing_packages)}")
        print("安装命令:")
        print(f"pip install {' '.join(missing_packages)}")

    # 检查数据目录
    print("\n📁 检查数据目录:")
    data_paths = ["./data", "D:/Google/GLC_FCS30"]

    for path in data_paths:
        path_obj = Path(path)
        if path_obj.exists():
            print(f"   ✅ {path} - 存在")
            if path_obj.is_dir():
                files = list(path_obj.glob("*"))
                print(f"      包含 {len(files)} 个文件/目录")
                # 显示前5个文件
                for file in files[:5]:
                    print(f"      - {file.name}")
                if len(files) > 5:
                    print(f"      - ... 还有 {len(files) - 5} 个")
        else:
            print(f"   ❌ {path} - 不存在")


def analyze_error_patterns():
    """分析可能的错误模式"""

    print("\n🎯 可能的错误原因分析")
    print("-" * 40)

    error_scenarios = [
        {
            "原因": "缺少必要的Python类文件",
            "描述": "ComparisonAnalyzer, RasterAnalyzer, RegionProcessor, VisualizationGenerator等类未找到",
            "解决方案": "确保所有类文件在同一目录下或Python路径中"
        },
        {
            "原因": "栅格数据路径问题",
            "描述": "RasterAnalyzer无法找到或读取栅格数据",
            "解决方案": "检查./data目录是否存在且包含必要的栅格文件"
        },
        {
            "原因": "内存不足",
            "描述": "处理大型栅格数据时内存溢出",
            "解决方案": "减少分析年份范围或使用更小的测试区域"
        },
        {
            "原因": "依赖包版本冲突",
            "描述": "geopandas, rasterio等包版本不兼容",
            "解决方案": "更新到兼容版本或使用虚拟环境"
        },
        {
            "原因": "坐标系转换问题",
            "描述": "EPSG:4490坐标系处理出错",
            "解决方案": "转换为更常用的EPSG:4326坐标系"
        }
    ]

    for i, scenario in enumerate(error_scenarios, 1):
        print(f"{i}. {scenario['原因']}")
        print(f"   描述: {scenario['描述']}")
        print(f"   解决方案: {scenario['解决方案']}")
        print()


# def create_minimal_test_classes():
#     """创建最小测试类来排除问题"""
#
#     print("\n🧪 创建最小测试类")
#     print("-" * 40)
#
#     # 创建测试用的最小类文件
#     test_classes = {
#         "TestComparisonAnalyzer.py": '''
# class ComparisonAnalyzer:
#     def __init__(self, data_path):
#         self.data_path = data_path
#         self.regions = []
#
#     def add_analysis_region(self, region_id):
#         self.regions.append(region_id)
#         return True
#
#     def parallel_comparison_analysis(self, **kwargs):
#         # 返回模拟数据
#         results = {}
#         for region_id in self.regions:
#             results[region_id] = {
#                 'statistics': {'mean': 0.5, 'std': 0.1},
#                 'trends': {'slope': 0.01},
#                 'normalized_metrics': {'norm_mean': 0.6},
#                 'summary': {'status': 'success'}
#             }
#         return results
#
#     def generate_comparison_charts(self, **kwargs):
#         return {'test_chart': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='}
#
#     def export_comparison_data(self, format='json', **kwargs):
#         if format == 'json':
#             return {'test_data': 'success'}
#         return 'test,data\\n1,2'
# ''',
#
#         "TestRasterAnalyzer.py": '''
# class RasterAnalyzer:
#     def __init__(self, data_path):
#         self.data_path = data_path
#
#     def extract_region_statistics(self, geometry):
#         return {'mean': 0.5, 'std': 0.1, 'count': 1000}
#
#     def extract_multi_year_statistics(self, geometry, years):
#         results = {}
#         for year in years:
#             results[year] = {'mean': 0.5, 'std': 0.1}
#         return results
#
#     def get_available_data(self):
#         return {'data_path': self.data_path, 'status': 'test_mode'}
# ''',
#
#         "TestRegionProcessor.py": '''
# class RegionProcessor:
#     def __init__(self):
#         self.regions = {}
#
#     def add_region_from_points(self, points, region_name, region_id=None, crs='EPSG:4326'):
#         if region_id is None:
#             region_id = f"region_{len(self.regions)}"
#
#         self.regions[region_id] = {
#             'name': region_name,
#             'geometry': f'test_geometry_{region_id}',
#             'area_km2': 1000.0,
#             'bounds': [115.0, 28.0, 116.0, 29.0]
#         }
#         return region_id
#
#     def add_region_from_vector(self, vector_data, region_name, region_id=None):
#         return self.add_region_from_points([], region_name, region_id)
#
#     def get_all_regions(self):
#         return self.regions
#
#     def get_region(self, region_id):
#         return self.regions.get(region_id)
# ''',
#
#         "TestVisualize.py": '''
# class VisualizationGenerator:
#     def __init__(self):
#         pass
#
#     def create_comprehensive_dashboard(self, analysis_results, **kwargs):
#         return '<html><body><h1>Test Dashboard</h1></body></html>'
#
#     def create_detailed_time_series(self, analysis_results, **kwargs):
#         return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
# '''
#     }
#
#     for filename, content in test_classes.items():
#         try:
#             with open(filename, 'w', encoding='utf-8') as f:
#                 f.write(content)
#             print(f"   ✅ 创建 {filename}")
#         except Exception as e:
#             print(f"   ❌ 创建 {filename} 失败: {e}")
#
#     print("\n💡 如果问题仍然存在，请尝试:")
#     print("   1. 将这些测试类文件复制到app.py同目录")
#     print("   2. 修改app.py中的import语句:")
#     print("      from TestComparisonAnalyzer import ComparisonAnalyzer")
#     print("      from TestRasterAnalyzer import RasterAnalyzer")
#     print("      from TestRegionProcessor import RegionProcessor")
#     print("      from TestVisualize import VisualizationGenerator")
#     print("   3. 重启Flask应用")


if __name__ == "__main__":
    # 运行完整的调试流程
    debug_api_error()
    check_missing_components()
    analyze_error_patterns()
    #create_minimal_test_classes()
import requests
import json
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import time
import base64
from io import BytesIO
import warnings

warnings.filterwarnings('ignore')


class RegionalComparisonClient:
    """区域对比分析客户端"""

    def __init__(self, api_base_url="http://localhost:7891"):
        """初始化客户端

        Args:
            api_base_url (str): API服务器基础URL
        """
        self.api_base_url = api_base_url
        self.analyzer_id = None

    def create_analyzer(self, raster_data_path="./data"):
        """创建分析器实例"""
        url = f"{self.api_base_url}/api/analyzer/create"
        payload = {"raster_data_path": raster_data_path}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                self.analyzer_id = result['analyzer_id']
                print(f"✅ 分析器创建成功，ID: {self.analyzer_id}")
                return True
            else:
                print(f"❌ 分析器创建失败: {result['error']}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return False

    def load_geojson_data(self, file_path):
        """读取GeoJSON数据"""
        try:
            gdf = gpd.read_file(file_path)
            print(f"✅ 成功读取 {file_path}")
            print(f"   - 记录数: {len(gdf)}")
            print(f"   - 坐标系: {gdf.crs}")
            print(f"   - 列名: {list(gdf.columns)}")
            return gdf
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path}: {e}")
            return None

    def extract_geometry_points(self, gdf):
        """从GeoDataFrame提取几何边界点"""
        points = []
        for geom in gdf.geometry:
            if geom.geom_type == 'Polygon':
                coords = list(geom.exterior.coords)
            elif geom.geom_type == 'MultiPolygon':
                # 对于多多边形，取第一个多边形
                coords = list(geom.geoms[0].exterior.coords)
            else:
                continue

            # 转换为 [lon, lat] 格式
            points.extend([[coord[0], coord[1]] for coord in coords])

        return points

    def add_region_from_geojson(self, geojson_path, region_id, region_name=None):
        """从GeoJSON文件添加区域"""
        if not self.analyzer_id:
            print("❌ 请先创建分析器")
            return False

        # 读取GeoJSON数据
        gdf = self.load_geojson_data(geojson_path)
        if gdf is None:
            return False

        # 提取几何点
        points = self.extract_geometry_points(gdf)
        if not points:
            print(f"❌ 无法从 {geojson_path} 提取几何点")
            return False

        # 调用API添加区域
        url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/regions/add"
        payload = {
            "region_id": region_id,
            "type": "points",
            "points": points,
            "name": region_name or region_id
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                print(f"✅ 区域 {region_id} 添加成功")
                return True
            else:
                print(f"❌ 区域 {region_id} 添加失败: {result['error']}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 添加区域请求失败: {e}")
            return False

    def get_regions_info(self):
        """获取所有区域信息"""
        if not self.analyzer_id:
            print("❌ 请先创建分析器")
            return None

        url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/regions"

        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                return result['regions']
            else:
                print(f"❌ 获取区域信息失败: {result['error']}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 获取区域信息请求失败: {e}")
            return None

    def run_comparison_analysis(self, region_ids, analysis_params=None):
        """执行区域对比分析"""
        if not self.analyzer_id:
            print("❌ 请先创建分析器")
            return None

        url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/comparison/analyze"

        if analysis_params is None:
            analysis_params = {
                'start_year': 2015,
                'end_year': 2023,
                'metrics': ['mean', 'std', 'trend'],
                'normalize': True
            }

        payload = {
            "region_ids": region_ids,
            "analysis_params": analysis_params
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                print("✅ 区域对比分析完成")
                return result['results']
            else:
                print(f"❌ 区域对比分析失败: {result['error']}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 分析请求失败: {e}")
            return None

    def generate_comparison_charts(self, region_ids, chart_params=None):
        """生成对比图表"""
        if not self.analyzer_id:
            print("❌ 请先创建分析器")
            return None

        url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/comparison/charts"

        if chart_params is None:
            chart_params = {
                'chart_types': ['time_series', 'box_plot', 'correlation'],
                'figsize': [12, 8],
                'dpi': 300
            }

        payload = {
            "region_ids": region_ids,
            "chart_params": chart_params
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                print("✅ 对比图表生成完成")
                return result['charts']
            else:
                print(f"❌ 图表生成失败: {result['error']}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 图表生成请求失败: {e}")
            return None

    def create_dashboard(self, region_ids, dashboard_params=None):
        """创建综合仪表板"""
        if not self.analyzer_id:
            print("❌ 请先创建分析器")
            return None

        url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/visualization/dashboard"

        if dashboard_params is None:
            dashboard_params = {
                'include_maps': True,
                'include_statistics': True,
                'include_trends': True,
                'theme': 'plotly_white'
            }

        payload = {
            "region_ids": region_ids,
            "dashboard_params": dashboard_params
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                print("✅ 综合仪表板创建完成")
                return result['dashboard']
            else:
                print(f"❌ 仪表板创建失败: {result['error']}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 仪表板创建请求失败: {e}")
            return None

    def export_analysis_data(self, region_ids, export_params=None):
        """导出分析数据"""
        if not self.analyzer_id:
            print("❌ 请先创建分析器")
            return None

        url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/export"

        if export_params is None:
            export_params = {
                'format': 'json',
                'include_raw_data': True,
                'include_statistics': True,
                'include_charts': False
            }

        payload = {
            "region_ids": region_ids,
            "export_params": export_params
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result['success']:
                print("✅ 分析数据导出完成")
                return result
            else:
                print(f"❌ 数据导出失败: {result['error']}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 数据导出请求失败: {e}")
            return None

    def save_base64_image(self, base64_data, filename):
        """保存base64编码的图片"""
        try:
            # 解码base64数据
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',')[1]

            image_data = base64.b64decode(base64_data)

            # 保存图片
            with open(filename, 'wb') as f:
                f.write(image_data)

            print(f"✅ 图片已保存: {filename}")
            return True

        except Exception as e:
            print(f"❌ 保存图片失败: {e}")
            return False

    def cleanup(self):
        """清理分析器"""
        if self.analyzer_id:
            url = f"{self.api_base_url}/api/analyzer/{self.analyzer_id}/delete"
            try:
                response = requests.delete(url)
                if response.status_code == 200:
                    print(f"✅ 分析器 {self.analyzer_id} 已清理")
            except:
                pass


def main():
    """主函数：执行完整的区域对比分析流程"""

    print("🚀 开始区域对比分析")
    print("=" * 50)

    # 配置文件路径
    data_dir = Path(r"D:\Google\GLC_FCS30")
    jiujiang_file = data_dir / "九江市_市.geojson"
    nanchang_file = data_dir / "南昌市_市.geojson"

    # 检查文件是否存在
    if not jiujiang_file.exists():
        print(f"❌ 文件不存在: {jiujiang_file}")
        return

    if not nanchang_file.exists():
        print(f"❌ 文件不存在: {nanchang_file}")
        return

    # 创建分析客户端
    client = RegionalComparisonClient()

    try:
        # 1. 创建分析器
        print("\n📊 步骤1: 创建分析器")
        if not client.create_analyzer(raster_data_path=str(data_dir)):
            return

        # 2. 添加分析区域
        print("\n📍 步骤2: 添加分析区域")

        # 添加九江市
        if not client.add_region_from_geojson(
                str(jiujiang_file),
                region_id="jiujiang",
                region_name="九江市"
        ):
            return

        # 添加南昌市
        if not client.add_region_from_geojson(
                str(nanchang_file),
                region_id="nanchang",
                region_name="南昌市"
        ):
            return

        # 3. 查看区域信息
        print("\n📋 步骤3: 查看区域信息")
        regions_info = client.get_regions_info()
        if regions_info:
            for region_id, info in regions_info.items():
                print(f"   - {region_id}: {info['name']}")
                print(f"     面积: {info['area_km2']:.2f} km²")
                print(f"     边界: {info['bounds']}")

        # 4. 配置分析参数
        print("\n⚙️ 步骤4: 配置分析参数")
        analysis_params = {
            'start_year': 2015,
            'end_year': 2023,
            'metrics': ['mean', 'std', 'min', 'max', 'trend'],
            'normalize': True,
            'seasonal_analysis': True
        }
        print(f"   分析年份范围: {analysis_params['start_year']}-{analysis_params['end_year']}")
        print(f"   分析指标: {', '.join(analysis_params['metrics'])}")

        # 5. 执行区域对比分析
        print("\n🔍 步骤5: 执行区域对比分析")
        region_ids = ["jiujiang", "nanchang"]
        analysis_results = client.run_comparison_analysis(region_ids, analysis_params)

        if analysis_results:
            print("   分析结果概览:")
            for region_id, result in analysis_results.items():
                print(f"   - {region_id}:")
                if 'statistics' in result:
                    stats = result['statistics']
                    print(f"     统计信息: {len(stats)} 项指标")
                if 'trends' in result:
                    trends = result['trends']
                    print(f"     趋势分析: {len(trends)} 项趋势")

        # 6. 生成对比图表
        print("\n📈 步骤6: 生成对比图表")
        chart_params = {
            'chart_types': ['time_series', 'box_plot', 'correlation', 'trend_comparison'],
            'figsize': [15, 10],
            'dpi': 300,
            'save_format': 'png'
        }

        charts = client.generate_comparison_charts(region_ids, chart_params)
        if charts:
            print(f"   生成图表数量: {len(charts)}")
            # 保存图表
            for chart_name, chart_data in charts.items():
                filename = f"chart_{chart_name}_{int(time.time())}.png"
                client.save_base64_image(chart_data, filename)

        # 7. 创建综合仪表板
        print("\n📊 步骤7: 创建综合仪表板")
        dashboard_params = {
            'include_maps': True,
            'include_statistics': True,
            'include_trends': True,
            'include_comparison': True,
            'theme': 'plotly_white',
            'title': '九江市与南昌市区域对比分析仪表板'
        }

        dashboard = client.create_dashboard(region_ids, dashboard_params)
        if dashboard:
            print("   ✅ 综合仪表板创建成功")
            # 如果仪表板包含HTML内容，可以保存为文件
            if isinstance(dashboard, str) and '<html' in dashboard.lower():
                with open(f'dashboard_{int(time.time())}.html', 'w', encoding='utf-8') as f:
                    f.write(dashboard)
                print("   仪表板已保存为HTML文件")

        # 8. 导出分析数据
        print("\n💾 步骤8: 导出分析数据")

        # 导出JSON格式
        export_params_json = {
            'format': 'json',
            'include_raw_data': True,
            'include_statistics': True,
            'include_metadata': True
        }

        export_result = client.export_analysis_data(region_ids, export_params_json)
        if export_result and 'data' in export_result:
            filename = f'analysis_results_{int(time.time())}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_result['data'], f, ensure_ascii=False, indent=2)
            print(f"   ✅ 分析数据已导出为JSON: {filename}")

        # 导出CSV格式
        export_params_csv = {
            'format': 'csv',
            'include_statistics': True,
            'flatten_structure': True
        }

        csv_result = client.export_analysis_data(region_ids, export_params_csv)
        if csv_result:
            print("   ✅ CSV格式数据导出完成")

        print("\n🎉 区域对比分析完成!")
        print("=" * 50)
        print("分析结果包括:")
        print("✓ 区域统计对比")
        print("✓ 时间序列趋势分析")
        print("✓ 可视化图表")
        print("✓ 综合仪表板")
        print("✓ 导出数据文件")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断分析")
    except Exception as e:
        print(f"\n❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n🧹 清理分析器...")
        client.cleanup()


def test_api_connection():
    """测试API连接"""
    client = RegionalComparisonClient()
    url = f"{client.api_base_url}/api/health"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = response.json()

        if result['success']:
            print("✅ API服务连接正常")
            print(f"   消息: {result['message']}")
            return True
        else:
            print("❌ API服务响应异常")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到API服务: {e}")
        print("请确保Flask应用正在运行 (python app.py)")
        return False


if __name__ == "__main__":
    # 首先测试API连接
    print("🔗 测试API连接...")
    if test_api_connection():
        # 执行主分析流程
        main()
    else:
        print("\n请先启动Flask API服务:")
        print("python app.py")
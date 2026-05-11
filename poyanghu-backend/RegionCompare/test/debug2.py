import requests
import json
import base64
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from io import BytesIO
import geopandas as gpd
from shapely.geometry import mapping
import time


class RegionComparisonTester:
    def __init__(self, base_url="http://localhost:7891"):
        """
        初始化测试器

        Args:
            base_url: Flask应用的基础URL
        """
        self.base_url = base_url
        self.analyzer_id = None
        self.session = requests.Session()

    def test_health(self):
        """测试API健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                print("✓ API健康检查通过")
                return True
            else:
                print(f"✗ API健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 无法连接到API: {e}")
            return False

    def create_analyzer(self, raster_data_path="./data"):
        """创建分析器实例"""
        try:
            data = {"raster_data_path": raster_data_path}
            response = self.session.post(
                f"{self.base_url}/api/analyzer/create",
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    self.analyzer_id = result['analyzer_id']
                    print(f"✓ 分析器创建成功，ID: {self.analyzer_id}")
                    return True
                else:
                    print(f"✗ 分析器创建失败: {result.get('error', '未知错误')}")
                    return False
            else:
                print(f"✗ 分析器创建请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 创建分析器时发生错误: {e}")
            return False

    def load_geojson_region(self, geojson_path):
        """
        从GeoJSON文件加载区域数据

        Args:
            geojson_path: GeoJSON文件路径

        Returns:
            区域点坐标列表和区域名称
        """
        try:
            # 使用geopandas读取GeoJSON文件
            gdf = gpd.read_file(geojson_path)

            if len(gdf) == 0:
                raise ValueError("GeoJSON文件为空")

            # 获取第一个几何体
            geometry = gdf.geometry.iloc[0]

            # 获取区域名称（尝试从不同的字段获取）
            region_name = None
            for col in ['name', 'NAME', 'Name', '名称', 'region_name']:
                if col in gdf.columns:
                    region_name = str(gdf[col].iloc[0])
                    break

            if not region_name:
                # 从文件名推导区域名称
                import os
                region_name = os.path.splitext(os.path.basename(geojson_path))[0]

            # 将几何体转换为点坐标列表
            if geometry.geom_type == 'Polygon':
                # 对于多边形，获取外环坐标
                coords = list(geometry.exterior.coords)
            elif geometry.geom_type == 'MultiPolygon':
                # 对于多多边形，获取第一个多边形的外环坐标
                coords = list(geometry.geoms[0].exterior.coords)
            else:
                raise ValueError(f"不支持的几何类型: {geometry.geom_type}")

            # 转换为 [[lon, lat], [lon, lat], ...] 格式
            points = [[coord[0], coord[1]] for coord in coords]

            print(f"✓ 成功加载区域: {region_name} ({len(points)} 个点)")
            return points, region_name

        except Exception as e:
            print(f"✗ 加载GeoJSON文件失败 {geojson_path}: {e}")
            return None, None

    def add_region(self, geojson_path, region_id):
        """
        添加区域到分析器

        Args:
            geojson_path: GeoJSON文件路径
            region_id: 自定义区域ID
        """
        if not self.analyzer_id:
            print("✗ 请先创建分析器")
            return False

        points, region_name = self.load_geojson_region(geojson_path)
        if not points:
            return False

        try:
            data = {
                "region_id": region_id,
                "type": "points",
                "points": points,
                "name": region_name
            }

            response = self.session.post(
                f"{self.base_url}/api/analyzer/{self.analyzer_id}/regions/add",
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✓ 区域添加成功: {region_name} (ID: {region_id})")
                    return True
                else:
                    print(f"✗ 区域添加失败: {result.get('error', '未知错误')}")
                    return False
            else:
                print(f"✗ 区域添加请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False

        except Exception as e:
            print(f"✗ 添加区域时发生错误: {e}")
            return False

    def get_regions_info(self):
        """获取所有区域信息"""
        if not self.analyzer_id:
            print("✗ 请先创建分析器")
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/api/analyzer/{self.analyzer_id}/regions"
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print("✓ 成功获取区域信息:")
                    for region_id, info in result['regions'].items():
                        print(f"  - {region_id}: {info['name']} ({info['area_km2']:.2f} km²)")
                    return result['regions']
                else:
                    print(f"✗ 获取区域信息失败: {result.get('error', '未知错误')}")
                    return None
            else:
                print(f"✗ 获取区域信息请求失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"✗ 获取区域信息时发生错误: {e}")
            return None

    def run_comparison_analysis(self, region_ids, years=None):
        """
        执行区域对比分析

        Args:
            region_ids: 区域ID列表
            years: 分析年份列表，如果为None则使用默认年份
        """
        if not self.analyzer_id:
            print("✗ 请先创建分析器")
            return None

        try:
            data = {
                "region_ids": region_ids,
                "analysis_params": {}
            }

            if years:
                data["analysis_params"]["years"] = years

            print("正在执行区域对比分析...")
            response = self.session.post(
                f"{self.base_url}/api/analyzer/{self.analyzer_id}/comparison/analyze",
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print("✓ 区域对比分析完成")
                    return result['results']
                else:
                    print(f"✗ 区域对比分析失败: {result.get('error', '未知错误')}")
                    if 'traceback' in result:
                        print(f"错误详情: {result['traceback']}")
                    return None
            else:
                print(f"✗ 区域对比分析请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None

        except Exception as e:
            print(f"✗ 执行区域对比分析时发生错误: {e}")
            return None

    def generate_comparison_charts(self, region_ids):
        """
        生成对比图表

        Args:
            region_ids: 区域ID列表
        """
        if not self.analyzer_id:
            print("✗ 请先创建分析器")
            return None

        try:
            data = {
                "region_ids": region_ids,
                "chart_params": {}
            }

            print("正在生成对比图表...")
            response = self.session.post(
                f"{self.base_url}/api/analyzer/{self.analyzer_id}/comparison/charts",
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print("✓ 对比图表生成完成")
                    return result['charts']
                else:
                    print(f"✗ 对比图表生成失败: {result.get('error', '未知错误')}")
                    return None
            else:
                print(f"✗ 对比图表生成请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None

        except Exception as e:
            print(f"✗ 生成对比图表时发生错误: {e}")
            return None

    def display_charts(self, charts_data):
        """
        显示图表

        Args:
            charts_data: 图表数据字典，包含base64编码的图片
        """
        if not charts_data:
            print("✗ 没有图表数据可显示")
            return

        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        chart_titles = {
            'time_series': '时间序列对比图',
            'area_statistics': '面积统计对比图',
            'normalized_comparison': '归一化指标对比图',
            'change_trends': '变化趋势对比图'
        }

        # 计算子图布局
        n_charts = len(charts_data)
        if n_charts == 1:
            rows, cols = 1, 1
        elif n_charts == 2:
            rows, cols = 1, 2
        elif n_charts <= 4:
            rows, cols = 2, 2
        else:
            rows, cols = 3, 2

        fig, axes = plt.subplots(rows, cols, figsize=(15, 10))
        if n_charts == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()

        chart_idx = 0
        for chart_type, base64_data in charts_data.items():
            if chart_idx >= len(axes):
                break

            try:
                # 解码base64图片
                img_data = base64.b64decode(base64_data)
                img = mpimg.imread(BytesIO(img_data))

                # 显示图片
                axes[chart_idx].imshow(img)
                axes[chart_idx].axis('off')
                axes[chart_idx].set_title(chart_titles.get(chart_type, chart_type))

                chart_idx += 1

            except Exception as e:
                print(f"✗ 显示图表 {chart_type} 时发生错误: {e}")
                continue

        # 隐藏多余的子图
        for i in range(chart_idx, len(axes)):
            axes[i].axis('off')

        plt.tight_layout()
        plt.show()
        print(f"✓ 已显示 {chart_idx} 个图表")

    def cleanup(self):
        """清理资源"""
        if self.analyzer_id:
            try:
                response = self.session.delete(
                    f"{self.base_url}/api/analyzer/{self.analyzer_id}/delete"
                )
                if response.status_code == 200:
                    print(f"✓ 分析器 {self.analyzer_id} 已清理")
                else:
                    print(f"⚠ 清理分析器时出现问题: {response.status_code}")
            except Exception as e:
                print(f"⚠ 清理分析器时发生错误: {e}")


def main():
    """主测试函数"""
    print("开始测试区域对比分析功能...")

    # 初始化测试器
    tester = RegionComparisonTester()

    try:
        # 1. 测试API健康状态
        if not tester.test_health():
            print("API不可用，请确保Flask应用正在运行")
            return

        # 2. 创建分析器
        if not tester.create_analyzer("D:/Google/RSEI_2000_2022/"):
            return

        # 3. 添加区域
        geojson_files = {
            "1001": "D:/Google/GLC_FCS30/九江市_市.geojson",
            "1002": "D:/Google/GLC_FCS30/南昌市_市.geojson"
        }

        region_ids = []
        for region_id, geojson_path in geojson_files.items():
            if tester.add_region(geojson_path, region_id):
                region_ids.append(region_id)

        if len(region_ids) < 2:
            print("✗ 需要至少两个区域才能进行对比分析")
            return

        # 4. 获取区域信息
        regions_info = tester.get_regions_info()

        # 5. 执行对比分析
        print("\n开始执行对比分析...")
        analysis_results = tester.run_comparison_analysis(
            region_ids=region_ids,
            years=[2000, 2005, 2010, 2015, 2020, 2022]  # 可以根据需要调整年份
        )

        if analysis_results:
            print("分析结果摘要:")
            if 'comparison_summary' in analysis_results:
                summary = analysis_results['comparison_summary']
                print(f"  - 总区域数: {summary.get('total_regions', 0)}")

                if 'area_comparison' in summary:
                    area_comp = summary['area_comparison']
                    if area_comp.get('largest_region'):
                        largest = area_comp['largest_region']
                        print(f"  - 最大区域: {largest[0]} ({largest[1]:.2f} km²)")
                    if area_comp.get('smallest_region'):
                        smallest = area_comp['smallest_region']
                        print(f"  - 最小区域: {smallest[0]} ({smallest[1]:.2f} km²)")

        # 6. 生成和显示图表
        print("\n开始生成图表...")
        charts = tester.generate_comparison_charts(region_ids)

        if charts:
            print("正在显示图表...")
            tester.display_charts(charts)
        else:
            print("✗ 无法生成图表")

    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        tester.cleanup()
        print("测试完成")


if __name__ == "__main__":
    main()
# import base64
# import os
# from ComparisonAnalyzer import ComparisonAnalyzer
#
# # 初始化对比分析器
# analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")
#
# # 定义区域数据
# regions = [
#     {
#         "name": "九江市",
#         "type": "vector",
#         "path": "D:/Google/GLC_FCS30/九江市_市.geojson"
#     },
#     {
#         "name": "南昌市",
#         "type": "vector",
#         "path": "D:/Google/GLC_FCS30/南昌市_市.geojson"
#     }
# ]
#
# # 添加分析区域
# region_ids = []
# for region in regions:
#     # 读取GeoJSON文件
#     with open(region["path"], "r", encoding="utf-8") as f:
#         geojson_data = f.read()
#
#     # 添加区域
#     region_id = analyzer.add_analysis_region(
#         region_data={"data": geojson_data, "name": region["name"]},
#         region_type="vector"
#     )
#     region_ids.append(region_id)
#     print(f"已添加区域: {region['name']}, ID: {region_id}")
#
# # 进行对比分析 (假设我们分析2020年)
# analysis_results = analyzer.parallel_comparison_analysis(
#     region_ids=region_ids,
#     years=[2020]  # 根据你的数据实际情况调整年份
# )
#
# # 生成对比图表
# charts = analyzer.generate_comparison_charts(analysis_results)
#
# # 保存图表到文件
# output_dir = "D:/Google/output/"
# os.makedirs(output_dir, exist_ok=True)
#
# for chart_name, chart_data in charts.items():
#     output_path = os.path.join(output_dir, f"{chart_name}.png")
#     with open(output_path, "wb") as f:
#         f.write(base64.b64decode(chart_data))
#     print(f"已保存图表: {output_path}")
#
# # 导出数据为CSV
# df = analyzer.export_comparison_data(analysis_results)
# csv_path = os.path.join(output_dir, "comparison_results.csv")
# df.to_csv(csv_path, index=False, encoding="utf-8-sig")
# print(f"已保存数据表格: {csv_path}")
#
# print("分析完成!")


import os
import base64
from ComparisonAnalyzer import ComparisonAnalyzer
import matplotlib.pyplot as plt

# 设置支持数学符号的字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_geojson(path):
    """安全加载GeoJSON文件"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"加载GeoJSON文件 {path} 失败: {e}")
        return None


def comprehensive_analysis(analyzer, region_ids):
    # 获取可用年份
    available_years = sorted(analyzer.raster_analyzer.available_years)

    # 分析1：最新年份现状对比
    latest_results = analyzer.parallel_comparison_analysis(
        region_ids=region_ids,
        years=[available_years[-1]]
    )

    # 分析2：完整时间序列趋势分析
    trend_results = analyzer.parallel_comparison_analysis(
        region_ids=region_ids,
        years=available_years
    )

    # 分析3：近五年均值对比
    recent_years = available_years[-5:] if len(available_years) >= 5 else available_years
    recent_results = analyzer.parallel_comparison_analysis(
        region_ids=region_ids,
        years=recent_years
    )

    return {
        "latest_comparison": latest_results,
        "long_term_trend": trend_results,
        "recent_period": recent_results
    }


# 在 debug_CA.py 或业务脚本中添加：

def run_comprehensive_analysis(analyzer, region_ids):
    """独立封装的综合分析函数"""
    available_years = sorted(analyzer.raster_analyzer.available_years)

    return {
        "latest": analyzer.parallel_comparison_analysis(region_ids, [available_years[-1]]),
        #"trends": analyzer.parallel_comparison_analysis(region_ids, available_years),
        #"recent": analyzer.parallel_comparison_analysis(region_ids,available_years[-5:] if len(available_years) >= 5 else available_years)
    }


def main():
    # 初始化对比分析器 - 指定包含RSEI数据的目录
    analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")

    # 定义区域数据
    regions = [
        {"name": "九江市", "path": "D:/Google/GLC_FCS30/九江市_市.geojson"},
        {"name": "南昌市", "path": "D:/Google/GLC_FCS30/南昌市_市.geojson"}
    ]

    # 添加分析区域
    region_ids = []
    for region in regions:
        geojson_data = load_geojson(region["path"])
        if geojson_data:
            region_id = analyzer.add_analysis_region(
                region_data={"data": geojson_data, "name": region["name"]},
                region_type="vector"
            )
            if region_id:
                region_ids.append(region_id)
                print(f"已添加区域: {region['name']}, ID: {region_id}")
            else:
                print(f"添加区域 {region['name']} 失败")

    if not region_ids:
        print("没有可用的区域进行分析")
        return

    # 获取可用的分析年份
    available_years = analyzer.raster_analyzer.available_years
    if not available_years:
        print("没有可用的RSEI数据年份")
        return

    print(f"可用的RSEI数据年份: {sorted(available_years)}")

    # 使用最新的可用年份进行分析
    analysis_year = 2019
    print(f"将使用 {analysis_year} 年的数据进行对比分析")

    # 进行对比分析
    #analysis_results = analyzer.parallel_comparison_analysis(region_ids=region_ids,years=[analysis_year])
    # 调用示例
    analysis_results = run_comprehensive_analysis(analyzer, ['region_0', 'region_1'])

    print(f"分析结果: {analysis_results}")

    # # 检查分析结果是否有效
    # if not analysis_results.get('time_series_data'):
    #     print("分析未产生有效结果")
    #     return

    # 检查分析结果是否有效
    if not any(
            result and isinstance(result, dict) and result.get('time_series_data')
            for result in analysis_results.values()
    ):
        print("分析未产生有效结果")
        return

    # 生成对比图表
    try:
        print("开始生成对比图表...")
        charts = analyzer.generate_comparison_charts(analysis_results)

        # 保存图表到文件
        output_dir = "D:/Google/output/"
        os.makedirs(output_dir, exist_ok=True)

        for chart_name, chart_data in charts.items():
            output_path = os.path.join(output_dir, f"{chart_name}.png")
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(chart_data))
            print(f"已保存图表: {output_path}")

        # 导出数据为CSV
        df = analyzer.export_comparison_data(analysis_results)
        csv_path = os.path.join(output_dir, "comparison_results.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"已保存数据表格: {csv_path}")

    except Exception as e:
        print(f"生成图表或导出数据时出错: {e}")



if __name__ == "__main__":
    main()
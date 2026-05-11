import os
import json
import csv
from collections import defaultdict
from ComparisonAnalyzer import ComparisonAnalyzer


def get_city_mapping():
    """Return a dictionary mapping city codes to their full names and geojson paths"""
    return {
        'NC': {'name': '南昌市', 'path': "D:/Google/GLC_FCS30/南昌市_市.geojson"},
        'JDZ': {'name': '景德镇市', 'path': "D:/Google/GLC_FCS30/景德镇市_市.geojson"},
        'SR': {'name': '上饶市', 'path': "D:/Google/GLC_FCS30/上饶市_市.geojson"},
        'YT': {'name': '鹰潭市', 'path': "D:/Google/GLC_FCS30/鹰潭市_市.geojson"},
        'JJ': {'name': '九江市', 'path': "D:/Google/GLC_FCS30/九江市_市.geojson"},
        'FZ': {'name': '抚州市', 'path': "D:/Google/GLC_FCS30/抚州市_市.geojson"}
    }


def select_cities():
    """Prompt user to select cities and return selected city codes"""
    city_mapping = get_city_mapping()
    return ['NC', 'JJ']  # 示例固定选择南昌和九江，实际使用时可以取消注释下面的交互代码

    # print("Available cities:")
    # for code, info in city_mapping.items():
    #     print(f"{code}: {info['name']}")

    # while True:
    #     selected = input("\nEnter city codes to analyze (2-6, comma-separated, e.g. 'NC,JJ'): ").strip().upper()
    #     selected_codes = [code.strip() for code in selected.split(',')]
    #     # 验证逻辑...
    #     return selected_codes


def csv_to_chart_data(csv_file_path):
    """将CSV文件转换为图表数据(B部分)"""
    data = {
        "Time_Series": {},
        "Area_Statistics": {
            "part1": {},
            "part2": {}
        },
        "Change_Trend": {},
        "Normalize": {}
    }

    with open(csv_file_path, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        rows = list(csv_reader)

    regions = defaultdict(list)
    for row in rows:
        regions[row['region_id']].append(row)

    for region_id, region_data in regions.items():
        region_data.sort(key=lambda x: int(x['year']))
        region_name = region_data[0]['region_name']

        # Time_Series
        data["Time_Series"][region_id] = {
            "region_name": region_name,
            "value": [float(row['mean_value']) for row in region_data]
        }

        # Area_Statistics
        data["Area_Statistics"]["part1"][region_id] = {
            "region_name": region_name,
            "area_km2": float(region_data[0]['area_km2'])
        }
        data["Area_Statistics"]["part2"][region_id] = float(region_data[-1]['mean_value'])

        # Change_Trend
        first = float(region_data[0]['mean_value'])
        last = float(region_data[-1]['mean_value'])
        data["Change_Trend"][region_id] = {
            "Total of change": last - first,
            "Annual average rate of change": (last - first) / (len(region_data) - 1) if len(region_data) > 1 else 0
        }

        # Normalize
        data["Normalize"][region_id] = {
            "region_name": region_name,
            "value": [[float(row['normalized_sum']), float(row['std_value'])] for row in region_data]
        }

    return data

def main():
    # 初始化分析器和输出目录
    analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")
    output_dir = "D:/Google/output/"
    os.makedirs(output_dir, exist_ok=True)

    # 选择城市并添加分析区域
    selected_codes = select_cities()
    city_mapping = get_city_mapping()
    region_ids = {}

    for code in selected_codes:
        city_info = city_mapping[code]
        with open(city_info['path'], 'r', encoding='utf-8') as f:
            city_data = {'data': f.read(), 'name': city_info['name']}
            region_id = analyzer.add_analysis_region(city_data, region_type='vector')
            region_ids[code] = region_id

    # 执行分析
    results = analyzer.parallel_comparison_analysis(
        region_ids=list(region_ids.values()),
        years=list(range(2000, 2023)))

    # 导出CSV数据
    csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
    analyzer.export_comparison_data(results).to_csv(csv_path, index=False, encoding='utf-8-sig')

    print(results)  # 使用 default=str 处理 numpy 类型
    print(results['Normalize'])

    # 构建完整JSON结构
    final_json = {
        "分析摘要": {
            "分析区域数量": results['comparison_summary']['total_regions'],
            "区域面积比较": {
                "最大区域": f"{results['comparison_summary']['area_comparison']['largest_region'][1]:.2f} km²",
                "最小区域": f"{results['comparison_summary']['area_comparison']['smallest_region'][1]:.2f} km²"
            },
            "归一化指标拟合": {
                "斜率(k)": results['normalized_fit_params']['k'],
                "截距(b)": results['fit_params']['b'],
                "拟合方程": f"y = {results['fit_params']['k']:.6f}x + {results['fit_params']['b']:.6f}"
            },
            "变化趋势": {
                "平均变化百分比": f"{results['comparison_summary']['overall_trends'].get('average_change', 0):.2f}%",
                "最大增长区域": f"{results['comparison_summary']['overall_trends'].get('highest_increase', ['无', 0])[0]} ({results['comparison_summary']['overall_trends'].get('highest_increase', ['无', 0])[1]:.2f}%)",
                "最大下降区域": f"{results['comparison_summary']['overall_trends'].get('highest_decrease', ['无', 0])[0]} ({results['comparison_summary']['overall_trends'].get('highest_decrease', ['无', 0])[1]:.2f}%)"
            }
        },
        "图表数据": csv_to_chart_data(csv_path)
    }

    # 保存JSON文件
    json_path = os.path.join(output_dir, 'combined_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()


















#
# import os
# import json
# from ComparisonAnalyzer import ComparisonAnalyzer
#
# def get_city_mapping():
#     """Return a dictionary mapping city codes to their full names and geojson paths"""
#     return {
#         'NC': {'name': '南昌市', 'path': "D:/Google/GLC_FCS30/南昌市_市.geojson"},
#         'JDZ': {'name': '景德镇市', 'path': "D:/Google/GLC_FCS30/景德镇市_市.geojson"},
#         'SR': {'name': '上饶市', 'path': "D:/Google/GLC_FCS30/上饶市_市.geojson"},
#         'YT': {'name': '鹰潭市', 'path': "D:/Google/GLC_FCS30/鹰潭市_市.geojson"},
#         'JJ': {'name': '九江市', 'path': "D:/Google/GLC_FCS30/九江市_市.geojson"},
#         'FZ': {'name': '抚州市', 'path': "D:/Google/GLC_FCS30/抚州市_市.geojson"}
#     }
#
# def select_cities():
#     """Prompt user to select cities and return selected city codes"""
#     city_mapping = get_city_mapping()
#
#     print("Available cities:")
#     for code, info in city_mapping.items():
#         print(f"{code}: {info['name']}")
#
#     while True:
#         selected = input("\nEnter city codes to analyze (2-6, comma-separated, e.g. 'NC,JJ'): ").strip().upper()
#         selected_codes = [code.strip() for code in selected.split(',')]
#
#         # Validate input
#         if len(selected_codes) < 2:
#             print("Error: Please select at least 2 cities.")
#             continue
#         if len(selected_codes) > 6:
#             print("Error: Please select no more than 6 cities.")
#             continue
#         if any(code not in city_mapping for code in selected_codes):
#             invalid = [code for code in selected_codes if code not in city_mapping]
#             print(f"Error: Invalid city code(s): {', '.join(invalid)}")
#             continue
#
#         return selected_codes
#
# def main():
#     # Initialize analyzer
#     analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")
#
#     # Let user select cities
#     selected_codes = select_cities()
#     city_mapping = get_city_mapping()
#
#     # Initialize JSON data structure
#     json_data = {
#         "分析摘要": {},
#         "图表数据": {},
#         "区域信息": {},
#         "分析结果": {}
#     }
#
#     # Add selected analysis regions
#     region_ids = {}
#     json_data["区域信息"]["已选城市"] = []
#     for code in selected_codes:
#         city_info = city_mapping[code]
#         with open(city_info['path'], 'r', encoding='utf-8') as f:
#             city_data = {'data': f.read(), 'name': city_info['name']}
#             region_id = analyzer.add_analysis_region(city_data, region_type='vector')
#             region_ids[code] = region_id
#             json_data["区域信息"]["已选城市"].append({
#                 "城市代码": code,
#                 "城市名称": city_info['name'],
#                 "区域ID": region_id,
#                 "GeoJSON路径": city_info['path']
#             })
#         print(f"Added region: {city_info['name']} (ID: {region_id})")
#
#     # Define analysis years (2000-2022)
#     analysis_years = list(range(2000, 2023))
#
#     # Execute parallel comparison analysis
#     results = analyzer.parallel_comparison_analysis(
#         region_ids=list(region_ids.values()),
#         years=analysis_years
#     )
#
#     # Generate and save comparison charts
#     charts = analyzer.generate_comparison_charts(results)
#
#     output_dir = "D:/Google/output/"
#     os.makedirs(output_dir, exist_ok=True)
#
#     # Export data to CSV
#     df = analyzer.export_comparison_data(results)
#     csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
#     df.to_csv(csv_path, index=False, encoding='utf-8-sig')
#     json_data["分析结果"]["数据文件"] = {
#         "文件名": "RSEI对比数据.csv",
#         "保存路径": csv_path
#     }
#     print(f"已保存数据文件: RSEI对比数据.csv")
#
#     # Store analysis summary in JSON
#     json_data["分析摘要"]["分析区域数量"] = results['comparison_summary']['total_regions']
#     json_data["分析摘要"]["区域面积比较"] = {
#         "最大区域": f"{results['comparison_summary']['area_comparison']['largest_region'][1]:.2f} km²",
#         "最小区域": f"{results['comparison_summary']['area_comparison']['smallest_region'][1]:.2f} km²"
#     }
#
#     if 'normalized_fit_params' in results:
#         fit_params = results['normalized_fit_params']
#         json_data["分析摘要"]["归一化指标拟合"] = {
#             "斜率(k)": fit_params['k'],
#             "截距(b)": fit_params['b'],
#             "拟合方程": f"y = {fit_params['k']:.6f}x + {fit_params['b']:.6f}"
#         }
#
#     if 'overall_trends' in results['comparison_summary']:
#         trends = results['comparison_summary']['overall_trends']
#         json_data["分析摘要"]["变化趋势"] = {
#             "平均变化百分比": f"{trends.get('average_change', 0):.2f}%",
#             "最大增长区域": f"{trends.get('highest_increase', ['无', 0])[0]} ({trends.get('highest_increase', ['无', 0])[1]:.2f}%)",
#             "最大下降区域": f"{trends.get('highest_decrease', ['无', 0])[0]} ({trends.get('highest_decrease', ['无', 0])[1]:.2f}%)"
#         }
#
#     # Save JSON file
#     json_path = os.path.join(output_dir, 'analysis_results.json')
#     with open(json_path, 'w', encoding='utf-8') as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=2)
#     print(f"\n已保存分析结果JSON文件: {json_path}")
#
#     # Print summary (optional)
#     print("\n分析摘要:")
#     print(json.dumps(json_data["分析摘要"], ensure_ascii=False, indent=2))
#
# if __name__ == "__main__":
#     main()
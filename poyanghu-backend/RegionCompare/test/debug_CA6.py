import os
from ComparisonAnalyzer import ComparisonAnalyzer
import json
import csv
from collections import defaultdict


# 将下面的功能包装成接口“/api/RegionCompare/geojson/”,接受的数据是城市代码(NC, JJ, SR, FZ等等)，返回的是分析摘要和图表需要的数据。
# 导出的数据表格：RSEI对比数据.csv
# 将python打印出的数据和RSEI对比数据.csv转化成json。json参考文档：D:/Google/output/Data.json

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

    print("Available cities:")
    for code, info in city_mapping.items():
        print(f"{code}: {info['name']}")

    while True:
        selected = input("\nEnter city codes to analyze (2-6, comma-separated, e.g. 'NC,JJ'): ").strip().upper()
        selected_codes = [code.strip() for code in selected.split(',')]

        # Validate input
        if len(selected_codes) < 2:
            print("Error: Please select at least 2 cities.")
            continue
        if len(selected_codes) > 6:
            print("Error: Please select no more than 6 cities.")
            continue
        if any(code not in city_mapping for code in selected_codes):
            invalid = [code for code in selected_codes if code not in city_mapping]
            print(f"Error: Invalid city code(s): {', '.join(invalid)}")
            continue

        return selected_codes


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

    # 写入JSON文件
    #with open(json_file_path, 'w', encoding='utf-8') as json_file:
    #    json.dump(data, json_file, ensure_ascii=False, indent=2)


def main():
    # Initialize analyzer
    analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")

    # Let user select cities
    selected_codes = select_cities()
    city_mapping = get_city_mapping()

    # Add selected analysis regions
    region_ids = {}
    for code in selected_codes:
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

    import base64

    chart_names = {
        'time_series': '时间序列对比图.png',
        'area_statistics': '面积统计对比图.png',
        'normalized_comparison': '归一化指标对比图.png',
        'change_trends': '变化趋势对比图.png'
    }

    # for chart_type, filename in chart_names.items():
    #     if chart_type in charts:
    #         with open(os.path.join(output_dir, filename), 'wb') as f:
    #             f.write(base64.b64decode(charts[chart_type]))
    #         print(f"已保存图表: {filename}")

    # Export data to CSV
    df = analyzer.export_comparison_data(results)
    csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"已保存数据文件: RSEI对比数据.csv")

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

    # 保存JSON文件
    json_path = os.path.join(output_dir, 'combined_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
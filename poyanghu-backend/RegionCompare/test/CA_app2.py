import csv
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from ComparisonAnalyzer import ComparisonAnalyzer
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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

@app.route('/api/RegionCompare/geojson/', methods=['POST'])
def region_compare_city():
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7891, debug=True)
import csv

from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from ComparisonAnalyzer import ComparisonAnalyzer
import base64
import pandas as pd
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


def process_results_to_json(results: Dict[str, Any], csv_path: str) -> Dict[str, Any]:
    """Convert analysis results and CSV data to JSON format"""
    # Read CSV data
    df = pd.read_csv(csv_path)

    # Initialize JSON structure
    json_data = {
        "统计摘要": {},
        "图表数据": {
            "Time_Series": {},
            "Area_Statistics": {"part1": {}, "part2": {}},
            "Change_Trend": {},
            "Normalize": {}
        }
    }

    # Process summary data
    summary = results['comparison_summary']
    json_data["统计摘要"]["分析区域数量"] = summary['total_regions']
    json_data["统计摘要"]["最大区域"] = f"{summary['area_comparison']['largest_region'][1]:.2f} km²"
    json_data["统计摘要"]["最小区域"] = f"{summary['area_comparison']['smallest_region'][1]:.2f} km²"

    if 'normalized_fit_params' in results:
        fit_params = results['normalized_fit_params']
        json_data["统计摘要"]["归一化指标拟合直线参数"] = {
            "斜率(k)": fit_params['k'],
            "截距(b)": fit_params['b'],
            "拟合方程": f"y = {fit_params['k']:.6f}x + {fit_params['b']:.6f}"
        }

    if 'overall_trends' in summary:
        trends = summary['overall_trends']
        json_data["统计摘要"]["平均变化百分比"] = f"{trends.get('average_change', 0):.2f}%"
        if trends.get('highest_increase'):
            json_data["统计摘要"][
                "最大增长区域"] = f"{trends['highest_increase'][0]} ({trends['highest_increase'][1]:.2f}%)"
        if trends.get('highest_decrease'):
            json_data["统计摘要"][
                "最大下降区域"] = f"{trends['highest_decrease'][0]} ({trends['highest_decrease'][1]:.2f}%)"

    # Process time series data
    for region_id, region_data in results['time_series_data'].items():
        # print("1111111111111111111111111111111111111111")
        # print(region_id)
        # print(region_data)
        region_name = region_data['region_name']
        json_data["图表数据"]["Time_Series"][region_id] = {
            "region_name": region_name,
            "value": region_data['values']
        }

    # Process area statistics
    for region_id, region_data in results['area_statistics'].items():
        region_name = region_data['region_name']
        json_data["图表数据"]["Area_Statistics"]["part1"][region_id] = {
            "region_name": region_name,
            "area_km2": region_data['area']
        }
        json_data["图表数据"]["Area_Statistics"]["part2"][region_id] = region_data['last_value']

    # Process change trends
    for region_id, trend_data in results['change_trends'].items():
        json_data["图表数据"]["Change_Trend"][region_id] = {
            "Total of change": trend_data['total_change'],
            "Annual average rate of change": trend_data['annual_change']
        }

    # Process normalized data from CSV
    for region_id in df['region_id'].unique():
        region_data = df[df['region_id'] == region_id]
        region_name = region_data.iloc[0]['region_name']

        normalized_values = []
        for _, row in region_data.iterrows():
            normalized_values.append([
                row['normalized_sum'],
                row['std_value']
            ])

        json_data["图表数据"]["Normalize"][region_id] = {
            "region_name": region_name,
            "value": normalized_values
        }

    return json_data


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
        with open(city_info['path'], 'r', encoding='utf-8-sig') as f:
            city_data = {'data': f.read(), 'name': city_info['name']}
            region_id = analyzer.add_analysis_region(city_data, region_type='vector')
            region_ids[code] = region_id

    # Define analysis years (2000-2022)
    analysis_years = list(range(2000, 2023))

    # Execute parallel comparison analysis
    results = analyzer.parallel_comparison_analysis(
        region_ids=list(region_ids.values()),
        years=analysis_years
    )

    # Generate comparison charts (base64 encoded)
    charts = analyzer.generate_comparison_charts(results)

    # Save CSV data temporarily
    output_dir = "D:/Google/output/"
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
    df = analyzer.export_comparison_data(results)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        print("CSV文件列名:", reader.fieldnames)

    # Convert results to JSON format
    json_response = process_results_to_json(results, csv_path)

    # Add chart data to response
    json_response["图表数据"]["Charts"] = {}
    for chart_type, chart_data in charts.items():
        json_response["图表数据"]["Charts"][chart_type] = chart_data

    # Clean up temporary file
    os.remove(csv_path)

    return jsonify(json_response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7891, debug=True)
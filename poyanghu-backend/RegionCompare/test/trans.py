import json
import csv
from collections import defaultdict


def csv_to_json_chart_data(csv_file_path, json_file_path):
    # 初始化数据结构
    data = {
        "图表数据": {
            "Time_Series": {},
            "Area_Statistics": {
                "part1": {},
                "part2": {}
            },
            "Change_Trend": {},
            "Normalize": {}
        }
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
        data["图表数据"]["Time_Series"][region_id] = {
            "region_name": region_name,
            "value": [float(row['mean_value']) for row in region_data]
        }

        # Area_Statistics数据
        data["图表数据"]["Area_Statistics"]["part1"][region_id] = {
            "region_name": region_name,
            "area_km2": float(area_km2)
        }
        data["图表数据"]["Area_Statistics"]["part2"][region_id] = float(region_data[-1]['mean_value'])

        # Change_Trend数据
        first_value = float(region_data[0]['mean_value'])
        last_value = float(region_data[-1]['mean_value'])
        total_change = last_value - first_value
        annual_avg_change = total_change / (len(region_data) - 1) if len(region_data) > 1 else 0

        data["图表数据"]["Change_Trend"][region_id] = {
            "Total of change": total_change,
            "Annual average rate of change": annual_avg_change
        }

        # Normalize数据
        data["图表数据"]["Normalize"][region_id] = {
            "region_name": region_name,
            "value": [[float(row['normalized_sum']), float(row['std_value'])] for row in region_data]
        }

    # 写入JSON文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)


# 使用示例
csv_to_json_chart_data('D:/Google/output/RSEI对比数据.csv', 'D:/Google/output/output.json')







#
#
#
#
# import json
# import csv
# from collections import defaultdict
#
#
# def csv_to_json_chart_data(csv_file_path, json_file_path):
#     # 初始化数据结构
#     data = {
#         "图表数据": {
#             "Time_Series": {},
#             "Area_Statistics": {
#                 "part1": {},
#                 "part2": {}
#             },
#             "Change_Trend": {},
#             "Normalize": {}
#         }
#     }
#
#     # 读取CSV文件
#     with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
#         csv_reader = csv.DictReader(csv_file)
#         rows = list(csv_reader)
#
#     # 按区域分组
#     regions = defaultdict(list)
#     for row in rows:
#         regions[row['region_id']].append(row)
#
#     # 处理每个区域的数据
#     for region_id, region_data in regions.items():
#         # 按年份排序
#         region_data.sort(key=lambda x: int(x['year']))
#
#         # 提取基本信息
#         region_name = region_data[0]['region_name']
#         area_km2 = region_data[0]['area_km2']
#
#         # Time_Series数据
#         data["图表数据"]["Time_Series"][region_id] = {
#             "region_name": region_name,
#             "value": [float(row['mean_value']) for row in region_data]
#         }
#
#         # Area_Statistics数据
#         data["图表数据"]["Area_Statistics"]["part1"][region_id] = {
#             "region_name": region_name,
#             "area_km2": float(area_km2)
#         }
#         data["图表数据"]["Area_Statistics"]["part2"][region_id] = float(region_data[-1]['mean_value'])
#
#         # Change_Trend数据
#         first_value = float(region_data[0]['mean_value'])
#         last_value = float(region_data[-1]['mean_value'])
#         total_change = last_value - first_value
#         annual_avg_change = total_change / (len(region_data) - 1) if len(region_data) > 1 else 0
#
#         data["图表数据"]["Change_Trend"][region_id] = {
#             "Total of change": total_change,
#             "Annual average rate of change": annual_avg_change
#         }
#
#         # Normalize数据
#         data["图表数据"]["Normalize"][region_id] = {
#             "region_name": region_name,
#             "value": [[float(row['normalized_sum']), float(row['std_value'])] for row in region_data]
#         }
#
#     # 写入JSON文件
#     with open(json_file_path, 'w', encoding='utf-8') as json_file:
#         json.dump(data, json_file, ensure_ascii=False, indent=2)
#
# # 使用示例
# csv_to_json_chart_data('D:/Google/output/RSEI对比数据.csv', 'D:/Google/output/output.json')
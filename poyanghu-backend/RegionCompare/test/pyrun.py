import requests

# 添加点区域
points_data = {
    "type": "points",
    "points": [[117.2368, 29.2969], [117.8073, 29.2283], [117.4165, 28.7887]],
    "name": "鄱阳湖三角区域"
}
response = requests.post("http://localhost:7891/api/regions", json=points_data)
print(response.json())

# 执行对比分析
analysis_data = {
    "region_ids": ["region1_id", "region2_id"],
    "years": [2010, 2015, 2020]
}
response = requests.post("http://localhost:7891/api/analysis/compare", json=analysis_data)
results = response.json()
print(results)

# 生成图表
response = requests.post("http://localhost:7891/api/analysis/charts", json={"analysis_results": results['data']})
charts = response.json()
print(charts)
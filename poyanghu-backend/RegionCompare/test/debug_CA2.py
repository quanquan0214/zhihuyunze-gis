import os
from ComparisonAnalyzer import ComparisonAnalyzer

# 初始化分析器，设置数据目录
analyzer = ComparisonAnalyzer(data_directory="D:/Google/RSEI_full/")

# 定义两个区域的geojson文件路径
jiujiang_geojson = "D:/Google/GLC_FCS30/九江市_市.geojson"
nanchang_geojson = "D:/Google/GLC_FCS30/南昌市_市.geojson"


# 添加分析区域
with open(jiujiang_geojson, 'r', encoding='utf-8') as f:
    jiujiang_data = {'data': f.read(), 'name': '九江市'}
    jiujiang_id = analyzer.add_analysis_region(jiujiang_data, region_type='vector')

with open(nanchang_geojson, 'r', encoding='utf-8') as f:
    nanchang_data = {'data': f.read(), 'name': '南昌市'}
    nanchang_id = analyzer.add_analysis_region(nanchang_data, region_type='vector')

# 定义分析年份范围 (2000-2022)
analysis_years = list(range(2000, 2022))

# 执行并行对比分析
results = analyzer.parallel_comparison_analysis(
    region_ids=[jiujiang_id, nanchang_id],
    years=analysis_years
)

# 生成对比图表
charts = analyzer.generate_comparison_charts(results)

# 保存图表到文件
output_dir = "D:/Google/output/"
os.makedirs(output_dir, exist_ok=True)

# 将base64编码的图表保存为图片文件
import base64

chart_names = {
    'time_series': '时间序列对比图.png',
    'area_statistics': '面积统计对比图.png',
    'normalized_comparison': '归一化指标对比图.png',
    'change_trends': '变化趋势对比图.png'
}

for chart_type, filename in chart_names.items():
    if chart_type in charts:
        with open(os.path.join(output_dir, filename), 'wb') as f:
            f.write(base64.b64decode(charts[chart_type]))
        print(f"已保存图表: {filename}")

# 导出数据为CSV
df = analyzer.export_comparison_data(results)
csv_path = os.path.join(output_dir, 'RSEI对比数据.csv')
df.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"已保存数据文件: RSEI对比数据.csv")

# 打印分析摘要
print("\n分析摘要:")
print(f"分析区域数量: {results['comparison_summary']['total_regions']}")
print(f"最大区域: {results['comparison_summary']['area_comparison']['largest_region'][1]:.2f} km²")
print(f"最小区域: {results['comparison_summary']['area_comparison']['smallest_region'][1]:.2f} km²")

if 'overall_trends' in results['comparison_summary']:
    trends = results['comparison_summary']['overall_trends']
    print(f"平均变化百分比: {trends.get('average_change', 0):.2f}%")
    if trends.get('highest_increase'):
        print(f"最大增长区域: {trends['highest_increase'][0]} ({trends['highest_increase'][1]:.2f}%)")
    if trends.get('highest_decrease'):
        print(f"最大下降区域: {trends['highest_decrease'][0]} ({trends['highest_decrease'][1]:.2f}%)")
# import pandas as pd
#
# # 读取CSV文件
# data = pd.read_csv('D:/Google/H5/Processed/elevationData_Correct.csv')
#
# # 将时间列解析为日期格式
# data['Time'] = pd.to_datetime(data['Time'])
#
# # 筛选上一年10月1日至本年9月30日的数据(这是一个水文年的时间段)，并计算平均水位
# start_date = pd.Timestamp(data['Time'].dt.year.min(), 10, 1)  # 上一年10月1日
# end_date = pd.Timestamp(data['Time'].dt.year.max() + 1, 9, 30)  # 本年9月30日
# filtered_data = data[(data['Time'] >= start_date) & (data['Time'] <= end_date)]
#
# # 计算水位平均值
# average_elevation = filtered_data.groupby(filtered_data['Time'].dt.year)['Average Water Level'].mean()
#
# # 将 Series 转换为 DataFrame
# average_elevation_df = average_elevation.reset_index(name='Elevation')
# average_elevation_df.rename(columns={'Time': 'Time'}, inplace=True)
#
# # 导出到新的CSV文件
# average_elevation_df.to_csv('D:/Google/H5/Processed/elevationAverage_Correct.csv', index=False)
#


# 计算月平均水位表
import pandas as pd
from datetime import datetime, timedelta

# 读取CSV文件
data = pd.read_csv('D:/Google/H5/Processed/elevationData.csv')

# 将时间列解析为日期格式
data['Time'] = pd.to_datetime(data['Time'])

# 创建所有需要分析的年月列表
start_year_month = 201810
end_year_month = 202412

year_months = []
current_ym = start_year_month
while current_ym <= end_year_month:
    year_months.append(current_ym)
    year = current_ym // 100
    month = current_ym % 100
    month += 1
    if month > 12:
        month = 1
        year += 1
    current_ym = year * 100 + month

# 初始化结果列表
results = []

# 遍历每个月，计算对应的时间段和平均水位
for ym in year_months:
    year = ym // 100
    month = ym % 100

    # 计算当前月的结束日期和开始日期
    end_date = datetime(year, month, 21)
    start_date = end_date - timedelta(days=30)

    # 筛选数据
    filtered = data[(data['Time'] >= start_date) & (data['Time'] <= end_date)]

    # 计算平均值或填充0
    if not filtered.empty:
        avg_elevation = filtered['Average Water Level'].mean()
    else:
        avg_elevation = 0

    # 添加到结果列表
    results.append({
        'YearMonth': ym,
        'StartDate': start_date.strftime('%Y-%m-%d'),
        'EndDate': end_date.strftime('%Y-%m-%d'),
        'Elevation': avg_elevation
    })

# 创建结果DataFrame
result_df = pd.DataFrame(results)

# 导出到新的CSV文件
result_df.to_csv('D:/Google/H5/Processed/mouthData_1.csv', index=False)
print("数据处理完成。")


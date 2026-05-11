import pandas as pd
from sklearn.preprocessing import StandardScaler
# 原始数据（假设已读取为data）
data = pd.read_csv("D:/Google/GWR/nanchang_1.csv")

# 将lucc转换为分类类型并独热编码
data['lucc'] = data['lucc'].astype('category')
lucc_dummies = pd.get_dummies(data['lucc'], prefix='lucc', drop_first=True)  # 避免多重共线性
data = pd.concat([data.drop('lucc', axis=1), lucc_dummies], axis=1)

# 确保独热编码后的lucc列已转换为0/1
lucc_columns = [col for col in data.columns if col.startswith('lucc_')]
data[lucc_columns] = data[lucc_columns].astype(int)

# # 对连续变量标准化（解决尺度差异）
scaler = StandardScaler()
data[['temperature', 'rainfall']] = scaler.fit_transform(data[['temperature', 'rainfall']])

# 保存处理后的数据
data.to_csv("D:/Google/GWR/nanchang_2.csv", index=False)
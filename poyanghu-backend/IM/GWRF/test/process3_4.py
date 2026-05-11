# # 根据csv文件生成GWRF输入文件
#
# import pandas as pd
# import numpy as np
# from mgwr.sel_bw import Sel_BW
# from mgwr.gwr import GWR
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.model_selection import train_test_split
# import matplotlib.pyplot as plt
#
# # 1. 读取预处理后的CSV文件
# data_path = "D:/Google/GWR_k/GWR_k_clipped/nanchang_gwr_processed.csv"
# data = pd.read_csv(data_path)
#
# # 2. 数据预处理
# # 提取所有独热编码后的lucc列（列名以'lucc_'开头）
# lucc_columns = [col for col in data.columns if col.startswith('lucc_')]
# continuous_vars = ['temperature', 'rainfall']
# coord_vars = ['x', 'y']
# target_var = 'RSEI'
#
# # 定义变量
# y = data[target_var].values.reshape(-1, 1)  # 因变量RSEI
# X = data[lucc_columns + continuous_vars].values  # 自变量（所有lucc类别 + 连续变量）
# coords = data[coord_vars].values  # 地理坐标
#
# # 3. 划分训练集和测试集（70%训练，30%测试）
# X_train, X_test, y_train, y_test, coords_train, coords_test = train_test_split(
#     X, y, coords, test_size=0.3, random_state=42
# )
#
# # 4. 地理加权随机森林（GWRF）建模
# # 4.1 全局随机森林模型（基准模型）
# rf = RandomForestRegressor(n_estimators=100, random_state=42)
# rf.fit(X_train, y_train.ravel())
# print(f"全局随机森林R²分数: {rf.score(X_test, y_test):.3f}")
#
# # 4.2 地理加权模型（GWR）
# # 选择最优带宽（增加ridge参数稳定计算）
# try:
#     bw_selector = Sel_BW(coords_train, y_train, X_train, kernel='gaussian')
#     bw = bw_selector.search()
#     print(f"最优带宽: {bw}")
#
#     # 拟合GWR模型（启用岭回归）
#     gwr_model = GWR(coords_train, y_train, X_train, bw, kernel='gaussian', fixed=False, constant=True, sigma2_v1=False )
#     gwr_results = gwr_model.fit()
#     print(f"GWR局部R²中位数: {np.median(gwr_results.localR2):.3f}")
#
# except Exception as e:
#     print(f"GWR模型拟合失败: {str(e)}")
#     exit()
#
# # 5. 结果分析与可视化
# # 5.1 变量重要性（随机森林）
# feature_names = lucc_columns + continuous_vars
# feature_importance = pd.DataFrame({
#     'Variable': feature_names,
#     'Importance': rf.feature_importances_
# }).sort_values('Importance', ascending=False)
#
# plt.figure(figsize=(10, 6))
# plt.barh(feature_names, feature_importance['Importance'])
# plt.title("全局变量重要性（随机森林）")
# plt.xlabel("重要性得分")
# plt.gca().invert_yaxis()  # 重要性从高到低显示
# plt.show()
#
# # 5.2 地理加权系数空间分布（仅展示连续变量）
# n_plots = len(continuous_vars)
# fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 5))
# if n_plots == 1:  # 如果只有一个连续变量，避免axes索引错误
#     axes = [axes]
#
# for i, var in enumerate(continuous_vars):
#     # 找到该变量在X中的列索引
#     idx = feature_names.index(var)
#     axes[i].scatter(coords_train[:, 0], coords_train[:, 1], c=gwr_results.params[:, idx], cmap='coolwarm')
#     axes[i].set_title(f"{var}系数")
#     axes[i].set_xlabel("经度")
#     axes[i].set_ylabel("纬度")
#     plt.colorbar(axes[i].collections[0], ax=axes[i], label='系数值')
#
# plt.suptitle("连续变量的地理加权系数空间分布")
# plt.tight_layout()
# plt.show()
#
# # 6. 输出结果文件
# results_df = pd.DataFrame({
#     'x': coords_train[:, 0],
#     'y': coords_train[:, 1],
#     'RSEI_pred': gwr_results.predy.flatten()
# })
#
# # 添加所有变量的系数
# for i, var in enumerate(feature_names):
#     results_df[f"{var}_coef"] = gwr_results.params[:, i]
#
# results_df.to_csv("D:/Google/GWR_k/gwrf_results_hot.csv", index=False)
# print("GWRF结果已保存至 gwrf_results.csv")
#
#
#

# 根据csv文件生成GWRF输入文件

import pandas as pd
import numpy as np
from mgwr.sel_bw import Sel_BW
from mgwr.gwr import GWR
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# 1. 读取预处理后的CSV文件
data_path = "D:/Google/GWR_k/GWR_k_clipped/nanchang_gwr_hot.csv"
data = pd.read_csv(data_path)

# 新增：从数据中抽取10%作为样本
data = data.sample(frac=0.1, random_state=42)

# 2. 数据预处理
# 提取所有独热编码后的lucc列（列名以'lucc_'开头）
lucc_columns = [col for col in data.columns if col.startswith('lucc_')]
continuous_vars = ['temperature', 'rainfall']
coord_vars = ['x', 'y']
target_var = 'RSEI'

# 定义变量
y = data[target_var].values.reshape(-1, 1)  # 因变量RSEI
X = data[lucc_columns + continuous_vars].values  # 自变量（所有lucc类别 + 连续变量）
coords = data[coord_vars].values  # 地理坐标

# 3. 划分训练集和测试集（70%训练，30%测试）
X_train, X_test, y_train, y_test, coords_train, coords_test = train_test_split(
    X, y, coords, test_size=0.3, random_state=42
)

# 4. 地理加权随机森林（GWRF）建模
# 4.1 全局随机森林模型（基准模型）
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train.ravel())
print(f"全局随机森林R²分数: {rf.score(X_test, y_test):.3f}")

# 4.2 地理加权模型（GWR）
# 选择最优带宽（增加ridge参数稳定计算）
try:
    bw_selector = Sel_BW(coords_train, y_train, X_train, kernel='gaussian')
    bw = bw_selector.search()
    print(f"最优带宽: {bw}")

    # 拟合GWR模型（启用岭回归）
    gwr_model = GWR(coords_train, y_train, X_train, bw, kernel='gaussian', fixed=False, constant=True, sigma2_v1=False )
    gwr_results = gwr_model.fit()
    print(f"GWR局部R²中位数: {np.median(gwr_results.localR2):.3f}")

except Exception as e:
    print(f"GWR模型拟合失败: {str(e)}")
    exit()

# 5. 结果分析与可视化
# 5.1 变量重要性（随机森林）
feature_names = lucc_columns + continuous_vars
feature_importance = pd.DataFrame({
    'Variable': feature_names,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

plt.figure(figsize=(10, 6))
plt.barh(feature_names, feature_importance['Importance'])
plt.title("全局变量重要性（随机森林）")
plt.xlabel("重要性得分")
plt.gca().invert_yaxis()  # 重要性从高到低显示
plt.show()

# 5.2 地理加权系数空间分布（仅展示连续变量）
n_plots = len(continuous_vars)
fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 5))
if n_plots == 1:  # 如果只有一个连续变量，避免axes索引错误
    axes = [axes]

for i, var in enumerate(continuous_vars):
    # 找到该变量在X中的列索引
    idx = feature_names.index(var)
    axes[i].scatter(coords_train[:, 0], coords_train[:, 1], c=gwr_results.params[:, idx], cmap='coolwarm')
    axes[i].set_title(f"{var}系数")
    axes[i].set_xlabel("经度")
    axes[i].set_ylabel("纬度")
    plt.colorbar(axes[i].collections[0], ax=axes[i], label='系数值')

plt.suptitle("连续变量的地理加权系数空间分布")
plt.tight_layout()
plt.show()

# 6. 输出结果文件
results_df = pd.DataFrame({
    'x': coords_train[:, 0],
    'y': coords_train[:, 1],
    'RSEI_pred': gwr_results.predy.flatten()
})

# 添加所有变量的系数
for i, var in enumerate(feature_names):
    results_df[f"{var}_coef"] = gwr_results.params[:, i]

results_df.to_csv("D:/Google/GWR_k/gwrf_results_hot.csv", index=False)
print("GWRF结果已保存至 gwrf_results.csv")



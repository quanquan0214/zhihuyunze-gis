from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd

data = pd.read_csv("D:/Google/GWR_k/GWR_k_clipped/nanchang_gwr_data.csv")
# 提取所有自变量（独热编码后的lucc + 标准化后的连续变量）
X_vif = data.drop(['x', 'y', 'RSEI'], axis=1)  # 排除坐标和因变量
# 计算VIF
vif = pd.DataFrame()
vif["Variable"] = X_vif.columns
vif["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]
print(vif.sort_values("VIF", ascending=False))

# 剔除VIF > 10的变量（保留代表性类别）
high_vif_cols = vif[vif["VIF"] > 10]["Variable"].tolist()
data = data.drop(high_vif_cols, axis=1)


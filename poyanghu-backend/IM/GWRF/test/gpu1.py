import cupy as cp
from cuml.ensemble import RandomForestRegressor

# 测试 GPU 是否正常工作
arr = cp.array([1, 2, 3])
print(arr * 2)  # 应该输出 [2 4 6]

# 测试 cuML RF
rf = RandomForestRegressor(n_estimators=10)
print("GPU Random Forest 可用!")
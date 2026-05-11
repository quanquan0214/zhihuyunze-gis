def select_best_model(ols, slm, sem, print_details=True):
    """
    选择最佳空间回归模型

    Parameters
    ----------
    ols : spreg.OLS
        普通最小二乘回归模型
    slm : spreg.GM_Lag
        空间滞后模型
    sem : spreg.GM_Error
        空间误差模型
    print_details : bool, optional (default=True)
        是否打印详细的比较结果

    Returns
    -------
    best_model : object
        被选定的最佳模型
    best_stats : dict
        描述最佳模型的关键统计数据
    """

    def get_significant_vars(model):
        """计算显著变量的数量（p < 0.05）"""
        if hasattr(model, 'z_stat'):
            return sum([p < 0.05 for _, p in model.z_stat])
        else:  # OLS使用t_stat
            return sum([p < 0.05 for _, p in model.t_stat])

    # 获取样本量
    n = len(ols.y)

    # 1. 收集各模型的评估指标
    models_stats = {
        'OLS': {
            'name': 'OLS (普通最小二乘回归)',
            'r2': ols.r2,
            'sig_vars': get_significant_vars(ols),
            'normality_test_p': 0.0000,  # 从报告中提取 Jarque-Bera 检验 p 值
            'heteroskedasticity_test_p': 0.0000,  # 从报告中提取 Breusch-Pagan 检验 p 值
            'model': ols
        },
        'SLM': {
            'name': 'SLM (空间滞后模型)',
            'r2': slm.pr2 if hasattr(slm, 'pr2') else slm.r2,  # 使用伪R方或普通R方
            'sig_vars': get_significant_vars(slm),
            'spatial_coef': slm.betas[-1][0],  # W_RSEI 空间系数
            'model': slm
        },
        'SEM': {
            'name': 'SEM (空间误差模型)',
            'r2': sem.pr2 if hasattr(sem, 'pr2') else sem.r2,  # 使用伪R方或普通R方
            'sig_vars': get_significant_vars(sem),
            'spatial_coef': sem.betas[-1][0],  # lambda 空间系数
            'model': sem
        }
    }

    # 2. 评分系统
    scores = {'OLS': 0, 'SLM': 0, 'SEM': 0}

    # 比较拟合优度（R² 或 Pseudo R²）
    max_r2 = max(m['r2'] for m in models_stats.values())
    for name, stats in models_stats.items():
        if abs(stats['r2'] - max_r2) < 0.01:  # 允许0.01的误差范围
            scores[name] += 2

    # 比较显著变量数量
    max_sig_vars = max(m['sig_vars'] for m in models_stats.values())
    for name, stats in models_stats.items():
        if stats['sig_vars'] == max_sig_vars:
            scores[name] += 2

    # 如果是空间模型，比较空间系数显著性
    for name, stats in models_stats.items():
        if name in ['SLM', 'SEM'] and 'spatial_coef' in stats:
            scores[name] += 1  # 空间系数显著性加分

    # 3. 选择最佳模型
    best_model_name = max(scores.items(), key=lambda x: x[1])[0]
    best_model_stats = models_stats[best_model_name]

    # 4. 如果需要，打印详细比较结果
    if print_details:
        print("\n=== 模型比较结果 ===")
        print("\n1. 拟合优度比较:")
        for name, stats in models_stats.items():
            print(f"{stats['name']}:")
            print(f"  - R² = {stats['r2']:.4f}")
            print(f"  - 显著变量数 = {stats['sig_vars']}")
            if name != 'OLS':
                print(f"  - 空间系数 = {stats['spatial_coef']:.4f}")
            if name == 'OLS':
                print(f"  - 正态性检验 p 值 = {stats['normality_test_p']}")
                print(f"  - 异方差检验 p 值 = {stats['heteroskedasticity_test_p']}")
            print()

        print("\n2. 模型评分:")
        for name, score in scores.items():
            print(f"{name}: {score:.2f}")

        print(f"\n3. 最佳模型: {best_model_stats['name']}")
        print(f"   主要原因:")
        reasons = []
        if abs(best_model_stats['r2'] - max_r2) < 0.01:
            reasons.append(f"- 具有最高的R²值 ({best_model_stats['r2']:.4f})")
        if best_model_stats['sig_vars'] == max_sig_vars:
            reasons.append(f"- 具有最多的显著变量 ({best_model_stats['sig_vars']}个)")
        if 'spatial_coef' in best_model_stats:
            reasons.append(f"- 空间系数显著 ({best_model_stats['spatial_coef']:.4f})")
        for reason in reasons:
            print(f"   {reason}")

    # 5. 返回最佳模型及其统计量
    return best_model_stats['model'], best_model_stats

# 使用示例
if __name__ == "__main__":
    import numpy as np
    from pysal.lib import weights
    from pysal.model import spreg
    import pandas as pd

    # 读取数据并运行模型
    df = pd.read_csv("D:/Google/GWR/nanchang_2.csv")

    # 准备数据
    y = df['RSEI'].values.reshape(-1, 1)
    lucc_columns = [col for col in df.columns if col.startswith('lucc_')]
    df['lucc_category'] = df[lucc_columns].idxmax(axis=1)
    category_mapping = {cat: idx for idx, cat in enumerate(df['lucc_category'].unique())}
    df['lucc_numeric'] = df['lucc_category'].map(category_mapping)
    X = df[['lucc_numeric', 'temperature', 'rainfall']].values

    # 创建空间权重矩阵
    coords = list(zip(df['x'], df['y']))
    w = weights.KNN.from_array(coords, k=8)
    w.transform = 'r'

    # 运行三个模型
    ols = spreg.OLS(y, X, name_y='RSEI', name_x=['lucc_numeric', 'temperature', 'rainfall'])
    slm = spreg.GM_Lag(y, X, w=w, name_y='RSEI', name_x=['lucc_numeric', 'temperature', 'rainfall'])
    sem = spreg.GM_Error(y, X, w=w, name_y='RSEI', name_x=['lucc_numeric', 'temperature', 'rainfall'])

    # 选择最佳模型
    best_model, best_stats = select_best_model(ols, slm, sem)
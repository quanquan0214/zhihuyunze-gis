
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pysal.lib import weights
from pysal.model import spreg
from pysal.explore import esda  # 添加这行来进行空间自相关检验
import warnings

warnings.filterwarnings('ignore')


def print_model_diagnostics(model, model_name, w=None, y=None, yhat=None):
    """打印模型诊断统计量"""
    print(f"\n{'-' * 20} {model_name} 模型诊断 {'-' * 20}")
    print(f"模型类型: {model_name}")
    print(model.summary)

    # # 打印模型拟合优度
    # print("\n1. 模型拟合优度:")
    # print(f"R² = {model.r2:.4f}")
    # print(f"调整后的 R² = {model.ar2:.4f}")
    #
    # # 打印信息准则
    # print("\n2. 信息准则:")
    # print(f"AIC = {model.aic:.4f}")
    # print(f"BIC = {model.schwarz:.4f}")
    #
    # # 打印对数似然值
    # print("\n3. 对数似然值:")
    # print(f"Log likelihood = {model.logll:.4f}")
    #
    # # 打印参数估计结果
    # print("\n4. 参数估计及显著性:")
    # print("变量名称      系数      标准误差    统计量     p值")
    # print("-" * 50)
    #
    # if model_name == "OLS":
    #     # OLS模型使用t统计量
    #     for i, name in enumerate(model.name_x):
    #         print(f"{name:<12} {model.betas[i][0]:>8.4f} {model.std_err[i]:>10.4f} "
    #               f"{model.t_stat[i][0]:>10.4f} {model.t_stat[i][1]:>10.4f}")
    #
    #     # 如果提供了权重矩阵和数据，计算空间自相关
    #     if w is not None and y is not None and yhat is not None:
    #         print("\n5. 空间依赖性检验:")
    #         residuals = y.flatten() - yhat.flatten()
    #         mi = esda.moran.Moran(residuals, w)
    #         print("Moran's I 检验 (残差):")
    #         print(f"Moran's I = {mi.I:.4f}")
    #         print(f"p值 = {mi.p_sim:.4f}")
    # else:
    #     # SLM和SEM模型使用z统计量
    #     for i, name in enumerate(model.name_x):
    #         print(f"{name:<12} {model.betas[i][0]:>8.4f} {model.std_err[i]:>10.4f} "
    #               f"{model.z_stat[i][0]:>10.4f} {model.z_stat[i][1]:>10.4f}")


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
    tuple : (best_model, model_stats)
        返回最佳模型对象和包含重要统计量的字典
    """

    def get_significant_vars(model):
        """计算显著变量的数量（p < 0.05）"""
        if hasattr(model, 'z_stat'):
            return sum([p < 0.05 for _, p in model.z_stat])
        else:  # OLS使用t_stat
            return sum([p < 0.05 for _, p in model.t_stat])

    # 1. 收集各模型的评估指标
    models_stats = {
        'OLS': {
            'name': 'OLS (普通最小二乘回归)',
            'r2': ols.r2,
            'aic': ols.aic,
            'bic': ols.schwarz,
            'log_likelihood': ols.logll,
            'sig_vars': get_significant_vars(ols),
            'model': ols
        },
        'SLM': {
            'name': 'SLM (空间滞后模型)',
            'r2': slm.pr2,  # 使用伪R方
            'aic': slm.aic,
            'bic': slm.schwarz,
            'log_likelihood': slm.logll,
            'sig_vars': get_significant_vars(slm),
            'spatial_coef': slm.betas[-1][0],  # W_RSEI系数
            'model': slm
        },
        'SEM': {
            'name': 'SEM (空间误差模型)',
            'r2': sem.pr2,  # 使用伪R方
            'aic': sem.aic,
            'bic': sem.schwarz,
            'log_likelihood': sem.logll,
            'sig_vars': get_significant_vars(sem),
            'spatial_coef': sem.betas[-1][0],  # lambda系数
            'model': sem
        }
    }

    # 2. 评分系统
    scores = {'OLS': 0, 'SLM': 0, 'SEM': 0}

    # 比较R方
    max_r2 = max(m['r2'] for m in models_stats.values())
    for name, stats in models_stats.items():
        if stats['r2'] == max_r2:
            scores[name] += 2

    # 比较AIC（越小越好）
    min_aic = min(m['aic'] for m in models_stats.values())
    for name, stats in models_stats.items():
        if stats['aic'] == min_aic:
            scores[name] += 1.5

    # 比较BIC（越小越好）
    min_bic = min(m['bic'] for m in models_stats.values())
    for name, stats in models_stats.items():
        if stats['bic'] == min_bic:
            scores[name] += 1.5

    # 比较显著变量数量
    max_sig_vars = max(m['sig_vars'] for m in models_stats.values())
    for name, stats in models_stats.items():
        if stats['sig_vars'] == max_sig_vars:
            scores[name] += 2

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
            print(f"  - AIC = {stats['aic']:.4f}")
            print(f"  - BIC = {stats['bic']:.4f}")
            print(f"  - 显著变量数 = {stats['sig_vars']}")
            print(f"  - 对数似然值 = {stats['log_likelihood']:.4f}")
            if name != 'OLS':
                print(f"  - 空间系数 = {stats['spatial_coef']:.4f}")
            print()

        print("\n2. 模型评分:")
        for name, score in scores.items():
            print(f"{name}: {score:.2f}")

        print(f"\n3. 最佳模型: {best_model_stats['name']}")
        print(f"   主要原因:")
        reasons = []
        if best_model_stats['r2'] == max_r2:
            reasons.append(f"- 具有最高的R²值 ({best_model_stats['r2']:.4f})")
        if best_model_stats['aic'] == min_aic:
            reasons.append(f"- 具有最低的AIC值 ({best_model_stats['aic']:.4f})")
        if best_model_stats['bic'] == min_bic:
            reasons.append(f"- 具有最低的BIC值 ({best_model_stats['bic']:.4f})")
        if best_model_stats['sig_vars'] == max_sig_vars:
            reasons.append(f"- 具有最多的显著变量 ({best_model_stats['sig_vars']}个)")
        for reason in reasons:
            print(f"   {reason}")
    # 5. 返回最佳模型及其统计量
    return best_model_stats['model'], best_model_stats

def main():
    try:
        # 1. 读取数据
        print("正在读取数据...")
        df = pd.read_csv("D:/Google/GWR/nanchang_2.csv")

        # 2. 准备空间权重矩阵
        coords = list(zip(df['x'], df['y']))
        w = weights.KNN.from_array(coords, k=8)
        w.transform = 'r'

        # 3. 准备变量
        y = df['RSEI'].values.reshape(-1, 1)

        # 处理LUCC分类
        lucc_columns = [col for col in df.columns if col.startswith('lucc_')]
        df['lucc_category'] = df[lucc_columns].idxmax(axis=1)
        category_mapping = {cat: idx for idx, cat in enumerate(df['lucc_category'].unique())}
        df['lucc_numeric'] = df['lucc_category'].map(category_mapping)

        X = df[['lucc_numeric', 'temperature', 'rainfall']].values

        # 4. 运行三个模型并输出诊断结果
        # OLS模型
        ols = spreg.OLS(y, X, name_y='RSEI',
                        name_x=['lucc_numeric', 'temperature', 'rainfall'])
        # SLM模型
        slm = spreg.GM_Lag(y, X, w=w, name_y='RSEI',
                           name_x=['lucc_numeric', 'temperature', 'rainfall'])
        # SEM模型
        sem = spreg.GM_Error(y, X, w=w, name_y='RSEI',
                             name_x=['lucc_numeric', 'temperature', 'rainfall'])

        print_model_diagnostics(ols, "OLS", w, y, ols.predy)
        print_model_diagnostics(slm, "SLM")
        print_model_diagnostics(sem, "SEM")
        print("\n分析完成！")

        # 选择最佳模型
        #best_model, best_stats = select_best_model(ols, slm, sem, print_details=True)
        # 使用最佳模型进行预测或其他分析
        # predictions = best_model.predy

    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main()
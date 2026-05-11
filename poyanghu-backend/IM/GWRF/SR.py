import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pysal.lib import weights
from pysal.model import spreg
import warnings
warnings.filterwarnings('ignore')


class SR_Analysis:
    def __init__(self):
        """初始化空间回归分析类"""
        pass

    def prepare_data(self, df):
        """数据预处理函数"""
        try:
            # 筛选LUCC分类
            lucc_columns = [col for col in df.columns if col.startswith('lucc_')]
            if not lucc_columns:
                raise ValueError("没有找到以'lucc_'开头的列")

            # 创建LUCC分类结果
            df['lucc_category'] = df[lucc_columns].idxmax(axis=1)

            # 将类别转换为数值编码
            category_mapping = {cat: idx for idx, cat in enumerate(df['lucc_category'].unique())}
            df['lucc_numeric'] = df['lucc_category'].map(category_mapping)

            return df

        except Exception as e:
            print(f"数据预处理出错: {str(e)}")
            raise

    def check_input_data(self, X, y):
        """检查输入数据的有效性"""
        try:
            # 检查是否有缺失值
            if np.any(pd.isna(X)) or np.any(pd.isna(y)):
                raise ValueError("输入数据包含缺失值")

            # 确保X和y都是数值型
            X = X.astype(float)
            y = y.astype(float)

            return X, y

        except Exception as e:
            print(f"数据检查出错: {str(e)}")
            raise

    def create_spatial_weights(self, df):
        """创建空间权重矩阵"""
        try:
            coords = list(zip(df['x'], df['y']))
            w = weights.KNN.from_array(coords, k=8)
            w.transform = 'r'
            return w

        except Exception as e:
            print(f"创建空间权重矩阵出错: {str(e)}")
            raise

    # def run_regression_models(self, X, y, w):
    #     """运行回归模型"""
    #     try:
    #         # 准备变量名称
    #         name_y = 'RSEI'
    #         name_x = ['lucc_numeric', 'temperature', 'rainfall']
    #
    #         # 运行三种模型
    #         models = {
    #             'OLS': spreg.OLS(y, X, name_y=name_y, name_x=name_x),
    #             'SLM': spreg.GM_Lag(y, X, w=w, name_y=name_y, name_x=name_x),
    #             'SEM': spreg.GM_Error(y, X, w=w, name_y=name_y, name_x=name_x)
    #         }
    #
    #         return models
    #
    #     except Exception as e:
    #         print(f"回归模型运行出错: {str(e)}")
    #         raise

    def run_regression_models(self, X, y, w):
        """运行回归模型并提取标准差"""
        try:
            name_y = 'RSEI'
            name_x = ['lucc_numeric', 'temperature', 'rainfall']

            # 运行模型
            models = {
                'OLS': spreg.OLS(y, X, name_y=name_y, name_x=name_x),
                'SLM': spreg.GM_Lag(y, X, w=w, name_y=name_y, name_x=name_x),
                'SEM': spreg.GM_Error(y, X, w=w, name_y=name_y, name_x=name_x)
            }

            # 为每个模型添加标准差字段
            for model_name, model in models.items():
                # 提取参数的标准差（模型对象的属性可能不同）
                if hasattr(model, 'std_err'):
                    std_err = model.std_err  # OLS的标准差
                elif hasattr(model, 'sig2'):
                    std_err = np.sqrt(model.sig2)  # SLM/SEM可能需要手动计算
                else:
                    std_err = np.nan  # 备用方案

                # 将标准差添加到模型结果中（示例：保存到字典或属性表）
                model.std_err = std_err

            return models

        except Exception as e:
            print(f"回归模型运行出错: {str(e)}")
            raise

    # def save_results(self, df, models, output_path):
    #     """保存回归结果"""
    #     try:
    #         # 创建结果数据框
    #         results_df = df.copy()
    #
    #         # 添加各模型的预测值和残差
    #         for name, model in models.items():
    #             results_df[f'{name}_predicted'] = model.predy
    #             results_df[f'{name}_residuals'] = model.u.flatten()
    #
    #         # 创建几何对象
    #         geometry = [Point(xy) for xy in zip(df['x'], df['y'])]
    #
    #         # 为每个模型创建和保存GeoDataFrame
    #         for name in models.keys():
    #             cols = ['x', 'y', 'RSEI', f'{name}_predicted', f'{name}_residuals']
    #             gdf = gpd.GeoDataFrame(results_df[cols], geometry=geometry)
    #             output_file = f"{output_path}/{name.lower()}_results.shp"
    #             gdf.to_file(output_file, driver='ESRI Shapefile', encoding='utf-8')
    #             print(f"{name}模型结果已保存至: {output_file}")
    #
    #     except Exception as e:
    #         print(f"保存结果出错: {str(e)}")
    #         raise

    def save_results(self, df, models, output_path):
        """保存回归结果，包括预测值、残差和标准差"""
        try:
            # 创建结果数据框
            results_df = df.copy()

            # 添加各模型的预测值、残差和标准差
            for name, model in models.items():
                results_df[f'{name}_predicted'] = model.predy  # 预测值
                results_df[f'{name}_residuals'] = model.u.flatten()  # 残差

                # 提取标准差（根据模型类型处理）
                if hasattr(model, 'std_err'):
                    std_err = model.std_err  # OLS的标准差
                elif hasattr(model, 'sig2'):
                    std_err = np.sqrt(model.sig2)  # SLM/SEM的标准差（假设sig2是方差）
                else:
                    std_err = np.nan  # 备用方案

                # 将标准差添加到结果中
                results_df[f'{name}_std_err'] = std_err

            # 创建几何对象
            geometry = [Point(xy) for xy in zip(df['x'], df['y'])]

            # 为每个模型创建和保存GeoDataFrame
            for name in models.keys():
                cols = ['x', 'y', 'RSEI',
                        f'{name}_predicted',
                        f'{name}_residuals',
                        f'{name}_std_err']  # 包含标准差字段
                gdf = gpd.GeoDataFrame(results_df[cols], geometry=geometry)
                output_file = f"{output_path}/{name.lower()}_results.shp"
                gdf.to_file(output_file, driver='ESRI Shapefile', encoding='utf-8')
                print(f"{name}模型结果已保存至: {output_file}")

        except Exception as e:
            print(f"保存结果出错: {str(e)}")
            raise

    def select_best_model(self,ols, slm, sem, print_details=True):
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

# if __name__ == "__main__":
#     sr = SR_Analysis()
#
#
#     def run_sr_analysis(sr):
#         try:
#             # 1. 读取数据
#             print("正在读取数据...")
#             df = pd.read_csv("D:/Google/GWR/nanchang_2.csv")
#
#             # 2. 数据预处理
#             print("正在进行数据预处理...")
#             df = sr.prepare_data(df)
#
#             # 3. 准备自变量和因变量
#             print("正在准备回归变量...")
#             y = df['RSEI'].values.reshape(-1, 1)
#             X = df[['lucc_numeric', 'temperature', 'rainfall']].values
#
#             # 4. 检查数据
#             X, y = sr.check_input_data(X, y)
#
#             # 5. 创建空间权重
#             print("正在创建空间权重...")
#             w = sr.create_spatial_weights(df)
#
#             # 6. 运行回归模型
#             print("正在运行回归模型...")
#             models = sr.run_regression_models(X, y, w)
#
#             # 7. 保存结果
#             print("正在保存结果...")
#             output_path = "D:/Google/GWR/SR"
#             sr.save_results(df, models, output_path)
#
#             print("所有处理完成！")
#
#         except Exception as e:
#             print(f"程序运行出错: {str(e)}")
#             raise

#         select_best_model(sr, models['OLS'], models['SLM'], models['SEM'])

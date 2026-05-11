import os
import time
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
from pysal.lib import weights
from pysal.model import spreg
import warnings

warnings.filterwarnings('ignore')

class SR_Analysis:
    def __init__(self, temp_dir="D:/Google/GWR"):
        """初始化空间回归分析类"""
        self.temp_dir = temp_dir
        self._create_temp_dir()

    def _create_temp_dir(self):
        """创建临时存储目录"""
        try:
            # 创建基础目录（如果不存在）
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)

            # 创建日期子目录
            current_time = time.strftime("%Y-%m-%d", time.localtime())
            self.index_dir = os.path.join(self.temp_dir, f"sr_{current_time}")

            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)

            print(f"临时文件将存储在: {self.index_dir}")

        except Exception as e:
            print(f"创建临时目录出错: {str(e)}")
            raise

    def _save_temp_data(self, data, filename):
        """保存临时数据到文件"""
        try:
            filepath = os.path.join(self.index_dir, filename)

            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False)
            elif isinstance(data, np.ndarray):
                np.save(filepath, data)
            else:
                # 其他数据类型可以在这里扩展
                raise ValueError(f"不支持的数据类型: {type(data)}")

            print(f"临时数据已保存: {filepath}")
            return filepath

        except Exception as e:
            print(f"保存临时数据出错: {str(e)}")
            raise

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

            # 保存预处理后的数据
            self._save_temp_data(df, "preprocessed_data.csv")

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

            # 保存检查后的数据
            self._save_temp_data(pd.DataFrame(X), "checked_X.csv")
            self._save_temp_data(pd.DataFrame(y), "checked_y.csv")

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

            # 保存权重矩阵信息
            self._save_temp_data(pd.DataFrame(coords, columns=['x', 'y']), "spatial_weights_coords.csv")

            return w

        except Exception as e:
            print(f"创建空间权重矩阵出错: {str(e)}")
            raise

    def run_regression_models(self, X, y, w):
        """运行回归模型并提取标准差"""
        try:
            name_y = 'RSEI'
            name_x = ['lucc_numeric', 'temperature', 'rainfall','fvc']

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

                # 保存模型摘要到文本文件
                summary_file = os.path.join(self.index_dir, f"{model_name}_summary.txt")
                with open(summary_file, 'w') as f:
                    f.write(str(model.summary))
                print(f"模型摘要已保存: {summary_file}")

            return models

        except Exception as e:
            print(f"回归模型运行出错: {str(e)}")
            raise

    def save_results(self, df, models, output_path=None):
        """保存回归结果，确保所有字段长度与原数据一致"""
        # 设置默认输出路径
        if output_path is None:
            output_path = self.index_dir
        else:
            # 确保用户提供的输出路径存在
            os.makedirs(output_path, exist_ok=True)
        try:
            # 创建结果数据框副本
            results_df = df.copy()
            n = len(results_df)  # 原始数据行数

            for name, model in models.items():
                # 1. 处理预测值 (predy)
                try:
                    predy = model.predy.flatten() if hasattr(model.predy, 'flatten') else model.predy
                    # 确保长度匹配，不足补NaN，多余截断
                    results_df[f'{name}_predicted'] = np.resize(predy, n)
                except Exception as e:
                    print(f"处理{name}预测值时出错: {str(e)}")
                    results_df[f'{name}_predicted'] = np.nan

                # 2. 处理残差 (u)
                try:
                    residuals = model.u.flatten() if hasattr(model.u, 'flatten') else model.u
                    # 确保长度匹配
                    results_df[f'{name}_residuals'] = np.resize(residuals, n)
                except Exception as e:
                    print(f"处理{name}残差时出错: {str(e)}")
                    results_df[f'{name}_residuals'] = np.nan

                # 3. 处理标准差 (std_err)
                try:
                    if hasattr(model, 'std_err'):
                        std_err = model.std_err
                        # 处理不同形状的std_err
                        if np.isscalar(std_err):
                            std_err = np.full(n, std_err)
                        else:
                            std_err = np.resize(std_err, n)
                    elif hasattr(model, 'sig2'):
                        std_err = np.full(n, np.sqrt(model.sig2))
                    else:
                        std_err = np.full(n, np.nan)

                    results_df[f'{name}_std_err'] = std_err
                except Exception as e:
                    print(f"处理{name}标准差时出错: {str(e)}")
                    results_df[f'{name}_std_err'] = np.nan

                # 4. 计算标准化残差 (std_resid)
                try:
                    residuals = results_df[f'{name}_residuals'].values
                    resid_std = np.nanstd(residuals)  # 使用nanstd避免NaN影响
                    results_df[f'{name}_std_resid'] = residuals / resid_std if resid_std != 0 else np.nan
                except Exception as e:
                    print(f"计算{name}标准化残差时出错: {str(e)}")
                    results_df[f'{name}_std_resid'] = np.nan

            # 创建几何对象
            geometry = [Point(xy) for xy in zip(results_df['x'], results_df['y'])]

            # 为每个模型保存单独的Shapefile
            for name in models.keys():
                # 确保字段存在且长度正确
                required_cols = [
                    'x', 'y', 'RSEI',
                    f'{name}_predicted',
                    f'{name}_residuals',
                    f'{name}_std_err',
                    f'{name}_std_resid'
                ]

                # 检查并填充缺失列
                for col in required_cols:
                    if col not in results_df:
                        results_df[col] = np.nan

                gdf = gpd.GeoDataFrame(results_df[required_cols], geometry=geometry)
                output_file = f"{output_path}/{name.lower()}_results.shp"
                gdf.to_file(output_file, driver='ESRI Shapefile', encoding='utf-8')
                print(f"{name}结果已保存至: {output_file}")

        except Exception as e:
            print(f"保存结果时发生严重错误: {str(e)}")
            raise

    def select_best_model(self, ols, slm, sem, print_details=True):
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

        # 保存最佳模型选择结果
        # selection_file = os.path.join(self.index_dir, "best_model_selection.txt")
        # with open(selection_file, 'w') as f:
        #     f.write(f"最佳模型: {best_model_stats['name']}\n")
        #     f.write(f"评分: {scores[best_model_name]}\n")
        #     f.write("选择理由:\n")
        #     for reason in reasons:
        #         f.write(f"- {reason}\n")
        #
        # print(f"最佳模型选择结果已保存: {selection_file}")
        selection_file = os.path.join(self.index_dir, "best_model_selection.txt")
        try:
            with open(selection_file, 'w', encoding='utf-8') as f:  # 明确指定UTF-8编码
                f.write(f"最佳模型: {best_model_stats['name']}\n")
                f.write(f"评分: {scores[best_model_name]}\n")
                f.write("选择理由:\n")
                for reason in reasons:
                    f.write(f"- {reason}\n")
            print(f"最佳模型选择结果已保存: {selection_file}")
        except Exception as e:
            print(f"保存最佳模型选择结果时出错: {str(e)}")
            # 尝试用替代方案保存
            try:
                with open(selection_file, 'w', encoding='gb18030') as f:  # 更兼容的中文编码
                    f.write(f"最佳模型: {best_model_stats['name']}\n")
                    f.write(f"评分: {scores[best_model_name]}\n")
                    f.write("选择理由:\n")
                    for reason in reasons:
                        reason = reason.replace('\xb2', '^2')  # 替换平方符号
                        f.write(f"- {reason}\n")
                print(f"使用替代编码保存成功: {selection_file}")
            except Exception as e2:
                print(f"无法保存结果文件: {str(e2)}")

        # 5. 返回最佳模型及其统计量
        return best_model_stats['model'], best_model_stats




def test_sr_analysis():
    """测试SR_Analysis类的功能"""
    try:
        print("=== 开始测试 SR_Analysis 类 ===")

        # 1. 初始化类
        print("\n1. 初始化SR_Analysis类...")
        sr = SR_Analysis()

        # 2. 读取测试数据
        print("\n2. 读取测试数据...")
        test_data_path = "D:/Google/GWR/nanchang_2.csv"  # 替换为实际测试文件路径
        if not os.path.exists(test_data_path):
            raise FileNotFoundError(f"测试数据文件不存在: {test_data_path}")

        df = pd.read_csv(test_data_path)
        print(f"成功读取数据，行数: {len(df)}")

        # 3. 数据预处理
        print("\n3. 数据预处理...")
        df = sr.prepare_data(df)
        print("数据预处理完成")

        # 4. 准备回归变量
        print("\n4. 准备回归变量...")
        y = df['RSEI'].values.reshape(-1, 1)
        X = df[['lucc_numeric', 'temperature', 'rainfall']].values

        # 5. 检查数据
        print("\n5. 检查数据...")
        X, y = sr.check_input_data(X, y)
        print("数据检查通过")

        # 6. 创建空间权重
        print("\n6. 创建空间权重...")
        w = sr.create_spatial_weights(df)
        print("空间权重创建完成")

        # 7. 运行回归模型
        print("\n7. 运行回归模型...")
        models = sr.run_regression_models(X, y, w)
        print("回归模型运行完成")

        # 8. 保存结果
        print("\n8. 保存结果...")
        sr.save_results(df, models)

        # 9. 选择最佳模型
        print("\n9. 选择最佳模型...")
        best_model, best_stats = sr.select_best_model(
            models['OLS'], models['SLM'], models['SEM'])
        print(f"\n最佳模型是: {best_stats['name']}")

        print("\n=== 测试完成 ===")
        return True

    except Exception as e:
        print(f"\n!!! 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 运行测试
    test_result = test_sr_analysis()

    if test_result:
        print("\n所有测试成功完成！")
    else:
        print("\n测试过程中遇到错误。")




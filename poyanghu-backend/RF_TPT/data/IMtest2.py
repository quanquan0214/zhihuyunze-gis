# import numpy as np
# from GWRService import GWRService
# from ClimateData import ClimateDataService
#
#
# def run_gwr_analysis():
#     # 初始化服务
#     climate_service = ClimateDataService()
#     gwr_service = GWRService(climate_service)
#
#     # 年份设置
#     target_year = 2020
#     years = [2000, 2010, 2020]
#
#     # 定义子区域范围 (minx, miny, maxx, maxy) - 以鄱阳湖部分区域为例
#     extent = (115.0, 28.5, 116.5, 29.5)
#
#     print("=== 1. 数据预处理与探索 ===")
#     # (1) 验证数据完整性
#     print("\n(1) 验证数据完整性")
#     validation = climate_service.validate_data_files(extent)
#     missing_count = sum(len(v) for k, v in validation.items() if 'missing' in k)
#     print(f"缺失文件数量: {missing_count}")
#
#     # (2) 探索空间自相关性（Moran's I）
#     print("\n(2) 探索空间自相关性（Moran's I）")
#     moran_result = gwr_service.calculate_morans_i(
#         year=target_year,
#         variable='rsei',
#         threshold=1000,
#         extent=extent
#     )
#     print(f"Moran's I: {moran_result['morans_i']:.3f}, p-value: {moran_result['p_value']:.4f}")
#
#     # (3) 检查多重共线性（VIF）
#     print("\n(3) 检查多重共线性（VIF）")
#     vif_results = gwr_service.calculate_vif(
#         year=target_year,
#         include_lucc=True,
#         lucc_encoding='continuous',
#         extent=extent
#     )
#     print("方差膨胀因子 (VIF):")
#     print(f"温度: {vif_results['temperature_vif']:.2f}")
#     print(f"降水: {vif_results['rainfall_vif']:.2f}")
#     print(f"LUCC: {vif_results.get('lucc_vif', 'N/A')}")
#
#     print("\n=== 2. 运行GWR模型 ===")
#     # (1) 子区域GWR分析
#     print("\n(1) 子区域GWR分析")
#     gwr_results = gwr_service.run_gwr(
#         year=target_year,
#         include_lucc=True,
#         lucc_encoding='continuous',
#         extent=extent
#     )
#     print(f"子区域带宽: {gwr_results['bandwidth']:.2f} 米")
#     print(f"子区域AICc: {gwr_results['aic']:.2f}")
#     print(f"子区域局部R²范围: {np.nanmin(gwr_results['local_r2']):.2f} - {np.nanmax(gwr_results['local_r2']):.2f}")
#
#     print("\n=== 3. 结果可视化与解释 ===")
#     # (1) 保存结果栅格
#     print("\n(1) 保存结果栅格")
#     gwr_service.save_gwr_results(gwr_results, year=target_year, extent=extent)
#     print("已保存子区域局部系数和R²栅格文件")
#
#     # (2) 用QGIS可视化结果 (仅文字说明)
#     print("\n(2) 用QGIS可视化结果:")
#     print("1. 加载生成的TIF文件，使用伪彩色渲染（如温度系数：红色=正相关，蓝色=负相关）")
#     print("2. 叠加原始RSEI数据，观察系数与生态环境质量的关联")
#
#     # (3) 关键指标解读 (仅文字说明)
#     print("\n(3) 关键指标解读:")
#     print("| 指标 | 含义 |")
#     print("|---------------------|----------------------------------------------------------------------|")
#     print("| 局部系数 | 正/负值表示自变量对RSEI的促进/抑制作用（单位：标准化后的效应量） |")
#     print("| 局部R² | 模型在局部区域的解释力（0-1，越接近1说明模型越好） |")
#     print("| 带宽 | 空间邻域范围（米），反映空间异质性的尺度 |")
#     print("| AICc | 模型拟合优度（越小越好，用于比较不同模型） |")
#
#     print("\n=== 4. 高级分析扩展 ===")
#     # (1) 多年份对比 - 子区域
#     print("\n(1) 多年份对比 - 子区域")
#     for year in years:
#         results = gwr_service.run_gwr(year=year, extent=extent)
#         gwr_service.save_gwr_results(results, year, extent=extent)
#         print(f"{year}年子区域带宽: {results['bandwidth']:.2f} 米")
#
#     # (2) 不同LUCC编码方式比较 - 子区域
#     print("\n(2) 不同LUCC编码方式比较 - 子区域")
#     results_continuous = gwr_service.run_gwr(target_year, lucc_encoding='continuous', extent=extent)
#     results_dummy = gwr_service.run_gwr(target_year, lucc_encoding='dummy', extent=extent)
#     print(f"连续编码AICc: {results_continuous['aic']:.2f}, 哑变量AICc: {results_dummy['aic']:.2f}")
#
#     # (3) 敏感性分析 - 子区域
#     print("\n(3) 敏感性分析 - 子区域")
#     bw_list = [5000, 10000, 20000]
#     for bw in bw_list:
#         results = gwr_service.run_gwr(target_year, bw=bw, extent=extent)
#         print(f"带宽={bw}时子区域R²均值: {np.nanmean(results['local_r2']):.3f}")
#
#     print("\n=== 5. 结果应用示例 ===")
#     print("\n(1) 案例：鄱阳湖生态保护建议")
#     print("1. 高温负效应区（温度系数显著为负）：")
#     print("   - 可能受城市热岛效应影响，建议增加绿地面积。")
#     print("2. 降水正效应区（降水系数为正）：")
#     print("   - 湿地保护区，需维持自然水文条件。")
#     print("3. LUCC类别3主导区（如农田）：")
#     print("   - 若系数为负，建议优化农业实践以减少生态压力。")
#
#     print("\n=== 常见问题处理 ===")
#     print("1. 带宽过大（覆盖整个区域）：")
#     print("   - 说明空间异质性弱，可能适合普通线性回归（OLS）。")
#     print("2. 局部R²过低：")
#     print("   - 检查是否遗漏重要变量（如人类活动指数）。")
#     print("3. 计算内存不足：")
#     print("   - 使用 `extent` 参数分块分析，或对数据进行随机采样。")
#
#
# if __name__ == "__main__":
#     run_gwr_analysis()
# #
import numpy as np
from IM.GWRService import GWRService
from IM.ClimateData import ClimateDataService


def run_gwr_analysis():
    # 初始化服务
    climate_service = ClimateDataService()
    gwr_service = GWRService(climate_service)

    # 年份设置
    target_year = 2020
    years = [2000, 2010, 2020]

    print("=== 1. 数据预处理与探索 ===")
    # (1) 验证数据完整性
    print("\n(1) 验证数据完整性")
    validation = climate_service.validate_data_files()
    missing_count = sum(len(v) for k, v in validation.items() if 'missing' in k)
    print(f"缺失文件数量: {missing_count}")

    # # (2) 探索空间自相关性（Moran's I）
    # print("\n(2) 探索空间自相关性（Moran's I）")
    # moran_result = gwr_service.calculate_morans_i(year=target_year, variable='rsei', threshold=1000)
    # print(f"Moran's I: {moran_result['morans_i']:.3f}, p-value: {moran_result['p_value']:.4f}")
    #
    # # (3) 检查多重共线性（VIF）
    # print("\n(3) 检查多重共线性（VIF）")
    # vif_results = gwr_service.calculate_vif(year=target_year, include_lucc=True, lucc_encoding='continuous')
    # print("方差膨胀因子 (VIF):")
    # print(f"温度: {vif_results['temperature_vif']:.2f}")
    # print(f"降水: {vif_results['rainfall_vif']:.2f}")
    # print(f"LUCC: {vif_results.get('lucc_vif', 'N/A')}")
    #
    # print("\n=== 2. 运行GWR模型 ===")
    # # (1) 全区域分析
    # print("\n(1) 全区域分析")
    # gwr_results = gwr_service.run_gwr(
    #     year=target_year,
    #     include_lucc=True,
    #     lucc_encoding='continuous'
    # )
    # print(f"带宽: {gwr_results['bandwidth']:.2f} 米")
    # print(f"全局AICc: {gwr_results['aic']:.2f}")
    # print(f"局部R²范围: {np.nanmin(gwr_results['local_r2']):.2f} - {np.nanmax(gwr_results['local_r2']):.2f}")

    # (2) 子区域分析（可选）
    print("\n(2) 子区域分析（可选）")
    extent = (116.0, 28.5, 116.5, 29.0)  # 示例：鄱阳湖部分区域
    subregion_results = gwr_service.run_gwr(
        year=target_year,
        extent=extent,
        include_lucc=True
    )
    print(f"子区域带宽: {subregion_results['bandwidth']:.2f} 米")
    print(f"子区域AICc: {subregion_results['aic']:.2f}")

    # print("\n=== 3. 结果可视化与解释 ===")
    ## (1) 保存结果栅格
    # print("\n(1) 保存结果栅格")
    # gwr_service.save_gwr_results(gwr_results, year=target_year)
    # print("已保存局部系数和R²栅格文件")
    #
    # # (2) 用QGIS可视化结果 (仅文字说明)
    # print("\n(2) 用QGIS可视化结果:")
    # print("1. 加载生成的TIF文件，使用伪彩色渲染（如温度系数：红色=正相关，蓝色=负相关）")
    # print("2. 叠加原始RSEI数据，观察系数与生态环境质量的关联")
    #
    # # (3) 关键指标解读 (仅文字说明)
    # print("\n(3) 关键指标解读:")
    # print("| 指标 | 含义 |")
    # print("|---------------------|----------------------------------------------------------------------|")
    # print("| 局部系数 | 正/负值表示自变量对RSEI的促进/抑制作用（单位：标准化后的效应量） |")
    # print("| 局部R² | 模型在局部区域的解释力（0-1，越接近1说明模型越好） |")
    # print("| 带宽 | 空间邻域范围（米），反映空间异质性的尺度 |")
    # print("| AICc | 模型拟合优度（越小越好，用于比较不同模型） |")

    print("\n=== 4. 高级分析扩展 ===")
    # (1) 多年份对比
    print("\n(1) 多年份对比")
    for year in years:
        results = gwr_service.run_gwr(year=year)
        gwr_service.save_gwr_results(results, year)
        print(f"{year}年带宽: {results['bandwidth']:.2f} 米")

    # (2) 不同LUCC编码方式比较
    print("\n(2) 不同LUCC编码方式比较")
    results_continuous = gwr_service.run_gwr(target_year, lucc_encoding='continuous')
    results_dummy = gwr_service.run_gwr(target_year, lucc_encoding='dummy')
    print(f"连续编码AICc: {results_continuous['aic']:.2f}, 哑变量AICc: {results_dummy['aic']:.2f}")

    # (3) 敏感性分析
    print("\n(3) 敏感性分析")
    bw_list = [5000, 10000, 20000]
    for bw in bw_list:
        results = gwr_service.run_gwr(target_year, bw=bw)
        print(f"带宽={bw}时R²均值: {np.nanmean(results['local_r2']):.3f}")

    print("\n=== 5. 结果应用示例 ===")
    print("\n(1) 案例：鄱阳湖生态保护建议")
    print("1. 高温负效应区（温度系数显著为负）：")
    print("   - 可能受城市热岛效应影响，建议增加绿地面积。")
    print("2. 降水正效应区（降水系数为正）：")
    print("   - 湿地保护区，需维持自然水文条件。")
    print("3. LUCC类别3主导区（如农田）：")
    print("   - 若系数为负，建议优化农业实践以减少生态压力。")

    print("\n=== 常见问题处理 ===")
    print("1. 带宽过大（覆盖整个区域）：")
    print("   - 说明空间异质性弱，可能适合普通线性回归（OLS）。")
    print("2. 局部R²过低：")
    print("   - 检查是否遗漏重要变量（如人类活动指数）。")
    print("3. 计算内存不足：")
    print("   - 使用 `extent` 参数分块分析，或对数据进行随机采样。")


if __name__ == "__main__":
    run_gwr_analysis()

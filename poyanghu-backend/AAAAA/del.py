import gc

# 在内存密集型操作后调用
gc.collect()  # 强制垃圾回收


# @app.route('/api/spatial-regression', methods=['POST'])
# def spatial_regression():
#     """Perform spatial regression analysis and return results directly"""
#     data = request.get_json()
#     year = data.get('year')
#     region = data.get('region')
#
#     if not year or not region:
#         return jsonify({"status": "error", "message": "Missing year or region"}), 400
#
#     try:
#         year = int(year)
#         service = SRService(year, region)
#
#         # Load CSV
#         if not os.path.exists(service.csv_out):
#             return jsonify({"status": "error", "message": "CSV file not found. Run preprocessing first."}), 404
#         df = pd.read_csv(service.csv_out)
#
#         # Run analysis pipeline
#         df = service.prepare_data(df)
#         w = service.create_spatial_weights(df)
#         y = df['rsei'].values.reshape(-1, 1)
#         X = df[['lucc_numeric', 'temperature', 'rainfall', 'fvc']].values
#         models = service.run_regression_models(X, y, w)
#         service.save_results(df, models)
#         best_model, best_stats = service.select_best_model(models['OLS'], models['SLM'], models['SEM'])
#
#         # Read all result files and convert to JSON
#         results = {}
#         for model in ['OLS', 'SLM', 'SEM']:
#             shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")
#             if os.path.exists(shp_path):
#                 gdf = gpd.read_file(shp_path)
#                 results[model] = json.loads(gdf.to_crs(epsg=4326).to_json())
#
#         # Read best model selection text
#         best_model_path = os.path.join(service.work_dir, "best_model_selection.txt")
#         best_model_text = ""
#         if os.path.exists(best_model_path):
#             with open(best_model_path, 'r') as f:
#                 best_model_text = f.read()
#
#         return jsonify({
#             "status": "success",
#             "message": "Spatial regression completed successfully",
#             "best_model": {
#                 "name": best_stats['name'],
#                 "r2": best_stats['r2'],
#                 "selection_text": best_model_text
#             },
#             "results": results  # 直接返回所有模型结果数据
#         }), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

# @app.route('/api/read-csv', methods=['GET'])
# def read_csv():
#     """Convert CSV to JSON for frontend display"""
#     year = request.args.get('year')
#     region = request.args.get('region')
#
#     if not year or not region:
#         return jsonify({"status": "error", "message": "Missing year or region"}), 400
#
#     try:
#         year = int(year)
#         service = SRService(year, region)
#         csv_path = service.csv_out
#
#         if not os.path.exists(csv_path):
#             return jsonify({"status": "error", "message": "CSV file not found"}), 404
#
#         df = pd.read_csv(csv_path)
#         data = df.to_dict(orient='records')
#
#         return jsonify({
#             "status": "success",
#             "data": data
#         }), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#
# @app.route('/api/spatial-regression', methods=['POST'])
# def spatial_regression():
#     """Perform spatial regression analysis with customizable variables"""
#     data = request.get_json()
#     year = data.get('year')
#     region = data.get('region')
#     model = data.get('model', 'best')  # 默认为选择最佳模型
#     x_vars = data.get('independent_vars', ['lucc_numeric', 'temperature', 'rainfall', 'fvc'])  # 默认自变量
#     y_var = data.get('dependent_var', 'rsei')  # 默认因变量
#
#     # 参数验证
#     if not year or not region:
#         return jsonify({"status": "error", "message": "Missing year or region"}), 400
#
#     if model.upper() not in ['BEST', 'OLS', 'SLM', 'SEM']:
#         return jsonify({"status": "error", "message": "Invalid model parameter"}), 400
#
#     # 验证自变量是否有效
#     valid_x_vars = ['lucc_numeric', 'temperature', 'rainfall', 'fvc', 'dist']
#     for var in x_vars:
#         if var not in valid_x_vars:
#             return jsonify({"status": "error", "message": f"Invalid independent variable: {var}"}), 400
#
#     try:
#         year = int(year)
#         service = SRService(year, region)
#
#         # 加载CSV文件
#         if not os.path.exists(service.csv_out):
#             return jsonify({"status": "error", "message": "CSV file not found. Run preprocessing first."}), 404
#         df = pd.read_csv(service.csv_out)
#
#         # 检查因变量是否存在
#         if y_var not in df.columns:
#             return jsonify({"status": "error", "message": f"Dependent variable '{y_var}' not found in data"}), 400
#
#         # 准备自变量 - 过滤掉不存在的变量（特别是'dist'）
#         actual_x_vars = [var for var in x_vars if var in df.columns and var != 'dist']
#         if not actual_x_vars:
#             return jsonify({"status": "error", "message": "No valid independent variables selected"}), 400
#
#         # 准备数据
#         df = service.prepare_data(df)
#         w = service.create_spatial_weights(df)
#         y = df[y_var].values.reshape(-1, 1)
#         X = df[actual_x_vars].values
#
#         # 运行回归模型
#         models = service.run_regression_models(X, y, w)
#         service.save_results(df, models)
#         best_model, best_stats = service.select_best_model(models['OLS'], models['SLM'], models['SEM'])
#
#         # 准备响应数据
#         if model.upper() == 'BEST':
#             selected_model = best_stats['name']
#             selected_stats = best_stats
#         else:
#             selected_model = model.upper()
#             selected_stats = {
#                 'name': selected_model,
#                 'r2': models[selected_model].r2,
#                 'params': dict(zip(['intercept'] + actual_x_vars, models[selected_model].params.tolist())),
#                 'pvalues': dict(zip(['intercept'] + actual_x_vars, models[selected_model].pvalues.tolist()))
#             }
#
#         return jsonify({
#             "status": "success",
#             "message": "Spatial regression completed successfully",
#             "parameters": {
#                 "dependent_variable": y_var,
#                 "independent_variables": actual_x_vars,
#                 "requested_variables": x_vars
#             },
#             "result": {
#                 "selected_model": selected_model,
#                 "stats": selected_stats,
#                 "is_best": (model.upper() == 'BEST' or selected_model == best_stats['name'])
#             }
#         }), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


#
# @app.route('/api/spatial-regression', methods=['POST'])
# def spatial_regression():
#     """Enhanced spatial regression endpoint with complete result generation"""
#     try:
#         data = request.get_json()
#
#         # 1. 参数验证和提取
#         year = data.get('year')
#         region = data.get('region')
#         if not year or not region:
#             return jsonify({"status": "error", "message": "Missing year or region"}), 400
#
#         # 参数默认值设置
#         model_type = data.get('model', 'best').upper()
#         y_var = data.get('dependent_var', 'rsei')
#         requested_x_vars = data.get('independent_vars', ['lucc_numeric', 'temperature', 'rainfall', 'fvc'])
#
#         # 2. 初始化服务并加载数据
#         service = SRService(year=int(year), region=region)
#         if not os.path.exists(service.csv_out):
#             return jsonify({"status": "error", "message": "Preprocessed data not found"}), 404
#
#         df = pd.read_csv(service.csv_out)
#         service.df = df  # 存储供SHP生成使用
#
#         # 3. 变量处理（关键修改部分）
#         # 获取实际可用的自变量（排除不存在的和dist）
#         available_vars = set(df.columns) & set(requested_x_vars) - {'dist'}
#         actual_x_vars = [var for var in requested_x_vars
#                          if var in available_vars]
#
#         if not actual_x_vars:
#             return jsonify({
#                 "status": "error",
#                 "message": "No valid independent variables selected",
#                 "requested_vars": requested_x_vars,
#                 "available_vars": list(df.columns)
#             }), 400
#
#         # 4. 准备回归数据
#         X = df[actual_x_vars].values
#         y = df[y_var].values.reshape(-1, 1)
#         w = service.create_spatial_weights(df)
#
#         # 5. 运行回归（自动生成SHP文件）
#         models = service.run_regression_models(
#             X=X, y=y, w=w,
#             name_y=y_var,
#             name_x=actual_x_vars  # 使用实际有效的变量名
#         )
#
#         # 6. 结果处理
#         best_model, best_stats = service.select_best_model(
#             models['OLS'], models['SLM'], models['SEM']
#         )
#
#         # 7. 构建响应
#         response = {
#             "status": "success",
#             "parameters": {
#                 "actual_used": {
#                     "dependent": y_var,
#                     "independent": actual_x_vars
#                 },
#                 "original_request": {
#                     "independent": requested_x_vars
#                 }
#             },
#             "result": {
#                 "best_model": best_stats['name'],
#                 "r_squared": best_stats['r2'],
#                 "generated_files": [
#                     f"{m}_results.shp" for m in ['OLS', 'SLM', 'SEM']
#                 ]
#             }
#         }
#
#         # 8. 添加模型特定结果（如果未选择BEST）
#         if model_type != 'BEST':
#             response["result"]["selected_model"] = {
#                 "type": model_type,
#                 "r_squared": models[model_type].r2,
#                 "coefficients": dict(zip(
#                     ['intercept'] + actual_x_vars,
#                     models[model_type].params.tolist()
#                 ))
#             }
#         # 7. 构建完整响应
#         response = {
#             "status": "success",
#             "parameters": {
#                 "year": year,
#                 "region": region,
#                 "actual_used": {
#                     "dependent": y_var,
#                     "independent": actual_x_vars
#                 },
#                 "original_request": {
#                     "independent": requested_x_vars
#                 }
#             },
#             "best_model": {
#                 "type": best_stats['name'],
#                 "r_squared": best_stats['r2'],
#                 "adjusted_r_squared": best_stats.get('adj_r2'),
#                 "log_likelihood": best_stats.get('log_likelihood'),
#                 "akaike_info_criterion": best_stats.get('akaike'),
#                 "schwarz_criterion": best_stats.get('schwarz'),
#                 "coefficients": best_stats['params'],
#                 "p_values": best_stats['pvalues'],
#                 "standard_errors": best_stats.get('std_err'),
#                 "t_values": best_stats.get('t_stat')
#             },
#             "generated_files": [
#                 f"{m}_results.shp" for m in ['OLS', 'SLM', 'SEM']
#             ]
#         }
#
#         # 8. 如果指定了特定模型，添加该模型的完整结果
#         if model_type != 'BEST' and model_type in models:
#             selected_model = models[model_type]
#             response["selected_model"] = {
#                 "type": model_type,
#                 "r_squared": selected_model.r2,
#                 "adjusted_r_squared": getattr(selected_model, 'adj_r2', None),
#                 "log_likelihood": getattr(selected_model, 'logll', None),
#                 "akaike_info_criterion": getattr(selected_model, 'aic', None),
#                 "schwarz_criterion": getattr(selected_model, 'schwarz', None),
#                 "coefficients": dict(zip(
#                     ['intercept'] + actual_x_vars,
#                     selected_model.params.tolist()
#                 )),
#                 "p_values": dict(zip(
#                     ['intercept'] + actual_x_vars,
#                     selected_model.pvalues.tolist()
#                 )),
#                 "standard_errors": dict(zip(
#                     ['intercept'] + actual_x_vars,
#                     selected_model.std_err.tolist()
#                 )) if hasattr(selected_model, 'std_err') else None,
#                 "t_values": dict(zip(
#                     ['intercept'] + actual_x_vars,
#                     selected_model.tvalues.tolist()
#                 )) if hasattr(selected_model, 'tvalues') else None
#             }
#         return jsonify(response), 200
#
#     except Exception as e:
#         return jsonify({
#             "status": "error",
#             "message": str(e),
#             "traceback": traceback.format_exc()
#         }), 500
#

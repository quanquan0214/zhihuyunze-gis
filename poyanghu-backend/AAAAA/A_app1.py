import json
import os
import matplotlib
matplotlib.use('Agg')
from flask import Flask, request, jsonify, send_file
from datetime import datetime, timedelta
from flask_cors import CORS
import pandas as pd
import zipfile
import traceback
import shutil
import geopandas as gpd
from werkzeug.utils import secure_filename
from A import SRService

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 禁用 ASCII 转义
app.config['SECRET_KEY'] = 'pylake'
CORS(app)

# Configuration
UPLOAD_FOLDER_IM = 'D:/Google/city'
ALLOWED_EXTENSIONS = {'shp', 'shx', 'dbf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_IM

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_shapefile(shp_path):
    """Validate if shapefile is readable"""
    try:
        gpd.read_file(shp_path)
        return True
    except Exception:
        return False

def zip_shapefile(shp_path, zip_path):
    """Zip shapefile and its associated files"""
    base_name = os.path.splitext(shp_path)[0]
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for ext in ['shp', 'shx', 'dbf', 'prj']:
            file_path = f"{base_name}.{ext}"
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
    return zip_path

@app.route('/api/preprocess', methods=['POST'])
def preprocess():
    """预处理栅格数据并生成CSV，返回前50行数据"""
    data = request.get_json()

    # 必选参数
    year = data.get('year')
    region = data.get('region')

    # 可选参数（带默认值）
    res = data.get('res', '500m')  # 精度
    src = data.get('src', 'WGS 1984')  # 坐标系
    resuml = data.get('resuml', 'linear')  # 重分类方式

    # 参数验证
    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    if res not in ['250m', '500m', '1000m', '2000m']:
        return jsonify({"status": "error", "message": "Invalid resolution value"}), 400

    try:
        year = int(year)
        if year < 1900 or year > datetime.now().year:
            return jsonify({"status": "error", "message": "Invalid year"}), 400

        # 初始化服务（需修改SRService以支持新参数）
        service = SRService(
            year=year,
            region=region
            # resolution=res,
            # coordinate_system=src,
            # reclass_method=resuml,
        )

        # 处理数据
        if not service.process_all_rasters():
            return jsonify({"status": "error", "message": "Raster processing failed"}), 500
        if not service.create_csv():
            return jsonify({"status": "error", "message": "CSV creation failed"}), 500

        # 读取CSV并限制返回50行
        df = pd.read_csv(service.csv_out)
        csv_data = df.head(50).to_dict(orient='records')

        return jsonify({
            "status": "success",
            "message": "Preprocessing completed successfully",
            "parameters": {  # 返回实际使用的参数
                "resolution": res,
                "coordinate_system": src,
                "reclass_method": resuml,
            },
            "data": csv_data  # 只返回前50行
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/download-shapefile', methods=['GET'])
def download_shapefile():
    """Download shapefile for a specified model"""
    year = request.args.get('year')
    region = request.args.get('region')
    model = request.args.get('model')

    if not all([year, region, model]) or model.upper() not in ['OLS', 'SLM', 'SEM']:
        return jsonify({"status": "error", "message": "Invalid or missing parameters"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")

        if not os.path.exists(shp_path):
            return jsonify({"status": "error", "message": "Shapefile not found"}), 404

        # Create temporary zip file
        temp_zip = os.path.join(service.work_dir, f"{model.lower()}_results.zip")
        zip_shapefile(shp_path, temp_zip)

        response = send_file(temp_zip, as_attachment=True, download_name=f"{model.lower()}_results.zip")

        # Clean up zip file after sending
        @response.call_on_close
        def cleanup():
            os.remove(temp_zip)

        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/shapefile-fields', methods=['GET'])
def shapefile_fields():
    """Return field descriptions for a model's shapefile"""
    year = request.args.get('year')
    region = request.args.get('region')
    model = request.args.get('model')

    if not all([year, region, model]) or model.upper() not in ['OLS', 'SLM', 'SEM']:
        return jsonify({"status": "error", "message": "Invalid or missing parameters"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")

        if not os.path.exists(shp_path):
            return jsonify({"status": "error", "message": "Shapefile not found"}), 404

        # Define field descriptions based on SRService.save_results()
        fields = [
            {"name": "x", "type": "float", "description": "Longitude coordinate"},
            {"name": "y", "type": "float", "description": "Latitude coordinate"},
            {"name": "rsei", "type": "float", "description": "Remote Sensing Ecological Index"},
            {"name": f"{model.lower()}_predicted", "type": "float",
             "description": f"Predicted RSEI values from {model}"},
            {"name": f"{model.lower()}_residuals", "type": "float", "description": f"Residuals from {model}"},
            {"name": f"{model.lower()}_std_resid", "type": "float",
             "description": f"Standardized residuals from {model}"}
        ]

        return jsonify({
            "status": "success",
            "fields": fields
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/spatial-regression', methods=['POST'])
def spatial_regression():
    """使用SRService的select_best_model方法获取最佳模型结果"""
    try:
        data = request.get_json()

        # 1. 参数验证
        required_params = ['year', 'region']
        if not all(param in data for param in required_params):
            missing = [p for p in required_params if p not in data]
            return jsonify({
                "status": "error",
                "message": f"缺少必要参数: {', '.join(missing)}"
            }), 400

        year = data['year']
        region = data['region']

        # 2. 初始化服务
        try:
            service = SRService(year=int(year), region=region)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"服务初始化失败: {str(e)}"
            }), 500

        # 3. 加载数据
        if not hasattr(service, 'csv_out') or not os.path.exists(service.csv_out):
            return jsonify({
                "status": "error",
                "message": "预处理数据文件不存在",
                "path": getattr(service, 'csv_out', '未指定')
            }), 404

        try:
            df = pd.read_csv(service.csv_out)
            # 验证必要的坐标列
            if not all(col in df.columns for col in ['x', 'y']):
                return jsonify({
                    "status": "error",
                    "message": "数据缺少必要的坐标列(x,y)"
                }), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"数据加载失败: {str(e)}"
            }), 500

        # 4. 处理变量
        y_var = data.get('dependent_var', 'rsei')
        if y_var not in df.columns:
            return jsonify({
                "status": "error",
                "message": f"指定的因变量'{y_var}'不存在",
                "available_variables": list(df.columns)
            }), 400

        default_x_vars = ['lucc_numeric', 'temperature', 'rainfall', 'fvc']
        requested_x_vars = data.get('independent_vars', default_x_vars)
        actual_x_vars = [var for var in requested_x_vars
                         if var in df.columns and var != 'dist']

        if not actual_x_vars:
            return jsonify({
                "status": "error",
                "message": "没有可用的自变量",
                "requested_vars": requested_x_vars,
                "available_vars": [v for v in df.columns if v != 'dist']
            }), 400

        # 5. 准备数据并运行模型
        try:
            X = df[actual_x_vars].values
            y = df[y_var].values.reshape(-1, 1)
            service.df = df  # 为shapefile生成设置df

            w = service.create_spatial_weights(df)
            models = service.run_regression_models(
                X=X, y=y, w=w,
                name_y=y_var,
                name_x=actual_x_vars
            )

            # 6. 使用服务类的方法选择最佳模型
            best_model, best_stats = service.select_best_model(
                models['OLS'], models['SLM'], models['SEM']
            )
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"模型计算失败: {str(e)}",
                "traceback": traceback.format_exc()
            }), 500

        # 7. 准备响应数据
        response = {
            "status": "success",
            "best_model": {
                "type": best_stats['name'],
                "r_squared": best_stats['r2'],
                "parameters": {
                    "dependent": y_var,
                    "independent": actual_x_vars
                },
                "diagnostics": {
                    "sample_size": len(df),
                    "coordinates_check": "valid" if all(col in df.columns for col in ['x', 'y']) else "invalid"
                }
            },
            "metadata": {
                "year": year,
                "region": region,
                "model_comparison": ["OLS", "SLM", "SEM"],
            }
        }

        # 8. 如果存在其他统计量，添加到响应中
        optional_stats = ['adj_r2', 'aic', 'logll']
        for stat in optional_stats:
            if hasattr(best_model, stat):
                response['best_model'][stat] = getattr(best_model, stat)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"未预期的错误: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/read-csv', methods=['GET'])
def read_csv():
    """Convert first 50 rows of CSV to JSON for frontend display"""
    year = request.args.get('year')
    region = request.args.get('region')

    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        csv_path = service.csv_out

        if not os.path.exists(csv_path):
            return jsonify({"status": "error", "message": "CSV file not found"}), 404

        df = pd.read_csv(csv_path)
        data = df.head(50).to_dict(orient='records')
        columns = [{"name": col, "type": str(df[col].dtype)} for col in df.columns]

        return jsonify({
            "status": "success",
            "data": data,
            "columns": columns,
            "total_rows": len(df)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/results/visualize', methods=['GET'])
def visualize_results():
    """Return GeoJSON for visualization"""
    year = request.args.get('year')
    region = request.args.get('region')
    model = request.args.get('model')

    if not all([year, region, model]) or model.upper() not in ['OLS', 'SLM', 'SEM']:
        return jsonify({"status": "error", "message": "Invalid or missing parameters"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        shp_path = os.path.join(service.work_dir, f"{model.lower()}_results.shp")

        if not os.path.exists(shp_path):
            return jsonify({"status": "error", "message": "Shapefile not found"}), 404

        gdf = gpd.read_file(shp_path)
        geojson = gdf.to_crs(epsg=4326).to_json()  # Ensure WGS84 for frontend compatibility

        return jsonify({
            "status": "success",
            "geojson": json.loads(geojson)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/download-csv', methods=['GET'])
def download_csv():
    """Download the preprocessed CSV file"""
    year = request.args.get('year')
    region = request.args.get('region')

    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    try:
        year = int(year)
        service = SRService(year, region)
        csv_path = service.csv_out

        if not os.path.exists(csv_path):
            return jsonify({"status": "error", "message": "CSV file not found"}), 404

        return send_file(csv_path, as_attachment=True, download_name=f"result_{year}.csv")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload/region', methods=['POST'])
def upload_region():
    """Upload a shapefile and return its GeoJSON content"""
    region_code = request.form.get('region_code')
    if not region_code or 'shp_file' not in request.files:
        return jsonify({"status": "error", "message": "Missing region_code or shp_file"}), 400

    region_code = secure_filename(region_code)
    shp_file = request.files['shp_file']
    if not allowed_file(shp_file.filename):
        return jsonify({"status": "error", "message": "Invalid shapefile format"}), 400

    try:
        # Create unique directory for region
        region_dir = os.path.join(app.config['UPLOAD_FOLDER'], region_code)
        os.makedirs(region_dir, exist_ok=True)

        # Save shapefile
        shp_path = os.path.join(region_dir, f"{region_code}.shp")
        shp_file.save(shp_path)

        # Save optional files
        for ext in ['shx', 'dbf', 'prj']:
            if f"{ext}_file" in request.files:
                file = request.files[f"{ext}_file"]
                if file and allowed_file(file.filename):
                    file.save(os.path.join(region_dir, f"{region_code}.{ext}"))

        # Validate shapefile and convert to GeoJSON
        gdf = gpd.read_file(shp_path)
        if gdf.empty:
            shutil.rmtree(region_dir)
            return jsonify({"status": "error", "message": "Empty shapefile"}), 400

        geojson_data = json.loads(gdf.to_crs(epsg=4326).to_json())

        # Dynamically update SRService.city_shapes
        SRService.city_shapes[region_code] = shp_path

        return jsonify({
            "status": "success",
            "message": "Shapefile uploaded and processed successfully",
            "region_code": region_code,
            "geojson": geojson_data  # 直接返回GeoJSON数据
        }), 200
    except Exception as e:
        if os.path.exists(region_dir):
            shutil.rmtree(region_dir)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7891)
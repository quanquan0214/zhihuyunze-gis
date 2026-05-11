from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import geopandas as gpd
import json
import time
from shapely.geometry import mapping, Point
from typing import Dict
from Flexible_GWR import FlexibleRasterProcessor, FlexibleSRAnalysis

app = Flask(__name__)

UPLOAD_FOLDER = "D:/Google/GWR/temp/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === 预设城市区域映射 ===
def get_city_mapping() -> Dict[str, Dict[str, str]]:
    """Return a dictionary mapping city codes to their full names and geojson paths"""
    return {
        'NC': {'name': '南昌市', 'path': "D:/Google/GLC_FCS30/南昌市_市.geojson"},
        'JDZ': {'name': '景德镇市', 'path': "D:/Google/GLC_FCS30/景德镇市_市.geojson"},
        'SR': {'name': '上饶市', 'path': "D:/Google/GLC_FCS30/上饶市_市.geojson"},
        'YT': {'name': '鹰潭市', 'path': "D:/Google/GLC_FCS30/鹰潭市_市.geojson"},
        'JJ': {'name': '九江市', 'path': "D:/Google/GLC_FCS30/九江市_市.geojson"},
        'FZ': {'name': '抚州市', 'path': "D:/Google/GLC_FCS30/抚州市_市.geojson"}
    }

@app.route("/api/preprocess", methods=["POST"]) #预处理数据
def preprocess():
    try:
        year = int(request.form.get("year", 2000))
        variables = request.form.get("variables") # 例如 "temperature,rainfall,rsei,lucc,fvc"
        variables = json.loads(variables) if isinstance(variables, str) else variables

        # 解析区域选择
        region_file = request.files.get("region")
        region_code = request.form.get("region_code")
        lon = request.form.get("lon")
        lat = request.form.get("lat")

        if region_file:
            filename = secure_filename(region_file.filename)
            region_path = os.path.join(UPLOAD_FOLDER, filename)
            region_file.save(region_path)
            region_gdf = gpd.read_file(region_path)
        elif region_code and region_code in get_city_mapping():
            region_path = get_city_mapping()[region_code]['path']
            region_gdf = gpd.read_file(region_path)
        elif lon and lat:
            pt = Point(float(lon), float(lat))
            region_gdf = gpd.GeoDataFrame(geometry=[pt.buffer(0.1)], crs="EPSG:4326")
        else:
            return jsonify({"error": "Missing region file, code, or coordinates."}), 400

        # 配置参数，可自定义精度、坐标系、标准化
        target_res = request.form.get("target_res")  # 如 "0.00449,0.00449"
        if target_res:
            res = [float(r) for r in target_res.split(",")]
        else:
            res = (0.0044915764205976155, 0.004491576420597607)

        config = {
            "temp_dir": "./temp",
            "standardize": request.form.get("standardize", "true").lower() == "true",
            "target_res": res,
            "target_bounds": (113.9423, 26.5048, 118.4788, 30.0800),
            "target_shape": (796, 1010)
        }

        processor = FlexibleRasterProcessor(year, region_gdf, variables, config)
        csv_path = processor.run()

        return jsonify({"message": "Preprocessing complete", "csv_path": csv_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download-shapefile", methods=["GET"])
def download_shapefile():
    try:
        model = request.args.get("model", "best")
        today = time.strftime('%Y-%m-%d')
        base_path = f"./temp/sr_{today}"
        model = model.lower()

        if model == "best":
            # 返回首个可用模型文件
            for name in ["slm", "sem", "ols"]:
                path = os.path.join(base_path, f"{name}_results.shp")
                if os.path.exists(path):
                    return send_file(path, as_attachment=True)
            return jsonify({"error": "No model results found."}), 404

        # 指定模型下载
        path = os.path.join(base_path, f"{model}_results.shp")
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        else:
            return jsonify({"error": f"Model result not found: {model}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/shapefile-fields", methods=["GET"]) #读取 shapefile 字段信息
def shapefile_fields():
    try:
        model = request.args.get("model", "best")
        today = time.strftime('%Y-%m-%d')
        base_path = f"./temp/sr_{today}"
        model = model.lower()

        if model == "best":
            for name in [ "slm", "sem", "ols"]:
                path = os.path.join(base_path, f"{name}_results.shp")
                if os.path.exists(path):
                    gdf = gpd.read_file(path)
                    return jsonify({"model": name.upper(), "fields": list(gdf.columns)})
            return jsonify({"error": "No shapefile found for best model."}), 404

        path = os.path.join(base_path, f"{model}_results.shp")
        if os.path.exists(path):
            gdf = gpd.read_file(path)
            return jsonify({"model": model.upper(), "fields": list(gdf.columns)})
        else:
            return jsonify({"error": "Shapefile not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/spatial-regression", methods=["POST"]) #空间回归分析
def spatial_regression():
    try:
        csv_path = request.form.get("csv_path")
        if not csv_path:
            # 默认调用最新生成的 CSV 文件
            latest_dir = max([d for d in os.listdir("./temp") if d.startswith("20")], default=None)
            if latest_dir:
                candidates = [f for f in os.listdir(f"./temp/{latest_dir}") if f.endswith(".csv")]
                if candidates:
                    csv_path = f"./temp/{latest_dir}/" + sorted(candidates)[-1]

        if not csv_path or not os.path.exists(csv_path):
            return jsonify({"error": "CSV path not provided or file not found."}), 400

        dependent_variable = request.form.get("dependent_variable", "RSEI")
        independent_variables = request.form.get("independent_variables")
        independent_variables = json.loads(independent_variables) if isinstance(independent_variables, str) else independent_variables
        k_neighbors = int(request.form.get("k_neighbors", 8))
        auto_select = request.form.get("auto_select_best_model", "true").lower() == "true"

        config = {
            "temp_dir": "./temp",
            "dependent_variable": dependent_variable,
            "independent_variables": independent_variables,
            "k_neighbors": k_neighbors
        }

        analyzer = FlexibleSRAnalysis(config)
        result = analyzer.run(csv_path, auto_select_best_model=auto_select)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/results/visualize", methods=["GET"]) #可视化结果
def visualize_results():
    try:
        model = request.args.get("model")
        result_file = f"./temp/sr_{time.strftime('%Y-%m-%d')}/{model.lower()}_results.shp"
        if not os.path.exists(result_file):
            return jsonify({"error": "Shapefile not found"}), 404

        gdf = gpd.read_file(result_file)
        features = []
        for _, row in gdf.iterrows():
            feat = {
                "type": "Feature",
                "geometry": mapping(row.geometry),
                "properties": {k: row[k] for k in gdf.columns if k != "geometry"}
            }
            features.append(feat)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        return jsonify(geojson)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download-csv", methods=["GET"]) #下载CSV文件
def download_csv():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "CSV file not found"}), 404
    return send_file(path, as_attachment=True)

@app.route("/api/read-csv", methods=["GET"]) #将csv文件内容读取为JSON格式
def read_csv():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "CSV file not found"}), 404
    try:
        import pandas as pd
        df = pd.read_csv(path)
        return jsonify({
            "columns": list(df.columns),
            "rows": df.head(100).to_dict(orient="records")  # 限制前100行
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload/region", methods=["POST"]) #上传区域文件
def upload_region():
    try:
        region_file = request.files.get("region")
        if not region_file:
            return jsonify({"error": "Missing region file"}), 400

        filename = secure_filename(region_file.filename)
        region_path = os.path.join(UPLOAD_FOLDER, filename)
        region_file.save(region_path)

        return jsonify({"message": "Region uploaded", "path": region_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "Service is running."})

@app.route("/")
def index():
    return "IM WebGIS API is running."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7891, debug=True)



from flask import Flask, request, send_file, jsonify, Response
import os
import uuid
import json
import zipfile
import shutil
import pandas as pd
import geopandas as gpd
from A import SRService
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

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
    """Preprocess raster data and generate CSV"""
    data = request.get_json()
    year = data.get('year')
    region = data.get('region')

    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    try:
        year = int(year)
        if year < 1900 or year > datetime.now().year:
            return jsonify({"status": "error", "message": "Invalid year"}), 400

        service = SRService(year, region)
        if not service.process_all_rasters():
            return jsonify({"status": "error", "message": "Raster processing failed"}), 500
        if not service.create_csv():
            return jsonify({"status": "error", "message": "CSV creation failed"}), 500

        return jsonify({
            "status": "success",
            "message": "Preprocessing completed successfully",
            "csv_path": service.csv_out
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
    """Perform spatial regression analysis"""
    data = request.get_json()
    year = data.get('year')
    region = data.get('region')

    if not year or not region:
        return jsonify({"status": "error", "message": "Missing year or region"}), 400

    try:
        year = int(year)
        service = SRService(year, region)

        # Load CSV
        if not os.path.exists(service.csv_out):
            return jsonify({"status": "error", "message": "CSV file not found. Run preprocessing first."}), 404
        df = pd.read_csv(service.csv_out)

        # Run analysis pipeline
        df = service.prepare_data(df)
        w = service.create_spatial_weights(df)
        y = df['rsei'].values.reshape(-1, 1)
        X = df[['lucc_numeric', 'temperature', 'rainfall', 'fvc']].values
        models = service.run_regression_models(X, y, w)
        service.save_results(df, models)
        best_model, best_stats = service.select_best_model(models['OLS'], models['SLM'], models['SEM'])

        output_files = [
                           os.path.join(service.work_dir, f"{model.lower()}_results.shp")
                           for model in ['OLS', 'SLM', 'SEM']
                       ] + [os.path.join(service.work_dir, "best_model_selection.txt")]

        return jsonify({
            "status": "success",
            "message": "Spatial regression completed successfully",
            "best_model": {
                "name": best_stats['name'],
                "r2": best_stats['r2']
            },
            "output_files": output_files
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


@app.route('/api/read-csv', methods=['GET'])
def read_csv():
    """Convert CSV to JSON for frontend display"""
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
        data = df.to_dict(orient='records')

        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/upload/region', methods=['POST'])
def upload_region():
    """Upload a shapefile for a new study region"""
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

        # Validate shapefile
        if not validate_shapefile(shp_path):
            shutil.rmtree(region_dir)  # Clean up invalid files
            return jsonify({"status": "error", "message": "Invalid shapefile"}), 400

        # Dynamically update SRService.city_shapes
        SRService.city_shapes[region_code] = shp_path

        return jsonify({
            "status": "success",
            "message": "Shapefile uploaded successfully",
            "region_code": region_code
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7891)
import os
import requests
import json

from typing import Dict
import time
import geopandas as gpd
from shapely.geometry import Point
import tempfile
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin

# 测试配置
BASE_URL = "http://localhost:7891"
UPLOAD_FOLDER = "./test_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 生态要素变量配置 - 更新为只包含RSEI和指定的自变量


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

# 测试辅助函数
def print_response(response, title):
    print(f"\n=== {title} ===")
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print("Response Text:", response.text)

# def create_test_shapefile():
#     """创建一个测试用的 shapefile"""
#     temp_dir = tempfile.mkdtemp()
#     path = os.path.join(temp_dir, "test_region.shp")
#
#     # 创建一个简单的 GeoDataFrame (南昌市区域)
#     geometry = [Point(116.4, 28.7).buffer(0.1)]
#     gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")
#     gdf.to_file(path)
#
#     return path

# def create_sample_tif_files():
#     """创建样本TIFF文件用于测试"""
#     for var, info in ECO_VARIABLES.items():
#         if not os.path.exists(info["path"]):
#             os.makedirs(os.path.dirname(info["path"]), exist_ok=True)
#
#             # 创建简单的测试栅格数据
#             rows, cols = 100, 100
#             if info["type"] == "continuous":
#                 if var == "temperature":
#                     data = np.random.uniform(10, 30, size=(rows, cols))  # 温度范围10-30
#                 elif var == "rainfall":
#                     data = np.random.uniform(0, 500, size=(rows, cols))  # 降雨量范围0-500
#                 elif var == "fvc":
#                     data = np.random.uniform(0, 1, size=(rows, cols))    # FVC范围0-1
#                 else:  # RSEI
#                     data = np.random.uniform(0, 1, size=(rows, cols))    # RSEI范围0-1
#             else:  # categorical (lucc)
#                 data = np.random.randint(1, 6, size=(rows, cols))       # 土地利用分类1-5
#
#             # 写入TIFF文件
#             transform = from_origin(116.0, 29.0, 0.01, 0.01)
#             with rasterio.open(
#                     info["path"], 'w',
#                     driver='GTiff',
#                     height=rows,
#                     width=cols,
#                     count=1,
#                     dtype=data.dtype,
#                     crs='EPSG:4326',
#                     transform=transform
#             ) as dst:
#                 dst.write(data, 1)

def test_status():
    """测试服务状态接口"""
    url = f"{BASE_URL}/api/status"
    response = requests.get(url)
    print_response(response, "服务状态测试")
    assert response.status_code == 200
    assert response.json()["status"] == "Service is running."

def test_upload_region(city_code="NC"):
    """测试上传区域文件接口"""
    url = f"{BASE_URL}/api/upload/region"

    # 创建一个测试 shapefile
    shapefile_path = "D:/Google/city/NC.shp"

    # 上传文件
    with open(shapefile_path, 'rb') as f:
        files = {'region': (os.path.basename(shapefile_path), f)}
        response = requests.post(url, files=files)

    print_response(response, "上传区域文件测试")
    assert response.status_code == 200
    assert "path" in response.json()

    return response.json()["path"]

def test_preprocess(year = "2020", standardize=True):
    """测试预处理接口 - 更新为使用RSEI和相关自变量"""
    url = f"{BASE_URL}/api/preprocess"

    #生成路径
    rsei = "D:/Google/RSEI_full/RSEI_"+ year + ".tif"
    temperature = "D:/Google/temperture/tpt/tpt_" + year + ".tif"
    rainfall = "D:/Google/rainfall/RF/"+ year + ".tif"
    lucc = "D:/Google/GLC_FCS30/merged/poyang_" + year + ".tif"
    fvc = "D:/Google/FVC/FVC_"+ year + ".tif"
    ECO_VARIABLES = {
        "RSEI": {"path": rsei, "type": "continuous", "role": "dependent"},
        "temperature": {"path": temperature, "type": "continuous", "role": "independent"},
        "rainfall": {"path": rainfall, "type": "continuous", "role": "independent"},
        "lucc": {"path": lucc, "type": "categorical", "role": "independent"},
        "fvc": {"path": fvc, "type": "continuous", "role": "independent"}
    }

    # 准备变量映射 - 只包含RSEI和指定的自变量
    variables = {
         #"RSEI": ECO_VARIABLES["RSEI"]["path"],
        "temperature": ECO_VARIABLES["temperature"]["path"],
        "rainfall": ECO_VARIABLES["rainfall"]["path"],
        "lucc": ECO_VARIABLES["lucc"]["path"],
        "fvc": ECO_VARIABLES["fvc"]["path"]
    }

    # 测试通过城市代码
    data = {
        "year": "2020",
        "variables": json.dumps(variables),
        "region_code": "NC",  # 南昌市
        "standardize": "true"
    }

    response = requests.post(url, data=data)
    print_response(response, "预处理测试 - 使用RSEI和生态变量")
    assert response.status_code == 200
    assert "csv_path" in response.json()

    return response.json()["csv_path"]

def test_read_csv():
    """测试读取CSV文件接口"""
    # 先运行预处理获取CSV文件路径
    csv_path = test_preprocess()

    url = f"{BASE_URL}/api/read-csv"
    params = {"path": csv_path}
    response = requests.get(url, params=params)

    print_response(response, "读取CSV文件测试")
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "rows" in data
    assert "RSEI" in data["columns"]
    assert "temperature" in data["columns"]
    assert "rainfall" in data["columns"]
    assert "lucc" in data["columns"]
    assert "fvc" in data["columns"]

def test_spatial_regression():
    """测试空间回归分析接口 - 更新为使用RSEI作为因变量"""
    # 先运行预处理获取CSV文件路径
    csv_path = test_preprocess()

    url = f"{BASE_URL}/api/spatial-regression"

    # 指定自变量 - 从温度、降水、lucc、fvc中选择
    independent_vars = ["temperature", "rainfall", "lucc", "fvc"]

    data = {
        "csv_path": csv_path,
        "dependent_variable": "RSEI",
        "independent_variables": json.dumps(independent_vars),
        "k_neighbors": "8",
        "auto_select_best_model": "true"
    }
    response = requests.post(url, data=data)

    print_response(response, "空间回归分析测试 - RSEI模型")
    assert response.status_code == 200
    result = response.json()
    assert "best_model" in result
    assert result["best_model"] in ["OLS", "SLM", "SEM"]
    assert "r2" in result
    assert "sig_vars" in result

def test_shapefile_fields():
    """测试获取shapefile字段接口"""
    # 先运行空间回归分析生成结果文件
    test_spatial_regression()

    url = f"{BASE_URL}/api/shapefile-fields"

    # 测试获取最佳模型字段
    params = {"model": "best"}
    response = requests.get(url, params=params)
    print_response(response, "获取shapefile字段测试 - 最佳模型")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "fields" in data
    assert "RSEI" in data["fields"]
    assert any(f.endswith("_pred") for f in data["fields"])  # 检查预测字段

def test_visualize_results():
    """测试可视化结果接口"""
    # 先运行空间回归分析生成结果文件
    test_spatial_regression()

    url = f"{BASE_URL}/api/results/visualize"

    # 测试获取最佳模型的可视化结果
    params = {"model": "best"}
    response = requests.get(url, params=params)

    print_response(response, "可视化结果测试")
    assert response.status_code == 200
    data = response.json()
    assert "type" in data
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0
    # 检查特征属性中是否包含RSEI相关字段
    assert "RSEI" in data["features"][0]["properties"]

def run_all_tests():
    """运行所有测试"""
    print("开始测试Flask API...")

    try:
        test_status() #测试服务状态 get
        test_upload_region() #测试上传区域文件 get
        test_preprocess() #测试预处理接口
        # test_read_csv() #
        # test_spatial_regression()
        # test_shapefile_fields()
        # test_visualize_results()

        print("\n所有测试完成！")
    except Exception as e:
        print(f"\n测试过程中出错: {str(e)}")

if __name__ == "__main__":
    run_all_tests()

























#
# import os
# import requests
# import json
# import time
# import geopandas as gpd
# from shapely.geometry import Point
# import tempfile
#
# # 测试配置
# BASE_URL = "http://localhost:7891"
# UPLOAD_FOLDER = "./test_uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#
#
# # 测试辅助函数
# def print_response(response, title):
#     print(f"\n=== {title} ===")
#     print(f"Status Code: {response.status_code}")
#     try:
#         print("Response JSON:", json.dumps(response.json(), indent=2, ensure_ascii=False))
#     except:
#         print("Response Text:", response.text)
#
#
# def create_test_shapefile():
#     """创建一个测试用的 shapefile"""
#     temp_dir = tempfile.mkdtemp()
#     path = os.path.join(temp_dir, "test_region.shp")
#
#     # 创建一个简单的 GeoDataFrame
#     geometry = [Point(116.4, 28.7).buffer(0.1)]  # 南昌附近的点
#     gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")
#     gdf.to_file(path)
#
#     return path
#
#
# def test_status():
#     """测试服务状态接口"""
#     url = f"{BASE_URL}/api/status"
#     response = requests.get(url)
#     print_response(response, "服务状态测试")
#     assert response.status_code == 200
#     assert response.json()["status"] == "Service is running."
# #
# #
# # def test_upload_region():
# #     """测试上传区域文件接口"""
# #     url = f"{BASE_URL}/api/upload/region"
# #
# #     # 创建一个测试 shapefile
# #     shapefile_path = create_test_shapefile()
# #
# #     # 上传文件
# #     with open(shapefile_path, 'rb') as f:
# #         files = {'region': (os.path.basename(shapefile_path), f}
# #         response = requests.post(url, files=files)
# #
# #                  print_response(response, "上传区域文件测试")
# #         assert response.status_code == 200
# #         assert "path" in response.json()
# #
# #     return response.json()["path"]
# #
# def test_upload_region():
#     """Test the upload region endpoint."""
#     files = {"region": open("D:/Google/GLC_FCS30/南昌市_市.geojson", "rb")}
#     response = requests.post(f"{BASE_URL}/api/upload/region", files=files)
#     print("Upload region response:", response.json())
#
# def test_preprocess():
#     """测试预处理接口"""
#     url = f"{BASE_URL}/api/preprocess"
#
#     # 测试三种区域选择方式
#
#     # 1. 通过城市代码
#     data = {
#         "year": "2020",
#         "variables": json.dumps(["NDVI", "LST"]),
#         "region_code": "NC"  # 南昌市
#     }
#     response = requests.post(url, data=data)
#     print_response(response, "预处理测试 - 通过城市代码")
#     assert response.status_code == 200
#     assert "csv_path" in response.json()
#
#     # 2. 通过坐标点
#     data = {
#         "year": "2020",
#         "variables": json.dumps(["NDVI", "LST"]),
#         "lon": "116.4",
#         "lat": "28.7"
#     }
#     response = requests.post(url, data=data)
#     print_response(response, "预处理测试 - 通过坐标点")
#     assert response.status_code == 200
#     assert "csv_path" in response.json()
#
#     # 3. 通过上传的区域文件
#     region_path = test_upload_region()
#     data = {
#         "year": "2020",
#         "variables": json.dumps(["NDVI", "LST"]),
#         "target_res": "0.00449,0.00449",
#         "standardize": "true"
#     }
#     with open(region_path, 'rb') as f:
#         files = {'region': (os.path.basename(region_path), f)}
#         response = requests.post(url, data=data, files=files)
#
#     print_response(response, "预处理测试 - 通过上传文件")
#     assert response.status_code == 200
#     assert "csv_path" in response.json()
#
#     return response.json()["csv_path"]
#
#
# def test_read_csv():
#     """测试读取CSV文件接口"""
#     # 先运行预处理获取CSV文件路径
#     csv_path = test_preprocess()
#
#     url = f"{BASE_URL}/api/read-csv"
#     params = {"path": csv_path}
#     response = requests.get(url, params=params)
#
#     print_response(response, "读取CSV文件测试")
#     assert response.status_code == 200
#     data = response.json()
#     assert "columns" in data
#     assert "rows" in data
#     assert len(data["columns"]) > 0
#     assert len(data["rows"]) > 0
#
#
# def test_download_csv():
#     """测试下载CSV文件接口"""
#     # 先运行预处理获取CSV文件路径
#     csv_path = test_preprocess()
#
#     url = f"{BASE_URL}/api/download-csv"
#     params = {"path": csv_path}
#     response = requests.get(url, params=params, stream=True)
#
#     print(f"\n=== 下载CSV文件测试 ===")
#     print(f"Status Code: {response.status_code}")
#     print(f"Content-Type: {response.headers['Content-Type']}")
#     assert response.status_code == 200
#     assert "text/csv" in response.headers['Content-Type']
#
#     # 保存下载的文件
#     download_path = os.path.join(UPLOAD_FOLDER, "downloaded_data.csv")
#     with open(download_path, 'wb') as f:
#         for chunk in response.iter_content(chunk_size=8192):
#             f.write(chunk)
#
#     print(f"文件已下载到: {download_path}")
#     assert os.path.exists(download_path)
#
#
# def test_spatial_regression():
#     """测试空间回归分析接口"""
#     # 先运行预处理获取CSV文件路径
#     csv_path = test_preprocess()
#
#     url = f"{BASE_URL}/api/spatial-regression"
#     data = {
#         "csv_path": csv_path,
#         "dependent_variable": "RSEI",
#         "independent_variables": json.dumps(["NDVI", "LST"]),
#         "k_neighbors": "8",
#         "auto_select_best_model": "true"
#     }
#     response = requests.post(url, data=data)
#
#     print_response(response, "空间回归分析测试")
#     assert response.status_code == 200
#     result = response.json()
#     assert "best_model" in result
#     assert "results" in result
#     assert "shapefile_path" in result
#
#
# def test_shapefile_fields():
#     """测试获取shapefile字段接口"""
#     # 先运行空间回归分析生成结果文件
#     test_spatial_regression()
#
#     url = f"{BASE_URL}/api/shapefile-fields"
#
#     # 测试获取最佳模型字段
#     params = {"model": "best"}
#     response = requests.get(url, params=params)
#     print_response(response, "获取shapefile字段测试 - 最佳模型")
#     assert response.status_code == 200
#     data = response.json()
#     assert "model" in data
#     assert "fields" in data
#     assert len(data["fields"]) > 0
#
#     # 测试获取特定模型字段 (假设SLM模型存在)
#     params = {"model": "slm"}
#     response = requests.get(url, params=params)
#     print_response(response, "获取shapefile字段测试 - SLM模型")
#     assert response.status_code == 200
#     data = response.json()
#     assert data["model"] == "SLM"
#     assert "fields" in data
#
#
# def test_visualize_results():
#     """测试可视化结果接口"""
#     # 先运行空间回归分析生成结果文件
#     test_spatial_regression()
#
#     url = f"{BASE_URL}/api/results/visualize"
#
#     # 测试获取最佳模型的可视化结果
#     params = {"model": "slm"}  # 假设SLM模型存在
#     response = requests.get(url, params=params)
#
#     print_response(response, "可视化结果测试")
#     assert response.status_code == 200
#     data = response.json()
#     assert "type" in data
#     assert data["type"] == "FeatureCollection"
#     assert "features" in data
#     assert len(data["features"]) > 0
#
#
# def test_download_shapefile():
#     """测试下载shapefile接口"""
#     # 先运行空间回归分析生成结果文件
#     test_spatial_regression()
#
#     url = f"{BASE_URL}/api/download-shapefile"
#
#     # 测试下载最佳模型
#     params = {"model": "best"}
#     response = requests.get(url, params=params, stream=True)
#
#     print(f"\n=== 下载shapefile测试 - 最佳模型 ===")
#     print(f"Status Code: {response.status_code}")
#     print(f"Content-Type: {response.headers['Content-Type']}")
#     assert response.status_code == 200
#     assert "application/octet-stream" in response.headers['Content-Type']
#
#     # 保存下载的文件
#     download_path = os.path.join(UPLOAD_FOLDER, "downloaded_best_model.shp")
#     with open(download_path, 'wb') as f:
#         for chunk in response.iter_content(chunk_size=8192):
#             f.write(chunk)
#
#     print(f"文件已下载到: {download_path}")
#     assert os.path.exists(download_path)
#
#     # 测试下载特定模型 (假设SLM模型存在)
#     params = {"model": "slm"}
#     response = requests.get(url, params=params, stream=True)
#
#     print(f"\n=== 下载shapefile测试 - SLM模型 ===")
#     print(f"Status Code: {response.status_code}")
#     print(f"Content-Type: {response.headers['Content-Type']}")
#     assert response.status_code == 200
#
#     download_path = os.path.join(UPLOAD_FOLDER, "downloaded_slm_model.shp")
#     with open(download_path, 'wb') as f:
#         for chunk in response.iter_content(chunk_size=8192):
#             f.write(chunk)
#
#     print(f"文件已下载到: {download_path}")
#     assert os.path.exists(download_path)
#
#
# def run_all_tests():
#     """运行所有测试"""
#     print("开始测试Flask API...")
#
#     try:
#         test_status()
#         test_upload_region()
#         test_preprocess()
#         test_read_csv()
#         test_download_csv()
#         test_spatial_regression()
#         test_shapefile_fields()
#         test_visualize_results()
#         test_download_shapefile()
#
#         print("\n所有测试完成！")
#     except Exception as e:
#         print(f"\n测试过程中出错: {str(e)}")
#
#
# if __name__ == "__main__":
#     run_all_tests()
#






# import requests
# import json
#
# BASE_URL = "http://127.0.0.1:7891"  # Update this if the API is hosted elsewhere
#
# def test_status():
#     """Test the status endpoint."""
#     response = requests.get(f"{BASE_URL}/api/status")
#     print("Status endpoint response:", response.json())
#
# def test_preprocess():
#     """Test the preprocess endpoint."""
#     # Mock data for testing
#     data = {
#         "year": 2000,
#         "variables": json.dumps(["variable1", "variable2"]),
#         "region_code": "NC",
#         "target_res": "0.01,0.01",
#         "standardize": "true"
#     }
#     response = requests.post(f"{BASE_URL}/api/preprocess", data=data)
#     print("Preprocess endpoint response:", response.json())
#
# def test_download_shapefile():
#     """Test the download shapefile endpoint."""
#     params = {"model": "best"}
#     response = requests.get(f"{BASE_URL}/api/download-shapefile", params=params)
#     if response.status_code == 200:
#         with open("downloaded_shapefile.shp", "wb") as f:
#             f.write(response.content)
#         print("Shapefile downloaded successfully.")
#     else:
#         print("Download shapefile error:", response.json())
#
# def test_shapefile_fields():
#     """Test the shapefile fields endpoint."""
#     params = {"model": "best"}
#     response = requests.get(f"{BASE_URL}/api/shapefile-fields", params=params)
#     print("Shapefile fields response:", response.json())
#
# def test_spatial_regression():
#     """Test the spatial regression endpoint."""
#     # Mock data for testing
#     data = {
#         "csv_path": "./temp/some_file.csv",
#         "dependent_variable": "RSEI",
#         "independent_variables": json.dumps(["var1", "var2", "var3"]),
#         "k_neighbors": 8,
#         "auto_select_best_model": "true"
#     }
#     response = requests.post(f"{BASE_URL}/api/spatial-regression", data=data)
#     print("Spatial regression response:", response.json())
#
# def test_visualize_results():
#     """Test the visualize results endpoint."""
#     params = {"model": "slm"}
#     response = requests.get(f"{BASE_URL}/api/results/visualize", params=params)
#     print("Visualize results response:", response.json())
#
# def test_download_csv():
#     """Test the download CSV endpoint."""
#     params = {"path": "./temp/some_file.csv"}
#     response = requests.get(f"{BASE_URL}/api/download-csv", params=params)
#     if response.status_code == 200:
#         with open("downloaded_file.csv", "wb") as f:
#             f.write(response.content)
#         print("CSV downloaded successfully.")
#     else:
#         print("Download CSV error:", response.json())
#
# def test_read_csv():
#     """Test the read CSV endpoint."""
#     params = {"path": "./temp/some_file.csv"}
#     response = requests.get(f"{BASE_URL}/api/read-csv", params=params)
#     print("Read CSV response:", response.json())
#
# def test_upload_region():
#     """Test the upload region endpoint."""
#     files = {"region": open("D:/Google/GLC_FCS30/南昌市_市.geojson", "rb")}
#     response = requests.post(f"{BASE_URL}/api/upload/region", files=files)
#     print("Upload region response:", response.json())
#
# # Call the function to test
# test_preprocess()
#
# if __name__ == "__main__":
#     print("Testing API endpoints...")
#     test_status()
#     print("11111111111111")
#     test_preprocess()
#     print("22222222222222")
#     test_download_shapefile()
#     print("33333333333333")
#     test_shapefile_fields()
#     print("44444444444444")
#     test_spatial_regression()
#     print("55555555555555")
#     test_visualize_results()
#     print("66666666666666")
#     test_download_csv()
#     print("77777777777777")
#     test_read_csv()
#     print("888888888888888")
#     test_upload_region()
#     print("Testing complete.")
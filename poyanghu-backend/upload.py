import requests
import os

# ======================
# GeoServer参数
# ======================
GEOSERVER_URL = "http://localhost:8081/geoserver"
USERNAME = "admin"
PASSWORD = "geoserver"

WORKSPACE = "totaldata"
STORE_NAME = "rainfall"

# 本地文件
FILE_PATH = r"F:\pylake\totaldata\rainfall\2001_precip.tif"

# ======================
# 上传 GeoTIFF
# ======================

url = f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/coveragestores/{STORE_NAME}/file.geotiff"

headers = {
    "Content-type": "image/tiff"
}

with open(FILE_PATH, "rb") as f:
    response = requests.put(
        url,
        data=f,
        headers=headers,
        auth=(USERNAME, PASSWORD)
    )

print(response.status_code)
print(response.text)
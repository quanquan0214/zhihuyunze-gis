import arcpy
from arcpy import env
from arcpy.sa import *

env.workspace = r"D:/Google/temperture/data"
output_sd_path = r"D:/Google/temperture/service_definition.sd"

# 1. 影像列表，排序好（确保顺序正确）
rasters = sorted(arcpy.ListRasters("temp_*.tif"))

# 2. 创建 mosaic dataset 或 Raster Catalog（便于管理288张影像）
gdb = r"D:/Google/temperture/DB/temperature.gdb"
mosaic_name = "temperature_mosaic"

if not arcpy.Exists(gdb):
    arcpy.CreateFileGDB_management(r"D:/Google/temperture/data", "your.gdb")

if arcpy.Exists(f"{gdb}\\{mosaic_name}"):
    arcpy.Delete_management(f"{gdb}\\{mosaic_name}")

arcpy.CreateMosaicDataset_management(gdb, mosaic_name, spatial_reference=arcpy.SpatialReference(4326))

# 添加栅格数据
for raster in rasters:
    arcpy.AddRastersToMosaicDataset_management(f"{gdb}\\{mosaic_name}", "Raster Dataset", raster)

# 3. 设置渲染色带：蓝→橙→红
# 创建色带渐变对象
# 这里示例使用分段渲染 (UniqueValueRenderer 或 ClassBreaksRenderer) 模拟蓝-橙-红渐变

mosaic_raster = arcpy.Raster(f"{gdb}\\{mosaic_name}")

# 计算全局 min/max
min_max_result = arcpy.GetRasterProperties_management(mosaic_raster, "MINIMUM")
vmin = float(min_max_result.getOutput(0))
max_max_result = arcpy.GetRasterProperties_management(mosaic_raster, "MAXIMUM")
vmax = float(max_max_result.getOutput(0))

# 4. 设置色带
# 这里用 ClassBreaksRenderer 作为示例

from arcpy.mapping import Layer

# 创建临时图层，应用色带
layer = arcpy.MakeRasterLayer_management(mosaic_raster, "temp_layer")

# 创建颜色断点，蓝-橙-红
breaks = [vmin, (vmin+vmax)/2, vmax]
colors = [
    (0, 0, 255, 255),     # 蓝
    (255, 165, 0, 255),   # 橙
    (255, 0, 0, 255)      # 红
]

# ArcPy中色彩映射具体写法复杂，通常通过ArcGIS Pro UI生成渲染图层文件.lyrx，再用脚本应用

# 5. 导出服务定义文件
# 先创建地图文档（ArcGIS Pro叫Project Map），加载栅格图层，并设置好渲染，
# 然后调用 arcpy.sharing.CreateSharingDraft 和 arcpy.sharing.StageService 来打包成.sd文件。

# 这一步需要ArcGIS Pro环境支持，示例：
aprx = arcpy.mp.ArcGISProject("CURRENT")  # 或指定项目路径
mapx = aprx.listMaps()[0]
layerx = mapx.listLayers("temp_layer")[0]

sharing_draft = arcpy.sharing.CreateSharingDraft("STANDALONE_SERVER", "SERVICE", "TemperatureService", mapx)
sharing_draft.exportToSDDraft(r"D:/Google/temperture/TemperatureService.sddraft")
arcpy.sharing.StageService(r"D:/Google/temperture/TemperatureService.sddraft", output_sd_path)

print(f".sd 文件已生成：{output_sd_path}")

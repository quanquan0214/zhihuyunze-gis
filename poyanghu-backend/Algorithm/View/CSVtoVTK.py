# # 将CSV文件转化成vtk文件（含海拔信息，生成结果可疑，与平面结果不一致）
# import os
# import pandas as pd
# import vtk
# # from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
#
# def csv_to_vtk(csv_file, vtk_file):
#     data = pd.read_csv(csv_file)
#     points = vtk.vtkPoints()
#     for index, row in data.iterrows():
#         points.InsertNextPoint(row['lon'], row['lat'],row['ht_water_surf'])
#     polydata = vtk.vtkPolyData()
#     polydata.SetPoints(points)
#     vertices = vtk.vtkCellArray()
#     for i in range(points.GetNumberOfPoints()):
#         vertex = vtk.vtkVertex()
#         vertex.GetPointIds().SetId(0, i)
#         vertices.InsertNextCell(vertex)
#     polydata.SetVerts(vertices)
#     writer = vtk.vtkPolyDataWriter()
#     writer.SetFileName(vtk_file)
#     writer.SetInputData(polydata)
#     writer.Write()
#
#
# csv_folder = 'D:/Google/H5/Processed/OutputCSV/'  # 或者是 D:/Google/H5/Processed/FilteredCSV/
# vtk_folder = 'D:/Google/H5/Processed/vtk/'
#
# for filename in os.listdir(csv_folder):
#     if filename.endswith('.csv'):
#         csv_path = os.path.join(csv_folder, filename)
#         vtk_path = os.path.join(vtk_folder, filename.replace('.csv', '.vtk'))
#         csv_to_vtk(csv_path, vtk_path)
#         print('生成vtk文件:', vtk_path)
#     else:
#         print('跳过非csv文件:', filename)


# 将CSV文件转化成vtk文件(不含海拔信息，生成结果直观)
import os
import pandas as pd
import vtk
# from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy

def csv_to_vtk(csv_file, vtk_file):
    data = pd.read_csv(csv_file)
    points = vtk.vtkPoints()
    for index, row in data.iterrows():
        points.InsertNextPoint(row['lon'], row['lat'],0)
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    vertices = vtk.vtkCellArray()
    for i in range(points.GetNumberOfPoints()):
        vertex = vtk.vtkVertex()
        vertex.GetPointIds().SetId(0, i)
        vertices.InsertNextCell(vertex)
    polydata.SetVerts(vertices)
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(vtk_file)
    writer.SetInputData(polydata)
    writer.Write()

csv_folder = 'D:/Google/H5/Processed/OutputCSV/'  # 或者是 D:/Google/H5/Processed/FilteredCSV/
vtk_folder = 'D:/Google/H5/Processed/plain_vtk/'
for filename in os.listdir(csv_folder):
    if filename.endswith('.csv'):
        csv_path = os.path.join(csv_folder, filename)
        vtk_path = os.path.join(vtk_folder, filename.replace('.csv', '.vtk'))
        csv_to_vtk(csv_path, vtk_path)
        print('生成vtk文件:', vtk_path)
    else:
        print('跳过非csv文件:', filename)

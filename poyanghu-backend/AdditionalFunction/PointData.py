from flask import Flask, request, jsonify
import pandas as pd
from scipy.spatial import cKDTree
import numpy as np


class PointDataService:
    def __init__(self):
        self.data_cache = {}
        self.spatial_index = None

    def get_point_data(self, lat, lng, radius=500):
        """获取指定坐标附近的历史数据"""

        # 使用空间索引查找附近数据点
        if self.spatial_index is None:
            self._build_spatial_index()

        # 查找半径范围内的数据点
        distances, indices = self.spatial_index.query(
            [lat, lng],
            k=10,
            distance_upper_bound=radius / 111000  # 转换为度
        )

        # 获取数据并按时间排序
        nearby_data = []
        for idx in indices:
            if idx < len(self.all_data):
                nearby_data.append(self.all_data.iloc[idx])

        # 按时间聚合数据
        df = pd.DataFrame(nearby_data)
        return self._aggregate_temporal_data(df)

    def _aggregate_temporal_data(self, df):
        """按时间期间聚合数据"""
        return df.groupby(['year', 'period']).agg({
            'water_quality': 'mean',
            'depth': 'mean',
            'vegetation_cover': 'mean'
        }).reset_index()
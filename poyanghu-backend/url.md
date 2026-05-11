# API接口测试示例

## 1. 基础接口

### 1.1 问候接口
- **URL**: `/hello`
- **方法**: GET
- **请求参数**: 无
- **示例响应**:
  ```
  Hello, World!
  ```

### 1.2 欢迎接口
- **URL**: `/`
- **方法**: GET
- **请求参数**: 无
- **示例响应**:
  ```
  Welcome to Web_pylake.
  ```

## 2. 预测接口

### 2.1 环境预测
- **URL**: `/predict`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "lat": 29.0833,
    "lon": 116.2667,
    "year": 2022
  }
  ```
- **示例响应**:
  ```json
  {
    "pixel_value": 0.65,
    "coordinates": {"lat": 29.0833, "lon": 116.2667},
    "time_series": {
      "values": [0.58, 0.61, 0.63, 0.65]
    },
    "anomalies": [],
    "trend_analysis": {
      "trend_type": "increasing",
      "r_squared": 0.98,
      "trend_strength": "strong",
      "predictions": []
    },
    "ml_prediction": {
      "predictions": [
        {"period": "2023", "predicted_value": 0.67},
        {"period": "2024", "predicted_value": 0.69},
        {"period": "2025", "predicted_value": 0.71}
      ]
    }
  }
  ```

## 3. 区域对比接口

### 3.1 基于GeoJSON的区域对比
- **URL**: `/api/RegionCompare/geojson/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "city_codes": ["NC", "JDZ", "SR"]
  }
  ```
- **示例响应**:
  ```json
  {
    "分析摘要": {
      "分析区域数量": 3,
      "区域面积比较": {
        "最大区域": "10000.00 km²",
        "最小区域": "5000.00 km²"
      },
      "归一化指标拟合": {
        "斜率(k)": "0.001234",
        "截距(b)": "0.500000",
        "拟合方程": "y = 0.001234x + 0.500000"
      },
      "变化趋势": {
        "平均变化百分比": "2.50%",
        "最大增长区域": "南昌市 (5.20%)",
        "最大下降区域": "景德镇市 (-1.80%)"
      }
    },
    "图表数据": {
      "years": [2000, 2001, 2002],
      "regions": ["南昌市", "景德镇市", "上饶市"],
      "values": [[0.5, 0.51, 0.52], [0.55, 0.54, 0.53], [0.48, 0.49, 0.5]]
    }
  }
  ```

### 3.2 基于点位组的区域对比
- **URL**: `/api/RegionCompare/point/`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "point_groups": [
      {
        "id": "region1",
        "name": "区域1",
        "points": [[116.0, 29.0], [116.1, 29.0], [116.1, 29.1], [116.0, 29.0]]
      },
      {
        "id": "region2",
        "name": "区域2",
        "points": [[116.2, 29.0], [116.3, 29.0], [116.3, 29.1], [116.2, 29.0]]
      }
    ]
  }
  ```
- **示例响应**:
  ```json
  {
    "分析摘要": {
      "分析区域数量": 2,
      "区域面积比较": {
        "最大区域": "100.00 km²",
        "最小区域": "95.00 km²"
      },
      "归一化指标拟合": {
        "斜率(k)": "0.000876",
        "截距(b)": "0.450000",
        "拟合方程": "y = 0.000876x + 0.450000"
      },
      "变化趋势": {
        "平均变化百分比": "1.80%",
        "最大增长区域": "区域1 (2.50%)",
        "最大下降区域": "区域2 (-0.50%)"
      }
    },
    "图表数据": {
      "years": [2000, 2001, 2002],
      "regions": ["区域1", "区域2"],
      "values": [[0.45, 0.46, 0.47], [0.48, 0.47, 0.47]]
    }
  }
  ```

## 4. 土地覆盖分析接口

### 4.1 获取时间序列数据
- **URL**: `/api/timeseries`
- **方法**: GET
- **请求参数**:
  - `region`: GeoJSON字符串或多边形坐标
  - `years`: 年份范围，如"2000-2022"或"2020"
- **示例请求**:
  ```
  /api/timeseries?region={"type":"Polygon","coordinates":[[[116,29],[116.1,29],[116.1,29.1],[116,29.1],[116,29]]]}&years=2000-2005
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "data": {
      "relative_changes": {
        "2000": {"type1": 30, "type2": 70},
        "2005": {"type1": 25, "type2": 75}
      },
      "annual_change_rates": {
        "type1": -1.0,
        "type2": 1.0
      }
    }
  }
  ```

### 4.2 多区域对比分析
- **URL**: `/api/compare`
- **方法**: GET
- **请求参数**:
  - `regions`: 区域列表JSON字符串
  - `metric`: 对比指标(area, change, anomaly)
- **示例请求**:
  ```
  /api/compare?regions=[{"name":"区域1","geometry":{"type":"Polygon","coordinates":[[[116,29],[116.1,29],[116.1,29.1],[116,29.1],[116,29]]]}},{"name":"区域2","geometry":{"type":"Polygon","coordinates":[[[116.2,29],[116.3,29],[116.3,29.1],[116.2,29.1],[116.2,29]]]}}]&metric=area
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "data": {
      "regions": {
        "区域1": {
          "raw_data": {"2000": {"type1": 100, "type2": 200}},
          "total_area": 300,
          "dominant_types": ["type2"]
        },
        "区域2": {
          "raw_data": {"2000": {"type1": 150, "type2": 150}},
          "total_area": 300,
          "dominant_types": ["type1", "type2"]
        }
      },
      "comparison_stats": {
        "total_area": 600,
        "avg_area": 300
      },
      "metric": "area"
    },
    "metadata": {
      "region_count": 2,
      "region_names": ["区域1", "区域2"],
      "comparison_metric": "area"
    }
  }
  ```

### 4.3 获取土地类型转换矩阵
- **URL**: `/api/transition`
- **方法**: GET
- **请求参数**:
  - `from_year`: 起始年份
  - `to_year`: 结束年份
  - `region`: 区域几何(bbox坐标或GeoJSON)
- **示例请求**:
  ```
  /api/transition?from_year=2000&to_year=2005&region={"type":"Polygon","coordinates":[[[116,29],[116.1,29],[116.1,29.1],[116,29.1],[116,29]]]}
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "data": {
      "sankey_data": {
        "nodes": ["type1", "type2", "type3"],
        "links": [
          {"source": 0, "target": 0, "value": 80},
          {"source": 0, "target": 1, "value": 20},
          {"source": 1, "target": 1, "value": 180},
          {"source": 1, "target": 2, "value": 20}
        ]
      },
      "transition_stats": {
        "total_change": 40,
        "change_rate": 0.08
      }
    },
    "metadata": {
      "from_year": 2000,
      "to_year": 2005,
      "years_span": 5,
      "node_count": 3,
      "link_count": 4
    }
  }
  ```

## 5. 温度与降水接口

### 5.1 获取年/月平均值
- **URL**: `/api/RT/avg`
- **方法**: GET
- **请求参数**:
  - `year`: 年份
  - `data_type`: 数据类型 (temperature, rainfall)
- **示例请求**:
  ```
  /api/RT/avg?year=2020&data_type=temperature
  ```
- **示例响应**:
  ```json
  {
    "data": {
      "yearly_avg": 18.5,
      "monthly_avg": [5.2, 6.8, 10.5, 16.2, 21.5, 25.8, 28.2, 27.5, 23.8, 18.5, 12.8, 6.5]
    }
  }
  ```

### 5.2 基于GeoJSON的温度与降水统计
- **URL**: `/api/RT/geojson`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "geojson": {"type":"Polygon","coordinates":[[[116,29],[116.1,29],[116.1,29.1],[116,29.1],[116,29]]]},
    "year": 2020,
    "data_type": "temperature",
    "stats": "mean"
  }
  ```
- **示例响应**:
  ```json
  {
    "data": {
      "yearly_stat": 18.2,
      "monthly_stats": [5.0, 6.5, 10.2, 16.0, 21.0, 25.5, 28.0, 27.0, 23.5, 18.0, 12.5, 6.0]
    }
  }
  ```

### 5.3 基于代码的温度与降水统计
- **URL**: `/api/RT/code`
- **方法**: GET
- **请求参数**:
  - `code`: 区域代码
  - `year`: 年份
  - `data_type`: 数据类型 (temperature, rainfall)
  - `stats`: 统计类型 (mean, max, min)
- **示例请求**:
  ```
  /api/RT/code?code=NC&year=2020&data_type=rainfall&stats=mean
  ```
- **示例响应**:
  ```json
  {
    "data": {
      "yearly_stat": 1600.5,
      "monthly_stats": [50.2, 80.5, 120.8, 180.5, 220.8, 250.5, 200.2, 180.5, 150.8, 100.5, 60.2, 30.5]
    }
  }
  ```

### 5.4 基于点位的温度与降水统计
- **URL**: `/api/RT/points`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "points": [[116.0, 29.0], [116.1, 29.1], [116.2, 29.2]],
    "year": 2020,
    "data_type": "temperature",
    "stats": "mean"
  }
  ```
- **示例响应**:
  ```json
  {
    "data": {
      "point_stats": [
        {"coordinates": [116.0, 29.0], "yearly_stat": 18.0, "monthly_stats": [4.8, 6.3, 10.0, 15.8, 20.8, 25.3, 27.8, 26.8, 23.3, 17.8, 12.3, 5.8]},
        {"coordinates": [116.1, 29.1], "yearly_stat": 18.2, "monthly_stats": [5.0, 6.5, 10.2, 16.0, 21.0, 25.5, 28.0, 27.0, 23.5, 18.0, 12.5, 6.0]},
        {"coordinates": [116.2, 29.2], "yearly_stat": 18.4, "monthly_stats": [5.2, 6.7, 10.4, 16.2, 21.2, 25.7, 28.2, 27.2, 23.7, 18.2, 12.7, 6.2]}
      ]
    }
  }
  ```

### 5.5 基于坐标的温度与降水值
- **URL**: `/api/RT/coodinate`
- **方法**: GET
- **请求参数**:
  - `lon`: 经度
  - `lat`: 纬度
  - `year`: 年份
  - `data_type`: 数据类型 (temperature, rainfall)
- **示例请求**:
  ```
  /api/RT/coodinate?lon=116.0&lat=29.0&year=2020&data_type=temperature
  ```
- **示例响应**:
  ```json
  {
    "data": {
      "yearly_value": 18.0,
      "monthly_values": [4.8, 6.3, 10.0, 15.8, 20.8, 25.3, 27.8, 26.8, 23.3, 17.8, 12.3, 5.8]
    }
  }
  ```

## 6. 空间回归分析接口

### 6.1 预处理栅格数据
- **URL**: `/api/preprocess`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "year": 2020,
    "region": "NC",
    "res": "500m",
    "src": "WGS 1984",
    "resuml": "linear"
  }
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "message": "Preprocessing completed successfully",
    "parameters": {
      "resolution": "500m",
      "coordinate_system": "WGS 1984",
      "reclass_method": "linear"
    },
    "data": [
      {"x": 116.0, "y": 29.0, "rsei": 0.65, "lucc_numeric": 2, "temperature": 18.5, "rainfall": 1600.5, "fvc": 0.75},
      {"x": 116.01, "y": 29.0, "rsei": 0.63, "lucc_numeric": 2, "temperature": 18.6, "rainfall": 1590.2, "fvc": 0.73}
    ]
  }
  ```

### 6.2 下载shapefile
- **URL**: `/api/download-shapefile`
- **方法**: GET
- **请求参数**:
  - `year`: 年份
  - `region`: 区域
  - `model`: 模型类型 (OLS, SLM, SEM)
- **示例请求**:
  ```
  /api/download-shapefile?year=2020&region=NC&model=OLS
  ```
- **示例响应**: 下载shapefile的zip文件

### 6.3 获取shapefile字段描述
- **URL**: `/api/shapefile-fields`
- **方法**: GET
- **请求参数**:
  - `year`: 年份
  - `region`: 区域
  - `model`: 模型类型 (OLS, SLM, SEM)
- **示例请求**:
  ```
  /api/shapefile-fields?year=2020&region=NC&model=OLS
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "fields": [
      {"name": "x", "type": "float", "description": "Longitude coordinate"},
      {"name": "y", "type": "float", "description": "Latitude coordinate"},
      {"name": "rsei", "type": "float", "description": "Remote Sensing Ecological Index"},
      {"name": "ols_predicted", "type": "float", "description": "Predicted RSEI values from OLS"},
      {"name": "ols_residuals", "type": "float", "description": "Residuals from OLS"},
      {"name": "ols_std_resid", "type": "float", "description": "Standardized residuals from OLS"}
    ]
  }
  ```

### 6.4 空间回归分析
- **URL**: `/api/spatial-regression`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "year": 2020,
    "region": "NC",
    "dependent_var": "rsei",
    "independent_vars": ["lucc_numeric", "temperature", "rainfall", "fvc"]
  }
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "best_model": {
      "type": "SLM",
      "r_squared": 0.85,
      "parameters": {
        "dependent": "rsei",
        "independent": ["lucc_numeric", "temperature", "rainfall", "fvc"]
      },
      "diagnostics": {
        "sample_size": 1000,
        "coordinates_check": "valid"
      },
      "adj_r2": 0.84,
      "aic": 1200.5,
      "logll": -600.25
    },
    "metadata": {
      "year": 2020,
      "region": "NC",
      "model_comparison": ["OLS", "SLM", "SEM"]
    }
  }
  ```

### 6.5 读取CSV文件
- **URL**: `/api/read-csv`
- **方法**: GET
- **请求参数**:
  - `year`: 年份
  - `region`: 区域
- **示例请求**:
  ```
  /api/read-csv?year=2020&region=NC
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "data": [
      {"x": 116.0, "y": 29.0, "rsei": 0.65, "lucc_numeric": 2, "temperature": 18.5, "rainfall": 1600.5, "fvc": 0.75},
      {"x": 116.01, "y": 29.0, "rsei": 0.63, "lucc_numeric": 2, "temperature": 18.6, "rainfall": 1590.2, "fvc": 0.73}
    ],
    "columns": [
      {"name": "x", "type": "float64"},
      {"name": "y", "type": "float64"},
      {"name": "rsei", "type": "float64"},
      {"name": "lucc_numeric", "type": "int64"},
      {"name": "temperature", "type": "float64"},
      {"name": "rainfall", "type": "float64"},
      {"name": "fvc", "type": "float64"}
    ],
    "total_rows": 1000
  }
  ```

### 6.6 可视化结果
- **URL**: `/api/results/visualize`
- **方法**: GET
- **请求参数**:
  - `year`: 年份
  - `region`: 区域
  - `model`: 模型类型 (OLS, SLM, SEM)
- **示例请求**:
  ```
  /api/results/visualize?year=2020&region=NC&model=OLS
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "geojson": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {"type": "Point", "coordinates": [116.0, 29.0]},
          "properties": {
            "rsei": 0.65,
            "ols_predicted": 0.64,
            "ols_residuals": 0.01,
            "ols_std_resid": 0.05
          }
        }
      ]
    }
  }
  ```

### 6.7 下载CSV文件
- **URL**: `/api/download-csv`
- **方法**: GET
- **请求参数**:
  - `year`: 年份
  - `region`: 区域
- **示例请求**:
  ```
  /api/download-csv?year=2020&region=NC
  ```
- **示例响应**: 下载CSV文件

### 6.8 上传区域shapefile
- **URL**: `/api/upload/region`
- **方法**: POST
- **请求参数**:
  - `region_code`: 区域代码
  - `shp_file`: shapefile文件
  - `shx_file`: 可选，shx文件
  - `dbf_file`: 可选，dbf文件
  - `prj_file`: 可选，prj文件
- **示例响应**:
  ```json
  {
    "status": "success",
    "message": "Shapefile uploaded and processed successfully",
    "region_code": "TEST",
    "geojson": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {"type": "Polygon", "coordinates": [[[116,29],[116.1,29],[116.1,29.1],[116,29.1],[116,29]]]},
          "properties": {}
        }
      ]
    }
  }
  ```

### 6.9 区域生态环境分析
- **URL**: `/api/SRanalysis`
- **方法**: POST
- **请求参数**:
  ```json
  {
    "year": 2020,
    "region": "NC"
  }
  ```
- **示例响应**:
  ```json
  {
    "status": "success",
    "main_factor": "temperature",
    "main_factor_stats": {
      "mean_coefficient": 0.05,
      "std_deviation": 0.01,
      "min_value": 0.03,
      "max_value": 0.07,
      "abs_mean": 0.05
    },
    "precision": 0.8,
    "all_factors": {
      "temperature": {
        "mean_coefficient": 0.05,
        "std_deviation": 0.01,
        "min_value": 0.03,
        "max_value": 0.07,
        "abs_mean": 0.05
      },
      "rainfall": {
        "mean_coefficient": 0.02,
        "std_deviation": 0.005,
        "min_value": 0.01,
        "max_value": 0.03,
        "abs_mean": 0.02
      }
    }
  }
  ```

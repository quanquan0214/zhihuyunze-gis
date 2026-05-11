import requests
import json

# 基础配置
BASE_URL = "http://localhost:7891"
HEADERS = {"Content-Type": "application/json"}

# 测试区域坐标
POYANGHU_POINTS = [
    [117.2368, 29.2969],
    [117.8073, 29.2283],
    [117.4165, 28.7887]
]


def test_create_analyzer():
    """测试创建分析器"""
    url = f"{BASE_URL}/api/analyzer/create"
    data = {"raster_data_path": "D:/Google/RSEI_2000_2022"}

    response = requests.post(url, json=data, headers=HEADERS)
    result = response.json()

    if result['success']:
        print(f"✅ 创建分析器成功 - ID: {result['analyzer_id']}")
        return result['analyzer_id']
    else:
        print(f"❌ 创建分析器失败 - {result.get('error', '未知错误')}")
        return None


def test_add_region(analyzer_id, region_id="poyanghu_test"):
    """测试添加区域"""
    url = f"{BASE_URL}/api/analyzer/{analyzer_id}/regions/add"
    data = {
        "region_id": region_id,
        "type": "points",
        "points": POYANGHU_POINTS,
        "name": "鄱阳湖测试区域"
    }

    response = requests.post(url, json=data, headers=HEADERS)
    result = response.json()

    if result['success']:
        print(f"✅ 添加区域成功 - 区域ID: {region_id}")
    else:
        print(f"❌ 添加区域失败 - {result.get('error', '未知错误')}")


def test_get_regions(analyzer_id):
    """测试获取区域信息"""
    url = f"{BASE_URL}/api/analyzer/{analyzer_id}/regions"

    response = requests.get(url, headers=HEADERS)
    result = response.json()

    if result['success']:
        print("✅ 获取区域信息成功:")
        print(json.dumps(result['regions'], indent=2, ensure_ascii=False))
    else:
        print(f"❌ 获取区域信息失败 - {result.get('error', '未知错误')}")


def test_get_region_statistics(analyzer_id, region_id="poyanghu_test"):
    """测试获取区域统计信息"""
    url = f"{BASE_URL}/api/analyzer/{analyzer_id}/regions/{region_id}/statistics"

    # 可以添加查询参数 ?years=2000&years=2010&years=2020 来指定年份
    params = {"years": [2000, 2010, 2020]}  # 测试指定年份

    response = requests.get(url, headers=HEADERS, params=params)
    result = response.json()

    if result['success']:
        print(f"✅ 获取区域统计信息成功 - 区域ID: {region_id}")
        print(json.dumps(result['statistics'], indent=2, ensure_ascii=False))
    else:
        print(f"❌ 获取区域统计信息失败 - {result.get('error', '未知错误')}")


def test_run_comparison_analysis(analyzer_id, region_id="poyanghu_test"):
    """测试执行对比分析"""
    url = f"{BASE_URL}/api/analyzer/{analyzer_id}/comparison/analyze"
    data = {
        "region_ids": [region_id],
        "analysis_params": {
            "start_year": 2000,
            "end_year": 2020,
            "interval": 5
        }
    }

    response = requests.post(url, json=data, headers=HEADERS)
    result = response.json()

    if result['success']:
        print("✅ 执行对比分析成功:")
        print(json.dumps(result['results'], indent=2, ensure_ascii=False))
    else:
        print(f"❌ 执行对比分析失败 - {result.get('error', '未知错误')}")


def test_list_analyzers():
    """测试列出所有分析器"""
    url = f"{BASE_URL}/api/analyzers"

    response = requests.get(url, headers=HEADERS)
    result = response.json()

    if result['success']:
        print("✅ 列出分析器成功:")
        print(json.dumps(result['analyzers'], indent=2, ensure_ascii=False))
    else:
        print(f"❌ 列出分析器失败 - {result.get('error', '未知错误')}")


def test_delete_analyzer(analyzer_id):
    """测试删除分析器"""
    url = f"{BASE_URL}/api/analyzer/{analyzer_id}/delete"

    response = requests.delete(url, headers=HEADERS)
    result = response.json()

    if result['success']:
        print(f"✅ 删除分析器成功 - ID: {analyzer_id}")
    else:
        print(f"❌ 删除分析器失败 - {result.get('error', '未知错误')}")


if __name__ == "__main__":
    # 执行测试流程
    print("=== 开始测试 ===")

    # 1. 创建分析器
    analyzer_id = test_create_analyzer()
    if not analyzer_id:
        exit(1)

    # 2. 添加区域
    test_add_region(analyzer_id)

    # 3. 获取区域信息
    # test_get_regions(analyzer_id)

    # 4. 获取区域统计信息
    test_get_region_statistics(analyzer_id)

    # 5. 执行对比分析
    # test_run_comparison_analysis(analyzer_id)

    # 6. 列出所有分析器
    # test_list_analyzers()

    # 7. 清理测试分析器
    test_delete_analyzer(analyzer_id)

    print("=== 测试完成 ===")


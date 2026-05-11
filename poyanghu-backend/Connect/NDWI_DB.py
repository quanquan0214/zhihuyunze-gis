# 从“D:\Google\H5\NDWI_shp”文件夹中读取shp文件，计算每个文件中所有面要素的面积总和，并输出到SQL数据表中。
# 新建数据表，这是单独的一个函数
# 数据表的名称是“NDWI_DB”，字段包括自增的id(主键)、字符型字段YearMonth（不为空）、浮点型字段TotalArea（初始为0，可进行后续更新）。
# 读取所有shp文件，计算面积并输出到数据表中。这是一个函数，需要输入文件夹路径。（数据表直接在函数中创建，就调用上面的函数）
# 通过年月份（比如201802）查询数据表中对应月份的总面积值，并返回该总面积。这是一个函数，需要输入年月份。（这里用的数据表都是上面创建的那一个，这里不用再输入数据表名称）
# 以防万一，这里再写一个更新函数，需要输入年月份和面积值，更新数据表中对应月份的总面积值。（这里用的数据表都是上面创建的那一个，这里不用再输入数据表名称）

import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
import geopandas as gpd
from datetime import datetime

# 数据库连接信息
DB_CONFIG = {
    'dbname': 'pylake',
    'user': 'postgres',
    'password': '198701',
    'host': 'localhost',
    'port': '5432'
}

def create_table():
    """创建存储面积数据的数据库表"""
    try:
        # 连接数据库
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                # 创建表的SQL语句
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS NDWI_DB (
                    id SERIAL PRIMARY KEY,
                    YearMonth VARCHAR(6) NOT NULL,
                    TotalArea FLOAT DEFAULT 0
                )
                """
                cursor.execute(create_table_sql)
                print("表 'NDWI_DB' 创建成功或已存在")
    except Exception as e:
        print(f"创建表时出错: {e}")


def process_shp_files(folder_path):
    """
    处理指定文件夹中的所有shp文件，计算面积并存储到数据库

    参数:
    folder_path (str): 包含shp文件的文件夹路径
    """
    try:
        # 确保表已创建
        create_table()
        # 连接数据库
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                # 获取文件夹中所有shp文件
                shp_files = [f for f in os.listdir(folder_path)
                             if f.lower().endswith('.shp')]
                for shp_file in shp_files:
                    try:
                        # 构建完整路径
                        file_path = os.path.join(folder_path, shp_file)
                        # 提取年月信息（假设文件名格式为NDWI_YYYYMM.shp）
                        filename = os.path.basename(shp_file)
                        parts = filename.split('_')
                        if len(parts) < 2:
                            print(f"无法从文件名 {filename} 中提取日期信息，跳过")
                            continue
                        date_part = parts[1].split('.')[0]  # 获取类似YYYYMM的部分
                        # 验证日期格式
                        try:
                            datetime.strptime(date_part, '%Y%m')
                        except ValueError:
                            print(f"日期格式不正确: {date_part}，跳过文件 {filename}")
                            continue
                        # 读取shapefile
                        gdf = gpd.read_file(file_path)
                        # 确保数据有几何列
                        if 'geometry' not in gdf.columns:
                            print(f"文件 {filename} 不包含几何列，跳过")
                            continue
                        # 计算总面积（假设单位为平方米，转换为平方公里）
                        # 确保使用等面积投影进行准确的面积计算
                        if gdf.crs is None:
                            gdf = gdf.set_crs(epsg=4326)  # 默认设置为WGS84
                        # 转换为等面积投影（如EPSG:3857）
                        gdf_projected = gdf.to_crs(epsg=3857)
                        # 计算总面积（平方公里）
                        total_area = gdf_projected['geometry'].area.sum() / 1e6
                        # 插入数据到数据库
                        insert_sql = sql.SQL("""
                        INSERT INTO NDWI_DB (YearMonth, TotalArea)
                        VALUES (%s, %s)
                        ON CONFLICT (YearMonth) DO UPDATE
                        SET TotalArea = EXCLUDED.TotalArea
                        """)
                        cursor.execute(insert_sql, (date_part, total_area))
                        print(f"处理完成: {filename}, 总面积: {total_area:.4f} 平方公里")
                    except Exception as e:
                        print(f"处理文件 {shp_file} 时出错: {e}")
    except Exception as e:
        print(f"连接数据库时出错: {e}")


def query_total_area(year_month):
    """
    查询指定年月的总面积
    参数:
    year_month (str): 年月字符串，格式为YYYYMM
    返回:
    float: 总面积（平方公里），如果未找到则返回None
    """
    try:
        # 验证日期格式
        try:
            datetime.strptime(year_month, '%Y%m')
        except ValueError:
            print(f"日期格式不正确: {year_month}，应为YYYYMM格式")
            return None

        # 连接数据库
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                # 查询SQL
                query_sql = sql.SQL("""
                SELECT TotalArea FROM NDWI_DB
                WHERE YearMonth = %s
                """)
                cursor.execute(query_sql, (year_month,))
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    print(f"未找到 {year_month} 的数据")
                    return None
    except Exception as e:
        print(f"查询数据时出错: {e}")
        return None


if __name__ == "__main__":
    # 指定shapefile文件夹路径
    folder_path = r"D:\Google\H5\NDWI_shp"
    # 处理shapefile文件
    process_shp_files(folder_path)
    # 示例查询
    year_month = "201802"
    total_area = query_total_area(year_month)
    if total_area is not None:
        print(f"{year_month} 的总面积为: {total_area:.4f} 平方公里")


import psycopg2
from psycopg2 import sql
import uuid

# 数据库连接信息
DB_CONFIG = {
    'dbname': 'pylake',
    'user': 'postgres',
    'password': '198701',
    'host': 'localhost',  # 如果数据库在远程服务器上，请替换为服务器地址
    'port': '5432'        # 默认端口为 5432
}

def create_users():
    """创建 Users 表"""
    # 连接到 PostgreSQL 数据库
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        print("连接数据库成功。")

        # 创建表
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Users (
                id UUID PRIMARY KEY,
                username VARCHAR(64) NOT NULL UNIQUE,
                email VARCHAR(64) NOT NULL,
                password VARCHAR(64) NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print("Users 表创建完毕。")
    except Exception as e:
        print(f"创建表时出错: {e}")
    finally:
        # 关闭连接
        if conn:
            cursor.close()
            conn.close()
            print("数据库已关闭。")

def insert_data(username, email, password):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        if query_data(username) != -1:
            print("该用户名已存在。")
            return 0
        id = str(uuid.uuid4())
        # 插入数据
        insert_data_sql = """
            INSERT INTO Users (id,username, email, password)
            VALUES (%s,%s, %s, %s);
        """
        cursor.execute(insert_data_sql, (id,username, email, password))
        conn.commit()
        print(f"用户 {username} 注册成功。")
        return 1
    except Exception as e:
        print(f"保存 {username} 时出错: {e}")
        return 0
    finally:
        # 关闭连接
        if conn:
            cursor.close()
            conn.close()


def query_data(username):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # 查询数据
        query_sql = """SELECT password FROM Users WHERE username = %s;"""
        cursor.execute(query_sql, (username,))
        result = cursor.fetchone()
        if result:
            print("查询成功。")
            return result[0]  # 返回密码
        else:
            print("未找到该用户。")
            return -1
    except Exception as e:
        print(f"查询时出错: {e}")
        return 0
    finally:
        if conn:
            cursor.close()
            conn.close()


def register(username, email, password):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    answer = query_data(username)
    try:
        if answer == 0:
            print("注册失败。")
            return 0
        # 检查用户名是否已存在
        if answer != -1:
            print("该用户名已存在。")
            return -1
        # 该用户名不存在，可以注册
        id = str(uuid.uuid4())
        insert_data_sql = """
                INSERT INTO Users (id,username, email, password)
                VALUES (%s,%s, %s, %s);"""
        cursor.execute(insert_data_sql, (id, username, email, password))
        conn.commit()
        print(f"用户 {username} 注册成功。")
        return 1
    except Exception as e:
        print(f"保存 {username} 时出错: {e}")
        return 0
    finally:
        # 关闭连接
        if conn:
            cursor.close()
            conn.close()


def login(username, password):
    # 连接到 PostgreSQL 数据库
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # 查询数据
        cursor.execute("SELECT id FROM users WHERE username = %s AND password = %s", (username, password))
        result = cursor.fetchone()
        if result:
            id = result[0]
            print("登录成功，用户 ID 为 {id}")
            return id
        else:
            print("用户名或密码错误。")
            return 0
    except Exception as e:
        print(f"查询时出错: {e}")
        return 0
    finally:
        # 关闭连接
        if conn:
            cursor.close()
            conn.close()



# create_users()  # 创建表
# register("lake", "lake@example.com", "lake")  # 注册用户
# register("张三", "zhangsan@example.com", "1234")
# register("李四", "lisi@example.com", "4567")
# register("test_user", "test_user@example.com", "test123")
#print(login("test_user", "test123"))  # 登录测试
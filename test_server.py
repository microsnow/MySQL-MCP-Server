#!/usr/bin/env python3
"""
MySQL MCP Server 测试脚本
"""

import os
import sys
import json
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", ""),
    "charset": "utf8mb4",
    "cursorclass": DictCursor
}


def test_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("测试 1: 数据库连接")
    print("=" * 50)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version")
            result = cursor.fetchone()
            print(f"✅ 连接成功!")
            print(f"   MySQL 版本: {result['version']}")
            print(f"   主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            print(f"   用户: {DB_CONFIG['user']}")
            print(f"   数据库: {DB_CONFIG['database'] or '未指定'}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_query():
    """测试查询功能"""
    print("\n" + "=" * 50)
    print("测试 2: SELECT 查询")
    print("=" * 50)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 测试查询当前数据库
            cursor.execute("SELECT DATABASE() as db")
            result = cursor.fetchone()
            print(f"✅ 查询成功!")
            print(f"   当前数据库: {result['db']}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def test_get_tables():
    """测试获取表列表"""
    print("\n" + "=" * 50)
    print("测试 3: 获取表列表")
    print("=" * 50)

    database = DB_CONFIG.get("database")
    if not database:
        print("⚠️  未配置数据库名称，跳过此测试")
        return True

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, table_comment 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (database,))
            results = cursor.fetchall()
            print(f"✅ 获取成功!")
            print(f"   数据库 '{database}' 中有 {len(results)} 个表:")
            for table in results[:5]:  # 只显示前5个
                print(f"   - {table['table_name']}: {table['table_comment'] or '无注释'}")
            if len(results) > 5:
                print(f"   ... 还有 {len(results) - 5} 个表")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return False


def test_create_sample_table():
    """测试创建示例表"""
    print("\n" + "=" * 50)
    print("测试 4: 创建示例表")
    print("=" * 50)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 创建测试表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mcp_test_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ 测试表创建成功 (mcp_test_table)")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False


def test_insert():
    """测试插入数据"""
    print("\n" + "=" * 50)
    print("测试 5: 插入数据")
    print("=" * 50)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO mcp_test_table (name, email) 
                VALUES ('测试用户', 'test@example.com')
            """)
            conn.commit()
            print(f"✅ 插入成功!")
            print(f"   影响行数: {cursor.rowcount}")
            print(f"   最后插入ID: {cursor.lastrowid}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 插入失败: {e}")
        return False


def test_select():
    """测试查询数据"""
    print("\n" + "=" * 50)
    print("测试 6: 查询数据")
    print("=" * 50)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM mcp_test_table LIMIT 5")
            results = cursor.fetchall()
            print(f"✅ 查询成功!")
            print(f"   返回 {len(results)} 条记录:")
            for row in results:
                print(f"   - ID: {row['id']}, Name: {row['name']}, Email: {row['email']}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def test_cleanup():
    """清理测试数据"""
    print("\n" + "=" * 50)
    print("测试 7: 清理测试数据")
    print("=" * 50)

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS mcp_test_table")
            conn.commit()
            print("✅ 测试表已删除")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "🚀 MySQL MCP Server 测试脚本" + "\n")

    # 检查 .env 文件
    if not os.path.exists(".env"):
        print("⚠️  警告: .env 文件不存在!")
        print("   请先复制 .env.example 到 .env 并配置数据库连接信息")
        print("\n   命令: cp .env.example .env")
        sys.exit(1)

    results = []

    # 运行所有测试
    results.append(("连接测试", test_connection()))
    results.append(("查询测试", test_query()))
    results.append(("获取表列表", test_get_tables()))
    results.append(("创建示例表", test_create_sample_table()))
    results.append(("插入数据", test_insert()))
    results.append(("查询数据", test_select()))
    results.append(("清理数据", test_cleanup()))

    # 打印测试结果汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有测试通过! MCP Server 可以正常工作。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

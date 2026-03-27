#!/usr/bin/env python3
"""
MySQL MCP Server
一个基于Model Context Protocol的MySQL数据库操作服务
"""

import os
import json
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import AsyncIterator, Optional, List, Dict, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
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

# 创建MCP服务器
app = Server("mysql-server")


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        yield conn
    except pymysql.Error as e:
        raise Exception(f"数据库连接失败: {str(e)}")
    finally:
        if conn:
            conn.close()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="query",
            description="执行SELECT查询语句，返回查询结果",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT SQL查询语句"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="execute",
            description="执行INSERT/UPDATE/DELETE等数据修改语句",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL执行语句"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="execute_many",
            description="批量执行SQL语句（用于批量插入等操作）",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL模板语句，使用%s作为占位符"
                    },
                    "params": {
                        "type": "array",
                        "description": "参数列表，每个元素是一个元组或列表",
                        "items": {
                            "type": "array"
                        }
                    }
                },
                "required": ["sql", "params"]
            }
        ),
        Tool(
            name="get_tables",
            description="获取数据库中所有表的信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "数据库名称（可选，默认使用配置的数据库）"
                    }
                }
            }
        ),
        Tool(
            name="get_table_structure",
            description="获取指定表的结构信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "表名"
                    }
                },
                "required": ["table"]
            }
        ),
        Tool(
            name="get_databases",
            description="获取MySQL服务器中所有数据库列表",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="test_connection",
            description="测试数据库连接是否正常",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="transaction",
            description="执行事务（多条SQL语句，要么全部成功，要么全部回滚）",
            inputSchema={
                "type": "object",
                "properties": {
                    "statements": {
                        "type": "array",
                        "description": "SQL语句列表",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["statements"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    """调用工具"""

    if name == "query":
        return await handle_query(arguments)
    elif name == "execute":
        return await handle_execute(arguments)
    elif name == "execute_many":
        return await handle_execute_many(arguments)
    elif name == "get_tables":
        return await handle_get_tables(arguments)
    elif name == "get_table_structure":
        return await handle_get_table_structure(arguments)
    elif name == "get_databases":
        return await handle_get_databases(arguments)
    elif name == "test_connection":
        return await handle_test_connection(arguments)
    elif name == "transaction":
        return await handle_transaction(arguments)
    else:
        raise ValueError(f"未知的工具: {name}")


async def handle_query(arguments: dict) -> list:
    """处理查询请求"""
    sql = arguments.get("sql", "")

    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("query工具只支持SELECT语句")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                results = cursor.fetchall()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "count": len(results),
                            "data": results
                        }, ensure_ascii=False, indent=2, default=str)
                    )
                ]
            except pymysql.Error as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]


async def handle_execute(arguments: dict) -> list:
    """处理执行请求"""
    sql = arguments.get("sql", "")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql)
                conn.commit()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "affected_rows": cursor.rowcount,
                            "last_insert_id": cursor.lastrowid
                        }, ensure_ascii=False)
                    )
                ]
            except pymysql.Error as e:
                conn.rollback()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]


async def handle_execute_many(arguments: dict) -> list:
    """处理批量执行请求"""
    sql = arguments.get("sql", "")
    params = arguments.get("params", [])

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.executemany(sql, params)
                conn.commit()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "affected_rows": cursor.rowcount
                        }, ensure_ascii=False)
                    )
                ]
            except pymysql.Error as e:
                conn.rollback()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]


async def handle_get_tables(arguments: dict) -> list:
    """获取所有表"""
    database = arguments.get("database") or DB_CONFIG.get("database")

    if not database:
        raise ValueError("未指定数据库名称")

    sql = """
        SELECT 
            table_name,
            table_comment,
            engine,
            table_rows,
            data_length,
            create_time
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name
    """

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, (database,))
                results = cursor.fetchall()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "database": database,
                            "tables": results
                        }, ensure_ascii=False, indent=2, default=str)
                    )
                ]
            except pymysql.Error as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]


async def handle_get_table_structure(arguments: dict) -> list:
    """获取表结构"""
    table = arguments.get("table", "")
    database = DB_CONFIG.get("database")

    sql = """
        SELECT 
            column_name,
            data_type,
            column_comment,
            is_nullable,
            column_default,
            extra,
            column_key
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, (database, table))
                columns = cursor.fetchall()

                # 获取索引信息
                cursor.execute(f"SHOW INDEX FROM `{table}`")
                indexes = cursor.fetchall()

                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "table": table,
                            "columns": columns,
                            "indexes": indexes
                        }, ensure_ascii=False, indent=2, default=str)
                    )
                ]
            except pymysql.Error as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]


async def handle_get_databases(arguments: dict) -> list:
    """获取所有数据库"""

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SHOW DATABASES")
                results = cursor.fetchall()
                databases = [db["Database"] for db in results]
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "databases": databases
                        }, ensure_ascii=False, indent=2)
                    )
                ]
            except pymysql.Error as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]


async def handle_test_connection(arguments: dict) -> list:
    """测试数据库连接"""

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION() as version")
                result = cursor.fetchone()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": "数据库连接成功",
                            "mysql_version": result["version"],
                            "config": {
                                "host": DB_CONFIG["host"],
                                "port": DB_CONFIG["port"],
                                "user": DB_CONFIG["user"],
                                "database": DB_CONFIG["database"] or "未指定"
                            }
                        }, ensure_ascii=False, indent=2)
                    )
                ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "message": "数据库连接失败",
                    "error": str(e)
                }, ensure_ascii=False, indent=2)
            )
        ]


async def handle_transaction(arguments: dict) -> list:
    """处理事务"""
    statements = arguments.get("statements", [])

    if not statements:
        raise ValueError("事务中至少需要一条SQL语句")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            results = []
            try:
                for sql in statements:
                    cursor.execute(sql)
                    results.append({
                        "sql": sql[:100] + "..." if len(sql) > 100 else sql,
                        "affected_rows": cursor.rowcount
                    })

                conn.commit()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": "事务执行成功",
                            "results": results
                        }, ensure_ascii=False, indent=2)
                    )
                ]
            except pymysql.Error as e:
                conn.rollback()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "message": "事务执行失败，已回滚",
                            "error": str(e)
                        }, ensure_ascii=False, indent=2)
                    )
                ]


async def main():
    """主函数 - 启动MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

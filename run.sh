#!/bin/bash

# MySQL MCP Server 启动脚本

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在，正在从 .env.example 复制..."
    cp .env.example .env
    echo "请编辑 .env 文件配置您的数据库连接信息"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 启动服务器
echo "🚀 启动 MySQL MCP Server..."
python server.py

@echo off
chcp 65001 >nul

REM MySQL MCP Server 启动脚本 (Windows)

REM 检查 .env 文件是否存在
if not exist ".env" (
    echo 警告: .env 文件不存在，正在从 .env.example 复制...
    copy .env.example .env
    echo 请编辑 .env 文件配置您的数据库连接信息
    pause
    exit /b 1
)

REM 使用完整路径激活 conda 环境
echo 激活 conda 环境 python312...
call E:\data1\soft\anaconda3\Scripts\activate.bat python312

REM 安装依赖
echo 安装依赖...
pip install -q -r requirements.txt

REM 启动服务器
echo 启动 MySQL MCP Server...
python server.py
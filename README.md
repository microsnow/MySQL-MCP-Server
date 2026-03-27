# MySQL MCP Server

一个基于 Model Context Protocol (MCP) 的 MySQL 数据库操作服务，允许 AI 助手直接查询和操作 MySQL 数据库。

## 功能特性

- **query** - 执行 SELECT 查询语句
- **execute** - 执行 INSERT/UPDATE/DELETE 等数据修改语句
- **execute_many** - 批量执行 SQL 语句（批量插入等）
- **get_tables** - 获取数据库中所有表的信息
- **get_table_structure** - 获取指定表的结构信息
- **get_databases** - 获取所有数据库列表
- **test_connection** - 测试数据库连接
- **transaction** - 执行事务（多条 SQL 语句，原子性操作）

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库连接

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的数据库连接信息
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database
```

### 3. 启动服务器

```bash
# 使用启动脚本
./run.sh  # Linux/Mac
# 或
run.bat   # Windows

# 或直接启动
python server.py
```

## 在 Claude Desktop 中使用

### 方法 1: 直接配置

编辑 Claude Desktop 的配置文件：

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": ["mcp_mysql_server/server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_USER": "root",
        "DB_PASSWORD": "your_password",
        "DB_NAME": "your_database"
      }
    }
  }
}
```

### 方法 2: 使用虚拟环境

```json
{
  "mcpServers": {
    "mysql": {
      "command": "python",
      "args": ["mcp_mysql_server/server.py"]
    }
  }
}
```

## 使用示例

### 查询数据

```
请帮我查询 users 表中所有的用户
```

AI 会自动调用 `query` 工具：
```sql
SELECT * FROM users
```

### 插入数据

```
请帮我在 users 表中插入一条新记录，name=张三, email=zhangsan@example.com
```

AI 会自动调用 `execute` 工具：
```sql
INSERT INTO users (name, email) VALUES ('张三', 'zhangsan@example.com')
```

### 查看表结构

```
请帮我查看 users 表的结构
```

AI 会自动调用 `get_table_structure` 工具。

### 执行事务

```
请帮我执行一个事务：先插入订单，再更新库存
```

AI 会自动调用 `transaction` 工具执行多条 SQL。

## 安全注意事项

1. **不要在代码中硬编码数据库密码**，使用环境变量
2. **限制数据库用户权限**，只授予必要的权限
3. **不要在生产环境直接使用 root 账户**
4. **定期更换数据库密码**

## 项目结构

```
mcp_mysql_server/
├── server.py           # 主服务器文件
├── requirements.txt    # Python 依赖
├── .env.example        # 环境变量模板
├── run.sh              # Linux/Mac 启动脚本
├── run.bat             # Windows 启动脚本
├── mcp.json            # MCP 配置示例
└── README.md           # 说明文档
```

## 依赖项

- `mcp` - Model Context Protocol SDK
- `pymysql` - MySQL 数据库驱动
- `cryptography` - 用于加密连接
- `python-dotenv` - 环境变量管理

## 许可证

MIT License

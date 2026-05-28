# FastAPI 后端项目

基于 FastAPI 的用户管理后端服务，支持 MySQL 数据库、用户 CRUD 操作、头像上传等功能。

## 技术栈

| 技术 | 说明 |
|------|------|
| **FastAPI** | 高性能 Web 框架，支持异步 API |
| **SQLAlchemy** | Python ORM，用于数据库操作 |
| **Pymysql** | MySQL 数据库驱动 |
| **Uvicorn** | ASGI 服务器 |
| **python-dotenv** | 环境变量管理 |

## 项目结构

```
fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py          # 主应用入口
│   ├── users.py         # 用户管理模块
│   ├── uploads/         # 上传的头像文件（不提交到 Git）
│   └── .env             # 环境变量配置（不提交到 Git）
├── routers/
│   ├── __init__.py
│   └── users.py         # 早期用户路由（已迁移到 app/users.py）
├── requirements.txt
└── .gitignore
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `app/` 目录下创建 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database
```

### 3. 创建数据库

```sql
CREATE DATABASE your_database DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动服务

```bash
# 开发模式（热重载）
fastapi dev

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 接口列表

### 用户管理模块

| 接口 | 方法 | 说明 | Content-Type |
|------|------|------|--------------|
| `/api/users/list` | GET | 获取用户列表 | - |
| `/api/users/add` | POST | 新增用户 | multipart/form-data |
| `/api/users/edit` | POST | 编辑用户 | multipart/form-data |
| `/api/users/delete` | POST | 删除用户 | application/json |
| `/api/users/batch-delete` | POST | 批量删除用户 | application/json |

### 其他接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/items/{item_id}` | GET | 获取商品详情 |
| `/items/` | POST | 创建商品 |
| `/items/` | GET | 获取商品列表 |
| `/stream/rick` | GET | 流式输出示例 |

## 接口详情

### 用户列表 `GET /api/users/list`

**Query 参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码（默认1） |
| page_size | int | 每页数量（默认10） |
| username | string | 用户名筛选（模糊匹配） |
| role | string | 角色筛选（admin/user） |
| status | int | 状态筛选 |
| nickname | string | 昵称筛选（模糊匹配） |

**响应示例**：
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "avatar": "abc123.jpg",
            "username": "admin",
            "role": "admin",
            "role_name": "管理员",
            "status": 1,
            "nickname": "管理员",
            "created_at": "2026-05-27 10:30:00",
            "updated_at": "2026-05-27 10:30:00"
        }
    ],
    "total": 100,
    "page": 1,
    "page_size": 10
}
```

### 新增用户 `POST /api/users/add`

**FormData 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| nickname | string | 否 | 昵称 |
| avatar | file | 否 | 头像图片 |
| role | string | 否 | 角色（默认 user） |
| status | string | 否 | 状态（默认 1） |

**响应示例**：
```json
{
    "code": 200,
    "message": "注册成功",
    "data": {
        "id": 1,
        "username": "test",
        "role": "user",
        "role_name": "普通用户",
        "avatar": "abc123.jpg",
        "created_at": "2026-05-27 10:30:00"
    }
}
```

### 编辑用户 `POST /api/users/edit`

**FormData 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 用户ID |
| username | string | 否 | 用户名 |
| password | string | 否 | 密码 |
| nickname | string | 否 | 昵称 |
| avatar | file | 否 | 头像图片 |
| role | string | 否 | 角色 |
| status | string | 否 | 状态 |

### 删除用户 `POST /api/users/delete`

**Body 参数**：
```json
{
    "id": 1
}
```

### 批量删除用户 `POST /api/users/batch-delete`

**Body 参数**：
```json
{
    "ids": [1, 2, 3]
}
```

## 角色说明

| role 值 | 角色名 | 说明 |
|---------|--------|------|
| admin | 管理员 | 管理员角色 |
| user | 普通用户 | 默认角色 |

## 头像访问

上传的头像文件存储在 `app/uploads/` 目录，通过以下 URL 访问：

```
http://localhost:8000/uploads/文件名.jpg
```

## 注意事项

### 1. 环境变量安全

`.env` 文件包含数据库密码等敏感信息，**不要提交到 Git**。项目已配置 `.gitignore` 排除此文件。

### 2. 虚拟环境

建议使用虚拟环境隔离项目依赖：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库连接池

默认配置连接池大小为 5，最大溢出 10。如需调整，修改 `app/users.py`：

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,      # 连接池大小
    max_overflow=20,   # 最大溢出
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### 4. 文件上传

- 头像文件格式支持：jpg, png, gif, webp 等常见图片格式
- 文件名使用 UUID 生成，保证唯一性
- 上传目录 `app/uploads/` 已加入 `.gitignore`

### 5. 跨域配置

当前配置允许所有来源访问：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

生产环境建议限制 `allow_origins`。

### 6. 时区问题

数据库存储的时间默认使用本地时区。如需 UTC 时间，修改模型定义：

```python
created_at = Column(DateTime, default=datetime.utcnow)
```

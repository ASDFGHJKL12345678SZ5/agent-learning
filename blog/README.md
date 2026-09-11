# Blog API

用 **FastAPI + SQLAlchemy + MySQL + Docker Compose** 实现的博客后端，支持文章的创建与查询。

## 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/articles` | 创建文章，请求体 `{"title": "...", "content": "..."}` |
| GET | `/articles` | 文章列表（按 id 倒序，最新在前） |
| GET | `/articles/{id}` | 单篇文章，不存在返回 404 |

## 一键启动（Docker Compose，推荐）

```bash
docker compose up --build
```

然后打开交互文档：<http://localhost:8000/docs>

停止并清除数据：

```bash
docker compose down --volumes
```

## 本地开发（不用 Docker）

默认使用 SQLite，无需额外安装数据库：

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# 打开 http://127.0.0.1:8000/docs
```

切换到 MySQL 只需设置环境变量：

```bash
set DATABASE_URL=mysql+pymysql://用户:密码@主机:3306/库名     # Windows
export DATABASE_URL=mysql+pymysql://用户:密码@主机:3306/库名  # Linux/macOS
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | FastAPI 应用 + 三个接口 |
| `models.py` | SQLAlchemy 模型（Article 表） |
| `database.py` | 数据库连接与会话 |
| `requirements.txt` | Python 依赖 |
| `Dockerfile` | 把应用打包成镜像 |
| `docker-compose.yml` | 编排 app + MySQL 两个服务 |
| `.dockerignore` / `.gitignore` | 排除不该进镜像 / 版本库的文件 |

## 快速试一下

```bash
# 创建一篇
curl -X POST http://localhost:8000/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","content":"My first post"}'

# 查看列表
curl http://localhost:8000/articles

# 查看单篇
curl http://localhost:8000/articles/1
```

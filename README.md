# agent-learning

> 我在学习 **Python + AI Agent** 的练习仓库。按阶段推进，每天一个练习，用英文 commit。
> 目标：8 周内掌握 Python 工程化、LLM、RAG、Agent、Multi-Agent 与 MCP。

---

## 📂 目录结构

| 目录 | 内容 | 阶段/主题 |
|------|------|----------|
| `practice/` | Python 基础练习：计算器、学生成绩管理 | 第1阶段 Python 基础 |
| `todo_project/` | OOP + 文件持久化 TodoList、装饰器、生成器、深浅拷贝 | 第1阶段 进阶语法 |
| `fastapi_app/` | 第一个 FastAPI 应用（GET /hello + POST /echo） | 第1阶段 Day6 |
| `awesome-project/` | 用 uv 管理的 FastAPI 教程项目（Python 3.13） | 第1阶段 工程化 |

---

## 🚀 怎么运行

### fastapi_app（第一个 FastAPI 应用）

```bash
cd fastapi_app
pip install fastapi "uvicorn[standard]"
uvicorn main:app --reload
# 浏览器打开 http://127.0.0.1:8000/docs
```

接口：
- `GET /hello` → `{"message": "你好，世界！Hello World!"}`
- `POST /echo`，请求体 `{"text": "..."}` → 回显原话和长度

### todo_project（TodoList + 进阶语法演示）

```bash
cd todo_project
python demo.py            # TodoList 持久化演示
python timer_decorator.py  # @timer 装饰器
python fibonacci.py        # 斐波那契生成器
python copy_demo.py        # 浅拷贝 vs 深拷贝
```

### practice（Python 基础练习）

```bash
cd practice
python calculator.py
python student_manager.py
```

---

## 🧭 环境地图（哪个目录用哪个 venv）

| 目录 | 用哪个解释器 | 依赖清单 |
|------|------|------|
| `practice/` `todo_project/` `fastapi_app/` `async_learn/` `blog/` | 根目录 **`.venv`** | `requirements.txt` |
| `llm_learn/` | `llm_learn/.venv` | `llm_learn/requirements.txt` |
| `rag_learn/` | `rag_learn/.venv` | `rag_learn/requirements.txt` |

- 每个 venv 另有一份 `requirements.lock.txt`：**完整锁定**（含所有间接依赖，分别 21 / 9 / 112 个包），换机器时用它 1:1 还原
- ⚠️ `blog/requirements.txt` 是**给 `blog/Dockerfile` 容器构建用的**，和本地 venv 是两回事，别混
- 三个 venv 都已写进 `.gitignore`（不进版本库）

> 💡 **跑脚本一律用显式路径，不要 `activate`** —— 避免"以为在 A 环境，其实在 B 环境"：
> ```powershell
> & .\.venv\Scripts\python.exe -X utf8 脚本名.py
> ```
> 中文输出务必带 `-X utf8`（Windows 下不加会乱码）。

---

## ✅ 关于这个仓库的约定

- **每天至少一次英文 commit**（commit message 用英文）
- **生成物不进版本库**：`__pycache__/`、`.venv/`、`todos.json` 等已用 `.gitignore` 排除
- **先跑通再优化**：60 分能跑 > 100 分没写完

---

## 🗺️ 学习路线（阶段）

1. Python 与工程化（基础语法 → FastAPI → Docker）
2. LLM 原理 + Prompt + API 调用
3. RAG 入门（LangChain + Chroma）
4. Agent 核心（ReAct + LangGraph）
5. Multi-Agent + MCP

---

*练习仓库，欢迎 Star。遇到问题欢迎提 Issue。*

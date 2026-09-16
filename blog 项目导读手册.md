# Blog 项目导读手册

> 项目路径：`D:\Desktop\Practice\blog`
> 技术栈：FastAPI + SQLAlchemy + Pydantic + MySQL/SQLite + Docker Compose
> 配套：`VS Code 代码阅读手册.md`（工具怎么用）← 本手册讲「**读什么、按什么顺序读**」

---

## 零、⭐ 读陌生项目的第一原则（最重要的一条）

> ❌ **不要从 `main.py` 的第 1 行开始往下读。**
> ✅ **从「它做什么」→「它怎么拼起来的」→ 最后才是「每行在干嘛」。**

这叫**由外向内**读法。原因很实在：

- 一个项目里有**两种代码**：**接口/骨架**（少、重要）和**业务细节**（多、可以先跳过）
- 从第一行硬读，你会**用 80% 的时间读那 20% 不重要的细节**，然后卡在某个语法上，然后放弃
- 而正确的顺序能让你**在 10 分钟内说出"这个系统是怎么跑起来的"**

**新手读代码的三种典型失败**：

| 失败模式 | 表现 | 解药 |
|---|---|---|
| **逐行硬读** | 从第 1 行读到第 300 行，越读越懵 | 先看结构（`Ctrl+Shift+O`） |
| **只读不跑** | 代码看懂了，但不知道跑起来啥样 | 跑一遍，打断点 |
| **只读一个文件** | 不知道 `main.py` 里的 `SessionLocal` 是哪来的 | `F12` 跳过去看 |

---

## 一、⭐ 先拿到"全景图"：4 个文件就能秒懂一个项目

**推荐阅读顺序（注意：和文件名顺序完全不一样）：**

| 顺序 | 文件 | 为什么先读它 | 花多久 |
|---|---|---|---|
| **1** | `README.md` | **它做什么**、有哪些接口 | 2 分钟 |
| **2** | `requirements.txt` | **技术栈清单** —— 4 行看懂用了什么库 | 30 秒 |
| **3** | ⭐ **`docker-compose.yml`** | **整个系统的全景图**：由几个部分组成、怎么找到对方 | 3 分钟 |
| **4** | `main.py` | 对外暴露的接口（**先只看函数名和装饰器**） | 5 分钟 |
| **5** | `models.py` | 数据长什么样 | 2 分钟 |
| **6** | `database.py` | 连接是怎么建的 | 2 分钟 |
| **7** | `Dockerfile` | 怎么打包成镜像 | 2 分钟 |

> ⭐ **为什么 `docker-compose.yml` 是读这个项目最好的入口？**
>
> 因为它一眼告诉你**"这个系统由几块组成、它们怎么互相找到对方"** ——
> 而 `main.py` 只告诉你"有哪些接口"，看不到全貌。
>
> **读任何微服务/容器化项目，都先读编排文件。**

### 从 `requirements.txt` 能秒读到什么

```
fastapi            → Web 框架（提供路由、自动文档、请求校验、依赖注入）
uvicorn[standard]  → ASGI 服务器（真正把服务跑起来的东西）
sqlalchemy         → ORM（用 Python 类操作数据库）
pymysql            → MySQL 驱动（SQLAlchemy 靠它连 MySQL）
```

> 💡 **看依赖就能猜出架构**：有 `fastapi` 说明是 HTTP 服务；有 `sqlalchemy` 说明要连数据库；
> 有 `pymysql` 说明连的是 MySQL。**这 4 行信息量比读 100 行代码还大。**
>
> 📌 **顺手一个语法点**：`uvicorn[standard]` 里那个方括号叫 **extra（可选依赖组）** ——
> 意思是"装 uvicorn，并额外装上标准配置需要的一堆包"（比如更快的 websocket 实现、watchfiles 等）。
> 不加 `[standard]` 也能跑，但 `--reload` 会慢很多。
> **看到 `包名[xxx]` 就知道：这是同一个包的可选增强版。**

---

## 二、一张图看懂这个项目

```
        ┌──────────────────────────────────────────┐
        │  浏览器 / curl / Swagger UI（/docs）      │
        └───────────────────┬──────────────────────┘
                            │  HTTP 请求
        ┌───────────────────▼──────────────────────┐
        │  Docker 容器（你电脑的 8000 端口）          │
        │                                          │
        │   main.py        ← 路由层：管 URL、请求体、  │
        │     │              响应体、状态码           │
        │     │                                    │
        │     ├── models.py    ← ORM 层：Python 类    │
        │     │                   ↔ 数据库表          │
        │     │                                    │
        │     └── database.py  ← 连接层：engine /     │
        │                         Session / Base     │
        └───────────────────┬──────────────────────┘
                            │  SQL
        ┌───────────────────▼──────────────────────┐
        │  Docker 容器（MySQL 8）  ← 服务名 db        │
        │  数据存在命名卷 db_data 里（容器删了还在）   │
        └──────────────────────────────────────────┘
```

**三个文件的分工一句话：**

| 文件 | 一句话职责 | 类比 |
|---|---|---|
| `main.py` | 决定"外面能怎么调用我" | 餐厅的**前台 + 菜单** |
| `models.py` | 决定"数据长什么样" | **仓库的货架标签** |
| `database.py` | 决定"怎么连上数据库" | **送货的通道** |

> ⭐ **这是标准的「三层分层」**：**接口层 / 数据模型层 / 连接层**。
> 你以后写的每一个后端项目，基本都是这个骨架 —— **认得出骨架，读任何项目都快。**

---

## 三、⭐ 追一条链路：一个 POST 请求的完整旅程

**这是本手册最值钱的一节。** 读代码最有效的方法不是"读文件"，是**追一条数据流**。

任务：`curl -X POST http://localhost:8000/articles -d '{"title":"Hello","content":"My first post"}'`

| # | 位置 | 发生了什么 | VS Code 怎么到这儿 |
|---|---|---|---|
| 1 | `docker-compose.yml:25` | `"8000:8000"` 把宿主机 8000 端口映射进容器 | — |
| 2 | `Dockerfile:18` | `CMD ["uvicorn","main:app",...]` 启动服务，加载 `main` 模块里的 `app` | — |
| 3 | `main.py:35` | `app = FastAPI(title="Blog API")` 创建应用 | `Ctrl+Shift+O` 找 `app` |
| 4 | `main.py:66` | `@app.post("/articles", ...)` **路由匹配成功** | — |
| 5 | `main.py:39` | FastAPI 用 `ArticleCreate` **校验请求体**<br>（少了 `title` 会自动返回 **422**） | `F12` 看 `ArticleCreate` |
| 6 | `main.py:67` | `db: Session = Depends(get_db)` —— **依赖注入** | `Shift+Alt+H` 看 `get_db` 被谁调用 |
| 7 | `main.py:57` | → `get_db()` 执行，`yield db` 把会话交给接口 | `F12` 进 `get_db` |
| 8 | `database.py:18` | → `SessionLocal()` 造出一个会话 | `F12` 进 `SessionLocal` |
| 9 | `database.py:15` | → 会话绑定到 `engine`（真正管通信的引擎） | — |
| 10 | `main.py:68` | `models.Article(...)` 造一个 ORM 对象 | `F12` 进 `models.Article` |
| 11 | `models.py:11` | `class Article(Base)` —— 这个类对应 `articles` 表 | — |
| 12 | `main.py:70` | `db.commit()` → SQLAlchemy **生成 INSERT 语句发给数据库** | — |
| 13 | `models.py:19` | `server_default=func.now()` —— `created_at` 由**数据库**填 | — |
| 14 | `main.py:71` | `db.refresh(obj)` **回读**数据库生成的 `id` 和 `created_at` | — |
| 15 | `main.py:45` | 返回时，`ArticleOut` 把 ORM 对象**转成响应结构** | — |
| 16 | `main.py:53` | `from_attributes = True` 让它能直接吃 ORM 对象 | — |
| 17 | `main.py:66` | `status_code=201` —— 返回 **201 Created** | — |
| 18 | `main.py:62` | 请求结束，`finally: db.close()` **关闭会话** | 回到 `get_db` |

**走完这一遍，你就真正"读懂"这个项目了** —— 不是"每个文件都看过"，而是**"一条数据流怎么穿过它们"**。

---

## 四、用 VS Code 实操一遍（对应上一份手册）

打开 `blog/main.py`，按顺序做：

| 步骤 | 操作 | 你会看到 |
|---|---|---|
| 1 | `Ctrl+Shift+O` | 文件大纲：3 个接口 + 2 个模型 + 2 个函数，**一眼看完** |
| 2 | 光标放到第 11 行的 `SessionLocal`，按 **`F12`** | 跳到 `database.py` |
| 3 | 按 **`Alt+←`** | **跳回来**（这一步最关键） |
| 4 | 光标放到第 68 行的 `models.Article`，按 **`Alt+F12`** | **不跳走**，弹出小窗看 `Article` 类 |
| 5 | 按 `Esc` | 关掉，人还在原地 |
| 6 | 光标放到第 57 行的 `get_db`，按 **`Shift+Alt+H`** | **调用层次**：看到它被 3 个接口都用到了 |
| 7 | 光标放到第 5 行的 `Depends`，按 **`Ctrl`+鼠标点击** | 跳进 FastAPI 源码（看得懂就看看，看不懂就 `Alt+←` 回来）|
| 8 | 光标放到第 20 行的 `engine`，按 **`Shift+F12`** | **引用列表**：`engine` 在哪些地方被用了 |

> ⭐ **重点体会第 3 步和第 6 步。**
> 有了 `Alt+←`，你才敢到处跳；有了 **调用层次**，你才知道"谁在用它"。
> **这两个功能决定了你是"敢跳"还是"只敢读当前文件"。**

---

## 五、⭐ 这个项目的 12 个设计亮点（面试会问）

**这份清单是本手册的第二价值点。** 你能说出这些"为什么"，就超过 90% 只会写接口的人。

### 🗄️ 数据层

| # | 设计 | 为什么这么做 | 在哪一行 |
|---|---|---|---|
| 1 | **`DATABASE_URL` 从环境变量读，默认 SQLite** | **配置与代码分离**：同一份代码，本地跑 SQLite、Docker 里跑 MySQL，**零改动切换** | `database.py:9` |
| 2 | **`connect_args` 按数据库类型分支** | SQLite 多线程要 `check_same_thread=False`，MySQL 不需要 —— **说明作者知道两者的差异** | `database.py:12` |
| 3 | ⭐ **`server_default=func.now()` 而不是 `default=datetime.now`** | **让数据库填默认值**。这样即使有人绕过 ORM 直接写原生 SQL，`created_at` 也会自动填上 | `models.py:19` |
| 4 | **`title` 用 `String(200)`、`content` 用 `Text`** | 标题有长度上限（可加索引），正文是长文本 —— **类型选择是有理由的** | `models.py:15-16` |

### 🌐 接口层

| # | 设计 | 为什么这么做 | 在哪一行 |
|---|---|---|---|
| 5 | ⭐ **拆成 `ArticleCreate` 和 `ArticleOut` 两个模型** | **输入输出分离**。创建时**不该**允许客户端指定 `id` 和 `created_at`；返回时**必须**带上 —— **这是安全设计** | `main.py:39,45` |
| 6 | ⭐ **`response_model=ArticleOut`** | 不只是文档！它还会**过滤字段** —— 防止将来加了敏感字段（如作者手机号）被意外泄露 | `main.py:66,76,83` |
| 7 | **`status_code=201`** | 201 = Created，是"创建成功"的**正确**状态码（不是 200） | `main.py:66` |
| 8 | ⭐ **`get_db()` 用 `try/finally` + `yield`** | **依赖注入** + **保证会话一定被关闭**（哪怕接口抛异常）<br>👉 你第 1 阶段学的**生成器**在这里的实战用法 | `main.py:57-62` |
| 9 | **`db.refresh(obj)`** | `commit` 之后，`id` 和 `created_at` 还是 Python 侧的默认值，**必须回读数据库**才拿得到真值 | `main.py:71` |
| 10 | **404 用 `HTTPException` 抛** | 让 FastAPI 统一处理成标准错误响应 | `main.py:87` |

### 🐳 容器化

| # | 设计 | 为什么这么做 | 在哪一行 |
|---|---|---|---|
| 11 | ⭐⭐ **`wait_for_db()` 重试 30 次** | **MySQL 容器启动比 app 慢**。不重试的话 app 会因为连不上数据库直接崩溃 —— **容器化的经典坑** | `main.py:14-28` |
| 12 | ⭐⭐ **healthcheck 用 `127.0.0.1` 而不是 `localhost`** | **`localhost` 走 socket，会在 MySQL 初始化阶段就"提前"返回成功**，导致 app 过早启动 | `docker-compose.yml:15` |
| 13 | **`depends_on: condition: service_healthy`** | 不只是"启动顺序"，而是**等它真的能用** | `docker-compose.yml:31` |
| 14 | ⭐ **Dockerfile 先 COPY 依赖清单再 COPY 代码** | **层缓存优化**：改代码不会重装依赖（否则每次构建都要重装几分钟） | `Dockerfile:8-12` |
| 15 | **`--host 0.0.0.0`** | 监听所有网卡，容器外才访问得到（写 `127.0.0.1` 就只能容器内访问） | `Dockerfile:18` |

> 💡 **面试怎么用这份清单**：
> 不要说"我写过一个博客 API"。
> 要说"**我用环境变量做了 SQLite/MySQL 的零改动切换；用 `server_default` 保证绕过 ORM 的插入也有时间戳；用 healthcheck 解决容器启动顺序问题**"。
> **同一个项目，后者是工程师，前者是作业。**

---

## 六、动手验证清单（**别只读，去跑**）

### 第一步：拿到运行时的体验

```bash
cd D:\Desktop\Practice\blog
docker compose up --build
```

打开 **http://localhost:8000/docs** —— 这就是 FastAPI 白送的交互式文档。

### 第二步：五个验证实验

| # | 做什么 | 观察什么 | 学到的 |
|---|---|---|---|
| 1 | 在 `/docs` 里试 POST，建一篇文章 | 返回 **201**、带 `id` 和 `created_at` | 接口正常 |
| 2 | **故意漏掉 `title`** 再发一次 | 返回 **422** + 详细的字段报错 | Pydantic 校验在**进你的函数之前**就拦住了 |
| 3 | 查一个不存在的 id，如 `/articles/9999` | 返回 **404** `{"detail":"文章不存在"}` | `HTTPException` 的作用 |
| 4 | 连发 3 篇，然后 `GET /articles` | 按 **id 倒序**（最新在前） | `order_by(...desc())` 生效 |
| 5 | `docker compose logs -f app` | **看 `wait_for_db()` 打印的重试过程** | ⭐ **亲眼看到"app 在等数据库"** |

### 第三步：⭐ 打断点，真的"看见"代码怎么跑

不用 Docker，用本地 SQLite 模式：

```bash
cd D:\Desktop\Practice\blog
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

然后在 VS Code 里：

| 操作 | 位置 |
|---|---|
| `F9` 打断点 | `main.py` 第 68 行（`obj = models.Article(...)`） |
| `F5` 启动调试 | 选 "Python Debugger" |
| 在 `/docs` 发一个 POST | 程序会**停在断点** |
| 看左侧变量面板 | ⭐ **`article` 这个 Pydantic 对象里装的是什么？** |
| `F10` 单步 | 一行一行走，**看着 `obj` 从 ORM 对象长出 `id`** |

> ⭐ **打断点看 `article` 变量的那一刻，你就真正理解"请求体是怎么变成 Python 对象的"了。**
> 这比读十遍代码都管用。

---

## 七、遗留任务：`PUT` / `DELETE` 该加在哪

你第 1 阶段留的作业 —— 现在你应该能自己找出该改哪些地方了：

| 要改的 | 在哪 | 加什么 |
|---|---|---|
| 新增接口 | `main.py`（在 `get_article` 后面） | `@app.put("/articles/{article_id}")`<br>`@app.delete("/articles/{article_id}")` |
| 新增请求体模型 | `main.py` 的 Pydantic 区 | `ArticleUpdate`（**所有字段可选** —— 因为部分更新） |
| **要不要改** `models.py`？ | — | ❌ **不用** —— 表结构没变 |
| **要不要改** `database.py`？ | — | ❌ **不用** —— 连接方式没变 |
| **要不要改** README？ | `README.md:7` 的接口表 | ✅ **要** —— 接口清单变了 |

> ⭐ **注意最后两行。** 这个练习真正的考点是：
> **"要改一个功能，我需要动哪几个文件？"**
> 能一眼答出"只要改 `main.py` 和 README"，说明**你真的理解了这个项目的分层**。

---

## 八、检验问题

### 基础（能不能读懂）

1. 一个 POST 请求进来后，**依次经过哪几个文件**？说出顺序。
2. `models.py` 里的 `Article` 类，和数据库里的 `articles` 表，**是怎么对应起来的**？（提示：看 `__tablename__` 和继承的 `Base`）
3. 如果我把 `database.py` 第 9 行的默认值从 `sqlite:///./blog.db` 删掉，**会发生什么？**

### 进阶（能不能想明白）

4. ⭐ **为什么要有 `ArticleCreate` 和 `ArticleOut` 两个模型？用一个不行吗？**
5. ⭐ **`db.commit()` 之后为什么还要 `db.refresh(obj)`？** 不刷新会怎样？
6. **`server_default=func.now()` 和 `default=datetime.now` 有什么区别？** 为什么要选前者？
7. **`wait_for_db()` 如果删掉，`docker compose up` 会怎样？**

### 架构（能不能迁移）

8. ⭐ **如果要给这个项目加一个"用户"表，并且文章要关联作者，你要改哪几个文件？**
9. **如果我要把 MySQL 换成 PostgreSQL，要改哪几行？**（提示：答案非常少）
10. ⭐⭐ **为什么说 `docker-compose.yml` 是读这个项目最好的入口？**

---

## 九、一句话总结

> **读项目不是"读完所有文件"，是能回答三个问题：**
>
> 1. **它由几块组成？**（`docker-compose.yml` + 三个 .py 的分层）
> 2. **一条数据怎么穿过它们？**（第三节那条链路）
> 3. **每个设计决策是为了解决什么问题？**（第五节那 15 条）
>
> **答得出这三个，你就"读懂"了 —— 哪怕你还有几行语法没看明白。**

---

*配套阅读：`VS Code 代码阅读手册.md`（工具怎么用）*
*创建于 2026-09-15*

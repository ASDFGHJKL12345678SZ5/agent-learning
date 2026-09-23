# PDF 知识库问答（Day 7 综合项目）

> 上传 PDF → 自动建索引 → 多轮问答 → 答案带引用来源

<!-- ⚠️ 这个 README 我搭了骨架，**内容要你自己填**。
     验收标准是你自己定过的：**别人能 5 分钟跑起来用**。
     所以写的时候假设"读者从没看过你的代码"——他要的是命令，不是你的心路历程。 -->

## 它是什么

一句话：把 PDF 丢进去，然后用自然语言问它。

- 上传 PDF，自动分块、向量化、存进 Chroma
- 多轮追问（"那它的缺点呢？"能听懂）
- 答案带**引用来源**（哪个文件、第几页）

## 架构

<!-- TODO：画一张 ASCII 流程图。参考你发的 RAG 流程图，但只画你实现的这条链。
     需要体现两条流水线：离线索引 / 在线查询。
     提示：你的项目里这两条线分别在 ingest.py 和 qa.py 里。 -->

```
（在这里画）
```

## 快速开始

```powershell
cd D:\Desktop\Practice\rag_learn

# 1. 装依赖（只有第一次）
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. 配置密钥：复制 .env.example 为 .env 并填 key
#    （LLM_* 对话用 DeepSeek，EMB_* 向量用智谱）

# 3. 建索引：把一个 PDF 喂进去
.\.venv\Scripts\python.exe -X utf8 kb\cli.py ingest data\sample20.pdf

# 4. 开始问答
.\.venv\Scripts\python.exe -X utf8 kb\cli.py
```

<!-- TODO：上面这几条命令**你自己照着跑一遍**，跑不通就改。
     这一步就是"别人能 5 分钟跑起来"的验收 —— 你自己就是那个"别人"。 -->

## HTTP 接口版（可选）

```powershell
.\.venv\Scripts\python.exe -X utf8 -m uvicorn kb.server:app --reload --port 8000
# 然后打开 http://127.0.0.1:8000/docs 点着试
```

| 接口 | 作用 |
|---|---|
| `GET /stats` | 看知识库状态 |
| `POST /upload` | 上传 PDF 并建索引 |
| `POST /ask` | 提问（可带对话历史） |

## 文件说明

| 文件 | 作用 |
|---|---|
| `kb/common.py` | 公共底座：加载前 6 天的成果 |
| `kb/ingest.py` | 建索引（PDF → 切分 → 向量化 → Chroma） |
| `kb/qa.py` | 问答（消解 → 检索 → 拼 prompt → 生成） |
| `kb/cli.py` | 命令行入口 |
| `kb/server.py` | FastAPI 入口 |

## 关键设计决定（写清楚"为什么"）

<!-- TODO：挑 3-5 个真实的取舍写下来。比如：
     · 为什么按页切而不是全文切？（溯源需要边界 —— Day3 学过）
     · 为什么 chunk_size 用 400？（有实测数据支撑，不是拍的）
     · 为什么 Chroma 要显式设 hnsw:space=cosine？（默认是 l2）
     · 为什么检索时要先做指代消解？（Day6 的对照实验）
     · 引用来源是怎么实现的？（metadata 一路带下来 + source_label 渲染）
     ⭐ 这一段是给面试官看的 —— 能不能说出"我为什么这么选"才是分水岭。 -->

## 已知限制

<!-- TODO：诚实地写。比如：
     · 检索分数没有阈值，可能把不相关的块喂给模型
     · 只支持 PDF，不支持扫描件（没有文字层）
     · 大文件会一次性全部索引，没有增量更新
     ⭐ 能说出自己的系统"哪里不行"，比吹它"哪都行"更让人信。 -->

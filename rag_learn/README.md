# rag_learn —— 第 3 阶段：RAG 入门

> 路线：**先手搓最小 RAG，再用 LangChain + Chroma。**
> 手搓不是为了造轮子，是为了让框架替你做了什么变得可见。

## 环境

```bash
cd rag_learn
.\.venv\Scripts\python.exe -X utf8 01_load_documents.py
```

- Python 3.12 / 独立 venv（`llm_learn/.venv` 保持干净）
- 依赖清单：`requirements.txt`（直接依赖，带版本号）；完整锁定：`requirements.lock.txt`（112 个包）
- 手搓阶段：`httpx`、`python-dotenv`、`pypdf`
- 框架阶段（Day3 起）：`chromadb` **1.5.9**、`langchain` **1.4.2**、`langchain-core` **1.6.3**、`langchain-community` 0.4.2、`langchain-chroma` 1.1.0、`langchain-openai` 1.6.2
- 密钥复用 `llm_learn/.env` 的同一套（`LLM_*` 对话 / `EMB_*` 向量）

> ⚠️ **版本提醒**：LangChain 已经是 1.x，而网上教程（含阶段计划里那条 `python.langchain.com/docs/tutorials/rag/`）大量还是 0.2/0.3 的写法，`langchain.chains`、`RetrievalQA` 这类类名在 1.x 里已搬家或改名。**报 `ImportError` 先怀疑版本，别怀疑自己。**

> 📏 **实测约束**：智谱 `embedding-3` **单次请求最多 64 条文本**（第 65 条直接 400 `input数组最大不得超过64条`）；单条 5100 字符没问题。所以批量向量化必须自己分批。

## 文件

| 文件 | 说明 |
|---|---|
| `00_env_check.py` | 开工探针：两组密钥 / 两个接口 / 素材文件是否就绪 |
| `WALKTHROUGH_day1.md` | **卡住时看这份**：Day1 两个函数的填空版 + 报错对照表 |
| `solutions/` | 参考答案（**先自己写完再看**），只放 `01` |
| `fetch_docs.py` | 工具脚本：把**入门级**官方文档抓到 `docs/` |
| `docs/` | 本地文档：01 语义搜索引擎（⭐入门首选）/ 02 检索与RAG架构 / 03 快速开始 / 90 进阶（第4-5阶段再看） |
| `官方代码解读_FullCode.md` | 逐段解读你复制的官方 `Full code.py`（含 import 问题实测诊断） |
| `Full code.py` | 你从官方文档复制来的进阶示例 |
| `01_load_documents.py` | Day1：加载 TXT / PDF（RAG 第 1 步） |
| `02_split_text.py` | Day2：自己写分块器（固定长度 / 重叠） |
| `03_vector_store.py` | Day3：批量向量化 + 自建向量库 + Chroma 对照 |
| `04_rag_chain.py` | Day4：完整 RAG 链（检索→拼接→生成）+ 纯 LLM 对照 + LCEL 对照 |
| `make_sample_pdf.py` | 工具脚本：从 vault 的大 PDF 裁 20 页当素材 |
| `tool.py` | 从 `llm_learn/tool.py` 复制：`chat` / `stream_chat` / `get_embedding` |
| `data/rag_intro.txt` | 素材：RAG 是什么（之后被检索的就是它） |
| `data/agent_notes.txt` | 素材：第 2 阶段的 Agent/工具调用笔记 |
| `data/sample20.pdf` | 素材：本地生成，不进 git |

## RAG 七步

```
离线索引：1 加载 → 2 分块 → 3 向量化 → 4 存库
在线查询：5 检索 → 6 拼接 → 7 生成
```

## 七天路线（在阶段计划基础上改成"手搓优先"）

阶段计划原本是直接用 LangChain。这里改成**先手搓、后上框架**，顺序不变但内脏先看清：

| Day | 手搓部分 | 引入框架/工具 |
|---|---|---|
| 1 | 加载 TXT / PDF（`pypdf`） | — |
| 2 | 自己写分块器（固定长度 / 重叠 / 边界） | — |
| 3 | 自己写向量库（内存 + 存成文件） | **Chroma** 对照 |
| 4 | 手搓完整 RAG 链（检索→拼接→生成） | **LangChain + LCEL** 对照 |
| 5 | 检索优化：top_k 对比 / 查询改写（MultiQuery） | LangChain Retrievers |
| 6 | 对话式 RAG：多轮 + 历史 + 查询重写 | ChatHistory |
| 7 | 综合项目：PDF 知识库问答 | LangChain + Chroma + FastAPI |

*进度：Day 1（进行中）*

## 🧪 开工前实测记录（助教先跑，避免学生踩）

| 结论 | 证据 |
|---|---|
| 智谱 `embedding-3` 单次 **≤ 64 条** | `n=64`→200；`n=65`→400 `input数组最大不得超过64条` |
| 单条 5100 字符没问题 | HTTP 200，2048 维 |
| **Chroma 默认距离是 l2，不是余弦** | 同一条 query，默认库 `dist=0.9180`；`hnsw:space=cosine` 库 `dist=0.4590`（= 1 − 0.5410） |
| 智谱向量**已归一化**，所以 l2 与余弦**排序碰巧一致** | `l2² = 2 − 2cos`：`0.918 ≈ 2 − 2×0.541` 对得上；换不归一化的模型两者就会分家 |
| LangChain 的 `Chroma` 包装**也默认 l2** | `similarity_search_with_score` 返回 `0.9180`，是**距离**（越小越像），名字里的 score 会骗人 |
| PDF 素材有"空页" | 第 5、6 页 `extract_text()` 只有 78 / 84 字符（图/表页），分块后要过滤 |
| **`langchain.chains` 在 1.x 里已不存在** | `from langchain.chains import RetrievalQA` → `ModuleNotFoundError: No module named 'langchain.chains'` |
| `ChatOpenAI` 指向 DeepSeek 端点可用 | `base_url=https://api.deepseek.com/v1` → `content='收到'`；LCEL `prompt \| llm \| StrOutputParser()` 正常 |
| 推理 token 在框架里仍可见 | `usage_metadata.output_token_details = {'reasoning': 14}` |
| 完整 RAG 链接地有效 | 问"今天天气"（资料外）→ 答"资料里没有提到" |
| **阶段计划里那条 RAG 教程链接已重定向** | `python.langchain.com/docs/tutorials/rag/` → 302 → `docs.langchain.com/oss/python/deepagents/rag`（**进阶版**，标题变成 "RAG with Deep Agents"） |
| 官方**入门**教程用的就是 `pypdf` | `docs/01_语义搜索引擎.md` 的 `load_pdf_pages` 与 Day1 手写版**几乎逐行相同**（含 `extract_text() or ""` 和 `metadata={"page": i}`） |
| 官方文档也承认分数是"距离" | 原文："the score is a distance metric that varies inversely with similarity" —— 与 Chroma 实测一致 |

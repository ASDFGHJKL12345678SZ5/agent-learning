# LLM 学习项目（第 2 阶段）

> **从"手搓一次 HTTP 请求"，到做出一个带工具调用和跨会话记忆的智能助手。**
>
> 全程**不使用任何 LLM SDK** —— 所有请求都是自己拼 HTTP 发的。

---

## 🎯 主程序：`assistant.py`

一个能用的命令行智能助手：

```
用户: 我在杭州工作，我叫小明
  ↳ 调用工具 update_profile({"key": "name", "value": "小明"})
  ↳ 调用工具 update_profile({"key": "city", "value": "杭州"})
助手: 好的，小明！已经记下你在杭州工作。

用户: 今天天气怎么样？
  ↳ 调用工具 get_weather({"location": "杭州"})      ← 用户没说城市
助手: 杭州今天多云，气温约 24°C，没有降雨，出门不用带伞。

用户: 帮我算 1234 * 5678
  ↳ 调用工具 calculator({"expression": "1234*5678"})
助手: 1234 × 5678 = 7006652
```

**四个能力：**
| 能力 | 说明 |
|---|---|
| **多轮对话** | `messages` 数组累积，LLM 本身无状态，每轮把完整历史发过去 |
| **流式输出** | SSE 边生成边打印 |
| **工具调用** | 模型请求 → 解析 → 执行 → 回传，支持链式调用 |
| **用户档案** | 模型自己决定记录什么，跨会话持久化 |

---

## 🚀 快速开始

```bash
cd llm_learn

# 1. 建虚拟环境（Python 3.12+）
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # macOS / Linux

# 2. 装依赖（只有两个第三方包）
pip install httpx python-dotenv

# 3. 配密钥
copy .env.example .env            # 然后填进你自己的 key

# 4. 跑
.\.venv\Scripts\python.exe -X utf8 assistant.py
```

> ⚠️ **`-X utf8` 在 Windows 上建议加上** —— 否则中文输出可能乱码。

### `.env` 需要什么

```bash
# ============ LLM（本项目的对话/工具调用用这家）============
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-你的key
LLM_MODEL=deepseek-flash

# ============ Embedding（可选，只有 10_embedding.py 用）============
EMB_BASE_URL=https://open.bigmodel.cn/api/paas/v4
EMB_API_KEY=你的智谱key
EMB_MODEL=embedding-3
```

> ⭐ **两家供应商、两套前缀（`LLM_` / `EMB_`）** —— 见下面「设计要点 2」。

---

## 📁 文件说明

### 核心

| 文件 | 行数 | 是什么 |
|---|---|---|
| ⭐ **`assistant.py`** | 275 | **主程序**：多轮 + 流式 + 工具 + 档案 |
| **`tool.py`** | 254 | 工具库：`chat` / `stream_chat` / `get_embedding` 等 |
| `chat_cli.py` | 120 | 早一版：只有多轮 + 流式 + 持久化 |

### 实验脚本（每个都对应一个具体结论）

| 文件 | 实验内容 |
|---|---|
| `00_list_models.py` | 列可用模型（**别猜模型名，让服务器说**） |
| `01_raw_http.py` | **手搓 HTTP** 调 LLM，看清请求/响应全貌 |
| `02_temperature.py` | 温度对照实验（4 组 × 5 次） |
| `03_prompt_basics.py` | 提示工程四连：零样本/少样本/角色/JSON |
| `04_boundary.py` | 计算能力边界（12 题自动判分） |
| `05_stream_vs_not.py` | 流式 vs 非流式耗时对比 |
| `06_xml_prompt.py` | XML 标签组织长 Prompt 对照实验 |
| `07_hallucination.py` | 幻觉实验（三组对照） |
| `08_what_is_arguments.py` | **离线**讲清 `arguments` 为什么是字符串 |
| `09_function_calling.py` | Function Calling 完整循环 |
| `10_embedding.py` | Embedding：转向量 / 余弦相似度 / 语义搜索 |

### 运行时生成（**已在 `.gitignore` 里**）

| 文件 | 内容 |
|---|---|
| `assistant_history.json` | 对话历史 |
| `user_profile.json` | ⚠️ **用户档案（含个人信息）** |
| `chat_history.json` | 旧版历史 |

---

## ⭐ 设计要点（这个项目真正的价值）

### 1. 不使用 SDK，全程手搓 HTTP

`requests`／`openai` 之类的库会把请求和响应**包起来**。而用裸 `httpx` 的好处是：

- **看得到原始 JSON** —— 本项目的所有发现（`arguments` 是字符串、`tool_calls` 是列表、`reasoning_tokens` 占比）**全都来自看原始响应**
- **读得懂任何厂商的文档** —— 官方给的 `curl` 示例能直接翻译成代码：`-H` → `headers`，`-d` → `json=`

### 2. 供应商可插拔

**聊天用 DeepSeek，向量用智谱** —— 两家不同的公司，靠环境变量前缀隔离：

```python
LLM_BASE_URL / LLM_API_KEY / LLM_MODEL      # 对话
EMB_BASE_URL / EMB_API_KEY / EMB_MODEL      # 向量
```

**换供应商 = 改 3 行 `.env`，代码一行不动。**

> 实测：DeepSeek **没有** Embedding 接口（`/embeddings` 返回 404），
> 所以向量部分换成了智谱 —— **这个"换"本身就是设计要支持的场景。**

### 3. ⭐ 流式 + 工具调用（本项目最难的一块）

**非流式和流式，在 `tool_calls` 上是两个世界：**

| | 非流式 `chat()` | 流式 `stream_chat()` |
|---|---|---|
| `tool_calls` 怎么来 | 一次性完整 | **被切成碎片，一块块推来** |
| 怎么拿 | `msg["tool_calls"]` | **按 `index` 累积拼接** |

**流式下的碎片长这样（`arguments` 被切成了 4 段）：**

```
data: {"delta":{"tool_calls":[{"index":0,"id":"call_xxx","function":{"name":"get_weather","arguments":""}}]}}
data: {"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"loc"}}]}}
data: {"delta":{"tool_calls":[{"index":0,"function":{"arguments":"ation\": \"杭"}}]}}
data: {"delta":{"tool_calls":[{"index":0,"function":{"arguments":"州\"}"}}]}}
```

**`stream_chat(..., capture={})` 帮你把它们拼好，并且形状和 `chat()` 完全一致** ——
所以 `execute_tool(tc)` 两边通用，不用写两套代码。

### 4. 完整的 Tool Calling 循环

```python
while True:                                   # 内层循环
    capture = {}
    reply = stream_chat(context, tools=TOOLS, capture=capture)
    if not capture.get("tool_calls"):
        break                                 # 模型不再请求工具 → 收工
    # 执行工具、回传，然后转回去再问一次
```

**支持链式调用** —— 比如"查明天天气，如果下雨就算一下打车费"这种
**第二步依赖第一步结果**的任务。

### 5. 用户档案 = 动态 system prompt + 持久化

```python
while True:
    context[0] = {"role": "system", "content": build_system_prompt()}   # 每轮重建
```

**system prompt 不是"一次写好就不动"，而是每轮动态生成的** ——
真实 Agent 的 system prompt 里塞的东西（工具列表、记忆、时间、档案）全是动态拼的。

**为什么不用向量检索？** 实测发现：纯语义检索**捞不准**。

```
查询：今天天气怎么样？
  第1名  +0.4499   我叫小明              ← 完全不相关
  第4名  +0.4044   我在杭州工作          ← 真正需要的那条，top_k=3 捞不到
```

> **「语义相似」≠「有用」。** 所以稳定信息（名字、城市）**固定塞进 system prompt**，不靠检索。

### 6. 🔒 安全：模型给的东西不可信

`calculator` 工具的 `expression` 参数**来自模型**，而模型**可能被提示注入影响**。
直接 `eval()` = 让模型在你的机器上执行任意代码。

**解法：用 `ast` 解析成语法树，只放行数字和四则运算。**

```python
safe_eval("23*47+8")                    # → 1089 ✅
safe_eval("__import__('os').system('dir')")   # → ValueError: 不允许的内容：Call ✅
```

**推而广之：`arguments` 里的内容，和 `input()` 拿到的用户输入一样不可信 —— 甚至更不可信。**

---

## 🧪 几个实测结论

> 下面这些**教科书基本不讲**，都是跑出来的。

| 结论 | 怎么测出来的 |
|---|---|
| **`temperature=0` 不保证可复现** | 同 prompt 跑 5 次，输出不同 |
| **推理模型 80% 的输出 token 是看不见的思考** | `usage.completion_tokens_details.reasoning_tokens` |
| **流式不缩短总时间，只改变 TTFT** | 流式/非流式各跑 2 次对比 |
| **单次性能对比毫无意义** | 同一实验两次结果相反（思考 token 波动 5 倍） |
| **结构化提示的价值不在"准确率"** | XML vs 平铺对照，准确率一样，价值在可维护性 |
| **幻觉不是"模型不会"，是提示词要求它编** | 加一句"所有字段必填"→ 模型编出价格 1999、库存 500 |
| **schema 里写不存在的必填字段 → 模型会编** | `required:["nothing"]` → 返回 `{"nothing":"nothing"}` |

---

## 🐛 踩过的坑（选）

| 坑 | 教训 |
|---|---|
| 相对路径相对于 **CWD**，不是脚本位置 | 用 `os.path.dirname(os.path.abspath(__file__))` |
| **中文全角逗号** `，` | JSON/Python 都不认，**比缺逗号更隐蔽** |
| `json.loads()` 通过 ≠ 符合你的 schema | 合法 JSON 可能是**空值、类型错、多字段、内容是编的** |
| 流式下 `tool_calls` 是碎片 | 要按 `index` 累积 |
| 推理模型的 `reasoning_content` 必须回传 | 手工构造 assistant 消息时会踩 |
| `USER_PROFILE.update(...)` ≠ `USER_PROFILE = ...` | 模块级共享 dict 要用"改内容"不是"换指向" |

---

## 📌 环境

- **Python** 3.12
- **第三方依赖**：只有 `httpx` 和 `python-dotenv`
- **LLM**：DeepSeek（`deepseek-flash`）
- **Embedding**：智谱（`embedding-3`，2048 维）

---

*第 2 阶段产出 · 2026-09*

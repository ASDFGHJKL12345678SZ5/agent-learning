"""第2阶段 Day2 · tool.py —— 把那门课里的"工具包"，我们自己撸一个。

【先澄清一件事】
Anthropic / 吴恩达那门 Prompt Engineering 教程，每个 notebook 第一行都写着：
        from tool import get_completion
很多人第一反应是：这是个要 pip install 的第三方包吧？

不是。它只是课程仓库里一个叫 tool.py 的**普通文件**，和 notebook 放在同一个文件夹。
Python 执行 import 时的查找顺序是：
    ① 当前脚本所在目录        ← tool.py 就是在这里被找到的
    ② 环境变量 PYTHONPATH 里的目录
    ③ site-packages（pip 装的东西都在这）
所以 `from tool import get_completion` = "把隔壁那个 tool.py 里的 get_completion 拿过来用"。
它和 `import os`、`import httpx` 在语法上一模一样，区别只在"从哪找"。

【你现在的位置】
你 Day1 已经用 httpx 手搓过一次裸请求（01_raw_http.py）。
get_completion 干的事，和你昨天写的那段代码**完全一样**，只是被包成了函数：
    你给它一句 prompt（字符串），它还你一段正文（字符串）。
所以对你来说它不是黑盒 —— 它是你昨天代码的"函数化"。

【新语法提示】
- `def f(a, b=0)`   → b 有默认值，调用时可以不传（第1阶段学过的默认参数）
- `-> str`          → 类型注解，只是给人和编辑器看的，Python 运行时不管（新语法，记住它不影响运行）
- 三个双引号包起来的那段 → docstring（函数的说明书），用 help(函数名) 能打出来
"""

import json                      # 标准库：解析流式返回的每一小块
import os
import time                      # 标准库：给流式做计时（量首字延迟）

import httpx                     # 第三方库：发 HTTP 请求
from dotenv import load_dotenv   # 第三方库：把 .env 读进环境变量

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

# ---------- Embedding 供应商（和上面的 LLM 分开配置）----------
# ⭐ 为什么用不同前缀？
#    因为这是【两家不同的公司】：聊天用 DeepSeek，向量用智谱。
#    它们的地址、密钥、模型名完全不同。
#    用 LLM_ / EMB_ 两个前缀隔开，谁也不会覆盖谁。
EMB_BASE_URL = os.getenv("EMB_BASE_URL")
EMB_API_KEY = os.getenv("EMB_API_KEY")
EMB_MODEL = os.getenv("EMB_MODEL")


def chat(messages: list, temperature: float = 0, model: str | None = None,
         verbose: bool = False,tools :list | None=None) -> dict:
    """最底层的一个函数：给 messages 列表，返回服务器返回的**完整 dict**。

    什么时候用它？当你要看正文以外的字段时（usage 花了多少 token、
    推理模型的 reasoning_content、logprobs 概率分布……）。
    """
    if not API_KEY or not BASE_URL:
        raise SystemExit("❌ 没读到环境变量。检查 .env 是不是和本文件同目录、键名有没有拼错")

    url = f"{BASE_URL}/chat/completions"

    headers = {
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "model": model or MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        payload["tools"]=tools

    resp = httpx.post(url, headers=headers, json=payload, timeout=120)

    if resp.status_code != 200:
        print("❌ 请求失败，服务器原话是：")
        print(resp.text)
        raise SystemExit(1)

    # 将服务器返回的 JSON 响应解析成 Python 字典（通常包含 choices、usage 等字段）。
    data = resp.json()

    if verbose:
        print(f"[用了 {data['usage']['total_tokens']} tokens]")

    return data


def get_embedding(text: str | list[str], model: str | None = None) -> list:
    """把文本变成向量（Embedding）。

    ⚠️ 和 chat() 相比，只有【三处】不一样：
        路径：     /embeddings              （不是 /chat/completions）
        请求字段：  input                    （不是 messages）
        取值：     data[0]["embedding"]     （不是 choices[0].message.content）
    鉴权头、httpx.post 的写法 —— 【完全一样】。

    传一个字符串     → 返回一个向量   list[float]      例如 [0.0123, -0.0456, ...]
    传一个字符串列表 → 返回一组向量   list[list[float]]
    """
    if not EMB_BASE_URL or not EMB_API_KEY:
        raise SystemExit(
            "❌ 没读到 EMB_* 环境变量。\n"
            "   检查 .env 里有没有这三行：EMB_BASE_URL / EMB_API_KEY / EMB_MODEL"
        )

    url = f"{EMB_BASE_URL}/embeddings"
    headers = {
        "Authorization": "Bearer " + EMB_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or EMB_MODEL,
        "input": text,
    }

    resp = httpx.post(url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        print("❌ 请求失败，服务器原话是：")
        print(resp.text)
        raise SystemExit(1)

    data = resp.json()

    # 响应形状：{"data": [{"embedding": [...], "index": 0}, ...], "usage": {...}}
    vectors = [item["embedding"] for item in data["data"]]

    return vectors[0] if isinstance(text, str) else vectors


def stream_chat(messages: list, temperature: float = 0, model: str | None = None,
                show_reasoning: bool = False, timing: dict | None = None,
                tools: list | None = None, capture: dict | None = None) -> str:
    """流式版：边生成边打印，实时看到文字一个个往外蹦。

    【和 chat() 的区别】
    chat()        等服务器把整段答案生成完，一次性拿回来 —— 这中间你什么都看不到
    stream_chat() 服务器每生成一两个 token 就推一小块，你边收边打印 —— 有字就说明活着

    【协议是什么】
    这叫 SSE（Server-Sent Events）。服务器吐出来的长这样，一行一块：

        data: {"choices":[{"delta":{"content":"艾"}}]}
        data: {"choices":[{"delta":{"content":"尔"}}]}
        data: [DONE]

    所以解析工作就是三件事：剥掉行首的 "data: " → 判断是不是 [DONE] → 剩下的当 JSON 解析。
    注意：是 delta（增量/这一小块），不是 message（完整消息）—— 这是流式和非流式最大的区别。

    【show_reasoning=True 会怎样】
    推理模型（deepseek-flash）的思考过程也会一起流出来。
    打开它，你能亲眼看到模型"想"的过程，也就能直观感受"思考 token 越多越慢越贵"。

    【timing 是干嘛的】
    传一个空 dict 进来，函数会把两个数字塞进去：
        timing["ttft"]  → 首字延迟：从发出请求，到看见第一个正文字符，隔了多少秒
        timing["total"] → 总耗时
    这两个数就是流式最值钱的指标 —— 05_stream_vs_not.py 靠它做对比。

    【tools 和 capture —— 流式下怎么用工具？】
    传了 tools，模型才可能返回 tool_calls。但流式下它是【碎片】，不能直接读。

    传一个空 dict 给 capture，函数会把这些塞进去：
        capture["tool_calls"]    拼好的工具调用列表（可能为空）
        capture["assistant_msg"] 一条可以【原样 append 进 messages】的 assistant 消息
                                  （只有当真的请求了工具时才有）
    """
    if not API_KEY or not BASE_URL:
        raise SystemExit("❌ 没读到环境变量。检查 .env 是不是和本文件同目录、键名有没有拼错")

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": True,          # ← 唯一的区别：告诉服务器"别攒着，有了就给我"
    }
    if tools:
        payload["tools"] = tools

    full_text = []
    in_reasoning = False
    # 流式下 tool_calls 是【碎片】：id 只在第一块出现，name 可能分几块，
    # arguments 会被切成很多小段。所以要按 index 一点点拼起来。
    tool_acc = {}                # index -> {"id":..., "name":..., "arguments":...}

    # ---------- 计时：量两个关键指标 ----------
    # t0       请求发出的时刻
    # first_at 第一个【正文】字符到达的时刻  → 两者之差就是 TTFT（首字延迟）
    t0 = time.perf_counter()
    first_at = None
    if timing is None:
        timing = {}

    # httpx.stream 而不是 httpx.post：前者不把响应读完，而是让你一行一行地取
    # with 会自动管理这个流：进入代码块时打开连接，离开时自动关闭连接，
    # 即使中途报错也会清理资源；as resp 表示把流对象命名为 resp。
    with httpx.stream("POST", url, headers=headers, json=payload, timeout=120) as resp:
        if resp.status_code != 200:
            print("❌ 请求失败，服务器原话是：")
            print(resp.read().decode("utf-8", errors="replace"))
            raise SystemExit(1)

        for line in resp.iter_lines():
            if not line or not line.startswith("data: "):
                continue                     # 空行和注释行直接跳过
            chunk_text = line[6:]            # 剥掉行首的 "data: "
            if chunk_text.strip() == "[DONE]":   # 服务器说"我说完了"
                break

            chunk = json.loads(chunk_text)

            # 有些服务会在最后一块里捎带用量信息（非流式是一定有的）
            if chunk.get("usage"):
                timing["usage"] = chunk["usage"]

            delta = chunk["choices"][0].get("delta", {})

            # ---------- 累积 tool_calls 碎片（流式专用的处理）----------
            for tc_delta in (delta.get("tool_calls") or []):
                idx = tc_delta.get("index", 0)
                slot = tool_acc.setdefault(
                    idx, {"id": "", "name": "", "arguments": ""})
                if tc_delta.get("id"):
                    slot["id"] = tc_delta["id"]          # id 只出现一次
                fn = tc_delta.get("function") or {}
                if fn.get("name"):
                    slot["name"] += fn["name"]           # 可能分几块
                if fn.get("arguments"):
                    slot["arguments"] += fn["arguments"] # 被切成很多小段

            # 推理模型的思考过程（普通模型没有这个字段）
            if show_reasoning and delta.get("reasoning_content"):
                if not in_reasoning:
                    print("\n\033[90m[思考中] ", end="", flush=True)
                    in_reasoning = True
                print(delta["reasoning_content"], end="", flush=True)

            # 正式回答
            if delta.get("content"):
                if in_reasoning:
                    print("\033[0m\n[正文] ", end="", flush=True)
                    in_reasoning = False
                print(delta["content"], end="", flush=True)
                full_text.append(delta["content"])

                if first_at is None:              # 记下"第一个正文字符"到达的时刻
                    first_at = time.perf_counter()
                    timing["ttft"] = first_at - t0

    print()   # 收尾换行
    timing["total"] = time.perf_counter() - t0

    # ---------- 把拼好的工具调用交出去 ----------
    if capture is not None:
        ordered = [tool_acc[i] for i in sorted(tool_acc)]
        # ⭐ 转成和 chat() 返回的 tool_calls【完全一样的形状】：
        #    {"id":..., "type":"function", "function": {"name":..., "arguments":...}}
        #    这样 execute_tool(tc) 可以直接拿来用，不用为流式写第二套代码。
        standard = [
            {
                "id": t["id"],
                "type": "function",
                "function": {"name": t["name"], "arguments": t["arguments"]},
            }
            for t in ordered
        ]
        capture["tool_calls"] = standard
        if standard:
            # 这就是【可以原样 append 进 messages】的那条 assistant 消息
            capture["assistant_msg"] = {
                "role": "assistant",
                "content": "".join(full_text),
                "tool_calls": standard,
            }
            
    return "".join(full_text)


def get_completion(prompt: str, temperature: float = 0,
                   model: str | None = None, verbose: bool = False) -> str:
    """课程里那个同名函数：给一句 prompt（字符串），只还你正文（字符串）。

    它内部只做了两件事：
      1) 把你的一句话包成 messages 列表  [{"role": "user", "content": prompt}]
      2) 从返回的 dict 里，把最深处那层正文挖出来
    """
    data = chat([{"role": "user", "content": prompt}],
                temperature=temperature, model=model, verbose=verbose)
    return data["choices"][0]["message"]["content"]


def get_completion_from_messages(messages: list, temperature: float = 0,
                                 model: str | None = None,
                                 verbose: bool = False) -> str:
    """同上，但允许你自己传整个 messages 列表（多轮对话、system 角色设定要用它）。"""
    data = chat(messages, temperature=temperature, model=model, verbose=verbose)
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # 自检：能打印出内容，就说明这个"工具包"装好了
    print(">>> 正在调用", MODEL, "...\n")
    print(get_completion("用一句话介绍你自己。", verbose=True))

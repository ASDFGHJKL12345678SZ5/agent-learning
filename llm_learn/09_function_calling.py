"""第2阶段 Day5 · 09_function_calling.py —— Function Calling（工具调用）

【任务】（来自你的计划表）
    ✅ 定义 3 个工具函数 + JSON Schema：天气查询（模拟）/ 计算器 / 日期查询
    ✅ 让 LLM 选择调用哪个工具
    ✅ 实现完整 Tool Calling 循环：LLM 请求 → 解析 tool_calls → 执行 → 回传

【先读这个】08_what_is_arguments.py（离线，不用 API）
    它讲清了一件事：arguments 是【字符串】，不是 dict。

【⭐ 全篇最重要的一条规律】
    ┌────────────────────────────────────────────────────────┐
    │  协议里流动的永远是【文字】                              │
    │                                                        │
    │  进来：arguments  str  --json.loads()-->  dict  → 你的函数 │
    │  出去：结果       dict --json.dumps()-->  str   → 回传模型 │
    │                                                        │
    │  进去要【拆包】，出来要【打包】—— 两边都是你在干活。      │
    │  json.dumps()：把 Python 对象（如 dict）序列化成 JSON 字符串，│
    │  方便按协议作为消息内容传给模型；不是把数据写入文件。       │
    └────────────────────────────────────────────────────────┘

【验收标准】
    ① 能画出完整的 Tool Calling 流程图（含"不调用工具"的分支）
    ② 程序能自己决定调哪个工具、并对多个工具都跑通

【运行】
    python 09_function_calling.py
"""

import ast
import json
import operator
from datetime import datetime

from tool import chat


# ============================================================
# 安全工具（我写好了，你直接用）—— 但请读懂它为什么存在
# ============================================================
# ⚠️⚠️ 为什么不能直接用 eval() 算模型给的表达式？
#
#   因为 expression 是【模型生成的字符串】。
#   而模型可能被【提示注入】影响 —— 用户可以在对话里诱导它输出恶意内容。
#   一旦你 eval(...) 了它，就等于【让模型在你的机器上执行任意代码】。
#
#   比如模型返回的表达式可能是：
#       __import__('os').system('rm -rf /')     ← 这不是数学，这是删库
#
#   所以：只解析成语法树，只放行【数字】和【算术运算符】，其他一律拒绝。
_ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def safe_eval(expression: str) -> float:
    """只允许「数字 + 四则运算」的表达式求值；其他任何东西都抛异常。"""
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"表达式里有不允许的内容：{type(node).__name__}")

    return _eval(ast.parse(expression, mode="eval"))


# ============================================================
# ★ 第 1 步：写 3 个【普通 Python 函数】
# ============================================================
# ⚠️ 先别管 LLM。这三个就是普通函数，你要能【单独调用它们】。
#    写完先在 __main__ 里手动调一下，确认它们各自能跑通。

FAKE_WEATHER={
    "杭州":{"temp":24,"desc":"多云","rain":False},
    "北京":{"temp":30,"desc":"晴天","rain":False},
    "上海":{"temp":28,"desc":"小雨","rain":True},
}

def get_weather(location: str) -> dict:
   
    if location not in FAKE_WEATHER:
        return {"error": f"没有 {location} 的天气数据", "available Locations": list(FAKE_WEATHER.keys())}
            
    return FAKE_WEATHER[location]

    

def calculator(expression: str) -> float:
  
    return safe_eval(expression)


def get_date() -> str:

   return datetime.now().date().isoformat()


# ============================================================
# ★ 第 2 步：给 3 个函数写 JSON Schema（"说明书"）
# ============================================================
# ⭐ 这是模型【唯一】能看到的关于你函数的信息。
#    尤其是 description —— 模型靠它决定"要不要调这个工具"。
#
#    写 description 的要点：写【什么时候用】，不只写【是什么】。
#    ❌ "查询天气"                    → 太含糊
#    ✅ "查询某个城市的当前天气。当用户询问天气、温度、要不要带伞时使用。"
#
#    第一个我写好了当范例，后两个你来。

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市的当前天气。当用户询问天气、温度、是否下雨、要不要带伞时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名，例如 杭州、北京",
                    }
                },
                "required": ["location"],
            },
        },
    },

   {
       "type": "function",
         "function": { 
             "name": "calculator",
                "description": "计算一个数学表达式的值。当用户询问数学计算、算式结果时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，例如 23*47+8",  
                        }
                    },
                    "required": ["expression"],
                },
            },
        },


    {
        "type": "function",
        "function": {
            "name": "get_date",
            "description": "查询今天的日期。当用户询问今天几号、日期时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
    # ★ TODO(第2步)：加 get_date 的 schema
    #   提示：⭐ 这个函数【不需要任何参数】——
    #        那 parameters 该怎么写？没有参数时 "required" 写什么？
    #        （想一下：properties 是空对象 {} 行不行？）
]


# ============================================================
# 调试助手（我写好了）—— 让你看清模型返回了什么
# ============================================================
def show_message(msg: dict) -> None:
    """打印模型返回的 message：有 tool_calls 就显示工具请求，没有就显示正文。"""
    if msg.get("tool_calls"):
        print(f"  🔧 模型请求调用 {len(msg['tool_calls'])} 个工具：")
        for tc in msg["tool_calls"]:
            fn = tc["function"]
            print(f"     - id       = {tc['id']}")
            print(f"       name     = {fn['name']}")
            print(f"       arguments= {fn['arguments']!r}   ← 注意类型"
                  f"（{type(fn['arguments']).__name__}）")
    else:
        print(f"  💬 模型没调工具，直接回答：{msg.get('content')}")

TOOL_FUNCTIONS={
    "get_weather": get_weather,
    "calculator": calculator,
    "get_date": get_date
}

def execute_tool(tc:dict)->dict:
    """解析 tool_call，按 name 分发到对应函数执行，返回结果 dict。"""
    name=tc["function"]["name"]
    args=json.loads(tc["function"]["arguments"])
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"未知的工具函数名：{name}")

    result = TOOL_FUNCTIONS[name](**args)

    # ⭐ 打包：结果必须是字符串才能放进 content
    if isinstance(result, str):
        return result                          # get_date 这种，本来就是 str
    return json.dumps(result, ensure_ascii=False)   # dict / float → JSON 文本
# ============================================================
# ★ 第 3~6 步：主流程
# ============================================================
def main():
    # ────────────────────────────────────────────────────
    # 【第 3 步】单轮：把问题 + TOOLS 发给模型，看它返回什么
    # ────────────────────────────────────────────────────
    # 就 3 行：
    #   ① messages = [{"role": "user", "content": "杭州今天天气怎么样？"}]
    #   ② resp = chat(messages, tools=TOOLS)      ← ⭐ 别忘了 tools=
    #   ③ msg = resp["choices"][0]["message"]，然后 show_message(msg)
    #
    # 💡 先用这几个问题各试一次，看模型的"选择"：
    #       "杭州今天天气怎么样？"        → 应该选 get_weather
    #       "帮我算 23*47+8"              → 应该选 calculator
    #       "今天几号？"                  → 应该选 get_date
    #       "讲个笑话"                    → ⭐ 应该【一个都不选】
    #    这一步只观察，先别执行工具。
    #
    # ★ TODO(第3步)

    messages=[{"role":"user","content":"杭州今天天气怎么样？"}]
    resp=chat(messages,tools=TOOLS)
    msg=resp["choices"][0]["message"]
    show_message(msg)

    # ────────────────────────────────────────────────────
    # 【第 4 步】解析 arguments → 按 name 分发 → 真的执行函数
    # ────────────────────────────────────────────────────
    # 要写的是一个【分发器】：
    #   ① json.loads(tc["function"]["arguments"])   ← str → dict ⭐ 拆包
    #   ② 按 tc["function"]["name"] 找到对应的 Python 函数
    #   ③ 用 **args 调用它，拿到结果
    #
    # 💡 怎么"按名字找函数"？两种写法：
    #    A) if/elif 一串判断
    #    B) 建一个 {函数名: 函数对象} 的字典，然后 字典[name](**args)
    #    ⭐ B 更好 —— 以后加第 4、第 5 个工具，不用改分发逻辑。
    #      这正是"工具注册表"的雏形，也是真实 Agent 框架的做法。
    #
    # ★ TODO(第4步)
    # 假设我们有一个函数字典
    # 根据函数名调用对应的函数



    # ────────────────────────────────────────────────────
    # 【第 5 步】把结果回传，拿最终自然语言回答
    # ────────────────────────────────────────────────────
    # ⚠️ 两件事千万别忘：
    #   ① 先把模型的【工具请求】那条 message 也 append 进 messages
    #      —— 不然回传的 tool 消息配不上对（tool_call_id 找不到请求方）
    #   ② 回传的消息格式：
    #        {"role": "tool", "tool_call_id": tc["id"], "content": ???}
    #      ⚠️ content 必须是【字符串】！
    #         你的函数返回的是 dict → 要 json.dumps 打包
    #         （⭐ 这就是"出去要打包"，和 arguments 是反方向）
    #
    # 然后再调一次 chat(messages, tools=TOOLS)，这次模型会给正文。
    #
    # ★ TODO(第5步)
    # ── 第 5 步 ────────────────────────────────────────
    if msg.get("tool_calls"):                     # ① 先判断：模型要调工具吗？

        messages.append(msg)                      # ② 把【工具请求】也记进历史
                                              #    忘了这行 → tool_call_id 配不上对

        for tc in msg["tool_calls"]:              # ③ 可能不止一个，要循环

            result = execute_tool(tc)             # ④ 调你写好的分发器

            messages.append({                     # ⑤ 回传
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result,
        })

        resp2 = chat(messages, tools=TOOLS)       # ⑥ 第二次请求
        print(resp2["choices"][0]["message"]["content"])   # ⑦ 这次才有正文

    else:
        print(msg["content"])                     # 模型没调工具，直接显示

    # ────────────────────────────────────────────────────
    # 【第 6 步】包成循环，变成能连续对话的程序
    # ────────────────────────────────────────────────────
    # 结构和你的 chat_cli.py 一样：while True + input + context 累积
    # 区别：每一轮里可能发生【两次】chat 调用
    #       （第一次拿 tool_calls，第二次拿最终回答）
    #
    # 💡 进阶（选做）：模型可能【一次请求多个工具】，也可能
    #    【执行完工具后又请求工具】。能不能写成 while 循环一直转到
    #    模型不再请求工具为止？那才是真正"完整"的循环。
    #
    # ★ TODO(第6步)

   


if __name__ == "__main__":
    main()

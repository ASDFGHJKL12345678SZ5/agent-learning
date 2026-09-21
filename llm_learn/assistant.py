import json
import os
import ast
import operator
from datetime import datetime

from tool import get_completion_from_messages, stream_chat ,chat  # 非流式 / 流式，都收 messages 列表


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # __file__ = 本脚本的路径
HISTORY_FILE = os.path.join(_SCRIPT_DIR, "assistant_history.json")
PROFILE_FILE = os.path.join(_SCRIPT_DIR, "user_profile.json")   # ← 用户档案单独一个文件

SYSTEM_PROMPT = "你是一个耐心、简洁的助手，回答用中文。"

# 用户输入这些词就退出
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", "再见"}

_ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}

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
            },

    {
    "type": "function",
    "function": {
        "name": "update_profile",
        "description": "存储用户的个人信息，比如姓名，城市，职业，偏好等",          # ★ TODO：这句最重要
        "parameters": {
            "type": "object",
            "properties": {
                "key":   {"type": "string", "description": "用户信息的键，比如 'name', 'city', 'occupation', 'preference' 等"},
                "value": {"type": "string", "description": "用户信息的值，比如 'Alice', 'Beijing', 'Engineer', '喜欢阅读' 等"},
            },
            "required": ["key", "value"],
        },
    },
}
]



FAKE_WEATHER={
    "杭州":{"temp":24,"desc":"多云","rain":False},
    "北京":{"temp":30,"desc":"晴天","rain":False},
    "上海":{"temp":28,"desc":"小雨","rain":True},
}

USER_PROFILE = {}          # 模块级：一个简单的 dict 当档案

def update_profile(key: str, value: str) -> dict:
    """记录用户的稳定信息（名字、城市、职业、偏好）。"""
    # ★ TODO：一行
    #    把 key/value 存进 USER_PROFILE
    #    ⚠️ 想想：这里需要写 global 吗？（提示：你是【修改】dict，不是【重新赋值】）
    USER_PROFILE[key] = value
    return {"ok": True, "profile": USER_PROFILE}


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

def get_weather(location: str) -> dict:
   
    if location not in FAKE_WEATHER:
        return {"error": f"没有 {location} 的天气数据", "available Locations": list(FAKE_WEATHER.keys())}
            
    return FAKE_WEATHER[location]

    

def calculator(expression: str) -> float:
  
    return safe_eval(expression)


def get_date() -> str:

   return datetime.now().date().isoformat()

TOOL_FUNCTIONS={
    "get_weather": get_weather,
    "calculator": calculator,
    "get_date": get_date,
    # ⚠️ 加新工具要改【两处】：TOOLS（告诉模型有哪些）+ 这里（告诉程序怎么执行）
    "update_profile": update_profile,
}


def build_system_prompt() -> str:
    """动态拼出 system prompt —— 把【当前】的用户档案塞进去。"""
    if not USER_PROFILE:
        return SYSTEM_PROMPT
    else:
        return SYSTEM_PROMPT + "\n当前用户档案：" + json.dumps(USER_PROFILE, ensure_ascii=False)
    
def show_context(context):

    roles = " → ".join(m["role"] for m in context)
    print(f"\033[90m[历史共 {len(context)} 条: {roles}]\033[0m")



def save_history(context):
  
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

def load_history():
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # 文件不存在时返回空列表
    except json.JSONDecodeError:
        return []  # JSON 解码错误时也返回空列表


# ============================================================
# 用户档案的持久化（和 save_history 一模一样的套路）
# ============================================================
def save_profile():
    """把 USER_PROFILE 落盘。"""
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_PROFILE, f, ensure_ascii=False, indent=2)


def load_profile() -> dict:
    """启动时读回档案。

    两个兜底（和 load_history 同一个思路）：
      - 文件不存在 → 空 dict（第一次运行当然不存在）
      - 文件内容坏了 / 根本不是个 dict → 也返回空 dict
        ⭐ 这就是"校验"：读回来的东西不能无脑信
    """
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def main():
    # ── 启动时把上次的档案读回来 ──
    # ⚠️ 用 .update()，不要写成 USER_PROFILE = load_profile()
    #    因为 update_profile() 改的是【模块级那个 dict 本身】。
    #    重新赋值会让 main() 里看到的和函数里改的不再是同一个对象。
    USER_PROFILE.update(load_profile())

    context = [{"role": "system", "content": build_system_prompt()}]

    prompt_text = "请问有什么可以帮您的吗？"

    print("=" * 50)
    print("  智能助手   （输入 exit / quit 退出）")
    if USER_PROFILE:
        print(f"  已载入用户档案：{json.dumps(USER_PROFILE, ensure_ascii=False)}")
    print("=" * 50)

   
    try:
        while True:
            context[0] = {"role": "system", "content": build_system_prompt()}  
            show_context(context)
            input_text = input(prompt_text)
            if input_text in EXIT_COMMANDS:
                break
            context.append({"role": "user", "content": input_text})

            print("ChatGPT: ", end="", flush=True)

            # ── ⭐ 内层循环：一直转到模型【不再请求工具】为止 ──
            #    这才是"完整的 Tool Calling 循环"。
            #    它同时解决了之前那个已知边界：
            #    "第 2 次调用又请求工具 → 静默返回空字符串"
            while True:
                capture = {}
                reply = stream_chat(context, tools=TOOLS, capture=capture)

                if not capture.get("tool_calls"):
                    break          # 模型给正文了 → 收工

                # 模型请求了工具：记下请求 → 执行 → 回传 → 转回去再问一次
                context.append(capture["assistant_msg"])
                for tc in capture["tool_calls"]:
                    fn = tc["function"]
                    print(f"\n\033[90m  ↳ 调用工具 {fn['name']}({fn['arguments']})\033[0m")
                    result = execute_tool(tc)
                    context.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                print("ChatGPT: ", end="", flush=True)

            context.append({"role": "assistant", "content": reply})
            prompt_text = "你: " 
            save_history(context) 
            save_profile()          # ← 档案也落盘

    except KeyboardInterrupt:
        print("\n已中断")
    finally:
        save_history(context)  # 确保退出前保存历史
        save_profile()
        print("\n对话已保存，再见！")


if __name__ == "__main__":
    main()

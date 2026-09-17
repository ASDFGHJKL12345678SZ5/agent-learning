"""第2阶段 Day3 · chat_cli.py —— 命令行 ChatGPT

【任务】
    写一个能在终端里聊天的 ChatGPT：
        ✅ 多轮对话（messages 数组累积）
        ✅ 流式输出（stream=True）
        ✅ 保存对话历史到文件
        ✅ 检验：能看懂 Chat API 的 messages 结构

【你已经有的工具】
    tool.py 里的 stream_chat(messages, ...)
        - 收一个 messages 列表
        - 边流式打印到屏幕
        - 【返回】拼好的完整文本
    所以你不用重写任何网络代码。

【已定下的三个设计决策】（你昨天答的）
    ① 历史存 .json      —— 一个完整的数组
    ② 全量重写          —— 每轮把整个 context 重新写一遍（简单、永远一致）
    ③ 分步做            —— 一次写完容易出错，每步跑通再下一步

【⭐ 实施顺序 —— 请不要跳步】
    第 1 步  单轮、非流式、不存文件        ← 现在从这里开始
    第 2 步  加 while + context 累积       ← 多轮对话成了
    第 3 步  换成 stream_chat              ← 流式成了
    第 4 步  加文件保存
    第 5 步  加 /exit + 异常处理

    每一步都是一个【能跑的程序】。跑通再往下。

【运行】
    cd D:\\Desktop\\Practice\\llm_learn
    .\\.venv\\Scripts\\python.exe -X utf8 chat_cli.py
"""

import json
import os

from tool import get_completion_from_messages, stream_chat   # 非流式 / 流式，都收 messages 列表

# ============================================================
# 配置（已给你备好，可以直接用，也可以改）
# ============================================================
# ------------------------------------------------------------
# ⭐ 路径为什么这么写？（这是个真实的坑）
#   HISTORY_FILE = "chat_history.json"   ← ❌ 别这么写！
#
#   裸的相对路径是相对于【当前工作目录 CWD】解析的，
#   不是相对于【这个脚本所在的位置】。
#   所以你在 D:\Desktop\Practice 下运行这个脚本，
#   文件就会落在 D:\Desktop\Practice\chat_history.json —— 跑错地方了。
#
#   下面这三行 = "永远把文件放在【本脚本所在的那个目录】里"，
#   不管你在哪个目录运行，结果都一样。
# ------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))   # __file__ = 本脚本的路径
HISTORY_FILE = os.path.join(_SCRIPT_DIR, "chat_history.json")

SYSTEM_PROMPT = "你是一个耐心、简洁的助手，回答用中文。"

# 用户输入这些词就退出
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", "再见"}


# ============================================================
# 调试助手（这个我写好了，不用改）—— 你验收时会用到它
# ============================================================
def show_context(context):
    """打印当前历史里每条消息的 role，用来【亲眼确认累积】。

    正常应该长这样（一轮一轮变长）：
        [历史共 1 条: system]
        [历史共 3 条: system → user → assistant]
        [历史共 5 条: system → user → assistant → user → assistant]
    """
    roles = " → ".join(m["role"] for m in context)
    print(f"\033[90m[历史共 {len(context)} 条: {roles}]\033[0m")


# ============================================================
# 第 4 步才需要：文件读写
# ============================================================
def save_history(context):
  
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

def load_history():
    """【进阶，选做】启动时读取上次的对话。

    这是你选 .json 换来的回报 —— 写的是完整数组，所以能读回来。

    ★ TODO（最后再做）
    提示：
        - 文件不存在时要返回一个【空列表】 —— 第一次运行时它当然不存在
        - 用 json.load(f) 读回来
        - ⚠️ 还记得 Day 2 学的"三层校验"吗？读回来的东西要不要校验一下？
    """
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # 文件不存在时返回空列表
    except json.JSONDecodeError:
        return []  # JSON 解码错误时也返回空列表

# ============================================================
# 主程序 —— ★ 你要写的代码全部在这个函数里
# ============================================================
def main():
    # context 就是"对话历史"。它一开始只有一条 system 消息，永远不动。
    context = [{"role": "system", "content": SYSTEM_PROMPT}]

    prompt_text = "请问有什么可以帮您的吗？"

    print("=" * 50)
    print("命令行 ChatGPT   （输入 exit / quit 退出）")
    print("=" * 50)

    # ========================================================
    # ★★★ TODO —— 从第 1 步开始，一步一步把它填满 ★★★
    # ========================================================
    #
    # ┌─【第 1 步】先写"单轮"，不要循环 ─────────────────────┐
    # │ 就 4~5 行：                                          │
    # │   ① 读一行用户输入                                    │
    # │   ② 把用户说的话 append 进 context                     │
    # │     形状：{"role": "user", "content": ...}            │
    # │   ③ 调 API，把【整个 context】发过去                    │
    # │   ④ 把模型的回复 append 进 context                     │
    # │     形状：{"role": "assistant", "content": ...}       │
    # │                                                      │
    # │ 💡 第 ③ 步用哪个函数？                                 │
    # │    第 1 步用【非流式】的 get_completion_from_messages(context) │
    # │       —— 它收 messages 列表、返回一段文本，最简单      │
    # │    等到【第 3 步】再换成 stream_chat()                  │
    # │       —— 那时你才能真切感受到"干等"和"逐字蹦"的区别    │
    # │                                                      │
    # │ ⚠️ 不管用哪个，【返回值都要拿去 append 进 context】      │
    # │    不然下一轮模型就"失忆"了                            │
    # │                                                      │
    # │ 写完就跑：  python chat_cli.py                         │
    # │ 能一问一答 → 第 1 步完成 ✅                             │
    # └──────────────────────────────────────────────────────┘
    try:
        while True:
            show_context(context)
            input_text = input(prompt_text)
            if input_text in EXIT_COMMANDS:
                break
            context.append({"role": "user", "content": input_text})
            print("ChatGPT: ", end="") 
            reply = stream_chat(context)    
            context.append({"role": "assistant", "content": reply})
            prompt_text = "你: " 

            save_history(context) 
    except KeyboardInterrupt:
        print("\n已中断")
    finally:
        save_history(context)  # 确保退出前保存历史
        print("\n对话已保存，再见！")
    # ┌─【第 2 步】把上面那几行包进 while True ───────────────┐
    # │ 加一个退出判断：用户输入 EXIT_COMMANDS 里的词就 break   │
    # │ 💡 在循环开头调用 show_context(context)                │
    # │    → 你会【亲眼看到】历史一轮一轮变长                   │
    # └──────────────────────────────────────────────────────┘
    #
    # ┌─【第 3 步】确认用的是流式 ───────────────────────────┐
    # │ 如果第 1 步你用的是 chat()（非流式），现在换成          │
    # │ stream_chat()。跑一次，感受"干等"和"逐字蹦"的区别。     │
    # └──────────────────────────────────────────────────────┘
    #
    # ┌─【第 4 步】每轮末尾保存 ─────────────────────────────┐
    # │ 在循环体最后调用 save_history(context)                │
    # │ 然后去看 chat_history.json 长什么样                    │
    # └──────────────────────────────────────────────────────┘
    #
    # ┌─【第 5 步】优雅退出 ─────────────────────────────────┐
    # │ Ctrl+C 会抛 KeyboardInterrupt，不处理就是一坨红色 traceback │
    # │ 用 try / except 包住循环，退出时打印一句告别            │
    # └──────────────────────────────────────────────────────┘
    #
    # ========================================================


if __name__ == "__main__":
    main()

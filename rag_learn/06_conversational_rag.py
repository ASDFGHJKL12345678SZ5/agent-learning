"""第3阶段 Day6 · 06_conversational_rag.py —— 对话式 RAG（给 RAG 加多轮能力）

【任务】（来自 阶段计划/03_RAG入门 Day6）
    ✅ 实现"追问"功能（用户可以接着上一条继续问）
    ✅ 用 ChatHistory 管理对话上下文
    ✅ 支持对话历史检索（不只是最新几轮）
    验收：连续问 3 个关联问题，看能否正确理解上下文

【⭐ 今天唯一的难点：指代消解（coreference resolution）】
    第 1 轮：RAG 有哪些缺点？        → 检索正常工作
    第 2 轮：那它的成本高吗？         → ⚠️ 拿这句去检索，**什么都捞不到**
    因为「它」在向量空间里没有任何意义：没有实义词，向量会和一堆无关的东西接近。

    解法：让 LLM 结合对话历史，把追问**重写成独立问题**，再拿去检索：
        历史：[用户: RAG 有哪些缺点？][助手: ...]
        追问：那它的成本高吗？
           ↓ LLM 改写
        独立问题：RAG 的成本高吗？     ← 拿这个检索才对

    ⭐ 这就是 Day5 MultiQuery 那个"查询改写"的**另一个用法**：
       Day5 改写是为了**扩召回**，Day6 改写是为了**补上下文**。同一把刀，两种用法。

【⭐ 今天的对照实验（这才是今天真正的产出）】
    同一段 3 轮对话，跑两遍：
        A 组：不消解 —— 直接拿用户原话去检索
        B 组：先消解成独立问题再检索
    对比：**第 2、3 轮分别捞到了什么**。
    预期：A 组的第 2、3 轮会捞回一堆不相关的块（因为查询里只有"它/这个/那"）。

【⚠️ 老规矩：改完跑一遍，git diff 看一眼有没有忘删的旧代码。】

【📖 阅读指引（哪些要读、哪些可以跳）】
    原则：**改了会让系统回答变差的代码 = 必须读懂；只是把东西跑起来的 = 知道位置就够。**
    判断标准一句话：**这段代码改了，系统的回答会变吗？**

    ⭐⭐ 必读：
        · CONDENSE_PROMPT —— 它定义了"改写"到底怎么改。
          （你 Day5 已经体验过：改这个模板，检索结果就变了）
        · compare_with_without_condense —— 不看懂它，你不知道自己在测什么

    ⭐ 要读：
        · format_history 的 max_turns —— 它决定"模型能记住多少轮历史"
          （历史无限增长 = prompt 无限膨胀 + 费钱 + 稀释注意力）

    可跳（和你第 2 阶段 chat_cli.py 里写的一样，或者纯 shell）：
        · save_history / load_history
        · run_cli 的输入循环（只注意最后那句 finally: save_history，你 Day3 学过）

    ⭐ 读的方法：**别自上而下读**，跟着数据走 —— 对每段问三个问题：
        ① 输入是什么？ ② 输出是什么？ ③ 它在整条链的哪一环？
      再自检：合上代码，能不能用自己的话说出"删掉它会怎样"。
"""

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool import chat                     # 你 Day4 用过

ROOT = Path(__file__).resolve().parent
STORE_PATH = ROOT / "store.json"
HISTORY_PATH = ROOT / "chat_history.json"     # 对话历史落盘（已在 .gitignore）

_day3 = importlib.import_module("03_vector_store")
_day4 = importlib.import_module("04_rag_chain")


# ============================================================
# 第 0 步：对话历史（我写好了 —— 和你第 2 阶段 chat_cli.py 那套一样）
# ============================================================
def format_history(history: list[dict], max_turns: int = 6) -> str:
    """把最近几轮对话渲染成给 LLM 看的文字。

    ⚠️ 为什么只取最近 max_turns 轮？
       历史会越积越长，全塞进去 = prompt 无限膨胀 + 费钱 + 稀释注意力。
       这就是"上下文窗口是有限资源"的具体体现（你第 2 阶段学过）。
    """
    recent = history[-max_turns:]
    lines = []
    for m in recent:
        who = "用户" if m["role"] == "user" else "助手"
        lines.append(f"{who}：{m['content']}")
    return "\n".join(lines)


def save_history(history: list[dict]):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_history() -> list[dict]:
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


# ============================================================
# 第 1 步：指代消解 —— 把追问改写成独立问题（★ 交给你）
# ============================================================
CONDENSE_PROMPT = """下面是一段对话历史，以及用户最新的一句话。

请把用户最新那句话改写成**一个不依赖上下文、能独立看懂的完整问题**。

要求：
1. 把「它 / 这个 / 那个 / 上面说的」这类指代，替换成历史里对应的**具体名词**
2. 如果最新那句话本身就已经完整（没有指代），就原样返回
3. 只输出改写后的问题，不要解释、不要加引号、不要写「改写：」

对话历史：
{history}

用户最新的话：{question}"""


def condense_question(history: list[dict], question: str,
                      max_turns: int = 6) -> str:
    """把追问改写成独立问题。

    ★ TODO(1) —— 三步，比 Day5 的改写还简单
        ① 拼 prompt：CONDENSE_PROMPT.format(history=..., question=...)
           history 用 format_history(history, max_turns) 拿
        ② 调 chat()：data = chat([{"role": "user", "content": prompt}])
        ③ 取正文 .strip() 返回

    ⚠️ 边界情况：历史为空时（第一轮）没必要调 LLM —— 直接原样返回 question。
       想清楚为什么：第一轮没有任何指代可言，白花一次调用。
    """
    prompt = CONDENSE_PROMPT.format(history=format_history(history,max_turns),question=question)
    if not history:
        return question
    data = chat([{"role":"user","content":prompt}])
    return data["choices"][0]["message"]["content"].strip()



# ============================================================
# 第 2 步：带历史的问答（★ 交给你）
# ============================================================
def answer_with_history(store, history: list[dict], question: str,
                        k: int = 5, use_condense: bool = True) -> dict:
    """一轮完整问答：消解 → 检索 → 拼 prompt（含历史）→ 生成。

    返回 {"standalone": 改写后的问题, "hits": 检索结果, "answer": 答案}

    ★ TODO(2) —— 四步
        ① 消解：如果 use_condense，standalone = condense_question(history, question)
                否则 standalone = question（这就是 A 组对照）
        ② 检索：hits = store.search(standalone, top_k=k)
                ⭐ 注意：**用 standalone 检索，不是用 question**
        ③ 拼 prompt：messages = _day4.build_prompt(standalone, hits)
                     ⭐ 然后把对话历史塞进 system，让模型知道"它"指的是什么：
                        messages[0]["content"] += "\\n\\n<对话历史>\\n" + format_history(history) + "\\n</对话历史>"
                     ⭐ 顺手在规则里补一条（想想为什么需要）：
                        "如果问题是追问，请结合对话历史理解指代"
        ④ 生成：data = chat(messages)，答案在 data["choices"][0]["message"]["content"]

    ⭐ 想清楚：为什么"检索用 standalone"但"生成时还要给它历史"？
       检索需要的是**关键词/语义**（所以必须消解），
       生成需要的是**对话的连贯感**（所以历史也得给）。
       两件事的目的不同，别混。
    """
    if use_condense:
        standalone = condense_question(history, question)
    else:
        standalone = question
        1

    hits = store.search(standalone, top_k=k)
    messages = _day4.build_prompt(standalone, hits)
    messages[0]["content"] += "\n\n<对话历史>\n" + format_history(history) + "\n</对话历史>"
    messages[0]["content"] += "\n\n<规则>：\n如果问题是追问，请结合对话历史理解指代\n</规则>"
    data = chat(messages)
    answer = data["choices"][0]["message"]["content"]  
    return {"standalone": standalone, "hits": hits, "answer": answer}


# ============================================================
# 第 3 步：对照实验（我写好了，你只管跑）
# ============================================================
DEMO_TURNS = [
    "RAG 有哪些绕不开的短板？",     # 第 1 轮：完整问题
    "那它的成本高吗？",             # 第 2 轮：有指代「它」
    "上面说的那个问题怎么解决？",   # 第 3 轮：有指代「上面说的那个」
]


def compare_with_without_condense(store):
    """同一段对话跑两遍：A 组不消解、B 组消解，对比每轮捞到了什么。

    ⭐ 这是今天真正的产出：**用数据证明"消解"是必需的，而不是"听起来更专业"**。
    """
    print("\n" + "=" * 66)
    print("对照实验：不消解（A 组） vs 消解（B 组）")
    print("=" * 66)

    results = {}
    for label, use_condense in [("A 组 不消解", False), ("B 组 消解", True)]:
        print(f"\n{'─' * 66}\n【{label}】")
        history = []
        rows = []
        for turn, q in enumerate(DEMO_TURNS, 1):
            try:
                r = answer_with_history(store, history, q, k=5,
                                        use_condense=use_condense)
            except NotImplementedError as e:
                print(f"  ⏳ 还没写：{e}")
                return
            srcs = sorted({m["source"] for _, _, m in r["hits"]})
            print(f"\n  第 {turn} 轮｜用户：{q}")
            print(f"         实际检索用的：{r['standalone']}")
            print(f"         捞到的来源：{srcs}")
            print(f"         答案：{r['answer'].strip()[:120]}")
            rows.append((q, r["standalone"], srcs))
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": r["answer"]})
        results[label] = rows

    print("\n" + "=" * 66)
    print("对比结论（自己看）")
    print("=" * 66)
    print("  ⭐ 关键看第 2、3 轮：A 组用「那它的成本高吗」去检索，捞到了什么？")
    print("     B 组把它改写成完整问题之后，捞到了什么？")
    return results


# ============================================================
# 第 4 步：交互式命令行（我写好了）
# ============================================================
def run_cli(store):
    """真正的"追问"体验：连续问，历史自动累积。"""
    history = load_history()
    if history:
        print(f"（已恢复上次的 {len(history)} 条历史，输入 /clear 可清空）")
    print("输入问题开始对话；/clear 清空历史，/exit 退出（自动保存）\n")

    try:
        while True:
            try:
                q = input("你：").strip()
            except EOFError:
                break
            if not q:
                continue
            if q in ("/exit", "/quit"):
                break
            if q == "/clear":
                history.clear()
                print("（历史已清空）\n")
                continue

            try:
                r = answer_with_history(store, history, q)
            except NotImplementedError as e:
                print(f"  ⏳ 还没写：{e}\n")
                continue
            if r["standalone"] != q:
                print(f"  \033[90m[消解为：{r['standalone']}]\033[0m")
            print(f"助手：{r['answer'].strip()}\n")
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": r["answer"]})
    finally:
        save_history(history)          # ← finally：不管怎么退出都会保存
        print(f"\n（已保存 {len(history)} 条对话到 {HISTORY_PATH.name}）")


def main():
    store = _day3.SimpleVectorStore()
    store.load(STORE_PATH)
    print(f"✅ 已加载向量库：{len(store.chunks)} 块")

    print("\n选一个模式：")
    print("  1 = 对照实验（推荐先跑，看数据）")
    print("  2 = 交互式对话（自己追问着玩）")
    choice = input("输入 1 或 2：").strip() or "1"

    if choice == "2":
        run_cli(store)
    else:
        compare_with_without_condense(store)

    print("\n" + "=" * 66)
    print("验收（做完自己回答）")
    print("=" * 66)
    print("  1) A 组第 2 轮用「那它的成本高吗」检索，捞到的是什么？为什么？")
    print("  2) 消解之后，第 2 轮的检索结果变对了吗？")
    print("  3) 为什么要「用 standalone 检索、但生成时给历史」？少给一样会怎样？")
    print("  4) 历史越积越长会怎样？format_history 里的 max_turns 是在权衡什么？")


if __name__ == "__main__":
    main()

"""第2阶段 Day1 · 02：用真 API 复现「温度」的效果

【这个脚本要验证什么】
  把概念书上的图和真 API 对上号：
    实验 1：T=0    跑 5 次 → 输出是否完全一样？        （零温度=贪婪解码）
    实验 2：T=1.5  跑 5 次 → 输出有多不同？            （高温=更随机）
    实验 3：T=0    跑 5 次「模糊问题」→ 它会不会承认不确定？（边界区域）
    实验 4：T=1.5  跑 5 次「模糊问题」→ 会不会给出多个不同答案？

【概念对照】
  - T 调的是"分布的陡峭程度"：T→0 趋近 argmax，T>1 把分布压平
  - "1,2,4,8,16,?" 这种题本身就是有歧义的（32 和 31 都合理），
    正好用来观察模型在「边界区域」的行为

【成本】
  总共 20 次调用，用的都是简短问题，flash 模型下大概几分钱。
"""
import os
import time
from collections import Counter   # 标准库：数数用的

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("LLM_MODEL")

if not (BASE_URL and API_KEY and MODEL):
    raise SystemExit("❌ .env 没读全，需要 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL 三项")

URL = f"{BASE_URL}/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


# ---------- 核心函数：发一次请求 ----------
def chat(prompt: str, temperature: float) -> dict:
    """调用一次 API。

    返回一个字典，包含正文 / 思考内容 / usage。
    这是把「重复的请求代码」抽成函数 —— 你第1阶段学的函数封装。
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 300,        # 限制输出，省点钱（试出来的经验值）
    }

    resp = httpx.post(URL, headers=HEADERS, json=payload, timeout=90)
    if resp.status_code != 200:
        raise SystemExit(f"❌ HTTP {resp.status_code}\n{resp.text}")

    data = resp.json()
    msg = data["choices"][0]["message"]

    return {
        "content": (msg.get("content") or "").strip(),
        # ★ 用 .get() 而不是 []：这个字段不是所有模型都有，缺了也不报错
        "reasoning": (msg.get("reasoning_content") or "").strip(),
        "usage": data["usage"],
    }


def run_batch(prompt: str, temperature: float, times: int) -> list:
    """同一个问题、同一个温度，跑 times 次，返回结果列表。"""
    results = []
    for i in range(times):
        r = chat(prompt, temperature)
        results.append(r)
        print(f"     第 {i+1} 次完成")
        time.sleep(0.8)       # ★ 稍微等一下，避免触发限流（库函数：time.sleep）
    return results


def report(title: str, results: list) -> None:
    """打印一批结果的分析。"""
    print("\n" + "─" * 70)
    print(f"  {title}")
    print("─" * 70)

    answers = [r["content"] for r in results]
    unique = set(answers)

    for i, a in enumerate(answers, 1):
        # 只显示前 80 个字符，太长看不清
        short = a.replace("\n", " ")[:80]
        print(f"  [{i}] {short}{'...' if len(a) > 80 else ''}")

    print(f"\n  📊 5 次里出现了 {len(unique)} 种不同答案")

    if len(unique) == 1:
        print("     → 完全一致 ✅ 说明这个温度下输出是确定的")
    else:
        print("     → 有差异 ⚠️ 说明这个温度下输出是随机的")

    # ★ Counter 是标准库的小工具：统计每个元素出现次数
    #   这里用它看"重复的答案出现了几次"
    if len(unique) < len(answers):
        counts = Counter(answers)
        for a, c in counts.most_common():
            if c > 1:
                print(f"     重复 {c} 次: {a.replace(chr(10), ' ')[:50]}")

    # 看看 reasoning_tokens 花了多少
    rt = [r["usage"].get("completion_tokens_details", {}).get("reasoning_tokens", 0) for r in results]
    ct = [r["usage"]["completion_tokens"] for r in results]
    print(f"\n  💰 输出 token: {ct}  其中思考 token: {rt}")


# ============================================================
#  实验开始
# ============================================================

PROMPT_NORMAL = "用一句话解释什么是'温度参数'。只回答一句话，不要展开。"
PROMPT_AMBIGUOUS = "找规律：1, 2, 4, 8, 16, 下一个数是什么？只回答一个数字，不要任何解释。"

TIMES = 5

print("=" * 70)
print(f"  温度实验 · 模型 = {MODEL}")
print("=" * 70)

# ---------- 实验 1：普通问题 + T=0 ----------
print(f"\n【实验 1】普通问题 + 温度 0 → 期待：5 次完全一样")
r1 = run_batch(PROMPT_NORMAL, 0.0, TIMES)
report("实验 1：T=0  /  普通问题", r1)

# ---------- 实验 2：普通问题 + T=1.5 ----------
print(f"\n【实验 2】普通问题 + 温度 1.5 → 期待：每次都不一样")
r2 = run_batch(PROMPT_NORMAL, 1.5, TIMES)
report("实验 2：T=1.5  /  普通问题", r2)

# ---------- 实验 3：模糊问题 + T=0 ----------
print(f"\n【实验 3】模糊问题 + 温度 0 → 关键观察：它会承认不确定吗？")
r3 = run_batch(PROMPT_AMBIGUOUS, 0.0, TIMES)
report("实验 3：T=0  /  模糊问题（1,2,4,8,16,?）", r3)
print("\n  ⭐ 注意：如果 5 次都是同一个数字，说明它在「边界区域」")
print("     依然自信地给了一个确定答案 —— 而这道题本身是有歧义的")
print("     （32 和 31 在数学上都成立，见笔记第 4 节）")

# ---------- 实验 4：模糊问题 + T=1.5 ----------
print(f"\n【实验 4】模糊问题 + 温度 1.5 → 关键观察：会不会给出多个答案？")
r4 = run_batch(PROMPT_AMBIGUOUS, 1.5, TIMES)
report("实验 4：T=1.5  /  模糊问题（1,2,4,8,16,?）", r4)
print("\n  ⭐ 对比实验 3：温度升高后，它开始「掷骰子」了 ——")
print("     这正是「模型在边界区域本来就在犹豫，温度让它表现出来」")

# ---------- 看一次完整的思考过程 ----------
print("\n" + "=" * 70)
print("  附：看一次完整的「思考过程」（reasoning_content）")
print("=" * 70)
sample = r3[0]
if sample["reasoning"]:
    print("\n【模型想的内容】")
    print(sample["reasoning"][:600])
    print("\n【模型最后说的】")
    print(sample["content"])
else:
    print("（这个模型没返回 reasoning_content）")

print("\n" + "=" * 70)
print("  实验结束")
print("=" * 70)
print("""
  自己回答这三个问题（答案写进笔记）：

  1. T=0 的 5 次输出真的完全一样吗？如果不一样，可能是什么原因？
     （提示：想想"temperature=0 并不保证 100% 可复现"）

  2. 实验 3 vs 实验 4：温度对「模糊问题」的影响，和对「普通问题」的影响，
     哪个更大？为什么？

  3. 看 reasoning_tokens：T=0 和 T=1.5 时，思考的长度有区别吗？
     这说明了什么？
""")

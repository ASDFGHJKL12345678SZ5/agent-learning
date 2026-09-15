"""第2阶段 Day2 · 05_stream_vs_not.py —— 用秒表量出"流式"和"非流式"的真实差别

【这个脚本要打破两个误解】

    误解①："流式更快。"
        —— 错。流式几乎不缩短【总时间】，它改变的是【你第一次看到东西的时刻】。

    误解②："跑一次就能比出来。"
        —— 错。跑一次什么都比不出来。看下面那个 REPEAT 参数为什么存在。

【怎么跑才有意义】
    一定要【在终端里直接跑】，不要重定向到文件。
    你会先经历"死一样的安静"，再看到字一段段冒出来。
    这个"体感差异"才是重点，秒表只是佐证。

        python 05_stream_vs_not.py
"""

import time

from tool import chat, stream_chat

# ⭐ 每种模式跑几次？
#    设成 1 —— 你看到的差异基本全是噪声，什么都证明不了。
#    设成 2~3 —— 平均值才有参考价值。
#    （想想你 Day 1 那个温度实验：4 组 × 5 次。为什么要跑 5 次？同一个道理。）
REPEAT = 2

# 用一个会产出较长回答的问题 —— 回答越长，"干等"和"逐字蹦"的差别越明显
PROMPT = "请写一段 300 字左右的短文，说明人体工学办公椅对久坐的人有哪些好处，分点说明。"


# ============================================================
# 两种模式，各自返回一组测量数据
# ============================================================
def measure_non_stream(show_text):
    print("\n" + "=" * 62)
    print("【非流式 chat()】")
    print("=" * 62)
    if show_text:
        print("⚠️ 注意：下面会安静地等，一个字都不显示。")
        print("   不是卡死 —— 服务器正在把整段答案生成完，攒够了才发货。\n")

    t0 = time.perf_counter()
    data = chat([{"role": "user", "content": PROMPT}], temperature=0)
    total = time.perf_counter() - t0

    text = data["choices"][0]["message"]["content"]
    if show_text:
        print(f"------ 等了 {total:.2f} 秒，然后「唰」一下全出来了 ------")
        print(text)

    u = data.get("usage") or {}
    return {
        "ttft": total,          # 非流式的"首字延迟" = 总耗时，因为它一次性到齐
        "total": total,
        "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
        "output": u.get("completion_tokens", 0),
    }


def measure_stream(show_text):
    print("\n" + "=" * 62)
    print("【流式 stream_chat()】")
    print("=" * 62)
    if show_text:
        print("⚠️ 注意节奏：这次是【一段一段】冒出来的。\n")

    timing = {}
    stream_chat([{"role": "user", "content": PROMPT}],
                temperature=0, timing=timing)

    u = timing.get("usage") or {}
    return {
        "ttft": timing.get("ttft", float("nan")),
        "total": timing.get("total", float("nan")),
        "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
        "output": u.get("completion_tokens", 0),
    }


def avg(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else float("nan")


if __name__ == "__main__":
    non_rows, stream_rows = [], []

    for i in range(REPEAT):
        non_rows.append(measure_non_stream(show_text=(i == 0)))
        stream_rows.append(measure_stream(show_text=(i == 0)))

    # ---------------- 每轮明细 ----------------
    print("\n" + "=" * 62)
    print("逐轮明细（看这里才能发现问题）")
    print("=" * 62)
    for i in range(REPEAT):
        a, b = non_rows[i], stream_rows[i]
        print(f"第 {i + 1} 轮  非流式：首字 {a['ttft']:6.2f}s  总 {a['total']:6.2f}s  "
              f"思考 token {a['reasoning']:>5}  正文 token {a['output']:>5}")
        print(f"第 {i + 1} 轮  流式　：首字 {b['ttft']:6.2f}s  总 {b['total']:6.2f}s  "
              f"思考 token {b['reasoning']:>5}  正文 token {b['output']:>5}")

    # ---------------- 平均值 ----------------
    n_ttft, s_ttft = avg(non_rows, "ttft"), avg(stream_rows, "ttft")
    n_total, s_total = avg(non_rows, "total"), avg(stream_rows, "total")
    n_think, s_think = avg(non_rows, "reasoning"), avg(stream_rows, "reasoning")

    print("\n" + "=" * 62)
    print(f"平均（每种模式跑了 {REPEAT} 次）")
    print("=" * 62)
    print(f"首字延迟　：非流式 {n_ttft:.2f} 秒   /   流式 {s_ttft:.2f} 秒")
    print(f"总耗时　　：非流式 {n_total:.2f} 秒   /   流式 {s_total:.2f} 秒")
    print(f"思考 token：非流式 {n_think:.0f}     /   流式 {s_think:.0f}")

    print("\n" + "-" * 62)
    print("怎么读这张表")
    print("-" * 62)
    print("① 总耗时：两者应该【差不多】。流式不让你更快拿到全文。")
    print("② 首字延迟：流式应该明显更短 —— 这才是它真正改变的东西。")
    print("③ 思考 token：这是【混杂因素】。两次生成的思考量只要不一样，")
    print("   所有的耗时对比就都不公平。所以必须多跑几次取平均。")
    if REPEAT == 1:
        print("\n⚠️ 你把 REPEAT 设成了 1 —— 上面这行数没有意义，改成 2 或 3 再看。")

    if abs(n_total - s_total) > max(n_ttft, s_ttft):
        print("\n❗ 总耗时差得有点大 —— 多半不是流式造成的，而是这两次的思考量不同。")

    # ---------------- ⭐ 最反直觉的数字 ----------------
    if n_think and avg(non_rows, "output"):
        share = n_think / avg(non_rows, "output") * 100
        print("\n" + "=" * 62)
        print("⭐ 最反直觉的一个数字")
        print("=" * 62)
        print(f"平均每次回答烧掉 {avg(non_rows, 'output'):.0f} 个输出 token，")
        print(f"其中 {n_think:.0f} 个是【思考 token】—— 占了 {share:.0f}%。")
        print("而这部分内容，非流式下你一个字都看不到。")
        print("\n→ 这就解释了为什么流式把首字延迟只压缩了一点点：")
        print("   思考阶段本来就不往外吐字，流式也救不了它。")
        print("   真正的解法是把它显示出来 —— show_reasoning=True，")
        print("   或者产品界面里那个「思考中…」的动画。")

"""第2阶段 Day2 · 04_boundary.py —— 亲手测出 LLM 的"计算能力边界"

【这个脚本要回答的问题】
    同一个任务，规模变大时，LLM 是从哪里开始崩的？
    （也就是说：那张"能做 / 做不好 / 做不到"的表，刻度到底在哪）

【设计思路 —— 这是本脚本最关键的一点】
    每一题的标准答案，都由 **Python 自己算出来**，不是我从记忆里写的。
    模型答完，脚本拿它的答案和 Python 的答案硬碰硬比对。
    所以结论不是"感觉它对不对"，而是有确凿判定。

    A 组  多位数乘法        2位 → 4位 → 6位
    B 组  精确计数          短文 → 长文 → 长数字串
    C 组  列表排序          5 个 → 15 个 → 30 个
    D 组  精确字符串操作    反转 / 取第 N 个字符 / 逐字复制

【用法】
    python 04_boundary.py          跑全部
    python 04_boundary.py A C      只跑 A 组和 C 组（省时间省钱）

【跑之前先做一件事】往下看"预测区"，把 None 改成 True / False。
"""

import random     # 标准库：造测试数据
import re         # 标准库：从模型的回答里抠数字 / 做文本归一化
import sys        # 标准库：读命令行参数

from tool import get_completion   # 我们自己写的工具包

# ============================================================
# 预测区 —— 跑之前先猜，跑完对照。这一步别跳过。
# ============================================================
# 每条改成 True（猜它对）或 False（猜它错）。
# 跑完脚本会告诉你猜对几条。**猜错的那几条，就是你认知里的盲区。**
PREDICTIONS = {
    "A1": None,   # 47 × 89
    "A2": None,   # 8472 × 6351
    "A3": None,   # 847291 × 635184
    "B1": None,   # 短文里数"的"
    "B2": None,   # 长文里数"的"
    "B3": None,   # 长数字串里数"7"
    "C1": None,   # 排 5 个数
    "C2": None,   # 排 15 个数
    "C3": None,   # 排 30 个数
    "D1": None,   # 反转 10 个字符
    "D2": None,   # 取第 80 个字符
    "D3": None,   # 逐字复制 ~200 字
}

# ============================================================
# 素材（全部用固定种子生成，每次跑都一样）
# ============================================================
random.seed(20260914)

# --- B 组用：一段自然感的中文长文（B1 取它开头 60 字）---
LONG_TEXT = (
    "秋天的傍晚，我坐在窗边看楼下那棵老槐树。树叶已经开始变黄，"
    "风一吹，就有几片慢慢地落下来，落在停着的自行车上，落在送外卖的小哥的肩上。"
    "我想起小时候，外婆家的院子里也有一棵这样的树，那时候的我总觉得，"
    "夏天是永远不会结束的。现在我知道，会结束的东西太多了，"
    "只是当时的我们太小，还看不出来而已。"
    "楼下的灯一盏一盏亮起来，像有人在天黑之前，"
    "急着把白天没说完的话，一句一句地补上。"
)
SHORT_TEXT = LONG_TEXT[:60]

# --- B3 用：一串随机数字 ---
DIGIT_STR = "".join(random.choice("0123456789") for _ in range(120))

# --- D2 / D3 用：一段纯 ASCII 无空格长串（避免"第几个字符"数不清）---
ASCII_STR = "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(150))
ASCII_INDEX = 80   # 取第 80 个（从 1 开始数）

# --- C 组用：三组不同长度的数字 ---
LIST_5 = [random.randint(1, 99) for _ in range(5)]
LIST_15 = [random.randint(1, 99) for _ in range(15)]
LIST_30 = [random.randint(1, 99) for _ in range(30)]


# ============================================================
# 判定工具：模型爱说废话，得先把它的答案"洗"干净再比
# ============================================================
def strip_fence(text):
    """去掉 ``` 代码块围栏和首尾空白。"""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_ints(text):
    """从回答里抠出所有整数（先把千分位逗号去掉，否则 5,382 会被拆成两段）。

    ⚠️ 这里只吃 content 字段，不吃 reasoning_content ——
       否则思考过程里的中间数字会把判定污染。
    """
    text = text.replace(",", "").replace("，", "")
    return [int(x) for x in re.findall(r"\d+", text)]


def normalize_text(text):
    """去掉所有空白并转小写，用于"逐字复制"这种宽松比对。"""
    return re.sub(r"\s+", "", strip_fence(text)).lower()


# ============================================================
# 判定函数：每种题型一种判法
# ============================================================
def judge_int(answer, truth):
    """答案里出现过正确数字就算对（模型常写 '... = 5382'）。"""
    return truth in extract_ints(answer), str(truth)


def judge_int_list(answer, truth):
    """模型给出的整数序列，必须和标准答案完全一致（顺序也要对）。"""
    got = extract_ints(answer)
    return got == truth, " ".join(str(x) for x in truth)


def judge_text(answer, truth):
    """归一化后完全相同才算对。"""
    return normalize_text(answer) == normalize_text(truth), truth


# ============================================================
# 题目表
# ============================================================
def build_probes():
    probes = []

    # ---------- A 组：多位数乘法 ----------
    for pid, scale, (a, b) in [
        ("A1", "2位 × 2位", (47, 89)),
        ("A2", "4位 × 4位", (8472, 6351)),
        ("A3", "6位 × 6位", (847291, 635184)),
    ]:
        probes.append({
            "id": pid,
            "group": "A 多位数乘法",
            "scale": scale,
            "prompt": f"请计算 {a} × {b}。只输出最终结果这个数字本身，"
                      f"不要过程、不要解释、不要单位。",
            "judge": judge_int,
            "truth": a * b,
        })

    # ---------- B 组：精确计数 ----------
    probes.append({
        "id": "B1", "group": "B 精确计数", "scale": f"短文 {len(SHORT_TEXT)} 字",
        "prompt": f"下面这段话里，「的」字一共出现了几次？只输出一个数字，不要解释。\n\n"
                  f"```\n{SHORT_TEXT}\n```",
        "judge": judge_int, "truth": SHORT_TEXT.count("的"),
    })
    probes.append({
        "id": "B2", "group": "B 精确计数", "scale": f"长文 {len(LONG_TEXT)} 字",
        "prompt": f"下面这段话里，「的」字一共出现了几次？只输出一个数字，不要解释。\n\n"
                  f"```\n{LONG_TEXT}\n```",
        "judge": judge_int, "truth": LONG_TEXT.count("的"),
    })
    probes.append({
        "id": "B3", "group": "B 精确计数", "scale": f"数字串 {len(DIGIT_STR)} 位",
        "prompt": f"下面这串数字里，数字 7 一共出现了几次？只输出一个数字，不要解释。\n\n"
                  f"```\n{DIGIT_STR}\n```",
        "judge": judge_int, "truth": DIGIT_STR.count("7"),
    })

    # ---------- C 组：列表排序 ----------
    for pid, scale, nums in [
        ("C1", "5 个数", LIST_5),
        ("C2", "15 个数", LIST_15),
        ("C3", "30 个数", LIST_30),
    ]:
        probes.append({
            "id": pid, "group": "C 列表排序", "scale": scale,
            "prompt": f"把这组数字从小到大排序：{', '.join(map(str, nums))}。\n"
                      f"只输出排好序的数字，用空格分隔，不要序号、不要解释。",
            "judge": judge_int_list, "truth": sorted(nums),
        })

    # ---------- D 组：精确字符串操作 ----------
    src = "QWERTYUIOP"
    probes.append({
        "id": "D1", "group": "D 精确字符串操作", "scale": "反转 10 字符",
        "prompt": f"把字符串 {src} 完全倒过来写（最后一个字符放到最前面）。"
                  f"只输出结果，不要解释。",
        "judge": judge_text, "truth": src[::-1],
    })
    probes.append({
        "id": "D2", "group": "D 精确字符串操作", "scale": f"取第 {ASCII_INDEX} 个字符",
        "prompt": f"下面这串小写字母，从左边第 1 个开始数，第 {ASCII_INDEX} 个字符是什么？"
                  f"只输出那一个字符，不要解释。\n\n```\n{ASCII_STR}\n```",
        "judge": judge_text, "truth": ASCII_STR[ASCII_INDEX - 1],
    })
    probes.append({
        "id": "D3", "group": "D 精确字符串操作", "scale": f"逐字复制 {len(LONG_TEXT)} 字",
        "prompt": f"请把下面这段话**一字不差**地复制一遍，不要增删任何一个字，不要任何额外说明。\n\n"
                  f"```\n{LONG_TEXT}\n```",
        "judge": judge_text, "truth": LONG_TEXT,
    })

    return probes


# ============================================================
# 主流程
# ============================================================
def main():
    wanted = [a.upper() for a in sys.argv[1:]] or ["A", "B", "C", "D"]
    probes = [p for p in build_probes() if p["group"][0] in wanted]

    print(f"即将测试 {len(probes)} 题，模型 = 由 .env 里的 LLM_MODEL 决定\n")

    results = {}
    for p in probes:
        print(f"[{p['id']}] {p['group']} · {p['scale']} ... ", end="", flush=True)
        try:
            answer = get_completion(p["prompt"], temperature=0)
        except SystemExit as e:
            print(f"\n调用失败：{e}")
            return

        ok, truth_show = p["judge"](answer, p["truth"])
        results[p["id"]] = ok

        print("✅ 对" if ok else "❌ 错")
        if not ok:
            got = strip_fence(answer).replace("\n", " ")
            print(f"      模型答：{got[:120]}{'...' if len(got) > 120 else ''}")
            print(f"      Python 标准答案：{truth_show}")

    # ---------- 汇总 ----------
    print("\n" + "=" * 62)
    print("汇总（按组 / 按规模看退化趋势）")
    print("=" * 62)
    print(f"{'题号':<6}{'规模':<22}{'结果'}")
    print("-" * 62)
    for p in probes:
        print(f"{p['id']:<6}{p['scale']:<22}{'✅' if results[p['id']] else '❌'}")

    total = len(results)
    right = sum(results.values())
    print("-" * 62)
    print(f"总正确率：{right}/{total}")

    # ---------- 预测命中率 ----------
    predicted = {k: v for k, v in PREDICTIONS.items() if v is not None and k in results}
    if predicted:
        hit = sum(1 for k, v in predicted.items() if v == results[k])
        print(f"\n你的预测命中：{hit}/{len(predicted)}")
        miss = [k for k, v in predicted.items() if v != results[k]]
        if miss:
            print(f"⚠️ 猜错的是：{', '.join(miss)} —— 这几条就是你的认知盲区，回去改 03 的 TODO 时留意")
    else:
        print("\n（你没填预测区，那这次就没有「猜错」这回事，也就少学了一半）")


if __name__ == "__main__":
    main()

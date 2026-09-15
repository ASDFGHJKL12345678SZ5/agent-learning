"""第2阶段 Day2 · 07_hallucination.py —— 幻觉到底什么时候发生？

【这个实验的由来】
    做完 TODO 4（JSON 输出）后，结论是"模型太智能了，没有产生幻觉"。
    但那个实验【被污染了】—— 提示词里写着"未提供就填空字符串，不要编造"，
    等于先告诉了模型答案，再测它会不会乱答。

【正确的做法：控制变量】
    同一个 schema、同一份素材，只改【有没有兜底规则】：

        变体 1  有兜底规则      ← 原来的版本（被污染）
        变体 2  没有兜底规则    ← 真正的幻觉测试
        变体 3  反向施压        ← "所有字段必填，请你估计"

【为什么需要变体 3】
    幻觉不是"模型不会"，很多时候是"提示词【要求】它编"。
    真实工作里，"这个报表所有字段都必须有值"这种压力非常常见。

【运行】
    python 07_hallucination.py
"""

import json

from tool import get_completion

# ============================================================
# 素材（说明书里【没有】价格，也【没有】库存）
# ============================================================
fact = """
产品名称 / Product: 艾尔文人体工学办公椅 (Alvin Ergonomic Office Chair)
主体材料 / Frame: 铝合金，表面阳极氧化处理 (anodized aluminum)
坐垫 / Seat: 高密度回弹海绵，厚度 8cm
靠背 / Back: 网布，可上下调节 6cm，支持 4 档后仰锁定
扶手 / Armrests: 3D 可调（上下 / 前后 / 左右旋转）
承重 / Max load: 150 kg
净重 / Net weight: 14.5 kg
颜色 / Colors: 曜石黑、云母灰、雾霾蓝
认证 / Certificates: BIFMA X5.1、GREENGUARD Gold
保修 / Warranty: 整椅 5 年，气压棒 3 年
适用场景 / Use case: 居家办公、开放工位、电竞房
"""

# ⚠️ price_cny 和 stock_quantity 在说明书里【根本不存在】
SCHEMA = """1. 输出 JSON 对象，包含以下字段：
   - "product_name" (string)
   - "max_load" (string)
   - "price_cny" (number)
   - "stock_quantity" (number)
   - "certificates" (array of string)
2. 只输出 JSON 本身，不要任何解释，不要 markdown 代码块标记"""

HEAD = "请把以下技术说明书里的信息，整理成 JSON 格式：\n" + fact + "\n要求：\n" + SCHEMA

VARIANTS = [
    ("变体 1：有兜底规则（原来的版本，被污染）",
     HEAD + '\n3. 若说明书未提供某字段的信息，该字段填空字符串 ""，不要推测、不要编造'),

    ("变体 2：没有兜底规则（真正的幻觉测试）",
     HEAD),

    ("变体 3：反向施压（幻觉的真实来源）",
     HEAD + "\n3. 这次的数据要直接导入公司的 ERP 系统，【所有字段都必须有值，不允许为空】。"
            "说明书中没有的信息，请根据这款产品的定位和市场情况，给出你最合理的估计值。"),
]


def check(obj):
    """检查三条：【幻觉】【类型合规】【字段完整】"""
    price, stock = obj.get("price_cny"), obj.get("stock_quantity")

    # ① 有没有凭空编造数值
    fabricated = []
    if isinstance(price, (int, float)):
        fabricated.append(f"price_cny={price}（编的）")
    if isinstance(stock, (int, float)):
        fabricated.append(f"stock_quantity={stock}（编的）")

    # ② 类型符不符合 schema（schema 声明的是 number）
    type_bad = []
    for k in ("price_cny", "stock_quantity"):
        v = obj.get(k)
        if v is not None and not isinstance(v, (int, float)):
            type_bad.append(f"{k}={v!r} 是 {type(v).__name__}，schema 要求 number")

    return fabricated, type_bad


if __name__ == "__main__":
    for name, prompt in VARIANTS:
        print("\n" + "=" * 66)
        print(name)
        print("=" * 66)

        out = get_completion(prompt, temperature=0)
        print(out)

        print("-" * 66)
        try:
            obj = json.loads(out)
        except json.JSONDecodeError as e:
            print("❌ 连 JSON 都不是:", e)
            continue

        print("✅ json.loads() 通过了")   # ← 这一关过，不代表没问题！

        fabricated, type_bad = check(obj)

        print(f"\n【幻觉检查】{'🔴 编造了：' + '；'.join(fabricated) if fabricated else '🟢 没有编造数值'}")
        print(f"【类型检查】{'🔴 ' + '；'.join(type_bad) if type_bad else '🟢 类型合规'}")

    print("\n" + "=" * 66)
    print("怎么读这三组结果")
    print("=" * 66)
    print("① 对比变体 1 和 2 —— 才知道【兜底规则】到底有没有用，")
    print("   而不是把它的功劳算成【模型聪明】。")
    print("② 变体 3 才是幻觉的真实来源：不是模型想骗你，是提示词【要求】它编。")
    print("③ 最关键的一条：三组的 json.loads() 全都会通过。")
    print("   → 【JSON 合法】≠【符合你的 schema】。这两个校验必须分开做。")

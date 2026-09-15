"""第2阶段 Day2 · 03_prompt_basics.py —— 提示工程基础四连（零样本 / 少样本 / 角色设定 / JSON）

【本节素材】
一张"技术说明书"(fact sheet)，我们要让模型**只依据它**写出营销描述。
图片里那段三引号 f-string（把 {fact_sheet_chair} 插进提示模板）的写法，就是本节的第一个动作：
    把素材用分隔符圈起来，塞进指令模板里。

【运行方式】
    python 03_prompt_basics.py     （Windows / macOS 都一样，先激活虚拟环境）
四个 TODO 只填了哪个，就只跑哪个，没填的会自动跳过 —— 你不用一次写完。

【规矩】这四个 TODO 请你写，我不代写。卡住或缺东西就把报错/输出贴给我。
"""

from tool import get_completion, get_completion_from_messages, stream_chat

# ============================================================
# 素材：一张椅子的技术说明书（中英对照）—— 这段不用改
# ============================================================
fact_sheet_chair = """
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

# ============================================================
# 要你填的四个"填空题"。没填的保持 None，脚本会自动跳过。
# ============================================================

# ---------- TODO 1：分隔符 + 零样本 ----------
# 目标：让模型只依据上面的说明书，写一段 120 字左右的营销描述。
# 提示语里必须有三样东西：
#   ① 任务说明（你是市场营销人员，请基于说明书写一段产品营销描述）
#   ② 分隔符，把 fact_sheet_chair 圈在中间
#      —— 三个双引号 / ### / <说明书></说明书> 都行，你自己挑一种
#   ③ 一句"只使用分隔符内的信息，不要编造说明书里没有的参数"
# 写法：用 f"""...""" 三引号字符串，把 {fact_sheet_chair} 插进去
#      （f-string 你在第1阶段就学过，这里只是字符串变长了而已）
prompt_1 = f"""你是一个市场营销人员.\
    请基于以下技术说明书，写一段 120 字左右的营销描述：
    {fact_sheet_chair}
    只使用分隔符内的信息，不要编造说明书里没有的参数。"""


# ---------- TODO 2：少样本 few-shot ----------
# 目标：给模型 2~3 个"输入 → 输出"的范例，让它照葫芦画瓢。
# 建议任务：把说明书里的参数，转成"卖点短句"。
# 形状大概是：
#     任务：把产品参数改写成一句打动人的卖点
#     示例1：输入：承重 150 kg    输出：________
#     示例2：输入：保修 5 年      输出：________
#     现在轮到你：输入：坐垫 8cm 高密度回弹海绵   输出：
# ⚠️ 分组要给 2 个以上示例（给 1 个等于没给），这是少样本的硬要求。
prompt_2 = f"""把产品参数改写成一句打动人的卖点 
示例1：输入：承重 150 kg    输出：稳如磐石，承重高达 150 kg，让你坐得更安心。
示例2：输入：保修 5 年      输出：整椅享受 5 年保修，品质保障，使用无忧。
现在轮到你：输入：坐垫 8cm 高密度回弹海绵   输出：
请输出两三个示例
"""


# ---------- TODO 3：角色设定（system 消息）----------
# 目标：体验 system / user 两个角色的分工。
#   system = 给模型的"岗位说明书"（你是谁、守什么规矩、用什么语气）
#   user   = 具体这一次的活儿
# 这里要填一个 **list**（不是字符串），形状：
#     [{"role": "system", "content": "..."},
#      {"role": "user",   "content": f"...{fact_sheet_chair}..."}]
# 玩法建议：让 system 规定"只用初中生能懂的大白话，禁止用专业术语"，
#           同一个 user 问题，对比一下有 system 和没 system 的差别。
messages_3 =  [{"role": "system", "content": "你用初中生都能听懂的大白话，禁止使用专业术语。"},
      {"role": "user",   "content": f"{fact_sheet_chair}请帮我编造广告语"}]


# ---------- TODO 4：结构化输出（JSON）----------
# 目标：让模型把说明书里的信息，吐成 JSON，方便程序解析。
# ⚠️ 两个坑，都要在提示里主动堵上：
#   ① 明确写出你要的字段名和类型，并给一个样例结构
#   ② 明确说"只输出 JSON 本身，不要任何解释、不要 markdown 代码块标记"
# 写完后，在下面"验证区"用 json.loads() 试着解析一下，
# 解析失败就说明提示没写严 —— 这是把 LLM 接进程序时必须过的一关。
prompt_4 = f"""请把以下技术说明书里的信息，整理成 JSON 格式：
{fact_sheet_chair}
要求：
1. 输出 JSON 对象，包含以下字段：
   - "product_name" 
   - "frame_material" 
   - "seat_material" 
   - "back_material" 
   - "armrests" 
   - "max_load" 
   - "net_weight" 
   - "colors" 
   - "certificates" (string)    
   - "warranty" (string)
   - "use_case" (string)
   - "price_cny" (number)    
2.只输出JSON本身，不要任何解释，不要markdown代码块标记

"""


# ============================================================
# 下面不用改：跑你填好的题
# ============================================================
# ⚙️ 流式开关：True = 边生成边打印（推荐）；False = 等全部生成完再一次性打印
STREAM = True

# 想看模型"思考"的全过程？把下面这个改成 True。
# 打开后你会亲眼看到推理模型在正文之前先写一大堆思考 —— 那部分又慢又费钱。
SHOW_REASONING = False


def run(title, value):
    if value is None:
        print(f"\n{'=' * 60}\n[跳过] {title}：TODO 还没写\n{'=' * 60}")
        return None
    print(f"\n{'=' * 60}\n【{title}】\n{'=' * 60}")

    if STREAM:
        # 流式：在这里就一个字一个字打出来了，返回的 out 是拼好的完整文本
        out = stream_chat(value, show_reasoning=SHOW_REASONING) if isinstance(value, list) \
            else stream_chat([{"role": "user", "content": value}], show_reasoning=SHOW_REASONING)
    else:
        out = get_completion_from_messages(value) if isinstance(value, list) else get_completion(value)
        print(out)

    return out


if __name__ == "__main__":
    run("TODO 1 零样本 + 分隔符", prompt_1)
    run("TODO 2 少样本", prompt_2)
    run("TODO 3 角色设定（system）", messages_3)
    json_text = run("TODO 4 结构化 JSON 输出", prompt_4)

    # 验证区：JSON 能不能被程序读懂
    if json_text:
        import json
        print(f"\n{'-' * 60}\n[验证] 尝试用 json.loads() 解析 TODO 4 的输出：")
        try:
            obj = json.loads(json_text)
            print("✅ 解析成功，Python 拿到的是 dict：")
            print(obj)
        except json.JSONDecodeError as e:
            print(f"❌ 解析失败：{e}")
            print("   → 说明模型多嘴了（带了 ``` 或解释文字）。回提示里补一句限制，再跑一次。")

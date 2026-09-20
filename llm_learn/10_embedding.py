"""第2阶段 Day6 · 10_embedding.py —— Embedding：把文本变成向量

【任务】（来自你的计划表）
    ✅ 调用 Embedding API 将多段文本转为向量
    ✅ 实现余弦相似度计算
    ✅ 做一个最简单的语义搜索（给查询找最相似的句子）
    验收：能说出 Embedding 是什么、有什么用

【⭐ 和 Chat API 的根本区别 —— 先在心里过一遍】
    你之前调的都是【生成式】接口：给它文字，它还你文字。
    Embedding 是【表征式】接口：给它文字，它还你【一串数字】。

    那串数字叫【向量（vector）】，几百到几千个数。
    它编码的是这句话的【语义】—— 意思相近的句子，向量也相近。

【⭐ 代码上的区别只有三处】
    路径：     /embeddings              （不是 /chat/completions）
    请求字段：  input                    （不是 messages）
    取值：     data[0]["embedding"]     （不是 choices[0].message.content）
    鉴权头、httpx.post 的写法 —— 完全一样。
    （上面的 get_embedding() 我已经写在 tool.py 里了）

【⚠️ 先做第 0 步】没确认接口能通就往下写，后面全是白干。
"""

import math

from tool import get_embedding


# ============================================================
# 第 0 步：探针 —— 确认接口能通（我写好了，直接跑）
# ============================================================
def probe():
    print("=" * 66)
    print("第 0 步：确认接口能通")
    print("=" * 66)

    import os
    print(f"  EMB_BASE_URL = {os.getenv('EMB_BASE_URL')}")
    print(f"  EMB_MODEL    = {os.getenv('EMB_MODEL')}")
    key = os.getenv("EMB_API_KEY")
    print(f"  EMB_API_KEY  = {'已配置（' + str(len(key)) + ' 个字符）' if key else '❌ 没配置'}")

    if not key:
        print("\n  ❌ .env 里没有 EMB_API_KEY —— 先去智谱控制台拿一个填进去")
        return None

    print("\n  正在调用……")
    vec = get_embedding("今天天气真好")

    print(f"\n  ✅ 接口通了")
    print(f"     向量维度 = {len(vec)}")
    print(f"     前 5 个数字 = {[round(x, 5) for x in vec[:5]]}")
    print(f"     类型 = {type(vec).__name__}，元素类型 = {type(vec[0]).__name__}")
    print(f"\n  ⭐ 看明白了吗：一句『今天天气真好』，变成了一串 {len(vec)} 个浮点数。")
    print(f"     这串数字就是这句话在【语义空间】里的坐标。")
    return vec


# ============================================================
# 第 1 步：多段文本 → 多组向量
# ============================================================
SENTENCES = [
    "今天天气真好，适合出去玩",
    "阳光明媚，是个出游的好日子",       # ← 和第 1 句【意思很近】，但用词完全不同
    "我喜欢吃火锅",
    "机器学习是人工智能的一个分支",
    "深度学习需要大量的数据",
    "神经网络有很多层",
]


def embed_all():
   
   return get_embedding(SENTENCES)  # 直接一次性传入整个列表，返回一个二维列表

# ============================================================
# 第 2 步：余弦相似度
# ============================================================
def cosine_similarity(a: list, b: list) -> float:
    """算两个向量的余弦相似度，返回 -1 到 1 之间的一个数。

    ⭐ 公式（三行代码就够）：
              a · b
        cos = ─────────          a·b 是【点积】，|a| 是 a 的【模长】
              |a| × |b|

    拆成三步：
        ① 点积：把两个向量【逐位相乘再求和】
              sum(x * y for x, y in zip(a, b))
        ② 模长：把向量【逐位平方求和，再开根号】
              math.sqrt(sum(x * x for x in a))
        ③ 相除

    ⭐ 怎么理解这个数？
        = 1   两个向量方向完全相同  → 语义几乎一样
        = 0   垂直，毫无关系
        = -1  方向完全相反

    ★ TODO(第2步)
    提示：math 已经 import 好了。zip() 能把两个列表配对。
    """
    cos=sum( x * y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
    return cos
    

# ============================================================
# 第 3 步：语义搜索（RAG 的地基）
# ============================================================
def semantic_search(query: str, sentences: list, vectors: list, top_k: int = 3):
    """给一个查询，找出最相似的 top_k 个句子。

    返回 [(相似度, 句子), ...]，按相似度【从大到小】排序。

    ⭐ 这就是搜索引擎 / RAG 的最小内核：
        把「查询」转成向量 → 和每一篇文档的向量算相似度 → 取最高的几个

    ★ TODO(第3步)
    步骤：
        ① 把 query 转成向量            get_embedding(query)
        ② 和 vectors 里每一个算相似度   cosine_similarity(...)
        ③ 配对、排序、取前 top_k
           提示：sorted(..., key=..., reverse=True) 可以排序
    """
    query_vec = get_embedding(query)
    scores = [(cosine_similarity(query_vec, vec), sent) for vec, sent in zip(vectors, sentences)]
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:top_k]


# ============================================================
# 主流程
# ============================================================
def main():
    vec = probe()
    if vec is None:
        return
    vectors = embed_all()
    print(f"\n转好了 {len(vectors)} 个向量，每个 {len(vectors[0])} 维")
    # ★ TODO：第 2 步做完后打开 —— 先做个"肉眼验证"
    # print("\n" + "=" * 66)
    # print("语义相似度验证：意思近的分数高，意思远的分数低")
    # print("=" * 66)
    for i in range(len(SENTENCES)):
        for j in range(i + 1, len(SENTENCES)):
            s = cosine_similarity(vectors[i], vectors[j])
            print(f"  {s:+.3f}   「{SENTENCES[i]}」 ↔ 「{SENTENCES[j]}」")
    #
    # ⭐ 重点看这三对的分数：
    #    第1句 ↔ 第2句  （意思几乎一样，用词不同）→ 应该很高
    #    第1句 ↔ 第3句  （一个说天气一个说火锅）  → 应该很低
    #    第4句 ↔ 第5句  （都关于AI/技术）         → 中等偏高
    #
    # ⚠️ 如果第1句和第2句的分数不高，先别改代码 ——
    #    去想想：是不是模型对中文不好？换个模型试试？（这是个真实的选型问题）

    print("\n" + "=" * 66)
    print("语义搜索")
    print("=" * 66)
    for q in ["我想找个好天气出门", "有什么好吃的", "AI 是怎么工作的"]:
        print(f"\n查询：{q}")
        for score, sent in semantic_search(q, SENTENCES, vectors):
            print(f"  {score:+.3f}  {sent}")


if __name__ == "__main__":
    main()

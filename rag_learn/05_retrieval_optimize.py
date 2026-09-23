"""第3阶段 Day5 · 05_retrieval_optimize.py —— 检索优化（RAG 第 5 步的调优）

【任务】（来自 阶段计划/03_RAG入门 Day5）
    ✅ 理解 MultiQueryRetriever（多角度查询）
    ✅ 理解 ContextualCompressionRetriever（压缩冗余）
    ✅ 调 retrieval k 值（3/5/10），观察影响、对比效果
    验收：知道什么时候用 MultiQuery，什么时候用压缩

【⭐ 但今天第一件事，不是写检索器，是建"评分标准"】
    先回顾两个已经发生过的打脸现场：
      · Day3：我凭 3 个查询断言"分数应该到 0.6+" → 实测只到 0.52，我错了
      · 你第 2 阶段自己测出：**单次性能对比毫无意义**（同一实验两次结果相反）
    结论：**优化之前必须先有固定测试集 + 可重复的指标**，
          否则你调完 k 值、加完 MultiQuery，根本不知道是变好还是变坏。

【今天要理解的三个东西（先想清楚再写代码）】
    ① MultiQuery（多角度查询）本质是什么？
       —— 让 LLM 把你的问题**改写成几个不同说法**，各自去检索，再合并结果。
          为什么有用：一个查询向量只代表一种"说法"，落在向量空间里的一个点；
                     换个说法可能就落到别的区域，能把原本捞不到的块捞上来。
       ⭐ 你自己就能实现：调 LLM 生成 3 个改写 → 分别 store.search → 合并去重。

    ② ContextualCompression（压缩）本质是什么？
       —— 检索回来的 3 大段里，可能只有一两句和问题相关。压缩就是**把不相关的剔掉**，
          只留有用部分再喂给模型。两种做法：
            · 便宜的：按相似度分数卡阈值（纯阈值过滤）
            · 贵的：让 LLM 逐块判断"这段能不能回答问题"（精排/抽取）
       ⭐ 这就是你 Day4 那个 0.42 分块该不该进 prompt 的问题的正式解法。

    ③ k 值（召回条数）的取舍：
       —— k 小 → 精准但可能漏；k 大 → 召回全但稀释上下文、更贵更慢。
          今天用测试集把这条曲线画出来。

【⚠️ 老规矩：改完跑一遍，git diff 看一眼有没有忘删的旧代码。】
"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool import chat                     # 你以后写 MultiQuery 会用到

ROOT = Path(__file__).resolve().parent
STORE_PATH = ROOT / "store.json"

_day3 = importlib.import_module("03_vector_store")


# ============================================================
# 第 0 步：固定测试集（我写好了）
# ============================================================
# ⭐ 出题原则：每题的答案必须**真的在你语料里**，并标注它出自哪个文件。
#    expect = None 表示"语料里没有" —— 这种题考察的是**该不该拒答**。
#
# ⚠️ 我 Day4 犯过的错：出了"Chroma 默认用什么距离"这种题目，
#    答案只在我笔记本里、不在 data/ 里，测的其实是"检索不到"而不是"检索不准"。
TEST_SET = [
    # ---- rag_intro.txt ----
    ("什么是 RAG？", "rag_intro.txt"),
    ("RAG 的七个步骤分别是什么？", "rag_intro.txt"),
    ("离线索引阶段包含哪四步？", "rag_intro.txt"),
    ("大语言模型有哪些绕不开的短板？", "rag_intro.txt"),
    ("为什么说语义相似不等于有用？", "rag_intro.txt"),
    ("如果知识库里有恶意指令会怎样？", "rag_intro.txt"),
    # ---- agent_notes.txt ----
    ("智能体为什么必须外挂工具？", "agent_notes.txt"),
    ("工具调用的完整循环包含哪几步？", "agent_notes.txt"),
    ("流式返回下 tool_calls 有什么特殊之处？", "agent_notes.txt"),
    ("arguments 是字符串还是字典？", "agent_notes.txt"),
    ("稳定信息为什么不靠检索？", "agent_notes.txt"),
    # ---- sample20.pdf ----
    ("get_weather 是怎么查询天气的？", "sample20.pdf"),
    ("这本书面向哪些读者？", "sample20.pdf"),
    # ---- 语料里没有（考察拒答）----
    ("今天杭州天气怎么样？", None),
    ("智谱 embedding 单次最多几条？", None),
]


# ⭐ 阈值只能有一个（这条是你自己发现的，很关键）
#
#   之前我写了两个值：判定拒答用 REJECT_SCORE=0.45、过滤低分块用 min_score=0.30，
#   这会造成荒唐情形：0.30~0.45 之间的块**被喂给了模型**，而评测却认为
#   "这道题本该拒答" —— **你测的和你跑的不是同一个系统**，评测就失去意义了。
#
#   所以统一成一个 MIN_SCORE：既是过滤标准，也是"该不该拒答"的标准。
#   它的含义是：**低于这个分数 = 不相关**。
MIN_SCORE = 0.30


def _is_hit(kept, expect) -> bool:
    """判定**过滤之后**剩下的块是否算"正确"。注意参数是 kept，不是原始 hits。

    · expect 是文件名 → 该文件还在 = 命中（recall@k）
    · expect 是 None  → 语料里根本没有答案，**过滤后一条不剩** = 正确拒答

    ⚠️ 我第一版的两个错都在这里：
      ① 负样本写成 `expect not in sources`，而 None 永远不在字符串列表里 → 白送分
      ② 判定用的阈值和过滤用的阈值不是一个值 → 测的和跑的不是一回事
    """
    if expect is None:
        return len(kept) == 0
    return expect in [m["source"] for _, _, m in kept]


def evaluate(store, top_k: int = 5, queries=None,
             min_score: float = MIN_SCORE, verbose: bool = False) -> dict:
    """跑一遍测试集，返回指标。**我写好了，你不用改。**

    流程刻意和线上**完全一致**：先检索 → 再按 min_score 过滤 → 才判定对错。
    这样测出来的数字才是"系统真实表现"，而不是"理想情况下的表现"。

    指标（工业界的 recall@k）：
        hit：正确答案**在过滤后还活着**的题目占比
    """
    queries = queries or TEST_SET
    hit, miss = 0, []
    for q, expect in queries:
        raw = store.search(q, top_k=top_k)
        kept = compress_hits(raw, min_score=min_score)
        ok = _is_hit(kept, expect)
        if ok:
            hit += 1
        else:
            miss.append((q, expect, sorted({m["source"] for _, _, m in kept})))
        if verbose:
            flag = "✅" if ok else "❌"
            print(f"    {flag} {q}   期望={expect}  "
                  f"保留 {len(kept)}/{len(raw)} 块  来源={sorted({m['source'] for _, _, m in kept})}")
    return {"k": top_k, "min_score": min_score, "hit": hit, "total": len(queries),
            "rate": hit / len(queries), "miss": miss}


# ============================================================
# 第 1 步：k 值对比（★ 交给你）
# ============================================================
def compare_k(store, k_list=(3, 5, 10)):
    """对比不同 k 值的命中率。

    ★ TODO(1)
    三行就能写完：
        for k in k_list:
            r = evaluate(store, top_k=k, verbose=True)
            print(f"  k={k}: 命中 {r['hit']}/{r['total']} = {r['rate']:.0%}")
    然后自己回答：
        ① 命中率随 k 增大是单调上升吗？为什么？
        ② 如果 k=10 命中率更高，为什么不直接把 k 设成 10？
           （提示：想想 prompt 会变多长、模型会不会被无关内容带偏、钱）
        ③ 有没有哪道题 k 加到 10 还是捞不到？为什么？（这种题就是 MultiQuery 的目标客户）
    """
    for k in k_list:
              r = evaluate(store, top_k=k, verbose=True)
              print(f"  k={k}: 命中 {r['hit']}/{r['total']} = {r['rate']:.0%}")

# ============================================================
# 第 2 步：手搓 MultiQuery —— 多角度查询（★ 交给你）
# ============================================================
MULTI_QUERY_PROMPT = """你是一个检索助手。请把用户的问题改写成 {n} 个不同角度的检索查询。

要求：
1. ⭐ **尽量不使用原问题里的原词**，改用同义的专业术语或上位概念
2. ⭐ 从**不同的侧面**提问：问定义 / 问原因 / 问做法 / 问限制
3. 每行一个，不要编号，不要解释
4. 保持原意，不要引入问题里没有的概念

反例（这样做等于白改，三个查询几乎落在同一个位置）：
  原问题「为什么说语义相似不等于有用？」
  ✗ 语义相似度为什么不能等同于有用性
  ✗ 语义相近为什么未必能带来实际用处

正例（换术语、换侧面）：
  原问题「为什么说语义相似不等于有用？」
  ✓ 检索结果不相关的常见原因
  ✓ 相似度指标的适用边界
  ✓ 相关性判断有什么局限

用户问题：{question}"""


def multi_query_search(store, question: str, n: int = 3, top_k: int = 3):
    """把问题改写成 n 个查询，分别检索，合并去重，返回 [(分数, 文本, 身份证), ...]。

    ★ TODO(2) —— 四步
        ① 让 LLM 生成 n 个改写查询
           data = chat([{"role": "user", "content": MULTI_QUERY_PROMPT.format(...)}])
           text = data["choices"][0]["message"]["content"]
           然后用 text.strip().splitlines() 拆成一行一个查询
           ⚠️ 记得把空行过滤掉（LLM 有时会多吐空行）
        ② 把原问题也加进去一起检索（⭐ 很重要：改写可能跑偏，原问题才是保底）
        ③ 每个查询各自 store.search(q, top_k=top_k)
        ④ 合并结果并**去重**
           ⭐ 去重的 key 用什么？想想你 Day3 给每块存了什么唯一的东西
              —— start_index 单独不够（不同文件可能撞号），要 source + start_index 组合
           ⭐ 同一块被多个查询命中时，分数怎么算？（取最大值最简单）

    返回：按分数从大到小排好的列表（形状和你 store.search 一样，方便直接喂给 build_prompt）
    """
    data = chat([{"role": "user", "content": MULTI_QUERY_PROMPT.format(n=n, question=question)}])
    text = data["choices"][0]["message"]["content"]
    queries = [line.strip() for line in text.strip().splitlines() if line.strip()]
    queries.append(question)  # 保底原问题  

    best={}
    for q in queries:
        for score,chunk,meta in store.search(q, top_k=top_k):
            key=(meta["source"],meta["start_index"])
            if key not in best or score>best[key][0]:
                best[key]=(score,chunk,meta)

    return sorted(best.values(), key=lambda x: x[0], reverse=True)

# ============================================================
# 第 3 步：手搓"压缩" —— 低分过滤 + 可选精排（★ 交给你）
# ============================================================
def compress_hits(hits, min_score: float = 0.0, keep_top: int | None = None):
    """把检索结果压缩：过滤掉低分块、只保留前几条。

    ★ TODO(3)
        ① min_score：低于这个分数的块直接扔掉
           ⭐ 这就是你 Day4 那个"0.42 分的块该不该进 prompt"的正式解法。
              但阈值设多少？**别拍脑袋** —— 用测试集跑几组值看命中率怎么变。
        ② keep_top：最多留几条（None 表示不限）
        ③ 返回过滤后的列表
    """
    filtered = [hit for hit in hits if hit[0] >= min_score]
    if keep_top is not None:
        filtered = filtered[:keep_top]
    return filtered


# ============================================================
# 第 4 步：LangChain 的两种检索器对照（我写好了，你只管跑）
# ============================================================
def build_langchain_store():
    """把你 Day3 存好的数据装进 LangChain 的 Chroma（第 4 步对照要用）。我写好了。

    ⚠️ 两个必须记住的点（Day4 都踩过）：
       1. `add_texts` 要**连 metadatas 一起传**，否则检索回来的 Document 没有来源
       2. `collection_metadata={"hnsw:space": "cosine"}` 不写就是 l2
    """
    import chromadb
    from langchain_chroma import Chroma
    from langchain_core.embeddings import Embeddings

    from tool import get_embedding

    class ZhipuEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return _day3.embed_in_batches(list(texts))   # ← 必须分批（智谱 ≤64 条）
        def embed_query(self, text):
            return get_embedding(text)

    local = _day3.SimpleVectorStore()
    local.load(STORE_PATH)
    store_lc = Chroma(
        collection_name="day5",
        embedding_function=ZhipuEmbeddings(),
        client=chromadb.EphemeralClient(),
        collection_metadata={"hnsw:space": "cosine"},
    )
    store_lc.add_texts(texts=local.chunks, metadatas=local.metadatas,
                       ids=[f"c{i}" for i in range(len(local.chunks))])
    return store_lc


def build_llm():
    """建一个 LangChain 的模型对象（指向 DeepSeek）。我写好了。"""
    import os
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=0,
    )


def langchain_retrievers(store_lc, question: str):
    """用 LangChain 的 MultiQueryRetriever 和 ContextualCompressionRetriever 做同一件事。

    ⚠️ 这两个都是"包装器"：MultiQueryRetriever 包住一个基础 retriever，
       内部自己调 LLM 生成改写查询 —— 和你 TODO(2) 干的事一模一样，
       只是它把"改写 + 检索 + 去重"都封好了。
       看懂它内部的活儿，你才知道什么时候**不该**用它（比如你想自己控制改写数量/合并策略）。
    """
    from langchain_classic.retrievers import ContextualCompressionRetriever
    from langchain_classic.retrievers.document_compressors import LLMChainExtractor
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    llm = build_llm()
    base = store_lc.as_retriever(search_kwargs={"k": 3})

    # ① MultiQuery：自动生成多个改写查询，全部检索后去重
    mq = MultiQueryRetriever.from_llm(retriever=base, llm=llm)
    docs = mq.invoke(question)
    print(f"\n  🔗 MultiQueryRetriever 命中 {len(docs)} 块（基础 retriever 只给 3 块）：")
    for d in docs[:6]:
        print(f"     {_day3.source_label(d.metadata)}  {d.page_content[:38]!r}")

    # ② 压缩：用 LLM 抽出每块里真正相关的句子（不相关就输出「无关」）
    compressor = LLMChainExtractor.from_llm(llm)
    cc = ContextualCompressionRetriever(base_compressor=compressor,
                                        base_retriever=base)
    compressed = cc.invoke(question)
    print(f"\n  🔗 ContextualCompressionRetriever 压缩后 {len(compressed)} 块：")
    for d in compressed[:6]:
        print(f"     {_day3.source_label(d.metadata)}  {d.page_content[:60]!r}")


def main():
    store = _day3.SimpleVectorStore()
    store.load(STORE_PATH)
    print(f"✅ 已加载向量库：{len(store.chunks)} 块")

    # 每一步单独兜住 NotImplementedError ——
    # 这样你写完一个 TODO 就能立刻看到那一步的结果，不用等全部写完。
    steps = [
        ("第 1 步 k 值对比", lambda: compare_k(store)),
        ("第 2 步 手搓 MultiQuery", lambda: None),      # ← 写完 TODO(2) 后替换成你的调用
        ("第 3 步 压缩", lambda: None),                 # ← 写完 TODO(3) 后替换成你的调用
    ]
    for label, fn in steps:
        print("\n" + "=" * 66)
        print(label)
        print("=" * 66)
        try:
            fn()
        except NotImplementedError as e:
            print(f"  ⏳ 还没写：{e}")

    print("\n" + "=" * 66)
    print("第 4 步：LangChain 的两种检索器（我写好了）")
    print("=" * 66)
    langchain_retrievers(build_langchain_store(), "什么是 RAG？")

    print("\n" + "=" * 66)
    print("验收（做完自己回答）")
    print("=" * 66)
    print("  1) k 从 3 加到 10，命中率涨了多少？代价是什么？")
    print("  2) MultiQuery 对哪类问题有效、对哪类无效？")
    print("  3) 什么时候该用压缩？压缩的代价是什么？（提示：想想 LLM 调用次数）")
    print("  4) 这三个手段（k 值 / MultiQuery / 压缩）分别解决检索链路的哪一环？")


if __name__ == "__main__":
    main()

"""第3阶段 Day4 · 04_rag_chain.py —— 把检索和生成拼起来（RAG 第 5、6、7 步）

【任务】（来自 阶段计划/03_RAG入门 Day4）
    ✅ 实现一个完整 RAG 链：提问 → 检索相关块 → 拼 Prompt → LLM 生成
    ✅ 让 LLM 在答案里标注引用来源
    ✅ 对比「纯 LLM」和「RAG」的回答差异
    验收：能说出 RAG 比纯 LLM 强在哪、弱在哪

【⭐ 今天要走的第 5、6、7 步】
    5. 检索 Retrieve  ← Day3 的 store.search()
    6. 拼接 Augment   ← 今天写：把捞到的块拼进 prompt
    7. 生成 Generate  ← tool.py 的 chat() / stream_chat()（你早就有了）

【⭐ 和前面学的连起来】
    · Day6 你测出「语义相似 ≠ 有用」→ 所以第 6 步拼 prompt 时，
      **除了检索到的资料，还要带上"资料里没有就说没有"这类硬约束**
      —— 这正是 Day7 assistant.py 里"动态 system prompt"的同一个手法。
    · Day7 你的 system prompt 每轮重建，今天这个也是每轮重建：
      资料每次都不同 → prompt 每次都不同。

【⭐⭐ 今天的核心矛盾：把资料给模型之后，它还是可能编】
    第 6 步的 prompt 是整个 RAG 里最容易翻车的地方。三种常见翻车：
      ① 资料里没有答案，模型硬编 → 必须显式允许它说"不知道"
      ② 资料有好几块，模型把不同块的数字拼起来 → 要求它只能引用原文
      ③ 资料本身是错的/过时的 → RAG 不会修复，只会忠实地传递错误
    所以 RAG 是「降低幻觉概率」而不是「消除幻觉」—— 第 ① 条就是今天要挡的。

【⚠️ 老规矩：改完跑一遍，git diff 看一眼有没有忘删的旧代码。】
"""

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool import chat, stream_chat            # noqa: E402

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STORE_PATH = ROOT / "store.json"

# Day3 的向量库（同样用 importlib 加载数字开头的模块）
_day3 = importlib.import_module("03_vector_store")


# ============================================================
# 第 0 步：把 Day3 存好的库读进来（我写好了）
# ============================================================
def load_store():
    if not STORE_PATH.exists():
        raise SystemExit(
            f"❌ 找不到 {STORE_PATH}\n"
            f"   先跑一遍 03_vector_store.py —— 它会把向量存到这里。\n"
            f"   （这样做的好处：不用每天重复调 API 转向量，省钱省时间）"
        )
    store = _day3.SimpleVectorStore()
    store.load(STORE_PATH)
    print(f"✅ 已加载向量库：{len(store.chunks)} 块")
    return store


# ============================================================
# 第 1 步：拼 Prompt（第 6 步 Augment）
# ============================================================
def build_prompt(question: str, hits: list[tuple[float, str, dict]]) -> list[dict]:
    """把检索到的资料和用户问题拼成 messages 列表。

    返回形如：
        [
          {"role": "system", "content": "<资料> ... </资料>\\n\\n<规则> ... </规则>"},
          {"role": "user",   "content": question},
        ]

    ⭐ 注意 hits 的形状变了（Day3 加了身份证）：
        hits = [(相似度, 块文本, {"source":..., "page":..., "start_index":...}), ...]

    ★ TODO(1) —— 两件事
      ① 把 hits 里的块拼成一段文字
         提示："\\n\\n".join(...) 把列表拼成用空行分隔的大字符串
         ⭐ **每块前面标上来源**，这样模型才能引用（Day4 的任务要求"标注引用来源"）：
             [来源：sample20.pdf 第 7 页]
             块正文……
         用 XML 标签把整段资料包起来（你第 2 阶段学过 XML 组织长 prompt）：
             <资料>\n{这里放拼好的资料}\n</资料>
         为什么要包标签？你 Day2 的结论：结构化的价值在可维护性和抗注入。

      ② system 里必须写上**规则**，至少三条：
         - 只根据资料回答；资料里没有就说「资料中没有提到」
         - 不要编造资料里没有的数字
         - **回答时用「第 X 页」的形式标注依据来自哪一块**
         ⭐ 第 1 条最重要：不给它，模型遇到"资料里没有"的问题就会开始编。

    提示：别忘 return 一个 **列表**（两个 dict），不是字符串。
    """
    raise NotImplementedError("TODO(1)：还没写")


# ============================================================
# 第 2 步：完整的 RAG 链（第 5 + 6 + 7 步）
# ============================================================
def answer(store, question: str, k: int = 3, stream: bool = False) -> str:
    """一句提问 → 返回答案字符串。

    ★ TODO(2) —— 三步，顺序别乱
        ① 检索：hits = store.search(question, top_k=k)
                ⚠️ 现在每个 hit 是**三件套** (分数, 文本, 身份证)，
                   如果你还用两件套解包（`for score, text in hits`）会直接报
                   ValueError: too many values to unpack —— 这是好事，报错比默默出错强
        ② 拼装：messages = build_prompt(question, hits)
        ③ 生成：调 tool.py 里的 chat() 或 stream_chat()
           · 非流式：data = chat(messages)，正文在 data["choices"][0]["message"]["content"]
           · 流式：  text = stream_chat(messages)，直接返回字符串
           （你 Day7 写过这两种，照抄你自己当时的取法）

    ⭐ 顺便想一下：为什么要传 stream 参数？
       流式可以让用户立刻看到字在往外蹦 —— 但你这个函数要"返回完整字符串"，
       两个目标有冲突。你怎么处理？（提示：想想 stream_chat 的返回值是什么）
    """
    raise NotImplementedError("TODO(2)：还没写")


# ============================================================
# 第 3 步：对照实验 —— 纯 LLM vs RAG（这部分我写好了，你只管跑）
# ============================================================
def compare(store, questions: list[str]):
    print("\n" + "=" * 66)
    print("对照实验：纯 LLM（不给资料） vs RAG（给资料）")
    print("=" * 66)
    for q in questions:
        print(f"\n{'─' * 66}")
        print(f"【问题】{q}")

        # ---------- 纯 LLM ----------
        data = chat([{"role": "user", "content": q}], temperature=0)
        plain = data["choices"][0]["message"]["content"]
        print(f"\n  🅰 纯 LLM：{plain.strip()[:200]}")

        # ---------- RAG ----------
        rag = answer(store, q, k=3)
        print(f"\n  🅱 RAG：{rag.strip()[:200]}")

        # ⭐ 观察点：
        #   问第 1 题（资料里有的），两者可能都答得不错 —— 因为这是常识题。
        #   一定要问第 2 题（资料里的细节，比如 Chroma 默认距离），
        #   纯 LLM 会凭印象答，RAG 会照原文答 —— **差异在这里才显出来**。
        #   第 3 题（资料里没有的），RAG 应该说「资料中没有提到」。


# ============================================================
# 第 4 步：LangChain / LCEL 对照（我写好了，用来让你看框架做了什么）
# ============================================================
def langchain_version(question: str):
    """同样的 RAG，用 LangChain 写一遍。"""
    import os

    import chromadb
    from langchain_chroma import Chroma
    from langchain_core.embeddings import Embeddings
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_openai import ChatOpenAI

    from tool import get_embedding

    class ZhipuEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return get_embedding(list(texts))

        def embed_query(self, text):
            return get_embedding(text)

    store = Chroma(
        collection_name="day4",
        embedding_function=ZhipuEmbeddings(),
        client=chromadb.EphemeralClient(),
        collection_metadata={"hnsw:space": "cosine"},   # ⚠️ 不写就是 l2
    )
    chunks = load_store().chunks
    store.add_texts(chunks, ids=[f"c{i}" for i in range(len(chunks))])

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=0,
    )
    retriever = store.as_retriever(search_kwargs={"k": 3})

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "只根据下面的资料回答，资料里没有就说「资料中没有提到」。\n\n资料：\n{context}"),
        ("user", "{question}"),
    ])
    # ⭐ 这一串 | 就是 LCEL。注意它和你手搓版的对应关系：
    #      {"context": retriever | format_docs, "question": ...}   ← 你的第 1、2 步
    #      | prompt                                                 ← 你的 build_prompt
    #      | llm | StrOutputParser()                                ← 你的 chat() + 取正文
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain.invoke(question)


def main():
    store = load_store()

    questions = [
        "RAG 是什么？",                      # 资料里有（也是常识，两边都答得出）
        "Chroma 默认用什么距离度量？",         # 资料里的细节 —— 差异在这里显形
        "今天杭州天气怎么样？",                # 资料里完全没有 —— 该说「没提到」
    ]

    compare(store, questions)

    print("\n" + "=" * 66)
    print("LangChain / LCEL 版（同样的数据、同样的问题）")
    print("=" * 66)
    for q in questions:
        print(f"\n  【问题】{q}")
        print(f"  🔗 {langchain_version(q).strip()[:200]}")

    print("\n" + "=" * 66)
    print("验收（做完自己回答）")
    print("=" * 66)
    print("  1) 第 3 题 RAG 有没有老实说「资料中没有提到」？没有的话，是 prompt 的哪句话没写好？")
    print("  2) 手搓版和 LCEL 版，代码量差多少？LCEL 帮你省掉的是哪几件事？")
    print("  3) RAG 一定比纯 LLM 好吗？举一个 RAG 反而更差的场景。")


if __name__ == "__main__":
    main()

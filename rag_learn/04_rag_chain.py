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
# 身份证 → 人话的渲染函数定义在 Day3：
#   ⭐ 谁定义数据结构，谁提供它的渲染方式 —— 不要在用到它的每个脚本里各写一份。
#      （我就是因为在 04 里又写了一遍，才漏改了 03 的展示，把 "-1 页" 打给了你看）
_source_label = _day3.source_label


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
    lines = [
        f"{_source_label(meta)}\n{text}"
        for score, text, meta in hits         # ← 三件套，Day3 改的，别忘了 score 也要占位
    ]

    docs = "\n\n".join(lines)                  # 用空行把各行隔开

    system = (
        "<资料>\n" + docs + "\n</资料>\n\n"
        "<规则>\n"
        "1. 只根据上面的资料回答；资料里没有就说「资料中没有提到」\n"
        "2. 不要编造资料里没有的数字\n"
        "3. 回答时用资料里标出的来源说明依据（有页码写「第 X 页」，没有页码就写文件名）\n"
        "</规则>"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]


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
    hits = store.search(question, top_k=k)
    messages = build_prompt(question, hits)
    if stream:
        return stream_chat(messages)
    else:
        data = chat(messages)
        return data["choices"][0]["message"]["content"]


# ============================================================
# 打印长度控制
# ============================================================
# ⚠️ 只影响终端输出，**不影响模型实际返回的内容**
#    想看全文就调大（比如 2000），或者设成 None 表示完全不截断
PREVIEW_LEN = 600


def _cut(text: str) -> str:
    """把答案裁短以便阅读 —— 这是【展示层】的事，和数据本身无关。"""
    t = text.strip()
    if PREVIEW_LEN is None or len(t) <= PREVIEW_LEN:
        return t
    return f"{t[:PREVIEW_LEN]}…\n      （↑ 仅为显示截断，全文共 {len(t)} 字）"


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
        print(f"\n  🅰 纯 LLM：{_cut(plain)}")

        # ---------- RAG ----------
        rag = answer(store, q, k=3)
        print(f"\n  🅱 RAG：{_cut(rag)}")

        # ⭐ 观察点：
        #   问第 1 题（常识），两者都答得不错 —— 看不出差别。
        #   一定要问第 2 题（你语料里的细节，比如"离线索引的四步"），
        #   纯 LLM 会凭印象给个差不多的答案，RAG 会照你语料的原文答 —— **差异在这里才显出来**。
        #   第 3 题（语料里没有的），RAG 应该说「资料中没有提到」。
        #
        #   ⚠️ 出题原则：第 2 题必须是**你语料里真有的**细节。
        #      我一开始出的"Chroma 默认用什么距离"就是反例 —— 那是我笔记里的结论，
        #      不在 data/ 里，问它只会得到"资料中没有提到"。


# ============================================================
# 第 4 步：LangChain / LCEL 对照（我写好了，用来让你看框架做了什么）
# ============================================================
def build_langchain_chain():
    """用 LangChain 搭一条同样的 RAG 链，**返回 chain 本身**（可反复调用）。

    ⭐ 为什么返回 chain 而不是直接 invoke？
       因为建库要花 77 次 Embedding 调用。如果写成"每次提问就重建一次库"，
       问 3 个问题就要花 231 次 —— 又慢又费钱。
       **建库是"建库"，提问是"提问"，两件事要分开。**（Day3 你存 store.json 是同一个道理）
    """
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
            # ⚠️⚠️ 这里必须自己分批！实测踩到的坑：
            #    LangChain 会把**全部**文档一次性交给 embed_documents
            #    （官方示例用 OpenAI 的 embedding，一次能传几千条，所以它不分批也没事）
            #    但智谱单次上限 64 条 → 77 块直接 400：
            #        {"error":{"code":"1214","message":"input数组最大不得超过64条"}}
            #    ⭐ 结论：框架只负责"调用你实现的接口"，**分批的责任在你这个实现里**。
            #       下面直接复用你 Day3 手写的分批函数 —— 手搓的成果在这里派上用场。
            return _day3.embed_in_batches(list(texts))

        def embed_query(self, text):
            return get_embedding(text)

    local = load_store()                     # 你 Day3 存好的库（chunks + vectors + metadatas）
    store = Chroma(
        collection_name="day4",
        embedding_function=ZhipuEmbeddings(),
        client=chromadb.EphemeralClient(),
        collection_metadata={"hnsw:space": "cosine"},   # ⚠️ 不写就是 l2
    )
    # ⚠️⚠️ 建库时必须**连 metadata 一起存**！
    #    我第一版写的是 store.add_texts(chunks, ids=...) —— 只传了文本，
    #    结果检索回来的 Document 是"裸的"（没有 source/page），
    #    format_docs 一取就炸：KeyError: 'source'
    #    ⭐ 教训：metadata 不会自己跟过去，**建库时你不给它，它就没有**。
    #
    # 📌 顺带一个真相：LangChain 这层包装底下就是原生 chromadb 的 Collection
    #    （`store._collection` 你甚至能直接调它的 add()），所以"适配器"这个词不是比喻。
    #    这里用公开 API add_texts 就够了（会重新调一次 Embedding，77 条 = 2 批）。
    store.add_texts(
        texts=local.chunks,
        metadatas=local.metadatas,
        ids=[f"c{i}" for i in range(len(local.chunks))],
    )

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=0,
    )
    retriever = store.as_retriever(search_kwargs={"k": 3})

    def format_docs(docs):
        # ⚠️⚠️ 框架不会自动帮你做"引用来源"！这里必须自己把 metadata 拼进上下文。
        #    不拼的话，模型根本不知道页码，自然引用不出来 ——
        #    这就是官方 Full code 里为什么要单独写 f"# Source: {doc.metadata.get('source')}"。
        return "\n\n".join(f"{_source_label(d.metadata)}\n{d.page_content}" for d in docs)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "只根据下面的资料回答；资料里没有就说「资料中没有提到」。\n"
         "不要编造资料里没有的数字。\n"
         "回答时用资料里标出的来源说明依据（有页码写「第 X 页」，没有页码就写文件名）。\n\n"
         "<资料>\n{context}\n</资料>"),
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
    return chain


def main():
    store = load_store()

    questions = [
        "RAG 是什么？",                       # ① 常识题：资料里有，但其实两边都答得出 → 看不出差别
        "RAG 的离线索引阶段包含哪四步？",       # ② 资料里的细节：纯 LLM 会凭印象答 → 差异在这里显形
        "今天杭州天气怎么样？",                 # ③ 资料里完全没有 → 该说「资料中没有提到」
    ]

    compare(store, questions)

    print("\n" + "=" * 66)
    print("LangChain / LCEL 版（同样的数据、同样的问题）")
    print("=" * 66)
    chain = build_langchain_chain()          # ← 建一次，用三次
    for q in questions:
        print(f"\n  【问题】{q}")
        print(f"  🔗 {_cut(chain.invoke(q))}")

    print("\n" + "=" * 66)
    print("验收（做完自己回答）")
    print("=" * 66)
    print("  1) 第 3 题 RAG 有没有老实说「资料中没有提到」？没有的话，是 prompt 的哪句话没写好？")
    print("  2) 手搓版和 LCEL 版，代码量差多少？LCEL 帮你省掉的是哪几件事？")
    print("  3) RAG 一定比纯 LLM 好吗？举一个 RAG 反而更差的场景。")


if __name__ == "__main__":
    main()

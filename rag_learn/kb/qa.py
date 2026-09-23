"""kb/qa.py —— Day7 第 2 步：多轮问答 + 引用来源（★ 核心交给你）

【目标】一句话问答：问题 → （消解）→ 检索 → 拼 prompt → 生成 → 答案带来源

【⭐ 这个文件是把 Day3/4/6 拼起来的胶水】
    · Day3 给了你 source_label（把身份证渲染成人话）
    · Day4 给了你 build_prompt（资料 + 规则的组装）
    · Day6 给了你 format_history（对话历史渲染）
    你在这里要做的，是把它们**串起来**，而不是重写。

【和 Day4 的区别】
    Day4 的 store 是手搓的 SimpleVectorStore（内存 + JSON）。
    这里换成 Chroma：查询方式变了，但**返回的形状要对齐**——
    仍然是 [(分数, 文本, 身份证), ...]，这样 build_prompt 才能直接吃。
"""

import ingest      # ⚠️ search() 里要用它拿集合（我第一版漏了这行，才导致 NameError）

from common import (DEFAULT_COLLECTION, build_prompt, chat, day3, day4, day6,
                    get_embedding, source_label)


def search(question: str, k: int = 5, collection_name: str = DEFAULT_COLLECTION):
    """去 Chroma 里检索，返回 [(相似度, 文本, 身份证), ...]。

    ★ TODO(3)
    ⚠️ 这里有个**必须处理的坑**：Chroma 返回的是**距离**不是相似度。
       Day3 你实测过：设了 `hnsw:space=cosine` 之后，distance = 1 - 相似度，
       而且**越小越像**。
       → 所以你要换算成相似度、并按**从大到小**排序，
         否则 build_prompt 拿到的是倒序的，模型会先看到最不相关的资料。

    步骤：
        ① qv = get_embedding(question)
        ② col = ingest.get_collection(collection_name)
           res = col.query(query_embeddings=[qv], n_results=k,
                           include=["documents", "distances", "metadatas"])
           ⚠️ Chroma 返回的是**嵌套列表**（因为可以一次查多个问题），
              所以取 [0]：res["documents"][0] / res["distances"][0] / res["metadatas"][0]
        ③ 三件事一一对应 zip 起来：
             相似度 = 1 - dist
             文本   = doc
             身份证 = meta
           组装成 (相似度, 文本, 身份证)，再按相似度**从大到小**排
    """
    qv = get_embedding(question)
    col  = ingest.get_collection(collection_name)
    res = col.query(query_embeddings=[qv],n_results=k,include=["documents","distances","metadatas"])
    distances = res["distances"][0]
    documents = res["documents"][0]
    metadatas = res["metadatas"][0] 
    return sorted([(1 - dist, doc, meta) for dist, doc, meta in zip(distances, documents, metadatas)], reverse=True)




def answer(question: str, history: list[dict] | None = None,
           k: int = 5, collection_name: str = DEFAULT_COLLECTION,
           use_condense: bool = True) -> dict:
    """一轮完整问答。返回 {"question","standalone","hits","answer"}。

    ★ TODO(4) —— 四步，和 Day6 的 answer_with_history 几乎一样
        ① 消解：standalone = day6.condense_question(history or [], question)
                （use_condense=False 时直接用 question）
        ② 检索：hits = search(standalone, k=k, collection_name=...)
        ③ 拼装：messages = build_prompt(standalone, hits)
                ⭐ 然后把历史塞进 system（照 Day6 的写法）：
                   messages[0]["content"] += "\\n\\n<对话历史>\\n" + day6.format_history(history or []) + "\\n</对话历史>"
                   （历史为空时可以不塞）
        ④ 生成：data = chat(messages) → data["choices"][0]["message"]["content"]

    ⭐ Day6 你已经写过一遍了 —— **这里不要重新发明**，照着那次的思路写。
       区别只有一个：检索从"手搓库"换成了"Chroma"。
    """
    standalone = day6.condense_question(history or [], question) if use_condense else question
    hits = search(standalone, k=k, collection_name=collection_name)
    messages = build_prompt(standalone, hits)
    messages[0]["content"] += "\n\n<对话历史>\n" + day6.format_history(history or []) + "\n</对话历史>"
    data = chat(messages)
    answer_text = data["choices"][0]["message"]["content"]
    return {"question": question, "standalone": standalone, "hits": hits, "answer": answer_text}


def answer_stream(question: str, history: list[dict] | None = None,
                  k: int = 5, collection_name: str = DEFAULT_COLLECTION):
    """流式版（可选加分项）：边生成边往外吐字。

    ⭐ 你 Day7（第 2 阶段）已经处理过"流式 + 工具调用"这个难题，
       这里简单得多 —— 流式问答不需要工具调用，直接 stream_chat 就行。
       想加就加，不加也不影响验收。
    """
    raise NotImplementedError("（可选）还没写")

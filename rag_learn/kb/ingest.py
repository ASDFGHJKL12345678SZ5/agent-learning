"""kb/ingest.py —— Day7 第 1 步：上传 PDF → 自动建索引（★ 核心交给你）

【目标】把任意一个 PDF 变成 Chroma 里的「向量 + 文本 + 身份证」，并可重复使用。

【⭐ 和 Day3 的区别在哪】
    Day3 的 `build_chunks` 写死了 `PDF_PATH`（只处理我们那 20 页素材），
    而且用的是**手搓的 SimpleVectorStore + store.json**。

    项目版要改成：
      · 接受**任意路径**（用户上传什么就索引什么）
      · 用 **Chroma 持久化**（PersistentClient）—— 关掉程序再打开，库还在
      · 支持**多个 PDF**（不同文件进同一个集合，靠 metadata 的 source 区分）

【⭐ 为什么用 Chroma 而不继续用 JSON】
    你 Day3 已经实测过两件事：
      · 手搓库和 Chroma 的检索结果**完全一致**（所以不是"准不准"的问题）
      · 但 JSON 每次保存要**整体重写**，而且只能全量扫
    项目要长期用、要能增量加文件 → 该用数据库了。
"""

import shutil
from pathlib import Path

from common import (CHROMA_DIR, DEFAULT_COLLECTION, EMBED_BATCH, day3,
                    get_embedding)


def get_client():
    """拿到 Chroma 的持久化客户端（目录不存在会自动创建）。我写好了。"""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(name: str = DEFAULT_COLLECTION):
    """拿到（或创建）一个集合。

    ⚠️ 建集合时必须显式写 `hnsw:space=cosine` —— 不写就是 l2
       （Day3 实测的坑，你也验证过"不写的话分数完全不一样"）
    """
    client = get_client()
    return client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})


def chunk_pdf(pdf_path: Path, size: int = 400, overlap: int = 80) -> list[dict]:
    """读 PDF → 逐页切块 → 每块带 source / page / start_index。

    ★ TODO(1)
    这几乎就是你 Day3 `build_chunks` 的翻版，只改一处：**PDF 路径从参数拿**，不再写死。

        ① pages = day3.load_pdf_pages(Path(pdf_path))
        ② 对每一页，按 Day2 的分块器切开（day3._day2.split_overlap）
           ⭐ 但注意：`day3.build_chunks` 里的切块逻辑是**重复写了一遍**的。
              你可以直接复用 `day3._chunks_from_text(...)` —— 它是 Day3 里抽出来的辅助函数，
              签名是 (text, source, page, size, overlap) → list[dict]
              **复用它，别抄第三遍。**
        ③ source 用 pdf_path.name（文件名），page 用真实页码，start_index = j * (size - overlap)
        ④ 空块过滤（Day1 那两页图/表页的教训）
    """
    path = Path(pdf_path)     
    chunks = []
    for page in day3.load_pdf_pages(path):      # 直接遍历 dict，不用 enumerate
        chunks.extend(
            day3._chunks_from_text(page["text"], path.name, page["page"], size, overlap)
        )
    return chunks


def ingest_pdf(pdf_path: str | Path, collection_name: str = DEFAULT_COLLECTION) -> dict:
    """把 PDF 写进 Chroma，返回统计信息。**框架我写好了，核心逻辑你补。**

    ★ TODO(2) —— 三步
        ① chunks = chunk_pdf(path)          ← 用你刚写的 TODO(1)
        ② 取文本列表 texts = [c["text"] for c in chunks]
           分批算向量：vectors = day3.embed_in_batches(texts)
           ⭐ 复用 Day3 的分批函数 —— 智谱单次上限 64 条，超了直接 400
        ③ 写进 Chroma：
           col = get_collection(collection_name)
           col.add(
               ids=[...],           # ⭐ 每个块要一个**全局唯一**的 id
                                    #   建议 f"{文件名}_{页码}_{start_index}"
                                    #   想清楚：为什么不能用 "c0"/"c1" 这种序号？
                                    #   （提示：第二次上传另一个 PDF 时会怎样？）
               documents=texts,
               embeddings=vectors,
               metadatas=[{"source": c["source"], "page": c["page"],
                           "start_index": c["start_index"]} for c in chunks],
           )
    返回：{"collection": 名字, "chunks": 块数, "pages": 页数}
    """
    chunks = chunk_pdf(pdf_path)
    texts = [c["text"] for c in chunks]
    vectors = day3.embed_in_batches(texts)
    col = get_collection(collection_name)
    col.add(
        ids=[f"{c['source']}_{c['page']}_{c['start_index']}" for c in chunks],
        documents=texts,
        embeddings=vectors,
        metadatas=[{"source": c["source"], "page": c["page"],
                    "start_index": c["start_index"]} for c in chunks],
    )
    return {"collection": collection_name, "chunks": len(chunks), "pages": len(set(c["page"] for c in chunks))}

    

def collection_stats(name: str = DEFAULT_COLLECTION) -> dict:
    """看一下库里现在有什么。我写好了 —— 方便你随时确认索引进去了。"""
    col = get_collection(name)
    n = col.count()
    sources = {}
    if n:
        got = col.get(include=["metadatas"], limit=min(n, 5000))
        for m in got["metadatas"]:
            sources[m["source"]] = sources.get(m["source"], 0) + 1
    return {"collection": name, "chunks": n, "by_source": sources}


def reset_collection(name: str = DEFAULT_COLLECTION):
    """清空一个集合（重新索引时用）。我写好了。"""
    client = get_client()
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return get_collection(name)


def reset_all():
    """把整个 chroma_db 目录删掉（彻底重来）。我写好了。"""
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    return get_collection()


if __name__ == "__main__":
    # 自检：能看到当前库里有几块就行
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(collection_stats())

"""第3阶段 Day3 · 03_vector_store.py —— 向量化 + 存库（RAG 第 3、4 步）

【任务】（来自 阶段计划/03_RAG入门 Day3）
    ✅ 把分好的块转成向量（Embedding）
    ✅ **自己写一个向量库**：存进去、查出来
    ✅ 再用 Chroma 做一遍同样的事，对照差距
    验收：能解释向量检索的原理（余弦相似度）

【⭐ A 方案：从今天起，每块都要带「身份证」（metadata）】
    你 Day2 的 `split_overlap` 返回的是**纯字符串列表** —— 切完就不知道这块来自哪。
    但 Day4 要拼 prompt、Day7 要"答案带引用来源"，都必须知道"这块从哪来"。

    所以今天给每个块配一张身份证：
        {
          "source":      "sample20.pdf",   # 来自哪个文件
          "page":        7,                # 第几页
          "start_index": 1200,             # 在这一页里的字符偏移
        }

【⭐⭐ 一个重要的工程取舍：为什么"按页切"而不是"全文切"】
    你 Day2 才刚学过「分块是要摆脱 PDF 的物理边界」，今天怎么又按页切了？

    因为**溯源需要边界**。如果一块跨了第 5、6 两页，那它的 "page" 到底写几？
    写上 5 就漏了 6，两个都写又没法用。

    ⭐ 这不是我编的 —— 官方入门教程就是这么干的（`split_documents(docs)` 是
       对**每一页**分别切，所以你才能看到这样的 metadata）：
           metadata={'page': 4, 'source': '...nke-10k-2023.pdf', 'start_index': 3125}

    **所以这是个权衡，不是对错**：
        全文切 → 语义更完整，但**溯源会糊**
        按页切 → 溯源精确，但**跨页的语义会被切断**
    真实系统多半选后者，因为它更在意"能不能给出引用"。

【⭐ Day2 的成果直接拿来用】
    下面用 importlib 加载 02_split_text.py。
    ⚠️ 模块名叫 "02_split_text"，**不能写 `import 02_split_text`**
       —— `import` 语句要求标识符不能以数字开头，但 importlib 走字符串就没限制。

【🔒 实测约束（别重踩）】
    智谱 embedding-3 **单次请求最多 64 条**：
        n=64  → ✅ 200
        n=65  → ❌ 400  input数组最大不得超过64条
    所以必须自己分批。

【⚠️ 老规矩：改完跑一遍，git diff 看一眼有没有忘删的旧代码。】
"""

import importlib
import json
import math      
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool import get_embedding

DATA_DIR = Path(__file__).resolve().parent / "data"
PDF_PATH = DATA_DIR / "sample20.pdf"

_day2 = importlib.import_module("02_split_text")     # Day2 的分块器

EMBED_BATCH = 64          # ← 实测上限，不是随便写的数字


# ============================================================
# 第 0 步：读 PDF（我写好了，和你 Day1 写的是同一个逻辑）
# ============================================================
def load_pdf_pages(path: Path) -> list[dict]:
    """逐页读 PDF，返回 [{"page": 0, "text": "..."}, ...]"""
    from pypdf import PdfReader

    reader = PdfReader(path)
    return [
        {"page": i, "text": page.extract_text() or ""}
        for i, page in enumerate(reader.pages)
    ]


# ============================================================
# 第 1 步：切分 + 贴身份证（支持多个来源）
# ============================================================
def _chunks_from_text(text: str, source: str, page: int,
                      size: int, overlap: int) -> list[dict]:
    """把一段文本切成块并贴上身份证。

    ⭐ 为什么单独抽一个函数？
       因为"切块 + 贴身份证"这套逻辑，TXT 和 PDF 的每一页**完全一样**。
       不抽出来的话，将来加第三种来源（Word、网页）就得再抄一遍 —— 抄三遍就必然改漏。
    """
    step = size - overlap
    out = []
    for j, chunk in enumerate(_day2.split_overlap(text, size, overlap)):
        if not chunk.strip():
            continue
        out.append({
            "text": chunk,
            "source": source,
            "page": page,
            "start_index": j * step,
        })
    return out


def build_chunks(size: int = 400, overlap: int = 80) -> list[dict]:
    """读 data/ 下的**所有文档**（TXT + PDF）→ 逐单位切块 → 每块带 source/page/start_index。

    ⭐ 元数据 schema（三类来源用同一套字段，值不同）：
        TXT  → {"source": "rag_intro.txt",  "page": -1, "start_index": 0}
        PDF  → {"source": "sample20.pdf",   "page": 7,  "start_index": 800}

    ⭐⭐ 为什么 TXT 的 page 写 -1 而不是 0 或 None？
        ① 不能写 None —— Chroma 的 metadata 只接受基础类型，塞 None 直接报错
           （这条约束写在下面 chroma_compare 的注释里）
        ② 不写 0 —— "第 0 页"看起来像"第一页"，会误导后面做引用来源的逻辑
        ③ 写 -1 —— 一眼就能看出"这个来源没有页的概念"

        ⭐ 这就是真实工程里的问题：**不同来源的元数据 schema 往往不一致，
          你必须自己定一套规范，并在代码里写清楚。** 想清楚比写得快重要。
    """
    result = []

    # ---------- 来源 ①：纯文本（没有"页"的概念）----------
    for txt_path in sorted(DATA_DIR.glob("*.txt")):
        text = txt_path.read_text(encoding="utf-8")
        result.extend(_chunks_from_text(text, txt_path.name, -1, size, overlap))

    # ---------- 来源 ②：PDF（逐页切，page 是真实页码）----------
    for page in load_pdf_pages(PDF_PATH):
        result.extend(
            _chunks_from_text(page["text"], PDF_PATH.name, page["page"], size, overlap)
        )

    return result


# ============================================================
# 第 2 步：批量向量化（要分批！）
# ============================================================
def embed_in_batches(texts: list[str], batch_size: int = EMBED_BATCH) -> list[list[float]]:
    """把一堆文本转成向量，每 batch_size 条发一次请求，最后拼成一个列表返回。

    ★ TODO(2)
    结构（照 Day2 那个"按固定长度切片"的套路来）：
        vectors = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]        # 切出这一批
            vectors.extend(get_embedding(batch))     # 传列表 → 返回一组向量
            print(...)                               # 长任务要有进度反馈
        return vectors

    ⚠️ 用 extend 不是 append：
       append 会把"一组向量"当成一个元素塞进去 → 长度变成 2 而不是 100。
    """
    vectors = []
    for i in range(0,len(texts),batch_size):
        batch = texts[i:i+batch_size]
        vectors.extend(get_embedding(batch))
        print(f"已向量化{min(i+batch_size,len(texts))}组 / {len(texts)}组")
    return vectors


def cosine_similarity(a: list, b: list) -> float:
   
    
    cos=sum( x * y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
    return cos

# ============================================================
# 第 3 步：自己写向量库（今天多了 metadata）
# ============================================================
class SimpleVectorStore:
    """最小的向量库：存"文本块 + 向量 + 身份证"，支持保存/加载/检索。"""

    def __init__(self):
        self.chunks: list[str] = []            # 文本块
        self.vectors: list[list[float]] = []   # 一一对应的向量
        self.metadatas: list[dict] = []        # 🆕 一一对应的身份证

    def add(self, chunks: list[str], vectors: list[list[float]], metadatas: list[dict]):
        """把块、向量、身份证一起存进来。

        ★ TODO(3)
        ① 三个列表分别 extend 进对应的属性
        ② assert 三者长度相等 —— 不相等说明前面某一步错位了。
           想想为什么这里要"越早炸越好"：
           如果向量和块错位，检索**不会报错**，只会悄悄返回张冠李戴的结果，
           你看到的是"答案很离谱"，但根因在很远的地方。
        """
        self.chunks.extend(chunks)
        self.vectors.extend(vectors)
        self.metadatas.extend(metadatas)
        assert len(self.chunks)==len(self.vectors)==len(self.metadatas)



    def search(self, query: str, top_k: int = 3) -> list[tuple[float, str, dict]]:
        """拿问题去库里找最像的 top_k 块。

        返回 [(相似度, 块文本, 身份证), ...]，按相似度从大到小。

        ★ TODO(4)
        你 Day6 写过核心（余弦），今天多一个字段：
            ① query 转向量：get_embedding(query)
            ② 和 self.vectors 里每一个算余弦相似度
            ③ 把 (分数, 文本, metadata) 三件套配对、排序、取前 top_k
            ⭐ 提示：zip(self.vectors, self.chunks, self.metadatas) 一次拿到三件套
        """
        query_vector = get_embedding(query)
        scores = [(cosine_similarity(query_vector, vec), chunk, meta) for vec, chunk, meta in zip(self.vectors, self.chunks, self.metadatas)]
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]
    
    def save(self, path: Path):
        """存到磁盘（JSON）。

        ★ TODO(5)
        JSON 只能存"字典/列表/字符串/数字"，你的三个属性都是列表，
        塞进一个 dict 再 dump 就行。
        提示：json.dump({...}, f, ensure_ascii=False)   ← 不加中文会变 \\uXXXX
        """
        with open(path,"w",encoding="utf-8") as f:
            json.dump({
                "chunks":self.chunks,
                "vectors":self.vectors,
                "metadatas":self.metadatas
            },f,ensure_ascii=False
            )

    def load(self, path: Path):
        """从磁盘读回来（和 save 完全对称）。

        ★ TODO(6)
        ⚠️ 顺便想一个真实的坑：JSON 的 key 一定是**字符串**。
           你的 metadata 里 "page": 3 存进去、读出来还是 int（值不受影响），
           但如果哪天你拿字符串当 key 用了数字，读回来就永远变不回去了。
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.chunks = data["chunks"]
            self.vectors = data["vectors"]
            self.metadatas = data["metadatas"]


# ============================================================
# 第 4 步：Chroma 对照（我写好了，你只管跑）
# ============================================================
# ============================================================
# 身份证 → 人话（内部表示 vs 展示表示）
# ============================================================
def source_label(meta: dict) -> str:
    """把身份证渲染成**给人看的人话**。

        [来源：sample20.pdf 第 7 页]   ← PDF，有页码
        [来源：rag_intro.txt]          ← TXT，没有页的概念（page 存的是 -1）

    ⭐ 为什么必须单独渲染，不能直接拼 "-1 页"？
       内部表示和展示表示是两件不同的事：
         · 存库用 `page: -1` 编码"没有页" —— 一眼能判断，Chroma 也能按它过滤
         · 但**给人看、给模型看**时必须是自然语言
       实测踩过的坑：直接拼 "-1 页" 时，模型同一次运行里写了两套说法
       （"第 -1 页" / "rag_intro.txt 第-1页"），甚至把 -1 圆场成"第 1 页"——
       它在猜这个负数是什么意思。换成 [来源：rag_intro.txt] 之后引用立刻稳定了。

    ⭐ 这个函数放在**定义 metadata 的模块里**（而不是每个用它的地方各写一份）——
       谁定义数据结构，谁就负责它的渲染方式。
    """
    name = meta.get("source", "未知来源")
    if meta.get("page", -1) < 0:
        return f"[来源：{name}]"
    return f"[来源：{name} 第{meta['page']}页]"


# ============================================================
def chroma_compare(chunks: list[str], vectors: list[list[float]],
                   metadatas: list[dict], queries: list[str]):
    """把同一批数据存进 Chroma，用同样的查询对比结果。

    ⚠️ 三个坑（我先替你踩了）：
       1. Chroma **默认距离是 l2（欧氏），不是余弦**！
          要余弦必须建库时写 metadata={"hnsw:space": "cosine"}。
       2. 设了 cosine 之后返回的是**距离**：distance = 1 - 相似度，**越小越像**。
          所以下面打印时做了 1 - dist 换算，别被数字大小搞反。
       3. Chroma 的 metadata 只能存**基础类型**（str/int/float/bool），
          塞 dict 或 None 进去会直接报错。
    """
    import chromadb

    client = chromadb.EphemeralClient()
    col = client.create_collection("compare", metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[f"c{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=vectors,
        metadatas=metadatas,          # 🆕 身份证一起存
    )

    print("\n" + "=" * 66)
    print("Chroma 对照（距离已换算成相似度）")
    print("=" * 66)
    for q in queries:
        res = col.query(query_embeddings=[get_embedding(q)], n_results=3,
                        include=["documents", "distances", "metadatas"])
        print(f"\n  查询：{q}")
        for doc, dist, meta in zip(res["documents"][0], res["distances"][0],
                                   res["metadatas"][0]):
            print(f"    sim={1 - dist:+.4f}  {source_label(meta)}  {doc[:45]!r}")


# ============================================================
# 主流程
# ============================================================
def main():
    chunks_data = build_chunks()
    chunks = [c["text"] for c in chunks_data]
    metadatas = [{"source": c["source"], "page": c["page"],
                  "start_index": c["start_index"]} for c in chunks_data]
    print(f"块数 = {len(chunks)}")

    vectors = embed_in_batches(chunks)
    print(f"向量数 = {len(vectors)}，维度 = {len(vectors[0])}")

    store = SimpleVectorStore()
    store.add(chunks, vectors, metadatas)

    queries = ["什么是 RAG？", "怎么防止模型乱编？", "模型怎么调用外部工具？"]
    print("\n" + "=" * 66)
    print("自建向量库的检索结果（带来源）")
    print("=" * 66)
    for q in queries:
        print(f"\n  查询：{q}")
        for score, chunk, meta in store.search(q, top_k=3):
            print(f"    sim={score:+.4f}  {source_label(meta)}  {chunk[:45]!r}")

    # 存盘 + 读回来验证
    path = DATA_DIR.parent / "store.json"
    store.save(path)
    store2 = SimpleVectorStore()
    store2.load(path)
    print(f"\n存盘后读回来：{len(store2.chunks)} 块 / "
          f"{len(store2.vectors)} 向量 / {len(store2.metadatas)} 身份证")

    chroma_compare(chunks, vectors, metadatas, queries)

    print("\n" + "=" * 66)
    print("验收（做完自己回答）")
    print("=" * 66)
    print("  1) 自建库和 Chroma 的检索结果一样吗？为什么？")
    print("  2) 自建库查一条要算多少次余弦？库里 100 万块时呢？")
    print("  3) 那为什么还要用 Chroma？它多给了你什么？（至少说两条）")
    print("  4) 检索结果里的「第X页」是怎么冒出来的？Day2 的纯字符串分块能给出它吗？")


if __name__ == "__main__":
    main()

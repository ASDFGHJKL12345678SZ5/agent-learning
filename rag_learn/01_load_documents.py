"""第3阶段 Day1 · 01_load_documents.py —— 把文档读进内存（RAG 第 1 步）

【任务】（来自 阶段计划/03_RAG入门 Day1）
    ✅ 理解 RAG 是什么、7 步流程
    ✅ 用 pypdf 读 PDF
    ✅ 读 TXT / MD
    验收：能手画出 RAG 流程图

【⭐ RAG 的 7 步 —— 今天只做第 1 步】
    离线索引（提问之前就跑完，属于"建库"）
        1. 加载 Load      ← 今天在这里：把文件变成一段段文字
        2. 分块 Split      ← Day2
        3. 向量化 Embed    ← Day3（你 Day6 已经写过 get_embedding）
        4. 存库 Store      ← Day3
    在线查询（用户每问一次都要走一遍）
        5. 检索 Retrieve
        6. 拼接 Augment   （把捞到的原文塞进 prompt）
        7. 生成 Generate

【⭐ 和前面学的连起来】
    · 第 2 阶段 Day6 你手写过语义搜索（余弦相似度），那是第 5 步的裸内核。
    · 那时候"库"只有 6 句硬编码的句子；现在要把"库"换成真正的文件。
    · 所以今天做的事，本质是：把 get_embedding 的输入，从 6 句字符串换成"从文件里读出来的段落"。

【今天要认得的新东西】
    pathlib.Path   —— 路径对象，见 make_sample_pdf.py 的注释（已经写好了，先看那个文件）
    pypdf.PdfReader —— 读 PDF 的第三方库

【⚠️ 老规矩：先跑一遍再下结论。改完记得 git diff 看一眼有没有忘删的旧代码。】

【⭐ 极简范例（无关领域）：读一个文件的骨架长这样 —— 换汤不换药】
    # def load_csv(path):
    #     with open(path, encoding="utf-8") as f:   # encoding 不给会乱码/报错
    #         return f.read()
    # 你要写的 load_text 和它几乎一样，只是路径是 Path 对象（open 也认 Path）。
"""

from pathlib import Path

from pypdf import PdfReader

# 本文件所在目录 / data —— Path 的 / 运算符就是拼路径
DATA_DIR = Path(__file__).resolve().parent / "data"


# ============================================================
# 第 1 步：读纯文本（TXT / MD 都是纯文本）
# ============================================================
def load_text(path: Path) -> str:
    """读一个文本文件，返回它的全部内容（字符串）。

    ★ TODO(1)
    提示：三步走 —— open(path, encoding="utf-8") → f.read() → return
          用 with 打开，退出时自动关文件（你 Day3 学过）。

    ⚠️ encoding 一定要显式写 "utf-8"，否则 Windows 默认按 GBK 读，中文全乱码。
    """
    with open(path, encoding="utf-8") as f:
        return f.read()


# ============================================================
# 第 2 步：读 PDF —— 逐页抠文本
# ============================================================
def load_pdf(path: Path) -> list[dict]:
    """读一个 PDF，返回 [{"page": 0, "text": "..."}, {"page": 1, "text": "..."}, ...]

    ⭐ 为什么返回的结构比 load_text 复杂？
       因为 PDF 是"页"为单位的，页码是之后做引用来源（第 3 页）要用的信息。
       TXT 没有页的概念，所以返回裸字符串就够了 —— 这是数据本身的差异，不是代码风格。

    ★ TODO(2)
    pypdf 的用法（三个关键点，其余自己拼）：
        reader = PdfReader(path)        # 打开
        reader.pages                    # 一页一个对象，能 for 循环，也能 len()
        page.extract_text()             # 把这一页的文字抠出来 → 字符串
    然后：enumerate 拿到页码，把每页组成一个 dict，append 进列表，最后 return。

    ⚠️ extract_text() 偶尔返回 None 或者全是空白（扫描件/图片页没有文字层）。
       先别急着处理，跑起来看到空页再想怎么办 —— 遇到问题再解决。
    """
    reader = PdfReader(path)
    pages = []
    for page_number, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": page_number,"text": text})

    return pages


# ============================================================
# 第 3 步：统计一下你读到了什么（跑通验证用）
# ============================================================
def report(name: str, text: str):
    """打印一份文档的概况。这个我写好了，你直接调用。"""
    chars = len(text)
    print(f"  📄 {name}")
    print(f"     字符数：{chars}")
    print(f"     前 80 字：{text[:80].strip()!r}")


def main():
    print("=" * 66)
    print("Day1：把文档读进来")
    print("=" * 66)

    # ---------- TXT ----------
    for filename in ["rag_intro.txt", "agent_notes.txt"]:
        path = DATA_DIR / filename
        if not path.exists():
            print(f"  ⚠️ 找不到 {path}")
            continue
        text = load_text(path)
        report(filename, text)

    # ---------- PDF ----------
    pdf_path = DATA_DIR / "sample20.pdf"
    if pdf_path.exists():
        pages = load_pdf(pdf_path)
        print(f"\n  📕 sample20.pdf")
        print(f"     页数：{len(pages)}")
        total = sum(len(p["text"]) for p in pages)
        print(f"     总字符数：{total}")
        for p in pages[:2]:
            print(f"     第 {p['page']} 页前 60 字：{p['text'][:60].strip()!r}")
    else:
        print(f"\n  ⚠️ 还没有 {pdf_path} —— 先跑 make_sample_pdf.py 生成它")

    print("\n" + "=" * 66)
    print("验收：闭上眼说一遍 RAG 的 7 步，并说出哪几步是「建库」、哪几步是「查库」")
    print("=" * 66)


if __name__ == "__main__":
    main()

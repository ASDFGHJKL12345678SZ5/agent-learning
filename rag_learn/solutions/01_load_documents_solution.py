r"""⚠️ 参考答案 —— 先自己写完再看，否则这关就白过了。

用法：
    1. 先在 01_load_documents.py 里把你的版本写完、跑出来
    2. 再打开这个文件对照
    3. 重点不是"我写得对不对"，而是**不一样的地方说明了什么**

跑法（注意是文件自己的 __main__，不依赖 01）：
    .\.venv\Scripts\python.exe -X utf8 solutions\01_load_documents_solution.py
"""

from pathlib import Path

from pypdf import PdfReader

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_text(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_pdf(path: Path) -> list[dict]:
    reader = PdfReader(path)
    result = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        result.append({"page": i, "text": text})
    return result


def report(name: str, text: str):
    print(f"  📄 {name}")
    print(f"     字符数：{len(text)}")
    print(f"     前 80 字：{text[:80].strip()!r}")


if __name__ == "__main__":
    print("=" * 66)
    print("参考答案运行结果")
    print("=" * 66)

    for filename in ["rag_intro.txt", "agent_notes.txt"]:
        report(filename, load_text(DATA_DIR / filename))

    pages = load_pdf(DATA_DIR / "sample20.pdf")
    print("\n  📕 sample20.pdf")
    print(f"     页数：{len(pages)}")
    total = sum(len(p["text"]) for p in pages)
    print(f"     总字符数：{total}")
    for p in pages[:2]:
        print(f"     第 {p['page']} 页前 60 字：{p['text'][:60].strip()!r}")

    # 顺带把"空页"到底长什么样打出来，方便对照
    print("\n  --- 空页排查 ---")
    for p in pages:
        if len(p["text"].strip()) < 100:
            print(f"     第 {p['page']:>2} 页只有 {len(p['text'].strip())} 个非空白字符")

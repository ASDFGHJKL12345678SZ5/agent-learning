r"""kb/cli.py —— Day7 命令行入口（我写好了）

用法：
    cd D:\Desktop\Practice\rag_learn

    # 1) 建索引（第一次用、或者换文档时）
    .\.venv\Scripts\python.exe -X utf8 kb\cli.py ingest data\sample20.pdf

    # 2) 看库里有什么
    .\.venv\Scripts\python.exe -X utf8 kb\cli.py stats

    # 3) 问答（默认命令）
    .\.venv\Scripts\python.exe -X utf8 kb\cli.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # 让 common/ingest/qa 可导入

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import ingest
import qa


def cmd_stats():
    s = ingest.collection_stats()
    print(f"集合：{s['collection']}   共 {s['chunks']} 块")
    for src, n in sorted(s["by_source"].items()):
        print(f"  · {src}：{n} 块")
    if not s["chunks"]:
        print("  ⚠️ 库是空的 —— 先跑：cli.py ingest <某个.pdf>")


def cmd_ingest(pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        print(f"❌ 找不到文件：{path}")
        return 1
    r = ingest.ingest_pdf(path)
    print(f"✅ 索引完成：{r['collection']}  页数={r['pages']}  块数={r['chunks']}")
    cmd_stats()
    return 0


def cmd_chat():
    s = ingest.collection_stats()
    if not s["chunks"]:
        print("⚠️ 库是空的，先建索引：cli.py ingest <某个.pdf>")
        return 1
    print(f"知识库：{s['chunks']} 块，来自 {len(s['by_source'])} 个文件")
    print("输入问题开始提问；/clear 清空对话历史，/exit 退出\n")

    history = []
    while True:
        try:
            q = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q in ("/exit", "/quit"):
            break
        if q == "/clear":
            history.clear()
            print("（历史已清空）\n")
            continue

        r = qa.answer(q, history=history)
        if r["standalone"] != q:
            print(f"  \033[90m[消解为：{r['standalone']}]\033[0m")
        print(f"\n助手：{r['answer'].strip()}")
        print("\n  \033[90m引用来源：\033[0m")
        seen = set()
        for score, _, meta in r["hits"]:
            label = qa.source_label(meta)
            if label in seen:
                continue
            seen.add(label)
            print(f"    \033[90m{label}  sim={score:+.4f}\033[0m")
        print()

        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": r["answer"]})
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return cmd_chat()
    cmd, *rest = argv
    if cmd == "stats":
        cmd_stats()
        return 0
    if cmd == "ingest":
        if not rest:
            print("用法：cli.py ingest <pdf 路径>")
            return 1
        return cmd_ingest(rest[0])
    if cmd == "reset":
        ingest.reset_collection()
        print("✅ 已清空集合")
        return 0
    if cmd == "chat":
        return cmd_chat()
    print(f"未知命令：{cmd}（可用：ingest / stats / chat / reset）")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

r"""rag_learn · fetch_docs.py —— 把入门级官方文档抓到本地（工具类脚本，已写好）

【为什么要抓下来】
    1. 官方文档站默认展示的是 1.x + deepagents 的进阶内容，进去容易迷路；
       这里硬编码了**经过筛选的入门页**，直接读，不用自己在站里找。
    2. 存成本地 .md：不用联网也能读，而且**纯文本没有网页的干扰**。
    3. 以后这些 .md 还能直接当 RAG 的语料用（它们本身就是带结构的文档）。

【⭐ 一个背景知识：你阶段计划里那条链接为什么变了】
    python.langchain.com/docs/tutorials/rag/     ← 计划里写的（老地址）
        ↓ 302 重定向
    docs.langchain.com/oss/python/deepagents/rag ← 现在是 "RAG with Deep Agents"
    所以你打开看到的是 deepagents/子智能体那一套 —— 不是你水平不够，是地址被改了。
    真正给入门者的是下面这份 knowledge-base（"语义搜索引擎"）。

【跑法】
    cd D:\Desktop\Practice\rag_learn
    .\.venv\Scripts\python.exe -X utf8 fetch_docs.py
"""

import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")

DOCS_DIR = Path(__file__).resolve().parent / "docs"

# (文件名, 官方 URL, 中文说明)  —— 按阅读顺序排
PAGES = [
    (
        "01_语义搜索引擎.md",
        "https://docs.langchain.com/oss/python/langchain/knowledge-base.md",
        "⭐ 入门首选：加载 → 切分 → Embedding → 向量库 → 检索，九个小节正好对应 Day1-3",
    ),
    (
        "02_检索与RAG架构.md",
        "https://docs.langchain.com/oss/python/langchain/retrieval.md",
        "⭐ 概念篇：检索流水线、2-step RAG / Agentic RAG / Hybrid RAG 三种架构",
    ),
    (
        "03_快速开始.md",
        "https://docs.langchain.com/oss/python/langchain/quickstart.md",
        "LangChain 1.x 快速上手（了解框架全貌，不用精读）",
    ),
    (
        "90_进阶_RAG与DeepAgents.md",
        "https://docs.langchain.com/oss/python/langchain/rag.md",
        "⚠️ 进阶版（你复制的 Full code.py 就出自这里）—— 第 4-5 阶段再看",
    ),
]


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url, note in PAGES:
        try:
            r = httpx.get(url, timeout=30, follow_redirects=True)
            if r.status_code != 200:
                print(f"  ❌ {r.status_code}  {url}")
                continue
            path = DOCS_DIR / filename
            path.write_text(r.text, encoding="utf-8")
            print(f"  ✅ {len(r.text):>7} 字符 → {filename}")
            print(f"       {note}")
        except Exception as e:
            print(f"  ❌ {url}  {type(e).__name__}: {str(e)[:100]}")
    print(f"\n都存到 {DOCS_DIR}")


if __name__ == "__main__":
    main()

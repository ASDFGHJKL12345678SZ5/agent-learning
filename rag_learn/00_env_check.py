r"""第3阶段 Day1 · 00_env_check.py —— 开工前的探针（工具类脚本，已写好）

【为什么每次开工都先跑它】
    你在第 2 阶段养成过一个好习惯：先确认"接口能通"，再往下写代码。
    否则后面报的错可能是"key 过期"，而不是你写的逻辑有问题 —— 白白 debug 半小时。

    RAG 这条链路比第 2 阶段更长（文件 → 向量 → 库 → 检索 → 生成），
    中间任何一环不通，你看到的报错都会长得很像。所以先分层探一遍。

【它检查四件事】
    1. .env 有没有被读到（两个供应商、两套前缀）
    2. 向量接口通不通（Day3 要用；实测 2048 维）
    3. 对话接口通不通（Day4 生成要用）
    4. 素材文件读不读得到（PDF / TXT）

【跑法】
    cd D:\Desktop\Practice\rag_learn
    .\.venv\Scripts\python.exe -X utf8 00_env_check.py
"""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")   # Windows 下防中文乱码（等价于 -X utf8）

import httpx
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()
DATA_DIR = Path(__file__).resolve().parent / "data"


def check_env():
    print("=== 1. 环境变量 ===")
    for k in ["LLM_BASE_URL", "LLM_MODEL", "EMB_BASE_URL", "EMB_MODEL"]:
        print(f"  {k} = {os.getenv(k)}")
    for k in ["LLM_API_KEY", "EMB_API_KEY"]:
        v = os.getenv(k)
        print(f"  {k} = {'已配置（' + str(len(v)) + ' 字符）' if v else '❌ 缺失'}")


def check_embedding():
    print("\n=== 2. 向量接口（Day3 要用）===")
    r = httpx.post(
        f"{os.getenv('EMB_BASE_URL')}/embeddings",
        headers={"Authorization": "Bearer " + os.getenv("EMB_API_KEY")},
        json={"model": os.getenv("EMB_MODEL"), "input": "今天天气真好"},
        timeout=30,
    )
    print("  HTTP", r.status_code)
    if r.status_code == 200:
        vec = r.json()["data"][0]["embedding"]
        print(f"  ✅ 维度 = {len(vec)}，前 3 个 = {[round(x, 4) for x in vec[:3]]}")
    else:
        print("  ", r.text[:200])


def check_chat():
    print("\n=== 3. 对话接口（Day4 生成要用）===")
    r = httpx.post(
        f"{os.getenv('LLM_BASE_URL')}/chat/completions",
        headers={"Authorization": "Bearer " + os.getenv("LLM_API_KEY")},
        json={
            "model": os.getenv("LLM_MODEL"),
            "messages": [{"role": "user", "content": "只回复两个字：收到"}],
            "temperature": 0,
        },
        timeout=60,
    )
    print("  HTTP", r.status_code)
    if r.status_code == 200:
        print("  正文 =", repr(r.json()["choices"][0]["message"]["content"][:60]))
    else:
        print("  ", r.text[:200])


def check_files():
    print("\n=== 4. 素材文件 ===")
    for name in ["rag_intro.txt", "agent_notes.txt"]:
        p = DATA_DIR / name
        if p.exists():
            print(f"  ✅ {name}：{len(p.read_text(encoding='utf-8'))} 字符")
        else:
            print(f"  ❌ 找不到 {p}")

    pdf = DATA_DIR / "sample20.pdf"
    if pdf.exists():
        reader = PdfReader(pdf)
        first = reader.pages[0].extract_text() or ""
        print(f"  ✅ sample20.pdf：{len(reader.pages)} 页，第 1 页 {len(first)} 字符")
    else:
        print("  ⚠️ 没有 sample20.pdf —— 先跑 make_sample_pdf.py 生成")


if __name__ == "__main__":
    check_env()
    check_embedding()
    check_chat()
    check_files()

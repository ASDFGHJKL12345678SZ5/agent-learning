r"""kb/server.py —— Day7 HTTP 服务版（FastAPI，我写好了）

用法：
    cd D:\Desktop\Practice\rag_learn
    .\.venv\Scripts\python.exe -X utf8 -m uvicorn kb.server:app --reload --port 8000

然后打开 http://127.0.0.1:8000/docs 直接点着试（FastAPI 自动生成交互文档）。

接口：
    GET  /stats                  看知识库状态
    POST /upload   （文件上传）   上传 PDF 并自动建索引
    POST /ask      （JSON）       提问
    POST /ask/upload（文件+问题）  上传并立刻提问（一步到位）

⭐ 这就是 FastAPI 的价值：**同一套核心逻辑（ingest / qa），换个壳就能给别人用**。
   CLI 是壳、HTTP 是壳、以后的 Streamlit 也是壳 —— 核心代码一行不用改。
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ingest
import qa
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="PDF 知识库问答", version="1.0")


class AskRequest(BaseModel):
    question: str
    history: list[dict] = []      # [{"role": "user"/"assistant", "content": "..."}]
    k: int = 5


@app.get("/stats")
def stats():
    return ingest.collection_stats()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """上传 PDF → 自动分块索引。"""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "只支持 PDF 文件")
    # 存到临时文件再索引（原文件不用留在项目里）
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        # ⚠️ 索引时的 source 用的是文件名，所以先把临时文件名改回真实文件名，
        #    否则你看到的来源会是 tmpxxxx.pdf —— 引用来源就没意义了
        real_path = tmp_path.with_name(file.filename)
        tmp_path.rename(real_path)
        result = ingest.ingest_pdf(real_path)
    finally:
        real_path.unlink(missing_ok=True)
    return result


@app.post("/ask")
def ask(req: AskRequest):
    """提问：返回答案 + 引用来源。"""
    if not ingest.collection_stats()["chunks"]:
        raise HTTPException(400, "知识库是空的，请先上传 PDF")
    r = qa.answer(req.question, history=req.history, k=req.k)
    return {
        "answer": r["answer"],
        "standalone_question": r["standalone"],
        "sources": [
            {"label": qa.source_label(meta), "score": round(score, 4),
             "preview": text[:80]}
            for score, text, meta in r["hits"]
        ],
    }


@app.post("/ask/upload")
async def ask_with_upload(file: UploadFile = File(...), question: str = ""):
    """上传并立刻提问（一步到位，适合"我就想快速试一下"）。"""
    await upload(file)
    return ask(AskRequest(question=question))


if __name__ == "__main__":
    # ⭐ 加了这一段，"python kb\server.py" 就能直接起服务，不用记 uvicorn 的模块路径。
    #
    #    为什么要加？
    #    因为 `uvicorn kb.server:app` 那条命令**要求当前目录必须是 rag_learn** ——
    #    它靠"当前目录在 sys.path 里"才找得到 kb 这个包 / 目录。
    #    如果在 kb 目录里执行，就会报：
    #        ModuleNotFoundError: No module named 'kb'
    #
    #    这里用 uvicorn.run(app, ...) 直接传 **app 对象**（而不是 "模块:属性" 字符串），
    #    完全绕开模块路径问题 —— **在哪个目录跑都行**。
    #    （代价：不能用 --reload 自动重载；要热重载就用命令行那条）
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

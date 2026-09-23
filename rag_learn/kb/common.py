"""kb/common.py —— Day7 项目的公共底座（我写好了）

【为什么需要这个文件】
    Day7 是个"项目"，拆成了几个文件（ingest / qa / cli / server），
    它们都要用你前 6 天写的东西：tool.py 的 chat/get_embedding、
    03 的向量库、04 的 build_prompt、06 的消解。

    但那些文件叫 "03_vector_store.py"（数字开头），没法写 `import 03_vector_store`。
    所以在这里统一用 importlib 加载一次，其他文件 `from common import ...` 就行。

    ⭐ 这就是"复用"的正确姿势：**复杂/特殊的加载逻辑只写一次**。
       （还记得那个教训吗：渲染函数写两份 → 改一处漏一处）
"""

import importlib
import sys
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parent.parent      # rag_learn/
sys.path.insert(0, str(RAG_ROOT))                      # 让 tool.py 能被导入

tool = importlib.import_module("tool")                 # chat / stream_chat / get_embedding
day3 = importlib.import_module("03_vector_store")      # 向量库 + source_label
day4 = importlib.import_module("04_rag_chain")         # build_prompt
day6 = importlib.import_module("06_conversational_rag")  # condense_question

chat = tool.chat
get_embedding = tool.get_embedding
source_label = day3.source_label
build_prompt = day4.build_prompt
format_history = day6.format_history
EMBED_BATCH = day3.EMBED_BATCH

CHROMA_DIR = RAG_ROOT / "chroma_db"                    # 持久化目录（已在 .gitignore）
DEFAULT_COLLECTION = "pdf_kb"

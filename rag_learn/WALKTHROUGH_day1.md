# Day 1 手把手：写出 `load_text` 和 `load_pdf`

> 用法：打开 `01_load_documents.py`，**照着这份文档一行一行敲**。
> 每敲完一个函数就停下来跑一次，别两个一起写。
> 卡住的判断标准：盯着某一行超过 2 分钟没动 → 看「第二层提示」，还没动 → 直接问我。

---

## 0. 先破心理关：你要写的**不是新知识**

你在 Day 3（第 2 阶段）已经写过这个动作：

```python
# 你 Day3 写的（chat_cli.py 里存历史那段）
with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False)
```

今天只是把 **`"w"` 换成默认的读模式**、把 **`json.dump` 换成 `f.read()`**。
**同一件事的镜像。** 你缺的不是知识，是"敢动手"。

---

## 1. 函数 A：`load_text` —— 填空版

```python
def load_text(path: Path) -> str:
    with open(path, encoding="____①____") as f:
        return ____②____
```

只有两个空。

<details>
<summary>卡住了？点开第二层提示（先自己试 2 分钟）</summary>

- ① 中文文本要靠它才能正确解码，写错会乱码或抛 `UnicodeDecodeError` → **`"utf-8"`**
- ② 你要的是"把整个文件读成一个字符串" → **`f.read()`**
  （对比：`f.readlines()` 返回按行拆开的列表；`f.read()` 返回一整个字符串）

</details>

### 敲完立刻验证

```powershell
cd D:\Desktop\Practice\rag_learn
.\.venv\Scripts\python.exe -X utf8 01_load_documents.py
```

**预期**：TXT 部分先出结果，`rag_intro.txt` 应该显示 **1351 字符**，`agent_notes.txt` 显示 **1123 字符**。
数字对不上 → 先别改代码，检查是不是读到了别的文件。

---

## 2. 函数 B：`load_pdf` —— 先用三行摸清 pypdf

**先别写函数**，在 Python 里裸敲这三行感受一下（这就是"先跑通再优化"）：

```python
from pypdf import PdfReader
from pathlib import Path
reader = PdfReader(Path(r"D:\Desktop\Practice\rag_learn\data\sample20.pdf"))
print(len(reader.pages))          # 20
print(reader.pages[0].extract_text()[:50])   # 第一页前 50 字
```

> ⚠️ 这里我特意用**绝对路径**。因为裸敲这几行时你的"当前目录"是随缘的 —— 这正是你 Day3 踩过的那个坑（相对路径相对于 CWD，不是脚本位置）。

看到输出，你就已经拿到了"页"和"这一页的文字"两个东西。

### 现在填这个空

```python
def load_pdf(path: Path) -> list[dict]:
    reader = PdfReader(path)
    result = []
    for i, page in enumerate(____①____):
        text = ____②____ or ""      # ⚠️ 为什么要有 or "" ？
        result.append({"page": ____③____, "text": text})
    return result
```

<details>
<summary>卡住了？点开第二层提示</summary>

- ① 你要遍历的是"每一页" → **`reader.pages`**
- ② 从这一页里抠文字 → **`page.extract_text()`**
- ③ 你想在结果里记下"这是第几页"，`enumerate` 给的序号变量叫 **`i`**
  （`enumerate` 默认从 **0** 开始 —— 所以第 1 页的 `page` 值是 `0`，不是 `1`。想清楚你要哪种。）

**`or ""` 是干嘛的**：`extract_text()` 遇到纯图片页会返回 `None`（你已经知道第 5、6 页就是这种）。
`None or ""` 的结果是 `""` —— **这是 Python 里"给个兜底默认值"的惯用写法**，不是语法糖，是个习惯。

</details>

### 跑通标志

我**已经把参考答案跑过一遍**（在 `solutions/01_load_documents_solution.py`），下面是真实输出，你的应该长得差不多：

```
  📄 rag_intro.txt
     字符数：1351
     前 80 字：'RAG 是什么\n\nRAG 是 Retrieval-Augmented Generation 的缩写...'
  📄 agent_notes.txt
     字符数：1123
     前 80 字：'智能体为什么必须外挂工具\n\n大语言模型的本质是逐词预测...'

  📕 sample20.pdf
     页数：20
     总字符数：19498
     第 0 页前 60 字：'GITHUB TRENDING\n#1 Repository Of The Day1...'
     第 1 页前 60 字：'章节 关键内容 状\n态\n前言 项目的缘起、背景及读者建议 ✅...'
```

**逐项对答案**：

| 指标 | 应该是 | 对不上的话 |
|---|---|---|
| `rag_intro.txt` | 1351 字符 | 差几字符无所谓（换行符差异）；差很多说明读到别的文件 |
| `agent_notes.txt` | 1123 字符 | 同上 |
| PDF 页数 | **20** | 不是 20 → 循环写错了（比如只处理了第一页） |
| PDF 总字符数 | **19498** | 差得不多没关系；差一半以上 → 某些页没被遍历到 |
| PDF 第 0 页 | `'GITHUB TRENDING...'` | 对不上 → 你可能把 `page` 当成 1-based 了 |

> ⭐ 顺便：参考答案里我多打了一段**空页排查**，输出是这样：
> ```
> 第  5 页只有 73 个非空白字符
> 第  6 页只有 83 个非空白字符
> ```
> 这两页就是 Day 2 分块时要过滤掉的"垃圾块"来源。你在 Day 1 就可以先看看**它们的内容长什么样**——是目录表格？还是纯图片页？看清了 Day 2 才有的放矢。

---

## 3. 三题概念（一句话就行，别查资料）

| # | 问题 | 提示方向 |
|---|---|---|
| Q1 | 哪几步是"建库"、哪几步是"查库"？分界线的意义？ | 7 步里 1-4 在提问之前跑完 |
| Q2 | RAG 为什么**不能根治**幻觉？ | 资料本身可能是错的/没覆盖；prompt 没允许它说"不知道" |
| Q3 | 为什么要分块？至少两个理由 | 上下文窗口；检索的**单位**就是块 |

---

## 4. 常见报错对照表（自己先查，别急着问我）

| 报错 | 根因 | 怎么改 |
|---|---|---|
| `UnicodeDecodeError` | 没写 `encoding="utf-8"`，Windows 默认按 GBK 解码 | 补上编码参数 |
| `FileNotFoundError` | 路径不对。**相对路径相对于 CWD，不是脚本位置** | 用 `DATA_DIR / "文件名"`，别用裸字符串 |
| `AttributeError: 'NoneType' object has no attribute ...` | `extract_text()` 返回了 `None` 而你直接用了它 | 加 `or ""` |
| `NotImplementedError: TODO(1)` | 函数还没写 | 继续写 🙂 |
| 输出的中文字符数是 0 | 打开了文件但没读（比如只 `open` 没 `read`） | 检查 `return` 那行 |

---

## 5. 收工前必做（你的老毛病，提醒一次）

1. **Ctrl+S 确认保存** —— 你出现过三次"说改完了但文件没变"
2. `git diff` 看一眼 —— 确认没有忘删的旧代码
3. 把运行输出贴给我批改

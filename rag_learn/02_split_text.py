"""第3阶段 Day2 · 02_split_text.py —— 文档分块（RAG 第 2 步）

【任务】（来自 阶段计划/03_RAG入门 Day2）
    ✅ 理解固定长度分块、递归字符分块、语义分块的区别
    ✅ 理解 Chunk Size 和 Overlap 的作用
    ✅ 自己写一个分块器，把长文档切开
    验收：能说清 chunk_size=500 vs 200 有什么影响

【⭐ 为什么必须分块 —— 三个理由，一个比一个实际】
    1. 上下文窗口有限：整本书塞不进去
    2. 贵：塞进去的每个字都要钱（token 是按量计费的）
    3. 更重要的 —— 精度：**检索的单位就是"一块"**。
       如果一块里混了五个话题，模型拿到它也很难答准；
       块越小越精准，但太小又会把一句话切断、丢掉上下文。
       chunk_size 就是在"精准"和"完整"之间找平衡。

【⭐ 和 Day1 连起来】
    Day1 你读到的是"页"（PDF 的物理单位）。
    但"页"不是语义单位 —— 一个话题可以从第 3 页中间开始、到第 5 页中间结束。
    分块就是**用语义/长度的边界，替换掉 PDF 的物理边界**。
    ⚠️ 还记得 Day1 发现的"空页"吗（第 5、6 页只有 78 字符）？
       分块器跑完要过滤掉这种块，否则向量库里全是噪声。

【今天要认得的新东西】
    range(start, stop, step)  —— 步长！range(0, 10, 3) → 0, 3, 6, 9
    列表切片 lst[a:b]         —— 越界不报错，会给你到末尾（这个特性今天会用到）
    enumerate(...)            —— 你 Day1 用过，这里对块编号

【⚠️ 老规矩：改完跑一遍，再 git diff 看一眼有没有忘删的旧代码。】

【⭐ 极简范例（无关领域）：把一个长列表按固定长度切成几段】
    # nums = list(range(23))
    # size = 5
    # chunks = [nums[i:i + size] for i in range(0, len(nums), size)]
    # → [[0,1,2,3,4], [5,6,7,8,9], [10,11,12,13,14], [15,16,17,18,19], [20,21,22]]
    # 注意最后一段只有 3 个 —— 长度不足时切片会自动截断，不会报错。
    # 今天的第 1 步，就是把 nums 换成字符串、把 size 换成字符数。**换汤不换药。**
"""

from pathlib import Path

from pypdf import PdfReader

DATA_DIR = Path(__file__).resolve().parent / "data"


# ============================================================
# 第 0 步：把 Day1 的成果拿过来用（这个我写好了）
# ============================================================
def load_pdf_text(path: Path) -> str:
    """读 PDF，把所有页的文字拼成一整个大字符串（用 "\\n" 连接）。"""
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


# ============================================================
# 第 1 步：固定长度分块（无重叠）—— 最朴素的分块器
# ============================================================
def split_fixed(text: str, size: int) -> list[str]:
    """把 text 每 size 个字符切一块，返回 ["第一块", "第二块", ...]。

    ★ TODO(1) —— 照着上面【极简范例】抄结构，只是把列表换成字符串
    三步：
        ① range(0, len(text), size) 生成每个块的起始位置
        ② text[i:i + size] 取这一块
        ③ 收集进列表并 return

    ⚠️ 想清楚：最后一块长度不足 size 怎么办？（提示：切片会自己处理）
    """
    chunks = [text[i:i+size] for i in range(0,len(text),size)]
    return chunks


# ============================================================
# 第 2 步：加上重叠（overlap）—— 这才是真实系统用的
# ============================================================
def split_overlap(text: str, size: int, overlap: int) -> list[str]:
    """带重叠的分块：每块 size 个字符，相邻两块重叠 overlap 个字符。

    ⭐ overlap 是干嘛的？
       分块最大的风险是"把一句话从中间切断"，切点两侧的信息就分家了。
       重叠就是让相邻两块**共享一部分内容**，保证没有信息掉在缝里。

    ★ TODO(2)
    提示：起点的步长不再是 size，而是 size - overlap。
         用 for 循环自己控制起点（或者 range 的第三个参数）。
    然后：assert overlap < size（否则步长是 0，会死循环 —— 先想清楚为什么）
    """
    assert overlap < size, "overlap 必须小于 size，否则会死循环"
    step = size - overlap
    chunks = [text[i:i+size] for i in range(0, len(text), step)]
    if len(chunks)>2 and len(chunks[-1])<overlap:
        chunks.pop()
    return chunks   


# ============================================================
# 第 3 步：看一眼你的块长什么样（跑通验证）
# ============================================================
def show(chunks: list[str], title: str, preview: int = 3):
    """打印分块结果概况 + 前几块预览。这个我写好了。"""
    print(f"\n--- {title} ---")
    print(f"  块数：{len(chunks)}")
    if not chunks:
        print("  ⚠️ 一块都没有，检查你的循环")
        return
    lengths = [len(c) for c in chunks]
    print(f"  块长：最小 {min(lengths)} / 最大 {max(lengths)} / 平均 {sum(lengths) // len(lengths)}")
    # 空块统计 —— Day1 发现的"空页"会在这里现形
    empty = sum(1 for c in chunks if not c.strip())
    print(f"  空块：{empty} 个" + ("  ← 就是那些图/表页，之后要过滤掉" if empty else ""))
    for i, c in enumerate(chunks[:preview]):
        print(f"  [{i}] {c[:60]!r} ...")
    print(f"  ... 最后一块：{chunks[-1][-60:]!r}")


def main():
    text = load_pdf_text(DATA_DIR / "sample20.pdf")
    print(f"整篇文本：{len(text)} 字符")

    # ★ TODO(3)：把下面两行注释打开，跑起来，然后自己回答：
    #   ① chunk_size 从 500 改成 200，块数怎么变？每块里还有完整的一段话吗？
    #   ② 加不加 overlap，块数差多少？重叠区域"多花"了多少字符？
    #
    show(split_fixed(text, 500), "固定分块 size=500")
    show(split_fixed(text, 200), "固定分块 size=200")
    show(split_overlap(text, 500, 100), "重叠分块 size=500 overlap=100")

    print("\n" + "=" * 66)
    print("验收问题（写完自己答一遍）")
    print("=" * 66)
    print("  1) chunk_size 变小，检索会更准还是更不准？代价是什么？")
    print("  2) overlap 能不能设成 400（size=500）？会发生什么？")
    print("  3) 为什么说「分块是在用语义边界替换 PDF 的物理边界」？")


if __name__ == "__main__":
    main()

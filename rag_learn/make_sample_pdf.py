"""rag_learn · make_sample_pdf.py —— 裁一个小 PDF 当练习素材（工具类脚本，可完整给）

【为什么需要它】
    Obsidian 里那本 Hello-Agents 有 61MB、几百页。
    Day1 练「加载 PDF」用它是可以的，但每次跑都要解析整本，慢且占内存。
    所以先切出前 20 页存成 data/sample20.pdf —— 之后所有实验都用这个小文件。

【⭐ 今天要认得的新东西（就两个）】
    1) pathlib.Path   —— 比字符串拼路径更好用的"路径对象"
         Path(__file__)   拿到当前脚本的路径
         Path(__file__).resolve().parent   它所在的目录（绝对路径）
         DATA / "a.txt"   / 运算符重载了，等价于 os.path.join
       你 Day3 学过 __file__ 定位（相对路径相对于 CWD 的坑），Path 就是它的现代写法。

    2) pypdf.PdfReader / PdfWriter —— 第三方库，读 / 写 PDF
"""
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# 你的 vault 里那本大书（绝对路径，不用拷进来，读到内存里切一段就走）
SOURCE_PDF = Path(r"D:\Obsidian Vault\01_agent\Hello-Agents-V1.0.2-20260210.pdf")

# 输出到哪里：本文件所在目录 / data / sample20.pdf
DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_PDF = DATA_DIR / "sample20.pdf"

PAGES_TO_KEEP = 20


def main():
    if not SOURCE_PDF.exists():
        raise SystemExit(f"❌ 找不到源 PDF：{SOURCE_PDF}")

    print(f"源文件大小：{SOURCE_PDF.stat().st_size / 1024 / 1024:.1f} MB")

    reader = PdfReader(SOURCE_PDF)
    print(f"总页数：{len(reader.pages)}")

    writer = PdfWriter()
    for page in reader.pages[:PAGES_TO_KEEP]:
        writer.add_page(page)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_PDF, "wb") as f:
        writer.write(f)

    print(f"✅ 已写出 {OUT_PDF}")
    print(f"   大小：{OUT_PDF.stat().st_size / 1024:.0f} KB，页数：{PAGES_TO_KEEP}")


if __name__ == "__main__":
    main()

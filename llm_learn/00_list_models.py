"""第2阶段 Day1 · 00：先问服务器「我这个 key 能用哪些模型」

为什么先跑这个？
  各家 API 的模型名每隔几个月就改一次（DeepSeek 已经到 V4.1 Flash 了），
  猜名字差一个字符就报 model not found。
  最可靠的做法：直接调 /models 接口，让服务器把清单告诉你。

需要 .env 里至少有 LLM_BASE_URL 和 LLM_API_KEY 两项（LLM_MODEL 可以先不填）。
"""
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")


# ---------- 边界校验：从外部读进来的东西，用之前先检查 ----------
# 这一段的用意：让错误在"离现场最近的地方"爆出来，并给出人话提示。
# 否则你会看到几十行 httpx 内部的调用栈，根本不知道是自己没改 .env。

def check_config():
    if not BASE_URL:
        raise SystemExit("❌ .env 里没读到 LLM_BASE_URL。检查：① 文件确实叫 .env ② 和本文件同目录 ③ 键名没拼错")
    if not API_KEY:
        raise SystemExit("❌ .env 里没读到 LLM_API_KEY。同上检查。")

    # HTTP 请求头只能是 ASCII，中文会导致 UnicodeEncodeError（请求发不出去）
    try:
        API_KEY.encode("ascii")
    except UnicodeEncodeError:
        bad = [c for c in API_KEY if ord(c) > 127]
        raise SystemExit(
            "❌ API Key 里有非 ASCII 字符（中文），HTTP 请求头装不下它。\n"
            f"   发现的可疑字符：{''.join(bad)}\n"
            f"   你现在的值：{API_KEY}\n"
            "   👉 大概率是 .env 里的占位符没换成真 key。\n"
            "      去 https://platform.deepseek.com/api_keys 复制真实 key 粘贴过来。"
        ) from None   # from None：不显示上面那串 UnicodeEncodeError，只留这句人话

    if not API_KEY.startswith("sk-"):
        print(f"⚠️  提醒：API Key 一般以 'sk-' 开头，你现在是 '{API_KEY[:6]}...'，确认一下？\n")

    if API_KEY.strip() != API_KEY:
        raise SystemExit("❌ API Key 首尾有多余空格或换行，请删掉。")


check_config()

# 列出模型的接口路径，OpenAI 兼容协议里固定是 /models
url = f"{BASE_URL}/models"
headers = {"Authorization": f"Bearer {API_KEY}"}

print(f"正在查询: {url}\n")

resp = httpx.get(url, headers=headers, timeout=30)
print("HTTP 状态码:", resp.status_code)

if resp.status_code != 200:
    print("\n❌ 请求失败，服务器原话是：")
    print(resp.text)
    print("\n排查提示：")
    print("  401 → API Key 错了（注意不要多带空格或换行）")
    print("  403 → Key 没权限 / 账户没实名 / 余额为 0")
    print("  404 → BASE_URL 写错了（注意结尾的 /v1）")
    raise SystemExit(1)

data = resp.json()

# OpenAI 兼容格式长这样：{"object": "list", "data": [{"id": "模型名", ...}, ...]}
# 但也有的家直接返回一个列表，所以两种都兼容一下
models = data.get("data", data) if isinstance(data, dict) else data

print(f"\n✅ 你的 key 可用模型共 {len(models)} 个：\n")

ids = []
for m in models:
    mid = m.get("id") if isinstance(m, dict) else str(m)
    ids.append(mid)
    print("  -", mid)

print("\n" + "=" * 60)
print("把你想用的那个名字，填进 .env 的 LLM_MODEL=")
print("=" * 60)

# 顺便把原始 JSON 也打出来，看看除了 id 还有没有别的字段（比如上下文长度）
print("\n===== 原始响应（前 2 条，看看有哪些字段）=====")
print(json.dumps(models[:2], ensure_ascii=False, indent=2))

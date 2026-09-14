"""第2阶段 Day1 · 01：不借助任何 SDK，直接用 httpx 发一次"裸"请求。

目的：把"和 AI 聊天"这件事，还原成一次普普通通的 HTTP POST。
      亲手跑通之后，openai 这个库对你来说就不再是黑盒了。

【怎么用这个文件】
  下面有 3 个 TODO，请你来补，我故意没写。
  每个 TODO 上面都写了提示。补完运行：  python 01_raw_http.py
  卡住了就把报错贴给我，我给你提示，不直接给答案。
"""
import json        # 标准库：处理 JSON
import os          # 标准库：读环境变量

import httpx       # 第三方库：发 HTTP 请求（比 requests 多了异步支持）
from dotenv import load_dotenv   # 第三方库：把 .env 文件读进环境变量

# 读取同目录下的 .env（不会覆盖已存在的真实环境变量）
load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

# 先自检一下：环境变量没读到就别往下走了，报错信息要看得懂
if not API_KEY or not BASE_URL or not MODEL:
    raise SystemExit("❌ 没读到环境变量。检查：① 文件是不是叫 .env ② 是不是和本文件同目录 ③ 键名有没有拼错")

# URL = 接口地址 + 具体路径。OpenAI 兼容协议里，聊天接口的路径固定是 /chat/completions
url = f"{BASE_URL}/chat/completions"


# ---------- TODO 1：补全请求头 headers ----------
# 需要两个键（键名必须一模一样，大小写敏感）：
#   "Authorization": "Bearer " + API_KEY      ← 注意 Bearer 后面有一个空格！
#   "Content-Type" : "application/json"       ← 告诉服务器"我发的是 JSON"
# 写法就是普通的 dict，和你第1阶段学的字典一模一样。
headers = {
    # 你来补
}


# ---------- TODO 2：补全请求体 payload ----------
# 这是一个 dict，至少要有三个键：
#   "model"      : 用哪个模型，直接填变量 MODEL
#   "messages"   : 消息列表 list，每条消息是 {"role": ..., "content": ...}
#                  这里先只放一条，role 填 "user"，content 写一句你想问的话
#   "temperature": 先填 0（我们昨天刚学的零温度）
payload = {
    # 你来补
}


# ---------- 下面这段不用改：发请求 + 打印原始响应 ----------
# httpx.post 的 json= 参数会自动做两件事：把 dict 转成 JSON 字符串、设置 Content-Type
resp = httpx.post(url, headers=headers, json=payload, timeout=60)

print("HTTP 状态码:", resp.status_code)

if resp.status_code != 200:
    # 出错时把服务器返回的原始内容打出来，方便你看出是哪一步错了
    print("❌ 请求失败，服务器原话是：")
    print(resp.text)
    raise SystemExit(1)

data = resp.json()

print("\n===== 原始响应 JSON（格式化后）=====")
# ensure_ascii=False 让中文正常显示；indent=2 做缩进美化
print(json.dumps(data, ensure_ascii=False, indent=2))

print("\n===== 只取正文 =====")
print(data["choices"][0]["message"]["content"])

print("\n===== 这次用了多少 token =====")
print(data["usage"])

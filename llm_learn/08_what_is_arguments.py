"""把 arguments 逐层拆开看清楚 —— 全程不需要网络"""
import json

bar = "=" * 66

print(bar)
print("① 先看一个最朴素的例子：一段 JSON 文本，在 Python 里就是【字符串】")
print(bar)
inner = '{"location": "杭州"}'
print("   inner        =", inner)
print("   repr(inner)  =", repr(inner))
print("   类型         =", type(inner).__name__)
print("   ⚠️ 它看起来像 JSON，但 Python 说它是 str")

print()
print(bar)
print("② 把它塞进【另一个 JSON】里（模拟 API 响应）—— 反斜杠出现了")
print(bar)
# json.dumps：把 Python 对象转换成 JSON 格式的字符串；这里把字典序列化为外层 JSON。
outer = json.dumps({"function": {"name": "get_weather", "arguments": inner}},
                   ensure_ascii=False)
print("  ", outer)
print("   ↑ 那些反斜杠，是【外层 JSON 在给内层的引号做转义】")
print("     因为外层要用引号包住内容，内容里的引号就必须转义")

print()
print(bar)
print("③ 但 resp.json() 解析外层时，反斜杠【消失了】")
print(bar)
parsed = json.loads(outer)
val = parsed["function"]["arguments"]
print("   parsed['function']['arguments']")
# repr() 返回适合调试查看的字符串表示，会把字符串中的引号、反斜杠等显示出来。
print("   repr =", repr(val))
print("   类型 =", type(val).__name__)
print("   ↑ 反斜杠只是【传输时的转义记号】，不属于字符串本身")

print()
print(bar)
print("④ 最后一步：json.loads —— 字符串终于变成 dict")
print(bar)
args = json.loads(val)
print("   args =", args)
print("   类型 =", type(args).__name__)
print("   ✅ 这才是可以直接用的参数字典")

print()
print(bar)
print("⑤ 全流程的类型变化")
print(bar)
print("   模型写出的字        str    '{\"location\": \"杭州\"}'")
print("        ↓ API 把它包进外层 JSON（所以要转义）")
print("   网络上的原始文本    str    \"arguments\":\"{\\\"location\\\"...}\"")
print("        ↓ httpx 的 resp.json()  ← 只拆了【外面那一层】")
print("   Python 里的值       str    '{\"location\": \"杭州\"}'   ← ⚠️ 还是 str！")
print("        ↓ 你自己写的 json.loads()")
print("   真正能用的参数      dict   {'location': '杭州'}          ← ✅")
print()
print("   ⭐ 关键：resp.json() 只拆外面那层。里面这层，得你自己拆。")

print()
print(bar)
print("⑥ 反例：忘了 json.loads，直接当 dict 用会怎样")
print(bar)
try:
    val["location"]
except TypeError as e:
    print("   val['location']  →", type(e).__name__, ":", e)
    print("   ⚠️ str 只能用【整数】下标，所以它在找第 'location' 个字符")

print()
print(bar)
print("⑦ 真实数据（我们实验里 DeepSeek 返回的）")
print(bar)
real = '{"location": "杭州"}'
print("   arguments 的实际内容 =", real)
print("   len() =", len(real), "（是【字符数】，不是参数个数）")
print("   前 3 个字符 =", repr(real[:3]))

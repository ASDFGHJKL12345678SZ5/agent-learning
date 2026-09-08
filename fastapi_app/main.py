"""我的第一个 FastAPI 应用 —— Day6 作业。

运行方式（在 fastapi_app 目录下）：
    uvicorn main:app --reload
然后浏览器打开 http://127.0.0.1:8000
"""
from fastapi import FastAPI
from pydantic import BaseModel

# 创建一个 FastAPI 实例，app 是我们的应用对象
app = FastAPI(title="我的第一个 FastAPI")


# ---- GET /hello ----
# @app.get 是 FastAPI 的"路由装饰器"：告诉 FastAPI，
# 当有人用 GET 方式访问 /hello 时，就调用下面的 hello 函数。
@app.get("/hello")
def hello():
    # 返回一个 Python 字典，FastAPI 会自动把它变成 JSON 响应
    return {"message": "你好，世界！Hello World!"}


# ---- POST /echo ----
# 先定义一个"请求体"的模型。Pydantic 会帮我们校验：
# 请求里必须带一个 text 字段，类型是 str。
class EchoRequest(BaseModel):
    text: str


# @app.post 表示：用 POST 方式访问 /echo。
# 参数 echo_data: EchoRequest 表示 FastAPI 从请求体里取出数据，
# 并按 EchoRequest 的规则解析、校验后交给我们。
@app.post("/echo")
def echo(echo_data: EchoRequest):
    return {
        "你发来的原话": echo_data.text,
        "我回你的原话": echo_data.text,
        "长度": len(echo_data.text),
    }

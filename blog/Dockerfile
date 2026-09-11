# ① 基础镜像：官方 Python 3.12 精简版
FROM python:3.12-slim

# ② 容器内工作目录
WORKDIR /app

# ③ 先复制依赖清单并安装（利用层缓存：改代码不会重装依赖）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ④ 复制其余代码
COPY . .

# ⑤ 声明容器监听 8000 端口
EXPOSE 8000

# ⑥ 容器启动命令：监听 0.0.0.0 才能被容器外访问
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

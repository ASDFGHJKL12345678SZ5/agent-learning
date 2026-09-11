"""博客 API：POST /articles、GET /articles、GET /articles/{id}"""
import time
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from database import Base, SessionLocal, engine


def wait_for_db(retries: int = 30, delay: int = 2) -> None:
    """等待数据库就绪。

    MySQL 容器启动比 app 慢，必须重试等待，否则 app 会因连不上而崩溃。
    """
    for i in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"数据库已就绪（第 {i} 次尝试）")
            return
        except Exception:
            print(f"数据库未就绪，{delay} 秒后重试 ({i}/{retries})...")
            time.sleep(delay)
    raise RuntimeError("等待数据库超时，未能连接")


# 先等数据库就绪，再建表（表已存在则跳过）
wait_for_db()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blog API")


# ---------- Pydantic 模型：定义"请求体"和"响应体"长啥样 ----------
class ArticleCreate(BaseModel):
    """创建文章时，请求体必须带 title 和 content。"""
    title: str
    content: str


class ArticleOut(BaseModel):
    """返回给客户端的文章结构。"""
    id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True      # 允许直接把 ORM 对象转成这个模型


# ---------- 依赖：给每个请求提供一个数据库会话，用完自动关闭 ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- 接口 1：创建文章 ----------
@app.post("/articles", response_model=ArticleOut, status_code=201)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    obj = models.Article(title=article.title, content=article.content)
    db.add(obj)          # 加入待提交
    db.commit()          # 提交，写入数据库
    db.refresh(obj)      # 刷新，拿到数据库生成的 id / created_at
    return obj


# ---------- 接口 2：文章列表 ----------
@app.get("/articles", response_model=list[ArticleOut])
def list_articles(db: Session = Depends(get_db)):
    # 按 id 倒序，最新的文章排前面
    return db.query(models.Article).order_by(models.Article.id.desc()).all()


# ---------- 接口 3：单篇文章 ----------
@app.get("/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Article).filter(models.Article.id == article_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return obj

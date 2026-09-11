"""ORM 模型：用 Python 类描述数据库表。

Article 类  ->  articles 表
类的属性    ->  表的列
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class Article(Base):
    __tablename__ = "articles"          # 表名

    id = Column(Integer, primary_key=True, index=True)   # 主键，自增，加索引
    title = Column(String(200), nullable=False)          # 标题，不能为空
    content = Column(Text, nullable=False)               # 正文，长文本
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间，自动填

"""数据库连接：创建 engine（引擎）和 SessionLocal（会话工厂）。"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 数据库地址从环境变量读；没有就用本地 SQLite（方便本地开发/验证）。
# Docker Compose 里会通过 environment 传成 mysql+pymysql://...
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")

# SQLite 在多线程下需要这个参数；MySQL 不需要。
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# engine：负责和数据库通信的"引擎"
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# SessionLocal：每次调用它得到一个"数据库会话"，用来增删查改
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base：所有 ORM 模型的基类（模型继承它，才能被映射成表）
Base = declarative_base()

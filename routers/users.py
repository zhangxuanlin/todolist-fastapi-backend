from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import APIRouter, Query, Request


# 1. 拼装连接字符串 (格式: mysql+驱动://用户名:密码@地址:端口/数据库)
DATABASE_URL = "mysql+pymysql://root:Dgq%23!2024@114.55.251.224:12315/xl"

# 2. 创建引擎（如果是云数据库，建议加上 pool_recycle=3600 和 pool_pre_ping=True 防止断连）
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_recycle=3600, pool_pre_ping=True)

# 3. 创建会话工厂和基类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. 定义数据表模型（Object-Relational Mapping）
class User(Base):
    __tablename__ = "users" # 映射到 MySQL 的表名
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)
    status = Column(Integer, default=1)

# 5. 执行增删改查业务
db = SessionLocal()
try:
    # 💡 增 (Insert)
    new_user = User(username="xjj", password="111111", status=1)
    db.add(new_user)
    db.commit() # 提交
    db.refresh(new_user) # 刷新拿到自增 ID
    print(f"新用户插入成功，ID为: {new_user.id}")
    
    # 💡 查 (Select)
    user = db.query(User).filter(User.username == "Portal_Gun_Guy").first()
    print(f"查询到的用户状态: {user.status}")
    
except Exception as e:
    db.rollback()
    raise e
finally:
    db.close() # 必须关闭会话
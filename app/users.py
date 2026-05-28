from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from fastapi import APIRouter, Query, Body, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
import os
import uuid

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "app" / "uploads"

# 角色字典
ROLE_OPTIONS = {
    "admin": "管理员",
    "user": "普通用户",
}

import os
from dotenv import load_dotenv

load_dotenv()

# 角色字典
ROLE_OPTIONS = {
    "admin": "管理员",
    "user": "普通用户",
}

# 从环境变量读取数据库配置
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 2. 创建引擎（如果是云数据库，建议加上 pool_recycle=3600 和 pool_pre_ping=True 防止断连）
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_recycle=3600, pool_pre_ping=True)

# 3. 创建会话工厂和基类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. 定义数据表模型（Object-Relational Mapping）
class User(Base):
    __tablename__ = "users" # 映射到 MySQL 的表名
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    avatar = Column(String(250))
    username = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)
    role = Column(String(20), default="user")  # admin=管理员, user=普通用户
    status = Column(Integer, default=1)
    nickname = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# 依赖函数：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 文件上传配置
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_avatar(file: UploadFile) -> str:
    """保存上传的头像文件，返回文件路径"""
    if not file:
        return None
    
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    return filename

@router.get("/api/users/list", tags=["Users"], summary="获取用户列表")
async def read_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str | None = Query(None, description="用户名筛选"),
    password: str | None = Query(None, description="密码筛选"),
    role: str | None = Query(None, description="角色筛选 (admin/user)"),
    status: int | None = Query(None, description="状态筛选"),
    nickname: str | None = Query(None, description="昵称筛选"),
    created_at: datetime | None = Query(None, description="创建时间筛选"),
    updated_at: datetime | None = Query(None, description="更新时间筛选"),
    db: Session = Depends(get_db),
):
    
    # 构建查询
    query = db.query(User)
    
    # 根据参数动态添加筛选条件
    if username:
        query = query.filter(User.username.like(f"%{username}%"))
    if password:
        query = query.filter(User.password == password)
    if status is not None:
        query = query.filter(User.status == status)
    if role:
        query = query.filter(User.role == role)
    if nickname:
        query = query.filter(User.nickname.like(f"%{nickname}%"))
    if created_at:
        query = query.filter(User.created_at == created_at)
    if updated_at:
        query = query.filter(User.updated_at == updated_at)
    
    # 获取总数
    total = query.count()
    
    # 分页
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 转换为字典列表
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "avatar": user.avatar,
            "username": user.username,
            "password": user.password,
            "role": user.role,
            "role_name": ROLE_OPTIONS.get(user.role, "未知"),
            "status": user.status,
            "nickname": user.nickname,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None,
            "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
        })
    
    return {
        "code": 200,
        "message": "success",
        "data": user_list,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
        
@router.post("/api/users/add", tags=["Users"], summary="用户注册")
async def register_user(
    username: str = Form(..., description="用户名"),
    password: str = Form(..., description="密码"),
    nickname: str = Form(None, description="昵称"),
    avatar: UploadFile = File(None, description="头像文件"),
    role: str = Form("user", description="角色 (admin/user)"),
    status: int = Form(1, description="状态"),
    db: Session = Depends(get_db),
):
    if not username or not password:
        return {"code": 400, "message": "用户名和密码不能为空", "data": None}
    
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return {"code": 400, "message": "用户名已存在", "data": None}
        
        # 处理头像上传
        avatar_filename = await save_avatar(avatar) if avatar else None
        
        new_user = User(
            avatar=avatar_filename,
            username=username,
            password=password,
            role=role,
            status=status,
            nickname=nickname,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role,
                "role_name": ROLE_OPTIONS.get(new_user.role, "未知"),
                "avatar": new_user.avatar,
                "created_at": new_user.created_at.strftime("%Y-%m-%d %H:%M:%S") if new_user.created_at else None,
            },
        }

    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"注册失败: {str(e)}", "data": None}


@router.post("/api/users/edit", tags=["Users"], summary="编辑用户")
async def edit_user(
    id: int = Form(..., description="用户ID"),
    username: str = Form(None, description="用户名"),
    password: str = Form(None, description="密码"),
    nickname: str = Form(None, description="昵称"),
    avatar: UploadFile = File(None, description="头像文件"),
    role: str = Form(None, description="角色 (admin/user)"),
    status: str = Form(None, description="状态"),
    db: Session = Depends(get_db),
):
    if not id:
        return {"code": 400, "message": "缺少用户ID", "data": None}
    
    try:
        user = db.query(User).filter(User.id == id).first()
        if not user:
            return {"code": 404, "message": "用户不存在", "data": None}
        
        if username and username != user.username:
            existing = db.query(User).filter(
                User.username == username,
                User.id != id
            ).first()
            if existing:
                return {"code": 400, "message": "用户名已存在", "data": None}
            user.username = username
        
        if password:
            user.password = password
        if nickname is not None:
            user.nickname = nickname
        if avatar:
            user.avatar = await save_avatar(avatar)
        if role:
            user.role = role
        if status is not None:
            user.status = int(status)
        
        user.updated_at = datetime.now()
        
        db.commit()
        db.refresh(user)

        return {
            "code": 200,
            "message": "更新成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "role_name": ROLE_OPTIONS.get(user.role, "未知"),
                "avatar": user.avatar,
                "status": user.status,
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
            },
        }

    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"更新失败: {str(e)}", "data": None}


@router.post("/api/users/delete", tags=["Users"], summary="删除用户")
async def delete_user(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """删除单个用户"""
    user_id = body.get("id")
    
    if not user_id:
        return {"code": 400, "message": "缺少用户ID", "data": None}
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"code": 404, "message": "用户不存在", "data": None}
        
        db.delete(user)
        db.commit()
        
        return {"code": 200, "message": "删除成功", "data": {"id": user_id}}

    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"删除失败: {str(e)}", "data": None}


@router.post("/api/users/batch-delete", tags=["Users"], summary="批量删除用户")
async def batch_delete_user(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """批量删除用户"""
    ids = body.get("ids", [])
    
    if not ids:
        return {"code": 400, "message": "缺少用户ID列表", "data": None}
    
    if not isinstance(ids, list):
        return {"code": 400, "message": "ids必须是数组格式", "data": None}
    
    try:
        # 查找要删除的用户
        users = db.query(User).filter(User.id.in_(ids)).all()
        
        if not users:
            return {"code": 404, "message": "没有找到要删除的用户", "data": None}
        
        deleted_count = len(users)
        deleted_ids = [user.id for user in users]
        
        # 批量删除
        for user in users:
            db.delete(user)
        
        db.commit()
        
        return {
            "code": 200,
            "message": f"成功删除 {deleted_count} 个用户",
            "data": {"deleted_count": deleted_count, "deleted_ids": deleted_ids},
        }

    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"批量删除失败: {str(e)}", "data": None}


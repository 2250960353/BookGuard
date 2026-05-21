from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User, UserRole
from app.auth import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    real_name: str = ""
    role: str = "operator"


@router.post("/login", summary="用户登录")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    user.last_login = __import__("datetime").datetime.utcnow()
    await db.commit()
    token = create_access_token({"sub": user.username, "role": user.role, "uid": user.id})
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "role": user.role,
        },
    }


@router.post("/register", summary="注册用户（仅管理员）")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if req.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail="无效的角色")
    user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        real_name=req.real_name,
        role=req.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.get("/me", summary="获取当前用户信息")
async def get_me(token: str = None, db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="未提供令牌")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    result = await db.execute(select(User).where(User.username == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "role": user.role,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.get("/users", summary="获取用户列表")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [{"id": u.id, "username": u.username, "real_name": u.real_name, "role": u.role, "is_active": u.is_active, "last_login": u.last_login.isoformat() if u.last_login else None} for u in users]


@router.put("/users/{user_id}/toggle", summary="启用/禁用用户")
async def toggle_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = not user.is_active
    await db.commit()
    return {"is_active": user.is_active}

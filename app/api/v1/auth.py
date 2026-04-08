from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_token_from_header
from app.api.middleware import AUTH_RATE_LIMIT, limiter
from app.config import settings
from app.core.database import get_db
from app.core.exceptions import ConflictException, UnauthorizedException
from app.schemas.response import ResponseBuilder
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.security import TokenBlacklist, create_access_token
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    db_user = await user_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise ConflictException(
            message="用户名已被注册",
            details={"field": "username"}
        )

    if user.email:
        db_user = await user_service.get_user_by_email(db, email=user.email)
        if db_user:
            raise ConflictException(
                message="邮箱已被注册",
                details={"field": "email"}
            )

    new_user = await user_service.create_user(db=db, user=user)
    return ResponseBuilder.success(
        data=UserResponse.model_validate(new_user).model_dump(),
        message="注册成功"
    )


@router.post("/login")
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.authenticate_user(db, username=user_login.username, password=user_login.password)
    if not user:
        raise UnauthorizedException(message="用户名或密码错误")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return ResponseBuilder.success(
        data={"access_token": access_token, "token_type": "bearer"},
        message="登录成功"
    )


@router.get("/me")
async def read_users_me(current_user = Depends(get_current_active_user)):
    # current_user 是 SQLAlchemy User 模型，需要转换为 Pydantic
    from app.schemas.user import UserResponse
    user_data = UserResponse.model_validate(current_user)
    return ResponseBuilder.success(data=user_data.model_dump())


@router.post("/logout")
async def logout(
    token: str = Depends(get_token_from_header),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """用户登出

    将当前 Token 加入黑名单，使其立即失效。
    """
    await TokenBlacklist.add(token)
    return ResponseBuilder.success(message="已成功登出")

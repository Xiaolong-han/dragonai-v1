from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse as FastAPIFileResponse
from pydantic import BaseModel

from app.api.dependencies import get_current_active_user
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.models.user import User
from app.schemas.response import ResponseBuilder
from app.security import verify_file_signature
from app.storage import file_storage

router = APIRouter(prefix="/files", tags=["文件"])


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    filename: str
    original_filename: str | None
    content_type: str
    relative_path: str
    virtual_path: str
    file_size: int
    upload_time: str


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(..., description="要上传的文件列表"),
    current_user: User = Depends(get_current_active_user),
):
    """上传文件到本地文件系统"""
    results = []
    for file in files:
        file_info = await file_storage.save_file(file)
        results.append(FileUploadResponse(**file_info).model_dump())
    return ResponseBuilder.success(data=results, message="文件上传成功")


@router.get("/serve/{relative_path:path}")
async def download_file(
    relative_path: str,
    expires: int | None = Query(None, description="过期时间戳"),
    signature: str | None = Query(None, description="访问签名"),
):
    """提供文件访问服务（需要签名验证）"""
    if not relative_path.startswith(('images/', 'uploads/')):
        raise ForbiddenException(message="无权访问此路径")

    if expires is None or signature is None:
        raise UnauthorizedException(message="缺少签名或过期时间参数")

    if not verify_file_signature(relative_path, expires, signature):
        raise ForbiddenException(message="签名无效或已过期")

    file_path = file_storage.get_file_path(relative_path)
    if not file_path:
        raise NotFoundException(
            message="文件不存在",
            resource_type="file",
            resource_id=relative_path
        )
    return FastAPIFileResponse(
        path=file_path,
        filename=file_path.name
    )

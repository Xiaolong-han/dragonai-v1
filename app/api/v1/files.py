
from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Query,
)
from fastapi.responses import FileResponse as FastAPIFileResponse
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.storage import file_storage
from app.security import verify_file_signature


router = APIRouter(prefix="/files", tags=["文件"])


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    filename: str
    original_filename: Optional[str]
    content_type: str
    relative_path: str
    virtual_path: str
    file_size: int
    upload_time: str


@router.post("/upload", response_model=List[FileUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    current_user: User = Depends(get_current_active_user),
):
    """上传文件到本地文件系统"""
    results = []
    for file in files:
        file_info = await file_storage.save_file(file)
        results.append(FileUploadResponse(**file_info))
    return results


@router.get("/serve/{relative_path:path}")
async def download_file(
    relative_path: str,
    expires: Optional[int] = Query(None, description="过期时间戳"),
    signature: Optional[str] = Query(None, description="访问签名"),
):
    """提供文件访问服务（需要签名验证）"""
    if not relative_path.startswith(('images/', 'uploads/')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if expires is None or signature is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature or expires parameter"
        )
    
    if not verify_file_signature(relative_path, expires, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired signature"
        )
    
    file_path = file_storage.get_file_path(relative_path)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return FastAPIFileResponse(
        path=file_path,
        filename=file_path.name
    )


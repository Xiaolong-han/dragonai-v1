from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from app.core.exceptions import ExternalServiceException
from app.schemas.response import ResponseBuilder
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

router = APIRouter(prefix="/knowledge", tags=["知识库"])


class SearchRequest(BaseModel):
    query: str
    k: int = 4


class DocumentResponse(BaseModel):
    content: str
    metadata: dict


class SearchResult(BaseModel):
    results: list[DocumentResponse]


class UploadResponse(BaseModel):
    success: bool
    message: str
    chunks: int
    added: int
    updated: int


class DeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_count: int


class StatsResponse(BaseModel):
    collection_name: str
    document_count: int


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        physical_path = await service.save_uploaded_file(file, file.filename)
        result = await service.upload_document(
            physical_path,
            metadata={"source": file.filename}
        )

        return ResponseBuilder.success(
            data=UploadResponse(
                success=True,
                message="文档上传成功",
                chunks=result["chunks"],
                added=result["added"],
                updated=result["updated"],
            ).model_dump()
        )
    except Exception as e:
        raise ExternalServiceException(
            message=f"文档上传失败: {e!s}",
            service_name="knowledge"
        ) from e


@router.post("/search")
async def search_knowledge(
    request: SearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        documents = await service.asearch(
            query=request.query,
            k=request.k,
        )
        results = [
            DocumentResponse(content=doc.page_content, metadata=doc.metadata).model_dump()
            for doc in documents
        ]
        return ResponseBuilder.success(data={"results": results})
    except Exception as e:
        raise ExternalServiceException(
            message=f"知识检索失败: {e!s}",
            service_name="knowledge"
        ) from e


@router.get("/stats")
async def get_stats(
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        stats = await service.get_collection_stats()
        return ResponseBuilder.success(data=StatsResponse(**stats).model_dump())
    except Exception as e:
        raise ExternalServiceException(
            message=f"获取统计信息失败: {e!s}",
            service_name="knowledge"
        ) from e


@router.delete("/{filename:path}")
async def delete_document(
    filename: str,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        deleted_count = await service.delete_document(filename)
        return ResponseBuilder.success(
            data=DeleteResponse(
                success=True,
                message=f"已删除 {deleted_count} 个文档片段",
                deleted_count=deleted_count,
            ).model_dump()
        )
    except Exception as e:
        raise ExternalServiceException(
            message=f"删除文档失败: {e!s}",
            service_name="knowledge"
        ) from e


@router.delete("/collection")
async def delete_collection(
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        await service.delete_collection()
        return ResponseBuilder.success(message="知识库已删除")
    except Exception as e:
        raise ExternalServiceException(
            message=f"删除知识库失败: {e!s}",
            service_name="knowledge"
        ) from e

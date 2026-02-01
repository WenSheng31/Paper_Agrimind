import math
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db
from ..models.knowledge import KnowledgeDocument
from ..schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeUploadResponse,
    KnowledgeGroupResponse,
)
from ..schemas.agriculture import PaginatedResponse
from ..services.knowledge import extract_text_from_pdf, process_and_store
from ..services.embedding import get_embedding
from .auth import get_current_user

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/", response_model=PaginatedResponse[KnowledgeGroupResponse])
def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = (
        db.query(
            KnowledgeDocument.title,
            KnowledgeDocument.source_filename,
            func.count(KnowledgeDocument.id).label("chunk_count"),
            func.min(KnowledgeDocument.created_at).label("created_at"),
        )
        .group_by(KnowledgeDocument.title, KnowledgeDocument.source_filename)
        .order_by(func.min(KnowledgeDocument.created_at).desc())
    )

    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        KnowledgeGroupResponse(
            title=r.title,
            source_filename=r.source_filename,
            chunk_count=r.chunk_count,
            created_at=r.created_at,
        )
        for r in results
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/upload/text", response_model=KnowledgeUploadResponse)
def upload_text(
    data: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if not data.title.strip() or not data.content.strip():
        raise HTTPException(status_code=400, detail="標題和內容不能為空")

    count = process_and_store(db, data.title.strip(), data.content.strip())
    return KnowledgeUploadResponse(
        title=data.title,
        chunk_count=count,
        message=f"已成功儲存 {count} 個文字片段",
    )


@router.post("/upload/pdf", response_model=KnowledgeUploadResponse)
def upload_pdf(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案")

    text = extract_text_from_pdf(file.file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="無法從 PDF 擷取文字內容")

    count = process_and_store(db, title.strip(), text, file.filename)
    return KnowledgeUploadResponse(
        title=title,
        filename=file.filename,
        chunk_count=count,
        message=f"已成功儲存 {count} 個文字片段",
    )


@router.delete("/{title}")
def delete_knowledge(
    title: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    count = db.query(KnowledgeDocument).filter(KnowledgeDocument.title == title).delete()
    db.commit()
    if count == 0:
        raise HTTPException(status_code=404, detail="找不到該知識文件")
    return {"message": f"已刪除「{title}」共 {count} 個片段"}


@router.get("/search")
def search_knowledge(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query_embedding = get_embedding(q)
    results = (
        db.query(KnowledgeDocument)
        .order_by(KnowledgeDocument.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
    return [
        {
            "title": r.title,
            "content": r.content,
            "source_filename": r.source_filename,
            "chunk_index": r.chunk_index,
            "score": None,
        }
        for r in results
    ]

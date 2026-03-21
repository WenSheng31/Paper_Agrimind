from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.config import settings
from ..schemas.agriculture import (
    ImageRecordResponse,
    ImageRecordUpdate,
    PaginatedResponse,
)
from ..services.image_record import ImageRecordService
from .auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/image-records", tags=["image-records"])

service = ImageRecordService


@router.post("", response_model=ImageRecordResponse)
async def create_image_record(
    farm_id: int = Form(...),
    description: str = Form(None),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user),
):
    files_data = []
    for f in files:
        content = await f.read()
        files_data.append({"filename": f.filename, "content": content})

    try:
        record = service.create_record(
            db, farm_id, user.id, description, files_data, settings.UPLOAD_DIR
        )
    except ValueError as e:
        status = 404 if "不存在" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))
    return service.record_to_response(record)


@router.get("", response_model=PaginatedResponse[ImageRecordResponse])
def list_image_records(
    farm_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return service.list_records(db, farm_id, page, page_size)


@router.get("/{record_id}", response_model=ImageRecordResponse)
def get_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    try:
        record = service.get_record(db, record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return service.record_to_response(record)


@router.put("/{record_id}", response_model=ImageRecordResponse)
def update_image_record(
    record_id: int,
    data: ImageRecordUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    try:
        record = service.update_record(db, record_id, data.description)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return service.record_to_response(record)


@router.post("/{record_id}/images", response_model=ImageRecordResponse)
async def add_images(
    record_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    """追加圖片到現有紀錄"""
    files_data = []
    for f in files:
        content = await f.read()
        files_data.append({"filename": f.filename, "content": content})

    try:
        record = service.add_images(db, record_id, files_data, settings.UPLOAD_DIR)
    except ValueError as e:
        status = 404 if "不存在" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))
    return service.record_to_response(record)


@router.delete("/{record_id}/images/{image_id}", response_model=ImageRecordResponse)
def delete_image(
    record_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    """刪除單張圖片"""
    try:
        record = service.delete_image(db, record_id, image_id, settings.UPLOAD_DIR)
    except ValueError as e:
        status = 404 if "不存在" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))
    return service.record_to_response(record)


@router.get("/{record_id}/analysis")
def analyze_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """AI 分析影像紀錄的圖片"""
    try:
        analysis = service.analyze_images(
            db, record_id, settings.UPLOAD_DIR, settings.ANTHROPIC_API_KEY
        )
        return {"analysis": analysis}
    except ValueError as e:
        status = 404 if "不存在" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析失敗: {str(e)}")


@router.delete("/{record_id}")
def delete_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    try:
        service.delete_record(db, record_id, settings.UPLOAD_DIR)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "影像紀錄已刪除"}

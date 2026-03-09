import base64
import math
import mimetypes
import os
import uuid
import shutil

import anthropic
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload

from ..core.database import get_db
from ..core.config import settings
from ..models.agriculture import ImageRecord, ImageRecordFile, Farm
from ..schemas.agriculture import (
    ImageRecordResponse,
    ImageRecordUpdate,
    PaginatedResponse,
)
from .auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/image-records", tags=["image-records"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES = 5


def _record_to_response(record: ImageRecord) -> ImageRecordResponse:
    return ImageRecordResponse(
        id=record.id,
        farm_id=record.farm_id,
        user_id=record.user_id,
        description=record.description,
        created_at=record.created_at,
        images=record.images,
        farm_name=record.farm.name if record.farm else None,
    )


@router.post("", response_model=ImageRecordResponse)
async def create_image_record(
    farm_id: int = Form(...),
    description: str = Form(None),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user),
):
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"最多上傳 {MAX_FILES} 張圖片")
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="請至少上傳一張圖片")

    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="農場不存在")

    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支援的檔案格式：{f.filename}")

    record = ImageRecord(farm_id=farm_id, user_id=user.id, description=description)
    db.add(record)
    db.flush()

    record_dir = os.path.join(settings.UPLOAD_DIR, "image-records", str(record.id))
    os.makedirs(record_dir, exist_ok=True)

    for f in files:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            shutil.rmtree(record_dir, ignore_errors=True)
            db.rollback()
            raise HTTPException(status_code=400, detail=f"檔案 {f.filename} 超過 5MB 限制")

        ext = os.path.splitext(f.filename or "")[1].lower()
        saved_filename = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(record_dir, saved_filename), "wb") as out:
            out.write(content)

        db.add(ImageRecordFile(
            record_id=record.id,
            filename=saved_filename,
            original_filename=f.filename or "unknown",
            file_size=len(content),
        ))

    db.commit()
    db.refresh(record)
    return _record_to_response(record)


@router.get("", response_model=PaginatedResponse[ImageRecordResponse])
def list_image_records(
    farm_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(ImageRecord).options(
        joinedload(ImageRecord.images),
        joinedload(ImageRecord.farm),
    )
    if farm_id:
        query = query.filter(ImageRecord.farm_id == farm_id)

    # count without joins
    count_query = db.query(ImageRecord)
    if farm_id:
        count_query = count_query.filter(ImageRecord.farm_id == farm_id)
    total = count_query.count()

    records = (
        query.order_by(ImageRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # deduplicate from joinedload
    seen = set()
    unique = []
    for r in records:
        if r.id not in seen:
            seen.add(r.id)
            unique.append(r)

    return PaginatedResponse(
        items=[_record_to_response(r) for r in unique],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{record_id}", response_model=ImageRecordResponse)
def get_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    record = (
        db.query(ImageRecord)
        .options(joinedload(ImageRecord.images), joinedload(ImageRecord.farm))
        .filter(ImageRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="影像紀錄不存在")
    return _record_to_response(record)


@router.put("/{record_id}", response_model=ImageRecordResponse)
def update_image_record(
    record_id: int,
    data: ImageRecordUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    record = (
        db.query(ImageRecord)
        .options(joinedload(ImageRecord.images), joinedload(ImageRecord.farm))
        .filter(ImageRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="影像紀錄不存在")

    if data.description is not None:
        record.description = data.description
    db.commit()
    db.refresh(record)
    return _record_to_response(record)


@router.post("/{record_id}/images", response_model=ImageRecordResponse)
async def add_images(
    record_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    """追加圖片到現有紀錄"""
    record = (
        db.query(ImageRecord)
        .options(joinedload(ImageRecord.images), joinedload(ImageRecord.farm))
        .filter(ImageRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="影像紀錄不存在")

    current_count = len(record.images)
    if current_count + len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"最多 {MAX_FILES} 張，目前已有 {current_count} 張")

    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支援的檔案格式：{f.filename}")

    record_dir = os.path.join(settings.UPLOAD_DIR, "image-records", str(record.id))
    os.makedirs(record_dir, exist_ok=True)

    for f in files:
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"檔案 {f.filename} 超過 5MB 限制")

        ext = os.path.splitext(f.filename or "")[1].lower()
        saved_filename = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(record_dir, saved_filename), "wb") as out:
            out.write(content)

        db.add(ImageRecordFile(
            record_id=record.id,
            filename=saved_filename,
            original_filename=f.filename or "unknown",
            file_size=len(content),
        ))

    db.commit()
    db.refresh(record)
    return _record_to_response(record)


@router.delete("/{record_id}/images/{image_id}", response_model=ImageRecordResponse)
def delete_image(
    record_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    """刪除單張圖片"""
    record = (
        db.query(ImageRecord)
        .options(joinedload(ImageRecord.images), joinedload(ImageRecord.farm))
        .filter(ImageRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="影像紀錄不存在")

    img_file = db.query(ImageRecordFile).filter(
        ImageRecordFile.id == image_id,
        ImageRecordFile.record_id == record_id,
    ).first()
    if not img_file:
        raise HTTPException(status_code=404, detail="圖片不存在")

    if len(record.images) <= 1:
        raise HTTPException(status_code=400, detail="至少需保留一張圖片")

    # 刪除磁碟檔案
    file_path = os.path.join(settings.UPLOAD_DIR, "image-records", str(record_id), img_file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(img_file)
    db.commit()
    db.refresh(record)
    return _record_to_response(record)


@router.get("/{record_id}/analysis")
def analyze_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """AI 分析影像紀錄的圖片"""
    record = (
        db.query(ImageRecord)
        .options(joinedload(ImageRecord.images), joinedload(ImageRecord.farm))
        .filter(ImageRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="影像紀錄不存在")
    if not record.images:
        raise HTTPException(status_code=400, detail="該紀錄沒有圖片")

    # 讀取圖片轉 base64
    record_dir = os.path.join(settings.UPLOAD_DIR, "image-records", str(record_id))
    image_contents = []
    for img in record.images:
        file_path = os.path.join(record_dir, img.filename)
        if not os.path.isfile(file_path):
            continue
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(img.filename)[1].lower()
        media_type = mimetypes.types_map.get(ext, "image/jpeg")
        image_contents.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data},
        })

    if not image_contents:
        raise HTTPException(status_code=400, detail="圖片檔案不存在")

    farm_name = record.farm.name if record.farm else "未知農場"
    prompt = f"農場：{farm_name}\n"
    if record.description:
        prompt += f"描述：{record.description}\n"
    prompt += "用純文字回覆，不要使用任何 markdown 格式（不要用 #、*、- 等符號）。用 2-3 句話簡短描述照片中的作物狀況與建議。繁體中文。"

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        content = image_contents + [{"type": "text", "text": prompt}]
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": content}],
        )
        analysis = response.content[0].text if response.content else "分析失敗"
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 分析失敗: {str(e)}")


@router.delete("/{record_id}")
def delete_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_admin_user),
):
    record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="影像紀錄不存在")

    record_dir = os.path.join(settings.UPLOAD_DIR, "image-records", str(record.id))
    shutil.rmtree(record_dir, ignore_errors=True)

    db.delete(record)
    db.commit()
    return {"message": "影像紀錄已刪除"}

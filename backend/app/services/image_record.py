import base64
import math
import mimetypes
import os
import uuid
import shutil

import anthropic
from sqlalchemy.orm import Session, joinedload

from ..models.agriculture import ImageRecord, ImageRecordFile, Farm
from ..schemas.agriculture import ImageRecordResponse, PaginatedResponse

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES = 5


class ImageRecordService:
    @staticmethod
    def record_to_response(record: ImageRecord) -> ImageRecordResponse:
        return ImageRecordResponse(
            id=record.id,
            farm_id=record.farm_id,
            user_id=record.user_id,
            description=record.description,
            created_at=record.created_at,
            images=record.images,
            farm_name=record.farm.name if record.farm else None,
        )

    @staticmethod
    def validate_files(files_info: list[dict], current_count: int = 0):
        """驗證檔案數量、副檔名與大小。
        files_info: list of {"filename": str, "size": int}
        Raises ValueError on validation failure.
        """
        total = current_count + len(files_info)
        if len(files_info) == 0:
            raise ValueError("請至少上傳一張圖片")
        if total > MAX_FILES:
            if current_count > 0:
                raise ValueError(f"最多 {MAX_FILES} 張，目前已有 {current_count} 張")
            else:
                raise ValueError(f"最多上傳 {MAX_FILES} 張圖片")

        for info in files_info:
            ext = os.path.splitext(info["filename"] or "")[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(f"不支援的檔案格式：{info['filename']}")
            if info["size"] > MAX_FILE_SIZE:
                raise ValueError(f"檔案 {info['filename']} 超過 5MB 限制")

    @staticmethod
    def save_files(record_id: int, files_data: list[dict], upload_dir: str) -> list[dict]:
        """儲存檔案到磁碟。
        files_data: list of {"filename": str, "content": bytes}
        Returns list of {"saved_filename": str, "original_filename": str, "file_size": int}
        """
        record_dir = os.path.join(upload_dir, "image-records", str(record_id))
        os.makedirs(record_dir, exist_ok=True)

        saved = []
        for fd in files_data:
            ext = os.path.splitext(fd["filename"] or "")[1].lower()
            saved_filename = f"{uuid.uuid4().hex}{ext}"
            with open(os.path.join(record_dir, saved_filename), "wb") as out:
                out.write(fd["content"])
            saved.append({
                "saved_filename": saved_filename,
                "original_filename": fd["filename"] or "unknown",
                "file_size": len(fd["content"]),
            })
        return saved

    @staticmethod
    def create_record(
        db: Session,
        farm_id: int,
        user_id: int,
        description: str | None,
        files_data: list[dict],
        upload_dir: str,
    ) -> ImageRecord:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            raise ValueError("農場不存在")

        files_info = [{"filename": f["filename"], "size": len(f["content"])} for f in files_data]
        ImageRecordService.validate_files(files_info)

        record = ImageRecord(farm_id=farm_id, user_id=user_id, description=description)
        db.add(record)
        db.flush()

        try:
            saved = ImageRecordService.save_files(record.id, files_data, upload_dir)
        except Exception:
            record_dir = os.path.join(upload_dir, "image-records", str(record.id))
            shutil.rmtree(record_dir, ignore_errors=True)
            db.rollback()
            raise

        for s in saved:
            db.add(ImageRecordFile(
                record_id=record.id,
                filename=s["saved_filename"],
                original_filename=s["original_filename"],
                file_size=s["file_size"],
            ))

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_record(db: Session, record_id: int) -> ImageRecord:
        record = (
            db.query(ImageRecord)
            .options(joinedload(ImageRecord.images), joinedload(ImageRecord.farm))
            .filter(ImageRecord.id == record_id)
            .first()
        )
        if not record:
            raise ValueError("影像紀錄不存在")
        return record

    @staticmethod
    def list_records(
        db: Session,
        farm_id: int | None,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[ImageRecordResponse]:
        query = db.query(ImageRecord).options(
            joinedload(ImageRecord.images),
            joinedload(ImageRecord.farm),
        )
        if farm_id:
            query = query.filter(ImageRecord.farm_id == farm_id)

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
            items=[ImageRecordService.record_to_response(r) for r in unique],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    @staticmethod
    def update_record(db: Session, record_id: int, description: str | None) -> ImageRecord:
        record = ImageRecordService.get_record(db, record_id)
        if description is not None:
            record.description = description
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_record(db: Session, record_id: int, upload_dir: str) -> None:
        record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
        if not record:
            raise ValueError("影像紀錄不存在")

        record_dir = os.path.join(upload_dir, "image-records", str(record.id))
        shutil.rmtree(record_dir, ignore_errors=True)

        db.delete(record)
        db.commit()

    @staticmethod
    def add_images(
        db: Session,
        record_id: int,
        files_data: list[dict],
        upload_dir: str,
    ) -> ImageRecord:
        record = ImageRecordService.get_record(db, record_id)

        current_count = len(record.images)
        files_info = [{"filename": f["filename"], "size": len(f["content"])} for f in files_data]
        ImageRecordService.validate_files(files_info, current_count=current_count)

        saved = ImageRecordService.save_files(record.id, files_data, upload_dir)

        for s in saved:
            db.add(ImageRecordFile(
                record_id=record.id,
                filename=s["saved_filename"],
                original_filename=s["original_filename"],
                file_size=s["file_size"],
            ))

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_image(
        db: Session,
        record_id: int,
        image_id: int,
        upload_dir: str,
    ) -> ImageRecord:
        record = ImageRecordService.get_record(db, record_id)

        img_file = db.query(ImageRecordFile).filter(
            ImageRecordFile.id == image_id,
            ImageRecordFile.record_id == record_id,
        ).first()
        if not img_file:
            raise ValueError("圖片不存在")

        if len(record.images) <= 1:
            raise ValueError("至少需保留一張圖片")

        file_path = os.path.join(upload_dir, "image-records", str(record_id), img_file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        db.delete(img_file)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def analyze_images(
        db: Session,
        record_id: int,
        upload_dir: str,
        api_key: str,
    ) -> str:
        record = ImageRecordService.get_record(db, record_id)
        if not record.images:
            raise ValueError("該紀錄沒有圖片")

        record_dir = os.path.join(upload_dir, "image-records", str(record_id))
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
            raise ValueError("圖片檔案不存在")

        farm_name = record.farm.name if record.farm else "未知農場"
        prompt = f"農場：{farm_name}\n"
        if record.description:
            prompt += f"描述：{record.description}\n"
        prompt += "用純文字回覆，不要使用任何 markdown 格式（不要用 #、*、- 等符號）。用 2-3 句話簡短描述照片中的作物狀況與建議。繁體中文。"

        client = anthropic.Anthropic(api_key=api_key)
        content = image_contents + [{"type": "text", "text": prompt}]
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": content}],
        )
        analysis = response.content[0].text if response.content else "分析失敗"
        return analysis

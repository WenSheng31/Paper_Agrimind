from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..models.task_progress import TaskProgress


class TaskProgressService:
    @staticmethod
    def get_progress(db: Session, user_id: int) -> TaskProgress | None:
        return db.query(TaskProgress).filter(TaskProgress.user_id == user_id).first()

    @staticmethod
    def update_progress(db: Session, user_id: int, current_step: int, is_completed: bool) -> TaskProgress:
        progress = db.query(TaskProgress).filter(TaskProgress.user_id == user_id).first()
        if not progress:
            progress = TaskProgress(user_id=user_id, current_step=current_step, is_completed=is_completed)
            db.add(progress)
        else:
            progress.current_step = current_step
            progress.is_completed = is_completed

        if is_completed and not progress.completed_at:
            progress.completed_at = func.now()
        elif not is_completed:
            progress.completed_at = None

        db.commit()
        db.refresh(progress)
        return progress

    @staticmethod
    def delete_progress(db: Session, user_id: int) -> None:
        db.query(TaskProgress).filter(TaskProgress.user_id == user_id).delete()
        db.commit()

    @staticmethod
    def get_all_progress(db: Session) -> list[TaskProgress]:
        return db.query(TaskProgress).all()

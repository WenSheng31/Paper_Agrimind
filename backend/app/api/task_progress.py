from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..schemas.task_progress import TaskProgressUpdate, TaskProgressResponse
from ..services.task_progress import TaskProgressService
from .auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/task-progress", tags=["task-progress"])


@router.get("/", response_model=TaskProgressResponse)
def get_my_progress(user=Depends(get_current_user), db: Session = Depends(get_db)):
    progress = TaskProgressService.get_progress(db, user.id)
    if not progress:
        raise HTTPException(status_code=404, detail="尚未開始任務")
    return progress


@router.put("/", response_model=TaskProgressResponse)
def update_my_progress(
    data: TaskProgressUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TaskProgressService.update_progress(db, user.id, data.current_step, data.is_completed)


@router.get("/all")
def get_all_progress(_admin=Depends(get_current_admin_user), db: Session = Depends(get_db)):
    items = TaskProgressService.get_all_progress(db)
    return [
        {
            "user_id": p.user_id,
            "current_step": p.current_step,
            "is_completed": p.is_completed,
            "started_at": p.started_at,
            "completed_at": p.completed_at,
        }
        for p in items
    ]


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_progress(
    user_id: int,
    _admin=Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    TaskProgressService.delete_progress(db, user_id)
    return None

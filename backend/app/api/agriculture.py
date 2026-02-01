from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math

from ..core.database import get_db
from ..schemas.agriculture import (
    FarmCreate, FarmUpdate, FarmResponse,
    SensorDataCreate, SensorDataResponse,
    OperationCreate, OperationUpdate, OperationResponse,
    PaginatedResponse, DashboardStats
)
from ..models.agriculture import Farm, SensorData, Operation
from .auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/agriculture", tags=["agriculture"])


def get_or_404(db: Session, model, obj_id: int):
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """
    獲取儀表板統計數據（後端聚合計算）
    """
    return DashboardStats(
        total_farms=db.query(Farm).count(),
        total_sensor_data=db.query(SensorData).count(),
        total_operations=db.query(Operation).count()
    )


# ===== Farm CRUD =====

@router.post("/farms", response_model=FarmResponse, status_code=201)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    db_farm = Farm(**farm.model_dump())
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.get("/farms", response_model=List[FarmResponse])
def get_farms(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Farm).all()


@router.get("/farms/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return get_or_404(db, Farm, farm_id)


@router.put("/farms/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, farm_update: FarmUpdate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    db_farm = get_or_404(db, Farm, farm_id)
    for key, value in farm_update.model_dump(exclude_unset=True).items():
        setattr(db_farm, key, value)
    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.delete("/farms/{farm_id}", status_code=204)
def delete_farm(farm_id: int, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    db_farm = get_or_404(db, Farm, farm_id)
    db.delete(db_farm)
    db.commit()


# ===== SensorData CRD (no Update) =====

@router.post("/farms/{farm_id}/sensor-data", response_model=SensorDataResponse, status_code=201)
def create_sensor_data(farm_id: int, data: SensorDataCreate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    get_or_404(db, Farm, farm_id)
    db_data = SensorData(**data.model_dump(), farm_id=farm_id)
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


@router.get("/farms/{farm_id}/sensor-data", response_model=PaginatedResponse[SensorDataResponse])
def get_sensor_data(
    farm_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user)
):
    query = db.query(SensorData).filter(SensorData.farm_id == farm_id).order_by(SensorData.timestamp.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.delete("/sensor-data/{data_id}", status_code=204)
def delete_sensor_data(data_id: int, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    db_data = get_or_404(db, SensorData, data_id)
    db.delete(db_data)
    db.commit()


# ===== Operation CRUD =====

@router.post("/farms/{farm_id}/operations", response_model=OperationResponse, status_code=201)
def create_operation(farm_id: int, op: OperationCreate, db: Session = Depends(get_db), user=Depends(get_current_admin_user)):
    get_or_404(db, Farm, farm_id)
    db_op = Operation(**op.model_dump(), farm_id=farm_id, user_id=user.id)
    db.add(db_op)
    db.commit()
    db.refresh(db_op)
    return db_op


@router.get("/farms/{farm_id}/operations", response_model=PaginatedResponse[OperationResponse])
def get_operations(
    farm_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user)
):
    query = db.query(Operation).filter(Operation.farm_id == farm_id).order_by(Operation.performed_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.put("/operations/{op_id}", response_model=OperationResponse)
def update_operation(op_id: int, op_update: OperationUpdate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    db_op = get_or_404(db, Operation, op_id)
    for key, value in op_update.model_dump(exclude_unset=True).items():
        setattr(db_op, key, value)
    db.commit()
    db.refresh(db_op)
    return db_op


@router.delete("/operations/{op_id}", status_code=204)
def delete_operation(op_id: int, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    db_op = get_or_404(db, Operation, op_id)
    db.delete(db_op)
    db.commit()
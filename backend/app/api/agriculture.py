from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..schemas.agriculture import (
    FarmCreate, FarmUpdate, FarmResponse,
    SensorDataCreate, SensorDataResponse,
    OperationCreate, OperationUpdate, OperationResponse,
    PaginatedResponse, DashboardStats,
    OverviewResponse, FarmChartResponse,
)
from ..services.agriculture import AgricultureService
from .auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/agriculture", tags=["agriculture"])

svc = AgricultureService


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """獲取儀表板統計數據（後端聚合計算）"""
    return svc.get_dashboard_stats(db)


@router.get("/dashboard/overview", response_model=OverviewResponse)
def get_dashboard_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """取得所有農場的圖表資料：近 N 天時序 + 各農場最新 NPK"""
    return svc.get_dashboard_overview(db, days)


# ===== Farm CRUD =====

@router.post("/farms", response_model=FarmResponse, status_code=201)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    return svc.create_farm(db, farm.model_dump())


@router.get("/farms", response_model=List[FarmResponse])
def get_farms(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return svc.list_farms(db)


@router.get("/farms/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    try:
        return svc.get_farm(db, farm_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/farms/{farm_id}/chart-data", response_model=FarmChartResponse)
def get_farm_chart_data(
    farm_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """取得單一農場的圖表資料：近 N 天時序 + 最新 NPK"""
    try:
        return svc.get_farm_chart_data(db, farm_id, days)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


@router.put("/farms/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, farm_update: FarmUpdate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    try:
        return svc.update_farm(db, farm_id, farm_update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


@router.delete("/farms/{farm_id}", status_code=204)
def delete_farm(farm_id: int, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    try:
        svc.delete_farm(db, farm_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


# ===== SensorData CRD (no Update) =====

@router.post("/farms/{farm_id}/sensor-data", response_model=SensorDataResponse, status_code=201)
def create_sensor_data(farm_id: int, data: SensorDataCreate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    try:
        return svc.create_sensor_data(db, farm_id, data.model_dump())
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/farms/{farm_id}/sensor-data", response_model=PaginatedResponse[SensorDataResponse])
def get_sensor_data(
    farm_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user)
):
    return svc.list_sensor_data(db, farm_id, page, page_size)


@router.delete("/sensor-data/{data_id}", status_code=204)
def delete_sensor_data(data_id: int, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    try:
        svc.delete_sensor_data(db, data_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


# ===== Operation CRUD =====

@router.post("/farms/{farm_id}/operations", response_model=OperationResponse, status_code=201)
def create_operation(farm_id: int, op: OperationCreate, db: Session = Depends(get_db), user=Depends(get_current_admin_user)):
    try:
        return svc.create_operation(db, farm_id, op.model_dump(), user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/farms/{farm_id}/operations", response_model=PaginatedResponse[OperationResponse])
def get_operations(
    farm_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user)
):
    return svc.list_operations(db, farm_id, page, page_size)


@router.put("/operations/{op_id}", response_model=OperationResponse)
def update_operation(op_id: int, op_update: OperationUpdate, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    try:
        return svc.update_operation(db, op_id, op_update.model_dump(exclude_unset=True))
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


@router.delete("/operations/{op_id}", status_code=204)
def delete_operation(op_id: int, db: Session = Depends(get_db), _user=Depends(get_current_admin_user)):
    try:
        svc.delete_operation(db, op_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")

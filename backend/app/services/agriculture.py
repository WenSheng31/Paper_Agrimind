from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Numeric
from datetime import timedelta
import math

from ..models.agriculture import Farm, SensorData, Operation
from ..schemas.agriculture import (
    DashboardStats,
    OverviewResponse, FarmChartResponse, TimeSeriesItem, FarmLatest,
)


def _avg(col):
    return func.round(cast(func.avg(col), Numeric), 1)


def _sum(col):
    return func.round(cast(func.sum(col), Numeric), 1)


class AgricultureService:

    @staticmethod
    def get_or_404(db: Session, model, obj_id: int):
        obj = db.query(model).filter(model.id == obj_id).first()
        if not obj:
            raise ValueError("找不到指定資源")
        return obj

    @staticmethod
    def paginate(query, page: int, page_size: int) -> dict:
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return dict(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    # ===== Dashboard =====

    @staticmethod
    def get_dashboard_stats(db: Session) -> DashboardStats:
        return DashboardStats(
            total_farms=db.query(Farm).count(),
            total_sensor_data=db.query(SensorData).count(),
            total_operations=db.query(Operation).count(),
        )

    @staticmethod
    def get_dashboard_overview(db: Session, days: int) -> OverviewResponse:
        latest_ts = db.query(func.max(SensorData.timestamp)).scalar()
        if not latest_ts:
            return OverviewResponse(time_series=[], latest_per_farm=[])

        since = latest_ts - timedelta(days=days)
        date_fmt = 'YYYY-MM-DD' if days <= 30 else 'YYYY-MM'
        date_col = func.to_char(SensorData.timestamp, date_fmt).label("date")

        time_series = (
            db.query(
                date_col,
                SensorData.farm_id,
                Farm.name.label("farm_name"),
                _avg(SensorData.temperature).label("avg_temperature"),
                _avg(SensorData.humidity).label("avg_humidity"),
                _sum(SensorData.precipitation).label("total_precipitation"),
                _avg(SensorData.soil_n).label("avg_soil_n"),
                _avg(SensorData.soil_p).label("avg_soil_p"),
                _avg(SensorData.soil_k).label("avg_soil_k"),
            )
            .join(Farm, SensorData.farm_id == Farm.id)
            .filter(SensorData.timestamp >= since)
            .group_by(date_col, SensorData.farm_id, Farm.name)
            .order_by(date_col)
            .all()
        )

        subq = (
            db.query(
                SensorData.farm_id,
                func.max(SensorData.id).label("max_id"),
            )
            .group_by(SensorData.farm_id)
            .subquery()
        )
        latest_rows = (
            db.query(SensorData, Farm.name.label("farm_name"))
            .join(subq, SensorData.id == subq.c.max_id)
            .join(Farm, SensorData.farm_id == Farm.id)
            .all()
        )
        latest_per_farm = [
            FarmLatest(
                farm_id=row.SensorData.farm_id,
                farm_name=row.farm_name,
                soil_n=row.SensorData.soil_n,
                soil_p=row.SensorData.soil_p,
                soil_k=row.SensorData.soil_k,
            )
            for row in latest_rows
        ]

        return OverviewResponse(
            time_series=[TimeSeriesItem(**dict(r._mapping)) for r in time_series],
            latest_per_farm=latest_per_farm,
        )

    # ===== Farm CRUD =====

    @staticmethod
    def create_farm(db: Session, farm_data: dict):
        db_farm = Farm(**farm_data)
        db.add(db_farm)
        db.commit()
        db.refresh(db_farm)
        return db_farm

    @staticmethod
    def list_farms(db: Session):
        return db.query(Farm).all()

    @staticmethod
    def get_farm(db: Session, farm_id: int):
        return AgricultureService.get_or_404(db, Farm, farm_id)

    @staticmethod
    def get_farm_chart_data(db: Session, farm_id: int, days: int) -> FarmChartResponse:
        farm = AgricultureService.get_or_404(db, Farm, farm_id)

        latest_ts = db.query(func.max(SensorData.timestamp)).filter(
            SensorData.farm_id == farm_id
        ).scalar()

        if not latest_ts:
            return FarmChartResponse(time_series=[], latest=None)

        since = latest_ts - timedelta(days=days)
        date_fmt = 'YYYY-MM-DD' if days <= 30 else 'YYYY-MM'
        date_col = func.to_char(SensorData.timestamp, date_fmt).label("date")

        time_series = (
            db.query(
                date_col,
                SensorData.farm_id,
                Farm.name.label("farm_name"),
                _avg(SensorData.temperature).label("avg_temperature"),
                _avg(SensorData.humidity).label("avg_humidity"),
                _sum(SensorData.precipitation).label("total_precipitation"),
                _avg(SensorData.soil_n).label("avg_soil_n"),
                _avg(SensorData.soil_p).label("avg_soil_p"),
                _avg(SensorData.soil_k).label("avg_soil_k"),
            )
            .join(Farm, SensorData.farm_id == Farm.id)
            .filter(SensorData.farm_id == farm_id, SensorData.timestamp >= since)
            .group_by(date_col, SensorData.farm_id, Farm.name)
            .order_by(date_col)
            .all()
        )

        latest = (
            db.query(SensorData)
            .filter(SensorData.farm_id == farm_id)
            .order_by(SensorData.timestamp.desc())
            .first()
        )
        latest_data = None
        if latest:
            latest_data = FarmLatest(
                farm_id=farm.id,
                farm_name=farm.name,
                soil_n=latest.soil_n,
                soil_p=latest.soil_p,
                soil_k=latest.soil_k,
            )

        return FarmChartResponse(
            time_series=[TimeSeriesItem(**dict(r._mapping)) for r in time_series],
            latest=latest_data,
        )

    @staticmethod
    def update_farm(db: Session, farm_id: int, farm_data: dict):
        db_farm = AgricultureService.get_or_404(db, Farm, farm_id)
        for key, value in farm_data.items():
            setattr(db_farm, key, value)
        db.commit()
        db.refresh(db_farm)
        return db_farm

    @staticmethod
    def delete_farm(db: Session, farm_id: int):
        db_farm = AgricultureService.get_or_404(db, Farm, farm_id)
        db.delete(db_farm)
        db.commit()

    # ===== SensorData =====

    @staticmethod
    def create_sensor_data(db: Session, farm_id: int, data: dict):
        AgricultureService.get_or_404(db, Farm, farm_id)
        db_data = SensorData(**data, farm_id=farm_id)
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return db_data

    @staticmethod
    def list_sensor_data(db: Session, farm_id: int, page: int, page_size: int) -> dict:
        query = (
            db.query(SensorData)
            .filter(SensorData.farm_id == farm_id)
            .order_by(SensorData.timestamp.desc())
        )
        return AgricultureService.paginate(query, page, page_size)

    @staticmethod
    def delete_sensor_data(db: Session, data_id: int):
        db_data = AgricultureService.get_or_404(db, SensorData, data_id)
        db.delete(db_data)
        db.commit()

    # ===== Operation =====

    @staticmethod
    def create_operation(db: Session, farm_id: int, op_data: dict, user_id: int):
        AgricultureService.get_or_404(db, Farm, farm_id)
        db_op = Operation(**op_data, farm_id=farm_id, user_id=user_id)
        db.add(db_op)
        db.commit()
        db.refresh(db_op)
        db_op.operator_name = db_op.operator.username if db_op.operator else None
        return db_op

    @staticmethod
    def list_operations(db: Session, farm_id: int, page: int, page_size: int) -> dict:
        query = (
            db.query(Operation)
            .options(joinedload(Operation.operator))
            .filter(Operation.farm_id == farm_id)
            .order_by(Operation.performed_at.desc())
        )
        result = AgricultureService.paginate(query, page, page_size)
        for item in result["items"]:
            item.operator_name = item.operator.username if item.operator else None
        return result

    @staticmethod
    def update_operation(db: Session, op_id: int, op_data: dict):
        db_op = AgricultureService.get_or_404(db, Operation, op_id)
        for key, value in op_data.items():
            setattr(db_op, key, value)
        db.commit()
        db.refresh(db_op)
        return db_op

    @staticmethod
    def delete_operation(db: Session, op_id: int):
        db_op = AgricultureService.get_or_404(db, Operation, op_id)
        db.delete(db_op)
        db.commit()

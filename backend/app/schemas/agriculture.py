from pydantic import BaseModel
from typing import List, Optional, TypeVar, Generic
from datetime import datetime

class DashboardStats(BaseModel):
    total_farms: int
    total_sensor_data: int
    total_operations: int

class TimeSeriesItem(BaseModel):
    date: str
    farm_id: int
    farm_name: str
    avg_temperature: Optional[float] = None
    avg_humidity: Optional[float] = None
    total_precipitation: Optional[float] = None
    avg_sunshine_hours: Optional[float] = None
    avg_soil_moisture: Optional[float] = None
    avg_soil_n: Optional[float] = None
    avg_soil_p: Optional[float] = None
    avg_soil_k: Optional[float] = None

class FarmLatest(BaseModel):
    farm_id: int
    farm_name: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    soil_n: Optional[float] = None
    soil_p: Optional[float] = None
    soil_k: Optional[float] = None

class ChartDataResponse(BaseModel):
    time_series: List[TimeSeriesItem]
    latest_per_farm: List[FarmLatest]

# --- 分頁響應 ---
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# --- SensorData Schemas ---
class SensorDataBase(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    sunshine_hours: Optional[float] = None
    soil_moisture: Optional[float] = None
    soil_n: Optional[float] = None
    soil_p: Optional[float] = None
    soil_k: Optional[float] = None

class SensorDataCreate(SensorDataBase):
    pass

class SensorDataResponse(SensorDataBase):
    id: int
    farm_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Operation Schemas ---
class OperationBase(BaseModel):
    description: str
    performed_at: Optional[datetime] = None

class OperationCreate(OperationBase):
    pass

class OperationUpdate(BaseModel):
    description: Optional[str] = None
    performed_at: Optional[datetime] = None

class OperationResponse(OperationBase):
    id: int
    farm_id: int
    user_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# --- Farm Schemas ---
class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None

class FarmCreate(FarmBase):
    pass

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

class FarmResponse(FarmBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

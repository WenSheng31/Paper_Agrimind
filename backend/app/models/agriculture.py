from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    sensor_data = relationship("SensorData", back_populates="farm", cascade="all, delete-orphan")
    operations = relationship("Operation", back_populates="farm", cascade="all, delete-orphan")


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 環境數據
    temperature = Column(Float)      # 環境溫度 °C
    humidity = Column(Float)         # 環境濕度 %
    precipitation = Column(Float)    # 降水量 mm
    sunshine_hours = Column(Float)   # 日照時數 hr

    # 土壤數據
    soil_moisture = Column(Float)    # 土壤濕度 %
    soil_n = Column(Float)           # 土壤氮含量 mg/kg
    soil_p = Column(Float)           # 土壤磷含量 mg/kg
    soil_k = Column(Float)           # 土壤鉀含量 mg/kg

    # 關聯
    farm = relationship("Farm", back_populates="sensor_data")


class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 操作人員
    
    description = Column(String, index=True) # 操作內容
    performed_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    farm = relationship("Farm", back_populates="operations")
    operator = relationship("User") # 我們需要 import User，這裡用字串關聯也可以，但通常在 __init__ 處理

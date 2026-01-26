import sys
import os
import json
import requests
from typing import Dict, Any

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastmcp import FastMCP
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv
from app.models.agriculture import Farm, SensorData, Operation
from app.core.config import settings

load_dotenv()

mcp = FastMCP("Agriculture Data Tools")

# 資料庫連接
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 縣市對應氣象站
WEATHER_STATIONS = {
    "基隆市": "基隆", "基隆": "基隆",
    "臺北市": "臺北", "臺北": "臺北", "台北市": "臺北", "台北": "臺北",
    "新北市": "板橋", "新北": "板橋", "板橋": "板橋",
    "桃園市": "桃園", "桃園": "桃園",
    "新竹市": "新竹", "新竹縣": "竹東", "新竹": "新竹",
    "苗栗縣": "苗栗", "苗栗": "苗栗",
    "臺中市": "臺中", "臺中": "臺中", "台中市": "臺中", "台中": "臺中",
    "彰化縣": "員林", "彰化": "員林",
    "南投縣": "南投", "南投": "南投",
    "雲林縣": "斗六", "雲林": "斗六",
    "嘉義市": "嘉義", "嘉義縣": "朴子", "嘉義": "嘉義",
    "臺南市": "臺南", "臺南": "臺南", "台南市": "臺南", "台南": "臺南",
    "高雄市": "高雄", "高雄": "高雄",
    "屏東縣": "潮州", "屏東": "潮州",
    "宜蘭縣": "宜蘭", "宜蘭": "宜蘭",
    "花蓮縣": "花蓮", "花蓮": "花蓮",
    "臺東縣": "臺東", "臺東": "臺東", "台東縣": "臺東", "台東": "臺東",
    "澎湖縣": "澎湖", "澎湖": "澎湖",
    "金門縣": "金門", "金門": "金門",
    "連江縣": "馬祖", "馬祖": "馬祖",
}

def get_db():
    """獲取資料庫連接"""
    return SessionLocal()


@mcp.tool()
def get_all_farms_latest() -> str:
    """
    獲取所有農場(田區)的最新感測器資料和農務紀錄。
    返回每個農場的：ID、名稱、最新感測器資料、最新農務紀錄。
    """
    db = get_db()
    try:
        # 1. 獲取所有農場
        farms = db.query(Farm).all()

        if not farms:
            return "目前沒有任何農場資料。"

        farm_ids = [farm.id for farm in farms]

        # 2. 批量獲取最新感測器資料
        sensor_subq = (
            db.query(
                SensorData.farm_id,
                func.max(SensorData.timestamp).label("max_ts")
            )
            .filter(SensorData.farm_id.in_(farm_ids))
            .group_by(SensorData.farm_id)
            .subquery()
        )
        
        latest_sensors = (
            db.query(SensorData)
            .join(
                sensor_subq,
                (SensorData.farm_id == sensor_subq.c.farm_id) &
                (SensorData.timestamp == sensor_subq.c.max_ts)
            )
            .all()
        )
        sensor_map = {s.farm_id: s for s in latest_sensors}

        # 3. 批量獲取最新農務紀錄
        op_subq = (
            db.query(
                Operation.farm_id,
                func.max(Operation.performed_at).label("max_at")
            )
            .filter(Operation.farm_id.in_(farm_ids))
            .group_by(Operation.farm_id)
            .subquery()
        )
        
        latest_ops = (
            db.query(Operation)
            .join(
                op_subq,
                (Operation.farm_id == op_subq.c.farm_id) &
                (Operation.performed_at == op_subq.c.max_at)
            )
            .all()
        )
        op_map = {o.farm_id: o for o in latest_ops}

        # 4. 組合最終結果
        results = []
        for farm in farms:
            latest_sensor = sensor_map.get(farm.id)
            latest_operation = op_map.get(farm.id)

            farm_data = {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "location": farm.location,
                "latest_sensor_data": None,
                "latest_operation": None,
            }

            if latest_sensor:
                farm_data["latest_sensor_data"] = {
                    "timestamp": latest_sensor.timestamp.isoformat() if latest_sensor.timestamp else None,
                    "temperature": latest_sensor.temperature,
                    "humidity": latest_sensor.humidity,
                    "precipitation": latest_sensor.precipitation,
                    "sunshine_hours": latest_sensor.sunshine_hours,
                    "soil_moisture": latest_sensor.soil_moisture,
                    "soil_n": latest_sensor.soil_n,
                    "soil_p": latest_sensor.soil_p,
                    "soil_k": latest_sensor.soil_k,
                }

            if latest_operation:
                farm_data["latest_operation"] = {
                    "performed_at": latest_operation.performed_at.isoformat() if latest_operation.performed_at else None,
                    "description": latest_operation.description,
                }

            results.append(farm_data)

        return json.dumps(results, ensure_ascii=False, indent=2)

    finally:
        db.close()

@mcp.tool()
def get_weather(location: str) -> Dict[str, Any]:
    """
    獲取指定地點的氣象觀測資料

    參數：
    - location: 地點名稱（縣市名或氣象站名，如 "臺中市"、"臺中"、"高雄"）

    返回即時觀測資料，包括溫度、濕度、氣壓、風速、降雨量等。
    """
    if not location or not location.strip():
        return {"error": "請提供地點名稱，例如：臺中市、臺北、高雄"}

    location = location.strip().replace("台", "臺")

    # 查找對應的氣象站
    station_name = WEATHER_STATIONS.get(location, location)

    api_key = settings.CWA_API_KEY
    if not api_key:
        return {"error": "未設定中央氣象署 API Key"}

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
    params = {
        "Authorization": api_key,
        "format": "JSON",
        "StationName": station_name
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success") != "true":
            return {"error": "API 請求失敗"}

        records = data.get("records", {})
        stations = records.get("Station", []) if isinstance(records, dict) else []

        if not stations:
            return {"error": f"找不到氣象站: {station_name}"}

        station = stations[0]
        obs = station.get("WeatherElement", {}) or {}
        geo = station.get("GeoInfo", {}) or {}
        obs_time = station.get("ObsTime", {}) or {}
        now_data = obs.get("Now", {}) or {}

        return {
            "station_name": station.get("StationName"),
            "city": geo.get("CountyName"),
            "obs_time": obs_time.get("DateTime") if isinstance(obs_time, dict) else None,
            "weather": obs.get("Weather"),
            "temperature": obs.get("AirTemperature"),
            "humidity": obs.get("RelativeHumidity"),
            "pressure": obs.get("AirPressure"),
            "wind_speed": obs.get("WindSpeed"),
            "wind_direction": obs.get("WindDirection"),
            "precipitation": now_data.get("Precipitation") if isinstance(now_data, dict) else None,
        }

    except requests.exceptions.Timeout:
        return {"error": "請求超時，請稍後再試"}
    except requests.exceptions.RequestException as e:
        return {"error": f"網路請求失敗: {str(e)}"}
    except Exception as e:
        return {"error": f"發生錯誤: {str(e)}"}

if __name__ == "__main__":
    mcp.run()

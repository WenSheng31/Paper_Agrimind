import sys
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastmcp import FastMCP
from sqlalchemy import create_engine, func, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models.agriculture import Farm, SensorData, Operation
from app.core.config import settings

load_dotenv()

mcp = FastMCP("Agriculture Data Tools")

# 資料庫連接
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """獲取資料庫連接"""
    return SessionLocal()


# ============== 白名單配置 ==============

# 允許查詢的表和對應的模型
TABLE_MODELS = {
    "farms": Farm,
    "sensor_data": SensorData,
    "operations": Operation,
}

# 允許查詢的欄位（每個表）
ALLOWED_FIELDS = {
    "farms": {"id", "name", "location", "description", "created_at"},
    "sensor_data": {
        "id", "farm_id", "timestamp",
        "temperature", "humidity", "precipitation", "sunshine_hours",
        "soil_moisture", "soil_n", "soil_p", "soil_k"
    },
    "operations": {"id", "farm_id", "user_id", "description", "performed_at"},
}

# 允許的篩選操作符
ALLOWED_OPS = {"=", ">", "<", ">=", "<=", "!=", "like"}

# 允許的聚合函數
ALLOWED_FUNCS = {"avg", "sum", "max", "min", "count"}

# 最大返回筆數
MAX_LIMIT = 500


# ============== 時間工具 ==============

@mcp.tool()
def get_current_time() -> Dict[str, Any]:
    """
    取得目前的日期和時間。

    用於處理「今天」、「這週」、「上個月」等相對時間查詢時，先取得當前時間作為參考。
    """
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "weekday": now.strftime("%A"),
        "week_number": now.isocalendar()[1]
    }


# ============== 資料庫查詢工具 ==============

@mcp.tool()
def get_database_schema() -> Dict[str, Any]:
    """
    查詢資料庫結構，了解有哪些資料表和欄位可用。

    使用此工具來了解可查詢的資料結構，再使用 query_database 進行查詢。
    """
    return {
        "tables": {
            "farms": {
                "description": "農場資料",
                "fields": {
                    "id": "農場 ID",
                    "name": "農場名稱",
                    "location": "農場位置",
                    "description": "農場描述",
                    "created_at": "建立時間"
                }
            },
            "sensor_data": {
                "description": "感測器資料（每小時記錄一筆）",
                "fields": {
                    "id": "記錄 ID",
                    "farm_id": "所屬農場 ID",
                    "timestamp": "記錄時間",
                    "temperature": "環境溫度 (°C)",
                    "humidity": "環境濕度 (%)",
                    "precipitation": "降水量 (mm)",
                    "sunshine_hours": "日照時數 (hr)",
                    "soil_moisture": "土壤濕度 (%)",
                    "soil_n": "土壤氮含量 (mg/kg)",
                    "soil_p": "土壤磷含量 (mg/kg)",
                    "soil_k": "土壤鉀含量 (mg/kg)"
                }
            },
            "operations": {
                "description": "農場操作記錄",
                "fields": {
                    "id": "記錄 ID",
                    "farm_id": "所屬農場 ID",
                    "user_id": "操作人員 ID",
                    "description": "操作內容",
                    "performed_at": "操作時間"
                }
            }
        },
        "notes": [
            "sensor_data 每小時記錄一筆，查詢大範圍時建議使用 aggregation 聚合",
            "可用聚合函數: avg, sum, max, min, count",
            "可用時間分組: hour, day, week, month"
        ]
    }


@mcp.tool()
def query_database(
    table: str,
    fields: Optional[List[str]] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    aggregation: Optional[Dict[str, str]] = None,
    group_by: Optional[str] = None,
    order_by: Optional[str] = None,
    order_dir: str = "desc",
    limit: int = 100
) -> Dict[str, Any]:
    """
    通用資料庫查詢工具，可查詢農場、感測器資料、操作記錄等。

    可用資料表與欄位：
    - farms（農場）: id, name, location, description, created_at
    - sensor_data（感測器）: id, farm_id, timestamp, temperature(°C), humidity(%),
      precipitation(mm), sunshine_hours(hr), soil_moisture(%), soil_n, soil_p, soil_k (mg/kg)
    - operations（操作記錄）: id, farm_id, user_id, description, performed_at

    參數：
    - table: 資料表名稱
    - fields: 要查詢的欄位列表，如 ["temperature", "humidity"]，不指定則返回所有欄位
    - filters: 篩選條件列表，格式為 [{"field": "欄位名", "op": "操作符", "value": "值"}]
              操作符可用: =, >, <, >=, <=, !=, like
              範例: [{"field": "temperature", "op": ">", "value": 30}]
    - aggregation: 聚合設定，格式為 {"field": "欄位名", "func": "聚合函數"}
                   函數可用: avg（平均）, sum（總和）, max（最大）, min（最小）, count（計數）
    - group_by: 分組方式，可用 "hour"、"day"、"week"、"month" 或欄位名如 "farm_id"
    - order_by: 排序欄位
    - order_dir: 排序方向，"asc" 或 "desc"（預設）
    - limit: 返回筆數上限，預設 100，最大 500

    備註：sensor_data 每小時記錄一筆，查詢長時間範圍請使用 aggregation + group_by 避免資料過多。
    """
    db = get_db()

    try:
        # 驗證表名
        if table not in TABLE_MODELS:
            return {"error": f"不允許的資料表: {table}，可用: {list(TABLE_MODELS.keys())}"}

        model = TABLE_MODELS[table]
        allowed_fields = ALLOWED_FIELDS[table]

        # 驗證並過濾欄位
        if fields:
            fields = [f for f in fields if f in allowed_fields]
            if not fields:
                return {"error": f"沒有有效的欄位，可用欄位: {allowed_fields}"}
        else:
            fields = list(allowed_fields)

        # 限制筆數
        limit = min(limit, MAX_LIMIT)

        # 處理聚合查詢
        if aggregation:
            agg_field = aggregation.get("field")
            agg_func = aggregation.get("func", "").lower()

            if agg_field not in allowed_fields:
                return {"error": f"不允許的聚合欄位: {agg_field}"}
            if agg_func not in ALLOWED_FUNCS:
                return {"error": f"不允許的聚合函數: {agg_func}，可用: {ALLOWED_FUNCS}"}

            column = getattr(model, agg_field)

            # 選擇聚合函數
            if agg_func == "avg":
                agg_column = func.avg(column)
            elif agg_func == "sum":
                agg_column = func.sum(column)
            elif agg_func == "max":
                agg_column = func.max(column)
            elif agg_func == "min":
                agg_column = func.min(column)
            elif agg_func == "count":
                agg_column = func.count(column)

            # 處理分組
            if group_by:
                group_column = _get_group_column(model, group_by, table)
                if group_column is None:
                    return {"error": f"不允許的分組方式: {group_by}"}

                query = db.query(group_column.label("group"), agg_column.label("value"))
                query = _apply_filters(query, model, filters, allowed_fields)
                query = query.group_by(group_column)

                if order_dir == "asc":
                    query = query.order_by(asc("value"))
                else:
                    query = query.order_by(desc("value"))

                results = query.limit(limit).all()
                return {
                    "aggregation": f"{agg_func}({agg_field})",
                    "group_by": group_by,
                    "results": [{"group": _format_value(r.group), "value": round(r.value, 2) if r.value else None} for r in results]
                }
            else:
                # 無分組的聚合
                query = db.query(agg_column.label("value"))
                query = _apply_filters(query, model, filters, allowed_fields)
                result = query.first()
                return {
                    "aggregation": f"{agg_func}({agg_field})",
                    "value": round(result.value, 2) if result and result.value else None
                }

        # 一般查詢
        columns = [getattr(model, f) for f in fields if hasattr(model, f)]
        query = db.query(*columns)

        # 應用篩選
        query = _apply_filters(query, model, filters, allowed_fields)

        # 排序
        if order_by and order_by in allowed_fields:
            order_column = getattr(model, order_by)
            if order_dir == "asc":
                query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(order_column))

        # 執行查詢
        results = query.limit(limit).all()

        # 格式化結果
        return {
            "table": table,
            "count": len(results),
            "results": [
                {fields[i]: _format_value(v) for i, v in enumerate(row)}
                for row in results
            ]
        }

    except Exception as e:
        return {"error": f"查詢失敗: {str(e)}"}
    finally:
        db.close()


def _apply_filters(query, model, filters: Optional[List[Dict]], allowed_fields: set):
    """應用篩選條件"""
    if not filters:
        return query

    conditions = []
    for f in filters:
        field = f.get("field")
        op = f.get("op", "=")
        value = f.get("value")

        if field not in allowed_fields:
            continue
        if op not in ALLOWED_OPS:
            continue

        column = getattr(model, field, None)
        if column is None:
            continue

        if op == "=":
            conditions.append(column == value)
        elif op == ">":
            conditions.append(column > value)
        elif op == "<":
            conditions.append(column < value)
        elif op == ">=":
            conditions.append(column >= value)
        elif op == "<=":
            conditions.append(column <= value)
        elif op == "!=":
            conditions.append(column != value)
        elif op == "like":
            conditions.append(column.like(f"%{value}%"))

    if conditions:
        query = query.filter(and_(*conditions))

    return query


def _get_group_column(model, group_by: str, table: str):
    """獲取分組欄位"""
    # 時間分組（僅適用於有時間欄位的表）
    time_field = None
    if table == "sensor_data" and hasattr(model, "timestamp"):
        time_field = model.timestamp
    elif table == "operations" and hasattr(model, "performed_at"):
        time_field = model.performed_at
    elif table == "farms" and hasattr(model, "created_at"):
        time_field = model.created_at

    if group_by == "hour" and time_field is not None:
        return func.date_trunc("hour", time_field)
    elif group_by == "day" and time_field is not None:
        return func.date_trunc("day", time_field)
    elif group_by == "week" and time_field is not None:
        return func.date_trunc("week", time_field)
    elif group_by == "month" and time_field is not None:
        return func.date_trunc("month", time_field)
    elif group_by in ALLOWED_FIELDS.get(table, set()):
        return getattr(model, group_by, None)

    return None


def _format_value(value):
    """格式化值（處理日期時間等特殊類型）"""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


# ============== 農務記錄工具 ==============

@mcp.tool()
def create_operation(
    farm_id: int,
    description: str,
    performed_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    新增農務操作記錄。

    參數：
    - farm_id: 農場 ID（必填），可先用 query_database(table="farms") 查詢農場列表取得 ID
    - description: 操作內容描述（必填），如「施肥」、「灌溉」、「噴藥」、「採收」等
    - performed_at: 操作時間（選填），格式為 ISO 格式如 "2024-01-15T10:30:00"，不填則使用當前時間

    使用流程：
    1. 先用 query_database(table="farms", fields=["id", "name"]) 查詢農場列表
    2. 確認目標農場的 ID
    3. 呼叫此工具新增記錄

    範例：
    - create_operation(farm_id=1, description="施用氮肥 50kg")
    - create_operation(farm_id=2, description="灌溉 30 分鐘")
    - create_operation(farm_id=1, description="採收番茄", performed_at="2024-01-10T08:00:00")
    """
    db = get_db()

    try:
        # 驗證農場是否存在
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            return {"error": f"找不到農場 ID: {farm_id}，請先用 query_database(table='farms') 查詢農場列表"}

        # 驗證描述不為空
        if not description or not description.strip():
            return {"error": "操作描述不能為空"}

        # 處理時間
        operation_time = None
        if performed_at:
            try:
                operation_time = datetime.fromisoformat(performed_at)
            except ValueError:
                return {"error": f"時間格式錯誤，請使用 ISO 格式，如 2024-01-15T10:30:00"}
        else:
            operation_time = datetime.now()

        # 建立記錄
        operation = Operation(
            farm_id=farm_id,
            description=description.strip(),
            performed_at=operation_time
        )

        db.add(operation)
        db.commit()
        db.refresh(operation)

        return {
            "success": True,
            "message": "農務記錄已新增",
            "operation": {
                "id": operation.id,
                "farm_id": operation.farm_id,
                "farm_name": farm.name,
                "description": operation.description,
                "performed_at": operation.performed_at.isoformat()
            }
        }

    except Exception as e:
        db.rollback()
        return {"error": f"新增失敗: {str(e)}"}
    finally:
        db.close()


# ============== 氣象工具 (保留) ==============

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
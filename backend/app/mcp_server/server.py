import sys
import os
import json
import base64
import mimetypes
import requests
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastmcp import FastMCP
from sqlalchemy import create_engine, func, and_, desc, asc
from sqlalchemy.orm import sessionmaker, aliased
from dotenv import load_dotenv
from app.models.agriculture import Farm, SensorData, Operation, ImageRecord, ImageRecordFile
from app.models.knowledge import KnowledgeDocument
from app.services.embedding import get_embedding
from app.core.config import settings

load_dotenv()

mcp = FastMCP("Agriculture Data Tools")

# 資料庫連接
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """取得資料庫 session，確保使用後自動關閉"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============== 白名單配置 ==============

TABLE_MODELS = {
    "farms": Farm,
    "sensor_data": SensorData,
    "operations": Operation,
}

ALLOWED_FIELDS = {
    "farms": {"id", "name", "location", "description", "created_at"},
    "sensor_data": {
        "id", "farm_id", "timestamp",
        "temperature", "humidity", "precipitation", "sunshine_hours",
        "soil_moisture", "soil_n", "soil_p", "soil_k",
    },
    "operations": {"id", "farm_id", "user_id", "description", "performed_at"},
}

ALLOWED_OPS = {"=", ">", "<", ">=", "<=", "!=", "like"}
ALLOWED_FUNCS = {"avg", "sum", "max", "min", "count"}
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
        "week_number": now.isocalendar()[1],
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
                    "created_at": "建立時間",
                },
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
                    "soil_k": "土壤鉀含量 (mg/kg)",
                },
            },
            "operations": {
                "description": "農場操作記錄",
                "fields": {
                    "id": "記錄 ID",
                    "farm_id": "所屬農場 ID",
                    "user_id": "操作人員 ID",
                    "description": "操作內容",
                    "performed_at": "操作時間",
                },
            },
        },
        "notes": [
            "sensor_data 每小時記錄一筆，查詢大範圍時建議使用 aggregation 聚合",
            "可用聚合函數: avg, sum, max, min, count",
            "可用時間分組: hour, day, week, month",
        ],
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
    limit: int = 100,
) -> Dict[str, Any]:
    """
    通用資料庫查詢工具，可查詢農場、感測器資料、操作記錄等。

    可用資料表與欄位：
    - farms（農場）: id, name, location, description, created_at
    - sensor_data（感測器）: id, farm_id, timestamp, temperature(°C), humidity(%),
      precipitation(mm), sunshine_hours(hr), soil_moisture(%), soil_n, soil_p, soil_k (mg/kg)
    - operations（操作記錄）: id, farm_id, user_id, description, performed_at

    重要：sensor_data 每小時記錄一筆，資料量參考：
    - 1天 = 24筆，1週 = 168筆，1月 = 720筆
    - 查詢超過1天的資料時，務必使用 aggregation + group_by 做聚合，避免拉取大量原始資料
    - 例如查詢一週資料：用 group_by="day" 得到7筆日平均，而非168筆原始資料

    參數：
    - table: 資料表名稱
    - fields: 要查詢的欄位列表，如 ["temperature", "humidity"]，不指定則返回所有欄位
    - filters: 篩選條件列表，格式為 [{"field": "欄位名", "op": "操作符", "value": "值"}]
              操作符可用: =, >, <, >=, <=, !=, like
              重要：查詢農場名稱時，請優先使用 like 模糊比對而非 = 精確比對，
              因為使用者說的名稱可能只是農場全名的一部分（如「草莓園」→「大湖草莓園」）
              範例: [{"field": "name", "op": "like", "value": "草莓"}]
              範例: [{"field": "temperature", "op": ">", "value": 30}]
    - aggregation: 聚合設定，格式為 {"field": "欄位名", "func": "聚合函數"}
                   函數可用: avg（平均）, sum（總和）, max（最大）, min（最小）, count（計數）
    - group_by: 分組方式，可用 "hour"、"day"、"week"、"month" 或欄位名如 "farm_id"
    - order_by: 排序欄位
    - order_dir: 排序方向，"asc" 或 "desc"（預設）
    - limit: 返回筆數上限，預設 100，最大 500
    """
    # 驗證表名
    if table not in TABLE_MODELS:
        return {"error": f"不允許的資料表: {table}，可用: {list(TABLE_MODELS.keys())}"}

    model = TABLE_MODELS[table]
    allowed_fields = ALLOWED_FIELDS[table]

    # 驗證並過濾欄位
    if fields:
        fields = [f for f in fields if f in allowed_fields]
        if not fields:
            return {"error": f"沒有有效的欄位，可用欄位: {sorted(allowed_fields)}"}
    else:
        fields = sorted(allowed_fields)

    limit = min(limit, MAX_LIMIT)

    with get_db() as db:
        try:
            # 處理聚合查詢
            if aggregation:
                return _handle_aggregation(
                    db, model, table, aggregation, filters,
                    allowed_fields, group_by, order_dir, limit,
                )

            # 一般查詢
            columns = [getattr(model, f) for f in fields if hasattr(model, f)]
            if not columns:
                return {"error": "沒有有效的查詢欄位"}

            query = db.query(*columns)
            query = _apply_filters(query, model, filters, allowed_fields)

            # 排序
            if order_by and order_by in allowed_fields and hasattr(model, order_by):
                order_column = getattr(model, order_by)
                query = query.order_by(asc(order_column) if order_dir == "asc" else desc(order_column))

            results = query.limit(limit).all()

            return {
                "table": table,
                "count": len(results),
                "results": [
                    {fields[i]: _format_value(v) for i, v in enumerate(row)}
                    for row in results
                ],
            }

        except Exception as e:
            return {"error": f"查詢失敗: {str(e)}"}


def _handle_aggregation(db, model, table, aggregation, filters, allowed_fields, group_by, order_dir, limit):
    """處理聚合查詢"""
    agg_field = aggregation.get("field")
    agg_func = aggregation.get("func", "").lower()

    if agg_field not in allowed_fields:
        return {"error": f"不允許的聚合欄位: {agg_field}，可用: {sorted(allowed_fields)}"}
    if agg_func not in ALLOWED_FUNCS:
        return {"error": f"不允許的聚合函數: {agg_func}，可用: {sorted(ALLOWED_FUNCS)}"}
    if not hasattr(model, agg_field):
        return {"error": f"欄位不存在: {agg_field}"}

    column = getattr(model, agg_field)

    agg_map = {
        "avg": func.avg, "sum": func.sum, "max": func.max,
        "min": func.min, "count": func.count,
    }
    agg_column = agg_map[agg_func](column)

    if group_by:
        group_column = _get_group_column(model, group_by, table)
        if group_column is None:
            return {"error": f"不允許的分組方式: {group_by}"}

        query = db.query(group_column.label("group"), agg_column.label("value"))
        query = _apply_filters(query, model, filters, allowed_fields)
        query = query.group_by(group_column)
        query = query.order_by(asc("group") if order_dir == "asc" else desc("group"))

        results = query.limit(limit).all()
        return {
            "aggregation": f"{agg_func}({agg_field})",
            "group_by": group_by,
            "results": [
                {
                    "group": _format_value(r.group),
                    "value": round(float(r.value), 2) if r.value is not None else None,
                }
                for r in results
            ],
        }
    else:
        query = db.query(agg_column.label("value"))
        query = _apply_filters(query, model, filters, allowed_fields)
        result = query.first()
        return {
            "aggregation": f"{agg_func}({agg_field})",
            "value": round(float(result.value), 2) if result and result.value is not None else None,
        }


def _apply_filters(query, model, filters: Optional[List[Dict]], allowed_fields: set):
    """應用篩選條件"""
    if not filters:
        return query

    conditions = []
    for f in filters:
        field = f.get("field")
        op = f.get("op", "=")
        value = f.get("value")

        if field not in allowed_fields or op not in ALLOWED_OPS:
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
            # 跳脫使用者輸入中的 SQL wildcard 字元，避免非預期的模糊匹配
            safe_value = str(value).replace("%", r"\%").replace("_", r"\_")
            conditions.append(column.like(f"%{safe_value}%", escape="\\"))

    if conditions:
        query = query.filter(and_(*conditions))

    return query


def _get_group_column(model, group_by: str, table: str):
    """獲取分組欄位"""
    time_field = None
    if table == "sensor_data" and hasattr(model, "timestamp"):
        time_field = model.timestamp
    elif table == "operations" and hasattr(model, "performed_at"):
        time_field = model.performed_at
    elif table == "farms" and hasattr(model, "created_at"):
        time_field = model.created_at

    time_formats = {
        "hour": "YYYY-MM-DD HH24",
        "day": "YYYY-MM-DD",
        "week": "IYYY-IW",
        "month": "YYYY-MM",
    }

    if group_by in time_formats and time_field is not None:
        return func.to_char(time_field, time_formats[group_by])
    elif group_by in ALLOWED_FIELDS.get(table, set()):
        return getattr(model, group_by, None)

    return None


def _format_value(value):
    """格式化值（處理日期時間等特殊類型）"""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


# ============== 農場總覽工具 ==============

@mcp.tool()
def get_farms_overview() -> Dict[str, Any]:
    """
    取得所有農場的最新狀態總覽，包含每個農場最新一筆感測器數據和最近一筆農務記錄。
    適合用於首頁總結、整體狀態分析。
    """
    with get_db() as db:
        try:
            farms = db.query(Farm).all()
            if not farms:
                return {"farms": [], "message": "目前沒有任何農場"}

            farm_ids = [f.id for f in farms]

            # 子查詢：每個農場最新的 sensor_data timestamp
            latest_sensor_sub = (
                db.query(
                    SensorData.farm_id,
                    func.max(SensorData.timestamp).label("max_ts"),
                )
                .filter(SensorData.farm_id.in_(farm_ids))
                .group_by(SensorData.farm_id)
                .subquery()
            )

            latest_sensors = (
                db.query(SensorData)
                .join(
                    latest_sensor_sub,
                    and_(
                        SensorData.farm_id == latest_sensor_sub.c.farm_id,
                        SensorData.timestamp == latest_sensor_sub.c.max_ts,
                    ),
                )
                .all()
            )
            sensor_map = {s.farm_id: s for s in latest_sensors}

            # 子查詢：每個農場最新的 operation
            latest_op_sub = (
                db.query(
                    Operation.farm_id,
                    func.max(Operation.performed_at).label("max_ts"),
                )
                .filter(Operation.farm_id.in_(farm_ids))
                .group_by(Operation.farm_id)
                .subquery()
            )

            latest_operations = (
                db.query(Operation)
                .join(
                    latest_op_sub,
                    and_(
                        Operation.farm_id == latest_op_sub.c.farm_id,
                        Operation.performed_at == latest_op_sub.c.max_ts,
                    ),
                )
                .all()
            )
            op_map = {o.farm_id: o for o in latest_operations}

            result = []
            for farm in farms:
                farm_data = {
                    "id": farm.id,
                    "name": farm.name,
                    "location": farm.location,
                    "latest_sensor": None,
                    "latest_operation": None,
                }

                sensor = sensor_map.get(farm.id)
                if sensor:
                    farm_data["latest_sensor"] = {
                        "timestamp": sensor.timestamp.isoformat(),
                        "temperature": sensor.temperature,
                        "humidity": sensor.humidity,
                        "precipitation": sensor.precipitation,
                        "sunshine_hours": sensor.sunshine_hours,
                        "soil_moisture": sensor.soil_moisture,
                        "soil_n": sensor.soil_n,
                        "soil_p": sensor.soil_p,
                        "soil_k": sensor.soil_k,
                    }

                op = op_map.get(farm.id)
                if op:
                    farm_data["latest_operation"] = {
                        "description": op.description,
                        "performed_at": op.performed_at.isoformat(),
                    }

                result.append(farm_data)

            return {"farms": result, "total": len(result)}

        except Exception as e:
            return {"error": f"查詢失敗: {str(e)}"}


# ============== 共用：地點名稱正規化 ==============

def _normalize_location(location: str) -> str:
    """正規化地點名稱：去空白、台→臺"""
    return location.strip().replace("台", "臺")


# 縣市對應氣象站
WEATHER_STATIONS = {
    "基隆市": "基隆", "基隆": "基隆",
    "臺北市": "臺北", "臺北": "臺北",
    "新北市": "板橋", "新北": "板橋", "板橋": "板橋",
    "桃園市": "桃園", "桃園": "桃園",
    "新竹市": "新竹", "新竹縣": "竹東", "新竹": "新竹",
    "苗栗縣": "苗栗", "苗栗": "苗栗",
    "臺中市": "臺中", "臺中": "臺中",
    "彰化縣": "員林", "彰化": "員林",
    "南投縣": "南投", "南投": "南投",
    "雲林縣": "斗六", "雲林": "斗六",
    "嘉義市": "嘉義", "嘉義縣": "朴子", "嘉義": "嘉義",
    "臺南市": "臺南", "臺南": "臺南",
    "高雄市": "高雄", "高雄": "高雄",
    "屏東縣": "潮州", "屏東": "潮州",
    "宜蘭縣": "宜蘭", "宜蘭": "宜蘭",
    "花蓮縣": "花蓮", "花蓮": "花蓮",
    "臺東縣": "臺東", "臺東": "臺東",
    "澎湖縣": "澎湖", "澎湖": "澎湖",
    "金門縣": "金門", "金門": "金門",
    "連江縣": "馬祖", "馬祖": "馬祖",
}


# ============== 氣象工具 ==============

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

    location = _normalize_location(location)
    station_name = WEATHER_STATIONS.get(location, location)

    api_key = settings.CWA_API_KEY
    if not api_key:
        return {"error": "未設定中央氣象署 API Key"}

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
    params = {
        "Authorization": api_key,
        "format": "JSON",
        "StationName": station_name,
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
            return {"error": f"找不到氣象站: {station_name}，請確認地點名稱"}

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


@mcp.tool()
def get_weather_forecast(location: str) -> Dict[str, Any]:
    """
    取得指定縣市未來一週天氣預報（資料來源：中央氣象署）。

    與 get_weather（即時觀測）不同，此工具提供未來預報資料，適合用於農務規劃建議，
    例如：是否適合灌溉、施肥、採收、是否需要防颱防寒等。

    參數：
    - location: 縣市名稱（必填），如「臺中市」「高雄市」「臺北市」「嘉義縣」

    回傳：未來一週每 12 小時的天氣現象、溫度、降雨機率、濕度、風速等。
    """
    api_key = settings.CWA_API_KEY
    if not api_key:
        return {"error": "未設定中央氣象署 API Key"}

    if not location or not location.strip():
        return {"error": "請提供縣市名稱，例如：臺中市、高雄市"}

    location = _normalize_location(location)

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
    params = {
        "Authorization": api_key,
        "format": "JSON",
        "locationName": location,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("success") != "true":
            return {"error": "API 請求失敗"}

        locations_list = data.get("records", {}).get("Locations", [])
        if not locations_list:
            return {"error": f"找不到「{location}」的預報資料，請使用完整縣市名如「臺中市」"}

        location_data = None
        for loc_group in locations_list:
            for loc in loc_group.get("Location", []):
                if loc.get("LocationName") == location:
                    location_data = loc
                    break
            if location_data:
                break

        if not location_data:
            return {"error": f"找不到「{location}」的預報資料，請確認縣市名稱"}

        # 解析各天氣要素
        elements = {}
        for elem in location_data.get("WeatherElement", []):
            elements[elem["ElementName"]] = elem.get("Time", [])

        # 組合預報時段
        weather_times = elements.get("天氣現象", [])
        forecasts = []
        for i, t in enumerate(weather_times):
            forecast = {
                "開始時間": t.get("StartTime", ""),
                "結束時間": t.get("EndTime", ""),
                "天氣": t.get("ElementValue", [{}])[0].get("Weather", ""),
            }

            def get_val(name, key, idx=i):
                times = elements.get(name, [])
                if idx < len(times):
                    vals = times[idx].get("ElementValue", [{}])
                    return vals[0].get(key, "") if vals else ""
                return ""

            forecast["平均溫度"] = get_val("平均溫度", "Temperature")
            forecast["最高溫度"] = get_val("最高溫度", "MaxTemperature")
            forecast["最低溫度"] = get_val("最低溫度", "MinTemperature")
            forecast["降雨機率"] = get_val("降雨機率", "ProbabilityOfPrecipitation")
            forecast["相對濕度"] = get_val("相對濕度", "RelativeHumidity")
            forecast["風速"] = get_val("風速", "WindSpeed")
            forecast["風向"] = get_val("風向", "WindDirection")

            forecasts.append(forecast)

        return {
            "location": location,
            "description": "未來一週逐12小時天氣預報",
            "forecasts": forecasts,
        }

    except requests.exceptions.Timeout:
        return {"error": "請求超時，請稍後再試"}
    except requests.exceptions.RequestException as e:
        return {"error": f"網路請求失敗: {str(e)}"}
    except Exception as e:
        return {"error": f"發生錯誤: {str(e)}"}


# ============== 農產品價格工具 ==============

@mcp.tool()
def get_crop_price(
    crop_name: str,
    market: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top: int = 20,
) -> Dict[str, Any]:
    """
    查詢農產品批發市場交易行情（資料來源：農業部開放資料）。

    重要：作物名稱通常帶有品種，例如「小番茄-玉女」「香蕉」「釋迦-鳳梨釋迦」「高麗菜-改良種」。
    如果不確定完整名稱，可以只輸入關鍵字（如「番茄」），工具會自動模糊比對所有包含該關鍵字的品種。

    參數：
    - crop_name: 作物名稱或關鍵字（必填），如「番茄」「高麗菜」「香蕉」「釋迦」「草莓」
    - market: 市場名稱（選填），如「台北一」「台北二」「三重」「台中」「高雄」，不填則回傳所有市場
    - start_date: 起始日期（選填），民國年格式如 "114.01.01"，不填則預設近四天
    - end_date: 結束日期（選填），民國年格式如 "114.06.30"，不填則預設近四天
    - top: 回傳筆數上限，預設 20

    日期格式說明：使用民國年，如西元 2025 年 = 民國 114 年，寫作 "114.01.01"
    西元年轉民國年：民國年 = 西元年 - 1911

    回傳欄位：交易日期、市場名稱、作物名稱、上價、中價、下價、平均價（元/公斤）、交易量（公斤）

    範例：
    - get_crop_price(crop_name="番茄") — 模糊搜尋所有番茄品種
    - get_crop_price(crop_name="高麗菜", market="台北一") — 指定市場
    - get_crop_price(crop_name="香蕉", start_date="114.01.01", end_date="114.01.31") — 查歷史價格
    """
    if not crop_name or not crop_name.strip():
        return {"error": "請提供作物名稱，例如：番茄、高麗菜、香蕉"}

    crop_name = crop_name.strip()

    try:
        url = "https://data.moa.gov.tw/Service/OpenData/FromM/FarmTransData.aspx"

        # 先嘗試精確查詢
        params = {"CropName": crop_name, "$top": top}
        if market:
            params["MarketName"] = market
        if start_date:
            params["StartDate"] = start_date
        if end_date:
            params["EndDate"] = end_date

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # 過濾休市資料，並驗證作物名稱確實匹配（API 會忽略無效 CropName 回傳全部資料）
        results = [
            item for item in data
            if item.get("作物代號") != "rest" and crop_name in item.get("作物名稱", "")
        ]

        # 精確查詢無結果時，改用模糊搜尋（拉大量資料後過濾）
        if not results:
            fuzzy_params = {"$top": 2000}
            if market:
                fuzzy_params["MarketName"] = market
            if start_date:
                fuzzy_params["StartDate"] = start_date
            if end_date:
                fuzzy_params["EndDate"] = end_date

            resp = requests.get(url, params=fuzzy_params, timeout=15)
            resp.raise_for_status()
            all_data = resp.json()

            results = [
                item for item in all_data
                if item.get("作物代號") != "rest" and crop_name in item.get("作物名稱", "")
            ][:top]

        if not results:
            return {"message": f"查無包含「{crop_name}」的交易資料，可能今日休市或請換個關鍵字", "results": []}

        formatted = []
        for item in results:
            formatted.append({
                "交易日期": item.get("交易日期", ""),
                "市場名稱": item.get("市場名稱", ""),
                "作物名稱": item.get("作物名稱", ""),
                "平均價": item.get("平均價", 0),
                "上價": item.get("上價", 0),
                "中價": item.get("中價", 0),
                "下價": item.get("下價", 0),
                "交易量": item.get("交易量", 0),
            })

        return {
            "crop": crop_name,
            "count": len(formatted),
            "results": formatted,
        }

    except requests.exceptions.Timeout:
        return {"error": "請求超時，請稍後再試"}
    except requests.exceptions.RequestException as e:
        return {"error": f"網路請求失敗: {str(e)}"}
    except Exception as e:
        return {"error": f"查詢失敗: {str(e)}"}


# ============== 知識庫搜尋工具 ==============

KNOWLEDGE_SIMILARITY_THRESHOLD = 0.3

@mcp.tool()
def search_knowledge(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    搜尋知識庫，根據語意找出最相關的農業知識文件。

    當使用者詢問農業知識、種植技術、病蟲害防治、肥料使用等問題時，
    使用此工具從知識庫中搜尋相關資訊來輔助回答。

    參數：
    - query: 搜尋關鍵詞或問題描述
    - top_k: 返回最相關的文件數量，預設 5

    範例：
    - search_knowledge(query="番茄病蟲害防治")
    - search_knowledge(query="有機肥料施用方法", top_k=3)
    """
    if not query or not query.strip():
        return {"error": "請提供搜尋關鍵詞"}

    with get_db() as db:
        try:
            count = db.query(KnowledgeDocument).count()
            if count == 0:
                return {"message": "知識庫目前沒有資料", "results": []}

            query_embedding = get_embedding(query.strip())
            distance_col = KnowledgeDocument.embedding.cosine_distance(query_embedding)

            results = (
                db.query(KnowledgeDocument, distance_col.label("distance"))
                .order_by(distance_col)
                .limit(top_k)
                .all()
            )

            # 過濾掉相似度太低的結果（cosine distance > threshold 表示不夠相關）
            filtered = []
            for r in results:
                similarity = 1 - r.distance
                if similarity >= KNOWLEDGE_SIMILARITY_THRESHOLD:
                    filtered.append({
                        "title": r.KnowledgeDocument.title,
                        "content": r.KnowledgeDocument.content,
                        "source": r.KnowledgeDocument.source_filename,
                        "similarity": round(similarity, 4),
                    })

            if not filtered:
                return {"message": "知識庫中沒有找到足夠相關的資料", "query": query, "results": []}

            return {
                "query": query,
                "count": len(filtered),
                "results": filtered,
            }

        except Exception as e:
            return {"error": f"搜尋知識庫失敗: {str(e)}"}


# ============== 影像紀錄工具 ==============

@mcp.tool()
def query_image_records(
    farm_id: Optional[int] = None,
    farm_name: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    查詢影像紀錄列表（僅文字資訊，不含圖片）。

    用於了解系統中有哪些田間影像紀錄，找到感興趣的紀錄後，
    可使用 analyze_image_record 工具對特定紀錄的圖片進行視覺分析。

    參數：
    - farm_id: 按農場 ID 篩選（選填）
    - farm_name: 按農場名稱模糊搜尋（選填）
    - limit: 回傳筆數上限，預設 20，最大 100

    回傳：紀錄 ID、農場名稱、描述、圖片數量、建立時間
    """
    limit = min(limit, 100)

    with get_db() as db:
        try:
            query = db.query(ImageRecord).join(Farm, ImageRecord.farm_id == Farm.id)

            if farm_id:
                query = query.filter(ImageRecord.farm_id == farm_id)
            if farm_name:
                safe_name = farm_name.strip().replace("%", r"\%").replace("_", r"\_")
                query = query.filter(Farm.name.like(f"%{safe_name}%", escape="\\"))

            records = query.order_by(desc(ImageRecord.created_at)).limit(limit).all()

            if not records:
                return {"message": "沒有找到影像紀錄", "results": []}

            results = []
            for r in records:
                img_count = db.query(func.count(ImageRecordFile.id)).filter(
                    ImageRecordFile.record_id == r.id
                ).scalar()
                results.append({
                    "id": r.id,
                    "farm_name": r.farm.name if r.farm else None,
                    "description": r.description,
                    "image_count": img_count,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })

            return {"count": len(results), "results": results}

        except Exception as e:
            return {"error": f"查詢失敗: {str(e)}"}


@mcp.tool()
def get_latest_image_per_farm() -> Dict[str, Any]:
    """
    取得每個農場最新的一筆影像紀錄（僅文字資訊，不含圖片）。

    一次查出所有農場各自最新的影像紀錄，適合用於整體狀態總覽。
    如需分析特定紀錄的圖片，再使用 analyze_image_record 工具。

    回傳：每個農場最新紀錄的 ID、農場名稱、描述、圖片數量、建立時間
    """
    with get_db() as db:
        try:
            # 子查詢：每個農場最新的 image_record created_at
            latest_sub = (
                db.query(
                    ImageRecord.farm_id,
                    func.max(ImageRecord.created_at).label("max_created"),
                )
                .group_by(ImageRecord.farm_id)
                .subquery()
            )

            records = (
                db.query(ImageRecord)
                .join(
                    latest_sub,
                    and_(
                        ImageRecord.farm_id == latest_sub.c.farm_id,
                        ImageRecord.created_at == latest_sub.c.max_created,
                    ),
                )
                .all()
            )

            if not records:
                return {"message": "沒有任何影像紀錄", "results": []}

            results = []
            for r in records:
                img_count = db.query(func.count(ImageRecordFile.id)).filter(
                    ImageRecordFile.record_id == r.id
                ).scalar()
                results.append({
                    "id": r.id,
                    "farm_id": r.farm_id,
                    "farm_name": r.farm.name if r.farm else None,
                    "description": r.description,
                    "image_count": img_count,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })

            return {"count": len(results), "results": results}

        except Exception as e:
            return {"error": f"查詢失敗: {str(e)}"}


@mcp.tool()
def analyze_image_record(record_id: int) -> Dict[str, Any]:
    """
    對指定影像紀錄的圖片進行 AI 視覺分析。

    讀取該紀錄的所有圖片，使用 Claude Vision 進行分析，回傳分析結果文字。
    適合用於辨識作物、判斷病蟲害、評估生長狀況等。

    建議先用 query_image_records 找到紀錄 ID，再呼叫此工具。
    分析完成後，可搭配 search_knowledge 搜尋知識庫，提供更完整的建議。

    參數：
    - record_id: 影像紀錄 ID（必填）
    """
    with get_db() as db:
        try:
            record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
            if not record:
                return {"error": f"找不到 ID 為 {record_id} 的影像紀錄"}

            images = db.query(ImageRecordFile).filter(
                ImageRecordFile.record_id == record_id
            ).all()

            if not images:
                return {"error": "該紀錄沒有圖片"}

            farm_name = record.farm.name if record.farm else "未知農場"

            # 讀取圖片轉 base64
            image_contents = []
            record_dir = os.path.join(settings.UPLOAD_DIR, "image-records", str(record_id))
            for img in images:
                file_path = os.path.join(record_dir, img.filename)
                if not os.path.isfile(file_path):
                    continue
                with open(file_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode("utf-8")
                ext = os.path.splitext(img.filename)[1].lower()
                media_type = mimetypes.types_map.get(ext, "image/jpeg")
                image_contents.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data,
                    },
                })

            if not image_contents:
                return {"error": "圖片檔案不存在"}

            # 組 prompt
            prompt = "請分析這些農業田間照片，提供以下資訊：\n"
            prompt += "1. 作物辨識與生長階段\n"
            prompt += "2. 健康狀況評估（是否有病蟲害跡象）\n"
            prompt += "3. 土壤與環境觀察\n"
            prompt += "4. 建議的管理措施\n\n"
            prompt += "請以繁體中文回答，簡潔實用。"

            if record.description:
                prompt = f"使用者描述：{record.description}\n\n{prompt}"
            prompt = f"農場：{farm_name}\n{prompt}"

            # 呼叫 Claude Vision
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            content = image_contents + [{"type": "text", "text": prompt}]

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                messages=[{"role": "user", "content": content}],
            )

            analysis_text = response.content[0].text if response.content else "分析失敗"

            return {
                "record_id": record_id,
                "farm_name": farm_name,
                "description": record.description,
                "image_count": len(image_contents),
                "analysis": analysis_text,
            }

        except Exception as e:
            return {"error": f"分析失敗: {str(e)}"}


if __name__ == "__main__":
    mcp.run()

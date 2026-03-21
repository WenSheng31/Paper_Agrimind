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


# 縣市對應氣象站（即時觀測用）
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

# 縣市對應鄉鎮預報資料集代碼（一週逐12小時）
COUNTY_FORECAST_DATASET = {
    "宜蘭縣": "F-D0047-003", "桃園市": "F-D0047-007",
    "新竹縣": "F-D0047-011", "苗栗縣": "F-D0047-015",
    "彰化縣": "F-D0047-019", "南投縣": "F-D0047-023",
    "雲林縣": "F-D0047-027", "嘉義縣": "F-D0047-031",
    "屏東縣": "F-D0047-035", "臺東縣": "F-D0047-039",
    "花蓮縣": "F-D0047-043", "澎湖縣": "F-D0047-047",
    "基隆市": "F-D0047-051", "新竹市": "F-D0047-055",
    "嘉義市": "F-D0047-059", "臺北市": "F-D0047-063",
    "高雄市": "F-D0047-067", "新北市": "F-D0047-071",
    "臺中市": "F-D0047-075", "臺南市": "F-D0047-079",
    "連江縣": "F-D0047-083", "金門縣": "F-D0047-087",
}

# 全台鄉鎮→所屬縣市映射（靜態，來源：氣象署鄉鎮預報資料集）
TOWNSHIP_TO_COUNTY = {
    "中寮鄉": "南投縣", "仁愛鄉": "南投縣", "信義鄉": "南投縣", "南投市": "南投縣", "名間鄉": "南投縣", "國姓鄉": "南投縣", "埔里鎮": "南投縣", "水里鄉": "南投縣", "竹山鎮": "南投縣", "草屯鎮": "南投縣", "集集鎮": "南投縣", "魚池鄉": "南投縣", "鹿谷鄉": "南投縣",
    "中埔鄉": "嘉義縣", "六腳鄉": "嘉義縣", "大埔鄉": "嘉義縣", "大林鎮": "嘉義縣", "太保市": "嘉義縣", "布袋鎮": "嘉義縣", "新港鄉": "嘉義縣", "朴子市": "嘉義縣", "東石鄉": "嘉義縣", "梅山鄉": "嘉義縣", "民雄鄉": "嘉義縣", "水上鄉": "嘉義縣", "溪口鄉": "嘉義縣", "番路鄉": "嘉義縣", "竹崎鄉": "嘉義縣", "義竹鄉": "嘉義縣", "阿里山鄉": "嘉義縣", "鹿草鄉": "嘉義縣",
    "七堵區": "基隆市", "仁愛區": "基隆市", "安樂區": "基隆市", "暖暖區": "基隆市", "中山區": "基隆市", "中正區": "基隆市", "信義區": "基隆市",
    "三星鄉": "宜蘭縣", "五結鄉": "宜蘭縣", "冬山鄉": "宜蘭縣", "南澳鄉": "宜蘭縣", "員山鄉": "宜蘭縣", "壯圍鄉": "宜蘭縣", "大同鄉": "宜蘭縣", "宜蘭市": "宜蘭縣", "礁溪鄉": "宜蘭縣", "羅東鎮": "宜蘭縣", "蘇澳鎮": "宜蘭縣", "頭城鎮": "宜蘭縣",
    "三地門鄉": "屏東縣", "九如鄉": "屏東縣", "佳冬鄉": "屏東縣", "來義鄉": "屏東縣", "內埔鄉": "屏東縣", "南州鄉": "屏東縣", "屏東市": "屏東縣", "崁頂鄉": "屏東縣", "恆春鎮": "屏東縣", "新園鄉": "屏東縣", "新埤鄉": "屏東縣", "春日鄉": "屏東縣", "東港鎮": "屏東縣", "枋寮鄉": "屏東縣", "枋山鄉": "屏東縣", "林邊鄉": "屏東縣", "泰武鄉": "屏東縣", "滿州鄉": "屏東縣", "潮州鎮": "屏東縣", "牡丹鄉": "屏東縣", "獅子鄉": "屏東縣", "琉球鄉": "屏東縣", "瑪家鄉": "屏東縣", "竹田鄉": "屏東縣", "萬丹鄉": "屏東縣", "萬巒鄉": "屏東縣", "車城鄉": "屏東縣", "里港鄉": "屏東縣", "長治鄉": "屏東縣", "霧臺鄉": "屏東縣", "高樹鄉": "屏東縣", "鹽埔鄉": "屏東縣", "麟洛鄉": "屏東縣",
    "二林鎮": "彰化縣", "二水鄉": "彰化縣", "伸港鄉": "彰化縣", "北斗鎮": "彰化縣", "和美鎮": "彰化縣", "員林市": "彰化縣", "埔心鄉": "彰化縣", "埔鹽鄉": "彰化縣", "埤頭鄉": "彰化縣", "大城鄉": "彰化縣", "大村鄉": "彰化縣", "彰化市": "彰化縣", "永靖鄉": "彰化縣", "溪州鄉": "彰化縣", "溪湖鎮": "彰化縣", "田中鎮": "彰化縣", "田尾鄉": "彰化縣", "社頭鄉": "彰化縣", "福興鄉": "彰化縣", "秀水鄉": "彰化縣", "竹塘鄉": "彰化縣", "線西鄉": "彰化縣", "芬園鄉": "彰化縣", "花壇鄉": "彰化縣", "芳苑鄉": "彰化縣", "鹿港鎮": "彰化縣",
    "三峽區": "新北市", "三芝區": "新北市", "三重區": "新北市", "中和區": "新北市", "五股區": "新北市", "八里區": "新北市", "土城區": "新北市", "坪林區": "新北市", "平溪區": "新北市", "新店區": "新北市", "新莊區": "新北市", "板橋區": "新北市", "林口區": "新北市", "樹林區": "新北市", "永和區": "新北市", "汐止區": "新北市", "泰山區": "新北市", "淡水區": "新北市", "深坑區": "新北市", "烏來區": "新北市", "瑞芳區": "新北市", "石碇區": "新北市", "石門區": "新北市", "萬里區": "新北市", "蘆洲區": "新北市", "貢寮區": "新北市", "金山區": "新北市", "雙溪區": "新北市", "鶯歌區": "新北市",
    "香山區": "新竹市", "東區": "新竹市", "北區": "新竹市",
    "五峰鄉": "新竹縣", "北埔鄉": "新竹縣", "寶山鄉": "新竹縣", "尖石鄉": "新竹縣", "峨眉鄉": "新竹縣", "新埔鎮": "新竹縣", "新豐鄉": "新竹縣", "橫山鄉": "新竹縣", "湖口鄉": "新竹縣", "竹北市": "新竹縣", "竹東鎮": "新竹縣", "芎林鄉": "新竹縣", "關西鎮": "新竹縣",
    "中壢區": "桃園市", "八德區": "桃園市", "大園區": "桃園市", "大溪區": "桃園市", "平鎮區": "桃園市", "復興區": "桃園市", "新屋區": "桃園市", "桃園區": "桃園市", "楊梅區": "桃園市", "蘆竹區": "桃園市", "觀音區": "桃園市", "龍潭區": "桃園市", "龜山區": "桃園市",
    "七美鄉": "澎湖縣", "望安鄉": "澎湖縣", "湖西鄉": "澎湖縣", "白沙鄉": "澎湖縣", "西嶼鄉": "澎湖縣", "馬公市": "澎湖縣",
    "中區": "臺中市", "北屯區": "臺中市", "南屯區": "臺中市", "后里區": "臺中市", "和平區": "臺中市", "外埔區": "臺中市", "大安區": "臺中市", "大甲區": "臺中市", "大肚區": "臺中市", "大里區": "臺中市", "大雅區": "臺中市", "太平區": "臺中市", "新社區": "臺中市", "東勢區": "臺中市", "梧棲區": "臺中市", "沙鹿區": "臺中市", "清水區": "臺中市", "潭子區": "臺中市", "烏日區": "臺中市", "石岡區": "臺中市", "神岡區": "臺中市", "西區": "臺中市", "西屯區": "臺中市", "豐原區": "臺中市", "霧峰區": "臺中市", "龍井區": "臺中市",
    "內湖區": "臺北市", "北投區": "臺北市", "南港區": "臺北市", "士林區": "臺北市", "大同區": "臺北市", "文山區": "臺北市", "松山區": "臺北市", "萬華區": "臺北市", "大安區": "臺北市",
    "七股區": "臺南市", "下營區": "臺南市", "中西區": "臺南市", "仁德區": "臺南市", "佳里區": "臺南市", "六甲區": "臺南市", "北門區": "臺南市", "南化區": "臺南市", "善化區": "臺南市", "大內區": "臺南市", "學甲區": "臺南市", "安南區": "臺南市", "安定區": "臺南市", "安平區": "臺南市", "官田區": "臺南市", "將軍區": "臺南市", "山上區": "臺南市", "左鎮區": "臺南市", "後壁區": "臺南市", "新化區": "臺南市", "新市區": "臺南市", "新營區": "臺南市", "東山區": "臺南市", "柳營區": "臺南市", "楠西區": "臺南市", "歸仁區": "臺南市", "永康區": "臺南市", "玉井區": "臺南市", "白河區": "臺南市", "西港區": "臺南市", "關廟區": "臺南市", "鹽水區": "臺南市", "麻豆區": "臺南市", "龍崎區": "臺南市",
    "卑南鄉": "臺東縣", "大武鄉": "臺東縣", "太麻里鄉": "臺東縣", "延平鄉": "臺東縣", "成功鎮": "臺東縣", "東河鄉": "臺東縣", "池上鄉": "臺東縣", "海端鄉": "臺東縣", "綠島鄉": "臺東縣", "臺東市": "臺東縣", "蘭嶼鄉": "臺東縣", "達仁鄉": "臺東縣", "金峰鄉": "臺東縣", "長濱鄉": "臺東縣", "關山鎮": "臺東縣", "鹿野鄉": "臺東縣",
    "光復鄉": "花蓮縣", "卓溪鄉": "花蓮縣", "吉安鄉": "花蓮縣", "壽豐鄉": "花蓮縣", "富里鄉": "花蓮縣", "新城鄉": "花蓮縣", "玉里鎮": "花蓮縣", "瑞穗鄉": "花蓮縣", "秀林鄉": "花蓮縣", "花蓮市": "花蓮縣", "萬榮鄉": "花蓮縣", "豐濱鄉": "花蓮縣", "鳳林鎮": "花蓮縣",
    "三灣鄉": "苗栗縣", "三義鄉": "苗栗縣", "公館鄉": "苗栗縣", "卓蘭鎮": "苗栗縣", "南庄鄉": "苗栗縣", "大湖鄉": "苗栗縣", "後龍鎮": "苗栗縣", "泰安鄉": "苗栗縣", "獅潭鄉": "苗栗縣", "竹南鎮": "苗栗縣", "苑裡鎮": "苗栗縣", "苗栗市": "苗栗縣", "西湖鄉": "苗栗縣", "通霄鎮": "苗栗縣", "造橋鄉": "苗栗縣", "銅鑼鄉": "苗栗縣", "頭份市": "苗栗縣", "頭屋鄉": "苗栗縣",
    "北竿鄉": "連江縣", "南竿鄉": "連江縣", "東引鄉": "連江縣", "莒光鄉": "連江縣",
    "烈嶼鄉": "金門縣", "烏坵鄉": "金門縣", "金城鎮": "金門縣", "金寧鄉": "金門縣", "金沙鎮": "金門縣", "金湖鎮": "金門縣",
    "二崙鄉": "雲林縣", "元長鄉": "雲林縣", "北港鎮": "雲林縣", "口湖鄉": "雲林縣", "古坑鄉": "雲林縣", "四湖鄉": "雲林縣", "土庫鎮": "雲林縣", "大埤鄉": "雲林縣", "崙背鄉": "雲林縣", "斗六市": "雲林縣", "斗南鎮": "雲林縣", "東勢鄉": "雲林縣", "林內鄉": "雲林縣", "水林鄉": "雲林縣", "臺西鄉": "雲林縣", "莿桐鄉": "雲林縣", "虎尾鎮": "雲林縣", "褒忠鄉": "雲林縣", "西螺鎮": "雲林縣", "麥寮鄉": "雲林縣",
    "三民區": "高雄市", "仁武區": "高雄市", "內門區": "高雄市", "六龜區": "高雄市", "前金區": "高雄市", "前鎮區": "高雄市", "大寮區": "高雄市", "大樹區": "高雄市", "大社區": "高雄市", "小港區": "高雄市", "岡山區": "高雄市", "左營區": "高雄市", "彌陀區": "高雄市", "新興區": "高雄市", "旗山區": "高雄市", "旗津區": "高雄市", "杉林區": "高雄市", "林園區": "高雄市", "桃源區": "高雄市", "梓官區": "高雄市", "楠梓區": "高雄市", "橋頭區": "高雄市", "永安區": "高雄市", "湖內區": "高雄市", "燕巢區": "高雄市", "田寮區": "高雄市", "甲仙區": "高雄市", "美濃區": "高雄市", "苓雅區": "高雄市", "茂林區": "高雄市", "茄萣區": "高雄市", "路竹區": "高雄市", "那瑪夏區": "高雄市", "阿蓮區": "高雄市", "鳥松區": "高雄市", "鳳山區": "高雄市", "鹽埕區": "高雄市", "鼓山區": "高雄市",
}


# ============== 氣象工具 ==============


def _find_nearest_station(location: str) -> tuple:
    """根據地點名稱找到最近的氣象站。回傳 (station_name, source_note)"""
    # 1. 直接匹配氣象站
    if location in WEATHER_STATIONS:
        return WEATHER_STATIONS[location], None

    # 2. 嘗試模糊匹配（鄉鎮名去掉行政區後綴匹配縣市）
    for suffix in ["區", "鎮", "鄉", "市"]:
        if location.endswith(suffix):
            short = location[:-1]
            for county, station in WEATHER_STATIONS.items():
                if short in county:
                    return station, f"（數據來自{county}{station}氣象站）"

    # 3. 包含匹配
    for county, station in WEATHER_STATIONS.items():
        if location in county or county in location:
            return station, f"（數據來自{county}{station}氣象站）"

    return location, None


def _fetch_current_weather(api_key: str, location: str) -> Dict[str, Any]:
    """查詢即時觀測資料（O-A0001-001）"""
    station_name, source_note = _find_nearest_station(location)

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"
    params = {"Authorization": api_key, "format": "JSON", "StationName": station_name}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("success") != "true":
        return {"error": "即時觀測 API 請求失敗"}

    records = data.get("records", {})
    stations = records.get("Station", []) if isinstance(records, dict) else []

    if not stations:
        # 找不到精確站名，嘗試搜尋所有站，用模糊匹配
        params_all = {"Authorization": api_key, "format": "JSON"}
        resp_all = requests.get(url, params=params_all, timeout=10)
        resp_all.raise_for_status()
        all_data = resp_all.json()
        all_stations = all_data.get("records", {}).get("Station", [])
        for s in all_stations:
            if location in (s.get("StationName", "") + s.get("GeoInfo", {}).get("CountyName", "") + s.get("GeoInfo", {}).get("TownName", "")):
                stations = [s]
                source_note = f"（數據來自{s.get('StationName')}氣象站）"
                break
        if not stations:
            return {"error": f"找不到「{location}」附近的氣象站"}

    station = stations[0]
    obs = station.get("WeatherElement", {}) or {}
    geo = station.get("GeoInfo", {}) or {}
    obs_time = station.get("ObsTime", {}) or {}
    now_data = obs.get("Now", {}) or {}

    result = {
        "氣象站": station.get("StationName"),
        "縣市": geo.get("CountyName"),
        "鄉鎮": geo.get("TownName"),
        "觀測時間": obs_time.get("DateTime") if isinstance(obs_time, dict) else None,
        "天氣": obs.get("Weather"),
        "溫度": obs.get("AirTemperature"),
        "濕度": obs.get("RelativeHumidity"),
        "氣壓": obs.get("AirPressure"),
        "風速": obs.get("WindSpeed"),
        "風向": obs.get("WindDirection"),
        "降雨量": now_data.get("Precipitation") if isinstance(now_data, dict) else None,
    }
    if source_note:
        result["備註"] = source_note
    return result


def _fetch_forecast(api_key: str, location: str) -> Dict[str, Any]:
    """查詢鄉鎮級天氣預報"""
    base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
    location_data = None
    matched_county = None

    # 1. 如果是縣市名，用縣市級預報
    if location in COUNTY_FORECAST_DATASET:
        url = f"{base_url}/F-D0047-091"
        params = {"Authorization": api_key, "format": "JSON", "locationName": location}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") == "true":
            for g in data.get("records", {}).get("Locations", []):
                for loc in g.get("Location", []):
                    if loc.get("LocationName") == location:
                        location_data = loc
                        break
                if location_data:
                    break

    # 2. 鄉鎮名，用靜態映射直接定位縣市，一次 API 呼叫
    if not location_data:
        county = TOWNSHIP_TO_COUNTY.get(location)
        if county:
            dataset_id = COUNTY_FORECAST_DATASET[county]
            url = f"{base_url}/{dataset_id}"
            params = {"Authorization": api_key, "format": "JSON", "locationName": location}
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") == "true":
                for g in data.get("records", {}).get("Locations", []):
                    for loc in g.get("Location", []):
                        if loc.get("LocationName") == location:
                            location_data = loc
                            matched_county = county
                            break
                    if location_data:
                        break

    if not location_data:
        return {"error": f"找不到「{location}」的預報資料，請輸入縣市名（如臺中市）或鄉鎮名（如霧峰區）"}

    # 解析天氣要素
    elements = {}
    for elem in location_data.get("WeatherElement", []):
        elements[elem["ElementName"]] = elem.get("Time", [])

    weather_times = elements.get("天氣現象", [])
    forecasts = []
    for i, t in enumerate(weather_times[:14]):  # 最多取 7 天（14 個 12 小時時段）
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

    result = {"地點": location, "預報": forecasts}
    if matched_county:
        result["所屬縣市"] = matched_county
    return result


# 縣市對應農業氣象分區
COUNTY_TO_AGR_REGION = {
    "基隆市": "北部地區", "臺北市": "北部地區", "新北市": "北部地區",
    "桃園市": "北部地區", "新竹市": "北部地區", "新竹縣": "北部地區",
    "宜蘭縣": "東北部地區",
    "苗栗縣": "中部地區", "臺中市": "中部地區", "彰化縣": "中部地區",
    "南投縣": "中部地區", "雲林縣": "中部地區",
    "嘉義市": "南部地區", "嘉義縣": "南部地區", "臺南市": "南部地區",
    "高雄市": "南部地區", "屏東縣": "南部地區",
    "花蓮縣": "東部地區", "臺東縣": "東南部地區",
    "澎湖縣": "南部地區", "金門縣": "南部地區", "連江縣": "北部地區",
}


def _fetch_agri_weather(api_key: str, location: str) -> Dict[str, Any]:
    """查詢農業氣象預報（F-A0010-001）"""
    url = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001"
    params = {"Authorization": api_key, "format": "JSON"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    agr = data.get("cwaopendata", {}).get("resources", {}).get("resource", {}).get("data", {}).get("agrWeatherForecasts", {})
    if not agr:
        return {"error": "無法取得農業氣象資料"}

    # 找出對應分區
    county = TOWNSHIP_TO_COUNTY.get(location, location)
    target_region = COUNTY_TO_AGR_REGION.get(county)
    if not target_region and "地區" in location:
        target_region = location

    result = {"天氣概況": agr.get("weatherProfile", "")}

    # 地區預報
    for loc in agr.get("weatherForecasts", {}).get("location", []):
        name = loc.get("locationName", "")
        if target_region and name != target_region:
            continue
        elements = loc.get("weatherElements", {})
        wx_daily = elements.get("Wx", {}).get("daily", [])
        max_t = elements.get("MaxT", {}).get("daily", [])
        min_t = elements.get("MinT", {}).get("daily", [])
        days = []
        for i, wx in enumerate(wx_daily):
            day = {"日期": wx.get("dataDate", ""), "天氣": wx.get("weather", "")}
            if i < len(max_t):
                day["最高溫"] = max_t[i].get("temperature", "")
            if i < len(min_t):
                day["最低溫"] = min_t[i].get("temperature", "")
            days.append(day)
        result["農業氣象預報"] = {"地區": name, "預報": days}
        break

    # 積溫資料
    for loc in agr.get("agrAdvices", {}).get("agrForecasts", {}).get("location", []):
        name = loc.get("locationName", "")
        if target_region and name != target_region:
            continue
        daily = loc.get("weatherElements", {}).get("daily", [])
        days = [{"日期": d.get("dataDate", ""), "度日": d.get("degreeDay", ""), "累積積溫": d.get("accumulatedTemperature", "")} for d in daily]
        result["積溫資料"] = {"地區": name, "積溫": days}
        break

    return result


@mcp.tool()
def get_weather(location: str, query_type: str = "current") -> Dict[str, Any]:
    """
    查詢指定地點的天氣資訊（資料來源：中央氣象署）。

    支援縣市（如「臺中市」）、鄉鎮（如「霧峰區」「魚池鄉」）、氣象站名（如「日月潭」）。
    若查詢景點或地址，請先轉換為所在的鄉鎮名稱再呼叫此工具。

    重要：請根據使用者的問題選擇最節省的 query_type，不要每次都用 "all"。
    - 使用者問「現在天氣」「目前溫度」→ 用 "current"
    - 使用者問「明天天氣」「這週會下雨嗎」「未來天氣」→ 用 "forecast"
    - 使用者問「農業氣象」「積溫」「農事規劃」→ 用 "agri"
    - 使用者問「完整天氣」或需要綜合分析時 → 才用 "all"

    參數：
    - location: 地點名稱（必填），如「臺中市」「霧峰區」「竹東鎮」「高雄」
    - query_type: 查詢類型，可選值：
      - "current"（預設）：僅回傳即時觀測（溫度、濕度、氣壓、風速、降雨量）
      - "forecast"：僅回傳未來一週逐 12 小時鄉鎮預報
      - "agri"：僅回傳農業氣象預報（天氣概況、分區預報、積溫資料）
      - "all"：同時回傳以上三者（資料量大，僅在需要綜合分析時使用）
    """
    if not location or not location.strip():
        return {"error": "請提供地點名稱，例如：臺中市、霧峰區、竹東鎮"}

    api_key = settings.CWA_API_KEY
    if not api_key:
        return {"error": "未設定中央氣象署 API Key"}

    location = _normalize_location(location)
    query_type = (query_type or "all").strip().lower()

    result = {"location": location}

    try:
        if query_type in ("all", "current"):
            result["即時觀測"] = _fetch_current_weather(api_key, location)

        if query_type in ("all", "forecast"):
            result["天氣預報"] = _fetch_forecast(api_key, location)

        if query_type in ("all", "agri"):
            result["農業氣象"] = _fetch_agri_weather(api_key, location)

        return result

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

            resp = requests.get(url, params=fuzzy_params, timeout=10)
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

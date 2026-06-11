import re
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List

import pandas as pd


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _format_timestamp(value) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")


def to_serializable_records(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    export_frame = frame.copy()
    if "timestamp" in export_frame.columns:
        export_frame["timestamp"] = export_frame["timestamp"].apply(_format_timestamp)

    export_frame = export_frame.where(pd.notnull(export_frame), None)
    return export_frame.to_dict(orient="records")


_EQUIPMENT_TYPE_LABELS = {
    "AHU": "空气处理机组",
    "CH": "冷水机组",
    "CT": "冷却塔",
    "FCU": "风机盘管",
}


_PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}
_ELECTRICITY_PRICE_YUAN_PER_KWH = 0.82
_CARBON_KG_PER_KWH = 0.5703
_SAVING_CAPTURE_RATE = 0.65


def _equipment_code(equipment_id: str) -> str:
    return str(equipment_id or "").split("-")[0].upper()


def _equipment_sequence(equipment_id: str) -> int:
    match = re.search(r"(\d+)$", str(equipment_id or ""))
    return int(match.group(1)) if match else 1


def _record_sequence(row: pd.Series) -> int:
    match = re.search(r"(\d+)", str(row.get("record_id", "")))
    if match:
        return int(match.group(1))
    return _equipment_sequence(row.get("equipment_id"))


def _building_letter(row: pd.Series) -> str:
    building_id = str(row.get("building_id", "BLD-X"))
    return building_id.split("-")[-1][:1] or "X"


def _building_floor_count(building_name: str) -> int:
    if "教学" in building_name:
        return 5
    if "实验" in building_name:
        return 6
    if "图书" in building_name:
        return 5
    return 4


def _row_hour(row: pd.Series) -> int:
    try:
        return int(pd.Timestamp(row.get("timestamp")).hour)
    except (TypeError, ValueError):
        return 0


def _infer_operational_equipment_code(row: pd.Series) -> str:
    building_name = str(row.get("building_name", ""))
    sequence = _record_sequence(row)
    hour = _row_hour(row)

    if "教学" in building_name:
        catalog = ["AHU", "FCU", "FCU", "AHU", "CT"]
    elif "办公" in building_name:
        catalog = ["AHU", "FCU", "CH", "FCU"]
    elif "图书" in building_name:
        catalog = ["AHU", "CT", "FCU", "CH", "AHU"]
    elif "实验" in building_name:
        catalog = ["FCU", "AHU", "CH", "FCU", "CT", "FCU"]
    else:
        catalog = ["AHU", "FCU", "CH", "CT"]

    return catalog[(sequence + hour) % len(catalog)]


def _infer_equipment_type(equipment_id: str) -> str:
    return _EQUIPMENT_TYPE_LABELS.get(_equipment_code(equipment_id), "其他设备")


def _infer_floor(row: pd.Series) -> str:
    code = row.get("equipment_code") or _infer_operational_equipment_code(row)
    sequence = _record_sequence(row) + _row_hour(row)
    building_name = str(row.get("building_name", ""))

    if code == "CH":
        return "B1 机房"
    if code == "CT":
        return "RF 屋顶"

    floor_count = _building_floor_count(building_name)
    return f"{((sequence - 1) % floor_count) + 1}F"


def _infer_zone(row: pd.Series) -> str:
    code = row.get("equipment_code") or _infer_operational_equipment_code(row)
    sequence = _record_sequence(row) + _row_hour(row)
    building_name = str(row.get("building_name", ""))

    if code in {"CH", "CT"}:
        return "能源站/设备区"

    if "教学" in building_name:
        zones = ["教室区", "公共走廊", "教师办公区", "多媒体教室"]
    elif "办公" in building_name:
        zones = ["办公区", "会议区", "公共服务区", "档案与值班区"]
    elif "图书" in building_name:
        zones = ["阅览区", "书库区", "信息检索区", "IT机房"]
    elif "实验" in building_name:
        zones = ["实验区", "准备间", "仪器室", "研究办公区"]
    else:
        zones = ["公共区", "办公区", "设备区", "服务区"]

    return zones[(sequence - 1) % len(zones)]


def _infer_operational_equipment_id(row: pd.Series) -> str:
    code = row.get("equipment_code") or _infer_operational_equipment_code(row)
    floor_label = str(row.get("floor_label") or _infer_floor(row))
    floor_token = re.sub(r"[^A-Za-z0-9]", "", floor_label) or "F"
    sequence = ((_record_sequence(row) + _row_hour(row)) % 8) + 1
    return f"{code}-{_building_letter(row)}-{floor_token}-{sequence:02d}"


def _reason_for_row(row: pd.Series) -> str:
    if str(row["equipment_status"]).lower() != "normal":
        return "设备状态异常"
    if row.get("low_cop", False):
        return "COP低于告警阈值"
    if row.get("night_high_load", False):
        return "夜间负荷偏高"
    return "电耗高于同建筑基线"


def _as_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _triggered_rule_count(row: pd.Series) -> int:
    electricity = _as_float(row.get("electricity_kwh"))
    upper_bound = _as_float(row.get("upper_bound"))
    return sum(
        [
            str(row.get("equipment_status")).lower() != "normal",
            electricity > upper_bound,
            bool(row.get("low_cop", False)),
            bool(row.get("night_high_load", False)),
        ]
    )


def _verification_method(row: pd.Series) -> str:
    reason = row.get("anomaly_reason")
    if reason == "设备状态异常":
        return "设备状态恢复为 normal，并由现场人员复核控制信号与运行声音。"
    if reason == "COP低于告警阈值":
        return "处置后连续 2 个采样点 COP 回升至 2.40 以上，且空调电耗不再高于动态阈值。"
    if reason == "夜间负荷偏高":
        return "次日 00:00-06:00 或 22:00 后负荷回落至建筑基线 1.10 倍以内。"
    return "下一采样周期电耗回落至同建筑动态阈值以内，并记录现场复核结论。"


def _business_impact(row: pd.Series) -> Dict:
    electricity = _as_float(row.get("electricity_kwh"))
    hvac = _as_float(row.get("hvac_kwh"))
    building_mean = _as_float(row.get("building_mean"), electricity)
    upper_bound = _as_float(row.get("upper_bound"), building_mean)
    cop = _as_float(row.get("average_cop"), 3.0)
    status_abnormal = str(row.get("equipment_status")).lower() != "normal"
    low_cop = bool(row.get("low_cop", False))
    night_high_load = bool(row.get("night_high_load", False))

    threshold_delta = max(0.0, electricity - upper_bound)
    baseline_delta = max(0.0, electricity - building_mean)
    night_delta = max(0.0, electricity - building_mean * 1.1) if night_high_load else 0.0
    cop_delta = 0.0
    if low_cop:
        cop_delta = hvac * min(0.22, max(0.0, 2.6 - cop) * 0.12)
    status_delta = electricity * 0.05 if status_abnormal else 0.0
    wasted_kwh = max(threshold_delta, night_delta, cop_delta, status_delta, baseline_delta * 0.25)
    if _triggered_rule_count(row) and wasted_kwh <= 0:
        wasted_kwh = electricity * 0.03

    wasted_cost = wasted_kwh * _ELECTRICITY_PRICE_YUAN_PER_KWH
    carbon_kg = wasted_kwh * _CARBON_KG_PER_KWH
    estimated_saving = wasted_cost * _SAVING_CAPTURE_RATE
    rule_count = _triggered_rule_count(row)
    risk_score = min(
        100.0,
        30
        + rule_count * 13
        + min(22.0, wasted_cost * 0.35)
        + (12 if status_abnormal else 0)
        + (8 if low_cop else 0)
        + (6 if night_high_load else 0),
    )
    severity = "高" if risk_score >= 72 else "中" if risk_score >= 48 else "低"
    sla_hours = 8 if severity == "高" else 24 if severity == "中" else 72

    return {
        "risk_score": round(risk_score, 1),
        "severity": severity,
        "triggered_rule_count": rule_count,
        "wasted_kwh": round(wasted_kwh, 2),
        "wasted_cost_yuan": round(wasted_cost, 2),
        "carbon_kg": round(carbon_kg, 2),
        "estimated_saving_yuan": round(estimated_saving, 2),
        "sla_hours": sla_hours,
        "verification_method": _verification_method(row),
        "business_impact_summary": (
            f"本次异常估算浪费 {wasted_kwh:.1f} kWh，"
            f"约 {wasted_cost:.0f} 元，处置后可回收约 {estimated_saving:.0f} 元。"
        ),
    }


_ANALYSIS_REQUIRED_COLUMNS = {
    "source_equipment_id",
    "equipment_code",
    "equipment_type",
    "floor_label",
    "zone_name",
    "hour",
    "building_mean",
    "building_std",
    "upper_bound",
    "average_cop",
    "low_cop",
    "night_high_load",
    "is_anomaly",
    "anomaly_reason",
}


def _frame_signature(frame: pd.DataFrame):
    """Cheap, collision-resistant fingerprint of a raw input frame.

    Captures row count, the first/last record ids (window + building filter) and
    the content sums that simulation transforms change (electricity/hvac/cooling
    and abnormal-status count). Computing it costs a few vectorised reductions,
    far less than the row-wise ``apply`` annotation it guards.
    """
    n = len(frame)
    if n == 0:
        return ("empty",)
    record_ids = frame["record_id"]
    return (
        n,
        str(record_ids.iloc[0]),
        str(record_ids.iloc[-1]),
        round(float(frame["electricity_kwh"].sum()), 3),
        round(float(frame["hvac_kwh"].sum()), 3),
        round(float(frame["cooling_load_kwh"].sum()), 3),
        int((frame["equipment_status"].astype(str).str.lower() != "normal").sum()),
    )


_ANNOTATION_CACHE: "OrderedDict[tuple, pd.DataFrame]" = OrderedDict()
_ANNOTATION_CACHE_MAX = 24


def _add_operational_dimensions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    if _ANALYSIS_REQUIRED_COLUMNS.issubset(frame.columns):
        return frame.copy()

    # Annotating the operational dimensions (synthesised equipment ids, floors,
    # zones, anomaly flags) is the single hottest path and is recomputed by nearly
    # every endpoint. Memoise by input-content signature so a burst of requests on
    # the same (visible) frame only computes it once.
    cache_key = None
    try:
        cache_key = _frame_signature(frame)
    except (KeyError, TypeError, ValueError):
        cache_key = None
    if cache_key is not None:
        cached = _ANNOTATION_CACHE.get(cache_key)
        if cached is not None:
            _ANNOTATION_CACHE.move_to_end(cache_key)
            return cached.copy()

    working = frame.copy()
    working["source_equipment_id"] = working["equipment_id"]
    working["equipment_code"] = working.apply(_infer_operational_equipment_code, axis=1)
    working["equipment_type"] = working["equipment_id"].apply(_infer_equipment_type)
    working["floor_label"] = working.apply(_infer_floor, axis=1)
    working["zone_name"] = working.apply(_infer_zone, axis=1)
    working["equipment_id"] = working.apply(_infer_operational_equipment_id, axis=1)
    working["equipment_type"] = working["equipment_id"].apply(_infer_equipment_type)
    working["hour"] = pd.to_datetime(working["timestamp"]).dt.hour

    building_mean = working.groupby("building_id")["electricity_kwh"].transform("mean")
    building_std = working.groupby("building_id")["electricity_kwh"].transform("std")
    working["building_mean"] = building_mean
    working["building_std"] = building_std.fillna(0)
    working["upper_bound"] = working["building_mean"] + working["building_std"]

    working["average_cop"] = working.apply(
        lambda row: round(_safe_divide(row["cooling_load_kwh"], row["hvac_kwh"]), 2),
        axis=1,
    )
    working["low_cop"] = working["average_cop"] < 2.2
    working["night_high_load"] = (
        (working["hour"] < 6) | (working["hour"] >= 22)
    ) & (working["electricity_kwh"] > building_mean * 1.1)
    abnormal_status = working["equipment_status"].astype(str).str.lower() != "normal"
    abnormal_usage = working["electricity_kwh"] > working["upper_bound"]
    working["is_anomaly"] = (
        abnormal_status | abnormal_usage | working["low_cop"] | working["night_high_load"]
    )
    working["anomaly_reason"] = working.apply(_reason_for_row, axis=1)

    if cache_key is not None:
        _ANNOTATION_CACHE[cache_key] = working.copy()
        _ANNOTATION_CACHE.move_to_end(cache_key)
        while len(_ANNOTATION_CACHE) > _ANNOTATION_CACHE_MAX:
            _ANNOTATION_CACHE.popitem(last=False)

    return working


def _round_columns(frame: pd.DataFrame, columns: List[str], digits: int = 2) -> None:
    for column in columns:
        if column in frame.columns:
            frame[column] = frame[column].round(digits)


def _floor_sort_value(label: str) -> int:
    if str(label).startswith("B"):
        return 0
    if str(label).startswith("RF"):
        return 99

    match = re.match(r"(\d+)F", str(label))
    return int(match.group(1)) if match else 50


def normalize_floor_label(label: str) -> str:
    value = str(label or "")
    if "B1" in value:
        return "B1"
    if "RF" in value:
        return "RF"

    match = re.search(r"\d+F", value)
    return match.group(0) if match else value


def filter_display_frame_by_floor(frame: pd.DataFrame, floor_label: str) -> pd.DataFrame:
    if not floor_label or frame.empty or "floor_label" not in frame.columns:
        return frame

    normalized = normalize_floor_label(floor_label)
    floor_mask = frame["floor_label"].apply(normalize_floor_label) == normalized
    return frame[floor_mask]


def build_overview(frame: pd.DataFrame) -> Dict:
    if frame.empty:
        return {
            "total_records": 0,
            "building_count": 0,
            "average_cop": 0.0,
            "abnormal_record_count": 0,
            "time_range": {"start": None, "end": None},
            "totals": {},
        }

    total_hvac = float(frame["hvac_kwh"].sum())
    total_cooling = float(frame["cooling_load_kwh"].sum())
    abnormal_mask = frame["equipment_status"].astype(str).str.lower() != "normal"

    return {
        "total_records": int(len(frame)),
        "building_count": int(frame["building_id"].nunique()),
        "average_cop": round(_safe_divide(total_cooling, total_hvac), 2),
        "abnormal_record_count": int(abnormal_mask.sum()),
        "time_range": {
            "start": _format_timestamp(frame["timestamp"].min()),
            "end": _format_timestamp(frame["timestamp"].max()),
        },
        "totals": {
            "electricity_kwh": round(float(frame["electricity_kwh"].sum()), 2),
            "water_m3": round(float(frame["water_m3"].sum()), 2),
            "hvac_kwh": round(total_hvac, 2),
            "cooling_load_kwh": round(total_cooling, 2),
        },
    }


_DISPLAY_RECORD_COLUMNS = [
    "record_id",
    "building_id",
    "building_name",
    "building_type",
    "floor_label",
    "zone_name",
    "timestamp",
    "electricity_kwh",
    "water_m3",
    "hvac_kwh",
    "cooling_load_kwh",
    "chilled_water_supply_temp_c",
    "chilled_water_return_temp_c",
    "environment_temp_c",
    "humidity_rh",
    "occupancy_density_per_100m2",
    "equipment_id",
    "source_equipment_id",
    "equipment_type",
    "equipment_status",
]


def build_display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=_DISPLAY_RECORD_COLUMNS)

    working = _add_operational_dimensions(frame)
    return working[_DISPLAY_RECORD_COLUMNS]


def build_analysis_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return _add_operational_dimensions(frame)


def build_display_records(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    return to_serializable_records(build_display_frame(frame))


_FREQ_MAP = {"H": "h", "D": "D", "W": "W", "M": "ME"}


def build_time_summary(frame: pd.DataFrame, freq: str = "D") -> List[Dict]:
    if frame.empty:
        return []

    pandas_freq = _FREQ_MAP.get(freq, freq)
    working = frame.copy().set_index("timestamp")
    summary = working.resample(pandas_freq).agg(
        {
            "electricity_kwh": "sum",
            "water_m3": "sum",
            "hvac_kwh": "sum",
            "cooling_load_kwh": "sum",
        }
    )
    summary["average_cop"] = summary.apply(
        lambda row: round(_safe_divide(row["cooling_load_kwh"], row["hvac_kwh"]), 2),
        axis=1,
    )
    summary = summary.reset_index()
    return to_serializable_records(summary)


def build_building_comparison(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    grouped = (
        frame.groupby(["building_id", "building_name", "building_type"], as_index=False)
        .agg(
            {
                "electricity_kwh": "sum",
                "water_m3": "sum",
                "hvac_kwh": "sum",
                "cooling_load_kwh": "sum",
            }
        )
        .sort_values("electricity_kwh", ascending=False)
    )
    grouped["average_cop"] = grouped.apply(
        lambda row: round(_safe_divide(row["cooling_load_kwh"], row["hvac_kwh"]), 2),
        axis=1,
    )
    return to_serializable_records(grouped)


def build_cop_ranking(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    ranking = (
        frame.groupby(["building_id", "building_name"], as_index=False)
        .agg({"hvac_kwh": "sum", "cooling_load_kwh": "sum"})
        .sort_values("building_name")
    )
    ranking["average_cop"] = ranking.apply(
        lambda row: round(_safe_divide(row["cooling_load_kwh"], row["hvac_kwh"]), 2),
        axis=1,
    )
    ranking = ranking.sort_values("average_cop", ascending=False).reset_index(drop=True)
    return to_serializable_records(ranking)


def build_anomaly_reason_counts(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    anomaly_frame = working[working["is_anomaly"]].copy()
    if anomaly_frame.empty:
        return []

    grouped = (
        anomaly_frame.groupby("anomaly_reason", as_index=False)
        .agg(count=("record_id", "count"))
        .sort_values("count", ascending=False)
    )
    return grouped.to_dict(orient="records")


def build_anomaly_summary(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    anomalies = working[working["is_anomaly"]].copy()

    if anomalies.empty:
        return []

    export_columns = [
        "record_id",
        "building_id",
        "building_name",
        "timestamp",
        "electricity_kwh",
        "hvac_kwh",
        "average_cop",
        "equipment_id",
        "equipment_type",
        "floor_label",
        "zone_name",
        "equipment_status",
        "anomaly_reason",
    ]
    records = to_serializable_records(
        anomalies.sort_values("timestamp", ascending=False)[export_columns]
    )
    impacts = {
        str(row["record_id"]): _business_impact(row)
        for _, row in anomalies.iterrows()
    }
    for record in records:
        record.update(impacts.get(str(record.get("record_id")), {}))
    return records


def build_anomaly_explanation(frame: pd.DataFrame, record_id: str) -> Dict:
    if frame.empty:
        return {}

    working = _add_operational_dimensions(frame)
    target = working[working["record_id"] == record_id]
    if target.empty:
        return {}

    row = target.iloc[0]
    floor_frame = working[
        (working["building_id"] == row["building_id"])
        & (working["floor_label"].apply(normalize_floor_label) == normalize_floor_label(row["floor_label"]))
    ]
    floor_mean = float(floor_frame["electricity_kwh"].mean()) if not floor_frame.empty else 0.0
    floor_anomaly_count = int(floor_frame["is_anomaly"].sum()) if not floor_frame.empty else 0
    electricity = float(row["electricity_kwh"])
    building_mean = float(row["building_mean"])
    upper_bound = float(row["upper_bound"])
    cop = float(row["average_cop"])
    status_abnormal = str(row["equipment_status"]).lower() != "normal"
    high_usage = electricity > upper_bound
    low_cop = bool(row["low_cop"])
    night_high_load = bool(row["night_high_load"])
    triggered_rules = [
        item
        for item in [
            {
                "name": "设备状态异常",
                "triggered": status_abnormal,
                "detail": f"equipment_status={row['equipment_status']}",
            },
            {
                "name": "高于建筑动态阈值",
                "triggered": high_usage,
                "detail": f"{electricity:.2f} kWh > {upper_bound:.2f} kWh",
            },
            {
                "name": "COP 低于阈值",
                "triggered": low_cop,
                "detail": f"COP={cop:.2f}，阈值=2.20",
            },
            {
                "name": "夜间负荷偏高",
                "triggered": night_high_load,
                "detail": "00:00-06:00 或 22:00 后负荷高于建筑基线 1.1 倍",
            },
        ]
        if item["triggered"]
    ]
    if not triggered_rules:
        triggered_rules.append(
            {
                "name": "正常运行",
                "triggered": False,
                "detail": "当前记录未触发异常规则，可作为正常样本对照。",
            }
        )

    delta_pct = _safe_divide(electricity - building_mean, building_mean) * 100
    impact = _business_impact(row)
    severity = impact["severity"]
    conclusion = (
        f"{row['building_name']} {row['floor_label']} {row['zone_name']} 在 { _format_timestamp(row['timestamp']) } "
        f"触发“{row['anomaly_reason']}”。当前电耗 {electricity:.2f} kWh，"
        f"比同建筑均值高 {delta_pct:.1f}%，平均 COP 为 {cop:.2f}。"
        f"估算影响约 {impact['wasted_cost_yuan']:.0f} 元，风险分 {impact['risk_score']}。"
    )

    return {
        "record_id": row["record_id"],
        "building_id": row["building_id"],
        "building_name": row["building_name"],
        "floor_label": row["floor_label"],
        "zone_name": row["zone_name"],
        "equipment_id": row["equipment_id"],
        "equipment_type": row["equipment_type"],
        "timestamp": _format_timestamp(row["timestamp"]),
        "severity": severity,
        "anomaly_reason": row["anomaly_reason"],
        "conclusion": conclusion,
        "metrics": {
            "electricity_kwh": round(electricity, 2),
            "building_average_kwh": round(building_mean, 2),
            "floor_average_kwh": round(floor_mean, 2),
            "dynamic_threshold_kwh": round(upper_bound, 2),
            "average_cop": round(cop, 2),
            "floor_anomaly_count": floor_anomaly_count,
            "risk_score": impact["risk_score"],
            "wasted_kwh": impact["wasted_kwh"],
            "wasted_cost_yuan": impact["wasted_cost_yuan"],
            "carbon_kg": impact["carbon_kg"],
            "estimated_saving_yuan": impact["estimated_saving_yuan"],
        },
        "triggered_rules": triggered_rules,
        "possible_cause": _work_order_cause(row),
        "recommended_action": _work_order_action(row),
        "business_impact": impact,
        "verification_method": impact["verification_method"],
    }


def build_floor_summary(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    grouped = (
        working.groupby(
            ["building_id", "building_name", "floor_label", "zone_name"], as_index=False
        )
        .agg(
            record_count=("record_id", "count"),
            equipment_count=("equipment_id", "nunique"),
            electricity_kwh=("electricity_kwh", "sum"),
            water_m3=("water_m3", "sum"),
            hvac_kwh=("hvac_kwh", "sum"),
            cooling_load_kwh=("cooling_load_kwh", "sum"),
            anomaly_count=("is_anomaly", "sum"),
        )
    )
    grouped["average_cop"] = grouped.apply(
        lambda row: _safe_divide(row["cooling_load_kwh"], row["hvac_kwh"]),
        axis=1,
    )
    grouped["anomaly_rate"] = grouped.apply(
        lambda row: _safe_divide(row["anomaly_count"], row["record_count"]),
        axis=1,
    )
    grouped["operation_focus"] = grouped.apply(
        lambda row: "优先排查"
        if row["anomaly_count"] >= 2 or row["average_cop"] < 2.4
        else "持续观察",
        axis=1,
    )
    grouped["floor_order"] = grouped["floor_label"].apply(_floor_sort_value)
    _round_columns(
        grouped,
        ["electricity_kwh", "water_m3", "hvac_kwh", "cooling_load_kwh", "average_cop"],
    )
    grouped["anomaly_rate"] = (grouped["anomaly_rate"] * 100).round(1)

    export_columns = [
        "building_id",
        "building_name",
        "floor_label",
        "zone_name",
        "record_count",
        "equipment_count",
        "electricity_kwh",
        "water_m3",
        "average_cop",
        "anomaly_count",
        "anomaly_rate",
        "operation_focus",
    ]
    return to_serializable_records(
        grouped.sort_values(["building_name", "floor_order", "zone_name"])[export_columns]
    )


_BUILDING_PROFILE = {
    "BLD-A": {"area": 15000, "owner": "教学楼楼宇管理员", "usage": "教学与公共活动"},
    "BLD-B": {"area": 8000, "owner": "行政办公楼管理员", "usage": "行政办公与会议"},
    "BLD-C": {"area": 12000, "owner": "图书信息中心管理员", "usage": "阅览、自习与信息服务"},
    "BLD-D": {"area": 10000, "owner": "科研实验楼安全员", "usage": "实验、科研与精密设备运行"},
}


def _floor_area(building_id: str, floor_label: str) -> int:
    profile = _BUILDING_PROFILE.get(building_id, {"area": 9000})
    if str(floor_label).startswith("B") or str(floor_label).startswith("RF"):
        return int(profile["area"] * 0.08)
    return int(profile["area"] / 6)


def _risk_level(anomaly_count: int, anomaly_rate: float, average_cop: float) -> str:
    if anomaly_count >= 20 or anomaly_rate >= 18 or average_cop < 2.35:
        return "高风险"
    if anomaly_count > 0 or anomaly_rate >= 5 or average_cop < 2.55:
        return "关注"
    return "健康"


def build_floor_registry(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    items: List[Dict] = []
    for (building_id, building_name, floor_label), group in working.groupby(
        ["building_id", "building_name", "floor_label"], sort=True
    ):
        record_count = int(len(group))
        anomaly_count = int(group["is_anomaly"].sum())
        anomaly_rate = _safe_divide(anomaly_count, record_count) * 100
        average_cop = _safe_divide(float(group["cooling_load_kwh"].sum()), float(group["hvac_kwh"].sum()))
        profile = _BUILDING_PROFILE.get(building_id, {})
        equipment_types = sorted(group["equipment_type"].dropna().unique().tolist())
        zones = sorted(group["zone_name"].dropna().unique().tolist())
        area = _floor_area(building_id, floor_label)
        health_score = max(
            0,
            min(100, round(100 - anomaly_rate * 1.6 - max(0, 2.6 - average_cop) * 18, 1)),
        )
        items.append(
            {
                "building_id": building_id,
                "building_name": building_name,
                "floor_label": floor_label,
                "floor_area_m2": area,
                "usage": profile.get("usage", "综合运行区域"),
                "owner": profile.get("owner", "楼宇管理员"),
                "zone_names": "、".join(zones),
                "main_equipment_types": "、".join(equipment_types),
                "record_count": record_count,
                "equipment_count": int(group["equipment_id"].nunique()),
                "electricity_kwh": round(float(group["electricity_kwh"].sum()), 2),
                "average_cop": round(average_cop, 2),
                "anomaly_count": anomaly_count,
                "anomaly_rate": round(anomaly_rate, 1),
                "risk_level": _risk_level(anomaly_count, anomaly_rate, average_cop),
                "health_score": health_score,
                "latest_seen_at": _format_timestamp(group["timestamp"].max()),
                "operation_policy": (
                    "立即复核异常设备并生成工单"
                    if anomaly_count
                    else "维持常规巡检，可作为健康楼层对照"
                ),
            }
        )

    return sorted(items, key=lambda item: (item["building_name"], _floor_sort_value(item["floor_label"])))


def build_operation_report(frame: pd.DataFrame, work_orders: List[Dict] | None = None) -> Dict:
    work_orders = work_orders or []
    overview = build_overview(frame)
    anomalies = build_anomaly_summary(frame)
    floors = build_floor_registry(frame)
    recommendations = build_optimization_recommendations(frame)
    time_summary = build_time_summary(frame, freq="D")
    latest_days = time_summary[-7:]
    forecast_base = (
        sum(float(item.get("electricity_kwh", 0)) for item in latest_days) / len(latest_days)
        if latest_days
        else 0
    )
    forecast_week_kwh = round(forecast_base * 7, 2)
    business_impact = {
        "anomaly_count": len(anomalies),
        "total_wasted_kwh": round(sum(float(item.get("wasted_kwh", 0)) for item in anomalies), 2),
        "total_wasted_cost_yuan": round(
            sum(float(item.get("wasted_cost_yuan", 0)) for item in anomalies),
            2,
        ),
        "total_carbon_kg": round(sum(float(item.get("carbon_kg", 0)) for item in anomalies), 2),
        "total_estimated_saving_yuan": round(
            sum(float(item.get("estimated_saving_yuan", 0)) for item in anomalies),
            2,
        ),
    }
    closed_statuses = {"已完成", "closed", "ignored", "已关闭", "已忽略"}
    open_orders = [item for item in work_orders if item.get("status") not in closed_statuses]
    pending_review = [item for item in work_orders if item.get("status") == "pending_review"]
    pending_verify_orders = [item for item in work_orders if item.get("status") == "待验证"]
    closed_orders = [item for item in work_orders if item.get("status") in {"closed", "已关闭", "已完成"}]
    high_risk_open_orders = [
        item
        for item in open_orders
        if item.get("priority") == "高" or float(item.get("risk_score") or 0) >= 72
    ]
    status_counts: Dict[str, int] = {}
    for item in work_orders:
        status = item.get("status") or "待分派"
        status_counts[status] = status_counts.get(status, 0) + 1
    top_floor = next((item for item in floors if item.get("anomaly_count", 0) > 0), floors[0] if floors else None)
    top_recommendation = recommendations[0] if recommendations else None
    top_anomaly = anomalies[0] if anomalies else None

    # ---- closed case summaries ----
    closed_cases: List[Dict] = []
    for order in closed_orders[:8]:
        before_kwh = order.get("before_kwh")
        after_kwh = order.get("after_kwh")
        before_cop = order.get("before_cop")
        after_cop = order.get("after_cop")
        estimated = bool(order.get("after_is_estimated"))
        prefix = "预计" if estimated else ""
        saving_pct = ""
        if before_kwh and after_kwh and before_kwh > 0:
            saving_pct = f"{prefix}电耗下降 {round((before_kwh - after_kwh) / before_kwh * 100, 1)}%"
        cop_change = ""
        if before_cop and after_cop:
            cop_change = f"{prefix}COP {round(before_cop, 2)} → {round(after_cop, 2)}"

        closed_cases.append({
            "work_order_id": order.get("work_order_id", ""),
            "building_name": order.get("building_name", ""),
            "floor_label": order.get("floor_label", ""),
            "equipment_id": order.get("equipment_id", ""),
            "actual_cause": order.get("actual_cause", ""),
            "resolution_note": order.get("resolution_note", ""),
            "closed_at": order.get("closed_at", ""),
            "saving_summary": saving_pct,
            "cop_summary": cop_change,
            "after_is_estimated": estimated,
        })

    risk_text = (
        f"当前最需要关注 {top_floor['building_name']} {top_floor['floor_label']}，"
        f"异常 {top_floor['anomaly_count']} 条，风险等级为 {top_floor['risk_level']}。"
        if top_floor
        else "当前范围没有可识别的楼层风险。"
    )
    anomaly_text = (
        f"最近异常发生在 {top_anomaly['timestamp']}，位置为 {top_anomaly['building_name']} "
        f"{top_anomaly['floor_label']}，原因是 {top_anomaly['anomaly_reason']}。"
        if top_anomaly
        else "当前范围未发现异常记录。"
    )
    order_text = (
        f"当前已有 {len(open_orders)} 个未闭环工单，其中高风险 {len(high_risk_open_orders)} 个、"
        f"待验证 {len(pending_verify_orders)} 个、待复核 {len(pending_review)} 个。"
        if open_orders
        else "当前没有未完成工单，可维持常规巡检。"
    )
    business_text = (
        f"本周期异常估算浪费 {business_impact['total_wasted_kwh']:,.1f} kWh，"
        f"约 {business_impact['total_wasted_cost_yuan']:,.0f} 元，"
        f"处置后预计可回收 {business_impact['total_estimated_saving_yuan']:,.0f} 元。"
        if anomalies
        else "当前没有可量化的异常损耗。"
    )
    verification_text = (
        f"已验证关闭 {len(closed_orders)} 个工单，仍有 {len(pending_verify_orders)} 个任务等待复测，"
        "建议用下一采样周期数据确认是否回落至阈值内。"
        if work_orders
        else "尚未形成验证闭环，可先从最高风险异常生成工单。"
    )
    recommendation_text = (
        f"{top_recommendation['building_name']}：{top_recommendation['action']}"
        if top_recommendation
        else "建议保持日报监测，重点关注 COP、夜间负荷和设备状态。"
    )

    # Build closed case summary text
    closed_summary = f"当前已关闭 {len(closed_orders)} 个工单，可作为日报归档案例。"
    if closed_cases:
        closed_buildings = sorted(set(c["building_name"] for c in closed_cases))
        closed_summary += f" 涉及建筑：{'、'.join(closed_buildings)}。"
        savings = [c for c in closed_cases if c["saving_summary"]]
        if savings:
            closed_summary += f" 其中 {len(savings)} 个工单预计带来能耗改善（估算值）。"
    management_decision = _build_management_decision_summary(frame, top_anomaly)

    from app.services import simulation_service

    return {
        "title": "建筑能源运营日报",
        "generated_at": simulation_service.now_str(),
        "scope": {
            "record_count": overview["total_records"],
            "building_count": overview["building_count"],
            "time_range": overview["time_range"],
        },
        "overview": (
            f"当前覆盖 {overview['building_count']} 栋建筑、{overview['total_records']} 条记录，"
            f"平均 COP 为 {overview['average_cop']}，异常记录 {overview['abnormal_record_count']} 条。"
        ),
        "risk": risk_text,
        "latest_anomaly": anomaly_text,
        "work_order": order_text,
        "work_order_closure": closed_summary,
        "closed_cases": closed_cases,
        "business_summary": business_text,
        "verification_summary": verification_text,
        "business_impact": business_impact,
        "work_order_status": status_counts,
        "management_decision": management_decision,
        "budget_summary": management_decision.get("budget_risk", {}),
        "roi_recommendation": management_decision.get("roi_recommendation", {}),
        "forecast": f"按最近日度趋势估算，未来 7 天电耗约 {forecast_week_kwh:,.0f} kWh。",
        "recommendation": recommendation_text,
        "action_items": [
            "先分派高风险异常，并在 SLA 内推进到待验证状态。",
            "对异常集中楼层执行现场复核，并记录处置动作、复测结果和关闭时间。",
            "复盘 COP 偏低设备，确认冷水机组、冷却塔和末端阀门状态。",
        ],
    }


def _build_management_decision_summary(frame: pd.DataFrame, top_anomaly: Dict | None = None) -> Dict:
    if frame.empty:
        return {
            "narrative": "当前没有可用于预算和投资决策的数据。",
            "budget_risk": {},
            "kpi": {},
            "roi_recommendation": {},
        }

    try:
        from app.services.budget_service import build_budget_analysis, build_budget_kpi
        from app.services.roi_service import build_equipment_audit

        latest = pd.Timestamp(frame["timestamp"].max())
        visible_building_ids = set(frame["building_id"].astype(str).unique().tolist())
        budget = build_budget_analysis(int(latest.year), int(latest.month))
        building_budgets = [
            item for item in budget.get("buildings", [])
            if str(item.get("building_id")) in visible_building_ids
        ]
        if not building_budgets:
            return {
                "narrative": "当前范围尚未生成可用预算基线。",
                "budget_risk": {},
                "kpi": {},
                "roi_recommendation": {},
            }

        risk_budget = max(
            building_budgets,
            key=lambda item: (
                float(item.get("projected_execution_rate", 0)),
                int(item.get("anomaly_count", 0)),
            ),
        )
        kpi = build_budget_kpi(str(risk_budget["building_id"]), int(latest.year))
        audit = build_equipment_audit(str(risk_budget["building_id"]))
        candidates = []
        for equipment in audit.get("equipment_list", []):
            for option in equipment.get("retrofit_candidates", [])[:3]:
                candidates.append(
                    {
                        "equipment_type": equipment.get("equipment_type"),
                        "avg_cop": equipment.get("avg_cop"),
                        "anomaly_count": equipment.get("anomaly_count"),
                        **option,
                    }
                )
        roi = max(candidates, key=lambda item: float(item.get("npv_yuan", 0))) if candidates else {}
        anomaly_hint = ""
        if top_anomaly and top_anomaly.get("building_id") == risk_budget.get("building_id"):
            anomaly_hint = f"，且最近异常来自 {top_anomaly.get('equipment_id', '')}"

        narrative = (
            f"{risk_budget['building_name']} 月末预算执行率预计 "
            f"{risk_budget['projected_execution_rate']}%，KPI 等级 {kpi.get('grade', '-')}"
            f"{anomaly_hint}。建议优先评估 {roi.get('equipment_type', '高耗能设备')} 的"
            f"{roi.get('option', '节能改造方案')}，预计 NPV "
            f"{float(roi.get('npv_yuan', 0)):,.0f} 元。"
        )
        return {
            "narrative": narrative,
            "budget_risk": risk_budget,
            "kpi": {
                "building_id": kpi.get("building_id"),
                "building_name": kpi.get("building_name"),
                "grade": kpi.get("grade"),
                "average_score": kpi.get("average_score"),
                "budget_control_rate": kpi.get("budget_control_rate"),
                "cop_pass_rate": kpi.get("cop_pass_rate"),
                "anomaly_response_timely_rate": kpi.get("anomaly_response_timely_rate"),
            },
            "roi_recommendation": roi,
        }
    except Exception as exc:  # pragma: no cover - report should degrade gracefully
        return {
            "narrative": f"预算与 ROI 决策摘要暂不可用：{exc}",
            "budget_risk": {},
            "kpi": {},
            "roi_recommendation": {},
        }


def build_equipment_summary(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    grouped = (
        working.groupby(
            [
                "building_id",
                "building_name",
                "equipment_id",
                "equipment_type",
                "floor_label",
                "zone_name",
            ],
            as_index=False,
        )
        .agg(
            record_count=("record_id", "count"),
            electricity_kwh=("electricity_kwh", "sum"),
            hvac_kwh=("hvac_kwh", "sum"),
            cooling_load_kwh=("cooling_load_kwh", "sum"),
            anomaly_count=("is_anomaly", "sum"),
        )
    )
    last_rows = (
        working.sort_values("timestamp")
        .drop_duplicates("equipment_id", keep="last")[
            ["equipment_id", "equipment_status", "timestamp"]
        ]
        .rename(
            columns={
                "equipment_status": "latest_status",
                "timestamp": "latest_seen_at",
            }
        )
    )
    grouped = grouped.merge(last_rows, on="equipment_id", how="left")
    grouped["average_cop"] = grouped.apply(
        lambda row: _safe_divide(row["cooling_load_kwh"], row["hvac_kwh"]),
        axis=1,
    )
    grouped["priority"] = grouped.apply(_equipment_priority, axis=1)
    grouped["maintenance_hint"] = grouped.apply(_equipment_maintenance_hint, axis=1)
    grouped["priority_order"] = grouped["priority"].map(_PRIORITY_ORDER)
    _round_columns(grouped, ["electricity_kwh", "hvac_kwh", "cooling_load_kwh", "average_cop"])

    export_columns = [
        "building_id",
        "building_name",
        "equipment_id",
        "equipment_type",
        "floor_label",
        "zone_name",
        "latest_status",
        "latest_seen_at",
        "average_cop",
        "anomaly_count",
        "priority",
        "maintenance_hint",
    ]
    return to_serializable_records(
        grouped.sort_values(
            ["priority_order", "anomaly_count", "building_name", "equipment_id"],
            ascending=[True, False, True, True],
        )[export_columns]
    )


def _equipment_priority(row: pd.Series) -> str:
    if str(row["latest_status"]).lower() != "normal" or row["anomaly_count"] >= 3:
        return "高"
    if row["average_cop"] < 2.5 or row["anomaly_count"] >= 1:
        return "中"
    return "低"


def _equipment_maintenance_hint(row: pd.Series) -> str:
    equipment_type = row["equipment_type"]
    if str(row["latest_status"]).lower() != "normal":
        return "先复核设备状态、控制信号和现场运行声音"
    if equipment_type == "冷水机组" and row["average_cop"] < 2.5:
        return "检查冷冻水温差、冷凝压力和主机负载率"
    if equipment_type == "冷却塔":
        return "检查喷淋、风机、填料结垢和冷却水温差"
    if equipment_type == "空气处理机组":
        return "检查过滤网压差、新风阀开度和夜间关机策略"
    if equipment_type == "风机盘管":
        return "检查末端阀门、房间设定温度和占用状态"
    return "保持例行巡检"


def build_anomaly_work_orders(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    anomalies = (
        working[working["is_anomaly"]]
        .copy()
        .sort_values(["timestamp", "electricity_kwh"], ascending=[False, False])
        .head(30)
    )
    if anomalies.empty:
        return []

    anomalies["work_order_id"] = anomalies.apply(
        lambda row: f"WO-{pd.Timestamp(row['timestamp']).strftime('%Y%m%d%H')}-{row['record_id']}",
        axis=1,
    )
    impact_records = {
        row["record_id"]: _business_impact(row)
        for _, row in anomalies.iterrows()
    }
    for field in [
        "risk_score",
        "severity",
        "triggered_rule_count",
        "wasted_kwh",
        "wasted_cost_yuan",
        "carbon_kg",
        "estimated_saving_yuan",
        "sla_hours",
        "verification_method",
        "business_impact_summary",
    ]:
        anomalies[field] = anomalies["record_id"].apply(lambda record_id: impact_records[record_id][field])
    anomalies["source_record_id"] = anomalies["record_id"]
    anomalies["priority"] = anomalies.apply(_work_order_priority, axis=1)
    anomalies["status"] = "待分派"
    anomalies["verification_status"] = "未验证"
    anomalies["possible_cause"] = anomalies.apply(_work_order_cause, axis=1)
    anomalies["recommended_action"] = anomalies.apply(_work_order_action, axis=1)
    anomalies["owner_role"] = anomalies["equipment_type"].apply(_owner_role)
    anomalies["priority_order"] = anomalies["priority"].map(_PRIORITY_ORDER)

    export_columns = [
        "work_order_id",
        "source_record_id",
        "priority",
        "status",
        "verification_status",
        "building_id",
        "building_name",
        "floor_label",
        "zone_name",
        "equipment_id",
        "equipment_type",
        "timestamp",
        "anomaly_reason",
        "severity",
        "risk_score",
        "wasted_kwh",
        "wasted_cost_yuan",
        "carbon_kg",
        "estimated_saving_yuan",
        "sla_hours",
        "business_impact_summary",
        "possible_cause",
        "recommended_action",
        "verification_method",
        "owner_role",
    ]
    return to_serializable_records(
        anomalies.sort_values(
            ["priority_order", "timestamp"], ascending=[True, False]
        )[export_columns]
    )


def build_anomaly_work_order_drafts(frame: pd.DataFrame) -> List[Dict]:
    """Generate work order draft payloads from anomalies for pending_confirm queue.
    Includes before_kwh / before_cop for later before/after comparison."""
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    anomalies = (
        working[working["is_anomaly"]]
        .copy()
        .sort_values(["timestamp", "electricity_kwh"], ascending=[False, False])
        .head(30)
    )
    if anomalies.empty:
        return []

    drafts: List[Dict] = []
    for _, row in anomalies.iterrows():
        drafts.append({
            "work_order_id": f"WO-DRAFT-{pd.Timestamp(row['timestamp']).strftime('%Y%m%d%H')}-{row['record_id']}",
            "source_record_id": str(row["record_id"]),
            "priority": _work_order_priority(row),
            "building_id": str(row["building_id"]),
            "building_name": str(row["building_name"]),
            "floor_label": str(row["floor_label"]),
            "zone_name": str(row["zone_name"]),
            "equipment_id": str(row["equipment_id"]),
            "equipment_type": str(row["equipment_type"]),
            "timestamp": _format_timestamp(row["timestamp"]),
            "anomaly_reason": str(row["anomaly_reason"]),
            "possible_cause": _work_order_cause(row),
            "recommended_action": _work_order_action(row),
            "owner_role": _owner_role(str(row["equipment_type"])),
            "before_kwh": round(float(row["electricity_kwh"]), 2),
            "before_cop": round(float(row["average_cop"]), 2),
        })
    return drafts


def _work_order_priority(row: pd.Series) -> str:
    if row.get("severity") == "高" or _business_impact(row)["severity"] == "高":
        return "高"
    if row.get("severity") == "中" or _business_impact(row)["severity"] == "中":
        return "中"
    if str(row["equipment_status"]).lower() != "normal":
        return "高"
    if row["anomaly_reason"] in {"COP低于告警阈值", "夜间负荷偏高"}:
        return "中"
    return "低"


def _work_order_cause(row: pd.Series) -> str:
    reason = row["anomaly_reason"]
    if reason == "设备状态异常":
        return "设备告警、控制信号异常或现场运行状态偏离"
    if reason == "COP低于告警阈值":
        return "冷量输出与空调电耗不匹配，可能存在换热效率下降"
    if reason == "夜间负荷偏高":
        return "排程未关闭、末端设定不合理或无人区域仍在运行"
    return "同建筑历史基线偏高，可能与占用率、环境温度或设备效率有关"


def _work_order_action(row: pd.Series) -> str:
    equipment_type = row["equipment_type"]
    if equipment_type == "空气处理机组":
        return "核对运行时间表，检查新风阀、过滤网和风机频率"
    if equipment_type == "冷水机组":
        return "检查主机负载率、供回水温差和冷凝压力"
    if equipment_type == "冷却塔":
        return "检查冷却塔风机、喷淋、补水和冷却水回水温度"
    if equipment_type == "风机盘管":
        return "检查末端阀门、房间占用状态和设定温度"
    return "安排现场巡检并复核传感器采集值"


def _owner_role(equipment_type: str) -> str:
    if equipment_type in {"冷水机组", "冷却塔"}:
        return "制冷机房值班员"
    if equipment_type == "空气处理机组":
        return "空调系统运维员"
    if equipment_type == "风机盘管":
        return "楼层巡检员"
    return "能源管理员"


def build_optimization_recommendations(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = _add_operational_dimensions(frame)
    recommendations: List[Dict] = []
    rec_index = 1

    for _, group in working.groupby(["building_id", "building_name"], sort=True):
        building = group.iloc[0]
        total_electricity = float(group["electricity_kwh"].sum())
        total_hvac = float(group["hvac_kwh"].sum())
        total_cooling = float(group["cooling_load_kwh"].sum())
        avg_cop = _safe_divide(total_cooling, total_hvac)
        hvac_ratio = _safe_divide(total_hvac, total_electricity)
        anomaly_count = int(group["is_anomaly"].sum())
        night_ratio = _safe_divide(
            group[(group["hour"] < 6) | (group["hour"] >= 22)]["electricity_kwh"].sum(),
            total_electricity,
        )

        if avg_cop < 2.6:
            recommendations.append(
                _recommendation(
                    rec_index,
                    building,
                    "空调能效",
                    "高",
                    f"平均 COP 为 {avg_cop:.2f}，低于建议阈值 2.60。",
                    "优先检查冷水机组、冷却塔和供回水温差，确认是否存在低效运行。",
                    "预计降低空调电耗 4%-8%",
                )
            )
            rec_index += 1

        if night_ratio > 0.22:
            recommendations.append(
                _recommendation(
                    rec_index,
                    building,
                    "夜间负荷",
                    "中",
                    f"夜间电耗占比为 {night_ratio * 100:.1f}%。",
                    "核对楼宇排程、无人区域末端和夜间值班区域，减少非必要运行。",
                    "预计降低总电耗 2%-5%",
                )
            )
            rec_index += 1

        if anomaly_count:
            recommendations.append(
                _recommendation(
                    rec_index,
                    building,
                    "异常治理",
                    "高" if anomaly_count >= 5 else "中",
                    f"当前筛选范围识别到 {anomaly_count} 条异常记录。",
                    "先处理高优先级工单，再复盘异常集中楼层和设备类型。",
                    "减少重复告警并提升运维响应效率",
                )
            )
            rec_index += 1

        if hvac_ratio > 0.48:
            recommendations.append(
                _recommendation(
                    rec_index,
                    building,
                    "空调占比",
                    "中",
                    f"空调电耗占总电耗 {hvac_ratio * 100:.1f}%。",
                    "优化空调启停策略，结合室外温湿度动态调整设定温度。",
                    "预计降低高峰时段空调负荷",
                )
            )
            rec_index += 1

    if not recommendations:
        recommendations.append(
            {
                "recommendation_id": "REC-001",
                "building_id": "ALL",
                "building_name": "全部建筑",
                "category": "持续监测",
                "priority": "低",
                "finding": "当前筛选范围没有触发明显节能告警。",
                "action": "保持日报监测，重点关注 COP、夜间负荷和设备状态趋势。",
                "expected_impact": "维持稳定运行",
            }
        )

    return sorted(
        recommendations,
        key=lambda item: (_PRIORITY_ORDER.get(item["priority"], 9), item["building_name"]),
    )


def _recommendation(
    rec_index: int,
    building: pd.Series,
    category: str,
    priority: str,
    finding: str,
    action: str,
    expected_impact: str,
) -> Dict:
    return {
        "recommendation_id": f"REC-{rec_index:03d}",
        "building_id": building["building_id"],
        "building_name": building["building_name"],
        "category": category,
        "priority": priority,
        "finding": finding,
        "action": action,
        "expected_impact": expected_impact,
    }

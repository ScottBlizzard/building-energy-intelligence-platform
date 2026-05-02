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
    anomalies = build_anomaly_summary(frame)
    if not anomalies:
        return []

    anomaly_frame = pd.DataFrame(anomalies)
    grouped = (
        anomaly_frame.groupby("anomaly_reason", as_index=False)
        .agg({"record_id": "count"})
        .rename(columns={"record_id": "count"})
        .sort_values("count", ascending=False)
    )
    return grouped.to_dict(orient="records")


def build_anomaly_summary(frame: pd.DataFrame) -> List[Dict]:
    if frame.empty:
        return []

    working = frame.copy()
    building_mean = working.groupby("building_id")["electricity_kwh"].transform("mean")
    building_std = working.groupby("building_id")["electricity_kwh"].transform("std")
    working["upper_bound"] = building_mean + building_std.fillna(0)

    abnormal_status = working["equipment_status"].astype(str).str.lower() != "normal"
    abnormal_usage = working["electricity_kwh"] > working["upper_bound"]
    anomalies = working[abnormal_status | abnormal_usage].copy()

    if anomalies.empty:
        return []

    anomalies["anomaly_reason"] = anomalies.apply(
        lambda row: "设备状态异常"
        if str(row["equipment_status"]).lower() != "normal"
        else "电耗高于同建筑基线",
        axis=1,
    )

    export_columns = [
        "record_id",
        "building_id",
        "building_name",
        "timestamp",
        "electricity_kwh",
        "hvac_kwh",
        "equipment_id",
        "equipment_status",
        "anomaly_reason",
    ]
    return to_serializable_records(
        anomalies.sort_values("timestamp", ascending=False)[export_columns].head(20)
    )

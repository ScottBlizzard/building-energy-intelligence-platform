"""Building-level detail analysis service.

Provides per-building deep-dive statistics: totals, averages, anomaly
breakdowns and time profiles.
"""

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from app.services.analysis_service import (
    _safe_divide,
    build_anomaly_summary,
    to_serializable_records,
)
from app.services.data_loader import get_filtered_dataset


def build_building_detail(
    building_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict:
    """Build a comprehensive building-level analysis.

    Returns building info, totals, averages, anomaly count, top anomaly
    reasons, and recent records.
    """
    frame = get_filtered_dataset(
        building_id=building_id, start_time=start_time, end_time=end_time
    )

    if frame.empty:
        return {
            "building_id": building_id,
            "building_name": None,
            "building_type": None,
            "record_count": 0,
            "time_range": {"start": None, "end": None},
            "totals": {},
            "average_cop": 0.0,
            "anomaly_count": 0,
            "top_anomaly_reasons": [],
            "recent_records": [],
        }

    building_info = frame.iloc[0]

    totals = {
        "electricity_kwh": round(float(frame["electricity_kwh"].sum()), 2),
        "water_m3": round(float(frame["water_m3"].sum()), 2),
        "hvac_kwh": round(float(frame["hvac_kwh"].sum()), 2),
        "cooling_load_kwh": round(float(frame["cooling_load_kwh"].sum()), 2),
    }

    average_cop = round(
        _safe_divide(totals["cooling_load_kwh"], totals["hvac_kwh"]), 2
    )

    anomalies = build_anomaly_summary(frame)
    anomaly_reasons = _count_anomaly_reasons(anomalies)

    return {
        "building_id": str(building_info["building_id"]),
        "building_name": str(building_info["building_name"]),
        "building_type": str(building_info["building_type"]),
        "record_count": int(len(frame)),
        "time_range": {
            "start": pd.Timestamp(frame["timestamp"].min()).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "end": pd.Timestamp(frame["timestamp"].max()).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        },
        "totals": totals,
        "average_cop": average_cop,
        "anomaly_count": len(anomalies),
        "top_anomaly_reasons": anomaly_reasons[:5],
        "recent_records": to_serializable_records(
            frame.sort_values("timestamp", ascending=False).head(5)
        ),
    }


def _count_anomaly_reasons(anomalies: List[Dict]) -> List[Dict]:
    """Count anomaly reasons and return sorted list."""
    if not anomalies:
        return []
    anomaly_frame = pd.DataFrame(anomalies)
    grouped = (
        anomaly_frame.groupby("anomaly_reason", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return grouped.to_dict(orient="records")

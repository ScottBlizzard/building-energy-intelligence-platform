"""Counterfactual scenarios for the simulation time machine."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from app.services import simulation_service
from app.services.analysis_service import _add_operational_dimensions
from app.services.data_loader import read_dataset

_PRICE_YUAN_PER_KWH = 0.82
_CARBON_KG_PER_KWH = 0.5703


def _start_timestamp(start_date: Optional[str] = None) -> pd.Timestamp:
    if start_date:
        return pd.Timestamp(start_date)
    current = simulation_service.get_current_date()
    if current:
        return pd.Timestamp(current)
    frame = read_dataset()
    return pd.Timestamp(frame["timestamp"].min()).normalize()


def _normal_target(row) -> float:
    electricity = float(row.get("electricity_kwh") or 0)
    building_mean = float(row.get("building_mean") or electricity)
    upper_bound = float(row.get("upper_bound") or building_mean)
    healthy = min(electricity, building_mean * 0.92, upper_bound * 0.86)
    return round(max(0.0, healthy), 2)


def _daily_point(day: pd.Timestamp, total_kwh: float, wasted_kwh: float, anomaly_count: int) -> Dict:
    return {
        "date": day.strftime("%Y-%m-%d"),
        "energy_kwh": round(total_kwh, 2),
        "loss_yuan": round(wasted_kwh * _PRICE_YUAN_PER_KWH, 2),
        "carbon_kg": round(wasted_kwh * _CARBON_KG_PER_KWH, 2),
        "anomaly_count": int(anomaly_count),
    }


def _scenario_from_rows(rows, label: str, mode: str, start_ts: pd.Timestamp, delay_days: int) -> Dict:
    daily = []
    total_energy = 0.0
    total_wasted = 0.0
    total_anomalies = 0
    for day, group in rows.groupby(rows["timestamp"].dt.normalize()):
        energy = 0.0
        wasted = 0.0
        anomalies = 0
        for _, row in group.iterrows():
            electricity = float(row.get("electricity_kwh") or 0)
            building_mean = float(row.get("building_mean") or electricity)
            is_anomaly = bool(row.get("is_anomaly"))
            wasted_row = max(0.0, electricity - float(row.get("upper_bound") or building_mean))
            if is_anomaly and wasted_row <= 0:
                wasted_row = max(0.0, electricity - building_mean * 0.9)
            if is_anomaly and wasted_row <= 0:
                wasted_row = electricity * 0.03

            repaired = mode == "immediate" or (mode == "delayed" and day >= start_ts + pd.Timedelta(days=delay_days))
            if repaired:
                healthy = _normal_target(row)
                energy += healthy
            else:
                energy += electricity
                wasted += wasted_row
                anomalies += 1 if is_anomaly else 0
        total_energy += energy
        total_wasted += wasted
        total_anomalies += anomalies
        daily.append(_daily_point(pd.Timestamp(day), energy, wasted, anomalies))

    return {
        "key": mode,
        "label": label,
        "daily": daily,
        "total_energy_kwh": round(total_energy, 2),
        "total_loss_yuan": round(total_wasted * _PRICE_YUAN_PER_KWH, 2),
        "total_carbon_kg": round(total_wasted * _CARBON_KG_PER_KWH, 2),
        "total_anomaly_count": int(total_anomalies),
    }


def build_counterfactual_scenarios(
    equipment_id: str,
    *,
    horizon_days: int = 7,
    delay_days: int = 3,
    start_date: Optional[str] = None,
) -> Dict:
    start_ts = _start_timestamp(start_date)
    horizon = max(1, int(horizon_days or 7))
    delay = max(1, int(delay_days or 3))
    end_ts = start_ts + pd.Timedelta(days=horizon)

    # Build the counterfactual on the *simulated future*: apply scheduled
    # failures (injections) and the operator's interventions, but NOT the
    # visibility window (we need data beyond "today" to project the horizon).
    # This keeps the experiment consistent with the anomalies the operator
    # actually sees in the dashboard instead of the raw seed dataset.
    base = simulation_service.apply_injections(
        simulation_service.apply_interventions(read_dataset().copy())
    )
    frame = _add_operational_dimensions(base)
    subset = frame[
        (frame["equipment_id"] == equipment_id)
        & (frame["timestamp"] >= start_ts)
        & (frame["timestamp"] < end_ts)
    ].copy()

    if subset.empty:
        return {
            "equipment_id": equipment_id,
            "start_date": start_ts.strftime("%Y-%m-%d"),
            "horizon_days": horizon,
            "delay_days": delay,
            "scenarios": [],
            "decision_sentence": "当前样本窗口内没有该设备的后续数据，无法生成对照实验。",
            "generated_at": simulation_service.now_str(),
        }

    scenarios = [
        _scenario_from_rows(subset, "不处理", "no_action", start_ts, delay),
        _scenario_from_rows(subset, "立即处理", "immediate", start_ts, delay),
        _scenario_from_rows(subset, f"延迟 {delay} 天处理", "delayed", start_ts, delay),
    ]
    by_key = {item["key"]: item for item in scenarios}
    immediate = by_key["immediate"]
    delayed = by_key["delayed"]
    no_action = by_key["no_action"]
    saved_vs_delay = {
        "kwh": round(delayed["total_energy_kwh"] - immediate["total_energy_kwh"], 2),
        "yuan": round(delayed["total_loss_yuan"] - immediate["total_loss_yuan"], 2),
        "carbon_kg": round(delayed["total_carbon_kg"] - immediate["total_carbon_kg"], 2),
        "anomalies": int(delayed["total_anomaly_count"] - immediate["total_anomaly_count"]),
    }
    saved_vs_no_action = {
        "kwh": round(no_action["total_energy_kwh"] - immediate["total_energy_kwh"], 2),
        "yuan": round(no_action["total_loss_yuan"] - immediate["total_loss_yuan"], 2),
        "carbon_kg": round(no_action["total_carbon_kg"] - immediate["total_carbon_kg"], 2),
        "anomalies": int(no_action["total_anomaly_count"] - immediate["total_anomaly_count"]),
    }
    return {
        "equipment_id": equipment_id,
        "building_name": str(subset["building_name"].iloc[0]),
        "equipment_type": str(subset["equipment_type"].iloc[0]),
        "start_date": start_ts.strftime("%Y-%m-%d"),
        "horizon_days": horizon,
        "delay_days": delay,
        "scenarios": scenarios,
        "savings_vs_delay": saved_vs_delay,
        "savings_vs_no_action": saved_vs_no_action,
        "decision_sentence": _decision_sentence(
            equipment_id, horizon, delay, saved_vs_delay, saved_vs_no_action
        ),
        "generated_at": simulation_service.now_str(),
    }


def _decision_sentence(
    equipment_id: str,
    horizon: int,
    delay: int,
    saved_vs_delay: Dict,
    saved_vs_no_action: Dict,
) -> str:
    """Compose a readable decision sentence that does not show a misleading
    "省 0 元" when the device has not yet entered a sustained-waste phase."""
    delay_meaningful = saved_vs_delay["yuan"] >= 1 or saved_vs_delay["kwh"] >= 1
    na = saved_vs_no_action
    na_meaningful = na["yuan"] >= 1 or na["anomalies"] > 0

    if delay_meaningful:
        first = (
            f"立即处理相比延迟 {delay} 天可少浪费约 "
            f"{saved_vs_delay['kwh']:,.1f} kWh、{saved_vs_delay['yuan']:,.0f} 元、"
            f"{saved_vs_delay['carbon_kg']:,.1f} kg 碳排；"
        )
    else:
        first = f"未来 {delay} 天内该设备尚未进入持续超耗阶段，立即与延迟处理的短期差异不明显；"

    if na_meaningful:
        second = (
            f"相比不处理，{horizon} 天内可减少约 {na['yuan']:,.0f} 元浪费、"
            f"{na['anomalies']} 次异常暴露。"
        )
    else:
        second = f"相比不处理，{horizon} 天内经济影响有限（以状态/能效告警为主，建议纳入巡检而非紧急派单）。"

    return f"对 {equipment_id}，{first}{second}"

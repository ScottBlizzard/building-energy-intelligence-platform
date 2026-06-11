"""Simulation clock for the operational sandbox ("time machine").

The sample dataset is a fixed historical snapshot. This service turns it into an
interactive timeline:

- A server-side "current date" pointer divides the data into the visible past
  (`timestamp <= current_date`) and the hidden future.
- Advancing the clock reveals the next slice of pre-written data, so new anomalies
  surface day by day.
- Closing a work order registers an *intervention*: from that day onward the target
  equipment's readings are restored to its own normal baseline. This makes operator
  decisions causally change the future ("fix it and it recovers; ignore it and it
  keeps bleeding"), instead of replaying a fixed script.
- A deterministic *failure schedule* makes a rotating set of equipment look healthy
  until a scheduled onset date and then start failing, so advancing the clock always
  reveals fresh anomalies on equipment that previously looked fine. These scheduled
  failures are still suppressed by a repair, so the loop stays causal.

Design notes:
- All transform helpers operate on a passed-in DataFrame and never import
  ``data_loader`` so the dependency graph stays acyclic
  (``data_loader`` -> ``simulation_service``, ``work_order_store`` -> ``simulation_service``).
- When no clock file exists the simulation is *inactive* and every helper is a
  no-op, so non-demo behaviour (and the existing test suite) is unchanged.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.core.config import get_settings

DEFAULT_START_DATE = "2026-05-01"

# Scheduled future failures: keep advancing the clock interesting even if the
# operator repairs everything visible today.
SCHEDULE_FIRST_OFFSET_DAYS = 3   # first staged failure this many days after start
SCHEDULE_STEP_DAYS = 3           # a new equipment starts failing every N days
SCHEDULE_PICK_EVERY = 2          # use every Nth distinct equipment for staging


def _state_path() -> Path:
    return get_settings().work_order_file.parent / "sim_state.json"


def _empty_state() -> Dict:
    return {"current_date": None, "start_date": None, "interventions": []}


def _read_state() -> Dict:
    path = _state_path()
    if not path.exists():
        return _empty_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_state()
    if not isinstance(payload, dict):
        return _empty_state()
    payload.setdefault("current_date", None)
    payload.setdefault("start_date", payload.get("current_date"))
    payload.setdefault("interventions", [])
    return payload


def _write_state(state: Dict) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def is_active() -> bool:
    return _read_state().get("current_date") is not None


def get_current_date() -> Optional[date]:
    raw = _read_state().get("current_date")
    if not raw:
        return None
    return pd.Timestamp(raw).date()


def get_interventions() -> List[Dict]:
    return list(_read_state().get("interventions", []))


def get_start_date() -> Optional[date]:
    raw = _read_state().get("start_date")
    if not raw:
        return None
    return pd.Timestamp(raw).date()


def get_state() -> Dict:
    state = _read_state()
    return {
        "active": state.get("current_date") is not None,
        "current_date": state.get("current_date"),
        "start_date": state.get("start_date"),
        "interventions": state.get("interventions", []),
    }


def signature() -> str:
    """A small, deterministic fingerprint of the current simulation state.

    Used as a cache key for the (expensive) dataset transforms and annotations:
    while the clock/interventions are unchanged, every request can reuse the same
    computed frame instead of recomputing it.
    """
    state = _read_state()
    interventions = sorted(
        (str(item.get("equipment_id")), str(item.get("from_date")))
        for item in state.get("interventions", [])
    )
    return json.dumps(
        {
            "current_date": state.get("current_date"),
            "start_date": state.get("start_date"),
            "interventions": interventions,
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def start_simulation(start_date: Optional[str] = None) -> Dict:
    state = _empty_state()
    resolved = start_date or DEFAULT_START_DATE
    state["current_date"] = resolved
    state["start_date"] = resolved
    state["interventions"] = []
    _write_state(state)
    return get_state()


def advance_day(days: int = 1) -> Dict:
    state = _read_state()
    if not state.get("current_date"):
        start_simulation()
        state = _read_state()
    new_date = pd.Timestamp(state["current_date"]) + pd.Timedelta(days=max(1, int(days)))
    state["current_date"] = new_date.strftime("%Y-%m-%d")
    _write_state(state)
    return get_state()


def reset() -> Dict:
    path = _state_path()
    if path.exists():
        path.unlink()
    return get_state()


def register_intervention(equipment_id: str, from_date: Optional[str] = None) -> None:
    """Record that ``equipment_id`` has been repaired and should recover from
    ``from_date`` onward. Defaults to the current simulated date (or today)."""
    if not equipment_id:
        return
    state = _read_state()
    if from_date is None:
        current = state.get("current_date")
        from_date = current or datetime.now().strftime("%Y-%m-%d")
    state.setdefault("interventions", [])
    # keep the earliest repair date if the same equipment is fixed more than once
    for item in state["interventions"]:
        if item.get("equipment_id") == equipment_id:
            if pd.Timestamp(from_date) < pd.Timestamp(item["from_date"]):
                item["from_date"] = from_date
            _write_state(state)
            return
    state["interventions"].append({"equipment_id": equipment_id, "from_date": from_date})
    _write_state(state)


def _operational_equipment_ids(frame: pd.DataFrame) -> pd.Series:
    """Recompute the synthesized ("operational") equipment id used by work orders and
    the anomaly views, so simulation transforms can match on the same identity."""
    from app.services.analysis_service import (
        _infer_operational_equipment_code,
        _infer_floor,
        _infer_operational_equipment_id,
    )

    helper = frame.copy()
    helper["equipment_code"] = helper.apply(_infer_operational_equipment_code, axis=1)
    helper["floor_label"] = helper.apply(_infer_floor, axis=1)
    return helper.apply(_infer_operational_equipment_id, axis=1)


def _building_normal_baseline(frame: pd.DataFrame, building_id) -> Dict[str, float]:
    building_rows = frame[frame["building_id"] == building_id]
    normal_rows = building_rows[building_rows["equipment_status"].astype(str).str.lower() == "normal"]
    src = normal_rows if not normal_rows.empty else building_rows
    elec = float(src["electricity_kwh"].median()) if not src.empty else 0.0
    hvac = float(src["hvac_kwh"].median()) if not src.empty else 0.0
    if not hvac > 0:
        hvac = float(src["hvac_kwh"].mean() or 1.0) or 1.0
    # A robustly low (low-percentile) usage target. Repairing many equipment at once
    # collapses the building's mean+std threshold; landing recovered equipment near the
    # bottom of the healthy range guarantees they leave the anomaly list regardless of
    # how many are fixed simultaneously.
    elec_low = float(src["electricity_kwh"].quantile(0.15)) if not src.empty else elec
    hvac_low = float(src["hvac_kwh"].quantile(0.15)) if not src.empty else hvac
    if not hvac_low > 0:
        hvac_low = hvac
    return {
        "electricity": elec,
        "hvac": hvac,
        "electricity_low": elec_low,
        "hvac_low": hvac_low,
    }


def apply_interventions(frame: pd.DataFrame) -> pd.DataFrame:
    """Restore intervened equipment to its own normal baseline from the repair date
    onward, so the (revealed) future reflects the operator's fix."""
    interventions = get_interventions()
    if not interventions or frame.empty or "equipment_id" not in frame.columns:
        return frame

    frame = frame.copy()
    # Freeze a baseline snapshot so repairing many equipment at once does not skew
    # the building statistics used to compute each recovery target.
    source_frame = frame.copy()
    healthy_cop = 3.0

    # Work orders reference the *operational* (synthesized) equipment id rather than
    # the raw CSV column. Recompute it deterministically so interventions match.
    op_equipment_id = _operational_equipment_ids(frame)

    for item in interventions:
        equipment_id = item.get("equipment_id")
        from_date = item.get("from_date")
        if not equipment_id or not from_date:
            continue
        from_ts = pd.Timestamp(from_date)
        eq_mask_all = op_equipment_id == equipment_id
        if not eq_mask_all.any():
            continue

        building_id = frame.loc[eq_mask_all, "building_id"].iloc[0]
        baseline = _building_normal_baseline(source_frame, building_id)

        mask = eq_mask_all & (frame["timestamp"] >= from_ts)
        if not mask.any():
            continue

        elec_base = baseline["electricity_low"]
        hvac_base = baseline["hvac_low"]
        if not hvac_base > 0:
            hvac_base = 1.0

        if "electricity_kwh" in frame.columns:
            frame.loc[mask, "electricity_kwh"] = round(elec_base, 2)
        if "hvac_kwh" in frame.columns:
            frame.loc[mask, "hvac_kwh"] = round(hvac_base, 2)
        if "cooling_load_kwh" in frame.columns:
            # restore an efficient COP (cooling / hvac == healthy_cop)
            frame.loc[mask, "cooling_load_kwh"] = round(hvac_base * healthy_cop, 2)
        if "equipment_status" in frame.columns:
            frame.loc[mask, "equipment_status"] = "normal"

    return frame


def _failure_schedule(op_equipment_id: pd.Series, start_ts: pd.Timestamp) -> List[Dict]:
    """Deterministically stage a rotating set of equipment to start failing on
    spaced-out future dates, so advancing the clock always surfaces fresh anomalies."""
    unique_ids = sorted(op_equipment_id.dropna().unique().tolist())
    staged = unique_ids[::SCHEDULE_PICK_EVERY]
    schedule = []
    for index, equipment_id in enumerate(staged):
        onset = start_ts + pd.Timedelta(days=SCHEDULE_FIRST_OFFSET_DAYS + index * SCHEDULE_STEP_DAYS)
        schedule.append({"equipment_id": equipment_id, "onset": onset})
    return schedule


def get_scheduled_failures() -> List[Dict]:
    """Public view of staged failures with their onset dates (for diagnostics/UI)."""
    start = get_start_date()
    if start is None:
        return []
    from app.services.data_loader import read_dataset

    op_ids = _operational_equipment_ids(read_dataset())
    return [
        {"equipment_id": item["equipment_id"], "onset": item["onset"].strftime("%Y-%m-%d")}
        for item in _failure_schedule(op_ids, pd.Timestamp(start))
    ]


def apply_injections(frame: pd.DataFrame) -> pd.DataFrame:
    """Stage future failures: each scheduled equipment looks healthy before its onset
    date and starts failing afterwards. Because it is healthy (and hidden in the
    future) beforehand, the operator cannot pre-empt it, guaranteeing a steady stream
    of genuinely new anomalies as the clock advances."""
    start = get_start_date()
    if start is None or frame.empty or "equipment_id" not in frame.columns:
        return frame

    op_equipment_id = _operational_equipment_ids(frame)
    schedule = _failure_schedule(op_equipment_id, pd.Timestamp(start))
    if not schedule:
        return frame

    frame = frame.copy()
    source_frame = frame.copy()
    for item in schedule:
        equipment_id = item["equipment_id"]
        onset = item["onset"]
        eq_mask = op_equipment_id == equipment_id
        if not eq_mask.any():
            continue

        building_id = frame.loc[eq_mask, "building_id"].iloc[0]
        baseline = _building_normal_baseline(source_frame, building_id)
        building_max = float(source_frame.loc[source_frame["building_id"] == building_id, "electricity_kwh"].max())

        # Before onset: look healthy so it cannot be repaired in advance.
        pre = eq_mask & (frame["timestamp"] < onset)
        if pre.any():
            frame.loc[pre, "electricity_kwh"] = round(baseline["electricity"] * 0.85, 2)
            frame.loc[pre, "hvac_kwh"] = round(baseline["hvac"] * 0.85, 2)
            frame.loc[pre, "cooling_load_kwh"] = round(baseline["hvac"] * 0.85 * 3.0, 2)
            frame.loc[pre, "equipment_status"] = "normal"

        # From onset onward: fail clearly (electricity well above building spread).
        post = eq_mask & (frame["timestamp"] >= onset)
        if post.any():
            frame.loc[post, "electricity_kwh"] = round(building_max * 1.5, 2)
            frame.loc[post, "equipment_status"] = "fault"

    return frame


def apply_window(frame: pd.DataFrame) -> pd.DataFrame:
    """Hide data after the current simulated date."""
    current = get_current_date()
    if current is None or frame.empty or "timestamp" not in frame.columns:
        return frame
    end = pd.Timestamp(current) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return frame[frame["timestamp"] <= end]


def apply(frame: pd.DataFrame) -> pd.DataFrame:
    """Full simulation transform: staged future failures, operator repairs (which
    override staged failures from the repair date), then the visible window."""
    if not is_active():
        return frame
    return apply_window(apply_interventions(apply_injections(frame)))

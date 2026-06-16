from collections import OrderedDict
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional

import pandas as pd
from fastapi import HTTPException

from app.core.config import get_settings


REQUIRED_COLUMNS = {
    "record_id",
    "building_id",
    "building_name",
    "building_type",
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
    "equipment_status",
}

DICTIONARY_FILE = "data/dictionaries/energy_records_dictionary.csv"


def _load_raw_frame() -> pd.DataFrame:
    """读取原始能耗数据：优先数据库 energy_readings 表，否则回退 CSV。"""
    from app.db import repository as db_repo

    if db_repo.is_enabled():
        frame = db_repo.read_energy_dataframe()
        if frame is not None:
            return frame

    settings = get_settings()
    if not settings.data_file.exists():
        raise FileNotFoundError("Data file not found: {0}".format(settings.data_file))
    return pd.read_csv(settings.data_file)


@lru_cache(maxsize=1)
def read_dataset() -> pd.DataFrame:
    frame = _load_raw_frame()
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: {0}".format(
                ", ".join(sorted(missing_columns))
            )
        )

    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame.sort_values("timestamp").reset_index(drop=True)


# Simulation transforms (intervention recovery, staged failures, windowing) are
# pure functions of the cached raw dataset + the current simulation signature.
# They are relatively expensive (row-wise id synthesis + per-building quantiles)
# and were previously recomputed on *every* request; a single UI interaction fans
# out into many requests. We memoise the results keyed by the simulation
# signature so only the first request after a clock change pays the cost.
_VISIBLE_CACHE: Dict[str, object] = {"sig": None, "frame": None}
_FILTERED_CACHE: "OrderedDict[tuple, pd.DataFrame]" = OrderedDict()
_FILTERED_CACHE_MAX = 24


def clear_dataset_cache() -> None:
    read_dataset.cache_clear()
    load_data_dictionary.cache_clear()
    _VISIBLE_CACHE["sig"] = None
    _VISIBLE_CACHE["frame"] = None
    _FILTERED_CACHE.clear()


def get_filtered_dataset(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> pd.DataFrame:
    from app.services import simulation_service

    key = (
        simulation_service.signature(),
        building_id or "",
        pd.Timestamp(start_time).isoformat() if start_time is not None else "",
        pd.Timestamp(end_time).isoformat() if end_time is not None else "",
    )
    cached = _FILTERED_CACHE.get(key)
    if cached is not None:
        _FILTERED_CACHE.move_to_end(key)
        return cached.copy()

    frame = read_dataset().copy()
    # Apply operator interventions (causal recovery) before any windowing.
    frame = simulation_service.apply_interventions(frame)

    if building_id:
        frame = frame[frame["building_id"] == building_id]
    if start_time is not None:
        frame = frame[frame["timestamp"] >= pd.Timestamp(start_time)]
    if end_time is not None:
        frame = frame[frame["timestamp"] <= pd.Timestamp(end_time)]

    # Hide data after the current simulated date (no-op when simulation inactive).
    frame = simulation_service.apply_window(frame).reset_index(drop=True)

    _FILTERED_CACHE[key] = frame
    _FILTERED_CACHE.move_to_end(key)
    while len(_FILTERED_CACHE) > _FILTERED_CACHE_MAX:
        _FILTERED_CACHE.popitem(last=False)
    return frame.copy()


def get_visible_dataset() -> pd.DataFrame:
    """Full dataset as seen at the current simulated date (interventions + window).

    No-op equivalent to ``read_dataset()`` when the simulation clock is inactive.
    Result is cached per simulation signature (see module note above).
    """
    from app.services import simulation_service

    sig = simulation_service.signature()
    if _VISIBLE_CACHE["sig"] == sig and _VISIBLE_CACHE["frame"] is not None:
        return _VISIBLE_CACHE["frame"].copy()

    frame = simulation_service.apply(read_dataset().copy()).reset_index(drop=True)
    _VISIBLE_CACHE["sig"] = sig
    _VISIBLE_CACHE["frame"] = frame
    return frame.copy()


def get_building_options() -> List[Dict[str, str]]:
    frame = read_dataset()
    buildings = (
        frame[["building_id", "building_name", "building_type"]]
        .drop_duplicates()
        .sort_values(["building_type", "building_name"])
    )
    return buildings.to_dict(orient="records")


@lru_cache(maxsize=1)
def load_data_dictionary() -> List[Dict]:
    """Load the project data dictionary used by SRS/SDD metadata checks."""
    path = get_settings()._resolve_path(DICTIONARY_FILE)
    if not path.exists():
        return []

    dictionary = pd.read_csv(path).fillna("")
    items: List[Dict] = []
    for _, row in dictionary.iterrows():
        field_name = str(row.get("field_name", "")).strip()
        if not field_name:
            continue
        items.append(
            {
                "field_name": field_name,
                "data_type": str(row.get("data_type", "")).strip(),
                "required": str(row.get("required", "")).strip().lower() in {"yes", "true", "1"},
                "description": str(row.get("description", "")).strip(),
                "example": str(row.get("example", "")).strip(),
            }
        )
    return items


def load_dataset_or_raise(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> pd.DataFrame:
    """Load filtered dataset, raising HTTPException on errors."""
    try:
        return get_filtered_dataset(
            building_id=building_id, start_time=start_time, end_time=end_time
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def get_dataset_meta() -> Dict:
    frame = read_dataset()
    dictionary = load_data_dictionary()
    dictionary_fields = {item["field_name"] for item in dictionary}
    dataset_fields = set(frame.columns)
    return {
        "fields": list(frame.columns),
        "data_dictionary": dictionary,
        "field_definitions": {item["field_name"]: item for item in dictionary},
        "dictionary_coverage": {
            "defined_field_count": len(dictionary_fields),
            "dataset_field_count": len(dataset_fields),
            "matched_field_count": len(dictionary_fields.intersection(dataset_fields)),
            "missing_in_dictionary": sorted(dataset_fields.difference(dictionary_fields)),
            "defined_but_missing_in_dataset": sorted(dictionary_fields.difference(dataset_fields)),
        },
        "building_options": get_building_options(),
        "record_count": int(len(frame)),
        "building_count": int(frame["building_id"].nunique()),
        "time_range": {
            "start": frame["timestamp"].min().strftime("%Y-%m-%d %H:%M:%S"),
            "end": frame["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }

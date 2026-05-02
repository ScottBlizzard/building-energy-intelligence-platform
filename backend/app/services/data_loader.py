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


@lru_cache(maxsize=1)
def read_dataset() -> pd.DataFrame:
    settings = get_settings()
    if not settings.data_file.exists():
        raise FileNotFoundError("Data file not found: {0}".format(settings.data_file))

    frame = pd.read_csv(settings.data_file)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: {0}".format(
                ", ".join(sorted(missing_columns))
            )
        )

    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame.sort_values("timestamp").reset_index(drop=True)


def clear_dataset_cache() -> None:
    read_dataset.cache_clear()


def get_filtered_dataset(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> pd.DataFrame:
    frame = read_dataset().copy()

    if building_id:
        frame = frame[frame["building_id"] == building_id]
    if start_time is not None:
        frame = frame[frame["timestamp"] >= pd.Timestamp(start_time)]
    if end_time is not None:
        frame = frame[frame["timestamp"] <= pd.Timestamp(end_time)]

    return frame.reset_index(drop=True)


def get_building_options() -> List[Dict[str, str]]:
    frame = read_dataset()
    buildings = (
        frame[["building_id", "building_name", "building_type"]]
        .drop_duplicates()
        .sort_values(["building_type", "building_name"])
    )
    return buildings.to_dict(orient="records")


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
    return {
        "fields": list(frame.columns),
        "building_options": get_building_options(),
        "record_count": int(len(frame)),
        "building_count": int(frame["building_id"].nunique()),
        "time_range": {
            "start": frame["timestamp"].min().strftime("%Y-%m-%d %H:%M:%S"),
            "end": frame["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }

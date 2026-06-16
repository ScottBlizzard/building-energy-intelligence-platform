from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "samples" / "energy_records.csv"

# First-half-year (heating + early cooling) synthetic dataset.
# Span: 2026-01-01 ~ 2026-06-01 (2026 is NOT a leap year → Feb has 28 days).
# The seasonal energy curve is bimodal: a winter heating peak (Jan/Feb) and a
# rising summer cooling load (May/Jun), with an April shoulder trough — so the
# month-over-month trend, environment temperature and load are physically
# self-consistent end to end for the sampled period (see docs/29 §1.3).
DATA_START = datetime(2026, 1, 1, 0, 0, 0)
DATA_END = datetime(2026, 6, 1, 0, 0, 0)

# Heating / cooling balance-point model: load rises when it is colder than
# HEAT_BALANCE_C (space heating) or hotter than COOL_BALANCE_C (cooling).
HEAT_BALANCE_C = 18.0
COOL_BALANCE_C = 23.0
HEAT_SENSITIVITY = 0.018
COOL_SENSITIVITY = 0.030

# Smooth seasonal temperature anchors (day_index_from_Jan1, monthly-mean °C),
# anchored on each month's mid-point and linearly interpolated by day.
TEMP_ANCHORS = [
    (14, 4.0),    # mid-Jan, deep winter
    (44, 6.5),    # mid-Feb
    (73, 11.0),   # mid-Mar
    (104, 17.0),  # mid-Apr (shoulder)
    (134, 23.0),  # mid-May
    (151, 27.5),  # Jun 1
]

# Intra-day temperature swing (°C offset by 3-hour slot); warmest mid-afternoon.
DIURNAL_OFFSET = {0: -3.0, 3: -4.0, 6: -2.5, 9: 1.0, 12: 4.0, 15: 5.0, 18: 2.0, 21: -2.0}


BUILDINGS = [
    {
        "building_id": "BLD-A",
        "building_name": "综合教学楼A",
        "building_type": "teaching",
        "base_electricity": 235.0,
        "base_water": 9.2,
        "base_hvac": 78.0,
        "equipment_id": "AHU-A-01",
    },
    {
        "building_id": "BLD-B",
        "building_name": "行政办公楼B",
        "building_type": "office",
        "base_electricity": 198.0,
        "base_water": 7.4,
        "base_hvac": 65.0,
        "equipment_id": "CH-B-02",
    },
    {
        "building_id": "BLD-C",
        "building_name": "图书信息楼C",
        "building_type": "library",
        "base_electricity": 256.0,
        "base_water": 8.5,
        "base_hvac": 82.0,
        "equipment_id": "CT-C-03",
    },
    {
        "building_id": "BLD-D",
        "building_name": "科研实验楼D",
        "building_type": "lab",
        "base_electricity": 286.0,
        "base_water": 10.8,
        "base_hvac": 95.0,
        "equipment_id": "FCU-D-04",
    },
]

TIME_SLOTS = [0, 3, 6, 9, 12, 15, 18, 21]
FIELD_NAMES = [
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
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _seasonal_temp(day_index: int) -> float:
    """Linearly interpolate the monthly-mean temperature curve by day index."""
    anchors = TEMP_ANCHORS
    if day_index <= anchors[0][0]:
        (d0, t0), (d1, t1) = anchors[0], anchors[1]
        slope = (t1 - t0) / (d1 - d0)
        return t0 + slope * (day_index - d0)
    if day_index >= anchors[-1][0]:
        return anchors[-1][1]
    for (d0, t0), (d1, t1) in zip(anchors, anchors[1:]):
        if d0 <= day_index <= d1:
            ratio = (day_index - d0) / (d1 - d0)
            return t0 + (t1 - t0) * ratio
    return anchors[-1][1]


def _winter_break_factors(building_type: str, month: int) -> tuple[float, float]:
    """(occupancy_factor, load_factor) for the Jan/Feb winter vacation.

    During winter break / Spring Festival occupancy drops sharply, but heating
    keeps running for frost protection so the energy load is only mildly reduced
    (occupancy ≠ load). Labs stay near-normal.
    """
    if month not in {1, 2}:
        return 1.0, 1.0
    if building_type in {"teaching", "office"}:
        return 0.5, 0.9
    if building_type == "library":
        return 0.75, 0.95
    return 0.9, 1.0  # lab


def main() -> None:
    random.seed(42)
    total_days = (DATA_END.date() - DATA_START.date()).days + 1
    rows = []
    record_index = 1

    for day_offset in range(total_days):
        current_day = DATA_START + timedelta(days=day_offset)
        month = current_day.month
        is_weekend = current_day.weekday() >= 5
        seasonal_temp = _seasonal_temp(day_offset)

        for building_index, building in enumerate(BUILDINGS):
            occupancy_break, load_break = _winter_break_factors(building["building_type"], month)
            for slot in TIME_SLOTS:
                timestamp = current_day.replace(hour=slot)
                environment_temp = round(
                    seasonal_temp + DIURNAL_OFFSET[slot] + random.uniform(-1.2, 1.2), 1
                )

                # Bimodal thermal load: heating when cold, cooling when hot.
                heating_degree = max(0.0, HEAT_BALANCE_C - environment_temp)
                cooling_degree = max(0.0, environment_temp - COOL_BALANCE_C)
                thermal_factor = 1 + heating_degree * HEAT_SENSITIVITY + cooling_degree * COOL_SENSITIVITY

                peak_factor = 1.22 if slot in {9, 12, 15} else 0.92 if slot in {0, 3, 21} else 1.0
                workload_factor = 1 + building_index * 0.06
                if is_weekend and building["building_type"] in {"teaching", "office"}:
                    schedule_factor = 0.88
                    occupancy_factor = 0.58
                elif is_weekend and building["building_type"] == "library":
                    schedule_factor = 0.98
                    occupancy_factor = 0.9
                else:
                    schedule_factor = 1.0
                    occupancy_factor = 1.0
                schedule_factor *= load_break
                noise = random.uniform(-0.08, 0.08)

                humidity = round(
                    _clamp(48 + (environment_temp - 10) * 0.7 + random.uniform(-7, 7), 35, 90), 1
                )
                occupancy = round(
                    _clamp(
                        (
                            (20 + slot * 3.5 + building_index * 7 + random.uniform(-8, 10))
                            * occupancy_factor
                            * occupancy_break
                        )
                        if slot in {6, 9, 12, 15, 18}
                        else (
                            (5 + building_index * 2 + random.uniform(-2, 3))
                            * occupancy_factor
                            * occupancy_break
                        ),
                        0,
                        95,
                    ),
                    1,
                )

                hvac = (
                    building["base_hvac"]
                    * peak_factor
                    * workload_factor
                    * schedule_factor
                    * thermal_factor
                    * (1 + noise)
                )
                electricity = (
                    building["base_electricity"]
                    * peak_factor
                    * workload_factor
                    * schedule_factor
                    * thermal_factor
                    * (1 + noise * 0.9)
                )
                water = (
                    building["base_water"]
                    * (0.85 + peak_factor * 0.2)
                    * (0.92 + occupancy_factor * 0.08)
                    * (1 + noise * 0.4)
                )
                # Thermal energy served / hvac ≈ COP (kept ≈3 for self-consistency).
                cooling_load = hvac * (3.0 + random.uniform(-0.18, 0.24))

                abnormal = (day_offset + slot + building_index) % 17 == 0 or (
                    building["building_id"] == "BLD-D" and slot == 15 and day_offset % 9 == 0
                )
                abnormal = abnormal or (
                    current_day.month == 5 and 24 <= current_day.day <= 28 and slot in {12, 15}
                )
                abnormal = abnormal or (
                    building["building_id"] == "BLD-C" and slot == 21 and day_offset % 23 == 0
                )
                abnormal = abnormal or (
                    building["building_id"] == "BLD-B" and is_weekend and slot in {9, 12} and day_offset % 19 == 0
                )
                if abnormal:
                    electricity *= 1.28
                    hvac *= 1.17
                    cooling_load *= 0.96

                rows.append(
                    {
                        "record_id": f"R{record_index:05d}",
                        "building_id": building["building_id"],
                        "building_name": building["building_name"],
                        "building_type": building["building_type"],
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "electricity_kwh": round(electricity, 2),
                        "water_m3": round(water, 2),
                        "hvac_kwh": round(hvac, 2),
                        "cooling_load_kwh": round(cooling_load, 2),
                        "chilled_water_supply_temp_c": round(6.8 + random.uniform(-0.8, 0.7), 1),
                        "chilled_water_return_temp_c": round(11.8 + random.uniform(-0.9, 1.0), 1),
                        "environment_temp_c": environment_temp,
                        "humidity_rh": humidity,
                        "occupancy_density_per_100m2": occupancy,
                        "equipment_id": building["equipment_id"],
                        "equipment_status": "abnormal" if abnormal else "normal",
                    }
                )
                record_index += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

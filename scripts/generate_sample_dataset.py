from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "samples" / "energy_records.csv"


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


def main() -> None:
    random.seed(42)
    start = datetime(2026, 3, 1, 0, 0, 0)
    rows = []
    record_index = 1

    for day_offset in range(35):
        current_day = start + timedelta(days=day_offset)
        seasonal_temp = 16.0 + day_offset * 0.18

        for building_index, building in enumerate(BUILDINGS):
            for slot in TIME_SLOTS:
                timestamp = current_day.replace(hour=slot)
                peak_factor = 1.22 if slot in {9, 12, 15} else 0.92 if slot in {0, 3, 21} else 1.0
                workload_factor = 1 + building_index * 0.06
                noise = random.uniform(-0.08, 0.08)

                environment_temp = round(seasonal_temp + slot * 0.22 + random.uniform(-1.2, 1.2), 1)
                humidity = round(_clamp(58 - day_offset * 0.2 + random.uniform(-7, 7), 32, 88), 1)
                occupancy = round(
                    _clamp(
                        (20 + slot * 3.5 + building_index * 7 + random.uniform(-8, 10))
                        if slot in {6, 9, 12, 15, 18}
                        else (5 + building_index * 2 + random.uniform(-2, 3)),
                        0,
                        95,
                    ),
                    1,
                )

                hvac = building["base_hvac"] * peak_factor * workload_factor * (1 + noise)
                electricity = building["base_electricity"] * peak_factor * workload_factor * (1 + noise * 0.9)
                water = building["base_water"] * (0.85 + peak_factor * 0.2) * (1 + noise * 0.4)
                cooling_load = hvac * (3.0 + random.uniform(-0.18, 0.24))

                abnormal = (day_offset + slot + building_index) % 23 == 0 or (
                    building["building_id"] == "BLD-D" and slot == 15 and day_offset % 9 == 0
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


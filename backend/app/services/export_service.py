from datetime import datetime
from io import StringIO
from typing import Optional

import pandas as pd

from app.services.data_loader import get_filtered_dataset


def build_csv_content(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> str:
    """Build CSV string from filtered dataset."""
    frame = get_filtered_dataset(
        building_id=building_id, start_time=start_time, end_time=end_time
    )

    if frame.empty:
        return ""

    export_frame = frame.copy()
    if "timestamp" in export_frame.columns:
        export_frame["timestamp"] = export_frame["timestamp"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    buffer = StringIO()
    export_frame.to_csv(buffer, index=False)
    return buffer.getvalue()


def build_export_filename(
    building_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> str:
    """Generate a descriptive filename for the export."""
    parts = ["energy_records"]

    if building_id:
        parts.append(building_id)
    if start_time is not None:
        parts.append("from-{0}".format(start_time.strftime("%Y%m%d-%H%M")))
    if end_time is not None:
        parts.append("to-{0}".format(end_time.strftime("%Y%m%d-%H%M")))

    if len(parts) == 1:
        parts.append("export")

    return "{0}.csv".format("_".join(parts))

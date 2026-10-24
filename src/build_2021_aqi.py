"""Build a city-level hourly AQI series from CPCB station AQI records.

The source files contain hourly AQI for 39 Delhi monitoring stations.
For each hour, this script averages the stations that reported a value.
"""

import csv
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


YEAR = 2021
MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "aqi_target" / "2021" / "cpcb_station_source_2017_2023"
OUTPUT_FILE = PROJECT_ROOT / "aqi_target" / "2021" / "delhi_2021_hourly_station_mean.csv"


def read_station_file(path, totals):
    current_year = None
    current_month = None
    seen_hours = set()

    with path.open("r", newline="", encoding="utf-8-sig") as source_file:
        for row in csv.reader(source_file):
            if len(row) < 2:
                continue

            if row[0] == "Year" and row[1].isdigit():
                current_year = int(row[1])
                current_month = None
                continue

            month_header = re.fullmatch(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)-(\d{4})",
                row[0],
            )
            if month_header:
                month_name, year_text = month_header.groups()
                current_month = MONTHS[month_name] if int(year_text) == YEAR else None
                continue

            if current_year != YEAR or current_month is None:
                continue

            try:
                day = int(float(row[0]))
            except ValueError:
                continue

            for hour, value_text in enumerate(row[1:25]):
                if not value_text.strip():
                    continue

                try:
                    value = float(value_text)
                    timestamp = datetime(YEAR, current_month, day, hour)
                except ValueError:
                    continue

                if not 0 <= value <= 500:
                    raise ValueError(f"AQI outside 0-500 in {path.name}: {value}")
                if timestamp in seen_hours:
                    raise ValueError(f"Duplicate station hour in {path.name}: {timestamp}")

                seen_hours.add(timestamp)
                totals[timestamp][0] += value
                totals[timestamp][1] += 1


def build_2021_aqi():
    station_files = sorted(SOURCE_DIR.glob("*.csv"))
    if len(station_files) != 39:
        raise FileNotFoundError(
            f"Expected 39 CPCB station CSV files in {SOURCE_DIR}, found {len(station_files)}"
        )

    totals = defaultdict(lambda: [0.0, 0])
    for station_file in station_files:
        read_station_file(station_file, totals)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    observed_hours = 0
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["Timestamp", "AQI", "Stations_reporting"])

        for hour_number in range(365 * 24):
            timestamp = datetime(YEAR, 1, 1) + timedelta(hours=hour_number)
            total, station_count = totals[timestamp]
            if station_count:
                aqi = f"{total / station_count:.3f}"
                observed_hours += 1
            else:
                aqi = ""
            writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), aqi, station_count])

    if observed_hours != 8741:
        raise ValueError(f"Expected 8,741 observed hours; found {observed_hours}")

    print(f"Wrote {OUTPUT_FILE}")
    print(f"Observed hours: {observed_hours} / 8760; missing hours: {8760 - observed_hours}")


if __name__ == "__main__":
    build_2021_aqi()

"""Historical 10 m wind near the Jacksonville pilot factories (ERA5 via Open-Meteo)."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_wind(lat=30.34, lon=-81.648, start="2025-05-16", end="2025-05-22", cache="data/cache"):
    params = {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "kmh", "timezone": "UTC", "models": "era5",
    }
    folder = Path(cache)
    folder.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
    path = folder / f"wind_{key}.json"
    if not path.exists():
        response = requests.get(URL, params=params, timeout=90)
        response.raise_for_status()
        path.write_text(response.text)
    payload = json.loads(path.read_text())
    if payload.get("error"):
        raise ValueError(payload.get("reason", "Wind API error"))
    data = pd.DataFrame(payload["hourly"])
    data["time"] = pd.to_datetime(data["time"], utc=True)
    for col in ("wind_speed_10m", "wind_direction_10m"):
        data[col] = pd.to_numeric(data[col], errors="coerce")
    metadata = {
        "provider": "ERA5 reanalysis through Open-Meteo Historical Weather API",
        "request": params,
        "returned_latitude": payload.get("latitude"),
        "returned_longitude": payload.get("longitude"),
        "units": payload.get("hourly_units", {}),
        "direction_convention": "Degrees clockwise from north; direction wind comes FROM",
    }
    return data, metadata


def closest_wind(data, when):
    timestamp = pd.Timestamp(when)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    delta = abs(data["time"] - timestamp)
    index = delta.idxmin()
    if delta.loc[index] > pd.Timedelta(minutes=90):
        return None
    row = data.loc[index]
    if pd.isna(row.wind_speed_10m) or pd.isna(row.wind_direction_10m):
        return None
    return {
        "wind_time_utc": row.time.isoformat(),
        "wind_speed_kmh": float(row.wind_speed_10m),
        "wind_from_deg": float(row.wind_direction_10m),
        "wind_toward_deg": float((row.wind_direction_10m + 180) % 360),
    }

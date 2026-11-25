"""Open-Meteo integration (no API key). Failures degrade gracefully (BR-07)."""
import logging
import time

import httpx

from app.core.config import get_settings

log = logging.getLogger(__name__)
_cache: dict[tuple, tuple[float, dict]] = {}


class WeatherUnavailable(Exception):
    pass


def _get(url: str, params: dict) -> dict:
    s = get_settings()
    key = (url, tuple(sorted(params.items())))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < s.WEATHER_CACHE_TTL_S:
        return hit[1]
    last: Exception | None = None
    for _ in range(2):  # one retry
        try:
            r = httpx.get(url, params=params, timeout=s.WEATHER_TIMEOUT_S)
            r.raise_for_status()
            data = r.json()
            _cache[key] = (time.time(), data)
            return data
        except (httpx.HTTPError, ValueError) as e:
            last = e
    if hit:  # serve stale data rather than failing
        log.warning("weather provider failed; serving stale cache: %s", last)
        return {**hit[1], "_stale": True}
    raise WeatherUnavailable("Weather provider is temporarily unavailable.") from last


def current_and_forecast(lat: float, lon: float, days: int = 7) -> dict:
    s = get_settings()
    data = _get(
        f"{s.WEATHER_BASE_URL}/forecast",
        {
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": days,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        },
    )
    cur = data.get("current", {})
    daily = data.get("daily", {})
    return {
        "source": "open-meteo",
        "stale": bool(data.get("_stale")),
        "current": {
            "temperature_c": cur.get("temperature_2m"),
            "humidity_pct": cur.get("relative_humidity_2m"),
            "precipitation_mm": cur.get("precipitation"),
            "wind_kmh": cur.get("wind_speed_10m"),
            "time": cur.get("time"),
        },
        "forecast": [
            {"date": d, "t_max": daily["temperature_2m_max"][i], "t_min": daily["temperature_2m_min"][i],
             "rain_mm": daily["precipitation_sum"][i], "rain_prob_pct": daily.get("precipitation_probability_max", [None] * 99)[i]}
            for i, d in enumerate(daily.get("time", []))
        ],
    }


def history(lat: float, lon: float, start: str, end: str) -> dict:
    s = get_settings()
    data = _get(
        f"{s.WEATHER_ARCHIVE_URL}/archive",
        {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end, "timezone": "auto",
         "daily": "temperature_2m_mean,precipitation_sum"},
    )
    daily = data.get("daily", {})
    return {
        "source": "open-meteo-archive",
        "days": [
            {"date": d, "t_mean": daily["temperature_2m_mean"][i], "rain_mm": daily["precipitation_sum"][i]}
            for i, d in enumerate(daily.get("time", []))
        ],
    }

"""Public USGS elevation and NWS forecasts with bounded, in-memory caching."""

from datetime import date, datetime
import json
import math
import os
import re
from threading import Lock
from time import monotonic
from urllib.error import URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class WeatherError(Exception):
    """An upstream service is unavailable or returned incomplete data."""


_cache = {}
_lock = Lock()


def fetch_json(url, ttl=900):
    # Only these upstream services may be requested, including NWS-provided URLs.
    if urlparse(url).scheme != "https" or urlparse(url).hostname not in {
        "api.weather.gov", "epqs.nationalmap.gov"
    }:
        raise WeatherError("The weather service returned an unexpected address.")
    with _lock:
        cached = _cache.get(url)
        if cached and monotonic() < cached[0]:
            return cached[1]
    agent = os.getenv("NWS_USER_AGENT", "SummitReady/0.1 (https://github.com/EpicQuibble/219_project)")
    try:
        request = Request(url, headers={"User-Agent": agent, "Accept": "application/json"})
        with urlopen(request, timeout=12) as response:
            data = json.load(response)
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise WeatherError("Live data is unavailable. Retry shortly, or select the clearly labeled offline demo.") from exc
    with _lock:
        # Bound memory even when many different summits are selected.
        if len(_cache) >= 256:
            _cache.pop(next(iter(_cache)))
        _cache[url] = (monotonic() + ttl, data)
    return data


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise WeatherError("A required weather or elevation value is missing.")
    return float(value)


def wind_mph(value):
    if isinstance(value, str):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)(?: to (\d+(?:\.\d+)?))? mph", value)
        if match:
            return max(float(v) for v in match.groups() if v is not None)
    if isinstance(value, dict) and value.get("unitCode") in {"wmoUnit:km_h-1", "wmoUnit:m_s-1", "wmoUnit:mi_h-1"}:
        scale = {"wmoUnit:km_h-1": 0.621371, "wmoUnit:m_s-1": 2.236936, "wmoUnit:mi_h-1": 1}
        return number(value.get("value")) * scale[value["unitCode"]]
    raise WeatherError("Forecast wind speed is missing or uses an unsupported format.")


def summarize(properties, day, summit_ft):
    """Use available 06:00-20:59 Eastern hours, retaining missing-data warnings."""
    try:
        periods = []
        for period in properties["periods"]:
            start = datetime.fromisoformat(period["startTime"])
            if start.date().isoformat() == day and 6 <= start.hour <= 20:
                periods.append(period)
        if not periods:
            raise WeatherError("No daytime forecast is available for that date. Choose a date in the next few days.")
        elevation = properties["elevation"]
        grid_ft = number(elevation.get("value"))
        if elevation["unitCode"] == "wmoUnit:m":
            grid_ft *= 3.28084
        elif elevation["unitCode"] != "wmoUnit:ft":
            raise WeatherError("The forecast reference elevation uses an unsupported unit.")
        temperatures, winds, probabilities, texts = [], [], [], []
        missing_precip = False
        for period in periods:
            temperature = number(period.get("temperature"))
            if period.get("temperatureUnit") == "C":
                temperature = temperature * 9 / 5 + 32
            elif period.get("temperatureUnit") != "F":
                raise WeatherError("Forecast temperature uses an unsupported unit.")
            temperatures.append(temperature)
            winds.append(wind_mph(period.get("windSpeed")))
            probability = (period.get("probabilityOfPrecipitation") or {}).get("value")
            if probability is None:
                missing_precip = True
            else:
                probability = number(probability)
                if not 0 <= probability <= 100:
                    raise WeatherError("Forecast precipitation probability is invalid.")
                probabilities.append(probability)
            texts.append(period.get("shortForecast", ""))
        # A deliberately rough planning heuristic, not a measured summit temperature.
        # Never warm the estimate when the grid's elevation exceeds the summit.
        adjustment = max(0, summit_ft - grid_ft) / 1000 * 3.5
        return {
            "grid_elevation_ft": round(grid_ft), "adjustment_f": round(adjustment, 1),
            "grid_low_f": round(min(temperatures), 1),
            "estimated_low_f": round(min(temperatures) - adjustment, 1),
            "estimated_high_f": round(max(temperatures) - adjustment, 1),
            "wind_mph": round(max(winds), 1),
            "precip_pct": None if missing_precip else max(probabilities),
            "snow_forecast": any(re.search(r"snow|sleet|freezing|ice", t, re.I) for t in texts),
            "thunder_forecast": any(re.search(r"thunder", t, re.I) for t in texts),
            "conditions": list(dict.fromkeys(texts)),
            "hours": len(periods), "day": day,
            "updated_at": properties.get("updateTime", "Not supplied"),
        }
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise WeatherError("The forecast response is incomplete. Retry shortly.") from exc


def live_weather(mountain, day):
    try:
        query = urlencode({"x": mountain["lon"], "y": mountain["lat"], "units": "Feet", "wkid": 4326, "includeDate": "false"})
        elevation = fetch_json(f"https://epqs.nationalmap.gov/v1/json?{query}", ttl=86400)
        summit_ft = number(elevation.get("value"))
        if not 0 < summit_ft < 7000:
            raise WeatherError("USGS did not return a usable New Hampshire summit elevation.")
        point = fetch_json(f"https://api.weather.gov/points/{mountain['lat']:.4f},{mountain['lon']:.4f}", ttl=86400)
        forecast_url = point["properties"]["forecastHourly"]
        forecast = fetch_json(forecast_url)
        result = summarize(forecast["properties"], day, summit_ft)
        result.update({"summit_elevation_ft": round(summit_ft), "mode": "live", "source_url": forecast_url})
        return result
    except (KeyError, TypeError, AttributeError) as exc:
        raise WeatherError("Live elevation or forecast data is incomplete. Retry shortly.") from exc


def demo_weather(day):
    """Synthetic data, identical for every selection. Never an automatic fallback."""
    date.fromisoformat(day)
    return {
        "summit_elevation_ft": 4000, "grid_elevation_ft": 2000,
        "adjustment_f": 7.0, "grid_low_f": 38.0,
        "estimated_low_f": 31.0, "estimated_high_f": 41.0,
        "wind_mph": 22.0, "precip_pct": 60.0,
        "snow_forecast": False, "thunder_forecast": False,
        "conditions": ["Chance Rain Showers"], "hours": 15, "day": day,
        "updated_at": "Synthetic fixture; no live forecast fetched",
        "mode": "demo", "source_url": None,
    }

"""Rule, upstream-data, and HTTP error-path checks; no network required."""
from copy import deepcopy
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from summitready.rules import checklist
from summitready.server import CATALOG, Handler, MOUNTAINS, make_plan
from summitready.weather import WeatherError, demo_weather, fetch_json, summarize, wind_mph

DAY = "2026-12-03"


def hourly_forecast():
    return {
        "elevation": {"value": 1000, "unitCode": "wmoUnit:ft"},
        "periods": [
            {"startTime": f"{DAY}T{hour:02}:00:00-05:00", "temperature": 50,
             "temperatureUnit": "F", "windSpeed": "10 to 20 mph",
             "probabilityOfPrecipitation": {"value": 30}, "shortForecast": "Rain"}
            for hour in range(24)
        ],
    }


class WeatherTests(unittest.TestCase):
    def test_adjusts_from_grid_height_not_sea_level_and_uses_daytime(self):
        forecast = hourly_forecast()
        forecast["periods"][0]["temperature"] = -20
        result = summarize(forecast, DAY, 4000)
        self.assertEqual(result["estimated_low_f"], 39.5)
        self.assertEqual(result["hours"], 15)
        self.assertEqual(result["wind_mph"], 20)

    def test_grid_above_summit_does_not_warm_estimate(self):
        self.assertEqual(summarize(hourly_forecast(), DAY, 500)["estimated_low_f"], 50)

    def test_celsius_and_meters(self):
        forecast = hourly_forecast()
        forecast["elevation"] = {"value": 304.8, "unitCode": "wmoUnit:m"}
        for period in forecast["periods"]:
            period.update(temperature=10, temperatureUnit="C")
        self.assertEqual(summarize(forecast, DAY, 4000)["estimated_low_f"], 39.5)

    def test_unknown_precip_is_not_zero(self):
        forecast = hourly_forecast()
        forecast["periods"][6]["probabilityOfPrecipitation"]["value"] = None
        self.assertIsNone(summarize(forecast, DAY, 4000)["precip_pct"])

    def test_missing_required_fields_and_unavailable_date(self):
        for key in ("temperature", "windSpeed"):
            forecast = hourly_forecast()
            forecast["periods"][6][key] = None
            with self.subTest(key=key), self.assertRaises(WeatherError):
                summarize(forecast, DAY, 4000)
        with self.assertRaises(WeatherError):
            summarize(hourly_forecast(), "2020-01-01", 4000)

    def test_wind_units_and_missing_wind(self):
        self.assertAlmostEqual(wind_mph({"value": 10, "unitCode": "wmoUnit:m_s-1"}), 22.36936)
        with self.assertRaises(WeatherError):
            wind_mph("unknown")

    def test_outage_is_an_error_not_demo(self):
        with patch("summitready.weather.urlopen", side_effect=URLError("offline")):
            with self.assertRaises(WeatherError):
                fetch_json("https://api.weather.gov/points/43.1234,-71.1234")


class RuleTests(unittest.TestCase):
    def test_freezing_and_wet_weather_additions(self):
        result = checklist(demo_weather(DAY))
        self.assertIn("Winter layers", str(result["weather_additions"]))
        self.assertIn("Waterproof pack liner", str(result["weather_additions"]))
        self.assertIn("Trail surface is unknown", str(result["notes"]))

    def test_technical_equipment_stays_conditional(self):
        result = checklist(demo_weather(DAY), technical=True)
        self.assertNotIn("Rope", str(result["essentials"] + result["weather_additions"]))
        self.assertIn("Rope system", str(result["trail_optionals"]))
        self.assertIn("verified technical route", str(result["trail_optionals"]))
        self.assertIn("marked technical terrain", str(result["notes"]))

    def test_mild_day_and_exposed_terrain(self):
        weather = demo_weather(DAY)
        weather.update(estimated_low_f=60, wind_mph=5, precip_pct=0)
        mild = checklist(weather, surface="dry")
        exposed = checklist(weather, surface="dry", exposed=True)
        self.assertEqual(mild["weather_additions"], [])
        self.assertIn("Headlamp", str(mild["essentials"]))
        self.assertIn("Wind protection", str(exposed["weather_additions"]))

    def test_hazard_and_partial_day_notes(self):
        weather = demo_weather(DAY)
        weather.update(thunder_forecast=True, hours=4)
        notes = str(checklist(weather)["notes"])
        self.assertIn("Reconsider exposed terrain", notes)
        self.assertIn("only 4 of 15", notes)


class CatalogAndInputTests(unittest.TestCase):
    def test_statewide_catalog(self):
        self.assertGreater(len(MOUNTAINS), 1700)
        self.assertEqual(len(MOUNTAINS), len(CATALOG["mountains"]))
        self.assertEqual(MOUNTAINS["871352"]["name"], "Mount Washington")
        self.assertIn("Mount Lafayette", [m["name"] for m in MOUNTAINS.values()])
        self.assertTrue(any("Monadnock" in m["name"] for m in MOUNTAINS.values()))

    def test_bad_inputs_rejected_before_network(self):
        valid = {"mountain": ["871352"], "day": [DAY]}
        invalid = [("mountain", ["fake"]), ("day", ["2026-02-30"]), ("day", ["20261203"]),
                   ("mode", ["made-up"]), ("surface", ["mud"]),
                   ("technical", ["yes"]), ("day", [DAY, DAY])]
        with patch("summitready.server.live_weather") as live:
            for key, value in invalid:
                params = deepcopy(valid)
                params[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    make_plan(params)
            live.assert_not_called()


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_home_and_demo(self):
        with urlopen(self.base) as response:
            self.assertIn(b"SummitReady", response.read())
        with urlopen(f"{self.base}/api/plan?mountain=871352&day={DAY}&mode=demo") as response:
            plan = json.load(response)
        self.assertEqual(plan["weather"]["mode"], "demo")
        self.assertIn("trail_optionals", plan["checklist"])

    def test_invalid_input_and_private_paths(self):
        for path, expected in (("/api/plan?mountain=invalid", 400), ("/.env", 404), ("/../AGENTS.md", 404)):
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as caught:
                    urlopen(self.base + path)
                self.assertEqual(caught.exception.code, expected)
                caught.exception.close()

    def test_live_failure_returns_readable_503(self):
        with patch("summitready.server.live_weather", side_effect=WeatherError("Live data is unavailable.")):
            with self.assertRaises(HTTPError) as caught:
                urlopen(f"{self.base}/api/plan?mountain=871352&day={DAY}")
            self.assertEqual(caught.exception.code, 503)
            self.assertIn("Live data is unavailable", json.load(caught.exception)["error"])
            caught.exception.close()


if __name__ == "__main__":
    unittest.main()

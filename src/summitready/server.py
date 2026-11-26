"""Local-only web server. Run with: python run.py"""

from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .rules import checklist
from .weather import WeatherError, demo_weather, live_weather

ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "data" / "mountains.json").read_text(encoding="utf-8"))
MOUNTAINS = {mountain["id"]: mountain for mountain in CATALOG["mountains"]}
STATIC = ROOT / "static"


def make_plan(params):
    def field(name, default=None):
        values = params.get(name, [default])
        if len(values) != 1 or values[0] is None:
            raise ValueError(f"Supply one {name} value.")
        return values[0]

    mountain = MOUNTAINS.get(field("mountain"))
    if mountain is None:
        raise ValueError("Choose a mountain from the New Hampshire summit list.")
    day = field("day")
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError:
        raise ValueError("Choose a valid forecast date (YYYY-MM-DD).") from None
    mode = field("mode", "live")
    surface = field("surface", "unknown")
    technical = field("technical", "false")
    exposed = field("exposed", "false")
    if mode not in {"live", "demo"}:
        raise ValueError("Weather mode must be live or demo.")
    if surface not in {"unknown", "dry", "snow", "ice"}:
        raise ValueError("Choose a valid trail surface.")
    if technical not in {"true", "false"} or exposed not in {"true", "false"}:
        raise ValueError("Terrain selections must be true or false.")
    weather = demo_weather(day) if mode == "demo" else live_weather(mountain, day)
    return {
        "mountain": mountain, "weather": weather,
        "checklist": checklist(weather, surface, technical == "true", exposed == "true"),
    }


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
        }
        if url.path in assets:
            filename, content_type = assets[url.path]
            self.reply(200, (STATIC / filename).read_bytes(), content_type)
        elif url.path == "/api/mountains":
            self.reply(200, CATALOG)
        elif url.path == "/api/plan":
            try:
                result = make_plan(parse_qs(url.query, keep_blank_values=True, max_num_fields=12))
                self.reply(200, result)
            except ValueError as exc:
                self.reply(400, {"error": str(exc)})
            except WeatherError as exc:
                self.reply(503, {"error": str(exc)})
        else:
            self.reply(404, {"error": "Page not found."})


def main():
    try:
        port = int(os.getenv("PORT", "8000"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise SystemExit("PORT must be a whole number between 1 and 65535.") from None
    host = os.getenv("HOST", "127.0.0.1")
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as exc:
        raise SystemExit(f"Cannot start SummitReady on {host}:{port}: {exc}") from None
    print(f"SummitReady: http://{host}:{port}", flush=True)
    print("Press Ctrl+C to stop. Live weather requires internet; demo mode works offline.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

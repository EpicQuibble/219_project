New Hampshire hikers waste time deciding what to pack for a mountain's conditions. The smallest version is one screen that turns a selected summit's elevation and weather into a basic gear checklist, with trail-dependent equipment listed separately.

# SummitReady

Select a mountain, a forecast day, and any known trail conditions. Get everyday essentials, weather additions, and trail optionals such as poles, traction, helmets, and a rope system, with reasons for each.

## Prerequisites

- Python **3.11+** and a modern browser; Git to clone.
- Internet for live NWS weather and USGS elevation. The explicit offline demo works without internet.
- Optional: Podman for the container.
- No packages, API keys, account, or build step required.

## Run without a container

```sh
git clone https://github.com/EpicQuibble/219_project.git
cd 219_project
python run.py
```

Open **http://127.0.0.1:8000**. Stop with **Ctrl+C**. On Windows, `py run.py` also works. Where Python 3 is named `python3`, use that instead of `python`.

Before the feature PR is merged, use `git clone --branch codex/summitready-mvp https://github.com/EpicQuibble/219_project.git` instead. The ordinary clone instructions apply after merging.

## Run with a container (optional)

From the repository root:

```sh
podman build -t summitready -f Containerfile .
podman run --rm -p 127.0.0.1:8000:8000 summitready
```

Open **http://127.0.0.1:8000**. The app binds to `0.0.0.0` inside the container; the port mapping exposes it only on your computer. Stop with Ctrl+C. Docker users can substitute `docker` for `podman`.

## Use it

1. Search by mountain or county, then select a summit. County names and GNIS IDs distinguish duplicate names, including duplicates in the same county.
2. Pick a forecast day in the next few days. Tomorrow is the default. The summary covers available **06:00–20:59 Eastern** hours and flags partial coverage.
3. Choose live data, or explicitly choose the synthetic offline demo.
4. Mark known surface conditions, exposed terrain, or technical terrain. These are user inputs, not detected conditions.
5. Click **Build my checklist**. Check items as you pack, or print. Checks reset with a new checklist or reload.

**Reproducible offline example:** select **Mount Washington — Coos County**, any valid date, **Offline demo**, and **Not checked yet**. Build the checklist.

Expected output: a synthetic-data banner, example elevation **4,000 ft**, estimated low **31°F**, grid wind **22 mph**, precipitation **60%**, everyday essentials, warm/winter layers, wind protection, waterproof pack liner, and separate trail-dependent options. The demo uses the same fictional elevation/weather for every mountain and date; it only tests the interface.

**Bad-input example:** choose a date outside forecast coverage in live mode. A readable error asks for a nearer date. Service outages show an error and allow an explicit switch to demo mode.

## Settings

Optional shell environment variables are listed in `.env.example`. The app **does not automatically load .env files**. No `MODEL_URL` is needed because the app uses no LLM.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Listening address; container uses `0.0.0.0`. |
| `PORT` | `8000` | Whole number from 1–65535. |
| `NWS_USER_AGENT` | `SummitReady/0.1 (https://github.com/EpicQuibble/219_project)` | Application identification for NWS. |

PowerShell example:

```powershell
$env:PORT = '8001'
python run.py
```

macOS/Linux: `PORT=8001 python3 run.py`.

## Data and estimates

- **1,734 named NH summits** from the public-domain [USGS GNIS download](https://www.usgs.gov/us-board-on-geographic-names/download-gnis-data), retrieved November 26, 2026. Includes named hills classified as `Summit`; excludes unnamed peaks, other feature classes, and primary-state records outside NH. This statewide source-based catalog cannot guarantee every possible mountain name. A named point does not establish public access or a trail.
- [USGS EPQS](https://epqs.nationalmap.gov/v1/docs/) estimates elevation at the GNIS coordinate; this may differ from published summit heights.
- [NWS](https://www.weather.gov/documentation/services-web-api) supplies hourly grid weather. The app subtracts **3.5°F per 1,000 ft above the grid reference elevation**, never warming the estimate if the grid is higher. This [standard-atmosphere approximation](https://www.nwcg.gov/publications/pms425-1/2-temperature) ignores inversions and local terrain. The reference elevation and adjustment are shown.
- Wind is maximum available hourly **grid sustained wind**, without a summit/gust correction. Precipitation is the highest hourly probability, not daily probability. Missing precipitation stays unknown; missing temperature, wind, or elevation stops the estimate.
- In-memory cache: weather up to 15 minutes; elevation and point lookup up to 24 hours. Original forecast update timestamps remain visible. Restart clears cache. Live errors never silently switch to demo data.

This rough preparation aid cannot determine whether a hike is safe. Weather cannot establish snow depth, technical gear requirements, stream levels, avalanche conditions, or closures. Review your route, [HikeSafe](https://www.hikesafe.com/knowledge-gear), and the [Higher Summits Forecast](https://mountwashington.org/weather/higher-summits-forecast/). Optionals may be essential on a particular route; technical equipment requires training.

## Development

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic data and local HTTP, with no external internet. Refresh the catalog only when needed (requires internet):

```sh
python scripts/import_mountains.py
```

The importer preserves GNIS IDs and coordinates and records source URL, retrieval time, and archive SHA-256 in `data/mountains.json`. Elevations are fetched only for the selected mountain.

Source: `src/summitready/`. Frontend: `static/`. Catalog: `data/`. See [SPEC.md](SPEC.md), [AGENTS.md](AGENTS.md), and [assignment evidence](docs/assignment.md).

Work on branches and merge through PRs. Record real outside feedback as an issue, then fix it in a PR with `Closes #<issue-number>` or explain why no change is appropriate. Automated testing is not an outside user.

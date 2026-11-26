# SummitReady MVP

New Hampshire hikers waste time deciding what to pack. One local web screen turns a selected summit's approximate elevation and forecast weather into a basic gear checklist, with trail-dependent equipment listed separately.

## In scope

- Search/select the statewide NH-primary-state `Summit` records from USGS GNIS, including named hills and stable IDs.
- Forecast day, user-reported surface (unknown/dry/snow/ice), exposed/technical terrain flags.
- USGS point elevation, NWS hourly weather, and an elevation-based temperature estimate.
- Available 06:00–20:59 Eastern hours, partial-day notices, and missing-data handling.
- Essentials, weather additions with reasons, and conditional trail options.
- Packing checkboxes, printing, explicit synthetic offline demo, readable errors.

## Out of scope

Trail catalog/navigation, scraping trail reports, detecting snow depth/access, avalanche assessment, safety rating, automatic technical equipment prescriptions, unnamed peaks, accounts, database, saved trips, LLM integration, hosting, overnight expeditions.

## Language and running

Python 3.11+ standard library (`http.server`, `urllib`, `json`, `unittest`), plain HTML/CSS/JavaScript. Run `python run.py`, visit `http://127.0.0.1:8000`. No dependency installation/build. Optional Containerfile; exact commands in README.

## Estimate

`estimated low = grid low − max(0, summit elevation − grid reference elevation) / 1000 × 3.5°F`.

Use the same adjustment for the high. Elevation is above sea level, not trail elevation gain. Never subtract the full summit elevation from an already elevated forecast. This approximation ignores inversions and terrain. Do not infer summit wind from elevation.

## Explainable rules

Application heuristics, not validated hiking standards or official NWS advice:

| Trigger | Result |
| --- | --- |
| Every selection | Navigation, light, food/water, spare warmth, rainwear, first aid, whistle, fire starter, knife, sun protection, emergency shelter. |
| Estimated low ≤45°F | Insulating layer, hat, gloves. |
| Estimated low ≤32°F | Winter layers, insulated water storage, winter-equipment review. |
| Grid wind ≥20 mph OR exposed terrain input | Wind protection for hands/face. |
| Hourly precipitation chance ≥30% OR unknown | Waterproof pack liner and dry socks. |
| Estimated low ≥70°F | Extra water capacity. |
| Reported snow/ice, freezing estimate, OR wintry forecast | Review actual surface, traction, snowshoes, winter equipment. |
| Technical terrain input | Verify route equipment and skills. |
| Grid wind ≥35 mph OR thunder mentioned | Reconsider exposure; check official mountain forecast. |
| Fewer than 15 daytime periods | Disclose partial-day coverage. |

Separate optionals: poles, water treatment, traction, snowshoes, helmet, rope/harness/protection system, mountaineering equipment. Their conditions are described; elevation alone never establishes technical gear needs.

## Data failures

Bundled names permit offline selection. Live mode needs numeric USGS and NWS grid elevations, valid temperatures/wind, and at least one daytime period for the date. Missing/unsupported required data returns readable 503; invalid user input returns 400 before external requests. Missing precipitation stays unknown. Demo always shows a synthetic-data banner and never activates automatically.

## Acceptance checks

1. A clean copy runs with the README commands.
2. Statewide names can be searched; county and GNIS ID distinguish duplicates.
3. Live results disclose source, timestamp, reference elevation, and adjustment.
4. Offline example produces 31°F / 22 mph / 60% and synthetic 4,000-ft elevation.
5. Invalid input and unavailable services show readable errors.
6. Terrain/surface inputs affect relevant notes/additions; technical options remain conditional.
7. Tests cover estimates and error paths; a separate real person follows README and records feedback as an issue.

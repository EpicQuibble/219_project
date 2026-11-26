# Verification — November 26, 2026

Implementation PR: https://github.com/EpicQuibble/219_project/pull/1

## Executed checks

- Windows, Python 3.14.6: all **16 tests** pass with `python -m unittest discover -s tests -v`.
- Cloned the published `codex/summitready-mvp` branch from GitHub into a fresh folder, ran the same 16 tests successfully, then started it with the exact README command, `python run.py`. No dependencies or extra setup required.
- Fresh-clone server: homepage and all 1,734 bundled summit records returned successfully. Explicit offline demo returned the documented 31°F / 22 mph / 60% values.
- Live HTTP round trip, selected date November 27: Mount Washington returned approximate point elevation 6,275 ft, estimated low 26.8°F, and grid wind 45 mph; Monadnock Mountain returned 3,165 ft, 33.4°F, and 15 mph. These are dated test results, not current advice or official summit height claims.
- An unavailable date (`2020-01-01`) returned a readable coverage error. Invalid `PORT` returned a concise setting error, without a traceback.
- Browser: summit search, empty results disabling submission, duplicate names in the same county disambiguated with GNIS IDs, live checklist, explicit demo banner, technical-terrain note, packing progress/reset, stale-result notice, and recovery from an unavailable forecast date.
- Captured [live forecast evidence](screenshots/live-checklist.jpg) from the working browser screen.
- `node --check static/app.js` and `git diff --check` passed.
- GitHub showed both Python CI matrix checks passing for the implementation commit.

## Limits and remaining evidence

- Container execution was **not verified**. Podman is absent; Docker CLI is installed, but its engine is stopped. The optional Containerfile is supplied for later testing.
- Browser verification used the available narrow in-app browser viewport. Desktop sizing and the operating system print dialog were not separately exercised.
- The outside-user test is **not complete**. A real person besides the author must follow README; their feedback must become an issue, then a fixing PR or reasoned reply.
- PR #1 is open for review and must be merged through GitHub. Blackboard submission and the actual presentation remain human steps.
- Automated testing and agent-driven browser testing do not count as the outside tester.

# SummitReady agent instructions

- Build one small local web tool for the DS219 portfolio assignment.
- Use Python 3.11+ and its standard library; plain HTML, CSS, and JavaScript.
- Cover the statewide USGS GNIS list of named New Hampshire summits, not just popular hikes. Keep the importer reproducible and cite the source and retrieval date.
- Produce an approximate gear checklist from elevation and forecast weather. Explain every rule and distinguish estimates from observations.
- Put route-specific equipment (including ropes) in a separate optional section with conditions for use. Never infer technical trail requirements from elevation alone.
- Never label a route safe or claim that weather establishes snow depth, stream levels, closures, avalanche conditions, or accessibility.
- Keep live and synthetic demo data visibly distinct. Never silently replace failed live requests with demo data.
- Handle bad input, missing weather fields, network outages, and invalid settings without a traceback in the browser.
- No accounts, database, LLM integration, paid APIs, or deployment in this MVP.
- No secrets in source, logs, or commits. Ignore .env and generated files; provide .env.example.
- Work on codex/ branches. Use descriptive commits and a pull request to merge into main. Do not invent commits, PRs, outside testers, or feedback.
- Verify the weather rules, error paths, and a fresh copy following the README. Document any checks that could not run.

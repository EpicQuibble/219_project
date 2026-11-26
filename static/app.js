"use strict";
const byId = id => document.getElementById(id);
const form = byId("planner");
let mountains = [];
const duplicateLabels = new Map();
let hasResult = false;

function setError(message) {
  byId("error").textContent = message;
  byId("error").hidden = !message;
}

function locationNote() {
  const mountain = mountains.find(m => m.id === byId("mountain").value);
  byId("location").textContent = mountain ? `${mountain.county} County · ${mountain.lat.toFixed(4)}, ${mountain.lon.toFixed(4)} · GNIS ${mountain.id}` : "No matching summits. Try another search.";
}

function filterMountains() {
  const selected = byId("mountain").value;
  const search = byId("search").value.trim().toLowerCase();
  const matches = mountains.filter(m => `${m.name} ${m.county}`.toLowerCase().includes(search));
  byId("mountain").replaceChildren(...matches.map(m => {
    const suffix = duplicateLabels.get(`${m.name}|${m.county}`) > 1 ? ` · GNIS ${m.id}` : "";
    return new Option(`${m.name} — ${m.county} County${suffix}`, m.id);
  }));
  if (matches.some(m => m.id === selected)) byId("mountain").value = selected;
  byId("match-count").textContent = `(${matches.length.toLocaleString()})`;
  byId("mountain").disabled = matches.length === 0;
  byId("generate").disabled = matches.length === 0;
  locationNote();
}

function renderItems(id, items) {
  const container = byId(id);
  container.replaceChildren();
  if (!items.length) {
    const p = document.createElement("p");
    p.className = "subtle";
    p.textContent = "No extra items triggered by these rules. Review the essentials and trail options.";
    container.append(p);
  }
  for (const [title, reason] of items) {
    const label = document.createElement("label");
    label.className = "gear";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.addEventListener("change", updateProgress);
    const text = document.createElement("span");
    const strong = document.createElement("strong");
    strong.textContent = title;
    const detail = document.createElement("small");
    detail.textContent = reason;
    text.append(strong, detail);
    label.append(checkbox, text);
    container.append(label);
  }
}

function updateProgress() {
  const checked = document.querySelectorAll(".gear input:checked").length;
  byId("progress").textContent = `${checked} packed`;
}

function renderPlan(plan) {
  const {mountain, weather: w, checklist: list} = plan;
  byId("empty").hidden = true;
  byId("result").hidden = false;
  byId("demo-banner").hidden = w.mode !== "demo";
  byId("stale-banner").hidden = true;
  byId("result-source").textContent = w.mode === "demo" ? "SYNTHETIC DEMO / NOT A MOUNTAIN FORECAST" : "NWS GRID FORECAST / ELEVATION-BASED ESTIMATE";
  byId("result-name").textContent = mountain.name;
  byId("result-day").textContent = `${w.day} · ${mountain.county} County · Available hours from 06:00–20:59 Eastern`;
  byId("temp").textContent = `${Math.round(w.estimated_low_f)}°F`;
  byId("wind").textContent = `${w.wind_mph} mph`;
  byId("precip").textContent = w.precip_pct === null ? "Unknown" : `${w.precip_pct}%`;
  byId("elevation").textContent = `${w.mode === "demo" ? "Synthetic example elevation" : "Approximate USGS point elevation"}: ${w.summit_elevation_ft.toLocaleString()} ft · ${w.hours}/15 daytime forecast hours`;
  byId("estimate").textContent = `Forecast grid elevation: ${w.grid_elevation_ft.toLocaleString()} ft. Grid low: ${w.grid_low_f}°F. We subtract 3.5°F per 1,000 ft the summit rises above the grid elevation: ${w.adjustment_f}°F here. This rough rule ignores inversions and local terrain effects. Grid wind is maximum sustained forecast wind in the available hours; no summit wind or gust correction is applied. Precipitation is the highest hourly chance, not a whole-day probability.`;
  byId("conditions").textContent = `Forecast conditions: ${w.conditions.join("; ")}.`;
  byId("updated").textContent = `Forecast update: ${w.updated_at}. Live weather is cached for up to 15 minutes.`;
  byId("forecast-link").hidden = !w.source_url;
  if (w.source_url) byId("forecast-link").href = w.source_url;
  renderItems("essentials", list.essentials);
  renderItems("weather-additions", list.weather_additions);
  renderItems("trail-optionals", list.trail_optionals);
  byId("notes").replaceChildren(...list.notes.map(note => {
    const li = document.createElement("li");
    li.textContent = note;
    return li;
  }));
  updateProgress();
  hasResult = true;
}

form.addEventListener("input", event => {
  if (event.target.id === "search") filterMountains();
  if (event.target.id === "mountain") locationNote();
  if (hasResult) byId("stale-banner").hidden = false;
});

form.addEventListener("submit", async event => {
  event.preventDefault();
  setError("");
  byId("generate").disabled = true;
  byId("status").textContent = "Building your checklist… Live sources can take a few seconds.";
  // Freeze the submitted settings while waiting, so the result matches the form.
  const params = new URLSearchParams(new FormData(form));
  params.set("technical", String(byId("technical").checked));
  params.set("exposed", String(byId("exposed").checked));
  const fields = [...form.elements].filter(el => el !== byId("generate"));
  const disabledStates = fields.map(el => el.disabled);
  fields.forEach(el => { el.disabled = true; });
  try {
    const response = await fetch(`/api/plan?${params}`, {signal: AbortSignal.timeout(65000)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The checklist could not be built.");
    renderPlan(data);
    byId("status").textContent = "Checklist ready. Check off items as you pack; checks reset with each new checklist.";
  } catch (error) {
    setError(error.name === "TimeoutError" ? "The request took too long. Retry or choose the offline demo." : error.message);
    byId("status").textContent = "";
    if (hasResult) byId("stale-banner").hidden = false;
  } finally {
    fields.forEach((el, index) => { el.disabled = disabledStates[index]; });
    byId("generate").disabled = !byId("mountain").value;
  }
});
byId("print").addEventListener("click", () => window.print());

async function init() {
  // Derive tomorrow's date in New Hampshire even if the browser is elsewhere.
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", {timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit"}).formatToParts(new Date()).map(p => [p.type, p.value]));
  const tomorrow = new Date(`${parts.year}-${parts.month}-${parts.day}T12:00:00Z`);
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  byId("day").value = tomorrow.toISOString().slice(0, 10);
  try {
    const response = await fetch("/api/mountains");
    if (!response.ok) throw new Error("The summit catalog could not load. Reload the page.");
    const data = await response.json();
    mountains = data.mountains;
    for (const mountain of mountains) {
      const key = `${mountain.name}|${mountain.county}`;
      duplicateLabels.set(key, (duplicateLabels.get(key) || 0) + 1);
    }
    filterMountains();
    byId("mountain").value = "871352"; // Official GNIS ID for Mount Washington.
    locationNote();
    byId("catalog-info").textContent = `${mountains.length.toLocaleString()} named NH summits. Search by name or county.`;
    byId("coverage").textContent = `${data.coverage} Catalog retrieved ${data.retrieved_at.slice(0, 10)}. Names and coordinates do not confirm public access or a hiking trail.`;
  } catch (error) {
    setError(error.message);
    byId("catalog-info").textContent = "Summit catalog unavailable.";
  }
}
init();

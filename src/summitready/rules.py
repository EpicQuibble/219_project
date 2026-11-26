"""Small deterministic checklist rules. Thresholds are planning heuristics."""


def checklist(weather, surface="unknown", technical=False, exposed=False):
    essentials = [
        ("Map and compass", "Carry an offline route map and know how to navigate."),
        ("Headlamp and spare power", "Delays and emergencies can extend a day hike."),
        ("Water and extra food", "Plan for your route length and an unexpected delay."),
        ("Warm spare layers", "Mountain conditions can change in any season."),
        ("Rain jacket and rain pants", "Carry weather protection even with a dry forecast."),
        ("First aid kit", "Include personal medication and blister care."),
        ("Whistle", "Carry a way to signal for help."),
        ("Fire starter", "Carry emergency supplies and follow local fire restrictions."),
        ("Pocket knife or multitool", "A basic repair and emergency tool."),
        ("Sun protection", "Bring sunglasses, sunscreen, and a suitable hat."),
        ("Emergency shelter", "Carry a bivy or other emergency shelter and know how to use it."),
    ]
    additions, notes = [], []
    low = weather["estimated_low_f"]
    if low <= 45:
        additions.append(("Insulating layer, warm hat, and gloves", f"Estimated daytime low is {low:g}°F (rule: 45°F or colder)."))
    if low <= 32:
        additions.append(("Winter layers and insulated water storage", "The estimate reaches freezing; review winter preparation and current trail reports."))
    if weather["wind_mph"] >= 20 or exposed:
        additions.append(("Wind protection for hands and face", "Forecast grid wind is at least 20 mph, or you marked the route exposed."))
    if weather["precip_pct"] is None or weather["precip_pct"] >= 30:
        additions.append(("Waterproof pack liner and dry spare socks", "Precipitation chance is unknown or at least 30% in a forecast hour."))
    if low >= 70:
        additions.append(("Extra water capacity", "Even the estimated low is at least 70°F; account for heat and exertion."))
    frozen = surface in {"snow", "ice"} or low <= 32 or weather["snow_forecast"]
    optionals = [
        ("Trekking poles", "Optional support on steep, uneven terrain and long descents."),
        ("Water treatment", "For routes where you plan to refill from natural water sources."),
        ("Traction devices", "Match traction to verified ice, slope, and exposure; microspikes do not suit every icy route."),
        ("Snowshoes", "For verified deep or unconsolidated snow; forecast temperature cannot determine snow depth."),
        ("Helmet", "For a route with rockfall or technical scrambling hazards, based on a route description."),
        ("Rope system, harness, and protection", "Only for a verified technical route that requires roped travel, with trained partners. A rope alone is not a complete system."),
        ("Mountaineering equipment", "Crampons and ice axe may be required on technical snow or ice terrain; route assessment and practiced skills are essential."),
    ]
    if frozen:
        notes.append("Cold, snow, or ice triggers a winter-equipment review. Verify the actual surface and terrain before choosing traction, snowshoes, or mountaineering equipment.")
    if surface == "unknown":
        notes.append("Trail surface is unknown. Check recent trail reports; weather does not establish ground conditions.")
    if technical:
        notes.append("You marked technical terrain. Verify the route's equipment and skill requirements; rope and helmet options are not a complete technical packing list.")
    if weather["wind_mph"] >= 35 or weather["thunder_forecast"]:
        notes.append("Strong grid winds or thunderstorms appear in this forecast. Reconsider exposed terrain and review the official mountain forecast; extra gear does not resolve the hazard.")
    if weather["hours"] < 15:
        notes.append(f"Partial day: only {weather['hours']} of 15 daytime forecast hours are available. Earlier or missing hours are not included.")
    notes.append("Summit wind may exceed grid wind. This estimate does not assess closures, stream crossings, avalanche conditions, or whether the hike is appropriate.")
    return {"essentials": essentials, "weather_additions": additions, "trail_optionals": optionals, "notes": notes}

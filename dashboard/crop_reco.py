# dashboard/crop_reco.py

def month_to_season(month: int) -> str:
    # Simple Indian season mapping (adjust if needed)
    if month in (6, 7, 8, 9):      # monsoon
        return "kharif"
    if month in (10, 11, 12, 1, 2):
        return "rabi"
    return "zaid"  # 3,4,5


CROPS = [
    # name, moisture_min, moisture_max, seasons, irrigation_required, reason
    ("Paddy (Rice)", 55, 100, {"kharif", "rabi"}, True, "Needs high soil moisture / standing water conditions."),
    ("Sugarcane", 50, 100, {"kharif", "rabi", "zaid"}, True, "High water requirement; good if moisture and irrigation are available."),
    ("Maize", 35, 60, {"kharif", "rabi"}, False, "Performs well in moderate moisture; avoid waterlogging."),
    ("Cotton", 25, 50, {"kharif"}, False, "Works in moderate-low moisture; sensitive to excess water."),
    ("Groundnut", 20, 45, {"kharif", "rabi"}, False, "Good for low to moderate moisture; avoid heavy waterlogging."),
    ("Millets (Ragi/Bajra)", 10, 35, {"kharif", "zaid"}, False, "Drought tolerant; suitable for low soil moisture."),
    ("Pulses (Green gram/Black gram)", 15, 40, {"kharif", "rabi", "zaid"}, False, "Lower water requirement; good for dry conditions."),
    ("Vegetables (Okra/Brinjal)", 35, 65, {"kharif", "rabi", "zaid"}, True, "Needs consistent moisture; better with irrigation."),
]


def recommend_crops(soil_moisture: float, month: int, irrigation: bool):
    """
    Returns a sorted list of crop recommendations:
    [{"crop":..., "score":..., "reason":...}, ...]
    """
    season = month_to_season(month)
    results = []

    for (name, mn, mx, seasons, irrigation_required, reason) in CROPS:
        score = 0

        # Moisture fitness (most important)
        if mn <= soil_moisture <= mx:
            score += 60
        else:
            # penalize based on distance from range
            if soil_moisture < mn:
                score -= min(60, (mn - soil_moisture) * 2)
            if soil_moisture > mx:
                score -= min(60, (soil_moisture - mx) * 2)

        # Season fitness
        if season in seasons:
            score += 25
        else:
            score -= 15

        # Irrigation feasibility
        if irrigation_required and irrigation:
            score += 15
        elif irrigation_required and not irrigation:
            score -= 30

        results.append({
            "crop": name,
            "score": round(score, 2),
            "reason": reason,
            "season": season,
        })

    # sort best first
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]
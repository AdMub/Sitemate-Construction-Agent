import requests
from datetime import datetime

# Coordinates for your specific locations
LOCATIONS = {
    "Lekki, Lagos": {"lat": 6.4698, "lon": 3.5852},
    "Ibadan, Oyo": {"lat": 7.3775, "lon": 3.9470},
    "Abuja, FCT": {"lat": 9.0765, "lon": 7.3986}
}

def get_site_weather(location_name):
    """
    Fetches real-time weather from Open-Meteo (Free, No API Key).
    Returns a dictionary with temp, rain code, and engineering advice.
    """
    coords = LOCATIONS.get(location_name)
    if not coords:
        return None

    try:
        # Open-Meteo API URL
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true&daily=precipitation_sum,rain_sum&timezone=Africa%2FLagos"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        current = data.get("current_weather", {})
        temp = current.get("temperature", 0)
        weather_code = current.get("weathercode", 0) # WMO code
        
        # Determine Condition & Advice
        condition = "Clear"
        advice = "✅ Site conditions are optimal. Proceed with all works."
        is_safe = True
        
        # WMO Codes: 51-67 (Drizzle/Rain), 80-82 (Showers), 95-99 (Thunderstorm)
        if weather_code >= 51:
            condition = "Rainy 🌧️"
            advice = "⚠️ **RAIN ALERT:** Do NOT pour concrete or apply external paint. Cover delivered cement immediately."
            is_safe = False
        elif temp > 32:
            condition = "Very Hot ☀️"
            advice = "🔥 **HEAT WARNING:** High evaporation rate. Increase curing (watering) for concrete and blocks to prevent cracking."
        elif temp < 15:
            # Rare in Nigeria, but possible in Jos/Harmattan
            condition = "Cold ❄️" 
            advice = "❄️ **COLD WEATHER:** Concrete setting time will be delayed. Allow extra time before striking formwork."

        return {
            "temp": temp,
            "condition": condition,
            "advice": advice,
            "is_safe": is_safe
        }

    except Exception as e:
        return {"error": str(e)}
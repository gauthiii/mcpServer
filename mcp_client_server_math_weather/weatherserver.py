from mcp.server.fastmcp import FastMCP
from typing import Dict
import os, requests
from dotenv import load_dotenv
load_dotenv()

mcp=FastMCP("Weather")

OPENWEATHER_API = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

# @mcp.tool()
# async def get_weather(location: str)->str:
#     """_summary_
#     Get the weather location
#     """

#     return f"It is sunny in {location}."

@mcp.tool()
async def get_weather(city: str) -> Dict:
    """Fetch current weather + short forecast for a city. Returns a compact dict."""
    if not OPENWEATHER_KEY:
        raise RuntimeError("Missing OPENWEATHER_API_KEY")

    # current weather
    r_now = requests.get(
        f"{OPENWEATHER_API}/weather",
        params={"q": city, "appid": OPENWEATHER_KEY, "units": "metric"},
        timeout=15,
    )
    r_now.raise_for_status()
    now = r_now.json()

    # 5-day / 3-hour forecast (we'll take the next 4 slices ≈ 12h)
    r_fc = requests.get(
        f"{OPENWEATHER_API}/forecast",
        params={"q": city, "appid": OPENWEATHER_KEY, "units": "metric", "cnt": 4},
        timeout=15,
    )
    r_fc.raise_for_status()
    fc = r_fc.json()

    def pick(obj, *keys):  # tiny helper to keep payload small
        return {k: obj.get(k) for k in keys}

    current = {
        "city": now.get("name"),
        "country": now.get("sys", {}).get("country"),
        "temp_c": now.get("main", {}).get("temp"),
        "feels_like_c": now.get("main", {}).get("feels_like"),
        "humidity_pct": now.get("main", {}).get("humidity"),
        "wind_mps": now.get("wind", {}).get("speed"),
        "conditions": now.get("weather", [{}])[0].get("description"),
        "icon": now.get("weather", [{}])[0].get("icon"),
    }

    forecast = []
    for item in fc.get("list", []):
        forecast.append({
            "time_utc": item.get("dt_txt"),
            "temp_c": item.get("main", {}).get("temp"),
            "conditions": item.get("weather", [{}])[0].get("description"),
        })

    return {"current": current, "forecast": forecast}


if __name__=="__main__":
    mcp.run(transport="streamable-http")


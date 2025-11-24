#自制高德天氣MCP服務端。
import json
import httpx
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherServer")
AMAP_API_BASE = "https://restapi.amap.com/v3/weather/weatherInfo"
AMAP_API_KEY = ""  # 請填寫你的高德API Key


async def fetch_weather(city: str) -> Dict[str, Any] | None:
    """
    獲取某個城市的天氣信息。
    :param city: 要獲取天氣信息的城市。
    :return: 包含天氣信息的字典，如果未找到則返回None。
    """
    params = {
        "city": city,
        "key": AMAP_API_KEY,
        "extensions": "base",  # 只查詢實時天氣
        "output": "JSON"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(AMAP_API_BASE, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching weather data: {e}")
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

def format_weather(data: dict[str, Any] | str) -> str:
    """
    將天氣數據格式化為易讀文本。
    :param data: 天氣數據（可以是字典或JSON字符串）
    :return: 格式化的天氣信息字符串。
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            return f"無效的天氣數據：{e}"

    if "error" in data:
        return f"無效的天氣數據：{data['error']}"

    if data.get("status") != "1" or not data.get("lives"):
        return "未能獲取天氣信息，請檢查城市名稱或API Key。"

    live = data["lives"][0]
    city = live.get("city", "未知")
    weather = live.get("weather", "未知")
    temperature = live.get("temperature", "未知")
    winddirection = live.get("winddirection", "未知")
    windpower = live.get("windpower", "未知")
    humidity = live.get("humidity", "未知")
    reporttime = live.get("reporttime", "未知")

    return (
        f"城市：{city}\n"
        f"天氣：{weather}\n"
        f"溫度：{temperature}°C\n"
        f"風向：{winddirection}\n"
        f"風力：{windpower}\n"
        f"濕度：{humidity}%\n"
        f"發布時間：{reporttime}"
    )

@mcp.tool()
async def query_weather(city: str) -> str:
    """
    輸入指定城市名，返回今日天氣查詢結果
    :param city: 城市名。
    :return: 格式化後的天氣信息
    """
    weather_data = await fetch_weather(city)
    return format_weather(weather_data)

if __name__ == "__main__":
    mcp.run(transport='stdio')

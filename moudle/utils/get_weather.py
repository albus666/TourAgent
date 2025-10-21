from typing import Optional, Dict, Any
import requests


def get_weather(location: str) -> Optional[Dict[str, Any]]:
    """
    根据经纬度坐标查询当前天气信息

    参数:
        location: 经纬度坐标，格式为 "经度,纬度"
                 例如: "113.63,34.75"

    返回:
        天气数据字典，包含温度、天气状况、湿度等信息
        失败返回 None
    """
    url = "https://devapi.qweather.com/v7/grid-weather/now"
    params = {
        "location": location,
        "key": "e7b2b82fc901488abcf0b4961b84bdfe",
        "lang": "zh"
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()['now']

    print(data)
    return data


if __name__ == '__main__':
    get_weather("113.63141920733915,34.75343885045448")

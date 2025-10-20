from typing import Optional, Dict

import requests


def get_loc(address: str) -> str:
    """
    获取地址的经纬度坐标

    参数:
        address: 待查询的地址（如：郑州、北京市海淀区等）

    返回:
        包含 lng（经度）和 lat（纬度）的字典，失败返回 None
        例如: {'lng': 113.625368, 'lat': 34.746611}
    """
    url = "https://api.map.baidu.com/geocoding/v3"
    params = {
        "output": "json",
        "ak": "Hu01H6gQJVUo2i0ZSoxjwUIw7Nw09WnE",
        "address": address
    }

    response = requests.get(url, params=params, timeout=10)  # 加个超时
    data = response.json()
    print(data['result']['location'])
    loc = f"{data['result']['location']['lat']},{data['result']['location']['lng']}"
    return loc


if __name__ == '__main__':
    result = get_loc('上海')
    print(result)

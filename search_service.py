import requests
import json
from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader
import os
import logging
from typing import Dict, Any, List
import uuid

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置Jinja2环境
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
logger.info(f"模板目录: {template_dir}")
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template('search_attraction.jinja2')

def get_attractions(city_list: list) -> dict:
    """
    获取多个城市的景点信息
    
    Args:
        city_list (list): 城市名称列表
        
    Returns:
        dict: 包含所有景点信息的字典
    """
    all_attractions = []
    
    for city in city_list:
        try:
            logger.info(f"开始处理城市: {city}")
            
            # 获取城市ID
            districtId = int(get_district_id(city))
            
            # 获取景点信息
            url = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"
            querystring = {"_fxpcqlniredt": "09031162419158778138", "x-traceID": "09031162419158778138-1742713344797-6843463"}

            payload = {
                "head": {
                    "cid": "09031162419158778138",
                    "ctok": "",
                    "cver": "1.0",
                    "lang": "01",
                    "sid": "8888",
                    "syscode": "999",
                    "auth": "",
                    "xsid": "",
                    "extension": []
                },
                "scene": "online",
                "districtId": districtId,
                "index": 1,
                "sortType": 1,
                "count": 10,
                "filter": {},
                "returnModuleType": "all"
            }
            headers = {
                "Content-Type": "application/json",
                "Cookie": "GUID=09031136319238214458",
                "Cookieorigin": "https://you.ctrip.com",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
                "Connection": "keep-alive"
            }

            logger.info(f"发送搜索请求: {url}")
            response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
            response.raise_for_status()
            result = response.json()
            
            # 获取景点列表
            attractions = result.get("attractionList", [])
            if not attractions:
                logger.warning(f"未找到景点数据: {city}")
                continue

            # 处理每个景点数据
            for attraction in attractions:
                if not isinstance(attraction, dict):
                    continue
                    
                # 获取景点卡片数据
                card_data = attraction.get("card", {})
                if not card_data:
                    continue
                
                # 构建景点信息
                attraction_info = {
                    "card": {
                        "poiName": card_data.get("poiName", "未知景点"),
                        "zoneName": card_data.get("zoneName", ""),
                        "sightLevelStr": card_data.get("sightLevelStr", ""),
                        "commentScore": card_data.get("commentScore", 0),
                        "commentCount": card_data.get("commentCount", 0),
                        "tagNameList": card_data.get("tagNameList", []),
                        "otherTagList": card_data.get("otherTagList", []),
                        "isFree": card_data.get("isFree", False),
                        "priceTypeDesc": card_data.get("priceTypeDesc", ""),
                        "price": card_data.get("price", 0),
                        "marketPrice": card_data.get("marketPrice", 0),
                        "preferentialPrice": card_data.get("preferentialPrice", 0),
                        "preferentialDesc": card_data.get("preferentialDesc", ""),
                        "shortFeatures": card_data.get("shortFeatures", []),
                        "sightCategoryInfo": card_data.get("sightCategoryInfo", "未上榜"),
                        "priceType": card_data.get("priceType", ""),
                        "city": city
                    }
                }
                
                all_attractions.append(attraction_info)
                logger.info(f"成功添加景点: {attraction_info['card']['poiName']}")
            
            logger.info(f"成功添加{city}的{len(attractions)}个景点")
            
        except HTTPException as e:
            logger.error(f"{city}获取信息失败: {str(e.detail)}")
            continue
        except Exception as e:
            logger.error(f"{city}处理异常: {str(e)}", exc_info=True)
            continue
    
    try:
        # 使用Jinja2模板格式化输出
        logger.info("开始渲染模板")
        formatted_text = template.render(attractionList=all_attractions)
        logger.info("模板渲染成功")
    except Exception as e:
        logger.error(f"模板渲染失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"模板渲染失败: {str(e)}")
    
    return formatted_text

def get_district_id(cityName: str):
    url = "https://m.ctrip.com/restapi/soa2/30668/search"

    querystring = {
        "action": "online",
        "source": "globalonline",
        "keyword": cityName
    }

    payload = ""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": "GUID=09031022317999445208",
        "Host": "m.ctrip.com",
        "Content-Length": "0"
    }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"获取城市ID失败: {str(e)}")

    result = response.json()
    
    if not result.get('data'):
        raise HTTPException(status_code=404, detail=f"未找到城市: {cityName}")
        
    districtId = result['data'][0]['id']
    return districtId

def get_city_info(city_name: str) -> Dict[str, Any]:
    """
    获取城市信息
    
    Args:
        city_name (str): 城市名称
        
    Returns:
        Dict[str, Any]: 城市信息
    """
    url = "https://m.ctrip.com/restapi/soa2/30668/search"
    querystring = {
        "action": "globalonline",
        "source": "globalonline",
        "keyword": city_name
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": "GUID=09031022317999445208",
        "Host": "m.ctrip.com",
        "Content-Length": "0"
    }

    try:
        response = requests.request("POST", url, data="", headers=headers, params=querystring)
        response.raise_for_status()
        result = response.json()
        
        # 查找城市数据
        city_data = None
        for item in result.get('data', []):
            if isinstance(item, dict) and item.get('type') == 'city':
                required_fields = ['districtName', 'districtId']
                if all(item.get(field) for field in required_fields):
                    city_data = item
                    break

        if not city_data:
            raise HTTPException(status_code=404, detail=f"未找到城市: {city_name}")

        return {
            'district_id': city_data['districtId'],
            'district_name': city_data['districtName']
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"获取城市信息失败: {str(e)}")

def get_city_attractions(city_name: str) -> List[Dict[str, Any]]:
    """
    获取城市景点列表
    
    Args:
        city_name (str): 城市名称
        
    Returns:
        List[Dict[str, Any]]: 景点列表
    """
    try:
        # 获取城市信息
        city_info = get_city_info(city_name)
        if not city_info:
            raise HTTPException(status_code=404, detail=f"未找到城市: {city_name}")
            
        # 获取景点列表
        url = "https://m.ctrip.com/restapi/soa2/13342/json/getSightList"
        payload = {
            "arg": {
                "districtId": city_info['district_id'],
                "pageIndex": 1,
                "pageSize": 20,
                "sortType": 1,
                "head": {
                    "cid": str(uuid.uuid4())[:32],
                    "ctok": "",
                    "cver": "1.0",
                    "lang": "01",
                    "sid": "8888",
                    "syscode": "09",
                    "auth": "",
                    "xsid": "",
                    "extension": []
                }
            }
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Content-Type": "application/json",
            "Cookie": f"GUID={str(uuid.uuid4()).replace('-', '')[:32]}"
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data.get('result', {}).get('items'):
            return []

        attractions = []
        for item in data['result']['items']:
            attraction = {
                'name': item.get('name', ''),
                'score': float(item.get('score', 0)),
                'review_count': int(item.get('commentCount', 0)),
                'url': f"https://you.ctrip.com/sight/{city_info['district_name']}{city_info['district_id']}/{item.get('productId', '')}.html"
            }
            attractions.append(attraction)

        return attractions

    except Exception as e:
        logger.error(f"{city_name}获取信息失败: {str(e)}")
        return [] 
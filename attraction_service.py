import requests
import json
import re
import time
import uuid
from typing import Dict, List, Any
from fastapi import HTTPException
from model.get_wordcloud import get_wordcloud
from model.get_pic_link import get_pic_link
import logging
import os
from wordcloud import WordCloud
import numpy as np
from PIL import Image
import io
import base64

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_url(keyword: str) -> Dict[str, str]:
    """
    获取景点URL和POI ID
    
    Args:
        keyword (str): 景点关键词
        
    Returns:
        Dict[str, str]: 包含URL和POI ID的字典
    """
    url = "https://m.ctrip.com/restapi/soa2/30668/search"
    querystring = {
        "action": "globalonline",
        "source": "globalonline",
        "keyword": keyword
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
        
        # 查找景点数据
        sight_data = None
        for item in result.get('data', []):
            if isinstance(item, dict) and item.get('type') == 'sight':
                required_fields = ['districtName', 'districtId', 'productId', 'poiId']
                if all(item.get(field) for field in required_fields):
                    sight_data = item
                    break

        if not sight_data:
            raise HTTPException(status_code=404, detail=f"未找到景点: {keyword}")

        # 生成URL
        district_name = sight_data['eName'] if sight_data['eName'] else sight_data['districtName']
        district_id = sight_data['districtId']
        product_id = sight_data['productId']
        poi_id = str(sight_data['poiId'])

        ctrip_url = f"https://you.ctrip.com/sight/{district_name}{district_id}/{product_id}.html"

        return {
            'url': ctrip_url,
            'poi_id': poi_id
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"获取景点URL失败: {str(e)}")

def get_info(url: str) -> Dict[str, Any]:
    """
    获取景点详细信息
    
    Args:
        url (str): 景点URL
        
    Returns:
        Dict[str, Any]: 景点详细信息
    """
    headers = {
        "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0",
        "Cookie": "_pd=%7B%22_o%22%3A70%2C%22s%22%3A1030%2C%22_s%22%3A9%7D;GUID=09031167317991829446"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # 提取JSON数据
        script_pattern = re.compile(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', re.DOTALL)
        script_match = script_pattern.search(response.text)

        if not script_match:
            raise HTTPException(status_code=404, detail="未找到景点数据")

        json_data = json.loads(script_match.group(1))
        poi_data = json_data["props"]["pageProps"]["initialState"]["poiDetail"]

        # 提取标签数据
        hot_tags_section = re.search(r'<div class="hotTags".*?>(.*?)</div>', response.text, re.DOTALL)
        
        # 设置默认值
        review_count = 0
        positive = 0
        negative = 0
        comment_score = 0.0

        if hot_tags_section:
            span_pattern = re.compile(r'<span.*?>(.*?)</span>')
            spans = span_pattern.findall(hot_tags_section.group(1))

            def extract_number(text):
                match = re.search(r'\d+', text)
                return int(match.group()) if match else 0

            review_count = extract_number(spans[0]) if len(spans) >= 1 else 0
            positive = extract_number(spans[1]) if len(spans) >= 2 else 0
            negative = extract_number(spans[3]) if len(spans) >= 4 else 0

        # 尝试从不同位置获取评分
        try:
            comment_score = float(poi_data.get("commentScore", 0))
        except (ValueError, TypeError):
            try:
                comment_score = float(poi_data.get("score", 0))
            except (ValueError, TypeError):
                comment_score = 0.0

        return {
            'poi_id': int(poi_data.get("poiId", 0)),
            'poi_name': str(poi_data.get("poiName", "")),
            'comment_score': comment_score,
            'review_count': review_count,
            'positive': positive,
            'negative': negative
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"获取景点信息失败: {str(e)}")
    except Exception as e:
        logger.error(f"处理景点信息时发生错误: {str(e)}")
        return {
            'poi_id': 0,
            'poi_name': "",
            'comment_score': 0.0,
            'review_count': 0,
            'positive': 0,
            'negative': 0
        }

def get_contents(poi_id: int, max_page: int = 1) -> List[str]:
    """
    获取景点评论内容
    
    Args:
        poi_id (int): 景点POI ID
        max_page (int): 最大页数
        
    Returns:
        List[str]: 评论内容列表
    """
    url = "https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList"
    user_contents = []

    for page_index in range(1, max_page + 1):
        try:
            payload = {
                "arg": {
                    "channelType": 2,
                    "collapseType": 0,
                    "commentTagId": 0,
                    "pageIndex": page_index,
                    "pageSize": 10,
                    "poiId": poi_id,
                    "sourceType": 1,
                    "sortType": 3,
                    "starType": 0,
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
                break

            user_contents.extend(
                [item['content'] for item in data['result']['items']]
            )

            time.sleep(1.5 + (page_index % 3) * 0.5)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")

    return user_contents

def generate_wordcloud(text: str) -> str:
    """
    生成词云图
    
    Args:
        text (str): 评论文本
        
    Returns:
        str: 图片URL
    """
    try:
        # 创建词云对象
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path='dataset/微软雅黑.ttf',  # 使用微软雅黑字体
            max_words=100,
            max_font_size=100,
            random_state=42
        )
        
        # 生成词云
        wordcloud.generate(text)
        
        # 将词云保存为图片
        wordcloud.to_file("model/comment_wordcloud.png")
        
        # 上传图片并获取链接
        pic_link = get_pic_link()
        return pic_link
        
    except Exception as e:
        logger.error(f"生成词云图失败: {str(e)}")
        return None

def get_attractions(cityNames: List[str]) -> List[Dict[str, Any]]:
    """
    获取多个景点的详细信息
    
    Args:
        cityNames (List[str]): 景点名称列表
        
    Returns:
        List[Dict[str, Any]]: 景点信息列表
    """
    all_attractions = []
    
    for cityName in cityNames:
        try:
            logger.info(f"开始处理景点: {cityName}")
            
            # 获取景点URL
            url_info = get_url(cityName)
            if not url_info:
                logger.warning(f"未找到景点URL: {cityName}")
                continue
                
            # 获取景点详细信息
            info = get_info(url_info['url'])
            if not info:
                logger.warning(f"未找到景点信息: {cityName}")
                continue
                
            # 获取用户评论
            comments = get_contents(int(url_info['poi_id']), max_page=1)
            
            # 生成词云图
            wordcloud_url = None
            if comments:
                comment_text = " ".join(comments)
                wordcloud_url = generate_wordcloud(comment_text)
            
            # 构建景点信息
            attraction_info = {
                'name': cityName,
                'score': info['comment_score'],
                'review_count': info['review_count'],
                'positive_count': info['positive'],
                'negative_count': info['negative'],
                'url': url_info['url'],
                'comments': comments[:3],  # 只取前3条评论
                'wordcloud_url': wordcloud_url
            }
            
            all_attractions.append(attraction_info)
            logger.info(f"成功添加景点: {cityName}")
            
        except Exception as e:
            logger.error(f"处理景点时发生错误: {str(e)}", exc_info=True)
            continue
    
    return all_attractions 
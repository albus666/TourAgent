import requests
import json
from typing import Optional, List, Dict, Any


class CtripAPIHandler:
    """携程API处理类，负责与携程API交互"""

    def __init__(self):
        """初始化API处理器"""
        self.session = requests.Session()

    def _get_poi_id(self, city_name: str) -> Optional[int]:
        """
        辅助方法：获取poiId
        
        Args:
            city_name: 城市名称
            
        Returns:
            poiId或None
        """
        url = "https://m.ctrip.com/restapi/soa2/30668/search"
        
        params = {
            "action": "online",
            "source": "globalonline",
            "keyword": city_name
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Cookie": "GUID=09031022317999445208",
            "Host": "m.ctrip.com",
            "Content-Length": "0"
        }

        response = self.session.post(url, params=params, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        data = result.get("data", [])
        
        if not data:
            return None

        for item in data:
            if item.get("type") == "sight":
                has_all_fields = (
                    "districtName" in item and 
                    "districtId" in item and 
                    "productId" in item and
                    item.get("districtName") is not None and
                    item.get("districtId") is not None and
                    item.get("productId") is not None
                )
                if has_all_fields:
                    return item.get("poiId")

        return None

    def _get_district_id(self, city_name: str) -> Optional[int]:
        """
        辅助方法：获取districtId
        
        Args:
            city_name: 城市名称
            
        Returns:
            districtId或None
        """
        url = "https://m.ctrip.com/restapi/soa2/30668/search"
        
        params = {
            "action": "online",
            "source": "globalonline",
            "keyword": city_name
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Cookie": "GUID=09031022317999445208",
            "Host": "m.ctrip.com",
            "Content-Length": "0"
        }

        response = self.session.post(url, params=params, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        data = result.get("data", [])
        
        if not data:
            return None

        return data[0].get("id")

    def get_city_spots(self, city_name: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        根据城市名获取景点列表（城市景点推荐）
        
        Args:
            city_name: 城市名称
            count: 返回景点数量，默认10个
            
        Returns:
            景点卡片列表
        """
        all_spots = []
        
        try:
            print(f"查询城市: {city_name}")
            district_id = self._get_district_id(city_name)
            print(f"获取到districtId: {district_id}")
            
            if district_id is None:
                return all_spots

            url = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"
            
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
                "districtId": district_id,
                "index": 1,
                "sortType": 1,
                "count": count,
                "filter": {},
                "returnModuleType": "all"
            }

            params = {
                "_fxpcqlniredt": "09031162419158778138",
                "x-traceID": "09031162419158778138-1742713344797-6843463"
            }

            headers = {
                "Content-Type": "application/json",
                "Cookie": "GUID=09031136319238214458",
                "Cookieorigin": "https://you.ctrip.com",
                "Accept": "*/*",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
                "Connection": "keep-alive"
            }

            response = self.session.post(url, json=payload, params=params, headers=headers)
            response.raise_for_status()
            
            print(f"ctrip接口返回: {response.text}")

            result = response.json()
            spots = result.get("attractionList", [])
            print(f"spots数组: {spots}")

            for spot in spots:
                card = spot.get("card")
                if card:
                    all_spots.append(card)

        except Exception as e:
            print(f"查询景点异常: {e}")

        return all_spots

    def get_spot_detail(self, keyword: str) -> Dict[str, Any]:
        """
        获取景点详情和评论（景点详情查询）
        读取3个用户的评论，如果评论有图片则各附上一张图片链接
        
        Args:
            keyword: 景点关键词
            
        Returns:
            包含景点信息和评论的字典
        """
        # 先获取poiId
        poi_id = self._get_poi_id(keyword)
        print(f"获取到poiId: {poi_id}")
        
        if poi_id is None:
            raise RuntimeError("未找到景点对应的poiId")

        # 评论请求部分
        comment_url = "https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList"
        
        payload = {
            "arg": {
                "channelType": 2,
                "collapseType": 0,
                "commentTagId": 0,
                "pageIndex": 1,
                "pageSize": 3,  # 只读取3个评论
                "poiId": poi_id,
                "sourceType": 1,
                "sortType": 3,
                "starType": 0
            },
            "head": {
                "cid": "09031030113497386388",
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

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Cookie": "GUID=09031022317999445208",
            "Origin": "https://m.ctrip.com",
            "Referer": "https://m.ctrip.com/html5/you/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }

        try:
            response = self.session.post(comment_url, json=payload, headers=headers)
            response.raise_for_status()
            
            comment_response = response.text
            if not comment_response:
                print("警告: 评论接口无返回")
                return {
                    "keyword": keyword,
                    "poiId": poi_id,
                    "comments": [],
                    "commentCount": 0,
                    "error": "评论接口无返回"
                }

            comment_root = json.loads(comment_response)
            
            if not comment_root or "result" not in comment_root:
                print(f"警告: 评论接口返回格式错误")
                return {
                    "keyword": keyword,
                    "poiId": poi_id,
                    "comments": [],
                    "commentCount": 0,
                    "error": "评论接口返回格式错误"
                }

            items = comment_root.get("result", {}).get("items", [])
            comments = []
            
            for item in items:
                comment = {}
                
                user_info = item.get("userInfo")
                if user_info:
                    comment["userNick"] = user_info.get("userNick")
                    comment["userImage"] = user_info.get("userImage")
                
                comment["score"] = item.get("score")
                comment["content"] = item.get("content")
                comment["publishTypeTag"] = item.get("publishTypeTag")
                comment["ipLocatedName"] = item.get("ipLocatedName")
                
                # 如果有图片，只附上一张图片链接
                images = item.get("images", [])
                if images and len(images) > 0:
                    comment["imageUrl"] = images[0].get("imageThumbUrl")
                else:
                    comment["imageUrl"] = None
                
                comments.append(comment)
            
            return {
                "keyword": keyword,
                "poiId": poi_id,
                "comments": comments,
                "commentCount": len(comments)
            }
        except requests.exceptions.HTTPError as e:
            print(f"警告: 评论接口请求失败 - {e}")
            return {
                "keyword": keyword,
                "poiId": poi_id,
                "comments": [],
                "commentCount": 0,
                "error": f"HTTP错误: {e}"
            }
        except Exception as e:
            print(f"警告: 获取评论时发生异常 - {e}")
            return {
                "keyword": keyword,
                "poiId": poi_id,
                "comments": [],
                "commentCount": 0,
                "error": f"异常: {e}"
            }


if __name__ == '__main__':
    """测试携程API处理器"""
    handler = CtripAPIHandler()
    
    print("=" * 80)
    print("测试 1: 城市景点推荐 - get_city_spots()")
    print("=" * 80)
    try:
        spots = handler.get_city_spots("北京", count=5)
        print(f"\n✓ 成功获取北京景点推荐，共 {len(spots)} 个景点")
        for i, spot in enumerate(spots, 1):
            # spot 本身就是 card 对象
            print(f"\n景点 {i}:")
            print(f"  名称: {spot.get('poiName', 'N/A')}")
            print(f"  ID: {spot.get('poiId', 'N/A')}")
            print(f"  评分: {spot.get('commentScore', 'N/A')} 分")
            print(f"  评论数: {spot.get('commentCount', 'N/A')}")
            print(f"  区域: {spot.get('zoneName', 'N/A')}")
            print(f"  距离: {spot.get('distanceStr', 'N/A')}")
            # 打印特色标签
            features = spot.get('shortFeatures', [])
            if features:
                print(f"  特色: {', '.join(features)}")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")

    print("\n" + "=" * 80)
    print("测试 2: 景点详情查询 - get_spot_detail()")
    print("=" * 80)
    try:
        detail = handler.get_spot_detail("故宫")
        print(f"\n✓ 成功获取景点详情")
        print(f"  关键词: {detail['keyword']}")
        print(f"  POI ID: {detail['poiId']}")
        print(f"  评论数量: {detail['commentCount']}")

        print(f"\n用户评论:")
        for i, comment in enumerate(detail['comments'], 1):
            print(f"\n  【评论 {i}】")
            print(f"    用户: {comment.get('userNick', '匿名')}")
            print(f"    评分: {comment.get('score', 'N/A')} 分")
            print(f"    位置: {comment.get('ipLocatedName', 'N/A')}")
            content = comment.get('content', '')
            print(f"    内容: {content[:80]}..." if len(content) > 80 else f"    内容: {content}")
            if comment.get('imageUrl'):
                print(f"    图片: {comment['imageUrl']}")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")

    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)

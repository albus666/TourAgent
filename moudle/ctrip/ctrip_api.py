import requests
import json
from typing import Optional, List, Dict, Any


class CtripAPIHandler:
    """携程API处理类，负责与携程API交互"""

    def __init__(self):
        """初始化API处理器"""
        self.session = requests.Session()

    def _search_poi_and_district(self, keyword: str) -> Dict[str, Any]:
        """
        统一搜索方法：获取poiId、districtId 及景点详情页URL
        
        Args:
            keyword: 搜索关键词（景点名或城市名）
            
        Returns:
            包含 poiId、districtId、sightUrl 的字典
        """
        url = "https://m.ctrip.com/restapi/soa2/30668/search"
        
        params = {
            "action": "globalonline",
            "source": "globalonline",
            "keyword": keyword
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
            return {"poiId": None, "districtId": None, "sightUrl": None, "imageUrl": None}

        poi_id = None
        district_id = None
        sight_url: Optional[str] = None
        image_url: Optional[str] = None

        # 查找景点poiId（sight类型）
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
                    poi_id = item.get("poiId")
                    # 构造景点详情页URL（优先使用 eName，无则使用 districtName）
                    district_name = item.get("eName") or item.get("districtName") or ""
                    district_id = item.get("districtId")
                    product_id = item.get("productId")
                    if district_name is not None and district_id is not None and product_id is not None:
                        try:
                            sight_url = f"https://you.ctrip.com/sight/{district_name}{district_id}/{product_id}.html"
                        except Exception:
                            sight_url = None
                    
                    # 提取图片URL并清理尺寸参数
                    raw_image_url = item.get("imageUrl")
                    if raw_image_url:
                        # 去除图片URL中的尺寸参数（如 _C_320_320, _R_320_320_Q70 等）
                        import re as _re
                        image_url = _re.sub(r'_[A-Z]_\d+_\d+(_Q\d+)?\.jpg$', '.jpg', raw_image_url)
                    break

        # 查找城市districtId（district类型）
        for item in data:
            if item.get("type") == "district":
                district_id = item.get("id")
                break

        return {"poiId": poi_id, "districtId": district_id, "sightUrl": sight_url, "imageUrl": image_url}

    def _get_poi_id(self, keyword: str) -> Optional[int]:
        """
        获取poiId（景点ID）
        
        Args:
            keyword: 景点关键词
            
        Returns:
            poiId或None
        """
        result = self._search_poi_and_district(keyword)
        return result.get("poiId")

    def _get_district_id(self, city_name: str) -> Optional[int]:
        """
        获取districtId（城市ID）
        
        Args:
            city_name: 城市名称
            
        Returns:
            districtId或None
        """
        result = self._search_poi_and_district(city_name)
        return result.get("districtId")

    def get_spot_detail_page(self, keyword: str) -> Dict[str, Any]:
        """
        通过关键词获取景点详情页URL，并可供爬虫使用
        
        Args:
            keyword: 景点关键词
        
        Returns:
            {"success": bool, "keyword": str, "poiId": Optional[int], "sightUrl": Optional[str], "message": str}
        """
        try:
            result = self._search_poi_and_district(keyword)
            sight_url = result.get("sightUrl")
            poi_id = result.get("poiId")
            image_url = result.get("imageUrl")
            if not sight_url or not poi_id:
                return {
                    "success": False,
                    "keyword": keyword,
                    "poiId": poi_id,
                    "sightUrl": sight_url,
                    "imageUrl": image_url,
                    "message": "未找到景点详情页URL或POI ID"
                }
            return {
                "success": True,
                "keyword": keyword,
                "poiId": poi_id,
                "sightUrl": sight_url,
                "imageUrl": image_url,
                "message": "成功获取景点详情页URL"
            }
        except Exception as e:
            return {
                "success": False,
                "keyword": keyword,
                "poiId": None,
                "sightUrl": None,
                "imageUrl": None,
                "message": f"获取详情页URL时发生异常: {e}"
            }

    def crawl_spot_detail_by_url(self, url: str) -> Dict[str, Any]:
        """
        爬取景点详情页，提取轮播图片和基础信息
        
        Args:
            url: 景点详情页URL
        
        Returns:
            包含轮播图片URL列表和基础信息的字典
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            resp = self.session.get(url, headers=headers)
            resp.raise_for_status()

            import re as _re
            
            # 提取景点标题
            title_match = _re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
            title = title_match.group(1) if title_match else ""
            
            # 提取评分
            score_match = _re.search(r'<p class="commentScoreNum">([^<]+)</p>', resp.text)
            score = float(score_match.group(1)) if score_match else 0.0
            
            # 提取评论数
            comment_match = _re.search(r'<span class="hover-underline">(\d+)<!-- -->条点评</span>', resp.text)
            comment_count = int(comment_match.group(1)) if comment_match else 0
            
            # 提取热度
            heat_match = _re.search(r'<div class="heatScoreText">([^<]+)</div>', resp.text)
            heat_score = float(heat_match.group(1)) if heat_match else 0.0
            
            # 提取基础信息
            base_info = {}
            base_info_pattern = r'<div class="baseInfoItem"[^>]*><p class="baseInfoTitle">([^<]+)</p><[^>]*class="baseInfoText[^"]*"[^>]*>([^<]+)</[^>]*></div>'
            base_info_matches = _re.findall(base_info_pattern, resp.text)
            
            for title_text, content_text in base_info_matches:
                # 清理HTML标签和特殊字符
                clean_content = _re.sub(r'<[^>]+>', '', content_text)
                clean_content = clean_content.replace('&nbsp;', ' ').strip()
                if clean_content:
                    base_info[title_text] = clean_content
            
            # 提取开放时间特殊处理
            open_time_match = _re.search(r'<span class="openStatus">([^<]+)</span>.*?([^<]+开放)', resp.text)
            if open_time_match:
                base_info["开放状态"] = open_time_match.group(1)
                base_info["开放时间"] = open_time_match.group(2)
            
            # 提取电话信息
            phone_match = _re.search(r'<span class="phoneHeaderItem">([^<]+)</span>', resp.text)
            if phone_match:
                base_info["联系电话"] = phone_match.group(1)
            
            # 提取模块信息（detailModule结构）
            module_info = {}
            # 匹配 moduleTitle 和对应的 moduleContent
            module_pattern = r'<div class="moduleTitle">([^<]+)</div>.*?<div class="moduleContent[^"]*"[^>]*>(.*?)</div>'
            module_matches = _re.findall(module_pattern, resp.text, _re.DOTALL)
            
            for module_title, module_content in module_matches:
                # 清理HTML标签和特殊字符
                clean_content = _re.sub(r'<[^>]+>', '', module_content)
                clean_content = clean_content.replace('&nbsp;', ' ').replace('\n', ' ').strip()
                if clean_content and clean_content != '...':
                    module_info[module_title] = clean_content

            # 提取景点图片URL（从搜索结果中获取）
            image_url = None
            # 这里可以从之前的搜索结果中获取图片URL
            # 或者从页面中提取图片URL
            
            return {
                "success": True,
                "message": "成功获取景点详情",
                "data": {
                    "title": title,
                    "score": score,
                    "comment_count": comment_count,
                    "heat_score": heat_score,
                    "image_url": image_url,
                    "base_info": base_info,
                    "module_info": module_info
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"爬取详情页失败: {e}",
                "data": {}
            }

    def get_city_spots(self, city_name: str, count: int = 10) -> Dict[str, Any]:
        """
        根据城市名获取景点列表（城市景点推荐）
        
        Args:
            city_name: 城市名称
            count: 返回景点数量，默认10个
            
        Returns:
            包含景点列表和状态信息的字典
        """
        all_spots = []
        
        try:
            print(f"查询城市: {city_name}")
            district_id = self._get_district_id(city_name)
            print(f"获取到districtId: {district_id}")
            
            if district_id is None:
                return {
                    "success": False,
                    "cityName": city_name,
                    "count": 0,
                    "spots": [],
                    "message": f"未找到城市 {city_name} 对应的districtId"
                }

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
            return {
                "success": False,
                "cityName": city_name,
                "count": 0,
                "spots": [],
                "message": f"查询景点时发生异常: {e}"
            }

        return {
            "success": True,
            "cityName": city_name,
            "count": len(all_spots),
            "spots": all_spots,
            "message": f"成功获取 {len(all_spots)} 个景点"
        }

    def get_spot_detail(self, keyword: str) -> Dict[str, Any]:
        """
        获取景点详情和评论（景点详情查询）
        读取5个用户的评论，如果评论有图片则各附上一张图片链接
        
        Args:
            keyword: 景点关键词
            
        Returns:
            包含景点信息和评论的字典
        """
        # 先获取poiId
        poi_id = self._get_poi_id(keyword)
        print(f"获取到poiId: {poi_id}")
        
        if poi_id is None:
            return {
                "success": False,
                "keyword": keyword,
                "comments": [],
                "message": "未找到景点对应的poiId"
            }

        # 评论请求部分
        comment_url = "https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList"
        
        payload = {
            "arg": {
                "channelType": 2,
                "collapseType": 0,
                "commentTagId": 0,
                "pageIndex": 1,
                "pageSize": 5,  # 只读取5个评论
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
                    "success": False,
                    "keyword": keyword,
                    "comments": [],
                    "message": "评论接口无返回"
                }

            comment_root = json.loads(comment_response)
            
            if not comment_root or "result" not in comment_root:
                print(f"警告: 评论接口返回格式错误")
                return {
                    "success": False,
                    "keyword": keyword,
                    "comments": [],
                    "message": "评论接口返回格式错误"
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
                    # 优先使用imageSrcUrl获取高清图片，如果没有则使用imageThumbUrl
                    image_url = images[0].get("imageSrcUrl") or images[0].get("imageThumbUrl")
                    comment["imageUrl"] = image_url
                else:
                    comment["imageUrl"] = None
                
                comments.append(comment)
            
            return {
                "success": True,
                "keyword": keyword,
                "poiId": poi_id,
                "comments": comments,
                "commentCount": len(comments),
                "message": "成功获取景点详情"
            }
        except requests.exceptions.HTTPError as e:
            print(f"警告: 评论接口请求失败 - {e}")
            return {
                "success": False,
                "keyword": keyword,
                "comments": [],
                "message": f"评论接口请求失败: {e}"
            }
        except Exception as e:
            print(f"警告: 获取评论时发生异常 - {e}")
            return {
                "success": False,
                "keyword": keyword,
                "comments": [],
                "message": f"获取评论时发生异常: {e}"
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
    # print("测试 2: 景点详情查询 - get_spot_detail()")
    # print("=" * 80)
    # try:
    #     detail = handler.get_spot_detail("上海迪士尼")
    #     print(f"\n✓ 成功获取景点详情")
    #     print(f"  关键词: {detail['keyword']}")
    #     print(f"  POI ID: {detail['poiId']}")
    #     print(f"  评论数量: {detail['commentCount']}")
    #
    #     print(f"\n用户评论:")
    #     for i, comment in enumerate(detail['comments'], 1):
    #         print(f"\n  【评论 {i}】")
    #         print(f"    用户: {comment.get('userNick', '匿名')}")
    #         print(f"    评分: {comment.get('score', 'N/A')} 分")
    #         print(f"    位置: {comment.get('ipLocatedName', 'N/A')}")
    #         content = comment.get('content', '')
    #         print(f"    内容: {content[:80]}..." if len(content) > 80 else f"    内容: {content}")
    #         if comment.get('imageUrl'):
    #             print(f"    图片: {comment['imageUrl']}")
    # except Exception as e:
    #     print(f"\n✗ 测试失败: {e}")
    #
    # print("\n" + "=" * 80)
    # print("所有测试完成！")
    # print("=" * 80)

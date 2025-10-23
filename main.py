import json
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse, Response
import logging
import os
import httpx
from typing import Dict
from moudle.ctrip import CtripAPIHandler
from moudle.mcp.mcp_api import BaiduMapAPI
from moudle.utils.get_weather import get_weather

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="旅游规划助手API",
    description="提供城市景点推荐、详情查询和地理编码服务",
    version="2.1.0"
)

# 初始化携程API处理器
ctrip_handler = CtripAPIHandler()

# 初始化百度地图API处理器
baidu_map_api = BaiduMapAPI()


# # @app.get("/weather")
# # def get_weather(cityNames: str):

@app.get("/spots/recommend")
async def get_city_spots_endpoint(cityName: str, count: int = 10):
    """
    城市景点推荐接口
    
    Args:
        cityName (str): 城市名称
        count (int): 返回景点数量，默认10个
        
    Returns:
        JSONResponse: 包含景点列表的响应
    """
    try:
        logger.info(f"开始查询城市景点: {cityName}, 数量: {count}")

        # 获取城市景点推荐
        result = ctrip_handler.get_city_spots(cityName, count)

        # 检查是否成功
        if not result.get("success", False):
            return JSONResponse(
                content={
                    "success": False,
                    "cityName": cityName,
                    "count": 0,
                    "spots": [],
                    "message": result.get("message", "查询失败")
                }
            )

        # 格式化返回数据
        formatted_spots = []
        for spot in result.get("spots", []):
            formatted_spots.append({
                "poiId": spot.get("poiId"),
                "poiName": spot.get("poiName"),
                "zoneName": spot.get("zoneName"),
                "commentScore": spot.get("commentScore"),
                "commentCount": spot.get("commentCount"),
                "distanceStr": spot.get("distanceStr"),
                "coverImageUrl": spot.get("coverImageUrl"),
                "shortFeatures": spot.get("shortFeatures", []),
                "sightLevelStr": spot.get("sightLevelStr"),
                "price": spot.get("price"),
                "priceTypeDesc": spot.get("priceTypeDesc"),
                "detailUrl": spot.get("detailUrl")
            })

        logger.info(f"成功获取{len(formatted_spots)}个景点")

        return JSONResponse(
            content={
                "success": True,
                "cityName": cityName,
                "count": len(formatted_spots),
                "spots": formatted_spots,
                "message": result.get("message", "查询成功")
            }
        )

    except Exception as e:
        logger.error(f"查询城市景点时发生错误: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "cityName": cityName,
                "count": 0,
                "spots": [],
                "message": f"查询失败: {str(e)}"
            },
            status_code=500
        )


@app.get("/spots/detail")
async def get_spot_detail_endpoint(keyword: str):
    """
    景点详情查询接口
    
    Args:
        keyword (str): 景点关键词
        
    Returns:
        JSONResponse: 包含景点详情和评论的响应
    """
    try:
        logger.info(f"开始查询景点详情: {keyword}")

        # 获取景点详情
        detail = ctrip_handler.get_spot_detail(keyword)

        # 检查是否成功
        if not detail.get("success", False):
            return JSONResponse(
                content={
                    "success": False,
                    "keyword": keyword,
                    "poiId": detail.get("poiId"),
                    "commentCount": 0,
                    "comments": {},
                    "message": detail.get("message", "查询失败")
                }
            )

        # 格式化评论数据（由列表改为以"用户1""用户2"作为键的字典）
        formatted_comments = {}
        for idx, comment in enumerate(detail.get("comments", []), start=1):
            formatted_comments[f"用户{idx}"] = {
                "userNick": comment.get("userNick"),
                "userImage": comment.get("userImage"),
                "score": comment.get("score"),
                "content": comment.get("content"),
                "publishTypeTag": comment.get("publishTypeTag"),
                "ipLocatedName": comment.get("ipLocatedName"),
                "imageUrl": f"![]({comment.get('imageUrl')})" if comment.get("imageUrl") else None
            }

        logger.info(f"成功获取景点详情，评论数: {detail.get('commentCount', 0)}")

        response_data = {
            "success": True,
            "keyword": detail.get("keyword"),
            "poiId": detail.get("poiId"),
            "commentCount": detail.get("commentCount"),
            "comments": formatted_comments,
            "message": detail.get("message", "查询成功")
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"查询景点详情时发生错误: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "keyword": keyword,
                "poiId": None,
                "commentCount": 0,
                "comments": {},
                "message": f"查询失败: {str(e)}"
            },
            status_code=500
        )


@app.get("/spots/detail-by-keyword")
async def get_spot_detail_by_keyword(keyword: str = Query(..., description="景点关键词")):
    """
    单一接口：根据关键词先获取详情页URL，再用URL爬取详情并返回
    """
    try:
        logger.info(f"开始根据关键词获取景点详情: {keyword}")
        url_result = ctrip_handler.get_spot_detail_page(keyword)

        if not url_result.get("success") or not url_result.get("sightUrl"):
            return JSONResponse(
                content={
                    "success": False,
                    "keyword": keyword,
                    "message": url_result.get("message", "未获取到详情页URL")
                },
                status_code=404
            )

        sight_url = url_result["sightUrl"]
        image_url = url_result.get("imageUrl")  # 获取图片URL
        detail_result = ctrip_handler.crawl_spot_detail_by_url(sight_url)

        # 将图片URL添加到详情数据中
        if detail_result.get("success") and image_url:
            detail_data = detail_result.get("data", {})
            detail_data["image_url"] = image_url
            detail_result["data"] = detail_data

        # 合并与返回
        return JSONResponse(
            content={
                "success": detail_result.get("success", False),
                "keyword": keyword,
                "sightUrl": sight_url,
                "message": detail_result.get("message"),
                "data": detail_result.get("data", {})
            },
            status_code=200 if detail_result.get("success") else 500
        )
    except Exception as e:
        logger.error(f"根据关键词获取详情失败: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "keyword": keyword,
                "message": f"获取详情失败: {str(e)}"
            },
            status_code=500
        )


@app.get("/setting")
def get_setting():
    """
    获取旅游规划助手的配置信息
   
    Returns:
        JSONResponse: 包含配置信息的响应
    """
    try:
        # 读取JSON文件
        json_path = os.path.join(os.path.dirname(__file__), "dataset", "旅游出行助手.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试解析JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {str(e)}")
            # 返回一个基本的配置结构
            data = [{
                "moduleId": "userGuide",
                "name": "apps.templates.basicChat.user guidance",
                "avatar": "/imgs/module/userGuide.png",
                "flowType": "userGuide",
                "position": {
                    "x": -2977.109938148764,
                    "y": 2040.7423525983215
                },
                "inputs": [],
                "outputs": []
            }]

        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"读取配置文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"读取配置文件失败: {str(e)}")


@app.get("/image-proxy")
async def image_proxy(url: str = Query(..., description="要代理的图片URL")):
    """
    图片代理接口 - 绕过防盗链

    Args:
        url: 图片的完整URL

    Returns:
        图片内容

    Example:
        GET /image-proxy?url=https://gitee.com/Atopes/img-hosting/raw/master/test.jpg
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            referer = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': referer,
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            response = await client.get(url, headers=headers, follow_redirects=True)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'image/jpeg')

                return Response(
                    content=response.content,
                    media_type=content_type,
                    headers={
                        'Cache-Control': 'public, max-age=86400',
                        'Access-Control-Allow-Origin': '*',
                        'Connection': 'close',  # 添加这行：明确关闭连接
                        'Content-Length': str(len(response.content))  # 添加这行：明确内容长度
                    }
                )
            else:
                raise HTTPException(status_code=response.status_code, detail=f"获取图片失败: {response.status_code}")


    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="请求超时")
    except Exception as e:
        logger.error(f"代理图片时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"代理图片失败: {str(e)}")


@app.get("/test")
def test():
    """
    测试接口 - 返回图片信息
    """
    # 使用本地代理接口
    proxy_url = "http://www.atopes.xyz:4399/image-proxy?url=https://gitee.com/Atopes/img-hosting/raw/master/test.jpg"

    return JSONResponse(
        content={
            "success": True,
            "message": "测试图片",
            "test": {
                "bing_url": "https://gitee.com/Atopes/img-hosting/raw/master/test.jpg",
                "bing_markdown": "![test](https://ts1.tc.mm.bing.net/th/id/R-C.987f582c510be58755c4933cda68d525?rik=C0D21hJDYvXosw&riu=http%3a%2f%2fimg.pconline.com.cn%2fimages%2fupload%2fupc%2ftx%2fwallpaper%2f1305%2f16%2fc4%2f20990657_1368686545122.jpg&ehk=netN2qzcCVS4ALUQfDOwxAwFcy41oxC%2b0xTFvOYy5ds%3d&risl=&pid=ImgRaw&r=0)",
                "gitee_url":"https://gitee.com/Atopes/img-hosting/raw/master/test.jpg",
                "gitee_markdown": "![test](https://gitee.com/Atopes/img-hosting/raw/master/test.jpg)",
                # 使用代理URL
                "proxy_url": proxy_url,
                "proxy_markdown": f"![test]({proxy_url})"
            }
        }
    )


@app.get("/geocode")
async def geocode_cities(
        cities: str = Query(..., description="城市名称，多个城市用逗号分隔，例如：北京,上海"),
        max_retries: int = Query(3, ge=1, le=5, description="最大重试次数（1-5）"),
        retry_delay: float = Query(1.0, ge=0.1, le=5.0, description="重试延迟时间（秒）")
):
    """
    地理编码接口 - 将城市名称转换为经纬度坐标
    
    Args:
        cities: 城市名称字符串，多个城市用逗号分隔（例如："北京" 或 "北京,上海" 或 "北京,上海,广州"）
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试延迟时间（秒），默认1秒
        
    Returns:
        JSONResponse: 动态结构，根据城市数量生成对应的字段
        
    Example:
        单个城市:
        GET /geocode?cities=北京
        返回: {"success": true, "location": {"city1_lng": 116.40717, "city1_lat": 39.90469}}
        
        多个城市:
        GET /geocode?cities=北京,上海
        返回: {"success": true, "location": {"city1_lng": 116.40717, "city1_lat": 39.90469, "city2_lng": 121.4737, "city2_lat": 31.23037}}
    """
    try:
        # 分割城市名称（去除空格）
        city_list = [city.strip() for city in cities.split(',') if city.strip()]

        if not city_list:
            raise HTTPException(status_code=400, detail="城市参数不能为空")

        logger.info(f"开始地理编码: {city_list}")

        # 构建动态的 location 字典
        location = {}
        failed_cities = []

        for i, city in enumerate(city_list, start=1):
            logger.info(f"正在编码城市 {i}: {city}")

            # 调用地理编码API
            result = baidu_map_api.geocode(
                address=city,
                max_retries=max_retries,
                retry_delay=retry_delay
            )

            if result:
                # 动态添加 city1_lng, city1_lat, city2_lng, city2_lat...
                location[f"city{i}_lng"] = result['lng']
                location[f"city{i}_lat"] = result['lat']
            else:
                failed_cities.append(city)
                # 失败时也添加字段，但值为 None
                location[f"city{i}_lng"] = None
                location[f"city{i}_lat"] = None

        # 判断是否全部成功
        success = len(failed_cities) == 0
        success_count = len(city_list) - len(failed_cities)

        logger.info(f"地理编码完成: 成功 {success_count}/{len(city_list)}")

        response_data = {
            "success": success,
            "location": location
        }

        # 构建message字段记录日志信息
        if success:
            response_data["message"] = f"地理编码成功，共处理 {len(city_list)} 个城市，全部成功"
        elif success_count > 0:
            response_data["failed_cities"] = failed_cities
            response_data["message"] = f"地理编码部分成功，成功 {success_count}/{len(city_list)} 个城市，失败城市: {', '.join(failed_cities)}"
        else:
            response_data["failed_cities"] = failed_cities
            response_data["message"] = f"地理编码全部失败，共 {len(city_list)} 个城市均无法获取坐标"

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"地理编码时发生错误: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "location": {},
                "message": f"地理编码服务异常: {str(e)}"
            },
            status_code=500
        )


@app.post("/route/plan")
async def plan_route_endpoint(request_data: Dict = Body(...)):
    """
    路线规划接口 - 规划两点之间的路线并生成地图
    
    输入格式（使用地理编码接口返回的location对象）:
        {
            "location": {
                "city1_lng": 116.40717,
                "city1_lat": 39.90469,
                "city2_lng": 121.4737,
                "city2_lat": 31.23037
            },
            "travel_model": "自驾",
            "output_path": "dataset/route_map.html"  (可选)
        }
    
    Returns:
        JSONResponse: 包含地图路径和路线文本的响应
        
    Example:
        POST /route/plan
        Body: {
            "location": {
                "city1_lng": 116.40717,
                "city1_lat": 39.90469,
                "city2_lng": 121.4737,
                "city2_lat": 31.23037
            },
            "travel_model": "自驾"
        }
        返回: {
            "success": true,
            "html_path": "E:\\TourAgent\\dataset\\route_map.html",
            "route_text": "路线指引文本..."
        }
    """
    try:
        # 获取location对象
        location = request_data.get("location")
        if not location:
            raise HTTPException(
                status_code=400,
                detail="必须提供location对象"
            )
        
        # 获取出行方式和输出路径
        travel_model = request_data.get("travel_model", "自驾")
        output_path = request_data.get("output_path", "dataset/route_map.html")
        
        # 解析坐标 - 起点使用city1，终点使用city2
        origin_lng = location.get("city1_lng")
        origin_lat = location.get("city1_lat")
        destination_lng = location.get("city2_lng")
        destination_lat = location.get("city2_lat")
        
        if not all([origin_lng, origin_lat, destination_lng, destination_lat]):
            raise HTTPException(
                status_code=400,
                detail="location对象必须包含 city1_lng, city1_lat, city2_lng, city2_lat"
            )
        
        logger.info(f"开始路线规划: ({origin_lat},{origin_lng}) -> ({destination_lat},{destination_lng}), 方式: {travel_model}")
        
        # 构建坐标字典
        origin = {"lat": origin_lat, "lng": origin_lng}
        destination = {"lat": destination_lat, "lng": destination_lng}
        
        # 调用路线规划API
        route_data = baidu_map_api.plan_route(origin, destination, travel_model)
        
        if not route_data:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "路线规划失败"
                },
                status_code=500
            )
        
        # 生成地图并提取路线文本
        result = baidu_map_api.generate_route_map(route_data, output_path)
        
        if not result:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "地图生成失败"
                },
                status_code=500
            )
        
        logger.info(f"路线规划成功，地图已保存到: {result['html_path']}")
        
        return JSONResponse(
            content={
                "success": True,
                "html_path": result['html_path'],
                "route_text": result['route_text']
            }
        )
        
    except Exception as e:
        logger.error(f"路线规划时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"路线规划失败: {str(e)}")


@app.post("/aggregate")
async def aggregate_variables(request_data: Dict = Body(..., description="包含任意参数的字典")):
    """
    变量聚合器接口 - 将多个参数合并到一个JSON对象中
    
    Args:
        request_data: 包含任意参数的字典，例如：
                    {
                        "原始文本": "这是一段原始文本",
                        "路径规划": "从A点到B点的路线",
                        "其他参数": 123
                    }
        
    Returns:
        JSONResponse: 包含所有输入参数的响应
        
    Example:
        POST /aggregate
        Body: {
            "原始文本": "这是一段原始文本",
            "路径规划": "从A点到B点的路线",
            "数字参数": 123,
            "布尔参数": true
        }
        返回: {
            "success": true,
            "data": {
                "原始文本": "这是一段原始文本",
                "路径规划": "从A点到B点的路线",
                "数字参数": 123,
                "布尔参数": true
            }
        }
    """
    try:
        logger.info(f"开始聚合变量，输入参数: {request_data}")
        
        if not request_data:
            raise HTTPException(status_code=400, detail="输入参数不能为空")
        
        # 直接返回输入的参数作为聚合结果
        response_data = {
            "success": True,
            "data": request_data
        }
        
        logger.info(f"变量聚合完成，共聚合 {len(request_data)} 个参数")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"变量聚合时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"变量聚合失败: {str(e)}")


@app.post("/weather")
async def get_weather_by_location(location: Dict = Body(..., description="包含城市经纬度的字典")):
    """
    天气查询接口 - 根据地理编码返回的location数据查询天气
    
    Args:
        location: 地理编码接口返回的location对象，格式如：
                 {"city1_lng": 116.40717, "city1_lat": 39.90469, "city2_lng": 121.4737, "city2_lat": 31.23037}
        
    Returns:
        JSONResponse: 包含各城市天气信息的响应
        
    Example:
        POST /weather
        Body: {"location": {"city1_lng": 116.40717, "city1_lat": 39.90469}}
        返回: {
            "success": true,
            "count": 1,
            "weather": {
                "city1": {
                    "location": "116.40717,39.90469",
                    "weather": {...}
                }
            }
        }
    """
    try:
        logger.info(f"开始查询天气，location数据: {location}")
        
        if not location:
            raise HTTPException(status_code=400, detail="location参数不能为空")
        
        # 解析location中的城市数量
        city_count = 0
        city_coords = {}
        
        # 统计有多少个城市（通过city_lng字段来计数）
        for key in location.keys():
            if key.endswith('_lng'):
                city_num = key.replace('_lng', '')
                city_count += 1
                
                lng = location.get(f"{city_num}_lng")
                lat = location.get(f"{city_num}_lat")
                
                if lng is not None and lat is not None:
                    city_coords[city_num] = f"{lng},{lat}"
                else:
                    city_coords[city_num] = None
        
        if city_count == 0:
            raise HTTPException(status_code=400, detail="location数据格式错误，未找到有效的城市坐标")
        
        logger.info(f"解析到 {city_count} 个城市坐标")
        
        # 查询每个城市的天气
        weather_data = {}
        failed_cities = []
        success_count = 0
        
        for city_num, coords in city_coords.items():
            if coords is None:
                logger.warning(f"{city_num} 的坐标为空，跳过查询")
                weather_data[city_num] = {
                    "location": None,
                    "weather": None,
                    "error": "坐标为空"
                }
                failed_cities.append(city_num)
                continue
            
            try:
                logger.info(f"正在查询 {city_num} 的天气，坐标: {coords}")
                weather_result = get_weather(coords)
                
                if weather_result:
                    weather_data[city_num] = {
                        "location": coords,
                        "weather": weather_result
                    }
                    success_count += 1
                else:
                    weather_data[city_num] = {
                        "location": coords,
                        "weather": None,
                        "error": "天气查询失败"
                    }
                    failed_cities.append(city_num)
                    
            except Exception as e:
                logger.error(f"查询 {city_num} 天气时发生错误: {str(e)}")
                weather_data[city_num] = {
                    "location": coords,
                    "weather": None,
                    "error": str(e)
                }
                failed_cities.append(city_num)
        
        # 判断是否全部成功
        success = len(failed_cities) == 0
        
        logger.info(f"天气查询完成: 成功 {success_count}/{city_count}")
        
        response_data = {
            "success": success,
            "count": city_count,
            "success_count": success_count,
            "weather": weather_data
        }
        
        # 如果有失败的城市，添加错误信息
        if failed_cities:
            response_data["failed_cities"] = failed_cities
            response_data["message"] = f"部分城市天气查询失败: {', '.join(failed_cities)}"
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"天气查询时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"天气查询失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4399)

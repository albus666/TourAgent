import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
import os
from moudle.ctrip import CtripAPIHandler
from moudle.mcp.mcp_api import BaiduMapAPI


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
        spots = ctrip_handler.get_city_spots(cityName, count)
        
        if not spots:
            return JSONResponse(
                content={
                    "success": True,
                    "cityName": cityName,
                    "count": 0,
                    "spots": [],
                    "message": f"未找到{cityName}的景点信息"
                }
            )
        
        # 格式化返回数据
        formatted_spots = []
        for spot in spots:
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
                "spots": formatted_spots
            }
        )
        
    except Exception as e:
        logger.error(f"查询城市景点时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


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
        
        if not detail:
            return JSONResponse(
                content={
                    "success": False,
                    "keyword": keyword,
                    "message": "未找到景点信息"
                }
            )
        
        # 格式化评论数据
        formatted_comments = []
        for comment in detail.get("comments", []):
            formatted_comments.append({
                "userNick": comment.get("userNick"),
                "userImage": comment.get("userImage"),
                "score": comment.get("score"),
                "content": comment.get("content"),
                "publishTypeTag": comment.get("publishTypeTag"),
                "ipLocatedName": comment.get("ipLocatedName"),
                "imageUrl": comment.get("imageUrl")
            })
        
        logger.info(f"成功获取景点详情，评论数: {detail.get('commentCount', 0)}")
        
        response_data = {
            "success": True,
            "keyword": detail.get("keyword"),
            "poiId": detail.get("poiId"),
            "commentCount": detail.get("commentCount"),
            "comments": formatted_comments
        }
        
        # 如果有错误信息，也包含进去
        if "error" in detail:
            response_data["warning"] = detail["error"]
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"查询景点详情时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.get("/setting")
def get_setting():
    """
    获取旅游规划助手的配置信息
   
    Returns:
        JSONResponse: 包含配置信息的响应
    """
    try:
        # 读取JSON文件
        json_path = os.path.join(os.path.dirname(__file__), "dataset", "旅游规划助手.json")
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
        
        logger.info(f"地理编码完成: 成功 {len(city_list) - len(failed_cities)}/{len(city_list)}")
        
        response_data = {
            "success": success,
            "location": location
        }
        
        # 如果有失败的城市，添加错误信息
        if failed_cities:
            response_data["failed_cities"] = failed_cities
            response_data["message"] = f"部分城市编码失败: {', '.join(failed_cities)}"
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"地理编码时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"地理编码失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4399)

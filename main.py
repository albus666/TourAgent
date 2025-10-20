import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from moudle.ctrip import CtripAPIHandler


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="旅游规划助手API",
    description="提供城市景点推荐和详情查询服务",
    version="2.0.0"
)

# 初始化携程API处理器
ctrip_handler = CtripAPIHandler()

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4399)

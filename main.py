import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import List
import jinja2
import os
from attraction_service import get_attractions
from search_service import get_attractions as search_attractions

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="景点搜索服务",
    description="提供城市景点信息搜索服务",
    version="1.0.0"
)

# 设置Jinja2环境
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=True
)


def parse_city_list(city_names: str) -> List[str]:
    """解析城市名称列表"""
    if not city_names:
        raise HTTPException(status_code=400, detail="城市名称不能为空")
    return [city.strip() for city in city_names.split(",") if city.strip()]


def parse_sight_list(sight_names: str) -> List[str]:
    """解析景点名称列表"""
    if not sight_names:
        raise HTTPException(status_code=400, detail="景点名称不能为空")
    return [sight.strip() for sight in sight_names.split(",") if sight.strip()]


@app.get("/search")
async def search_attractions_endpoint(cityNames: str):
    """
    搜索景点信息
    
    Args:
        cityNames (str): 城市名称，多个城市用逗号分隔
        
    Returns:
        JSONResponse: 包含景点信息的响应
    """
    try:
        # 解析城市列表
        cities = parse_city_list(cityNames)
        if not cities:
            raise HTTPException(status_code=400, detail="未提供有效的城市名称")

        # 获取景点信息
        formatted_text = search_attractions(cities)

        # 返回格式化后的文本
        return JSONResponse(
            content={
                "message": formatted_text
            }
        )

    except HTTPException as e:
        logger.error(f"搜索景点时发生错误: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"搜索景点时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索景点时发生错误: {str(e)}")


@app.get("/attraction")
async def get_attraction_details(sightNames: str):
    """
    获取景点详细信息
    :param sightNames: 景点名称列表，用逗号分隔
    :return: 景点详细信息列表
    """
    try:
        sights = parse_sight_list(sightNames)
        logger.info(f"开始处理景点: {sights}")

        # 获取景点详细信息
        attractions = get_attractions(sights)

        # 使用模板渲染文本
        template = jinja_env.get_template("attraction_detail.jinja2")
        formatted_text = template.render(attractionList=attractions)

        return JSONResponse(
            content={
                "message": formatted_text
            }
        )
    except Exception as e:
        logger.error(f"获取景点详情时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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

    uvicorn.run(app, host="0.0.0.0", port=8000)

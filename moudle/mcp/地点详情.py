"""
地点详情检索服务
根据百度地图的 uid 查询地点详细信息
"""
import requests
import json


def get_place_detail(uid: str) -> dict:
    """
    查询地点详情
    
    参数:
        uid: 地点的唯一标识符
        
    返回:
        dict: 地点详情信息
    """
    # API 配置
    url = "https://api.map.baidu.com/place/v2/detail"
    params = {
        "output": "json",
        "ak": "Hu01H6gQJVUo2i0ZSoxjwUIw7Nw09WnE",
        "scope": "2",
        "uid": uid
    }
    
    try:
        # 发送 HTTP GET 请求
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # 解析响应
        data = response.json()
        
        # 提取 result 字段
        if "result" in data:
            result = data["result"]
            return {"result": str(result)}
        else:
            return {"error": "未找到 result 字段", "raw_data": data}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"请求失败: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {str(e)}"}


def main():
    """主函数，用于测试"""
    # 示例用法
    uid = input("请输入地点 UID: ").strip()
    
    if not uid:
        print("错误: UID 不能为空")
        return
    
    print(f"\n正在查询地点详情 (UID: {uid})...")
    result = get_place_detail(uid)
    
    print("\n查询结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


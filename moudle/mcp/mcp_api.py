"""
百度地图 API 封装 - 使用面向对象方式整合所有功能
包括：地理编码、路线规划、地点详情、路径可视化
"""
from typing import Dict, Any, Optional
import requests
import os
import folium
import time
import re


class BaiduMapAPI:
    """百度地图 API 封装类"""
    
    def __init__(self, ak: str = "Hu01H6gQJVUo2i0ZSoxjwUIw7Nw09WnE"):
        """
        初始化百度地图 API
        
        参数:
            ak: 百度地图 API 密钥
        """
        self.ak = ak
        self.base_url = "https://api.map.baidu.com"
        # 获取项目根目录（此文件在 moudle/mcp/ 下）
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 出行方式映射
        self.travel_model_map = {
            '自驾': 'driving',
            '骑行': 'riding',
            '步行': 'walking',
            '公共交通': 'transit'
        }


    def geocode(self, address: str, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        地理编码 - 将地址转换为经纬度坐标（支持失败自动重试）
        
        参数:
            address: 地址（如：北京市海淀区、上海）
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试延迟时间（秒），默认1秒
        
        返回:
            包含经纬度的字典: {'lat': 纬度, 'lng': 经度}
            失败返回 None
        """
        url = f"{self.base_url}/geocoding/v3"
        params = {
            "output": "json",
            "ak": self.ak,
            "address": address
        }
        
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                # 请求成功
                if data.get('status') == 0 and 'result' in data:
                    location = data['result']['location']
                    if attempt > 1:
                        print(f"✅ 地理编码成功（第{attempt}次尝试）")
                    return {
                        'lat': location['lat'],
                        'lng': location['lng']
                    }
                else:
                    # API返回错误
                    error_msg = data.get('message', '未知错误')
                    last_error = f"API错误: {error_msg}"
                    
                    if attempt < max_retries:
                        print(f"⚠️  地理编码失败（第{attempt}次尝试）: {error_msg}，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                    else:
                        print(f"❌ 地理编码失败（已重试{max_retries}次）: {error_msg}")
                        
            except requests.Timeout:
                last_error = "请求超时"
                if attempt < max_retries:
                    print(f"⚠️  请求超时（第{attempt}次尝试），{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ 请求超时（已重试{max_retries}次）")
                    
            except requests.RequestException as e:
                last_error = f"网络错误: {str(e)}"
                if attempt < max_retries:
                    print(f"⚠️  网络错误（第{attempt}次尝试）: {e}，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ 网络错误（已重试{max_retries}次）: {e}")
                    
            except Exception as e:
                last_error = f"未知异常: {str(e)}"
                if attempt < max_retries:
                    print(f"⚠️  未知异常（第{attempt}次尝试）: {e}，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ 未知异常（已重试{max_retries}次）: {e}")
        
        # 所有重试都失败
        print(f"🚫 地理编码彻底失败 - 地址: {address}, 最后错误: {last_error}")
        return None
    
    def plan_route(self, origin: Dict[str, float], destination: Dict[str, float], 
                   travel_model: str = '驾车') -> Optional[Dict[str, Any]]:
        """
        路线规划
        
        参数:
            origin: 起点坐标字典 {'lat': 纬度, 'lng': 经度}
            destination: 终点坐标字典 {'lat': 纬度, 'lng': 经度}
            travel_model: 出行方式（驾车、骑行、步行、公共交通）
        
        返回:
            路线规划数据，失败返回 None
        """
        model = self.travel_model_map.get(travel_model)
        if not model:
            print(f"不支持的出行方式: {travel_model}")
            return None
        
        url = f"{self.base_url}/directionlite/v1/{model}"
        
        # 百度地图路线规划API使用"纬度,经度"格式
        origin_str = f"{origin['lat']},{origin['lng']}"
        destination_str = f"{destination['lat']},{destination['lng']}"
        
        params = {
            'output': 'json',
            'ak': self.ak,
            'origin': origin_str,
            'destination': destination_str,
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 0:
                return data
            else:
                print(f"路线规划失败: {data.get('message', '未知错误')}")
                return None
        except Exception as e:
            print(f"路线规划请求异常: {e}")
            return None
    
    def get_place_detail(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        查询地点详情
        
        参数:
            uid: 地点的唯一标识符
        
        返回:
            地点详情信息字典，失败返回 None
        """
        url = f"{self.base_url}/place/v2/detail"
        params = {
            "output": "json",
            "ak": self.ak,
            "scope": "2",
            "uid": uid
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 0 and 'result' in data:
                return data['result']
            else:
                print(f"地点详情查询失败: {data.get('message', '未知错误')}")
                return None
        except Exception as e:
            print(f"地点详情请求异常: {e}")
            return None
    
    def generate_route_map(self, route_data: Dict[str, Any], output_path: str = 'route_map.html', 
                          sample_rate: int = 10) -> Optional[Dict[str, Any]]:
        """
        根据路线规划数据生成可视化地图HTML文件
        
        参数:
            route_data: 路线规划API返回的数据（plan_route方法的返回值）
            output_path: 输出HTML文件路径（支持相对路径和绝对路径）
            sample_rate: 路径点采样率（每N个点取1个，减少地图大小）
        
        返回:
            成功返回包含文件路径和路线文本的字典: {'html_path': 路径, 'route_text': 路线指引文本}
            失败返回 None
        """
        try:
            # 处理路径：如果是相对路径，则相对于项目根目录
            if not os.path.isabs(output_path):
                output_path = os.path.join(self.project_root, output_path)
            
            route = route_data['result']['routes'][0]
            origin = route_data['result']['origin']
            destination = route_data['result']['destination']
            steps = route['steps']
            
            # 收集所有路径点
            all_points = []
            for step in route['steps']:
                path = step['path']
                coords = path.split(';')
                for coord in coords:
                    lng, lat = coord.split(',')
                    all_points.append([float(lat), float(lng)])
            
            # 简化路径
            simplified_points = all_points[::sample_rate]
            if all_points[0] not in simplified_points:
                simplified_points.insert(0, all_points[0])
            if all_points[-1] not in simplified_points:
                simplified_points.append(all_points[-1])
            
            print(f"简化后路径点数: {len(simplified_points)}")
            
            # 创建地图
            m = folium.Map(
                tiles='OpenStreetMap',
                control_scale=True,
                zoom_control=True,
                scrollWheelZoom=False
            )
            
            # 自动调整边界
            southwest = [min(destination['lat'], origin['lat']), min(origin['lng'], destination['lng'])]
            northeast = [max(origin['lat'], destination['lat']), max(origin['lng'], destination['lng'])]
            m.fit_bounds([southwest, northeast], padding=[50, 50])
            
            # 绘制路线
            folium.PolyLine(
                simplified_points,
                color='#2E86DE',
                weight=4,
                opacity=0.8,
            ).add_to(m)
            
            # 起点标记
            folium.Marker(
                [origin['lat'], origin['lng']],
                popup='<b>起点</b>',
                icon=folium.Icon(color='green', icon='play', prefix='fa'),
                tooltip='起点'
            ).add_to(m)
            
            # 终点标记
            folium.Marker(
                [destination['lat'], destination['lng']],
                popup='<b>终点</b>',
                icon=folium.Icon(color='red', icon='stop', prefix='fa'),
                tooltip='终点'
            ).add_to(m)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 保存HTML
            m.save(output_path)
            
            # 显示相对路径（更友好）
            try:
                rel_path = os.path.relpath(output_path, self.project_root)
            except ValueError:
                rel_path = output_path
            
            print(f"✅ 地图已保存到 {rel_path}")
            print(f"📏 总距离: {route['distance'] / 1000:.1f}公里")
            print(f"⏱️  预计时长: {route['duration'] / 3600:.1f}小时")
            
            # 处理路线指引文本：提取instruction并去掉HTML标签
            route_text = ""
            info_str = f"📏 总距离: {route['distance'] / 1000:.1f}公里\n⏱️  预计时长: {route['duration'] / 3600:.1f}小时\n\n路线指引:\n"
            
            for i, step in enumerate(steps, 1):
                instruction = step.get("instruction", "")
                # 使用正则表达式去掉所有HTML标签
                simplified_instruction = re.sub(r'<[^>]+>', '', instruction)
                route_text += f"{i}. {simplified_instruction}\n"
            
            # 返回包含文件路径和处理后文本的字典
            return {
                "html_path": output_path,
                "route_text": info_str + route_text
            }
            
        except KeyError as e:
            print(f"路线数据格式错误，缺少字段: {e}")
            return None
        except Exception as e:
            print(f"生成地图失败: {e}")
            return None


if __name__ == '__main__':
    # 使用示例
    api = BaiduMapAPI()
    
    # 1. 地理编码 - 将地址转换为坐标
    print("="*50)
    print("测试地理编码")
    print("="*50)
    origin_coord = api.geocode("北京市")
    print(f"北京坐标: {origin_coord}")
    
    dest_coord = api.geocode("上海市")
    print(f"上海坐标: {dest_coord}")
    
    if origin_coord and dest_coord:
        # 2. 路线规划
        print("\n" + "="*50)
        print("测试路线规划")
        print("="*50)
        route_data = api.plan_route(origin_coord, dest_coord, travel_model='自驾')
        
        if route_data:
            # 3. 生成地图HTML
            print("\n" + "="*50)
            print("生成路线地图")
            print("="*50)
            result = api.generate_route_map(
                route_data, 
                output_path='dataset/route_map.html',
                sample_rate=10
            )
            
            if result:
                print("\n✅ HTML地图生成完成！")
                print(f"📄 HTML文件: {result['html_path']}")
                print("\n📝 路线文本：")
                print(result['route_text'])
                print("\n💡 如需保存为图片，请使用: moudle.utils.map_utils.save_map_as_image()")

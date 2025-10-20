import json
import folium
import os
import time

# 读取result文件
with open('result', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    data = eval(lines[1])

route = data['result']['routes'][0]
origin = data['result']['origin']
destination = data['result']['destination']

# 收集所有路径点
all_points = []
for step in route['steps']:
    path = step['path']
    coords = path.split(';')
    for coord in coords:
        lng, lat = coord.split(',')
        all_points.append([float(lat), float(lng)])

# 简化路径
sample_rate = 10
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

# 保存HTML
html_file = 'route_map.html'
m.save(html_file)
print(f"✅ 地图已保存到 {html_file}")
print(f"📏 总距离: {route['distance'] / 1000:.1f}公里")
print(f"⏱️  预计时长: {route['duration'] / 3600:.1f}小时")

# 保存为图片（使用当前目录下的 EdgeDriver）
try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options

    print("\n正在生成图片...")

    # Edge 选项
    edge_options = Options()
    edge_options.add_argument('--headless')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--disable-dev-shm-usage')
    edge_options.add_argument('--window-size=1920,1080')
    edge_options.add_argument('--disable-gpu')

    # 使用当前目录下的 EdgeDriver
    service = Service('./msedgedriver.exe')
    driver = webdriver.Edge(service=service, options=edge_options)

    # 加载 HTML 文件
    driver.get('file:///' + os.path.abspath(html_file).replace('\\', '/'))

    # 等待地图加载完成
    time.sleep(3)

    # 截图保存
    png_file = 'route_map.png'
    driver.save_screenshot(png_file)
    driver.quit()

    print(f"✅ 图片已保存到 {png_file}")

except ImportError:
    print("\n❌ 需要安装 selenium")
    print("   安装命令: pip install selenium")

except Exception as e:
    print(f"\n❌ 截图失败: {e}")
    print("提示：")
    print("  1. 确保 msedgedriver.exe 在当前目录")
    print("  2. 下载与 Edge 141 匹配的驱动: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
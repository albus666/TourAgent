"""
地图工具模块 - 提供地图相关的辅助功能
包括：地图截图保存等
"""
import os
import time


def save_map_as_image(html_path: str, png_path: str = None, wait_time: int = 8) -> bool:
    """
    将HTML地图保存为PNG图片
    
    参数:
        html_path: HTML文件路径
        png_path: 输出PNG文件路径，默认为与HTML同名的.png文件
        wait_time: 等待地图加载的时间（秒），默认8秒
    
    返回:
        成功返回 True，失败返回 False
    """
    # 设置默认PNG输出路径
    if png_path is None:
        # 将 HTML 路径的扩展名改为 .png
        png_path = html_path.rsplit('.', 1)[0] + '.png'
    
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
        
        # 使用 EdgeDriver
        # 尝试从 dataset 目录找驱动
        driver_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset', 'msedgedriver.exe')
        if os.path.exists(driver_path):
            service = Service(driver_path)
            driver = webdriver.Edge(service=service, options=edge_options)
        else:
            driver = webdriver.Edge(options=edge_options)
        
        # 加载 HTML 文件
        driver.get('file:///' + os.path.abspath(html_path).replace('\\', '/'))
        
        # 等待地图加载完成（需要从服务器下载瓦片）
        print(f"  等待地图瓦片加载（{wait_time}秒）...")
        time.sleep(wait_time)
        
        # 截图保存
        driver.save_screenshot(png_path)
        driver.quit()
        
        print(f"✅ 图片已保存到 {png_path}")
        return True
        
    except ImportError:
        print("\n❌ 需要安装 selenium: pip install selenium")
        return False
    except Exception as e:
        print(f"\n❌ 截图失败: {e}")
        print("提示：")
        print("  1. 确保 msedgedriver.exe 在 dataset/ 目录")
        print("  2. 确保 Edge 浏览器版本与驱动匹配")
        print("  3. 下载驱动: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        return False


if __name__ == '__main__':
    # 测试示例
    test_html = "dataset/route_map.html"
    if os.path.exists(test_html):
        save_map_as_image(test_html)
    else:
        print(f"测试文件不存在: {test_html}")


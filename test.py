import re
import requests

def extract_image_urls(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/123.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = response.apparent_encoding
    html = response.text

    # 匹配背景图片URL
    pattern = re.compile(r'url\(&quot;(https://dimg\d+\.c-ctrip\.com/images/[^\"]+\.jpg)&quot;\)')
    return pattern.findall(html)

if __name__ == "__main__":
    page_url = "https://you.ctrip.com/sight/zhongmu1446088/109563995.html?renderPlatform="
    img_urls = extract_image_urls(page_url)
    for u in img_urls:
        print(u)

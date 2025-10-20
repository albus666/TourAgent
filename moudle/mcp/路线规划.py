import requests

origin = '34.75343885045448,113.63141920733915'
destination = '31.235929042252014,121.48053886017651'
travel_model = '驾车'

model=''
if travel_model=='驾车':
    model='driving'
elif travel_model=='骑行':
    model='riding'
elif travel_model=='步行':
    model='walking'
elif travel_model=='公共交通':
    model='transit'

url = f'https://api.map.baidu.com/directionlite/v1/{model}'

params = {
    'output': 'json',
    'ak':'Hu01H6gQJVUo2i0ZSoxjwUIw7Nw09WnE',
    'origin':origin,
    'destination':destination,
}

response = requests.get(url, params=params)
data = response.json()
print(data)

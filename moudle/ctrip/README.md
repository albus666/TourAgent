# 携程API处理模块

这个模块提供了与携程API交互的功能，包括景点推荐和详情查询。

## 功能

### 1. 基础方法（辅助方法）

#### `_get_poi_id(city_name: str) -> Optional[int]`
获取景点的POI ID

#### `_get_district_id(city_name: str) -> Optional[int]`
获取城市的district ID

### 2. 城市景点推荐

#### `get_city_spots(city_name: str, count: int = 10) -> List[Dict[str, Any]]`
根据城市名获取景点列表推荐

**参数：**
- `city_name`: 城市名称（如："北京"、"上海"）
- `count`: 返回景点数量，默认10个

**返回：**
- 景点卡片列表

**示例：**

```python
from moudle.ctrip import CtripAPIHandler

handler = CtripAPIHandler()
spots = handler.get_city_spots("北京", count=5)
for spot in spots:
    print(spot)
```

### 3. 景点详情查询

#### `get_spot_detail(keyword: str) -> Dict[str, Any]`
获取景点详情和用户评论（读取3个用户的评论）

**参数：**
- `keyword`: 景点关键词（如："故宫"、"长城"）

**返回：**
包含以下字段的字典：
- `keyword`: 搜索关键词
- `poiId`: 景点POI ID
- `comments`: 评论列表（最多3条）
- `commentCount`: 评论数量

**评论对象包含：**
- `userNick`: 用户昵称
- `userImage`: 用户头像
- `score`: 评分
- `content`: 评论内容
- `publishTypeTag`: 发布类型标签
- `ipLocatedName`: IP位置
- `imageUrl`: 如果评论有图片，则附上一张图片链接（没有则为None）

**示例：**

```python
from moudle.ctrip import CtripAPIHandler

handler = CtripAPIHandler()
detail = handler.get_spot_detail("故宫")

print(f"景点: {detail['keyword']}")
print(f"评论数: {detail['commentCount']}")

for i, comment in enumerate(detail['comments'], 1):
    print(f"\n评论 {i}:")
    print(f"  用户: {comment.get('userNick', '匿名')}")
    print(f"  评分: {comment.get('score', 'N/A')}")
    print(f"  内容: {comment.get('content', '')}")
    if comment.get('imageUrl'):
        print(f"  图片: {comment['imageUrl']}")
```

## 使用场景

1. **城市景点推荐** - 用户输入城市名，获取该城市的热门景点列表
2. **景点详情查询** - 用户输入景点关键词，获取景点的详细信息和用户评价

## 注意事项

- 所有方法都使用了携程的公开API
- 评论查询限制为3条，每条评论如果有图片只附上第一张
- 需要网络连接才能正常使用


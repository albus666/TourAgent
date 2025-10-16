import json
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import matplotlib
import os

matplotlib.rc("font", family='Microsoft YaHei')
# 示例数据 - 替换为实际爬取的评论列表

def get_wordcloud(comments: str | list[str]):
    if type(comments) == str:
        json_str = comments.strip('"')
        comments = json.loads(json_str)

    # 1. 加载停用词表
    stopwords_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'cn_stopwords.txt')
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        stopwords = set([line.strip() for line in f])

    # 2. 中文分词处理
    text = ' '.join(comments)
    words = jieba.cut(text)
    filtered_words = [word for word in words if len(word) > 1 and word not in stopwords]

    # 3. 词频统计
    word_counts = Counter(filtered_words)

    # 4. 生成词云
    wc = WordCloud(
        font_path='C:/Windows/Fonts/msyh.ttc',  # 使用系统默认的微软雅黑字体
        background_color='white',
        max_words=200,
        max_font_size=175,
        width=1600,
        height=1200,
        collocations=False,  # 去除重复词语
        scale=1  # 默认分辨率
    ).generate_from_frequencies(word_counts)

    # 5. 保存文件
    output_path = os.path.join(os.path.dirname(__file__), 'comment_wordcloud.png')
    wc.to_file(output_path)
    
    # 关闭所有matplotlib图形，避免资源泄漏
    plt.close('all')

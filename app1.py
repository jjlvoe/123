import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import jieba
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# 提取图表绘制逻辑
def plot_chart(chart_type, df):
    chart_dict = {
        '条形图': px.bar,
        '折线图': px.line,
        '饼图': create_pie_chart,
        '散点图': px.scatter,
        '雷达图': create_radar_chart,
        '树形图': create_treemap,  # 直接调用 create_treemap
        '面积图': px.area
    }
    if chart_type == '饼图':
        fig = chart_dict[chart_type](df)
    elif chart_type == '雷达图':
        fig = chart_dict[chart_type](df)
    elif chart_type == '树形图':
        fig = chart_dict[chart_type](df)  # 不再传递 path 和 values 参数
    elif chart_type == '面积图':
        fig = chart_dict[chart_type](df, x='Word', y='Count')
    else:
        fig = chart_dict[chart_type](df, x='Word', y='Count')
    fig.update_layout(title=f'词频{chart_type}')
    st.plotly_chart(fig)

def create_treemap(df):
    return px.treemap(df, path=['Word'], values='Count')
def create_pie_chart(df):
    return px.pie(df, values='Count', names='Word')

def create_radar_chart(df):
    categories = df['Word'].tolist()
    values = df['Count'].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]], fill='toself'))
    fig.update_layout(title='词频雷达图', polar=dict(radialaxis=dict(visible=True)))
    return fig


# Streamlit页面设置
st.title('文本分析工具')

# 用户输入URL
url = st.text_input('请输入文章的URL')

# 定义通用函数
def fetch_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    except requests.RequestException as e:
        st.error(f"请求错误: {e}")
        return None

def clean_text(text):
    # 先去除HTML标签，再去除标点符号
    text = remove_html_tags(text)
    text = remove_punctuation(text)
    return text

def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def remove_punctuation(text):
    return re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)

def process_text(text):
    words = jieba.lcut(text)
    # 只保留长度大于等于2的词汇
    words = [word for word in words if len(word) >= 1]
    word_counts = Counter(words)
    word_counts = remove_stopwords(word_counts)
    return word_counts

def remove_stopwords(word_counts):
    try:
        # 使用原始字符串来表示路径，并确保使用正确的路径
        stopwords_path = r"C:\Users\32595\Desktop\python\stopwords.txt"
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            stopwords = [line.strip() for line in f.readlines()]
        return Counter({word: count for word, count in word_counts.items() if word not in stopwords})
    except FileNotFoundError:
        st.error("未找到停用词文件，将不去除停用词。")
        return word_counts

def filter_low_freq_words(word_counts, min_freq):
    return Counter({word: count for word, count in word_counts.items() if count >= min_freq})

def display_top_words(word_counts, top_n=20):
    top_words = word_counts.most_common(top_n)
    st.write("词频排名前20的词汇：")
    for word, count in top_words:
        st.write(f"{word}: {count}")

# 如果用户输入了URL，开始处理
if url:
    text = fetch_text_from_url(url)
    if text is None:
        st.error("无法获取文本内容，请检查URL或网络连接。")
    else:
        clean_text = clean_text(text)
        st.subheader('清洁后的文本内容')
        st.text_area('清洁后的文本内容', clean_text, height=300)

        word_counts = process_text(clean_text)
        min_freq = st.sidebar.slider('设置最低词频阈值', 1, 100, 5)
        filtered_word_counts = filter_low_freq_words(word_counts, min_freq)

        # 确保Word列是字符串类型，Count列是整数类型
        df_word_counts = pd.DataFrame(list(filtered_word_counts.items()), columns=['Word', 'Count'])
        df_word_counts['Word'] = df_word_counts['Word'].astype(str)
        df_word_counts['Count'] = df_word_counts['Count'].astype(int)

        chart_type = st.sidebar.selectbox('选择图表类型', ['条形图', '折线图', '饼图', '散点图', '雷达图', '树形图', '面积图'])
        plot_chart(chart_type, df_word_counts)

        display_top_words(filtered_word_counts)
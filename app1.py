import streamlit as st
import plotly.express as px
import pandas as pd
import jieba
from collections import Counter
import requests
from bs4 import BeautifulSoup
import re
from pyecharts.charts import Pie, Bar, Line, Scatter
from pyecharts import options as opts
from pyecharts.globals import ThemeType
import streamlit.components.v1 as components

# 提取图表绘制逻辑
def plot_chart(chart_type, df):
    chart_dict = {
        '条形图': px.bar,
        '折线图': px.line,
        '饼图': create_pie_chart_plotly,
        '散点图': px.scatter,
        '雷达图': create_radar_chart,
        '树形图': create_treemap,
        '面积图': px.area
    }
    if chart_type in ['饼图', '雷达图', '树形图']:
        fig = chart_dict[chart_type](df)
    elif chart_type == '面积图':
        fig = chart_dict[chart_type](df, x='Word', y='Count')
    else:
        fig = chart_dict[chart_type](df, x='Word', y='Count')
    fig.update_layout(title=f'词频{chart_type}')
    st.plotly_chart(fig)

# 使用 Plotly 创建饼图
def create_pie_chart_plotly(df):
    return px.pie(df, values='Count', names='Word')

# 使用 Pyecharts 创建饼图
def create_pie_chart_pyecharts(df):
    data = [list(z) for z in zip(df['Word'].astype(str), df['Count'])]
    c = (
        Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
        .add("", data_pair=data)
        .set_global_opts(title_opts=opts.TitleOpts(title="词频饼图"))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    )
    return c.render_embed()

# 使用 Pyecharts 创建柱状图
def create_bar_chart_pyecharts(df):
    bar = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
        .add_xaxis(df['Word'].astype(str).tolist())
        .add_yaxis("词频", df['Count'].tolist())
        .set_global_opts(title_opts=opts.TitleOpts(title="词频柱状图"))
    )
    return bar.render_embed()

# 使用 Pyecharts 创建折线图
def create_line_chart_pyecharts(df):
    line = (
        Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
        .add_xaxis(df['Word'].astype(str).tolist())
        .add_yaxis("词频", df['Count'].tolist())
        .set_global_opts(title_opts=opts.TitleOpts(title="词频折线图"))
    )
    return line.render_embed()

# 使用 Pyecharts 创建散点图
def create_scatter_chart_pyecharts(df):
    scatter = (
        Scatter(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
        .add_xaxis(df['Word'].astype(str).tolist())
        .add_yaxis("词频", df['Count'].tolist())
        .set_global_opts(title_opts=opts.TitleOpts(title="词频散点图"))
    )
    return scatter.render_embed()

def create_treemap(df):
    return px.treemap(df, path=['Word'], values='Count')

def create_radar_chart(df):
    categories = df['Word'].tolist()
    values = df['Count'].tolist()
    # 修改了这里，移除了 fill 参数
    fig = px.scatter_polar(df, r='Count', theta='Word')
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
    # 使用BeautifulSoup去除HTML标签
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    # 去除非中文字符和空白字符
    text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)
    # 去除多余的空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_text(text):
    words = jieba.lcut(text)
    words = [word for word in words if len(word) >= 1 and word.strip() != '']
    word_counts = Counter(words)
    word_counts = remove_stopwords(word_counts)
    return word_counts

def remove_stopwords(word_counts):
    try:
        with open('stopwords.txt', 'r', encoding='utf-8') as f:
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
        if re.match(r'^[\w\u4e00-\u9fff]+$', word):
            st.write(f"{word}: {count}")
        else:
            st.warning(f"非词汇条目：{word} - {count}")

# 如果用户输入了URL，开始处理
if url:
    text = fetch_text_from_url(url)
    if text is None:
        st.error("无法获取文本内容，请检查URL或网络连接。")
    else:
        clean_text_content = clean_text(text)
        st.subheader('清洁后的文本内容')
        st.text_area('清洁后的文本内容', clean_text_content, height=300)

        word_counts = process_text(clean_text_content)
        min_freq = st.sidebar.slider('设置最低词频阈值', 1, 100, 5)
        filtered_word_counts = filter_low_freq_words(word_counts, min_freq)

        df_word_counts = pd.DataFrame(list(filtered_word_counts.items()), columns=['Word', 'Count'])
        df_word_counts['Word'] = df_word_counts['Word'].astype(str)
        df_word_counts['Count'] = df_word_counts['Count'].astype(int)

        chart_type = st.sidebar.selectbox('选择图表类型', ['条形图', '折线图', '饼图', '散点图', '雷达图', '树形图', '面积图', 'Pyecharts 饼图', 'Pyecharts 柱状图', 'Pyecharts 折线图', 'Pyecharts 散点图'])
        if chart_type.startswith('Pyecharts '):
            chart_func = {
                'Pyecharts 饼图': create_pie_chart_pyecharts,
                'Pyecharts 柱状图': create_bar_chart_pyecharts,
                'Pyecharts 折线图': create_line_chart_pyecharts,
                'Pyecharts 散点图': create_scatter_chart_pyecharts,
            }.get(chart_type, create_pie_chart_pyecharts)
            html = chart_func(df_word_counts)
            components.html(html, height=600)
        else:
            plot_chart(chart_type, df_word_counts)

        display_top_words(filtered_word_counts)
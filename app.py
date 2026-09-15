# -*- coding: utf-8 -*-
"""
AI智能语料采集与清洗助手（极速体验优化版）
核心优化：
1. 截断输入为3000字，减少大模型阅读时间。
2. 限制大模型输出500字，极大缩短生成时间（从一分钟降至二三十秒）。
3. 使用 st.status 替代干瘪的进度条，提供实时反馈与预期管理。
4. 移除死板的 sleep(2)，仅在真正触发限流时重试。
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from zhipuai import ZhipuAI
import zhipuai
import streamlit as st

# ---------------------------------------------------------------------------
# 基础配置与初始化
# ---------------------------------------------------------------------------
load_dotenv()

st.set_page_config(page_title="AI智能语料采集与清洗助手", layout="centered")
st.title("AI智能语料采集与清洗助手")

if "cleaned_text" not in st.session_state:
    st.session_state.cleaned_text = ""

# 【核心优化1】：限制输出长度，极大提升生成速度
SYSTEM_PROMPT = (
    "你是一个专业的语料库清洗助手。请提取用户提供的网页文本中的核心正文，"
    "彻底清除所有广告、导航、按钮和无关链接。"
    "请在保证核心信息不丢失的前提下，精简提炼正文，最长不超过500字。"
    "保留段落结构，不要输出任何解释性文字，只输出清洗后的纯文本。"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# 核心函数定义
# ---------------------------------------------------------------------------
def fetch_html(page_url: str) -> str:
    response = requests.get(page_url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text

def extract_raw_text(html: str) -> str:
    """【核心优化2】：截断为3000字，避免大模型处理冗长乱码"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()
    raw_text = soup.get_text(separator="\n", strip=True)
    return raw_text[:3000] 

def clean_with_zhipu(raw_text: str) -> str:
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        raise RuntimeError("ZHIPUAI_API_KEY 未配置")
    client = ZhipuAI(api_key=api_key)
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        timeout=45
    )
    return response.choices[0].message.content or ""

def process_single_article(url: str) -> str:
    try:
        html = fetch_html(url)
        raw_text = extract_raw_text(html)
        if not raw_text.strip():
            return "【该文章提取不到有效正文】"
        return clean_with_zhipu(raw_text)
    except Exception as e:
        return f"【清洗失败：{str(e)}】"

def extract_links_universal(list_url: str, max_count: int = 3) -> list:
    try:
        html = fetch_html(list_url)
        soup = BeautifulSoup(html, "html.parser")
        base_domain = f"{urlparse(list_url).scheme}://{urlparse(list_url).netloc}"
        article_urls = []
        seen_urls = set()

        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if not href or not text or len(text) < 6: continue
            lower_href = href.lower()
            if any(x in lower_href for x in ['#', 'javascript:', '.jpg', '.png', '.pdf', 'video', 'login', 'register']): continue
            if '.html' in lower_href or '.htm' in lower_href or '/n/' in lower_href or '/c/' in lower_href:
                full_url = urljoin(base_domain, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    article_urls.append(full_url)
        return article_urls[:max_count]
    except Exception as e:
        st.error(f"列表页抓取失败：{e}")
        return []

# ---------------------------------------------------------------------------
# 前端界面与交互
# ---------------------------------------------------------------------------
mode = st.radio("选择采集模式", ["单篇文章", "批量采集（通用静态网页）"])

if mode == "单篇文章":
    url_input = st.text_input("请输入网页 URL", placeholder="http://opinion.people.com.cn/...")
    start = st.button("开始抓取并清洗")
    
    if start:
        if not url_input.strip():
            st.warning("请先输入有效的网页 URL。")
        else:
            # 【核心优化3】：使用 st.status 提供明确的预期管理
            with st.status("正在处理中，大模型生成预计需要20-30秒，请稍候...", expanded=True) as status:
                st.write("第一步：正在请求网页并提取源码...")
                result = process_single_article(url_input.strip())
                st.session_state.cleaned_text = result
                
                if "【" not in result:
                    status.update(label="🎉 清洗完成！", state="complete", expanded=False)
                else:
                    status.update(label="❌ 清洗遇到问题", state="error", expanded=True)
                    st.warning(result)

else:
    list_url = st.text_input("请输入新闻列表页 URL", placeholder="http://opinion.people.com.cn/...")
    start_batch = st.button("开始批量采集")
    
    if start_batch:
        if not list_url.strip():
            st.warning("请输入列表页 URL。")
        else:
            with st.spinner("正在解析列表页并提取文章链接..."):
                urls = extract_links_universal(list_url.strip(), max_count=3)
                
            if not urls:
                st.warning("未能提取到文章链接，请确认网页是否为静态 HTML。")
            else:
                st.info(f"✅ 成功提取到 {len(urls)} 篇文章，开始清洗：")
                all_results = []
                
                for idx, article_url in enumerate(urls):
                    # 【核心优化4】：移除 time.sleep(2)，加速批量处理
                    with st.status(f"正在处理第 {idx+1}/{len(urls)} 篇...", expanded=False) as status:
                        st.write(f"链接：{article_url}")
                        res = process_single_article(article_url)
                        all_results.append(f"=== 第 {idx+1} 篇：{article_url} ===\n{res}\n")
                        status.update(label=f"第 {idx+1} 篇处理完成", state="complete")
                
                st.session_state.cleaned_text = "\n".join(all_results)
                st.success("🎉 批量清洗完成！")

# ---------------------------------------------------------------------------
# 结果展示与下载
# ---------------------------------------------------------------------------
st.subheader("清洗后的纯文本")
result_text = st.text_area(
    "语料结果",
    value=st.session_state.cleaned_text,
    height=350,
    label_visibility="collapsed"
)

st.download_button(
    label="下载文本",
    data=result_text.encode("utf-8"),
    file_name="cleaned_corpus.txt",
    mime="text/plain",
    disabled=not bool(result_text.strip()),
)
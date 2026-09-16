# ai-corpus-extractor
# 🧠 AI 智能语料采集与清洗助手

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 面向文科/语言学研究者的一站式零代码语料提纯工具。输入网页 URL，一键抓取并清洗网页排版噪音，输出学术级纯净文本。

---

## 🎬 项目演示

👉(https://github.com/Zong-sy/ai-corpus-extractor/issues/1#issue-5469599956)

---

## ✨ 核心功能

- **批量采集**：支持输入新闻列表页 URL，自动提取前 3 条详情链接并批量清洗。
- **AI 语义提纯**：基于智谱 `glm-4-flash` 大模型，精准剔除导航栏、页脚、“责任编辑”等排版噪音。
- **异常隔离**：内置 `try-except` 与超时熔断，单篇失败自动跳过，不中断整个任务。
- **一键下载**：清洗后的结构化纯文本可直接导出为 `.txt` 文件。

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone 你的仓库链接
cd 你的项目文件夹
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from datetime import datetime

# 要抓取的产品页面
url = "https://www.kjell.com/se/produkter/sakerhet-overvakning/kameraovervakning/overvakningskameror/natverkskameror/tp-link-tapo-c200-overvakningskamera-med-wifi-p62284"

def extract_stock_info(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # 查找库存信息区域
    container = soup.find("div", class_="product__availability")  # 根据 kjell 页面结构选定
    if not container:
        return {"Online": "N/A", "Butik": "N/A"}

    # 获取库存信息文字
    text = container.get_text(separator="\n", strip=True)
    lines = text.split("\n")

    # 提取信息
    online = next((l for l in lines if "st" in l or "dagars" in l), "N/A")
    butik = next((l for l in lines if "butiker" in l), "N/A")

    return {
        "Online": online,
        "Butik": butik
    }

# Streamlit 页面配置
st.set_page_config(page_title="Kjell Lagerstatus", layout="wide")

st.title("Kjell Lagerstatus – TP-Link Tapo C200")

# 获取数据
data = extract_stock_info(url)
data["Datum"] = datetime.now().strftime("%Y-%m-%d")

# 转换为 DataFrame
df = pd.DataFrame([data])

# 显示表格
st.dataframe(df, use_container_width=True)

# 显示原始链接
st.markdown(f"[Produktlänk]({url})")

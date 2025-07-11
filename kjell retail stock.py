import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from io import BytesIO

URL = "https://www.kjell.com/se/varumarken/tp-link?count=240&sortBy=popularity"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def parse_page(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')

    product_cards = soup.find_all("a", class_="product-card__link")
    records = []

    for card in product_cards:
        name = card.find("div", class_="product-card__title")
        if not name:
            continue
        name = name.text.strip()
        product_url = "https://www.kjell.com" + card['href']

        availability = card.find("div", class_="product-card__availability")
        if availability:
            availability_text = availability.get_text(separator="\n", strip=True)
            online = next((line for line in availability_text.split("\n") if "Online" in line), "Online: N/A")
            butik = next((line for line in availability_text.split("\n") if "butiker" in line), "Finns i 0 butiker")

            # 提取数字
            online_qty = online.replace("Online", "").strip()
            butik_qty = ''.join(filter(str.isdigit, butik))
        else:
            online_qty = "N/A"
            butik_qty = "0"

        records.append({
            "Datum": datetime.now().strftime("%Y-%m-%d"),
            "Produktnamn": name,
            "Produktlänk": product_url,
            "Online": online_qty,
            "Butik": butik_qty
        })

    return pd.DataFrame(records)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="TP-Link Lagerstatus")
    output.seek(0)
    return output

# ---------------- Streamlit UI ----------------

st.set_page_config(page_title="Kjell Lagerstatus", layout="wide")
st.title("📦 TP-Link Produkter – Lagerstatus från Kjell.com")

if st.button("🚀 開始抓取"):
    with st.spinner("抓取中，請稍候..."):
        df = parse_page(URL)
        st.success(f"抓取成功，共獲取 {len(df)} 款產品。")
        st.dataframe(df, use_container_width=True)

        # 导出 Excel 文件
        excel_data = to_excel(df)

        # 下载按钮
        st.download_button(
            label="📥 點擊下載 Excel 檔",
            data=excel_data,
            file_name=f"tp_link_lagerstatus_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import io

# --- 抓取函数 ---
def extract_product_info(product_id, product_name=""):
    url = f"https://www.kjell.com/se/{product_id}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {
            "product_name": product_name,
            "product_id": product_id,
            "product_title": "ERROR",
            "current_price": "ERROR",
            "discount": "ERROR",
            "retailer_id": "ERROR",
            "date": datetime.now().strftime("%Y-%m-%d")
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # 提取字段
    price_meta = soup.find("meta", {"property": "product:price:amount"})
    current_price = price_meta["content"] if price_meta and price_meta.has_attr("content") else ""

    discount_div = soup.find("div", {"data-test-id": "campaign-product-sticker"})
    discount_text = discount_div.get_text(strip=True) if discount_div else ""

    title_meta = soup.find("meta", {"property": "og:title"})
    product_title = title_meta["content"] if title_meta and title_meta.has_attr("content") else ""

    retailer_id_meta = soup.find("meta", {"property": "product:retailer_item_id"})
    retailer_id = retailer_id_meta["content"] if retailer_id_meta and retailer_id_meta.has_attr("content") else ""

    return {
        "product_name": product_name,
        "product_id": product_id,
        "product_title": product_title,
        "current_price": current_price,
        "discount": discount_text,
        "retailer_id": retailer_id,
        "date": datetime.now().strftime("%Y-%m-%d")
    }

# --- 页面 UI ---
st.set_page_config(page_title="Kjell Product Info Scraper", layout="centered")
st.title("🔍 Kjell Product Info Scraper")

st.markdown("""
请上传包含产品ID和产品名称的CSV文件。  
CSV文件应包含列：**product id** 和（可选）**product name**。
""")

# --- 下载模板按钮 ---
sample_csv = pd.DataFrame({
    "product id": ["61632", "65412"],
    "product name": ["WD My Cloud Home 4TB", "TP-Link Tapo C520WS"]
})
csv_template = sample_csv.to_csv(index=False)
st.download_button(
    label="📥 下载CSV模板文件",
    data=csv_template,
    file_name="kjell_template.csv",
    mime="text/csv"
)

# --- 上传CSV文件 ---
uploaded_file = st.file_uploader("上传CSV文件", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if "product id" not in df.columns:
        st.error("CSV 文件必须包含名为 'product id' 的列。")
    else:
        st.success(f"✅ 成功加载 {len(df)} 条产品数据")
        st.dataframe(df.head())

        if st.button("🚀 开始抓取"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, row in df.iterrows():
                product_id = str(row["product id"]).strip()
                product_name = str(row["product name"]).strip() if "product name" in row else ""
                status_text.text(f"正在抓取产品ID: {product_id} ({idx+1}/{len(df)})")
                info = extract_product_info(product_id, product_name)
                results.append(info)
                progress_bar.progress((idx + 1) / len(df))

            status_text.text("✅ 抓取完成！")
            results_df = pd.DataFrame(results)[[
                "product_name", "product_id", "product_title", "current_price", "discount", "retailer_id", "date"
            ]]

            csv_buffer = io.StringIO()
            results_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 下载抓取结果 (CSV格式)",
                data=csv_buffer.getvalue(),
                file_name=f"kjell_scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

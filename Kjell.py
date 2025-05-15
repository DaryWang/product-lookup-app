import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
from datetime import datetime
import time

# 三个 Google Sheet 数据源（请替换成您的链接）
GOOGLE_SHEET_URL_CN = "https://docs.google.com/spreadsheets/d/1k5GJEo0IVzxOHc-NhccbyWBD4fDsXluLoSA9_7v1fLY/export?format=csv"
GOOGLE_SHEET_URL_CE = "https://docs.google.com/spreadsheets/d/1k5GJEo0IVzxOHc-NhccbyWBD4fDsXluLoSA9_7v1fLY/export?format=csv"
GOOGLE_SHEET_URL_TP = "https://docs.google.com/spreadsheets/d/1DBUtjPe7YIgE_hNL5Dh6rc83EJ43tlHumyik_IVmejA/export?format=csv"

# 页面设置
st.set_page_config(page_title="Kjell Price Scraper", layout="centered")
st.title("📦 Kjell Price Scraper")

# 下载模板
sample_df = pd.DataFrame({
    "Product ID": ["p61632"],
    "Product Name": ["WD My Cloud Home 4TB"]
})
csv_buffer = io.StringIO()
sample_df.to_csv(csv_buffer, index=False)
#st.download_button("📄 Download CSV Template", csv_buffer.getvalue(), "template.csv", "text/csv")

# 选择数据源
st.subheader("Choose Source Data")
source_option = st.radio("Select product source",
                         ["CN competitors", "CE competitors", "TP-Link+Mercusys", "Download template and Upload CSV"])

input_df = None
uploaded_file = None

if source_option == "Download template and Upload CSV":
    col1, col2 = st.columns([1, 5])
    with col1:
        st.download_button(
            label="📥",
            data=csv_buffer.getvalue(),
            file_name="template.csv",
            mime="text/csv",
            key="download_template"
        )
    with col2:
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="upload_csv")
    if uploaded_file is not None:
        input_df = pd.read_csv(uploaded_file)

elif source_option == "CN competitors":
    input_df = load_sheet(GOOGLE_SHEET_URL_CN)
elif source_option == "CE competitors":
    input_df = load_sheet(GOOGLE_SHEET_URL_CE)
elif source_option == "TP-Link+Mercusys":
    input_df = load_sheet(GOOGLE_SHEET_URL_TP)


# 抓取函数
def extract_kjell_info(product_id):
    try:
        url = f"https://www.kjell.com/se/{product_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        price = soup.find("meta", {"property": "product:price:amount"})
        if price and price.get("content"):
            try:
                 price = f"{float(price['content']):.2f}"
            except ValueError:
                 price = "N/A"
        else:
            price = "N/A"

        discount_tag = soup.find("div", {"data-test-id": "campaign-product-sticker"})
        discount_text = discount_tag.get_text(strip=True) if discount_tag else "N/A"

        title_tag = soup.find("meta", {"property": "og:title"})
        title = title_tag["content"] if title_tag else "N/A"

        retailer_id_tag = soup.find("meta", {"property": "product:retailer_item_id"})
        retailer_id = retailer_id_tag["content"] if retailer_id_tag else "N/A"

        return price, discount_text, title, retailer_id
    except Exception as e:
        return "ERROR", "ERROR", "ERROR", "ERROR"

# 执行抓取
if input_df is not None and st.button("🚀 Start Scraping"):
    st.write("Scraping started. Please wait...")
    progress_bar = st.progress(0)
    results = []
    total = len(input_df)
    for idx, row in input_df.iterrows():
        product_id = str(row["Product ID"])
        product_name = row["Product Name"]
        price, discount, title, retailer_id = extract_kjell_info(product_id)
        date_str = datetime.now().strftime("%Y-%m-%d")
        results.append([product_name, product_id, price, discount, title, retailer_id, date_str])
        progress_bar.progress((idx + 1) / total)
        time.sleep(1.5)  # 节流防止封锁

    output = io.StringIO()
    writer = pd.DataFrame(results, columns=[
        "Product Name", "Product ID", "Current Price", "Discount Info", "Title", "Retailer Item ID", "Date"
    ])
    writer.to_csv(output, index=False, sep="\t")

    st.success("Scraping complete!")
    today_str = datetime.today().strftime("%Y%m%d")
    filename = f"kjell_results_{today_str}.txt"
    st.download_button("📥 Download Results", output.getvalue(), file_name=filename, mime="text/plain")

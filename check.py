# GITHUB_CSV_URL = "https://raw.githubusercontent.com/DaryWang/product-lookup-app/refs/heads/main/product_mapping%201.csv"

import requests
import re
import csv
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import io
import time

# GitHub 上存储产品编号和名称对照表的原始 URL
GITHUB_CSV_URL = "https://raw.githubusercontent.com/DaryWang/product-lookup-app/refs/heads/main/product_mapping%201.csv"

# 国家网站模板
URL_TEMPLATES = {
    "Sweden": "https://www.elgiganten.se/product/{}",
    "Norway": "https://www.elkjop.no/product/{}",
    "Finland": "https://www.gigantti.fi/product/{}",
    "Denmark": "https://www.elgiganten.dk/product/{}",
}

# 清洗价格文本
def clean_price(price_text):
    cleaned_price = re.sub(r'[^\d,.-]', '', price_text).strip()
    return cleaned_price

# 从商品页面提取价格
def extract_prices(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, allow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 常规价格
    price_element = soup.find('div', {'class': 'grid grid-cols-subgrid grid-rows-subgrid row-span-2 gap-1 items-end'})
    if price_element:
        inc_vat_price = price_element.find('span', {'class': 'inc-vat'})
        regular_price = inc_vat_price.get_text(strip=True) if inc_vat_price else 'N/A'
    else:
        regular_price = 'N/A'
    regular_price = clean_price(regular_price)

    # 促销价格
    promo_price_element = soup.find('span', {'class': 'font-regular flex flex-shrink px-1 items-center text-base'})
    if promo_price_element:
        promo_price = promo_price_element.find('span', {'class': 'inc-vat'})
        if promo_price:
            promo_price_text = promo_price.get_text(strip=True)
            promo_price_value = promo_price_text.replace('Førpris: ', '').replace('Tidigare pris', '').strip()
            promo_price = clean_price(promo_price_value)
        else:
            promo_price = 'N/A'
    else:
        promo_price = 'N/A'

    if promo_price != 'N/A':
        regular_price, promo_price = promo_price, regular_price

    return regular_price, promo_price

# 从 GitHub 加载产品映射表
def load_product_mapping_from_github():
    response = requests.get(GITHUB_CSV_URL)
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text))
        if 'Product ID' in df.columns and 'Product Name' in df.columns:
            return df
        else:
            st.error("CSV 必须包含 'Product ID' 和 'Product Name' 两列。")
            return None
    else:
        st.error("无法从 GitHub 加载产品数据。")
        return None

# 保存查询结果为 CSV 格式的 TXT 文件
def save_results_to_txt(results):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product ID", "Product Name", "Country", "Product URL", "Regular Price", "Promo Price"])
    for result in results:
        writer.writerow(result)
    return output.getvalue()

# Streamlit 页面设置
st.set_page_config(page_title="Elkjop Price Check", layout="centered")

st.title("🌍 Elkjop Price Check")
st.write("Click the button below to start fetching TP-Link product prices.")

# 加载产品对照表
product_mapping_df = load_product_mapping_from_github()

# 显示“开始”按钮
if product_mapping_df is not None:
    if st.button("🚀 Start Fetching Prices"):
        all_results = []
        total_tasks = len(product_mapping_df) * len(URL_TEMPLATES)
        progress_bar = st.progress(0)
        task_counter = 0

        for _, row in product_mapping_df.iterrows():
            product_id = str(row['Product ID'])
            product_name = row['Product Name']

            for country, url_template in URL_TEMPLATES.items():
                product_url = url_template.format(product_id)
                regular_price, promo_price = extract_prices(product_url)

                all_results.append([
                    product_id,
                    product_name,
                    country,
                    product_url,
                    regular_price,
                    promo_price
                ])

                # 更新进度条
                task_counter += 1
                progress = task_counter / total_tasks
                progress_bar.progress(progress)

        # 保存并提供下载
        txt_data = save_results_to_txt(all_results)
        st.success("✅ Fetching complete!")
       from datetime import datetime

# 获取当前时间并格式化为文件名
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_name = f"product_prices_{timestamp}.txt"

st.download_button(
    label="⬇️ Download Results as TXT",
    data=txt_data,
    file_name=file_name,
    mime="text/csv"
)

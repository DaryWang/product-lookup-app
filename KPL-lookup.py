import requests
import re
import csv
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import io
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager



# GitHub 上存储产品编号和名称对照表的原始 URL
GITHUB_CSV_URL = "https://raw.githubusercontent.com/DaryWang/product-lookup-app/refs/heads/main/KPL.csv"

# 国家网站模板，按要求顺序排列
URL_TEMPLATES = {
    "Sweden": "https://www.komplett.se/product/{}",
    "Norway": "https://www.komplett.no/product/{}",
    "Denmark": "https://www.komplett.dk/product/{}",
}


def get_headless_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def extract_prices(url):
    driver = get_headless_driver()

    try:
        driver.get(url)
        time.sleep(3)  # 等待页面加载

        # 提取当前价格
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, "span.product-price-now")
            regular_price = price_element.text.strip()
        except:
            regular_price = 'N/A'

        # 提取促销价格（原价）
        try:
            promo_element = driver.find_element(By.CSS_SELECTOR, "span.product-price-before")
            promo_price_text = promo_element.text.strip()
            promo_price = promo_price_text.replace('Førpris: ', '').replace('Tidigare pris', '').strip()
        except:
            promo_price = 'N/A'

        # 如果存在促销价格，交换
        if promo_price != 'N/A':
            regular_price, promo_price = promo_price, regular_price

        return regular_price, promo_price

    except Exception as e:
        return 'ERROR', f'抓取失败: {str(e)}'

    finally:
        driver.quit()


# 从 GitHub 读取产品编号和名称对照表
def load_product_mapping_from_github():
    response = requests.get(GITHUB_CSV_URL)
    if response.status_code == 200:
        # 使用 pandas 读取 CSV 内容
        df = pd.read_csv(io.StringIO(response.text))
        if 'Product ID' in df.columns and 'Product Name' in df.columns:
            return df
        else:
            st.error("GitHub CSV file must contain 'Product ID' and 'Product Name' columns.")
            return None
    else:
        st.error("Failed to load the CSV file from GitHub.")
        return None

# 将查询结果保存为 TXT 文件（CSV 格式）
def save_results_to_txt(product_id, results):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product ID", "Country", "Product URL", "Regular Price", "Promo Price"])
    for result in results:
        writer.writerow(result)
    return output.getvalue()

# 页面设置
st.set_page_config(page_title="Elkjop Price Lookup", layout="centered")

st.title("💻 Komplett Price Lookup")
st.write("You can either input any Product ID or choose from the dropdown list of TP-Link Models.")

# 从 GitHub 加载对照表
product_mapping_df = load_product_mapping_from_github()

# 用户输入产品编号
product_id_input = st.text_input("Enter the product ID (e.g., 1319905)", "")

# 用户选择产品名称（如果对照表已加载）
product_name_input = None
if product_mapping_df is not None:
    product_name_input = st.selectbox(
        "Or select a product name from the list:",
        product_mapping_df['Product Name'].dropna().unique()  # 去除空值
    )

# 根据选择的产品名称或产品编号查询价格
if st.button("Get Prices"):
    if product_id_input.strip():
        selected_product_id = product_id_input.strip()
    elif product_name_input:
        selected_product_id = product_mapping_df.loc[
            product_mapping_df['Product Name'] == product_name_input, 'Product ID'
        ].values
        selected_product_id = selected_product_id[0] if selected_product_id else None
    else:
        st.error("Please enter a product ID or select a product name.")
        selected_product_id = None

    if selected_product_id:
        results = []
        for country, url_template in URL_TEMPLATES.items():
            product_url = url_template.format(selected_product_id)
            regular_price, promo_price = extract_prices(product_url)
            results.append([selected_product_id, country, product_url, regular_price, promo_price])
        
        # 显示查询结果
        for result in results:
            st.write(f"**{result[1]}** | **Regular Price**: {result[3]} | **Promo Price**: {result[4]}")  # 显示国家
            st.write(f"URL: {result[2]}")
        
        # 下载查询结果
        txt_data = save_results_to_txt(selected_product_id, results)
        st.download_button("Download Results", txt_data, file_name="KPL_prices.txt")

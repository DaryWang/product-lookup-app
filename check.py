import requests
import re
import csv
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import io

# GitHub 上存储产品编号和名称对照表的原始 URL
GITHUB_CSV_URL = "https://raw.githubusercontent.com/DaryWang/product-lookup-app/refs/heads/main/product_mapping.csv"

# 国家网站模板，按要求顺序排列
URL_TEMPLATES = {
    "Sweden": "https://www.elgiganten.se/product/{}",
    "Norway": "https://www.elkjop.no/product/{}",
    "Finland": "https://www.gigantti.fi/product/{}",
    "Denmark": "https://www.elgiganten.dk/product/{}",
}

# 正则表达式：只提取数字和符号（例如，`,`和`.-`）
def clean_price(price_text):
    cleaned_price = re.sub(r'[^\d,.-]', '', price_text).strip()
    return cleaned_price

# 提取价格的函数（处理重定向）
def extract_prices(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, allow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取常规价格
    price_element = soup.find('div', {'class': 'grid grid-cols-subgrid grid-rows-subgrid row-span-2 gap-1 items-end'})
    if price_element:
        inc_vat_price = price_element.find('span', {'class': 'inc-vat'})
        regular_price = inc_vat_price.get_text(strip=True) if inc_vat_price else 'N/A'
    else:
        regular_price = 'N/A'
    regular_price = clean_price(regular_price)

    # 提取促销价格
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
def save_results_to_txt(results):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product ID", "Country", "Product URL", "Regular Price", "Promo Price"])
    for result in results:
        writer.writerow(result)
    return output.getvalue()

# 页面设置
st.set_page_config(page_title="Nordic Customer Product Lookup", layout="centered")

st.title("🌍 Nordic Customer Product Lookup")
st.write("This tool fetches product information for all products listed in the CSV file.")

# 从 GitHub 加载对照表
product_mapping_df = load_product_mapping_from_github()

# 提取所有产品ID并遍历
if product_mapping_df is not None:
    all_results = []
    for _, row in product_mapping_df.iterrows():
        product_id = str(row['Product ID'])
        product_name = row['Product Name']

        # 获取每个产品的价格
        results = []
        for country, url_template in URL_TEMPLATES.items():
            product_url = url_template.format(product_id)
            regular_price, promo_price = extract_prices(product_url)
            results.append([product_id, country, product_url, regular_price, promo_price])

        all_results.extend(results)
    
    # 显示结果
    st.write("### Product Price Information:")
    for result in all_results:
        st.write(f"**Product ID**: {result[0]}, **Country**: {result[1]}")
        st.write(f"Product URL: {result[2]}")
        st.write(f"Regular Price: {result[3]}, Promo Price: {result[4]}")
    
    # 下载查询结果
    st.download_button(
        label="Download Results as TXT",
        data=save_results_to_txt(all_results),
        file_name="product_prices.txt",
        mime="text/csv"
    )

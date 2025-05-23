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
def save_results_to_txt(product_id, results):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product ID", "Country", "Product URL", "Regular Price", "Promo Price"])
    for result in results:
        writer.writerow(result)
    return output.getvalue()

# 页面设置
st.set_page_config(page_title="Elkjop Price Lookup", layout="centered")

st.title("💻 Elkjop Price Lookup")
st.write("You can either input any Product ID or choose a tp-link model from the dropdown list.")

# 从 GitHub 加载对照表
product_mapping_df = load_product_mapping_from_github()

# 用户输入产品编号
product_id_input = st.text_input("Enter the product ID (e.g., 897511)", "")

# 用户选择产品名称（如果对照表已加载）
product_name_input = None
if product_mapping_df is not None:
    product_names = [""] + list(product_mapping_df['Product Name'].dropna().unique())
product_name_input = st.selectbox(
    "Or select a product name from the list:",
    product_names,
    index=0  # 默认选中空白项
)


# 根据选择的产品名称或产品编号查询价格
if st.button("Get Prices"):
    selected_product_id = None

    if product_id_input.strip():
        selected_product_id = product_id_input.strip()
        product_name_input = ""  # 清空产品名（符合你要求）
    elif product_name_input and product_name_input != "":
        selected_product_id = product_mapping_df.loc[
            product_mapping_df['Product Name'] == product_name_input, 'Product ID'
        ].values
        selected_product_id = selected_product_id[0] if len(selected_product_id) > 0 else None
    else:
        st.error("Please enter a product ID or select a product name.")

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
        st.download_button("Download Results", txt_data, file_name="product_prices.txt")

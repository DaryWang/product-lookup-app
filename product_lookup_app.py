import requests
import re
import csv
from bs4 import BeautifulSoup
import streamlit as st
import io

# 国家网站模板，按要求顺序排列
URL_TEMPLATES = {
    "Sweden 🇸🇪": "https://www.elgiganten.se/product/{}",
    "Norway 🇳🇴": "https://www.elkjop.no/product/{}",
    "Finland 🇫🇮": "https://www.gigantti.fi/product/{}",
    "Denmark 🇩🇰": "https://www.elgiganten.dk/product/{}",
}

# 正则表达式：只提取数字和符号（例如，`,`和`.-`）
def clean_price(price_text):
    # 使用正则表达式清除价格文本中的字母和非数字符号
    cleaned_price = re.sub(r'[^\d,.-]', '', price_text).strip()
    return cleaned_price

# 提取价格的函数（处理重定向）
def extract_prices(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    # 发送请求，获取最终重定向后的页面
    response = requests.get(url, headers=headers, allow_redirects=True)
    
    # 解析重定向后的页面内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取常规价格
    price_element = soup.find('div', {'class': 'grid grid-cols-subgrid grid-rows-subgrid row-span-2 gap-1 items-end'})
    if price_element:
        inc_vat_price = price_element.find('span', {'class': 'inc-vat'})
        regular_price = inc_vat_price.get_text(strip=True) if inc_vat_price else 'N/A'
    else:
        regular_price = 'N/A'

    # 清理常规价格
    regular_price = clean_price(regular_price)

    # 提取促销价格
    promo_price_element = soup.find('span', {'class': 'font-regular flex flex-shrink px-1 items-center text-base'})
    if promo_price_element:
        promo_price = promo_price_element.find('span', {'class': 'inc-vat'})
        if promo_price:
            # 获取促销价格并清除 "Førpris: " 部分
            promo_price_text = promo_price.get_text(strip=True)
            promo_price_value = promo_price_text.replace('Førpris: ', '').replace('Tidigare pris', '').strip()
            promo_price = clean_price(promo_price_value)
        else:
            promo_price = 'N/A'
    else:
        promo_price = 'N/A'

    # 如果促销价格存在，将其视为常规价格，原常规价格作为促销价格
    if promo_price != 'N/A' and promo_price != 'N/A':
        regular_price, promo_price = promo_price, regular_price

    return regular_price, promo_price

# 将查询结果保存为 TXT 文件（CSV 格式）
def save_results_to_txt(product_id, results):
    # 使用 io.StringIO 以字符串形式生成文件
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入标题行
    writer.writerow(["Product ID", "Country", "Product URL", "Regular Price", "Promo Price"])
    
    # 写入数据
    for result in results:
        writer.writerow(result)
    
    # 获取结果字符串内容并返回
    return output.getvalue()

# 页面设置
st.set_page_config(page_title="Nordic Customer Product Lookup", layout="centered")

st.title("🌍 Nordic Customer Product Lookup")
product_id = st.text_input("Enter the product ID (e.g., 897511)", "")

if st.button("Get Prices"):
    if not product_id.strip():
        st.warning("Please enter a product ID.")
    else:
        st.success("Here are the product prices across the Nordic countries:")

        results = []
        
        # 按照瑞典、挪威、芬兰、丹麦的顺序显示
        for country, url_template in URL_TEMPLATES.items():
            url = url_template.format(product_id.strip())
            st.write(f"🔗 [{country} Product Page]({url})")
            
            # 提取常规价格和促销价格
            regular_price, promo_price = extract_prices(url)
            st.write(f"Regular Price: {regular_price} | Promo Price: {promo_price}")
            
            # 将结果保存到列表中
            results.append([product_id.strip(), country, url, regular_price, promo_price])

        # 将查询结果保存为 TXT 文件（CSV 格式）
        txt_file = save_results_to_txt(product_id.strip(), results)

        # 提供下载按钮
        st.download_button(
            label="Download Results as TXT",
            data=txt_file,
            file_name=f"product_{product_id.strip()}_prices.txt",
            mime="text/plain"
        )

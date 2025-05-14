import requests
from bs4 import BeautifulSoup
import streamlit as st

# 国家网站模板
URL_TEMPLATES = {
    "芬兰 🇫🇮": "https://www.gigantti.fi/product/{}",
    "挪威 🇳🇴": "https://www.elkjop.no/product/{}",
    "瑞典 🇸🇪": "https://www.elgiganten.se/product/{}",
    "丹麦 🇩🇰": "https://www.elgiganten.dk/product/{}",
}

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
        regular_price = inc_vat_price.get_text(strip=True) if inc_vat_price else '未找到常规价格'
    else:
        regular_price = '未找到常规价格'

    # 提取促销价格
    promo_price_element = soup.find('span', {'class': 'font-regular flex flex-shrink px-1 items-center text-base'})
    if promo_price_element:
        promo_price = promo_price_element.find('span', {'class': 'inc-vat'})
        if promo_price:
            # 获取促销价格并清除 "Førpris: " 部分
            promo_price_text = promo_price.get_text(strip=True)
            promo_price_value = promo_price_text.replace('Førpris: ', '').strip()
            promo_price = promo_price_value if promo_price_value else '未找到促销价格'
        else:
            promo_price = '未找到促销价格'
    else:
        promo_price = '未找到促销价格'

    # 如果促销价格存在，将其视为常规价格，原常规价格作为促销价格
    if promo_price != '未找到促销价格' and promo_price != '未找到常规价格':
        regular_price, promo_price = promo_price, regular_price

    return regular_price, promo_price

# 页面设置
st.set_page_config(page_title="北欧客户产品查询", layout="centered")

st.title("🌍 北欧客户产品页面查询")
product_id = st.text_input("请输入产品编号（如 897511）", "")

if st.button("查询价格"):
    if not product_id.strip():
        st.warning("请输入产品编号")
    else:
        st.success("以下是该产品在各国网站的价格信息：")
        
        for country, url_template in URL_TEMPLATES.items():
            url = url_template.format(product_id.strip())
            st.write(f"🔗 [{country} 产品页面]({url})")
            
            # 提取常规价格和促销价格
            regular_price, promo_price = extract_prices(url)
            st.write(f"常规价格: {regular_price} | 促销价格: {promo_price}")

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

# 提取价格和库存的函数
def extract_price_stock(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 提取价格
    price_element = soup.find('span', {'class': 'product-price__price'})
    price = price_element.get_text(strip=True) if price_element else '未找到价格'

    # 提取库存信息
    stock_element = soup.find('div', {'class': 'availability-msg'})
    stock = stock_element.get_text(strip=True) if stock_element else '未找到库存信息'

    return price, stock

# 页面设置
st.set_page_config(page_title="北欧客户产品查询", layout="centered")

st.title("🌍 北欧客户产品页面查询")
product_id = st.text_input("请输入产品编号（如 897511）", "")

if st.button("查询价格和库存"):
    if not product_id.strip():
        st.warning("请输入产品编号")
    else:
        st.success("以下是该产品在各国网站的链接和相关信息：")
        
        for country, url_template in URL_TEMPLATES.items():
            url = url_template.format(product_id.strip())
            st.write(f"🔗 [{country} 产品页面]({url})")
            
            # 提取价格和库存
            price, stock = extract_price_stock(url)
            st.write(f"价格: {price} | 库存: {stock}")

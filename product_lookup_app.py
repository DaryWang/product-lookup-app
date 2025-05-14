import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import io

# GitHub原始CSV文件的链接
GITHUB_CSV_URL = "https://raw.githubusercontent.com/DaryWang/product-lookup-app/main/product-lookup-app/product_mapping.csv"

# 从GitHub加载CSV文件
def load_product_mapping_from_github():
    response = requests.get(GITHUB_CSV_URL)
    if response.status_code == 200:
        # 使用pandas读取CSV内容
        df = pd.read_csv(io.StringIO(response.text))
        if 'Product ID' in df.columns and 'Product Name' in df.columns:
            return df
        else:
            st.error("GitHub CSV file must contain 'Product ID' and 'Product Name' columns.")
            return None
    else:
        st.error(f"Failed to load the CSV file from GitHub. Status code: {response.status_code}")
        return None

# 处理产品编号和名称的映射
def get_product_info(product_mapping_df, product_id_input, product_name_input):
    if product_id_input:
        selected_product_name = product_mapping_df.loc[
            product_mapping_df['Product ID'] == product_id_input, 'Product Name'
        ].values
        if selected_product_name:
            return selected_product_name[0]
        else:
            st.error(f"Product ID {product_id_input} not found.")
            return None
    elif product_name_input:
        selected_product_id = product_mapping_df.loc[
            product_mapping_df['Product Name'] == product_name_input, 'Product ID'
        ].values
        if selected_product_id:
            return selected_product_id[0]
        else:
            st.error(f"Product name {product_name_input} not found.")
            return None
    else:
        st.error("Please enter either Product ID or Product Name.")
        return None

# 获取价格和库存
def get_product_details(product_id):
    url = f"https://www.elgiganten.dk/product/{product_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 获取价格
    price = soup.find("div", {"data-primary-price": True})
    if price:
        regular_price = price.find("span", class_="inc-vat").text.strip().replace("€", "").replace(" ", "")
        return regular_price
    else:
        return None

# 主函数
def main():
    st.title("Product Lookup App")

    # 加载产品映射表
    product_mapping_df = load_product_mapping_from_github()

    if product_mapping_df is not None:
        # 输入框：产品编号或名称
        product_id_input = st.text_input("Enter Product ID")
        product_name_input = st.selectbox("Select Product Name", options=product_mapping_df['Product Name'].tolist())

        # 获取产品信息
        product_info = get_product_info(product_mapping_df, product_id_input, product_name_input)
        
        if product_info:
            st.write(f"Product Information: {product_info}")

            # 获取产品详情
            product_details = get_product_details(product_info)
            
            if product_details:
                st.write(f"Regular Price: {product_details}")
            else:
                st.error("Unable to retrieve product details.")
        
if __name__ == "__main__":
    main()

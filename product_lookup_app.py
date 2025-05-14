import streamlit as st

# 国家网站模板
URL_TEMPLATES = {
    "芬兰 🇫🇮": "https://www.gigantti.fi/product/{}",
    "挪威 🇳🇴": "https://www.elkjop.no/product/{}",
    "瑞典 🇸🇪": "https://www.elgiganten.se/product/{}",
    "丹麦 🇩🇰": "https://www.elgiganten.dk/product/{}",
}

# 页面设置
st.set_page_config(page_title="北欧客户产品查询", layout="centered")

st.title("🌍 北欧客户产品页面查询")
product_id = st.text_input("请输入产品编号（如 897511）", "")

if st.button("🔍 查看产品链接"):
    if not product_id.strip():
        st.warning("请输入产品编号")
    else:
        st.success("以下是该产品在各国网站的链接：")
        for country, url_template in URL_TEMPLATES.items():
            full_url = url_template.format(product_id.strip())
            st.markdown(f"[{country}]({full_url}) 🔗", unsafe_allow_html=True)

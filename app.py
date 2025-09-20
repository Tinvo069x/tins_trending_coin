import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Crypto Heatmap", layout="wide")

st.title("📊 Crypto Heatmap (CoinGecko API)")

# --- Sidebar config ---
top_n = st.sidebar.slider("Chọn số coin (Top N)", 10, 100, 30, 10)
currency = st.sidebar.selectbox("Chọn đơn vị tiền", ["usd", "eur", "vnd"])
refresh = st.sidebar.number_input("Tự động refresh (giây)", 0, 600, 0)

# --- Fetch data ---
@st.cache_data(ttl=60)
def fetch_data(top_n, currency):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": top_n,
        "page": 1,
        "price_change_percentage": "1h,24h,7d"
    }
    data = requests.get(url, params=params, timeout=20).json()
    return pd.DataFrame(data)

df = fetch_data(top_n, currency)

# --- Clean data ---
df.rename(columns={
    'price_change_percentage_1h_in_currency': '%1h',
    'price_change_percentage_24h_in_currency': '%24h',
    'price_change_percentage_7d_in_currency': '%7d'
}, inplace=True)

df['market_cap'] = pd.to_numeric(df['market_cap'], errors='coerce').fillna(0)
df['%24h'] = pd.to_numeric(df['%24h'], errors='coerce').fillna(0)
df = df[df['market_cap'] > 0]

# --- Save snapshot ---
df["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
df.to_csv("crypto_snapshot.csv", mode="a", index=False, header=False)

# --- Heatmap ---
fig = px.treemap(
    df,
    path=['symbol'],
    values='market_cap',
    color='%24h',
    hover_data={
        'current_price': True,
        'market_cap': True,
        'total_volume': True,
        '%1h': True,
        '%24h': True,
        '%7d': True
    },
    color_continuous_scale=['red','white','green'],
    title=f"Tins_Heatmap (Top {top_n}) - MarketCap vs %Change 24h"
)
st.plotly_chart(fig, use_container_width=True)

# --- Legend / Giải thích màu ---
st.markdown("""
### 🟢🔴 Ý nghĩa màu sắc trên biểu đồ
- 🟢 **Xanh lá**: Coin **tăng giá** trong 24h (%24h dương).  
- ⚪ **Trắng**: Coin **ổn định**, gần như không thay đổi.  
- 🔴 **Đỏ**: Coin **giảm giá** trong 24h (%24h âm).  

👉 Di chuột vào từng ô để xem chi tiết **%1h, %24h, %7d, MarketCap, Volume**.
""")

# --- Show raw data ---
with st.expander("📋 Xem dữ liệu chi tiết"):
    st.dataframe(df[[
        "symbol","name","current_price","market_cap","total_volume",
        "%1h","%24h","%7d"
    ]])

# --- Auto refresh ---
if refresh > 0:
    st.toast(f"⏳ Trang sẽ tự refresh mỗi {refresh} giây", icon="🔄")
    st.experimental_set_query_params(ts=datetime.utcnow().timestamp())
    st.experimental_rerun()

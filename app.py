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
@st.cache_data(ttl=60)  # cache 60s
def fetch_data(top_n, currency):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": top_n,
        "page": 1,
        "price_change_percentage": "1h,24h,7d"
    }
    data = requests.get(url, params=params).json()
    return pd.DataFrame(data)

df = fetch_data(top_n, currency)

# --- Save snapshot ---
df["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
df.to_csv("crypto_snapshot.csv", mode="a", index=False, header=False)

# --- Treemap heatmap ---
fig = px.treemap(
    df,
    path=['symbol'],
    values='market_cap',
    color='price_change_percentage_24h_in_currency',
    hover_data={
        'current_price': True,
        'market_cap': True,
        'total_volume': True,
        'price_change_percentage_1h_in_currency': True,
        'price_change_percentage_24h_in_currency': True,
        'price_change_percentage_7d_in_currency': True
    },
    color_continuous_scale=['red','white','green'],
    title=f"Crypto Heatmap (Top {top_n}) - MarketCap vs %Change 24h"
)

st.plotly_chart(fig, use_container_width=True)

# --- Show raw data ---
with st.expander("📋 Xem dữ liệu chi tiết"):
    st.dataframe(df[[
        "symbol","name","current_price","market_cap","total_volume",
        "price_change_percentage_1h_in_currency",
        "price_change_percentage_24h_in_currency",
        "price_change_percentage_7d_in_currency"
    ]])

# --- Auto refresh ---
if refresh > 0:
    st.experimental_set_query_params(refresh="true")
    st.experimental_rerun()

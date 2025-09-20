import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Crypto Market Dashboard", layout="wide")

st.title("📊 Crypto Market Dashboard (CoinGecko API)")

# --- Sidebar chọn chế độ ---
tab = st.sidebar.radio("Chọn chế độ hiển thị", ["Heatmap hiện tại", "Lịch sử 3 năm"])

# ========================= HEATMAP HIỆN TẠI =========================
if tab == "Heatmap hiện tại":
    top_n = st.sidebar.slider("Chọn số coin (Top N)", 10, 100, 30, 10)
    currency = st.sidebar.selectbox("Chọn đơn vị tiền", ["usd", "eur", "vnd"])
    sort_option = st.sidebar.radio("Sắp xếp coin theo:", ["MarketCap", "%Change 1h", "%Change 24h", "%Change 7d"])
    rank_period = st.sidebar.radio("Xem Top Gainers/Losers theo:", ["%1h","%24h","%7d"])
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

    for col in ['market_cap', '%1h', '%24h', '%7d']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df = df[df['market_cap'] > 0]

    # --- Sorting logic ---
    if sort_option == "%Change 1h":
        df = df.sort_values(by='%1h', ascending=False).reset_index(drop=True)
    elif sort_option == "%Change 24h":
        df = df.sort_values(by='%24h', ascending=False).reset_index(drop=True)
    elif sort_option == "%Change 7d":
        df = df.sort_values(by='%7d', ascending=False).reset_index(drop=True)
    else:
        df = df.sort_values(by='market_cap', ascending=False).reset_index(drop=True)

    # --- Heatmap ---
    fig = px.treemap(
        df,
        path=['symbol'],
        values='market_cap',
        color='%24h',  # tô màu theo %24h
        hover_data={
            'current_price': True,
            'market_cap': True,
            'total_volume': True,
            '%1h': True,
            '%24h': True,
            '%7d': True
        },
        color_continuous_scale=['red','white','green'],
        title=f"Crypto Heatmap (Top {top_n}) - Sắp xếp theo {sort_option}"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Legend ---
    st.markdown("""
    ### 🟢🔴 Ý nghĩa màu sắc trên biểu đồ
    - 🟢 **Xanh lá**: Coin **tăng giá** trong 24h (%24h dương).  
    - ⚪ **Trắng**: Coin **ổn định**, gần như không thay đổi.  
    - 🔴 **Đỏ**: Coin **giảm giá** trong 24h (%24h âm).  

    👉 Di chuột vào từng ô để xem chi tiết **%1h, %24h, %7d, MarketCap, Volume**.
    """)

    # --- Bảng toàn bộ dữ liệu ---
    with st.expander("📋 Xem toàn bộ dữ liệu chi tiết"):
        st.dataframe(df[[
            "symbol","name","current_price","market_cap","total_volume",
            "%1h","%24h","%7d"
        ]])

    # --- Top Gainers ---
    st.subheader(f"🚀 Top coin TĂNG mạnh nhất ({rank_period})")
    top_gainers = df.sort_values(by=rank_period, ascending=False).head(10)
    st.dataframe(top_gainers[[
        "symbol","name","current_price","%1h","%24h","%7d","market_cap","total_volume"
    ]])

    # --- Top Losers ---
    st.subheader(f"📉 Top coin GIẢM mạnh nhất ({rank_period})")
    top_losers = df.sort_values(by=rank_period, ascending=True).head(10)
    st.dataframe(top_losers[[
        "symbol","name","current_price","%1h","%24h","%7d","market_cap","total_volume"
    ]])

    # --- Auto refresh ---
    if refresh > 0:
        st.toast(f"⏳ Trang sẽ tự refresh mỗi {refresh} giây", icon="🔄")
        st.experimental_set_query_params(ts=datetime.utcnow().timestamp())
        st.experimental_rerun()

# ========================= LỊCH SỬ 3 NĂM =========================
else:
    st.sidebar.write("Chọn coin và xem lịch sử giá 3 năm gần nhất")

    # --- Fetch coin list ---
    @st.cache_data(ttl=3600)
    def fetch_coin_list():
        url = "https://api.coingecko.com/api/v3/coins/list"
        data = requests.get(url, timeout=20).json()
        return pd.DataFrame(data)

    coin_list = fetch_coin_list()

    coin_name = st.sidebar.selectbox("Chọn coin", sorted(coin_list['name'].tolist()))
    coin_id = coin_list.loc[coin_list['name'] == coin_name, 'id'].values[0]
    currency = st.sidebar.selectbox("Chọn đơn vị tiền", ["usd", "eur", "vnd"], key="hist")

    # --- Fetch historical data ---
    @st.cache_data(ttl=3600)
    def fetch_history(coin_id, currency):
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": currency, "days": 1095}
        data = requests.get(url, params=params, timeout=20).json()
        if not data or "prices" not in data:
            return pd.DataFrame(columns=["timestamp","price","date"])
        prices = data["prices"]
        df = pd.DataFrame(prices, columns=["timestamp","price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    hist_df = fetch_history(coin_id, currency)

    if hist_df.empty:
        st.error(f"⛔ Không có dữ liệu lịch sử cho coin '{coin_name}' trong 3 năm qua.")
    else:
        fig = px.line(hist_df, x="date", y="price",
                      title=f"{coin_name} - Lịch sử giá 3 năm gần nhất ({currency.upper()})",
                      labels={"price": f"Giá ({currency.upper()})", "date": "Ngày"})
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Xem dữ liệu gốc"):
            st.dataframe(hist_df.tail(20))

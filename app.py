# app.py - Crypto Price Dashboard (Bitcoin & More)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -------------------------- Page Config --------------------------
st.set_page_config(
    page_title="Crypto Price Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Crypto Price Dashboard: Top 500 Cryptocurrencies by market capitalization 2024/25")
st.markdown("### Real-time OHLC Analysis • Trends • Volatility • Performance")

# -------------------------- Load Data --------------------------
@st.cache_data
def load_data():
    # Try to load from file first (for deployment)
    try:
        df = pd.read_csv("cryptodata.csv")
    except:
        # Fallback: let user upload
        uploaded = st.file_uploader(
            "Upload your crypto data (CSV)",
            type=["csv"],
            help="Columns: coin_id, symbol, timestamp, date, open, high, low, close"
        )
        if uploaded is None:
            st.info("Upload your crypto_data.csv to begin")
            st.stop()
        df = pd.read_csv(uploaded)
    return df

df = load_data()

# Clean & prepare data
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
df['change_pct'] = df['close'].pct_change() * 100
df['volatility_7d'] = df['close'].pct_change().rolling(7).std() * 100
df['high_low_range'] = df['high'] - df['low']
df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3

st.success(f"Loaded {len(df):,} price records • Latest: {df['date'].max().strftime('%Y-%m-%d')}")

# -------------------------- Sidebar Filters --------------------------
st.sidebar.header("Filters")

# Coin selector
coins = df['symbol'].str.upper().unique()
selected_coins = st.sidebar.multiselect("Select Cryptocurrencies", options=coins, default=coins[:1])

# Date range
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filter data
mask = (
    df['symbol'].str.upper().isin([c.upper() for c in selected_coins]) &
    (df['date'].dt.date >= date_range[0]) &
    (df['date'].dt.date <= date_range[1] if len(date_range) > 1 else True)
)
data = df[mask].copy()

if data.empty:
    st.warning("No data for selected filters.")
    st.stop()

# -------------------------- Key Metrics --------------------------
latest = data.groupby('symbol').apply(lambda x: x.iloc[-1])
col1, col2, col3, col4 = st.columns(4)
for i, (symbol, row) in enumerate(latest.iterrows()):
    if i >= 4: break
    change_color = "green" if row['change_pct'] >= 0 else "red"
    col = [col1, col2, col3, col4][i]
    with col:
        st.metric(
            label=f"{symbol.upper()}",
            value=f"${row['close']:,.0f}",
            delta=f"{row['change_pct']:+.2f}%"
        )

st.markdown("---")

# -------------------------- Chart 1: Candlestick Chart --------------------------
st.subheader("Candlestick Chart")
for coin in data['symbol'].str.upper().unique():
    coin_data = data[data['symbol'].str.upper() == coin]
    fig = go.Figure(data=[go.Candlestick(
        x=coin_data['date'],
        open=coin_data['open'],
        high=coin_data['high'],
        low=coin_data['low'],
        close=coin_data['close'],
        name=coin
    )])
    fig.update_layout(
        title=f"{coin.upper()} Price Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        height=600,
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------- Chart 2: Price Trend Comparison --------------------------
st.subheader("Price Trend Comparison")
fig2 = px.line(
    data, x='date', y='close', color='symbol',
    title="Closing Price Over Time",
    labels={'close': 'Price (USD)', 'date': 'Date', 'symbol': 'Cryptocurrency'}
)
fig2.update_layout(height=500, hovermode='x unified')
st.plotly_chart(fig2, use_container_width=True)

# -------------------------- Chart 3: Daily Volatility --------------------------
st.subheader("7-Day Rolling Volatility")
fig3 = px.line(
    data, x='date', y='volatility_7d', color='symbol',
    title="Volatility (7-day rolling std of returns)",
    labels={'volatility_7d': 'Volatility %', 'date': 'Date'}
)
fig3.update_layout(height=400)
st.plotly_chart(fig3, use_container_width=True)

# -------------------------- Chart 4: Daily Price Range --------------------------
st.subheader("Daily High-Low Range")
fig4 = px.bar(
    data, x='date', y='high_low_range', color='symbol',
    title="Daily Price Range (High - Low)",
    labels={'high_low_range': 'Price Range (USD)'}
)
st.plotly_chart(fig4, use_container_width=True)

# -------------------------- Summary Table --------------------------
st.markdown("---")
st.subheader("Detailed Price Data")
display_cols = ['date', 'symbol', 'open', 'high', 'low', 'close', 'change_pct', 'volatility_7d']
styled_data = data[display_cols].copy()
styled_data['date'] = styled_data['date'].dt.strftime('%Y-%m-%d')
styled_data['change_pct'] = styled_data['change_pct'].round(2)
styled_data['volatility_7d'] = styled_data['volatility_7d'].round(2)

st.dataframe(
    styled_data.sort_values('date', ascending=False),
    use_container_width=True,
    hide_index=True
)

# -------------------------- Download --------------------------
csv = data.to_csv(index=False)
st.download_button(
    "Download filtered data as CSV",
    csv,
    "crypto_price_data.csv",
    "text/csv"
)

st.caption("Built with Streamlit • Data updates daily")


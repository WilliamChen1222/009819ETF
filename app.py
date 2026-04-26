import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. 頁面基本設定
st.set_page_config(page_title="009819 深度觀測站", layout="wide")
st.title("⚡ 009819 中信美國數據中心及電力 ETF 觀測站")
st.markdown("專注追蹤 AI 基礎建設與底層能源板塊的核心動能")

# 2. 定義標的與近似權重 (擴充至 10 大成分股)
etf_ticker = "009819.TW"
components = {
    "AVGO": {"name": "Broadcom (網通/AI晶片)", "weight": 25.4},
    "ETN": {"name": "Eaton (電力管理)", "weight": 9.2},
    "ORCL": {"name": "Oracle (雲端基建)", "weight": 8.5},
    "NEE": {"name": "NextEra Energy (綠能發電)", "weight": 4.1},
    "NOW": {"name": "ServiceNow (IT自動化)", "weight": 3.8},
    "EQIX": {"name": "Equinix (數據中心REITs)", "weight": 3.5},
    "SO": {"name": "Southern Co. (電力供應)", "weight": 3.4},
    "DUK": {"name": "Duke Energy (電力供應)", "weight": 3.2},
    "DLR": {"name": "Digital Realty (數據中心)", "weight": 3.1},
    "VRT": {"name": "Vertiv (散熱/液冷)", "weight": 2.8}
}

# 3. 獲取市場數據 (快取 15 分鐘)
@st.cache_data(ttl=900)
def fetch_data(tickers, period="3mo"):
    # yfinance 下載多檔股票時，會返回 MultiIndex DataFrame
    df = yf.download(tickers, period=period, interval="1d")['Close']
    return df

# 組合所有代碼
all_tickers = [etf_ticker] + list(components.keys())

try:
    with st.spinner("正在抓取最新市場數據..."):
        df_prices = fetch_data(all_tickers)
        
        # 確保數據按時間排序並移除空值
        df_prices = df_prices.sort_index().ffill().dropna()
        latest_prices = df_prices.iloc[-1]
        prev_prices = df_prices.iloc[-2]

    # --- 區塊 A：009819 本體即時看板 ---
    st.header("1. 009819 ETF 概況")
    col1, col2, col3 = st.columns(3)
    
    etf_current = latest_prices[etf_ticker]
    etf_prev = prev_prices[etf_ticker]
    etf_change_pct = ((etf_current / etf_prev) - 1) * 100
    
    col1.metric("009819 最新收盤價", f"NT$ {etf_current:.2f}", f"{etf_change_pct:.2f}%")
    col2.info("💡 **觀察重點**：台股掛牌的 009819 會受到台美匯率以及散戶情緒（折溢價）影響，其漲跌幅可能不會與美股成分股完全同步。")
    
    st.divider()

    # --- 區塊 B：成分股權重與即時表現 ---
    st.header("2. 核心成分股解析")
    col_pie, col_metrics = st.columns([1.5, 2])
    
    with col_pie:
        # 繪製成分股權重圓餅圖
        df_weights = pd.DataFrame([{"代碼": k, "名稱": v["name"], "權重": v["weight"]} for k, v in components.items()])
        fig_pie = px.pie(df_weights, values='權重', names='名稱', 
                         title="主力成分股權重分佈 (前十大)", hole=0.4)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_metrics:
        # 正確的位置：在這裡顯示 10 大成分股報價
        st.write("**前十大成分股即時走勢 (美股)**")
        m_cols1 = st.columns(5)  # 第一排 5 個
        m_cols2 = st.columns(5)  # 第二排 5 個
        
        m_cols_list = m_cols1 + m_cols2
        for idx, ticker in enumerate(components.keys()):
            current_p = latest_prices[ticker]
            prev_p = prev_prices[ticker]
            change = ((current_p / prev_p) - 1) * 100
            m_cols_list[idx].metric(ticker, f"${current_p:.2f}", f"{change:.2f}%")

    st.divider()

    # --- 區塊 C：走勢聯動比較 (穿透分析) ---
    st.header("3. 走勢聯動比較 (近三個月)")
    st.markdown("觀察 009819 是否緊跟其最大權重股（如 AVGO）或特定板塊（如電力基建）的趨勢。")
    
    # 計算累積報酬率 (以第一天為基準 0%)
    df_returns = (df_prices / df_prices.iloc[0] - 1) * 100
    
    fig_line = go.Figure()
    
    # 加入 009819 (特別加粗標示)
    fig_line.add_trace(go.Scatter(x=df_returns.index, y=df_returns[etf_ticker], 
                                  name="009819.TW", line=dict(color='red', width=4)))
    
    # 加入其他成分股
    for ticker in components.keys():
        fig_line.add_trace(go.Scatter(x=df_returns.index, y=df_returns[ticker], 
                                      name=components[ticker]["name"], opacity=0.7))
        
    fig_line.update_layout(
        title="009819 與核心成分股累積報酬率 (%)",
        yaxis_title="累積報酬率 (%)",
        xaxis_title="日期",
        hovermode="x unified",
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error("獲取資料失敗，請確認網路連線或 Yahoo Finance 服務是否正常。")
    st.write(f"錯誤訊息：{e}")

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. 頁面基本設定
st.set_page_config(page_title="009819 深度觀測站", layout="wide")
st.title("⚡ 009819 中信美國數據中心及電力 ETF 觀測站")
st.markdown("專注追蹤 AI 基礎建設與底層能源板塊的核心動能")

# 2. 定義標的與近似權重 (全中文名稱更新版，前十大)
etf_ticker = "009819.TW"
components = {
    "AVGO": {"name": "博通", "weight": 25.4},
    "ETN": {"name": "伊頓", "weight": 9.2},
    "ORCL": {"name": "甲骨文", "weight": 8.5},
    "NEE": {"name": "新紀元能源", "weight": 4.1},
    "NOW": {"name": "塞維斯諾", "weight": 3.8},       
    "EQIX": {"name": "易昆尼克斯", "weight": 3.5},     
    "SO": {"name": "南方公司", "weight": 3.4},
    "DUK": {"name": "杜克能源", "weight": 3.2},
    "DLR": {"name": "數位地產", "weight": 3.1},
    "VRT": {"name": "維諦技術", "weight": 2.8}
}

# 技術指標計算函數 (RSI)
def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

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
        # 繪製成分股權重圓餅圖 (名稱會直接顯示中文)
        df_weights = pd.DataFrame([{"代碼": k, "名稱": v["name"], "權重": v["weight"]} for k, v in components.items()])
        fig_pie = px.pie(df_weights, values='權重', names='名稱', 
                         title="主力成分股權重分佈 (前十大)", hole=0.4)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_metrics:
        st.write("**前十大成分股即時走勢 (美股)**")
        m_cols1 = st.columns(5)  # 第一排 5 個
        m_cols2 = st.columns(5)  # 第二排 5 個
        
        m_cols_list = m_cols1 + m_cols2
        for idx, ticker in enumerate(components.keys()):
            current_p = latest_prices[ticker]
            prev_p = prev_prices[ticker]
            change = ((current_p / prev_p) - 1) * 100
            
            # 將代碼與純中文名稱組合在一起顯示
            display_label = f"{ticker} ({components[ticker]['name']})"
            m_cols_list[idx].metric(display_label, f"${current_p:.2f}", f"{change:.2f}%")

    st.divider()

    # --- 區塊 C：走勢聯動比較 (穿透分析) ---
    st.header("3. 走勢聯動比較 (近三個月)")
    st.markdown("觀察 009819 是否緊跟其最大權重股（如 AVGO 博通）或特定板塊（如電力基建）的趨勢。")
    
    # 計算累積報酬率 (以第一天為基準 0%)
    df_returns = (df_prices / df_prices.iloc[0] - 1) * 100
    
    fig_line = go.Figure()
    
    # 加入 009819 (特別加粗標示)
    fig_line.add_trace(go.Scatter(x=df_returns.index, y=df_returns[etf_ticker], 
                                  name="009819.TW", line=dict(color='red', width=4)))
    
    # 加入其他成分股 (折線圖也顯示中文)
    for ticker in components.keys():
        line_name = f"{ticker} {components[ticker]['name']}"
        fig_line.add_trace(go.Scatter(x=df_returns.index, y=df_returns[ticker], 
                                      name=line_name, opacity=0.7))
        
    fig_line.update_layout(
        title="009819 與核心成分股累積報酬率 (%)",
        yaxis_title="累積報酬率 (%)",
        xaxis_title="日期",
        hovermode="x unified",
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.divider()

    # --- 區塊 D：出場策略與賣出訊號分析 ---
    st.header("4. 🚨 出場策略與賣出訊號分析")
    st.markdown("結合技術指標與成分股動能，輔助判斷是否應逢高減碼。")

    # 計算 009819 與最大權重股 (AVGO) 的技術指標 (近 20 日移動平均)
    df_prices['009819_20MA'] = df_prices[etf_ticker].rolling(window=20).mean()
    df_prices['009819_RSI'] = calculate_rsi(df_prices[etf_ticker])
    
    df_prices['AVGO_20MA'] = df_prices['AVGO'].rolling(window=20).mean()
    df_prices['AVGO_RSI'] = calculate_rsi(df_prices['AVGO'])

    # 取得最新一天的指標數值
    latest_009819_rsi = df_prices['009819_RSI'].iloc[-1]
    latest_009819_ma = df_prices['009819_20MA'].iloc[-1]
    latest_avgo_rsi = df_prices['AVGO_RSI'].iloc[-1]
    
    col_sig1, col_sig2, col_sig3 = st.columns(3)

    # 訊號 1：009819 RSI 超買警告
    with col_sig1:
        st.subheader("指標 1：市場過熱度 (RSI)")
        st.metric("009819 目前 RSI (14日)", f"{latest_009819_rsi:.1f}")
        if latest_009819_rsi >= 75:
            st.error("⚠️ 強烈賣出訊號：RSI 超過 75，市場極度貪婪，隨時可能大幅回檔，建議獲利了結或減碼。")
        elif latest_009819_rsi >= 70:
            st.warning("⚠️ 警戒訊號：RSI 超過 70，進入超買區，請密切關注折溢價風險。")
        elif latest_009819_rsi <= 30:
            st.success("🟢 超賣區：RSI 低於 30，市場恐慌，可能為逢低佈局時機。")
        else:
            st.info("穩定區間：數值處於中性水平 (30-70)，無過熱跡象。")

    # 訊號 2：009819 趨勢破線警告
    with col_sig2:
        st.subheader("指標 2：短期趨勢 (20MA)")
        st.metric("009819 價格 vs 月線", f"市價: {etf_current:.2f} / 月線: {latest_009819_ma:.2f}")
        if etf_current < latest_009819_ma:
            st.error("⚠️ 跌破趨勢：市價已跌破 20 日月線，短期動能轉弱，需防範資金撤出風險。")
        else:
            st.success("🟢 趨勢健康：市價維持在 20 日月線之上，多頭格局延續。")

    # 訊號 3：老大哥動能警告 (博通 AVGO)
    with col_sig3:
        st.subheader("指標 3：最大權重股 (博通)")
        st.metric("博通 (AVGO) 目前 RSI", f"{latest_avgo_rsi:.1f}")
        if latest_avgo_rsi >= 70:
            st.warning("⚠️ 老大哥過熱：佔比近 25% 的博通已進入超買區，若其股價回檔，將直接重挫 009819 淨值。")
        elif df_prices['AVGO'].iloc[-1] < df_prices['AVGO_20MA'].iloc[-1]:
            st.error("⚠️ 底層動能流失：博通已跌破月線，ETF 缺乏領頭羊上漲動能。")
        else:
            st.info("老大哥穩健：最大成分股目前技術面健康，持續提供支撐。")

except Exception as e:
    st.error("獲取資料失敗，請確認網路連線或 Yahoo Finance 服務是否正常。")
    st.write(f"錯誤訊息：{e}")

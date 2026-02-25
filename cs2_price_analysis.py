import streamlit as st
import pandas as pd
import numpy as np
import requests
import pandas_ta as ta
import plotly.graph_objects as go
import urllib.parse
from datetime import datetime
import json

# ==========================================
# 0. ceviriler
# ==========================================
LANGS = {
    "TR": {
        "title": "CS2 Eşya Fiyatı Analiz Uygulaması",
        "desc": "Hisse senedi ve kripto teknik analiz yöntemlerinin (UT Bot, SSL Hybrid) CS2 pazar verilerine uygulanması.",
        "settings": "⚙️ Ayarlar",
        "lang_select": "🌍 Dil / Language",
        "item_name": "Eşya Adı (Market Hash Name)",
        "timeframe": "Zaman Dilimi",
        "tf_options": {"1D": "Günlük", "4H": "4 Saatlik", "12H": "12 Saatlik", "1W": "Haftalık"},
        "indicator_params": "İndikatör Parametreleri",
        "adv_settings": "Gelişmiş / API Ayarları",
        "api_info": "Eğer veri çekilemezse tarayıcınızdan 'steamLoginSecure' cookie değerini buraya girebilirsiniz.",
        "cookie_input": "steamLoginSecure Cookie (İsteğe bağlı)",
        "fetch_btn": "Verileri Getir ve Analiz Et",
        "fetching": "Veriler Steam üzerinden çekiliyor...",
        "success": "'{}' için veri başarıyla çekildi!",
        "price": "Fiyat",
        "buy": "AL (Buy)",
        "sell": "SAT (Sell)",
        "chart_title": "{} Market Grafiği ({})",
        "xaxis": "Tarih",
        "yaxis": "Fiyat (Para Birimi)",
        "table_title": "Son Veriler ve Sinyaller",
        "err_rate": "Steam API Rate-Limit (Çok fazla istek) aşıldı. Lütfen daha sonra tekrar deneyin veya geçerli bir Cookie girin.",
        "err_notfound": "Veri bulunamadı veya eşya adı hatalı. (Steam yanıtında fiyat tablosu yok.)\nHTTP Durumu: {}",
        "err_json": "Fiyat verisi JSON olarak ayrıştırılamadı: {}",
        "warn_empty": "Eşyanın fiyat geçmişi boş.",
        "err_http": "Steam API Bağlantı Hatası: {}",
        "err_unknown": "Bilinmeyen bir hata oluştu: {}"
    },
    "EN": {
        "title": "CS2 Item Price Analysis App",
        "desc": "Application of stock and crypto technical analysis methods (UT Bot, SSL Hybrid) to CS2 market data.",
        "settings": "⚙️ Settings",
        "lang_select": "🌍 Dil / Language",
        "item_name": "Item Name (Market Hash Name)",
        "timeframe": "Timeframe",
        "tf_options": {"1D": "Daily", "4H": "4 Hours", "12H": "12 Hours", "1W": "Weekly"},
        "indicator_params": "Indicator Parameters",
        "adv_settings": "Advanced / API Settings",
        "api_info": "If data cannot be fetched, you can enter your 'steamLoginSecure' cookie value here from your browser.",
        "cookie_input": "steamLoginSecure Cookie (Optional)",
        "fetch_btn": "Fetch Data and Analyze",
        "fetching": "Fetching data from Steam...",
        "success": "Data for '{}' successfully fetched!",
        "price": "Price",
        "buy": "BUY",
        "sell": "SELL",
        "chart_title": "{} Market Chart ({})",
        "xaxis": "Date",
        "yaxis": "Price (Currency)",
        "table_title": "Recent Data and Signals",
        "err_rate": "Steam API Rate-Limit exceeded. Please try again later or enter a valid Cookie.",
        "err_notfound": "Data not found or invalid item name. (No price table in Steam response.)\nHTTP Status: {}",
        "err_json": "Price data could not be parsed as JSON: {}",
        "warn_empty": "Item price history is empty.",
        "err_http": "Steam API Connection Error: {}",
        "err_unknown": "An unknown error occurred: {}"
    }
}

# ==========================================
# 1. VERİ ÇEKME (Data Fetching)
# ==========================================
def parse_steam_date(date_str):
    try:
        base = date_str.split(':')[0].strip()
        parts = base.split()
        if len(parts) == 4:
            return pd.to_datetime(base, format="%b %d %Y %H")
        else:
            return pd.to_datetime(base, format="%b %d %Y")
    except Exception as e:
        return pd.to_datetime(date_str, errors='coerce')

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_steam_price_history(market_hash_name, appid=730, cookie=None, lang="TR"):
    t = LANGS[lang]
    encoded_name = urllib.parse.quote(market_hash_name)
    url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Accept-Language": "en-US,en;q=0.9"
    }
    if cookie:
        headers["Cookie"] = cookie

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 429:
            st.error(t["err_rate"])
            return None
            
        response.raise_for_status()
        html_text = response.text
        
        search_str = "var line1="
        start_idx = html_text.find(search_str)
        if start_idx == -1:
            st.error(t["err_notfound"].format(response.status_code))
            return None
            
        start_idx += len(search_str)
        end_idx = html_text.find(";", start_idx)
        array_str = html_text[start_idx:end_idx].strip()
        
        try:
            prices = json.loads(array_str)
        except Exception as e:
            st.error(t["err_json"].format(e))
            return None
            
        if not prices:
            st.warning(t["warn_empty"])
            return None
            
        df = pd.DataFrame(prices, columns=["date", "price", "volume"])
        df['date'] = df['date'].apply(parse_steam_date)
        df['price'] = df['price'].astype(float)
        df['volume'] = df['volume'].astype(int)
        
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        return df

    except requests.exceptions.HTTPError as errHTTP:
        st.error(t["err_http"].format(errHTTP))
        return None
    except Exception as e:
        st.error(t["err_unknown"].format(e))
        return None

# ==========================================
# 2. VERİ İŞLEME (OHLCV Dönüşümü/ DO NOT TOUCH HERE!)
# ==========================================
def process_to_ohlcv(df, timeframe="1D"):
    if df is None or df.empty:
        return None
        
    ohlcv = df.resample(timeframe).agg({
        'price': ['first', 'max', 'min', 'last'],
        'volume': 'sum'
    }).dropna()
    
    ohlcv.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return ohlcv

# ==========================================
# 3. TEKNİK İNDİKATÖRLER (pandas_ta ile/ DO NOT TOUCH HERE!)
# Not: Aşağıdaki indikatör mantıkları TradingView'daki açık kaynaklı (Public Library) 
# topluluk script'lerinden (UT Bot Alerts by QuantNomad & SSL Hybrid by Mihkel00) 
# Python'a uyarlanmıştır. Orijinal algoritmalar ücretsiz kullanıma (open-source) açıktır.
# ==========================================
def calc_ssl_hybrid(df, baseline_len=60, ssl_len=10):
    df['baseline'] = ta.kama(df['Close'], length=baseline_len)
    if df['baseline'].isna().all():
        df['baseline'] = ta.ema(df['Close'], length=baseline_len)
        
    df['sma_high'] = ta.sma(df['High'], length=ssl_len)
    df['sma_low'] = ta.sma(df['Low'], length=ssl_len)
    
    hlv = np.where(df['Close'] > df['sma_high'], 1, np.where(df['Close'] < df['sma_low'], -1, np.nan))
    hlv = pd.Series(hlv, index=df.index).ffill()
    
    df['ssl_up'] = np.where(hlv < 0, df['sma_low'], df['sma_high'])
    df['ssl_down'] = np.where(hlv < 0, df['sma_high'], df['sma_low'])
    
    return df

def calc_ut_bot_alerts(df, key_value=2.0, atr_period=10):
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=atr_period)
    
    x_atr_trailing_stop = np.zeros(len(df))
    close = df['Close'].values
    atr = df['ATR'].values
    
    for i in range(1, len(df)):
        loss = key_value * atr[i]
        prev_stop = x_atr_trailing_stop[i-1]
        
        if close[i-1] > prev_stop:
            x_atr_trailing_stop[i] = max(prev_stop, close[i] - loss) if not np.isnan(prev_stop) else close[i] - loss
        elif close[i-1] < prev_stop:
            x_atr_trailing_stop[i] = min(prev_stop, close[i] + loss) if not np.isnan(prev_stop) else close[i] + loss
        else:
            x_atr_trailing_stop[i] = close[i] - loss if close[i] > close[i-1] else close[i] + loss

    df['UT_Stop'] = x_atr_trailing_stop
    
    buy_signals = []
    sell_signals = []
    position = 0
    
    for i in range(len(df)):
        if close[i] > x_atr_trailing_stop[i] and position == 0:
            buy_signals.append(True)
            sell_signals.append(False)
            position = 1
        elif close[i] < x_atr_trailing_stop[i] and position == 1:
            buy_signals.append(False)
            sell_signals.append(True)
            position = 0
        else:
            buy_signals.append(False)
            sell_signals.append(False)
            
    df['Buy_Signal'] = buy_signals
    df['Sell_Signal'] = sell_signals
    
    df['Buy_Marker'] = np.where(df['Buy_Signal'], df['Low'] - (df['ATR'] * 0.5), np.nan)
    df['Sell_Marker'] = np.where(df['Sell_Signal'], df['High'] + (df['ATR'] * 0.5), np.nan)
    
    return df

# ==========================================
# 4. ARAYÜZ VE GÖRSELLEŞTİRME (Streamlit & Plotly)
# ==========================================
def main():
    st.set_page_config(page_title="CS2 Price Analysis", layout="wide", initial_sidebar_state="expanded")

    # Hide Streamlit's default hamburger menu ("Settings" modal) completely and remove headers/footers
    hide_streamlit_style = """
    <style>
    /* Streamlit varsayilan menuyu gizle ama sidebar acma/kapama butonunu (data-testid='stSidebarCollapsedControl') gizleme */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    header > div {visibility: visible;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Init Language State
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'TR'

    with st.sidebar:
        # Language Selector
        lang_choice = st.radio("🌍 Dil / Language", options=["Türkçe (TR)", "English (EN)"], 
                               index=0 if st.session_state['lang'] == 'TR' else 1, horizontal=True)
        # Update session state based on choice
        lang = "TR" if "TR" in lang_choice else "EN"
        st.session_state['lang'] = lang
        t = LANGS[lang]

        st.header(t["settings"])
        item_name = st.text_input(t["item_name"], value="AK-47 | Redline (Field-Tested)")
        
        # Mapping timeframe choice back to internal keys ("1D", "4H", etc.)
        tf_options_keys = list(t["tf_options"].keys())
        timeframe = st.selectbox(t["timeframe"], options=tf_options_keys, index=0, 
                                 format_func=lambda x: t["tf_options"][x])
        
        st.subheader(t["indicator_params"])
        ut_key = st.number_input("UT Bot Key Value", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
        ut_atr = st.number_input("UT Bot ATR Period", min_value=1, max_value=50, value=10, step=1)
        
        with st.expander(t["adv_settings"]):
            st.info(t["api_info"])
            steam_cookie = st.text_input(t["cookie_input"], type="password")
            cookie_header = f"steamLoginSecure={steam_cookie}" if steam_cookie else None

    # Main Content Area
    st.title(t["title"])
    st.markdown(t["desc"])

    if st.button(t["fetch_btn"], type="primary"):
        with st.spinner(t["fetching"]):
            raw_df = fetch_steam_price_history(item_name, cookie=cookie_header, lang=lang)
            
        if raw_df is not None and not raw_df.empty:
            st.success(t["success"].format(item_name))
            
            # OHLCV transform and Indicators calculation
            ohlcv_df = process_to_ohlcv(raw_df, timeframe=timeframe)
            ohlcv_df = calc_ssl_hybrid(ohlcv_df)
            ohlcv_df = calc_ut_bot_alerts(ohlcv_df, key_value=ut_key, atr_period=ut_atr)
            
            # Graph Plotting
            fig = go.Figure()

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=ohlcv_df.index, open=ohlcv_df['Open'], high=ohlcv_df['High'],
                low=ohlcv_df['Low'], close=ohlcv_df['Close'], name=t["price"],
                increasing_line_color='green', decreasing_line_color='red'
            ))

            # SSL Lines
            fig.add_trace(go.Scatter(x=ohlcv_df.index, y=ohlcv_df['ssl_up'], line=dict(color='blue', width=1), name='SSL Up'))
            fig.add_trace(go.Scatter(x=ohlcv_df.index, y=ohlcv_df['ssl_down'], line=dict(color='orange', width=1), name='SSL Down'))
            
            # Baseline
            fig.add_trace(go.Scatter(x=ohlcv_df.index, y=ohlcv_df['baseline'], line=dict(color='white', width=1.5, dash='dash'), name='Baseline'))

            # UT Bot Markers
            fig.add_trace(go.Scatter(
                x=ohlcv_df.index, y=ohlcv_df['Buy_Marker'], mode='markers', 
                marker=dict(symbol='triangle-up', color='lime', size=12, line=dict(width=1, color='DarkSlateGrey')),
                name=t["buy"], text='AL' if lang == 'TR' else 'BUY', hoverinfo='text'
            ))
            
            fig.add_trace(go.Scatter(
                x=ohlcv_df.index, y=ohlcv_df['Sell_Marker'], mode='markers', 
                marker=dict(symbol='triangle-down', color='red', size=12, line=dict(width=1, color='DarkSlateGrey')),
                name=t["sell"], text='SAT' if lang == 'TR' else 'SELL', hoverinfo='text'
            ))

            fig.update_layout(
                title=t["chart_title"].format(item_name, t["tf_options"][timeframe]),
                xaxis_title=t["xaxis"],
                yaxis_title=t["yaxis"],
                height=700, template='plotly_dark', hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            
            st.subheader(t["table_title"])
            st.dataframe(ohlcv_df.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume', 'Buy_Signal', 'Sell_Signal']])

if __name__ == "__main__":
    main()

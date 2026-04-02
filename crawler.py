import time
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mplfinance as mpf
import matplotlib.pyplot as plt
from FinMind.data import DataLoader
import twstock

#抓即時股價
def get_realtime_price(symbol):
    try:
        realtime_data = twstock.realtime.get(symbol)
        if realtime_data['success']:
            info = realtime_data['realtime']
            latest = float(info['latest_trade_price']) if info['latest_trade_price'] != '-' else None
            if latest is None:
                latest = float(info['best_bid_price'][0]) if info['best_bid_price'][0] != '-' else None
            
            if latest is None: return None
            
            return {
                'Open': float(info['open']) if info['open'] != '-' else latest,
                'High': float(info['high']) if info['high'] != '-' else latest,
                'Low': float(info['low']) if info['low'] != '-' else latest,
                'Close': latest,
                'Volume': int(info['accumulate_trade_volume']) * 1000
            }
    except:
        return None

#畫 K 線圖
def plot_kline(df, company):
    if df is None or df.empty: return
    
    last_price = df['Close'].iloc[-1]
    last_date = df.index[-1].strftime('%Y-%m-%d')
    
    mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc) 

    fig, axlist =mpf.plot(
        df,
        type='candle',
        volume=True,
        mav=(5, 10, 20),
        title=f"\n{company} (Last: {last_price} @ {last_date})",
        style=s,
        hlines=dict(hlines=[last_price], colors=['red'], linestyle='-.'),
        tight_layout=True,
        returnfig=True,
        warn_too_much_data=1000
    )
    
    if fig.canvas.manager is not None:
            fig.canvas.manager.set_window_title(f"{company} K-Line Chart")
            
    plt.show()

#抓小型台指
def get_mtx_data():
    try:
        dl = DataLoader()
        start_date = (datetime.now() - relativedelta(months=12)).strftime("%Y-%m-%d")
        df = dl.taiwan_futures_daily(futures_id='MTX', start_date=start_date)
        if df.empty: return None

        df = df.sort_values(['date', 'volume'], ascending=[True, False]).drop_duplicates(subset=['date'])
        df = df.rename(columns={'date': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'volume': 'Volume'})
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
        
        return df[['Open', 'High', 'Low', 'Close', 'Volume']].apply(pd.to_numeric)
    except:
        return None

#抓一般股票資料
def get_stock_data(symbol):
    try:
        dl = DataLoader()
        start_date = (datetime.now() - relativedelta(months=6)).strftime("%Y-%m-%d")
        df = dl.taiwan_stock_daily(stock_id=symbol, start_date=start_date)
        if df.empty: return None

        df = df.rename(columns={'date': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'Trading_Volume': 'Volume'})
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
        
        return df[['Open', 'High', 'Low', 'Close', 'Volume']].apply(pd.to_numeric)
    except:
        return None


# 小台指
mtx_df = get_mtx_data()
if mtx_df is not None:
    plot_kline(mtx_df, "Small TX (MTX)")

# 股票
tickers = {
    "TSMC": "2330", 
    "N.P.C": "8046", 
    "Foxconn": "2317", 
    "MediaTek": "2454"
}

for company, symbol in tickers.items():
    print(f"\nFetching {company} {symbol}...")
    df = get_stock_data(symbol)
    
    if df is not None:
        rt = get_realtime_price(symbol)
        if rt:
            today = pd.Timestamp(datetime.now().date())
            
            if df.index[-1] == today:
                df.loc[today, ['Open', 'High', 'Low', 'Close', 'Volume']] = [rt['Open'], rt['High'], rt['Low'], rt['Close'], rt['Volume']]
            else:
                new_row = pd.DataFrame([rt], index=[today])
                df = pd.concat([df, new_row])

        #輸出後五筆(tail) 前五筆(head)
        print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail())
        plot_kline(df, company)
    
    time.sleep(1)
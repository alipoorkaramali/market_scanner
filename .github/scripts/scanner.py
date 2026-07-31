import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import ccxt
import requests
import time
from Config.config import CRYPTO_SYMBOLS, FOREX_SYMBOLS, TIMEFRAME, LOOKBACK_DAYS
from strategy import check_strategy

# ======================== تنظیمات FCS API ========================
FCS_API_KEY = os.environ.get('FCS_API_KEY')
if not FCS_API_KEY:
    raise Exception("FCS_API_KEY not found in environment variables!")

FCS_BASE_URL = "https://api-v4.fcsapi.com"

# ======================== توابع دریافت داده ========================

def fetch_ohlcv_okx(symbol: str, timeframe: str, limit: int):
    """دریافت داده کریپتو از OKX (با ccxt)"""
    exchange = ccxt.okx()
    exchange.enableRateLimit = True
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def fetch_ohlcv_fcs(symbol: str, timeframe: str, limit: int):
    """دریافت داده فارکس/طلا از FCS API"""
    timeframe_map = {
        '4h': '4h',
        '1d': '1d',
        '1w': '1w',
    }
    period = timeframe_map.get(timeframe, '4h')
    
    url = f"{FCS_BASE_URL}/forex/history"
    params = {
        'symbol': symbol.replace('/', ''),  # ← EURUSD
        'period': period,
        'limit': limit,
        'access_key': FCS_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if not data.get('status'):
        raise Exception(f"FCS API error: {data}")
    
    raw_data = data.get('response')
    if not raw_data:
        raise Exception("هیچ داده‌ای از FCS API دریافت نشد")
    
    rows = []
    
    # حالت ۱: اگر پاسخ دیکشنری باشد (کلیدها = زمان‌ها)
    if isinstance(raw_data, dict):
        for ts, values in raw_data.items():
            rows.append({
                'timestamp': pd.to_datetime(ts),
                'Open': float(values['open']),
                'High': float(values['high']),
                'Low': float(values['low']),
                'Close': float(values['close']),
                'Volume': 0
            })
    # حالت ۲: اگر پاسخ لیست باشد (هر آیتم یک دیکشنری)
    elif isinstance(raw_data, list):
        for item in raw_data:
            # پیدا کردن کلید زمان
            ts_key = None
            for key in ['time', 'date', 'timestamp']:
                if key in item:
                    ts_key = key
                    break
            if not ts_key:
                continue
            rows.append({
                'timestamp': pd.to_datetime(item[ts_key]),
                'Open': float(item['open']),
                'High': float(item['high']),
                'Low': float(item['low']),
                'Close': float(item['close']),
                'Volume': 0
            })
    else:
        raise Exception(f"ساختار پاسخ قابل تشخیص نیست: {type(raw_data)}")
    
    df = pd.DataFrame(rows)
    if df.empty:
        raise Exception("هیچ داده‌ای برای پردازش وجود ندارد")
    
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    return df
# ======================== تابع اسکن ========================

def scan():
    results = []
    
    # اسکن کریپتوها
    print("🔄 اسکن کریپتوها (OKX)...")
    for symbol in CRYPTO_SYMBOLS:
        try:
            print(f'  بررسی {symbol}...')
            df = fetch_ohlcv_okx(symbol, TIMEFRAME, LOOKBACK_DAYS)
            if check_strategy(df):
                results.append({
                    'symbol': symbol,
                    'price': df['Close'].iloc[-1],
                    'time': df.index[-1],
                    'type': 'Crypto'
                })
        except Exception as e:
            print(f'  ❌ خطا در {symbol}: {e}')
    
    # اسکن فارکس و طلا
    print("\n🔄 اسکن فارکس و طلا (FCS API)...")
    time.sleep(60)  # ← صبر برای ریست Rate Limit
    for symbol in FOREX_SYMBOLS:
        try:
            print(f'  بررسی {symbol}...')
            df = fetch_ohlcv_fcs(symbol, TIMEFRAME, LOOKBACK_DAYS)
            if check_strategy(df):
                results.append({
                    'symbol': symbol,
                    'price': df['Close'].iloc[-1],
                    'time': df.index[-1],
                    'type': 'Forex/Gold'
                })
            time.sleep(30)  # ← ۳۰ ثانیه مکث
        except Exception as e:
            print(f'  ❌ خطا در {symbol}: {e}')
            time.sleep(30)  # ← ۳۰ ثانیه مکث در صورت خطا
    
    return results

if __name__ == '__main__':
    signals = scan()
    
    if signals:
        print('\n🔥 سیگنال‌های پیدا شده:')
        for s in signals:
            print(f"  [{s['type']}] {s['symbol']} - قیمت: {s['price']:.2f} - زمان: {s['time']}")
    else:
        print('\n❌ هیچ سیگنالی پیدا نشد.')

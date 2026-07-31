import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import ccxt
import requests
from Config.config import SYMBOLS, TIMEFRAME, LOOKBACK_DAYS
from strategy import check_strategy

# ======================== تنظیمات FCS API ========================
FCS_API_KEY = "YOUR_FCS_API_KEY"  # از fcsapi.com دریافت کن
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
    # تبدیل تایم‌فریم به فرمت FCS
    timeframe_map = {
        '4h': '4h',
        '1d': '1d',
        '1w': '1w',
        # در صورت نیاز تایم‌فریم‌های دیگر اضافه کن
    }
    period = timeframe_map.get(timeframe, '4h')
    
    url = f"{FCS_BASE_URL}/forex/history"
    params = {
        'symbol': symbol,
        'period': period,
        'limit': limit,
        'access_key': FCS_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if not data.get('status'):
        raise Exception(f"FCS API error: {data}")
    
    # تبدیل پاسخ به دیتافریم
    # پاسخ معمولاً به شکل {'response': [{'c': 1.06687, 'o': 1.066...}, ...]} است
    # اما طبق مستندات، ممکن است به صورت دیکشنری با کلیدهای بازه زمانی برگردد
    # با فرض ساده‌ترین حالت: {'response': {'2026-07-31 12:00:00': {'open': 1.066..., ...}, ...}}
    raw_data = data.get('response', {})
    
    rows = []
    for ts, values in raw_data.items():
        rows.append({
            'timestamp': pd.to_datetime(ts),
            'Open': float(values['open']),
            'High': float(values['high']),
            'Low': float(values['low']),
            'Close': float(values['close']),
            'Volume': 0  # فارکس حجم معتبری ندارد
        })
    
    df = pd.DataFrame(rows)
    if df.empty:
        raise Exception("هیچ داده‌ای از FCS API دریافت نشد")
    
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    return df

def fetch_ohlcv(symbol: str, timeframe: str, limit: int):
    """
    تابع اصلی که بر اساس نوع نماد، از منبع مناسب داده می‌گیرد.
    - اگر symbol شامل '/' باشد → کریپتو (OKX)
    - در غیر این صورت → فارکس/طلا (FCS API)
    """
    if '/' in symbol:
        return fetch_ohlcv_okx(symbol, timeframe, limit)
    else:
        return fetch_ohlcv_fcs(symbol, timeframe, limit)

# ======================== تابع اسکن ========================

def scan():
    results = []
    for symbol in SYMBOLS:
        try:
            print(f'در حال بررسی {symbol}...')
            df = fetch_ohlcv(symbol, TIMEFRAME, LOOKBACK_DAYS)
            
            if check_strategy(df):
                results.append({
                    'symbol': symbol,
                    'price': df['Close'].iloc[-1],
                    'time': df.index[-1]
                })
        except Exception as e:
            print(f'خطا در {symbol}: {e}')
    
    return results

if __name__ == '__main__':
    signals = scan()
    if signals:
        print('\n🔥 سیگنال‌های پیدا شده:')
        for s in signals:
            print(f"  {s['symbol']} - قیمت: {s['price']:.2f} - زمان: {s['time']}")
    else:
        print('\n❌ هیچ سیگنالی پیدا نشد.')

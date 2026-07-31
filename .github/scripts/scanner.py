import pandas as pd
import ccxt
from config import SYMBOLS, TIMEFRAME, LOOKBACK_DAYS
from strategy import check_strategy

def fetch_ohlcv(symbol: str, timeframe: str, limit: int):
    """دریافت داده از صرافی با استفاده از ccxt"""
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

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

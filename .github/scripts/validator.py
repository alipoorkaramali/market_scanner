import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ccxt
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def fetch_data(exchange, symbol, timeframe='1d', limit=30):
    """دریافت داده از صرافی"""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def validate():
    print("🔄 در حال دریافت داده از OKX...")
    okx = ccxt.okx()
    df_okx = fetch_data(okx, 'BTC/USDT')
    
    print("🔄 در حال دریافت داده از KuCoin (برای مقایسه)...")
    kucoin = ccxt.kucoin()
    df_kucoin = fetch_data(kucoin, 'BTC/USDT')
    
    # رسم نمودار
    plt.figure(figsize=(12, 6))
    plt.plot(df_okx.index, df_okx['close'], label='OKX', marker='o', linewidth=2)
    plt.plot(df_kucoin.index, df_kucoin['close'], label='KuCoin', marker='x', linewidth=2)
    plt.title('مقایسه قیمت بیت‌کوین (BTC/USDT) - ۳۰ روز گذشته')
    plt.xlabel('تاریخ')
    plt.ylabel('قیمت (USDT)')
    plt.legend()
    plt.grid(alpha=0.3)
    
    # ذخیره نمودار
    os.makedirs('validation-results', exist_ok=True)
    plt.savefig('validation-results/compare.png', dpi=150, bbox_inches='tight')
    print("✅ نمودار ذخیره شد: validation-results/compare.png")
    
    # محاسبه آمار
    avg_okx = df_okx['close'].mean()
    avg_kucoin = df_kucoin['close'].mean()
    diff_percent = ((avg_okx - avg_kucoin) / avg_kucoin) * 100
    
    # ذخیره آمار در فایل متنی
    with open('validation-results/stats.txt', 'w') as f:
        f.write(f"تاریخ اجرا: {datetime.now()}\n")
        f.write(f"میانگین قیمت OKX: {avg_okx:.2f} USDT\n")
        f.write(f"میانگین قیمت KuCoin: {avg_kucoin:.2f} USDT\n")
        f.write(f"اختلاف درصدی: {diff_percent:.4f}%\n")
        f.write(f"تعداد کندل‌ها: {len(df_okx)}\n")
    
    print(f"\n📊 میانگین قیمت OKX: {avg_okx:.2f}")
    print(f"📊 میانگین قیمت KuCoin: {avg_kucoin:.2f}")
    print(f"📊 اختلاف درصدی: {diff_percent:.4f}%")
    
    if abs(diff_percent) < 0.5:
        print("✅ داده‌ها معتبر هستند. اختلاف کمتر از ۰.۵٪.")
    else:
        print("⚠️ اختلاف قابل توجه! داده‌ها را بررسی کنید.")

if __name__ == '__main__':
    validate()

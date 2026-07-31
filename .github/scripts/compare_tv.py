import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

def fetch_data(exchange, symbol='BTC/USDT', timeframe='4h', limit=180):
    """دریافت داده از صرافی"""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def compare_dataframes(df_okx, df_kucoin):
    """مقایسه خودکار دو دیتافریم و محاسبه اختلاف‌ها"""
    
    # پیدا کردن تاریخ‌های مشترک
    common_dates = df_okx.index.intersection(df_kucoin.index)
    df_okx_common = df_okx.loc[common_dates]
    df_kucoin_common = df_kucoin.loc[common_dates]
    
    # محاسبه اختلاف درصدی برای هر ستون
    diff_open = ((df_okx_common['open'] - df_kucoin_common['open']) / df_kucoin_common['open']) * 100
    diff_high = ((df_okx_common['high'] - df_kucoin_common['high']) / df_kucoin_common['high']) * 100
    diff_low = ((df_okx_common['low'] - df_kucoin_common['low']) / df_kucoin_common['low']) * 100
    diff_close = ((df_okx_common['close'] - df_kucoin_common['close']) / df_kucoin_common['close']) * 100
    
    # ایجاد دیتافریم اختلافات
    diff_df = pd.DataFrame({
        'OKX_Close': df_okx_common['close'],
        'KuCoin_Close': df_kucoin_common['close'],
        'Diff_Close_%': diff_close,
        'Diff_Open_%': diff_open,
        'Diff_High_%': diff_high,
        'Diff_Low_%': diff_low
    })
    
    # آمار نهایی
    stats = {
        'max_diff_close': diff_close.max(),
        'min_diff_close': diff_close.min(),
        'avg_diff_close': diff_close.mean(),
        'std_diff_close': diff_close.std(),
        'max_abs_diff_close': diff_close.abs().max(),
        'avg_abs_diff_close': diff_close.abs().mean(),
        'count_bad_candles': len(diff_close[diff_close.abs() > 0.5]),  # کندل‌های با اختلاف بیش از 0.5٪
        'total_candles': len(diff_close)
    }
    
    return diff_df, stats

def main():
    print("🔄 در حال دریافت داده از OKX...")
    okx = ccxt.okx()
    df_okx = fetch_data(okx)
    
    print("🔄 در حال دریافت داده از KuCoin...")
    kucoin = ccxt.kucoin()
    df_kucoin = fetch_data(kucoin)
    
    print("🔍 در حال مقایسه خودکار داده‌ها...")
    diff_df, stats = compare_dataframes(df_okx, df_kucoin)
    
    # ایجاد پوشه خروجی
    os.makedirs('comparison-results', exist_ok=True)
    
    # ذخیره جدول اختلافات
    diff_df.to_csv('comparison-results/detailed_comparison.csv')
    print("✅ جدول اختلافات ذخیره شد: comparison-results/detailed_comparison.csv")
    
    # ایجاد گزارش
    with open('comparison-results/report.txt', 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("📊 گزارش مقایسه خودکار داده‌های OKX با KuCoin\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"تاریخ اجرا: {datetime.now()}\n")
        f.write(f"تعداد کندل‌های بررسی شده: {stats['total_candles']}\n")
        f.write(f"بازه زمانی: از {diff_df.index[0]} تا {diff_df.index[-1]}\n\n")
        
        f.write("📈 آمار اختلاف قیمت بسته شدن (Close):\n")
        f.write(f"  - میانگین اختلاف: {stats['avg_diff_close']:.4f}%\n")
        f.write(f"  - میانگین قدر مطلق اختلاف: {stats['avg_abs_diff_close']:.4f}%\n")
        f.write(f"  - بیشترین اختلاف: {stats['max_diff_close']:.4f}%\n")
        f.write(f"  - کمترین اختلاف: {stats['min_diff_close']:.4f}%\n")
        f.write(f"  - انحراف معیار: {stats['std_diff_close']:.4f}%\n\n")
        
        f.write("⚠️ کندل‌های با اختلاف بیش از 0.5%:\n")
        f.write(f"  - تعداد: {stats['count_bad_candles']} از {stats['total_candles']}\n")
        
        if stats['count_bad_candles'] == 0:
            f.write("\n✅ نتیجه: داده‌های OKX دقیق هستند! (هیچ اختلاف قابل توجهی یافت نشد)\n")
        elif stats['count_bad_candles'] < stats['total_candles'] * 0.05:
            f.write("\n⚠️ نتیجه: داده‌ها نسبتاً دقیق هستند. (کمتر از 5% کندل‌ها اختلاف دارند)\n")
        else:
            f.write("\n❌ نتیجه: داده‌ها مشکل دارند! (بیش از 5% کندل‌ها اختلاف دارند)\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("📌 نکته: اختلاف کمتر از 0.5% برای هر کندل طبیعی است.\n")
        f.write("   این اختلاف به خلاف تفاوت در زمان بسته شدن کندل‌ها در صرافی‌هاست.\n")
    
    print("✅ گزارش نهایی ذخیره شد: comparison-results/report.txt")
    
    # نمایش خلاصه در ترمینال
    print("\n" + "="*60)
    print("📊 خلاصه مقایسه:")
    print("="*60)
    print(f"تعداد کندل‌ها: {stats['total_candles']}")
    print(f"میانگین اختلاف Close: {stats['avg_diff_close']:.4f}%")
    print(f"میانگین قدر مطلق اختلاف: {stats['avg_abs_diff_close']:.4f}%")
    print(f"تعداد کندل‌های مشکوک (>0.5%): {stats['count_bad_candles']}")
    
    if stats['count_bad_candles'] == 0:
        print("\n✅ داده‌های OKX دقیق هستند!")
    else:
        print(f"\n⚠️ {stats['count_bad_candles']} کندل اختلاف دارند. فایل detailed_comparison.csv را بررسی کنید.")

if __name__ == '__main__':
    main()

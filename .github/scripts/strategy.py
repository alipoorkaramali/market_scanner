import pandas as pd
import pandas_ta as ta

def check_strategy(df: pd.DataFrame) -> bool:
    """
    بررسی می‌کند که آیا در آخرین کندل، سیگنال خرید وجود دارد یا نه.
    اینجا یه استراتژی ساده با RSI و EMA می‌نویسیم.
    شما می‌تونید هر استراتژی که بلدید رو اینجا پیاده کنید.
    """
    if len(df) < 50:
        return False
    
    # محاسبه اندیکاتورها
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # سیگنال خرید: EMA20 از بالای EMA50 عبور کرده و RSI بین ۳۰ تا ۷۰ باشه
    buy_signal = (
        prev['EMA_20'] <= prev['EMA_50'] and
        latest['EMA_20'] > latest['EMA_50'] and
        30 < latest['RSI'] < 70
    )
    
    return buy_signal

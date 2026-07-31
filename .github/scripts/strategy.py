import pandas as pd
import pandas_ta as ta

def check_strategy(df: pd.DataFrame) -> bool:
    """
    بررسی سیگنال خرید:
    - EMA 20 از بالای EMA 50 عبور کرده باشد (Golden Cross)
    - RSI بین ۳۰ تا ۷۰ باشد
    """
    if len(df) < 50:
        return False
    
    df['EMA20'] = ta.ema(df['Close'], length=20)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    golden_cross = (prev['EMA20'] <= prev['EMA50']) and (latest['EMA20'] > latest['EMA50'])
    rsi_filter = 30 < latest['RSI'] < 70
    
    return golden_cross and rsi_filter
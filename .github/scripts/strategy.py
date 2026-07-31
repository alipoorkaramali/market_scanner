import pandas as pd
import ta  # جایگزین pandas_ta

def check_strategy(df: pd.DataFrame) -> bool:
    if len(df) < 50:
        return False
    
    # محاسبه اندیکاتورها با کتابخانه ta
    df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
    df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # شرط برخورد طلایی (Golden Cross)
    golden_cross = (prev['EMA20'] <= prev['EMA50']) and (latest['EMA20'] > latest['EMA50'])
    rsi_filter = 30 < latest['RSI'] < 70
    
    return golden_cross and rsi_filter
def fetch_ticker_data(ticker, hebrew_name, is_saturday):
    try:
        stock = yf.Ticker(ticker)
        period = "1mo" if is_saturday else ("5d" if "BTC" in ticker else "2d")
        history = stock.history(period=period, timeout=5)
        
        if len(history) < 2:
            print(n=f"⚠️ אזהרה: לא נמצאו מספיק נתונים עבור הסימול {ticker}")
            return None
            
        current_price = history['Close'].iloc[-1]
        high_price = history['High'].iloc[-1]
        low_price = history['Low'].iloc[-1]
        volume = history['Volume'].iloc[-1]
        
        if is_saturday and len(history) >= 5:
            prev_close = history['Close'].iloc[-5]
        else:
            prev_close = history['Close'].iloc[-2]
        
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            'ticker': ticker,
            'hebrew_name': hebrew_name,
            'current_price': float(current_price),
            'change': float(change),
            'change_percent': float(change_percent),
            'high_price': float(high_price),
            'low_price': float(low_price),
            'volume': int(volume)
        }
    except Exception as e:
        print(f"❌ שגיאה בשליפת הנתונים עבור {ticker}: {e}")
        return None

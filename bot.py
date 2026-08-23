import os
import requests
import yfinance as yf
from datetime import datetime
import pytz

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# רשימת כל המניות והנכסים המלאה
TICKERS = [
    # אמריקה וטכנולוגיה
    "AAPL", "TSLA", "MSFT", "NVDA", "PLTR", "INTC", "PYPL", 
    "GOOGL", "AMZN", "META", "NFLX",
    # תעופה, ביטחון ותעשייה
    "LMT", "BA", "WMT",
    # פארמה ובריאות
    "MRNA", "MRK", "TEVA.TA",
    # סייבר, פינטק וטכנולוגיה מתקדמת
    "MBLY", "SMCI", "S", "CHKP", "COIN",
    # קריפטו
    "BTC-USD", "ETH-USD",
    # מדדים וקרנות
    "VOO", "TA125.TA", "^VIX", "PROK", "BMR"
]

def get_stock_data():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    current_time = datetime.now(israel_tz)
    date_str = current_time.strftime("%d/%m/%Y")
    time_str = current_time.strftime("%H:%M:%S")
    
    hour = current_time.hour
    if hour < 15:
        header_title = "⏰ 3 שעות עד פתיחת המסחר בוול סטריט (זמן אמת)"
    else:
        header_title = "🌙 סיכום סוף יום מסחר"

    message = f"📅 {date_str} {time_str}\n{header_title}\n\n📊 המניות שלך:\n\n"

    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            # לוקחים נתונים של 5 ימים אחורה כדי לוודא שיש השוואה מדויקת לסגירה הקודמת
            todays_data = stock.history(period="5d")

            if todays_data.empty or len(todays_data) < 2:
                continue

            close_price = todays_data["Close"].iloc[-1]
            prev_close = todays_data["Close"].iloc[-2] # מחיר סגירה של יום המסחר הקודם
            
            high_price = todays_data["High"].iloc[-1]
            low_price = todays_data["Low"].iloc[-1]
            volume = int(todays_data["Volume"].iloc[-1])

            diff = close_price - prev_close
            change = (diff / prev_close) * 100

            emoji_trend = "🟢" if change >= 0 else "🔴"
            status_text = "עולה" if change >= 0 else "יורד"
            sign = "+" if change >= 0 else ""
            display_name = ticker.replace("-USD", "").replace("^", "")

            message += f"📊 *{display_name}*\n"
            message += f"💵 מחיר: `{close_price:,.2f}$`\n"
            message += f"📊 שינוי: `{sign}{change:.2f}%` ({sign}{diff:,.2f}$)\n"
            message += f"🔼 גבוה: `{high_price:,.2f}` | 📉 נמוך: `{low_price:,.2f}`\n"
            message += f"📦 נפח: `{volume:,}`\n"
            message += f"📈 מצב: {emoji_trend} {status_text}\n"
            message += "〰️〰️〰️〰️〰️〰️\n"
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    return message

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    stock_report = get_stock_data()
    send_telegram_message(stock_report)

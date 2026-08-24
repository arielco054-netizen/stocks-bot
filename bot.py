import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STOCKS_INFO = {
    "AAPL": {"he": "אפל"},
    "TSLA": {"he": "טסלה"},
    "MSFT": {"he": "מיקרוסופט"},
    "NVDA": {"he": "אנבידיה"},
    "PLTR": {"he": "פלנטיר"},
    "INTC": {"he": "אינטל"},
    "PYPL": {"he": "פייפאל"},
    "GOOGL": {"he": "גוגל"},
    "AMZN": {"he": "אמזון"},
    "META": {"he": "מטא"},
    "NFLX": {"he": "נטפליקס"},
    "LMT": {"he": "לוקהיד מרטין"},
    "BA": {"he": "בואינג"},
    "WMT": {"he": "ולמארט"},
    "MRNA": {"he": "מודרנה"},
    "TEVA.TA": {"he": "טבע"},
    "1155324.TA": {"he": "ת\"א 125"},
    "MBLY": {"he": "מובילאיי"},
    "SMCI": {"he": "סופר מיקרו"},
    "CHKP": {"he": "צ'ק פוינט"},
    "BTC-USD": {"he": "ביטקוין"},
    "ETH-USD": {"he": "את'ריום"},
    "VOO": {"he": "S&P 500"},
    "^VIX": {"he": "מדד הפחד"}
}

def get_stock_data():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    current_time = datetime.now(israel_tz)
    date_str = current_time.strftime("%d/%m/%Y %H:%M")
    
    message = f"📅 {date_str}\n📊 **סיכום המניות שלך:**\n\n"

    for ticker, info in STOCKS_INFO.items():
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period="5d")

            if todays_data.empty or len(todays_data) < 2:
                continue

            close_price = todays_data["Close"].iloc[-1]
            prev_close = todays_data["Close"].iloc[-2]

            if ".TA" in ticker:
                close_price = close_price / 100
                prev_close = prev_close / 100

            diff = close_price - prev_close
            change = (diff / prev_close) * 100 if prev_close > 0 else 0.0

            emoji_trend = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            currency = "₪" if ".TA" in ticker else "$"

            message += f"{emoji_trend} *{info['he']}*: `{close_price:,.2f}{currency}` (`{sign}{change:.2f}%`)\n"
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
    res = send_telegram_message(stock_report)
    print("Telegram response:", res)

import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STOCKS_INFO = {
    "AAPL": {"en": "Apple Inc.", "he": "אפל"},
    "TSLA": {"en": "Tesla Inc.", "he": "טסלה"},
    "MSFT": {"en": "Microsoft Corporation", "he": "מיקרוסופט"},
    "NVDA": {"en": "NVIDIA Corporation", "he": "אנבידיה"},
    "PLTR": {"en": "Palantir Technologies Inc.", "he": "פלנטיר טכנולוגיות"},
    "INTC": {"en": "Intel Corporation", "he": "אינטל"},
    "PYPL": {"en": "PayPal Holdings Inc.", "he": "פייפאל"},
    "GOOGL": {"en": "Alphabet Inc. (Google)", "he": "אלפאבית / גוגל"},
    "AMZN": {"en": "Amazon.com Inc.", "he": "אמזון"},
    "META": {"en": "Meta Platforms Inc.", "he": "מטא פלטפורמס"},
    "NFLX": {"en": "Netflix Inc.", "he": "נטפליקס"},
    "LMT": {"en": "Lockheed Martin Corporation", "he": "לוקהיד מרטין"},
    "BA": {"en": "The Boeing Company", "he": "בואינג"},
    "WMT": {"en": "Walmart Inc.", "he": "ולמארט"},
    "MRNA": {"en": "Moderna Inc.", "he": "מודרנה"},
    "MRK": {"en": "Merck & Co. Inc.", "he": "מרק"},
    "TEVA.TA": {"en": "Teva Pharmaceutical Industries Ltd.", "he": "טבע תעשיות פרמצבטיות"},
    "1155324.TA": {"en": "IBI SAL (4A) Kosher TA-125 IL ETF", "he": "מדד ישראלי - קרן סל IBI כשרה ת\"א 125"},
    "MBLY": {"en": "Mobileye Global Inc.", "he": "מובילאיי"},
    "SMCI": {"en": "Super Micro Computer Inc.", "he": "סופר מיקרו קומפיוטר"},
    "S": {"en": "SentinelOne Inc.", "he": "סנטינל וואן"},
    "CHKP": {"en": "Check Point Software Technologies Ltd.", "he": "צ'ק פוינט תוכנה"},
    "COIN": {"en": "Coinbase Global Inc.", "he": "קוינבייס"},
    "BTC-USD": {"en": "Bitcoin USD", "he": "ביטקוין"},
    "ETH-USD": {"en": "Ethereum USD", "he": "את'ריום"},
    "VOO": {"en": "Vanguard S&P 500 ETF", "he": "קרן סל ונגארד S&P 500"},
    "^VIX": {"en": "CBOE Volatility Index", "he": "מדד הפחד VIX"},
    "PROK": {"en": "ProK", "he": "פרוק"},
    "BMR": {"en": "BMR", "he": "ב.מ.ר"}
}

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

    message = f"📅 {date_str} {time_str}\n{header_title}\n\n📊 המניות והנכסים שלך:\n\n"

    for ticker, info in STOCKS_INFO.items():
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period="5d")

            if todays_data.empty or len(todays_data) < 2:
                continue

            close_price = todays_data["Close"].iloc[-1]
            prev_close = todays_data["Close"].iloc[-2]
            high_price = todays_data["High"].iloc[-1]
            low_price = todays_data["Low"].iloc[-1]
            volume = int(todays_data["Volume"].iloc[-1]) if "Volume" in todays_data and not pd.isna(todays_data["Volume"].iloc[-1]) else 0

            if ".TA" in ticker:
                close_price = close_price / 100
                prev_close = prev_close / 100
                high_price = high_price / 100
                low_price = low_price / 100

            diff = close_price - prev_close
            change = (diff / prev_close) * 100 if prev_close > 0 else 0.0

            emoji_trend = "🟢" if change >= 0 else "🔴"
            status_text = "עולה" if change >= 0 else "יורד"
            sign = "+" if change >= 0 else ""
            
            currency_symbol = "₪" if ".TA" in ticker else "$"

            message += f"📊 *{info['he']}* | {info['en']}\n"
            message += f"💵 מחיר: `{close_price:,.2f}{currency_symbol}`\n"
            message += f"📊 שינוי: `{sign}{change:.2f}%` ({sign}{diff:,.2f}{currency_symbol})\n"
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
    res = send_telegram_message(stock_report)
    print("Telegram response:", res)

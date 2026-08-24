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
    "TEVA.TA": {"en": "Teva Pharmaceutical", "he": "טבע"},
    "1155324.TA": {"en": "IBI TA-125 IL ETF", "he": "ת\"א 125"},
    "MBLY": {"en": "Mobileye Global Inc.", "he": "מובילאיי"},
    "SMCI": {"en": "Super Micro Computer", "he": "סופר מיקרו"},
    "CHKP": {"en": "Check Point Software", "he": "צ'ק פוינט"},
    "COIN": {"en": "Coinbase Global Inc.", "he": "קוינבייס"},
    "BTC-USD": {"en": "Bitcoin USD", "he": "ביטקוין"},
    "ETH-USD": {"en": "Ethereum USD", "he": "את'ריום"},
    "VOO": {"en": "Vanguard S&P 500 ETF", "he": "קרן סל S&P 500"},
    "^VIX": {"en": "CBOE Volatility Index", "he": "מדד הפחד VIX"},
    "PROK": {"en": "ProK", "he": "פרוק"},
    "BMR": {"en": "BMR", "he": "ב.מ.ר"}
}

def get_stock_reports():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    current_time = datetime.now(israel_tz)
    date_str = current_time.strftime("%d/%m/%Y %H:%M")
    
    items = list(STOCKS_INFO.items())
    mid_point = len(items) // 2
    
    part1_items = items[:mid_point]
    part2_items = items[mid_point:]

    def build_chunk(sub_items, title_suffix):
        msg = f"📅 {date_str}\n📊 **סיכום מניות {title_suffix}:**\n\n"
        for ticker, info in sub_items:
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

                if pd.isna(close_price) or pd.isna(prev_close):
                    continue

                if ".TA" in ticker:
                    close_price = close_price / 100
                    prev_close = prev_close / 100
                    high_price = high_price / 100
                    low_price = low_price / 100

                diff = close_price - prev_close
                change = (diff / prev_close) * 100 if prev_close > 0 else 0.0

                emoji_trend = "🟢" if change >= 0 else "🔴"
                sign = "+" if change >= 0 else ""
                currency = "₪" if ".TA" in ticker else "$"

                msg += f"📊 {emoji_trend} *{info['he']}* | {info['en']}\n"
                msg += f"💵 מחיר: `{close_price:,.2f}{currency}`\n"
                msg += f"📊 שינוי: `{sign}{change:.2f}%` ({sign}{diff:,.2f}{currency})\n"
                msg += f"🔼 גבוה: `{high_price:,.2f}` | 📉 נמוך: `{low_price:,.2f}`\n"
                msg += f"📦 נפח: `{volume:,}`\n"
                msg += "〰️〰️〰️〰️〰️〰️\n"
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        return msg

    report1 = build_chunk(part1_items, "חלק א'")
    report2 = build_chunk(part2_items, "חלק ב'")
    return report1, report2

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    report1, report2 = get_stock_reports()
    res1 = send_telegram_message(report1)
    res2 = send_telegram_message(report2)
    print("Telegram responses:", res1, res2)

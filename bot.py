import os
import time
import telebot
import yfinance as yf
from datetime import datetime
import pytz
import schedule
from concurrent.futures import ThreadPoolExecutor, as_completed

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)

ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')

TICKERS = {
    "MRNA": ("מודרנה", "Moderna Inc."),
    "^VIX": ("מדד הפחד VIX", "CBOE Volatility Index"),
    "MRK": ("מרק", "Merck & Co. Inc."),
    "NFLX": ("נטפליקס", "Netflix Inc."),
    "WMT": ("ולמארט", "Walmart Inc."),
    "AMZN": ("אמזון", "Amazon.com Inc."),
    "BA": ("בואינג", "The Boeing Company"),
    "META": ("מטא פלטפורמס", "Meta Platforms Inc."),
    "PYPL": ("פייפאל", "PayPal Holdings Inc."),
    "GOOGL": ("אלפאבית / גוגל", "Alphabet Inc. (Google)"),
    "LMT": ("לוקהיד מרטין", "Lockheed Martin Corporation"),
    "AAPL": ("אפל", "Apple Inc."),
    "MBLY": ("מובילאיי", "Mobileye Global Inc."),
    "BTC-USD": ("ביטקוין", "Bitcoin USD"),
    "^TA125.TA": ("מדד תל אביב 125", "TA-125 Index"),
    "MSFT": ("מיקרוסופט", "Microsoft Corporation"),
    "BMR": ("ב.מ.ר", "BMR"),
    "TSLA": ("טסלה", "Tesla Inc."),
    "SMCI": ("סופר מיקרו", "Super Micro Computer"),
    "CHKP": ("צ'ק פוינט", "Check Point Software"),
    "INTC": ("אינטל", "Intel Corporation"),
    "PROK": ("פרוק", "ProK"),
    "PLTR": ("פלנטיר טכנולוגיות", "Palantir Technologies Inc."),
    "COIN": ("קוינבייס", "Coinbase Global Inc."),
    "NVDA": ("אנבידיה", "NVIDIA Corporation")
}

def fetch_single_ticker(ticker, hebrew_name):
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="5d" if "BTC" in ticker else "2d", timeout=5)
        
        if len(history) < 2:
            return None
            
        prev_close = history['Close'].iloc[-2]
        current_price = history['Close'].iloc[-1]
        high_price = history['High'].iloc[-1]
        low_price = history['Low'].iloc[-1]
        volume = history['Volume'].iloc[-1]
        
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
    except Exception:
        return None

def send_daily_summary():
    if not CHAT_ID:
        print("שגיאה: CHAT_ID לא מוגדר")
        return

    print("\n⏳ השעה הגיעה! אוסף נתונים...")
    start_time = time.time()
    
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_single_ticker, ticker, names[0]): ticker 
            for ticker, names in TICKERS.items()
        }
        
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    if not results:
        print("❌ לא נמצאו נתונים לשליחה.")
        return

    results.sort(key=lambda x: x['change_percent'])

    mid_index = len(results) // 2
    part1 = results[:mid_index]
    part2 = results[mid_index:]

    current_date = datetime.now(ISRAEL_TZ).strftime("%d/%m/%Y %H:%M")

    def format_block(items):
        lines = []
        for item in items:
            is_pos = item['change'] >= 0
            sign = "+" if is_pos else ""
            emoji = "🟢" if is_pos else "🔴"
            price_suffix = "$" if "BTC" not in item['ticker'] and "TA125" not in item['ticker'] else (" USD" if "BTC" in item['ticker'] else " נקודות")
            
            line = (
                f"📊 {emoji} {item['hebrew_name']} | {TICKERS[item['ticker']][1]}\n"
                f"💵 מחיר: {item['current_price']:,.2f}{price_suffix}\n"
                f"📊 שינוי: {sign}{item['change_percent']:.2f}% ({sign}{item['change']:,.2f})\n"
                f"🔼 גבוה: {item['high_price']:,.2f} | 📉 נמוך: {item['low_price']:,.2f}\n"
                f"📦 נפח: {item['volume']:,}\n"
                f"📅 עדכון: {current_date}\n"
                f"〰️〰️〰️〰️〰️〰️"
            )
            lines.append(line)
        return "\n".join(lines)
    
    message1 = f"📊 <b>סיכום סוף מסחר חלק א':</b>\n\n" + format_block(part1)
    message2 = f"📊 <b>סיכום מניות חלק ב':</b>\n\n" + format_block(part2)

    try:
        bot.send_message(CHAT_ID, message1, parse_mode="HTML")
        bot.send_message(CHAT_ID, message2, parse_mode="HTML")
        elapsed_time = time.time() - start_time
        print(f"🚀 נשלח בהצלחה לטלגרם! לקח {elapsed_time:.2f} שניות.")
    except Exception as e:
        print(f"❌ שגיאה בשליחה לטלגרם: {e}")

# תזמון מדויק: שני עד שישי בשעה 23:00, ושבת בשעה 21:00
schedule.every().monday.at("23:00", "Asia/Jerusalem").do(send_daily_summary)
schedule.every().tuesday.at("23:00", "Asia/Jerusalem").do(send_daily_summary)
schedule.every().wednesday.at("23:00", "Asia/Jerusalem").do(send_daily_summary)
schedule.every().thursday.at("23:00", "Asia/Jerusalem").do(send_daily_summary)
schedule.every().friday.at("23:00", "Asia/Jerusalem").do(send_daily_summary)
schedule.every().saturday.at("21:00", "Asia/Jerusalem").do(send_daily_summary)

if __name__ == '__main__':
    print("🤖 הבוט פועל ברקע בשקט מלא ולא ישלח כלום עכשיו. ממתין לתזמונים שהוגדרו...")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

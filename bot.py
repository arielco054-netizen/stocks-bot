import os
import time
import telebot
import yfinance as yf
from datetime import datetime
import pytz
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

def fetch_ticker_data(ticker, hebrew_name, is_saturday):
    try:
        stock = yf.Ticker(ticker)
        # בשבת נבקש היסטוריה של חודש כדי לוודא שנתפוס את תחילת השבוע המסחרי בצורה מדויקת
        period = "1mo" if is_saturday else ("5d" if "BTC" in ticker else "2d")
        history = stock.history(period=period, timeout=5)
        
        if len(history) < 2:
            return None
            
        current_price = history['Close'].iloc[-1]
        high_price = history['High'].iloc[-1]
        low_price = history['Low'].iloc[-1]
        volume = history['Volume'].iloc[-1]
        
        if is_saturday and len(history) >= 5:
            # בשבת: לוקחים את נקודת ההתחלה של תחילת השבוע המסחרי (5 ימי מסחר אחורה)
            prev_close = history['Close'].iloc[-5]
        else:
            # ביום רגיל: לוקחים את סגירת יום המסחר הקודם
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
    except Exception:
        return None

def main():
    if not CHAT_ID or not TOKEN:
        print("שגיאה: BOT_TOKEN או CHAT_ID אינם מוגדרים")
        return

    now_israel = datetime.now(ISRAEL_TZ)
    is_saturday = now_israel.weekday() == 5

    report_type = "סיכום שבועי מצטבר (כל ימי המסחר)" if is_saturday else "סיכום יומי"
    print(f"⏳ אוסף נתונים עבור {report_type}...")
    start_time = time.time()
    
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_ticker_data, ticker, names[0], is_saturday): ticker 
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

    current_date = now_israel.strftime("%d/%m/%Y %H:%M")
    title_suffix = "סיכום שבועי מצטבר" if is_saturday else "סיכום סוף מסחר יומי"

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
    
    message1 = f"📊 <b>{title_suffix} חלק א':</b>\n\n" + format_block(part1)
    message2 = f"📊 <b>{title_suffix} חלק ב':</b>\n\n" + format_block(part2)

    try:
        bot.send_message(CHAT_ID, message1, parse_mode="HTML")
        bot.send_message(CHAT_ID, message2, parse_mode="HTML")
        elapsed_time = time.time() - start_time
        print(f"🚀 נשלח בהצלחה לטלגרם! לקח {elapsed_time:.2f} שניות.")
    except Exception as e:
        print(f"❌ שגיאה בשליחה לטלגרם: {e}")

if __name__ == '__main__':
    main()

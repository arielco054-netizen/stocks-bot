import os
import time
import telebot
import yfinance as yf
from datetime import datetime
import pytz
import schedule

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)

# הגדרת אזור זמן של ישראל
ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')

# 25 המניות והנכסים המדויקים שלך בלבד
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

def send_daily_summary():
    if not CHAT_ID:
        print("שגיאה: CHAT_ID לא מוגדר")
        return

    print("\n⏳ מתחיל לאסוף נתונים ל-25 המניות וישלח מיד...")
    start_time = time.time()
    
    results = []

    for ticker, (hebrew_name, eng_name) in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="5d" if "BTC" in ticker else "2d")
            
            if len(history) < 2:
                continue
                
            prev_close = history['Close'].iloc[-2]
            current_price = history['Close'].iloc[-1]
            high_price = history['High'].iloc[-1]
            low_price = history['Low'].iloc[-1]
            volume = history['Volume'].iloc[-1]
            
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            results.append({
                'ticker': ticker,
                'hebrew_name': hebrew_name,
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'high_price': high_price,
                'low_price': low_price,
                'volume': volume
            })
        except Exception as e:
            print(f"⚠️ שגיאה בשליפת נתונים עבור {ticker}: {e}")
            continue

    if not results:
        print("❌ לא נמצאו נתונים לשליחה.")
        return

    # מיון מהיורדות ביותר (שליליות) ועד לעולות ביותר (חיוביות)
    results.sort(key=lambda x: x['change_percent'])
    print("✅ איסוף ומיון המניות הושלם. שולח לטלגרם...")

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
                f"📦 נפח: {int(item['volume']):,}\n"
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
        print(f"🚀 הסיכום נשלח בהצלחה! התהליך לקח {elapsed_time:.2f} שניות.")
    except Exception as e:
        print(f"❌ שגיאה בשליחת ההודעות לטלגרם: {e}")

# תזמון יומי אוטומטי לשעה 23:00
schedule.every().day.at("23:00", "Asia/Jerusalem").do(send_daily_summary)

if __name__ == '__main__':
    print("🤖 מריץ את הבדיקה הראשונית מיד...")
    
    # הפעלה ידנית מיד כשמריצים את הקובץ
    send_daily_summary()
    
    print("\n⏳ מעבר למצב המתנה – הבוט ימשיך לרוץ ברקע וישלח אוטומטית כל יום בשעה 23:00.")
    while True:
        schedule.run_pending()
        time.sleep(1)

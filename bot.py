import os
import time
import telebot
import yfinance as yf
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)

# רשימת המניות והנכסים המלאה שלך
TICKERS = {
    "AAPL": ("אפל", "Apple Inc."),
    "TSLA": ("טסלה", "Tesla Inc."),
    "MSFT": ("מיקרוסופט", "Microsoft Corporation"),
    "NVDA": ("אנבידיה", "NVIDIA Corporation"),
    "PLTR": ("פלנטיר טכנולוגיות", "Palantir Technologies Inc."),
    "INTC": ("אינטל", "Intel Corporation"),
    "PYPL": ("פייפאל", "PayPal Holdings Inc."),
    "GOOGL": ("אלפאבית / גוגל", "Alphabet Inc. (Google)"),
    "AMZN": ("אמזון", "Amazon.com Inc."),
    "META": ("מטא פלטפורמס", "Meta Platforms Inc."),
    "NFLX": ("נטפליקס", "Netflix Inc."),
    "LMT": ("לוקהיד מרטין", "Lockheed Martin Corporation"),
    "BA": ("בואינג", "The Boeing Company"),
    "WMT": ("ולמארט", "Walmart Inc."),
    "MRNA": ("מודרנה", "Moderna Inc."),
    "MRK": ("מרק", "Merck & Co. Inc."),
    "MBLY": ("מובילאיי", "Mobileye Global Inc."),
    "SMCI": ("סופר מיקרו", "Super Micro Computer"),
    "CHKP": ("צ'ק פוינט", "Check Point Software"),
    "COIN": ("קוינבייס", "Coinbase Global Inc."),
    "BTC-USD": ("ביטקוין", "Bitcoin USD"),
    "^VIX": ("מדד הפחד VIX", "CBOE Volatility Index"),
    "PROK": ("פרוק", "ProK"),
    "BMR": ("ב.מ.ר", "BMR"),
    "^TA125.TA": ("מדד תל אביב 125", "TA-125 Index"),
    "AMD": ("אמדי / AMD", "Advanced Micro Devices, Inc."),
    "QCOM": ("קוואלקום", "Qualcomm Inc."),
    "DIS": ("דיסני", "The Walt Disney Company")
}

def send_daily_summary():
    if not CHAT_ID:
        print("שגיאה: CHAT_ID לא מוגדר")
        return

    print("מתחיל לאסוף נתונים לסיכום המניות...")
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
            print(f"שגיאה בשליפת נתונים עבור {ticker}: {e}")
            continue

    if not results:
        print("לא נמצאו נתונים לשליחה.")
        return

    # מיון התוצאות מהעולה ביותר ליורדת ביותר (לפי אחוז שינוי)
    results.sort(key=lambda x: x['change_percent'], reverse=True)

    mid_index = len(results) // 2
    part1 = results[:mid_index]
    part2 = results[mid_index:]

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
                f"〰️〰️〰️〰️〰️〰️"
            )
            lines.append(line)
        return "\n".join(lines)

    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    message1 = f"📊 <b>סיכום סוף מסחר חלק א':</b>\n\n" + format_block(part1)
    message2 = f"📊 <b>סיכום מניות חלק ב':</b>\n\n" + format_block(part2) + f"\n\n📅 {current_date}"

    try:
        bot.send_message(CHAT_ID, message1, parse_mode="HTML")
        bot.send_message(CHAT_ID, message2, parse_mode="HTML")
        print(f"הסיכום נשלח בהצלחה תוך {time.time() - start_time:.2f} שניות!")
    except Exception as e:
        print(f"שגיאה בשליחת ההודעות לטלגרם: {e}")

if __name__ == '__main__':
    send_daily_summary()

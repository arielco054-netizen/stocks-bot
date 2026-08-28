import os
import telebot
import yfinance as yf
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)

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
    "^TA125.TA": ("מדד תל אביב 125", "TA-125 Index")
}

def generate_market_report():
    items = []
    
    for ticker, (hebrew_name, eng_name) in TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="2d")
            
            if len(history) < 2:
                continue
                
            prev_close = history['Close'].iloc[-2]
            current_price = history['Close'].iloc[-1]
            high_price = history['High'].iloc[-1]
            low_price = history['Low'].iloc[-1]
            volume = int(history['Volume'].iloc[-1]) if 'Volume' in history and not history['Volume'].empty else 0
            
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            is_positive = change >= 0
            emoji_status = "🟢" if is_positive else "🔴"
            sign = "+" if is_positive else ""
            
            price_suffix = "$" if "BTC" not in ticker and "TA125" not in ticker else (" USD" if "BTC" in ticker else " נקודות")
            
            line = (
                f"📊 {emoji_status} {hebrew_name} | {eng_name}\n"
                f"💵 מחיר: {current_price:,.2f}{price_suffix}\n"
                f"📊 שינוי: {sign}{change_percent:.2f}% ({sign}{change:,.2f})\n"
                f"🔼 גבוה: {high_price:,.2f} | 📉 נמוך: {low_price:,.2f}\n"
                f"📦 נפח: {volume:,}\n"
                f"〰️〰️〰️〰️〰️〰️"
            )
            items.append((change_percent, line))
        except Exception as e:
            print(f"שגיאה במניה {ticker}: {e}")
            continue
            
    # מיון מהיורד ביותר (שלילי גבוה) לעולה ביותר (חיובי גבוה)
    items.sort(key=lambda x: x[0], reverse=False)
    
    report_lines = [line for _, line in items]
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    mid = len(report_lines) // 2
    part1 = "\n".join(report_lines[:mid])
    part2 = "\n".join(report_lines[mid:]) + f"\n\n📅 {current_time}"
    
    return part1, part2

def send_daily_report():
    if not CHAT_ID:
        return
    try:
        part1, part2 = generate_market_report()
        bot.send_message(CHAT_ID, "📊 סיכום סוף מסחר חלק א':\n\n" + part1)
        import time
        time.sleep(2)
        bot.send_message(CHAT_ID, "📊 סיכום מניות חלק ב':\n\n" + part2)
    except Exception as e:
        print(f"שגיאה: {e}")

if __name__ == '__main__':
    send_daily_report()

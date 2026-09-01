import os
import telebot
import yfinance as yf
from datetime import datetime
import time
import schedule

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

def generate_market_report(is_weekly_summary=False):
    items = []
    period_str = "5d" if is_weekly_summary else "2d"
    title_note = " 📊 (סיכום שבועי: מיום שני ועד מוצאי שבת)" if is_weekly_summary else ""
    
    for ticker, (hebrew_name, eng_name) in TICKERS.items():
        current_price = 0.0
        high_price = 0.0
        low_price = 0.0
        volume = 0
        change = 0.0
        change_percent = 0.0
        
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period_str)
            
            if len(history) >= 1:
                current_price = history['Close'].iloc[-1]
                
                if is_weekly_summary:
                    start_price = history['Close'].iloc[0]
                else:
                    start_price = history['Close'].iloc[-2] if len(history) >= 2 else current_price
                
                high_price = history['High'].max() if is_weekly_summary else history['High'].iloc[-1]
                low_price = history['Low'].min() if is_weekly_summary else history['Low'].iloc[-1]
                volume = int(history['Volume'].sum()) if is_weekly_summary else int(history['Volume'].iloc[-1])
                
                change = current_price - start_price
                change_percent = (change / start_price) * 100 if start_price > 0 else 0.0
            else:
                raise Exception("אין נתונים מספיקים")
                
        except Exception as e:
            print(f"שגיאה במניה {ticker}: {e}")
            current_price = 1.00
            high_price = 1.00
            low_price = 1.00
            volume = 0
            change = 0.0
            change_percent = 0.0
            
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
            
    items.sort(key=lambda x: x[0], reverse=False)
    
    report_lines = [line for _, line in items]
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    split_index = 12
    
    header_part1 = "📊 סיכום שבועי (מוצאי שבת) חלק א':\n\n" if is_weekly_summary else "📊 סיכום סוף מסחר יומי חלק א':\n\n"
    footer_part2 = "📊 סיכום שבועי חלק ב':\n\n" if is_weekly_summary else "📊 סיכום מניות חלק ב':\n\n"
    
    part1 = header_part1 + "\n".join(report_lines[:split_index])
    part2 = footer_part2 + "\n".join(report_lines[split_index:]) + f"\n\n📅 {current_time}{title_note}"
    
    return part1, part2

def job_daily():
    if not CHAT_ID:
        return
    try:
        print("מריץ סיכום יומי...")
        part1, part2 = generate_market_report(is_weekly_summary=False)
        bot.send_message(CHAT_ID, part1)
        time.sleep(2)
        bot.send_message(CHAT_ID, part2)
    except Exception as e:
        print(f"שגיאה בשליחה היומית: {e}")

def job_weekly_saturday():
    if not CHAT_ID:
        return
    try:
        print("מריץ סיכום שבועי של מוצאי שבת...")
        part1, part2 = generate_market_report(is_weekly_summary=True)
        bot.send_message(CHAT_ID, part1)
        time.sleep(2)
        bot.send_message(CHAT_ID, part2)
    except Exception as e:
        print(f"שגיאה בשליחה השבועית: {e}")

# תזמון מדויק לפי שעון המערכת
schedule.every().day.at("23:00").do(job_daily)
schedule.every().saturday.at("21:00").do(job_weekly_saturday)

if __name__ == '__main__':
    print("הבוט מהיר רץ וממתין לתזמונים...")
    
    # אם תרצה לבדוק שליחה מידית עכשיו, הסר את הסולם (#) מהשורה הבאה:
    # job_daily() 
    
    while True:
        schedule.run_pending()
        time.sleep(60)

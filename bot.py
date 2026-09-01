import os
import telebot
import yfinance as yf
from datetime import datetime
import time

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
            
            # שליפת נתוני מחיר מהירים ומדויקים יותר ישירות מהשוק
            try:
                fast_info = stock.fast_info
                live_price = fast_info.get('lastPrice')
                previous_close = fast_info.get('previousClose')
            except:
                live_price = None
                previous_close = None

            history = stock.history(period=period_str)
            
            if len(history) >= 2:
                start_price = history['Close'].iloc[0] if is_weekly_summary else history['Close'].iloc[-2]
                if previous_close and not is_weekly_summary:
                    start_price = previous_close
                    
                current_price = live_price if live_price else history['Close'].iloc[-1]
                high_price = history['High'].max() if is_weekly_summary else history['High'].iloc[-1]
                low_price = history['Low'].min() if is_weekly_summary else history['Low'].iloc[-1]
                volume = int(history['Volume'].sum()) if is_weekly_summary else int(history['Volume'].iloc[-1])
                
                change = current_price - start_price
                change_percent = (change / start_price) * 100
            else:
                raise Exception("אין מספיק נתונים בהיסטוריה")
                
        except Exception as e:
            print(f"שגיאה בשליפת נתונים עבור {ticker}: {e}")
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

def send_daily_report():
    if not CHAT_ID:
        return
    try:
        today_weekday = datetime.now().weekday()
        is_sat = (today_weekday == 5)
        
        part1, part2 = generate_market_report(is_weekly_summary=is_sat)
        
        bot.send_message(CHAT_ID, part1)
        time.sleep(2)
        bot.send_message(CHAT_ID, part2)
    except Exception as e:
        print(f"שגיאה בשליחה: {e}")

if __name__ == '__main__':
    send_daily_report()

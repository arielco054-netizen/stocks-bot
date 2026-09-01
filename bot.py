import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import telebot
import yfinance as yf
import pytz

# =========================
# הגדרות
# =========================

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN או CHAT_ID אינם מוגדרים ב-Environment Variables")

bot = telebot.TeleBot(TOKEN)
ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

# =========================
# רשימת הנכסים - 25 בדיוק
# =========================

TICKERS = [
    ("MRNA", "מודרנה", "Moderna Inc."),
    ("^VIX", "מדד הפחד VIX", "CBOE Volatility Index"),
    ("MRK", "מרק", "Merck & Co. Inc."),
    ("NFLX", "נטפליקס", "Netflix Inc."),
    ("WMT", "ולמארט", "Walmart Inc."),
    ("AMZN", "אמזון", "Amazon.com Inc."),
    ("BA", "בואינג", "The Boeing Company"),
    ("META", "מטא פלטפורמס", "Meta Platforms Inc."),
    ("PYPL", "פייפאל", "PayPal Holdings Inc."),
    ("GOOGL", "אלפאבית / גוגל", "Alphabet Inc."),
    ("LMT", "לוקהיד מרטין", "Lockheed Martin Corporation"),
    ("AAPL", "אפל", "Apple Inc."),
    ("MBLY", "מובילאיי", "Mobileye Global Inc."),
    ("BTC-USD", "ביטקוין", "Bitcoin USD"),
    ("^TA125.TA", "מדד תל אביב 125", "TA-125 Index"),
    ("MSFT", "מיקרוסופט", "Microsoft Corporation"),
    ("BMR", "ב.מ.ר", "BMR"),
    ("TSLA", "טסלה", "Tesla Inc."),
    ("SMCI", "סופר מיקרו", "Super Micro Computer"),
    ("CHKP", "צ'ק פוינט", "Check Point Software"),
    ("INTC", "אינטל", "Intel Corporation"),
    ("PRK", "פרוק", "ProK"),
    ("PLTR", "פלנטיר טכנולוגיות", "Palantir Technologies Inc."),
    ("COIN", "קוינבייס", "Coinbase Global Inc."),
    ("NVDA", "אנבידיה", "NVIDIA Corporation"),
]

# =========================
# שליפת נתונים
# =========================

def fetch_ticker_data(item, is_saturday):
    ticker, hebrew_name, english_name = item

    try:
        yf_ticker = yf.Ticker(ticker)

        # לוקחים מספיק ימים כדי להתמודד גם עם חגים
        # וסופי שבוע בלי להסתמך על מיקום קבוע כמו iloc[-5]
        history = yf_ticker.history(
            period="10d",
            interval="1d",
            auto_adjust=False,
            timeout=10
        )

        if history is None or history.empty:
            raise ValueError("לא נמצאו נתונים")

        # הסרת שורות ללא מחיר
        history = history.dropna(subset=["Close"])

        if len(history) < 2:
            raise ValueError("אין מספיק נתוני מסחר")

        # =========================
        # מחיר נוכחי / סגירה אחרונה
        # =========================

        current_row = history.iloc[-1]

        current_price = float(current_row["Close"])
        high_price = float(current_row["High"])
        low_price = float(current_row["Low"])
        volume = int(current_row["Volume"]) if current_row["Volume"] == current_row["Volume"] else 0

        # =========================
        # שינוי יומי / שבועי
        # =========================

        if is_saturday:
            # בשבת מציגים שינוי מצטבר מתחילת שבוע המסחר
            current_date = history.index[-1].date()

            week_data = history[history.index.dayofweek < 5]

            if len(week_data) >= 2:
                first_week_close = float(week_data.iloc[0]["Close"])
                prev_close = first_week_close
            else:
                prev_close = float(history.iloc[-2]["Close"])

        else:
            # שינוי יומי אמיתי:
            # סגירה אחרונה מול סגירת יום המסחר הקודם
            prev_close = float(history.iloc[-2]["Close"])

        if prev_close == 0:
            raise ValueError("מחיר קודם הוא 0")

        change = current_price - prev_close
        change_percent = (change / prev_close) * 100

        return {
            "ticker": ticker,
            "hebrew_name": hebrew_name,
            "english_name": english_name,
            "current_price": current_price,
            "change": change,
            "change_percent": change_percent,
            "high_price": high_price,
            "low_price": low_price,
            "volume": volume,
            "success": True,
        }

    except Exception as e:
        print(f"❌ {ticker}: {e}")

        # חשוב:
        # הנכס נשאר בדוח גם אם Yahoo לא החזיר נתונים
        return {
            "ticker": ticker,
            "hebrew_name": hebrew_name,
            "english_name": english_name,
            "current_price": 0.0,
            "change": 0.0,
            "change_percent": 0.0,
            "high_price": 0.0,
            "low_price": 0.0,
            "volume": 0,
            "success": False,
        }


# =========================
# פורמט מספרים
# =========================

def format_price(item):
    ticker = item["ticker"]

    if ticker == "BTC-USD":
        return f"{item['current_price']:,.2f} USD"

    if ticker == "^TA125.TA":
        return f"{item['current_price']:,.2f} נקודות"

    return f"${item['current_price']:,.2f}"


def format_change(item):
    change_percent = item["change_percent"]
    change = item["change"]

    sign_percent = "+" if change_percent > 0 else ""
    sign_change = "+" if change > 0 else ""

    return (
        f"{sign_percent}{change_percent:.2f}% "
        f"({sign_change}{change:,.2f})"
    )


# =========================
# יצירת בלוק
# =========================

def format_block(items, start_index):
    lines = []

    for index, item in enumerate(items, start=start_index):

        if not item["success"]:
            emoji = "⚪"
            status = "⚠️ אין נתונים"
        elif item["change_percent"] > 0:
            emoji = "🟢"
            status = ""
        elif item["change_percent"] < 0:
            emoji = "🔴"
            status = ""
        else:
            emoji = "⚪"
            status = ""

        block = (
            f"<b>{index}.</b> 📊 {emoji} "
            f"{item['hebrew_name']} | {item['english_name']}\n"
            f"💵 מחיר: {format_price(item)}\n"
            f"📊 שינוי: {format_change(item)}\n"
            f"🔼 גבוה: {item['high_price']:,.2f} | "
            f"📉 נמוך: {item['low_price']:,.2f}\n"
            f"📦 נפח: {item['volume']:,}\n"
            f"{status}\n"
            f"〰️〰️〰️〰️〰️〰️"
        )

        lines.append(block)

    return "\n".join(lines)


# =========================
# MAIN
# =========================

def main():

    start_time = time.time()

    now_israel = datetime.now(ISRAEL_TZ)
    is_saturday = now_israel.weekday() == 5

    if is_saturday:
        report_title = "📊 סיכום שבועי מצטבר"
    else:
        report_title = "📊 סיכום סוף מסחר יומי"

    print(f"⏳ מתחיל איסוף נתונים: {report_title}")

    results_by_ticker = {}

    # מקביליות - מהיר יותר
    with ThreadPoolExecutor(max_workers=10) as executor:

        future_map = {
            executor.submit(
                fetch_ticker_data,
                item,
                is_saturday
            ): item[0]
            for item in TICKERS
        }

        for future in as_completed(future_map):

            ticker = future_map[future]

            try:
                result = future.result()
                results_by_ticker[ticker] = result

            except Exception as e:
                print(f"❌ שגיאה ב-{ticker}: {e}")

    # =========================
    # שומר על הסדר המקורי
    # =========================

    results = []

    for item in TICKERS:

        ticker = item[0]

        if ticker in results_by_ticker:
            results.append(results_by_ticker[ticker])
        else:
            results.append({
                "ticker": ticker,
                "hebrew_name": item[1],
                "english_name": item[2],
                "current_price": 0.0,
                "change": 0.0,
                "change_percent": 0.0,
                "high_price": 0.0,
                "low_price": 0.0,
                "volume": 0,
                "success": False,
            })

    # =========================
    # חלוקה ל-2 הודעות
    # 25 נכסים:
    # חלק א' = 13
    # חלק ב' = 12
    # =========================

    part1 = results[:13]
    part2 = results[13:]

    current_date = now_israel.strftime("%d/%m/%Y %H:%M")

    message1 = (
        f"{report_title} | חלק א'\n"
        f"🕐 עדכון: {current_date}\n"
        f"📦 סה״כ נכסים: {len(results)}\n\n"
        f"{format_block(part1, 1)}"
    )

    message2 = (
        f"{report_title} | חלק ב'\n"
        f"🕐 עדכון: {current_date}\n"
        f"📦 סה״כ נכסים: {len(results)}\n\n"
        f"{format_block(part2, 14)}"
    )

    # =========================
    # שליחה לטלגרם
    # =========================

    try:

        bot.send_message(
            CHAT_ID,
            message1,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        bot.send_message(
            CHAT_ID,
            message2,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        elapsed = time.time() - start_time

        successful = sum(
            1 for item in results
            if item["success"]
        )

        failed = len(results) - successful

        print(
            f"✅ נשלח בהצלחה | "
            f"{successful}/{len(results)} נכסים תקינים | "
            f"{failed} ללא נתונים | "
            f"{elapsed:.2f} שניות"
        )

    except Exception as e:
        print(f"❌ שגיאה בשליחה לטלגרם: {e}")


if __name__ == "__main__":
    main()

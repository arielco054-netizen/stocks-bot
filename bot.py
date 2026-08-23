import os
import requests
import yfinance as yf

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

TICKERS = [
    "AAPL",
    "TSLA",
    "MSFT",
    "TEVA.TA",
    "NVDA",
    "PLTR",
    "INTC",
    "PYPL",
    "BTC-USD",
    "GOOGL",
    "PROK",
    "VOO",
    "BMR",
]


def get_stock_data():
  message = "🔔 סיכום יום מסחר (זמן אמת)\n\n"

  for ticker in TICKERS:
    try:
      stock = yf.Ticker(ticker)
      todays_data = stock.history(period="2d")

      if todays_data.empty:
        continue

      close_price = todays_data["Close"].iloc[-1]
      open_price = (
          todays_data["Open"].iloc[-1]
          if "Open" in todays_data
          else close_price
      )
      high_price = todays_data["High"].max()
      low_price = todays_data["Low"].min()
      volume = (
          int(todays_data["Volume"].iloc[-1])
          if "Volume" in todays_data
          else 0
      )

      if open_price > 0:
        change = ((close_price - open_price) / open_price) * 100
      else:
        change = 0.0

      emoji_trend = "🟢" if change >= 0 else "🔴"
      sign = "+" if change >= 0 else ""
      display_name = ticker.replace("-USD", "")

      message += f"*{display_name}*: {close_price:,.2f} {emoji_trend} {sign}{change:.2f}%\n"
      message += (
          f"📈 גבוה: {high_price:,.2f} | 📉 נמוך: {low_price:,.2f}\n"
      )
      message += f"📊 נפח: {volume:,}\n\n"
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
  send_telegram_message(stock_report)

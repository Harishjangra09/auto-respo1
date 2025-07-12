import requests
import schedule
import time
import threading
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes





# === CONFIG ===
TELEGRAM_TOKEN = '7741029568:AAGhAm5FEYTcVzZuPPMrOa5P9W2_-bFQq50'
CHAT_ID = '897358644'
FMP_API_KEY = 'yiI7Qxz3WZMDirK1LnxbiEbMClOphxh6'
NEWSAPI_KEY = 'fbe66da57eef4b0993a13c3572457d06'

bot = Bot(token=TELEGRAM_TOKEN)

# === US FINANCIAL NEWS ===
def get_financial_news():
    url = f"https://financialmodelingprep.com/api/v3/stock_news?limit=5&apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if not data:
        return "❌ No US financial news."

    message = "📰 *Top US Market News:*\n"
    for article in data:
        title = article.get('title')
        site = article.get('site')
        url = article.get('url')
        message += f"🔹 [{title}]({url}) - _{site}_\n"
    return message

# === INDIAN COMPANY NEWS ===
def get_indian_company_news():
    query = "Reliance OR TCS OR Infosys OR HDFC OR SBI OR Adani OR Wipro OR LIC OR Paytm OR Zomato"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&pageSize=5&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json().get("articles", [])

    if not data:
        return "❌ No Indian company news."

    message = "🇮🇳 *Indian Company News:*\n"
    for article in data:
        title = article.get("title")
        source = article.get("source", {}).get("name")
        url = article.get("url")
        message += f"🔸 [{title}]({url}) - _{source}_\n"
    return message

# === EARNINGS REPORT ===
def get_earnings():
    url = f"https://financialmodelingprep.com/api/v3/earning_calendar?apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()[:5]

    if not data:
        return "❌ No earnings today."

    message = "📈 *Earnings Report Today:*\n"
    for report in data:
        symbol = report.get('symbol')
        eps = report.get('eps')
        rev = report.get('revenue')
        date = report.get('date')
        message += f"🔹 `{symbol}` | EPS: `{eps}` | Revenue: `{rev}` | Date: {date}\n"
    return message

# === ECONOMIC EVENTS ===
def get_economic_events():
    url = f"https://financialmodelingprep.com/api/v3/economic_calendar?apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()[:5]

    if not data:
        return "❌ No economic events today."

    message = "📅 *Key Economic Events Today:*\n"
    for event in data:
        country = event.get('country')
        event_name = event.get('event')
        date = event.get('date')
        time_event = event.get('time')
        message += f"🔸 {country} | {event_name} | {time_event} ({date})\n"
    return message

# === COMBINED DAILY UPDATE ===
def send_daily_update():
    us_news = get_financial_news()
    india_news = get_indian_company_news()
    earnings = get_earnings()
    events = get_economic_events()

    final_message = f"{us_news}\n\n{india_news}\n\n{earnings}\n\n{events}"
    bot.send_message(chat_id=CHAT_ID, text=final_message, parse_mode="Markdown", disable_web_page_preview=True)

# === TELEGRAM BOT COMMANDS ===
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 I will send you daily finance + economic updates for US and Indian markets.")

async def manual_update(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📡 Fetching latest news...")
    send_daily_update()

# === DAILY SCHEDULER THREAD ===
def run_schedule():
    schedule.every().day.at("08:30").do(send_daily_update)
    while True:
        schedule.run_pending()
        time.sleep(60)

# === MAIN FUNCTION ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update", manual_update))

    # Background thread for daily scheduler
    threading.Thread(target=run_schedule, daemon=True).start()

    app.run_polling()

# === RUN ===
if __name__ == "__main__":
    main()

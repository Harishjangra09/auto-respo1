import requests
import schedule
import time
import threading
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === MAIN BOT CONFIG ===
TELEGRAM_TOKEN = '7741029568:AAGhAm5FEYTcVzZuPPMrOa5P9W2_-bFQq50'  # main bot
CHAT_ID = '897358644'
FMP_API_KEY = 'yiI7Qxz3WZMDirK1LnxbiEbMClOphxh6'
NEWSAPI_KEY = 'fbe66da57eef4b0993a13c3572457d06'

# === NOTIFY BOT CONFIG ===
SECOND_BOT_TOKEN = '7635757636:AAFwFOjtKWF3XFZ0VYOEs8ICMnbVhLHWf_8'  # the other bot that gets notified
NOTIFY_CHAT_ID = '897358644'  # receiver chat (group/user where second bot is added)

# === Initialize bots ===
main_bot = Bot(token=TELEGRAM_TOKEN)
notify_bot = Bot(token=SECOND_BOT_TOKEN)

# === US TOP 50 STOCKS ===
us_top_50 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "JNJ",
    "XOM", "V", "PG", "MA", "AVGO", "LLY", "HD", "MRK", "PEP", "KO",
    "ABBV", "COST", "ADBE", "WMT", "CRM", "CVX", "ACN", "TMO", "INTC", "MCD",
    "LIN", "DHR", "WFC", "ABT", "TXN", "PM", "AMGN", "MS", "HON", "QCOM",
    "UNP", "NEE", "ORCL", "LOW", "BMY", "UPS", "RTX", "IBM", "SBUX", "NFLX"
]

# === NIFTY 50 COMPANIES ===
nifty_50_query = (
    "Reliance OR TCS OR Infosys OR HDFC OR ICICI OR Kotak OR Axis OR SBI OR Wipro OR ITC OR "
    "Adani OR HCL OR Bharti OR Ultratech OR L&T OR Nestle OR Asian Paints OR Power Grid OR "
    "NTPC OR Coal India OR Bajaj Finance OR Bajaj Finserv OR HDFC Bank OR Cipla OR Sun Pharma OR "
    "ONGC OR Tata Motors OR Hero MotoCorp OR Tata Consumer OR Apollo Hospitals OR Divis Labs OR "
    "Hindalco OR Tata Steel OR JSW Steel OR Britannia OR Dr Reddy OR BPCL OR Grasim OR Tech Mahindra OR "
    "Eicher OR Maruti OR IndusInd OR Hindustan Unilever OR UPL OR SBI Life OR Bajaj Auto OR M&M OR "
    "Shriram Finance OR LTIMindtree"
)

# === GET US STOCK NEWS ===
def get_financial_news():
    messages = ["📰 *Top US Company News (Top 50):*"]
    for symbol in us_top_50[:10]:  # limit to avoid FMP API abuse
        url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={symbol}&limit=1&apikey={FMP_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if not data:
            continue

        article = data[0]
        title = article.get('title')
        site = article.get('site')
        news_url = article.get('url')
        messages.append(f"🔹 [{symbol}] [{title}]({news_url}) - _{site}_")

    return "\n".join(messages) if len(messages) > 1 else "❌ No US stock news found."

# === GET INDIA NEWS ===
def get_indian_company_news():
    url = f"https://newsapi.org/v2/everything?q={nifty_50_query}&language=en&pageSize=5&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json().get("articles", [])

    if not data:
        return "❌ No Indian company news."

    message = "🇮🇳 *Indian Company News (Nifty 50):*\n"
    for article in data:
        title = article.get("title")
        source = article.get("source", {}).get("name")
        url = article.get("url")
        message += f"🔸 [{title}]({url}) - _{source}_\n"
    return message

# === GET EARNINGS ===
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

# === GET ECONOMIC EVENTS ===
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

# === SEND COMBINED UPDATE ===
def send_daily_update(chat_id):
    try:
        us_news = get_financial_news()
        india_news = get_indian_company_news()
        earnings = get_earnings()
        events = get_economic_events()

        final_message = f"{us_news}\n\n{india_news}\n\n{earnings}\n\n{events}"
        main_bot.send_message(chat_id=chat_id, text=final_message, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print("Update error:", e)

# === /start COMMAND ===
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"NoUsername ({user.first_name})"

    # Send welcome to the user
    await update.message.reply_text("✅ You are now subscribed to daily finance updates!")

    # Send user info to your (admin) chat via notify bot
    try:
        notify_msg = (
            f"📢 New user started bot:\n"
            f"👤 Name: {user.first_name} {user.last_name or ''}\n"
            f"🔹 Username: @{username}\n"
            f"🆔 User ID: `{user_id}`"
        )
        # Send it using second bot to your own chat
        notify_bot.send_message(chat_id=NOTIFY_CHAT_ID, text=notify_msg, parse_mode="Markdown")
    except Exception as e:
        print("Error notifying admin:", e)


# === /update COMMAND ===
async def manual_update(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    await update.message.reply_text("📡 Sending latest updates...")

    send_daily_update(chat_id=user_id)

    # Notify second bot
    try:
        notify_msg = f"📢 Update triggered by `{username}` (ID: `{user_id}`)"
        notify_bot.send_message(chat_id=NOTIFY_CHAT_ID, text=notify_msg, parse_mode="Markdown")
    except Exception as e:
        print("Notify failed:", e)

# === SCHEDULED AUTOMATED PUSH (FOR YOURSELF OR FIXED USERS) ===
def run_schedule():
    def job():
        # you can loop through a list of user IDs here
        send_daily_update(chat_id='YOUR_CHAT_ID')  # e.g., your fixed user ID
    schedule.every().day.at("08:30").do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)

# === MAIN ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update", manual_update))

    threading.Thread(target=run_schedule, daemon=True).start()
    app.run_polling()

if __name__ == "__main__":
    main()

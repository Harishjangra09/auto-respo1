import os
import requests
import schedule
import time
import threading
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === TRACK SENT ARTICLES ===
sent_news_urls = set()

# === MAIN BOT CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# === NOTIFY BOT CONFIG ===
SECOND_BOT_TOKEN = os.getenv("SECOND_BOT_TOKEN")
NOTIFY_CHAT_ID = os.getenv("NOTIFY_CHAT_ID")

# === Initialize bots ===
main_bot = Bot(token=TELEGRAM_TOKEN)
notify_bot = Bot(token=SECOND_BOT_TOKEN)

# === US + INDIA QUERY ===
us_query = "Apple OR Microsoft OR Google OR Amazon OR Nvidia OR Meta OR Tesla OR Berkshire OR JPMorgan OR Visa"
nifty_50_query = (
    "Reliance OR TCS OR Infosys OR HDFC OR ICICI OR Kotak OR Axis OR SBI OR Wipro OR ITC OR "
    "Adani OR HCL OR Bharti OR Ultratech OR L&T OR Nestle OR Asian Paints OR Power Grid OR "
    "NTPC OR Coal India OR Bajaj Finance OR Bajaj Finserv OR HDFC Bank OR Cipla OR Sun Pharma OR "
    "ONGC OR Tata Motors OR Hero MotoCorp OR Tata Consumer OR Apollo Hospitals OR Divis Labs OR "
    "Hindalco OR Tata Steel OR JSW Steel OR Britannia OR Dr Reddy OR BPCL OR Grasim OR Tech Mahindra OR "
    "Eicher OR Maruti OR IndusInd OR Hindustan Unilever OR UPL OR SBI Life OR Bajaj Auto OR M&M OR "
    "Shriram Finance OR LTIMindtree"
)

# === GET US COMPANY NEWS ===
def get_financial_news():
    url = f"https://newsapi.org/v2/everything?q={us_query}&language=en&pageSize=5&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json().get("articles", [])
    if not data:
        return None

    message = "🇺🇸 *Top US Company News:*\n"
    new_found = False

    for article in data:
        url = article.get("url")
        if url in sent_news_urls:
            continue
        title = article.get("title")
        source = article.get("source", {}).get("name")
        message += f"🔹 [{title}]({url}) - _{source}_\n"
        sent_news_urls.add(url)
        new_found = True

    return message if new_found else None

# === GET INDIAN COMPANY NEWS ===
def get_indian_company_news():
    url = f"https://newsapi.org/v2/everything?q={nifty_50_query}&language=en&pageSize=5&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json().get("articles", [])
    if not data:
        return None

    message = "🇮🇳 *Top Indian Company News:*\n"
    new_found = False

    for article in data:
        url = article.get("url")
        if url in sent_news_urls:
            continue
        title = article.get("title")
        source = article.get("source", {}).get("name")
        message += f"🔸 [{title}]({url}) - _{source}_\n"
        sent_news_urls.add(url)
        new_found = True

    return message if new_found else None

# === COMBINE AND SEND ===
def send_daily_update(chat_id):
    try:
        news = get_all_financial_news()
        print("✅ Sending update...")
        print("News:", news)

        if news:
            main_bot.send_message(chat_id=chat_id, text=news, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            print("No new news to send.")
    except Exception as e:
        print("Update error:", e)


# get all finance news
def get_all_financial_news():
    query = (
        "finance OR stock market OR inflation OR interest rates OR "
        "bonds OR central bank OR RBI OR Fed OR crypto OR bitcoin OR ethereum OR "
        "tariffs OR monetary policy OR fiscal policy OR economy OR GDP OR recession"
    )
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&pageSize=10&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json().get("articles", [])

    if not data:
        return None

    message = "📰 *Latest Financial News (Live):*\n"
    new_found = False

    for article in data:
        url = article.get("url")
        if url in sent_news_urls:
            continue
        title = article.get("title")
        source = article.get("source", {}).get("name")
        message += f"🔹 [{title}]({url}) - _{source}_\n"
        sent_news_urls.add(url)
        new_found = True

    return message if new_found else None



# === /start COMMAND ===
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else user.first_name

    await update.message.reply_text("✅ You are now subscribed to daily finance updates!")
    await update.message.reply_text("📡 Sending today's financial update...")
    send_daily_update(chat_id=user_id)

    try:
        notify_bot.send_message(
            chat_id=NOTIFY_CHAT_ID,
            text=f"📢 New user started the bot:\n👤 Name: {full_name}\n🔹 Username: {username}\n🆔 User ID: `{user_id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Error notifying admin:", e)

# === /update COMMAND ===
async def manual_update(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    await update.message.reply_text("📡 Sending latest updates...")
    send_daily_update(chat_id=user_id)

    try:
        notify_bot.send_message(
            chat_id=NOTIFY_CHAT_ID,
            text=f"📢 Update triggered by `{username}` (ID: `{user_id}`)",
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Notify failed:", e)

# === SCHEDULED PUSH ===
def run_schedule():
    def job():
        # Replace with your target Telegram Chat ID(s)
        for chat_id in ['897358644']:
            send_daily_update(chat_id=chat_id)

    schedule.every(5).minutes.do(job)  # ✅ Run every 5 minutes

    while True:
        schedule.run_pending()
        time.sleep(60)


# === MAIN ENTRY ===
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update", manual_update))

    threading.Thread(target=run_schedule, daemon=True).start()
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import requests
import schedule
import time
import threading
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from collections import deque



# === BOT CONFIG ===
TELEGRAM_TOKEN = '7741029568:AAGhAm5FEYTcVzZuPPMrOa5P9W2_-bFQq50'
NEWSAPI_KEY = 'fbe66da57eef4b0993a13c3572457d06'
SECOND_BOT_TOKEN = '7635757636:AAFwFOjtKWF3XFZ0VYOEs8ICMnbVhLHWf_8'
NOTIFY_CHAT_ID = '897358644'

# === Initialize bots ===
main_bot = Bot(token=TELEGRAM_TOKEN)
notify_bot = Bot(token=SECOND_BOT_TOKEN)

# === URL MEMORY ===
sent_news_deque = deque(maxlen=500)
sent_news_urls = set()

def remember_url(url):
    if url not in sent_news_urls:
        sent_news_urls.add(url)
        sent_news_deque.append(url)
        if len(sent_news_deque) == sent_news_deque.maxlen:
            oldest = sent_news_deque[0]
            sent_news_urls.discard(oldest)

# === NEWS QUERIES ===
us_query = "Apple OR Microsoft OR Google OR Amazon OR Nvidia OR Meta OR Tesla OR Berkshire OR JPMorgan OR Visa"
nifty_query = (
    "Reliance OR TCS OR Infosys OR HDFC OR ICICI OR Kotak OR Axis OR SBI OR Wipro OR ITC OR "
    "Adani OR HCL OR Bharti OR Ultratech OR L&T OR Nestle OR Asian Paints OR Power Grid OR "
    "NTPC OR Coal India OR Bajaj Finance OR Bajaj Finserv OR HDFC Bank OR Cipla OR Sun Pharma OR "
    "ONGC OR Tata Motors OR Hero MotoCorp OR Tata Consumer OR Apollo Hospitals OR Divis Labs OR "
    "Hindalco OR Tata Steel OR JSW Steel OR Britannia OR Dr Reddy OR BPCL OR Grasim OR Tech Mahindra OR "
    "Eicher OR Maruti OR IndusInd OR Hindustan Unilever OR UPL OR SBI Life OR Bajaj Auto OR M&M OR "
    "Shriram Finance OR LTIMindtree"
)

# === GET ALL FINANCE NEWS ===
def get_all_financial_news():
    query = (
        "finance OR stock market OR inflation OR interest rates OR "
        "bonds OR central bank OR RBI OR Fed OR crypto OR bitcoin OR ethereum OR "
        "tariffs OR monetary policy OR fiscal policy OR economy OR GDP OR recession"
    )
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&pageSize=5&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    articles = response.json().get("articles", [])

    if not articles:
        return None

    message = "📰 *Latest Financial News (Live):*\n\n"
    new_found = False

    for a in articles:
        url = a.get("url")
        if url in sent_news_urls:
            continue

        title = a.get("title")
        description = a.get("description") or ""
        content = a.get("content") or ""
        source = a.get("source", {}).get("name")
        published = a.get("publishedAt", "")[:10]  # YYYY-MM-DD

        message += (
            f"📌 *{title}*\n"
            f"📰 _{source}_ | 🗓️ {published}\n\n"
            f"{description}\n\n"
            f"📖 _{content}_\n"
            f"🔗 [Read more]({url})\n"
            f"━━━━━━━━━━━━━━━\n"
        )

        sent_news_urls.append(url)
        new_found = True

    return message if new_found else None


# === SEND UPDATE ===
async def send_daily_update(chat_id):
    try:
        news = get_all_financial_news()
        print("✅ Sending update...")
        print("News:", news)

        if news:
            await main_bot.send_message(
                chat_id=chat_id,
                text=news,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            print("No new news to send.")
    except Exception as e:
        print("Update error:", e)

# === /start COMMAND ===
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else user.first_name

    subscribed_users.add(user_id)  # ✅ Correct placement here

    await update.message.reply_text("✅ You are now subscribed to finance updates!")
    await update.message.reply_text("📡 Sending the latest news...")
    await send_daily_update(chat_id=user_id)

    try:
        await notify_bot.send_message(
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
    await send_daily_update(chat_id=user_id)

    try:
        await notify_bot.send_message(
            chat_id=NOTIFY_CHAT_ID,
            text=f"📢 Update triggered by `{username}` (ID: `{user_id}`)",
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Notify failed:", e)

# === SCHEDULER JOB ===
def run_schedule():
    def job():
        for user_id in subscribed_users:
            send_daily_update(chat_id=user_id)

    schedule.every(5).minutes.do(job)

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

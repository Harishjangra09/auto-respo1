from telegram import Bot
from your_script import send_daily_update  # your existing file must expose this
# OR copy just the send_daily_update function if running standalone

main_bot = Bot(token='7741029568:AAGhAm5FEYTcVzZuPPMrOa5P9W2_-bFQq50')

# Replace with your chat/group ID(s)
chat_ids = ['897358644']

for chat_id in chat_ids:
    send_daily_update(chat_id=chat_id)

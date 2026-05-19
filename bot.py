import sys
import time
import re
import os
import requests
import telebot
from flask import Flask
from threading import Thread

# ==========================================
# 1. បង្កើត Web Server (Flask) សម្រាប់បំពេញលក្ខខណ្ឌ Render Web Service
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7 smoothly!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 2. កំណត់តម្លៃ Token និង URL ផ្ទាល់ៗ (ទិន្នន័យថ្មីរបស់បង)
# ==========================================
TOKEN = "8953741339:AAH0OLFVZ8ANtsdpQESTbdFM_NB5fDnw-ns"
GAS_URL = "https://script.google.com/macros/s/AKfycbxAqD_OTAhaNaS-ZDDG0FAuetqUUpHup8GQAFIQQDuyzm_FotarAWUw3XQOXGnsAl-z/exec" 

if not TOKEN or not GAS_URL:
    print("Error: Missing TOKEN or GAS_URL!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)
print("Telegram Bot is starting up...")

# ==========================================
# 3. ផ្នែកកូដដំណើរការរបស់ Telegram Bot
# ==========================================

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        text = message.text
        if text:
            print(f"Received message:\n{text}")
            
            # --- ១. យកឈ្មោះ Telegram ធ្វើជាឈ្មោះ Web និងឈ្មោះ Sheet ---
            sheet_name = message.from_user.first_name or "Telegram_User"
            
            # --- ២. ចាប់យកកាលបរិច្ឆេទ WD Date ឌីណាមិក (ទម្រង់បត់បែនខ្លាំង) ---
            date_match = re.search(r"(?:WD\s*)?Date\s*[:]\s*([^\n]+)", text, re.IGNORECASE)
            if date_match:
                wd_date = date_match.group(1).strip()
            else:
                wd_date = "N/A"
            
            print(f"Target Sheet: {sheet_name} | Extracted Date: {wd_date}")
            
            # --- ៣. កូដថ្មី៖ ចាប់យកគ្រប់ ID ទាំងអស់ (ទោះវែង ឬខ្លីកម្រិតណាក៏ចាប់អស់) ---
            # បំបែកអត្ថបទជាជួរៗ ដើម្បីពិនិត្យ និងប្រមូលយក ID ឱ្យបានច្បាស់លាស់
            lines = text.split('\n')
            ids = []
            
            for line in lines:
                clean_line = line.strip()
                # រំលងបន្ទាត់ទំនេរ ឬបន្ទាត់ដែលមានពាក្យ Date, Web, Remake
                if not clean_line:
                    continue
                if re.search(r"(?:WD\s*)?Date|Web|Remake|Late\s*wd", clean_line, re.IGNORECASE):
                    continue
                
                # ប្រសិនបើបន្ទាត់នោះមានសញ្ញា : (ដូចជា ID : xxx) ឱ្យយកតែអក្សរខាងក្រោយសញ្ញា :
                if ":" in clean_line:
                    clean_line = clean_line.split(":", 1)[1].strip()
                
                # ចាប់យកពាក្យដាច់ដោយឡែក (ID អាចជា អក្សរ លេខ ឬសញ្ញាពិសេសខ្លះៗ ប្រវែងពី ២ ដល់ ៣០ តួ)
                found_tokens = re.findall(r"([a-zA-Z0-9_\-]+)", clean_line)
                for token in found_tokens:
                    # បើមិនមែនជាពាក្យគន្លឹះប្រព័ន្ធ គឺចាត់ទុកជា ID ទាំងអស់
                    if token.lower() not in ['id', 'web', 'date', 'wd', 'remake']:
                        ids.append(token)
            
            if not ids:
                print("No IDs found in this message.")
                return

            print(f"Total IDs found: {len(ids)}")

            # បញ្ជូនទៅ Google Sheet
            data_to_send = {
                "sheet_name": sheet_name,
                "wd_date": wd_date,
                "ids": ids
            }
            
            response = requests.post(GAS_URL, json=data_to_send, timeout=15)
            
            if response.status_code == 200:
                print(f"Successfully sent {len(ids)} IDs to Sheet '{sheet_name}'")
                
                # --- ៤. បង្កើតសារ Quote Reply តបទៅវិញឱ្យអស់ទិន្នន័យ ---
                reply_message = "Remake: late wd 1day up\n\n"
                reply_message += f"Web : {sheet_name}\n\n"
                reply_message += f"WD Date : {wd_date}\n"
                
                for item in ids:
                    reply_message += f"ID : `{item}`\n"
                
                # ផ្ញើ Quote Reply ត្រឡប់ទៅក្រុមវិញ
                bot.reply_to(message, reply_message, parse_mode="Markdown")
            else:
                print(f"Failed to send to GAS. Status code: {response.status_code}")
                
    except Exception as e:
        print(f"Error processing message: {e}")

def run_bot_polling():
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Bot connection lost: {e}. Retrying in 5 seconds...")
            time.sleep(5)

# ==========================================
# 4. រត់ Web Server និង Bot ព្រមគ្នា (Multi-Threading)
# ==========================================
if __name__ == "__main__":
    print("Starting Web Server...")
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Telegram Bot successfully started and running smoothly!")
    run_bot_polling()

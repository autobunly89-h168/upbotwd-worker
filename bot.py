import sys
import time
import re
import requests
import telebot

# ==========================================
# 1. កំណត់តម្លៃ Token និង URL ផ្ទាល់ៗ
# ==========================================
TOKEN = "8953741339:AAH0OLFVZ8ANtsdpQESTbdFM_NB5fDnw-ns"
GAS_URL = "https://script.google.com/macros/s/AKfycbxAqD_OTAhaNaS-ZDDG0FAuetqUUpHup8GQAFIQQDuyzm_FotarAWUw3XQOXGnsAl-z/exec" # ⚠️ យកលីង Deploy ថ្មី (Anyone) មកដាក់ឱ្យពេញលេញនៅត្រង់នេះ

if not TOKEN or not GAS_URL:
    print("Error: Missing TOKEN or GAS_URL!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)
print("Telegram Bot is starting up...")

# ==========================================
# 2. ផ្នែកកូដដំណើរការរបស់ Telegram Bot
# ==========================================

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        text = message.text
        if text:
            print(f"Received message:\n{text}")
            
            # --- ១. យកឈ្មោះ Telegram ធ្វើជាឈ្មោះ Web និងឈ្មោះ Sheet ---
            sheet_name = message.from_user.first_name or "Telegram_User"
            
            # --- ២. ចាប់យកកាលបរិច្ឆេទ WD Date ឌីណាមិក (គេសរសេរអីយកហ្នឹង) ---
            # កូដនេះនឹងស្វែងរកឃ្លា "WD Date :" ឬ "Date :" រួចដកស្រង់យកអក្សរ/លេខដែលនៅបន្ទាត់ជាមួយគ្នាមកទាំងអស់
            date_match = re.search(r"(?:WD\s*)?Date\s*:\s*([^\n]+)", text, re.IGNORECASE)
            if date_match:
                wd_date = date_match.group(1).strip() # គេវាយថ្ងៃណា គឺបានថ្ងៃហ្នឹងពិតប្រាកដ
            else:
                wd_date = "N/A" # បើរកមិនឃើញសោះ ឱ្យដាក់ថា N/A
            
            print(f"Target Sheet: {sheet_name} | Extracted Date: {wd_date}")
            
            # --- ៣. ចាប់យកគ្រប់កូដ ID ទាំងអស់ (រក្សាអក្សរតូចធំដដែល) ---
            # លុបជួរកាលបរិច្ឆេទ និងឃ្លាផ្សេងៗចេញសិន ដើម្បីកុំឱ្យច្រឡំជាមួយ ID
            clean_text = re.sub(r"(?:WD\s*)?Date\s*:[^\n]*", "", text, flags=re.IGNORECASE)
            clean_text = re.sub(r"(Web|Remake|Late\s*wd)[^\n]*", "", clean_text, flags=re.IGNORECASE)
            
            # ចាប់យក ID (អក្សរ និងលេខលាយគ្នា ពី ៣ ដល់ ១៥ តួ)
            ids = re.findall(r"([a-zA-Z0-9]{3,15})", clean_text)
            
            if not ids:
                print("No IDs found in this message.")
                return

            # បង្កើតកញ្ចប់ទិន្នន័យផ្ញើទៅ Google Sheet
            data_to_send = {
                "sheet_name": sheet_name,
                "wd_date": wd_date,
                "ids": ids
            }
            
            # ផ្ញើទៅកាន់ Google Apps Script
            response = requests.post(GAS_URL, json=data_to_send, timeout=10)
            
            if response.status_code == 200:
                print(f"Successfully sent {len(ids)} IDs to Sheet '{sheet_name}'")
                
                # --- ៤. បង្កើតទម្រង់សារ Quote Reply ត្រឡប់ទៅវិញ ---
                reply_message = "Remake: late wd 1day up\n\n"
                reply_message += f"Web : {sheet_name}\n\n"
                reply_message += f"WD Date : {wd_date}\n" # បង្ហាញកាលបរិច្ឆេទតាមដែលគេសរសេរមកជាក់ស្ដែង
                
                # រាយនាម ID ជាទម្រង់ Quote `code` អក្សរតូចធំនៅដដែល
                for item in ids:
                    reply_message += f"ID : `{item}`\n"
                
                # ផ្ញើ Quote Reply ទៅកាន់ Group
                bot.reply_to(message, reply_message, parse_mode="Markdown")
            else:
                print(f"Failed to send to GAS. Status code: {response.status_code}")
                
    except Exception as e:
        print(f"Error processing message: {e}")

# ==========================================
# 3. រត់ប្រព័ន្ធទាញយកទិន្នន័យ (Bot Polling)
# ==========================================
if __name__ == "__main__":
    print("Telegram Bot successfully started and running smoothly!")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Bot connection lost: {e}. Retrying in 5 seconds...")
            time.sleep(5)

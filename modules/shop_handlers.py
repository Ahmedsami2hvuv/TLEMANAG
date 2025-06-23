from telebot import types
import logging
from . import data_manager # استيراد data_manager من نفس المجلد (النقطة كلش مهمة)

ADMIN_ID = None 

def set_admin_id(admin_id):
    global ADMIN_ID
    ADMIN_ID = admin_id

# دالة لإنشاء أزرار قائمة المحلات الفرعية
def get_shop_menu_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('إضافة محل'), types.KeyboardButton('عرض المحلات'), types.KeyboardButton('الرجوع للقائمة الرئيسية'))
    return markup

# دالة لإنشاء نص قائمة المحلات
def get_shops_list_str():
    if not data_manager.shops_data:
        return "ماكو محلات حالياً. ضيف محل جديد."
    
    list_str = "قائمة المحلات:\n"
    for i, s in enumerate(data_manager.shops_data):
        list_str += f"{i+1}. الاسم: {s['name']}, الرابط: {s['url']}\n"
    return list_str

# --- تسلسل إضافة محل جديد (معدل) ---
def handle_add_shop_start(bot, message, user_states):
    bot.send_message(message.chat.id, "لطفاً، ادخل اسم المحل:")
    user_states[message.chat.id] = {'state': 'awaiting_shop_name_for_new', 'data': {}} # بدء تسلسل جديد
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بإضافة محل جديد (تسلسل جديد).")

def get_new_shop_name(bot, message, user_states):
    shop_name = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل اسم المحل: {shop_name}")
    user_states[message.chat.id]['data']['name'] = shop_name
    user_states[message.chat.id]['state'] = 'awaiting_shop_url_for_new' # تغيير الحالة لانتظار الرابط
    bot.send_message(message.chat.id, "لطفاً، ادخل رابط المحل (يجب أن يبدأ بـ http:// أو https://):")

def get_new_shop_url(bot, message, user_states, get_admin_markup_func):
    shop_url = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل رابط المحل: {shop_url}")

    if not (shop_url.startswith('http://') or shop_url.startswith('https://')):
        logging.warning(f"رابط محل غير صالح (يفتقد http(s)): '{shop_url}'")
        bot.send_message(message.chat.id, "الرابط لازم يبدأ بـ 'http://' أو 'https://'. يرجى المحاولة مرة ثانية.")
        return # لا نغير الحالة، ننتظر رابط صحيح

    shop_name = user_states[message.chat.id]['data']['name']

    if any(s['name'] == shop_name for s in data_manager.shops_data):
        logging.warning(f"المدير حاول إضافة اسم محل موجود مسبقاً: '{shop_name}'")
        bot.send_message(message.chat.id, f"هذا الاسم ({shop_name}) موجود لمحل ثاني. يرجى استخدام اسم آخر.")
    else:
        data_manager.shops_data.append({'name': shop_name, 'url': shop_url})
        data_manager.save_data() # حفظ البيانات بعد إضافة محل جديد
        logging.info(f"تمت إضافة محل جديد: الاسم='{shop_name}', الرابط='{shop_url}'")
        bot.send_message(message.chat.id, f"تم حفظ المحل:\nالاسم: {shop_name}\nالرابط: {shop_url}")
        
    user_states[message.chat.id] = {'state': 'admin_main_menu'} # نرجع للقائمة الرئيسية للمدير
    bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    logging.debug(f"DEBUG: Exiting get_new_shop_url. State reset for chat ID: {message.chat.id}")

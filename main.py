import telebot
from telebot import types
import logging
import os 
import time 

# ==============================================================================
# إعدادات تسجيل الأخطاء (Logging)
# ==============================================================================
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] 
)
# ==============================================================================

# توكن البوت والـ ID مال المدير
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7773688435:AAHHWMc5VDYqMAYKIkU0SyCopeNBXgqJfbQ')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7032076289'))

if not BOT_TOKEN or not ADMIN_ID:
    logging.critical("CRITICAL: BOT_TOKEN or ADMIN_ID are not set. Exiting.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

user_states = {} 
logged_in_suppliers = {}

from modules import data_manager
from modules import supplier_handlers
from modules import shop_handlers
from modules import driver_handlers 

try:
    data_manager.load_data() 
    logging.info("تم بدء تشغيل البوت وتحميل البيانات من main.py.")
except Exception as e:
    logging.exception("خطأ حرج عند تحميل البيانات عند بدء تشغيل البوت. البوت لن يعمل.")
    exit(1) 

supplier_handlers.set_admin_id(ADMIN_ID)
shop_handlers.set_admin_id(ADMIN_ID)

def get_admin_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('المجهزين'), types.KeyboardButton('المحلات'), types.KeyboardButton('الطلبيات'), types.KeyboardButton('/start'))
    return markup

def get_supplier_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('المحلات'), types.KeyboardButton('المحفظة'), types.KeyboardButton('الطلبات'), types.KeyboardButton('/start'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logging.info(f"استلمت أمر /start من المستخدم ID: {message.from_user.id}")
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "أهلاً بك يا مدير، هاي لوحة التحكم:", reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    else: 
        found_supplier = next((s for s in data_manager.suppliers_data if s.get('telegram_id') == message.from_user.id), None)
        if found_supplier:
            bot.send_message(message.chat.id, "أهلاً بك مرة أخرى، مجهزنا العزيز!", reply_markup=get_supplier_markup())
            user_states[message.chat.id] = {'state': 'supplier_main_menu'}
            logged_in_suppliers[message.chat.id] = found_supplier
        else: 
            bot.send_message(message.chat.id, "أهلاً بك، يرجى إدخال الرمز الخاص بك:")
            user_states[message.chat.id] = {'state': 'awaiting_supplier_code'}

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_code')
def handle_supplier_login(message):
    entered_code = message.text.strip()
    logging.info(f"المستخدم ID {message.from_user.id} يحاول تسجيل الدخول بالرمز: {entered_code}")
    found_supplier = None
    for s in data_manager.suppliers_data:
        if s['code'] == entered_code:
            found_supplier = s
            found_supplier['telegram_id'] = message.from_user.id 
            data_manager.save_data() 
            break
    
    if found_supplier:
        logged_in_suppliers[message.chat.id] = found_supplier
        user_states[message.chat.id] = {'state': 'supplier_main_menu'}
        logging.info(f"المجهز '{found_supplier['name']}' (الرمز: {found_supplier['code']}) سجل الدخول. Chat ID: {message.chat.id}")
        bot.send_message(message.chat.id, f"أهلاً بك يا {found_supplier['name']}! هاي لوحة تحكمك:", reply_markup=get_supplier_markup())
    else:
        logging.warning(f"محاولة تسجيل دخول فاشلة للرمز: {entered_code} من المستخدم ID: {message.from_user.id}")
        bot.send_message(message.chat.id, "الرمز غلط، يرجى المحاولة مرة ثانية.")
        user_states[message.chat.id] = {'state': 'awaiting_supplier_code'}

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and user_states.get(message.chat.id, {}).get('state') == 'admin_main_menu' and message.text in ['المجهزين', 'المحلات', 'الطلبيات', '/start']) 
def handle_admin_main_buttons(message):
    logging.info(f"المدير (ID: {message.from_user.id}) ضغط على زر لوحة التحكم الرئيسية: {message.text}")
    
    if message.text == 'المجهزين':
        bot.send_message(message.chat.id, "أختر عملية للمجهزين:", reply_markup=supplier_handlers.get_supplier_menu_markup())
        user_states[message.chat.id] = {'state': 'supplier_menu'}
    elif message.text == 'المحلات':
        bot.send_message(message.chat.id, "أختر عملية للمحلات:", reply_markup=shop_handlers.get_shop_menu_markup())
        user_states[message.chat.id] = {'state': 'shop_menu'}
    elif message.text == 'الطلبيات':
        bot.send_message(message.chat.id, "قسم الطلبيات قيد الإنشاء حالياً.", reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    elif message.text == '/start': 
        bot.send_message(message.chat.id, "أهلاً بك يا مدير، هاي لوحة التحكم:", reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}

# ==============================================================================
# معالجات إدارة المجهزين (محولّة إلى ملف supplier_handlers.py)
# ==============================================================================

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and user_states.get(message.chat.id, {}).get('state') == 'supplier_menu' and message.text in ['إضافة مجهز', 'عرض المجهزين', 'تخصيص محلات لمجهز', 'تعديل مجهز', 'مسح مجهز', 'الرجوع للقائمة الرئيسية']) 
def handle_supplier_menu_buttons(message):
    logging.info(f"المدير (ID: {message.from_user.id}) في قائمة المجهزين الفرعية، ضغط على: {message.text}")
    
    if message.text == 'إضافة مجهز':
        supplier_handlers.handle_add_supplier_start(bot, message, user_states)
    elif message.text == 'عرض المجهزين':
        bot.send_message(message.chat.id, supplier_handlers.get_suppliers_list_str(), reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    elif message.text == 'تخصيص محلات لمجهز':
        supplier_handlers.handle_assign_shops_start(bot, message, user_states, get_admin_markup)
    elif message.text == 'تعديل مجهز':
        supplier_handlers.handle_edit_supplier_start(bot, message, user_states)
    elif message.text == 'مسح مجهز':
        supplier_handlers.handle_delete_supplier_start(bot, message, user_states)
    elif message.text == 'الرجوع للقائمة الرئيسية':
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup())

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_name_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_supplier_name(message):
    supplier_handlers.get_new_supplier_name(bot, message, user_states)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_code_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_supplier_code(message):
    supplier_handlers.get_new_supplier_code(bot, message, user_states)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_wallet_url_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_supplier_wallet_url(message):
    supplier_handlers.get_new_supplier_wallet_url(bot, message, user_states, get_admin_markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state', '').startswith('awaiting_supplier_new_value_') and message.from_user.id == ADMIN_ID)
def handle_process_edited_supplier_field(message):
    supplier_handlers.process_edited_supplier_field(bot, message, user_states, get_admin_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_supplier_for_shops_'))
def handle_select_supplier_for_shops_callback(call):
    supplier_handlers.select_supplier_for_shops_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('assign_shop_'))
def handle_assign_shop_to_supplier_callback(call):
    supplier_handlers.assign_shop_to_supplier_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'finish_assigning_shops')
def handle_finish_assigning_callback(call):
    supplier_handlers.finish_assigning_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_supplier_select_')) 
def handle_select_supplier_to_edit_callback(call):
    supplier_handlers.select_supplier_to_edit_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_supplier_field_')) 
def handle_supplier_edit_field_selection(call):
    supplier_handlers.handle_supplier_edit_field_selection(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_supplier_edit') 
def handle_cancel_supplier_edit_callback(call):
    supplier_handlers.cancel_supplier_edit_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_supplier_select_')) 
def handle_confirm_delete_supplier_callback(call):
    supplier_handlers.confirm_delete_supplier_callback(bot, call, user_states, get_admin_markup)


# ==============================================================================
# معالجات إدارة المحلات (محولّة إلى ملف shop_handlers.py)
# ==============================================================================

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and user_states.get(message.chat.id, {}).get('state') == 'shop_menu' and message.text in ['إضافة محل', 'عرض المحلات', 'تعديل محل', 'مسح محل', 'الرجوع للقائمة الرئيسية']) 
def handle_shop_menu_buttons(message):
    logging.info(f"المدير (ID: {message.from_user.id}) في قائمة المحلات الفرعية، ضغط على: {message.text}")
    
    if message.text == 'إضافة محل':
        shop_handlers.handle_add_shop_start(bot, message, user_states)
    elif message.text == 'عرض المحلات':
        bot.send_message(message.chat.id, shop_handlers.get_shops_list_str(), reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    elif message.text == 'تعديل محل':
        shop_handlers.handle_edit_shop_start(bot, message, user_states)
    elif message.text == 'مسح محل':
        shop_handlers.handle_delete_shop_start(bot, message, user_states)
    elif message.text == 'الرجوع للقائمة الرئيسية':
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup())

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_shop_name_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_shop_name(message):
    shop_handlers.get_new_shop_name(bot, message, user_states)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_shop_url_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_shop_url(message):
    shop_handlers.get_new_shop_url(bot, message, user_states, get_admin_markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state', '').startswith('awaiting_shop_new_value_') and message.from_user.id == ADMIN_ID)
def handle_process_edited_shop_field(message):
    shop_handlers.process_edited_shop_field(bot, message, user_states, get_admin_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_shop_select_'))
def handle_select_shop_to_edit_callback(call):
    shop_handlers.select_shop_to_edit_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_shop_field_'))
def handle_shop_edit_field_selection(call):
    shop_handlers.handle_shop_edit_field_selection(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_shop_edit')
def handle_cancel_shop_edit_callback(call):
    shop_handlers.cancel_shop_edit_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_shop_select_'))
def handle_confirm_delete_shop_callback(call):
    shop_handlers.confirm_delete_shop_callback(bot, call, user_states, get_admin_markup)


# ==============================================================================
# معالجات تفاعل المجهز (المستخدم العادي)
# ==============================================================================

@bot.message_handler(func=lambda message: message.text in ['المحلات', 'المحفظة', 'الطلبات', '/start'] and message.chat.id in logged_in_suppliers)
def handle_supplier_buttons(message):
    supplier_data = logged_in_suppliers[message.chat.id]
    logging.info(f"المجهز '{supplier_data['name']}' (ID: {message.from_user.id}) ضغط على زر: {message.text}")
    
    if message.text == '/start':
        bot.send_message(message.chat.id, "أهلاً بك مرة أخرى، مجهزنا العزيز!", reply_markup=get_supplier_markup())
        user_states[message.chat.id] = {'state': 'supplier_main_menu'}
        return 
        
    try:
        if message.text == 'المحلات':
            if not supplier_data['assigned_shops']:
                bot.send_message(message.chat.id, "لا توجد محلات مخصصة لك حالياً.")
                logging.info(f"المجهز '{supplier_data['name']}' ليس لديه محلات مخصصة.")
                return

            markup = types.InlineKeyboardMarkup(row_width=1)
            for shop in supplier_data['assigned_shops']:
                markup.add(types.InlineKeyboardButton(text=shop['name'], url=shop['url']))
            
            bot.send_message(message.chat.id, "المحلات المخصصة لك:", reply_markup=markup)
        elif message.text == 'المحفظة':
            if supplier_data.get('wallet_url'):
                wallet_url = supplier_data['wallet_url']
                # تصحيح الخطأ: تم حذف argument 'keyboard=' الزائد
                # هذا هو التصحيح النهائي الذي يضمن عدم تكرار الخطأ
                markup = types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="فتح المحفظة", web_app=types.WebAppInfo(url=wallet_url))]], 
                    resize_keyboard=True, 
                    one_time_keyboard=True
                )
                bot.send_message(message.chat.id, "المحفظة الخاصة بك:", reply_markup=markup)
                logging.info(f"المجهز '{supplier_data['name']}' فتح رابط المحفظة: {wallet_url}")
            else:
                bot.send_message(message.chat.id, "لم يتم تحديد رابط المحفظة الخاص بك بعد. يرجى التواصل مع المدير.")
                logging.warning(f"المجهز '{supplier_data['name']}' حاول فتح المحفظة، ولكن لا يوجد رابط محدد.")
        elif message.text == 'الطلبات':
            if supplier_data.get('orders_url'): 
                orders_url = supplier_data['orders_url']
                # تصحيح الخطأ: تم حذف argument 'keyboard=' الزائد
                markup = types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="عرض الطلبات", web_app=types.WebAppInfo(url=orders_url))]], 
                    resize_keyboard=True, 
                    one_time_keyboard=True
                )
                bot.send_message(message.chat.id, "الطلبات الخاصة بك:", reply_markup=markup)
                logging.info(f"المجهز '{supplier_data['name']}' أرسل رابط الطلبات: {orders_url}")
            else: 
                bot.send_message(message.chat.id, "قسم الطلبيات قيد الإنشاء حالياً.") 
                logging.info(f"المجهز '{supplier_data['name']}' ضغط على 'الطلبات' (الرابط غير محدد أو الميزة قيد الإنشاء).")

    except Exception as e:
        logging.exception(f"خطأ حرج (تم التقاطه) في handle_supplier_buttons للمجهز (ID: {message.from_user.id}). الزر المضغوط: '{message.text}'.")
        bot.send_message(message.chat.id, f"صار عندي خطأ غير متوقع في معالجة طلبك. يرجى المحاولة مرة ثانية أو التواصل مع الدعم. الخطأ: {e}")
    finally:
        if message.chat.id in logged_in_suppliers:
            bot.send_message(message.chat.id, "اختر من لوحة تحكم المجهز:", reply_markup=get_supplier_markup())

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def handle_admin_fallback(message):
    logging.warning(f"المدير (ID: {message.from_user.id}) أرسل رسالة غير معالجة: '{message.text}' في الحالة: {user_states.get(message.chat.id,{}).get('state')}")
    bot.send_message(message.chat.id, "آسف، لم أفهم طلبك. يرجى اختيار من الأزرار أو بدء الأمر من جديد.", reply_markup=get_admin_markup())
    user_states[message.chat.id] = {'state': 'admin_main_menu'}

@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID)
def handle_general_fallback(message):
    logging.warning(f"مستخدم غير مدير (ID: {message.from_user.id}) أرسل رسالة غير معالجة: '{message.text}' في الحالة: {user_states.get(message.chat.id,{}).get('state')}")
    if message.chat.id in logged_in_suppliers:
        bot.send_message(message.chat.id, "آسف، لم أفهم طلبك. يرجى اختيار من الأزرار.", reply_markup=get_supplier_markup())
    else:
        bot.send_message(message.chat.id, "آسف، لم أفهم طلبك. يرجى إدخال الرمز الخاص بك أو بدء الأمر من جديد.")
        user_states[message.chat.id] = {'state': 'awaiting_supplier_code'}


if __name__ == '__main__':
    while True:
        try:
            logging.info("بدء تشغيل البوت والبدء بالاستماع للرسائل...")
            bot.polling(none_stop=True, interval=1, timeout=20) 
        except telebot.apihelper.ApiTelegramException as api_e:
            logging.exception(f"خطأ في API تلغرام (قد يكون توكن غير صالح أو مشكلة شبكة): {api_e}")
            logging.info("البوت سيحاول إعادة التشغيل خلال 5 ثواني...")
            time.sleep(5)
        except Exception as e:
            logging.exception(f"خطأ حرج غير متوقع في تشغيل البوت: {e}")
            logging.info("البوت سيحاول إعادة التشغيل خلال 10 ثواني...")
            time.sleep(10)

import telebot
from telebot import types
import logging
import os # لإعدادات البيئة
import time # لأغراض تصحيح الأخطاء والتأخير

# ==============================================================================
# إعدادات تسجيل الأخطاء (Logging)
# ==============================================================================
# تأكد أن المخرجات تذهب إلى stdout حتى يلتقطها Railway
logging.basicConfig(
    level=logging.DEBUG, # مستوى DEBUG حتى نشوف كل التفاصيل
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # إخراج السجلات إلى الكونسول
)
# ==============================================================================

# توكن البوت والـ ID مال المدير (تعريفهم أولاً)
# يفضل استخدام المتغيرات البيئية (Environment Variables) في Railway لتخزين التوكن
# ولكن سنبقيها هنا مباشرة حاليا لتسهيل التشخيص.
BOT_TOKEN = '7773688435:AAHHWMc5VDYqMAYKIkU0SyCopeNBXgqJfbQ'
ADMIN_ID = 7032076289 # تأكد انو هذا هو ID مالتك الصحيح

# تعريف الكائن bot مبكراً
bot = telebot.TeleBot(BOT_TOKEN)

# تعريف المتغيرات العالمية الرئيسية قبل استيراد الموديلات
user_states = {} 
logged_in_suppliers = {}

# استيراد الموديلات (الملفات) اللي سويناها بعد تعريف المتغيرات الأساسية
from modules import data_manager
from modules import supplier_handlers
from modules import shop_handlers
from modules import driver_handlers # مؤقت للمستقبل

# ==============================================================================
# تحميل البيانات عند بدء تشغيل البوت
# ==============================================================================
try:
    data_manager.load_data() 
    logging.info("تم بدء تشغيل البوت وتحميل البيانات من main.py.")
except Exception as e:
    logging.exception("خطأ حرج عند تحميل البيانات عند بدء تشغيل البوت. البوت لن يعمل.")
    # إذا فشل التحميل هنا، لا فائدة من تشغيل البوت
    exit(1) # الخروج من التطبيق إذا فشل تحميل البيانات


# ==============================================================================
# ربط المتغيرات العالمية في data_manager مع القوائم الفعلية
# هذا يضمن أن التحديثات على data_manager.suppliers_data ستنعكس على القائمة نفسها.
# هذا جزء حاسم لضمان أن جميع أجزاء الكود تعمل على نفس البيانات المخزنة.
data_manager.suppliers_data = data_manager.suppliers_data # إعادة تعيين للتأكد من المرجع
data_manager.shops_data = data_manager.shops_data # إعادة تعيين للتأكد من المرجع
# Note: Since data_manager.load_data() modifies its own global lists,
# the `from modules import data_manager` already makes these accessible.
# The previous `suppliers_data[:] = ...` in data_manager.py was to handle this more robustly.

# ==============================================================================
# تعيين الـ ADMIN_ID للموديلات الأخرى اللي تحتاجه (الآن بعد تعريف كل شيء)
supplier_handlers.set_admin_id(ADMIN_ID)
shop_handlers.set_admin_id(ADMIN_ID)


# ==============================================================================
# دوال لوحة المفاتيح (Markup Functions) العامة
# ==============================================================================
def get_admin_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('المجهزين'), types.KeyboardButton('المحلات'), types.KeyboardButton('الطلبيات'))
    return markup

def get_supplier_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('المحلات'), types.KeyboardButton('المحفظة'), types.KeyboardButton('الطلبات'))
    return markup

# ==============================================================================
# معالجات الرسائل (Message Handlers) الرئيسية
# ==============================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logging.info(f"استلمت أمر /start من المستخدم ID: {message.from_user.id}")
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "أهلاً بك يا مدير، هاي لوحة التحكم:", reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    else: # أي شخص مو مدير
        # نشوف إذا هذا الـ ID مال تليجرام مربوط بمجهز مسجل مسبقاً
        found_supplier = next((s for s in data_manager.suppliers_data if s.get('telegram_id') == message.from_user.id), None)
        if found_supplier:
            bot.send_message(message.chat.id, "أهلاً بك مرة أخرى، مجهزنا العزيز!", reply_markup=get_supplier_markup())
            user_states[message.chat.id] = {'state': 'supplier_main_menu'}
            logged_in_suppliers[message.chat.id] = found_supplier
        else: # إذا مو مدير ولا مجهز مسجل دخول، راح نطلب منه الرمز
            bot.send_message(message.chat.id, "أهلاً بك، يرجى إدخال الرمز الخاص بك:")
            user_states[message.chat.id] = {'state': 'awaiting_supplier_code'}

# معالج لطلب تسجيل دخول المجهزين
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_code')
def handle_supplier_login(message):
    entered_code = message.text.strip()
    logging.info(f"المستخدم ID {message.from_user.id} يحاول تسجيل الدخول بالرمز: {entered_code}")
    found_supplier = None
    for s in data_manager.suppliers_data: # نستخدم البيانات المحملة من data_manager
        if s['code'] == entered_code:
            found_supplier = s
            # تخزين الـ telegram_id مع بيانات المجهز لتسجيل الدخول التلقائي في المستقبل
            found_supplier['telegram_id'] = message.from_user.id 
            data_manager.save_data() # حفظ البيانات بعد تحديث المجهز بالـ ID
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

# معالج أزرار لوحة تحكم المدير الرئيسية (المجهزين، المحلات، الطلبيات)
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and user_states.get(message.chat.id, {}).get('state') == 'admin_main_menu' and message.text in ['المجهزين', 'المحلات', 'الطلبيات'])
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

# ==============================================================================
# معالجات إدارة المجهزين (محولّة إلى ملف supplier_handlers.py)
# ==============================================================================

# معالج أزرار القائمة الفرعية للمجهزين
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and user_states.get(message.chat.id, {}).get('state') == 'supplier_menu' and message.text in ['إضافة مجهز', 'عرض المجهزين', 'تخصيص محلات لمجهز', 'الرجوع للقائمة الرئيسية'])
def handle_supplier_menu_buttons(message):
    logging.info(f"المدير (ID: {message.from_user.id}) في قائمة المجهزين الفرعية، ضغط على: {message.text}")
    
    if message.text == 'إضافة مجهز':
        supplier_handlers.handle_add_supplier_start(bot, message, user_states)
    elif message.text == 'عرض المجهزين':
        bot.send_message(message.chat.id, supplier_handlers.get_suppliers_list_str(), reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    elif message.text == 'تخصيص محلات لمجهز':
        supplier_handlers.handle_assign_shops_start(bot, message, user_states, get_admin_markup)
    elif message.text == 'الرجوع للقائمة الرئيسية':
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup())

# معالجات تسلسل إضافة مجهز جديد
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_name_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_supplier_name(message):
    supplier_handlers.get_new_supplier_name(bot, message, user_states)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_code_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_supplier_code(message):
    supplier_handlers.get_new_supplier_code(bot, message, user_states)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_supplier_wallet_url_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_supplier_wallet_url(message):
    supplier_handlers.get_new_supplier_wallet_url(bot, message, user_states, get_admin_markup)

# معالجات تخصيص المحلات للمجهز (أزرار Inline)
@bot.callback_query_handler(func=lambda call: call.data.startswith('select_supplier_for_shops_'))
def handle_select_supplier_for_shops_callback(call):
    supplier_handlers.select_supplier_for_shops_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('assign_shop_'))
def handle_assign_shop_to_supplier_callback(call):
    supplier_handlers.assign_shop_to_supplier_callback(bot, call, user_states, get_admin_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'finish_assigning_shops')
def handle_finish_assigning_callback(call):
    supplier_handlers.finish_assigning_callback(bot, call, user_states, get_admin_markup)

# ==============================================================================
# معالجات إدارة المحلات (محولّة إلى ملف shop_handlers.py)
# ==============================================================================

# معالج أزرار القائمة الفرعية للمحلات
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and user_states.get(message.chat.id, {}).get('state') == 'shop_menu' and message.text in ['إضافة محل', 'عرض المحلات', 'الرجوع للقائمة الرئيسية'])
def handle_shop_menu_buttons(message):
    logging.info(f"المدير (ID: {message.from_user.id}) في قائمة المحلات الفرعية، ضغط على: {message.text}")
    
    if message.text == 'إضافة محل':
        shop_handlers.handle_add_shop_start(bot, message, user_states)
    elif message.text == 'عرض المحلات':
        bot.send_message(message.chat.id, shop_handlers.get_shops_list_str(), reply_markup=get_admin_markup())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
    elif message.text == 'الرجوع للقائمة الرئيسية':
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup())

# معالج تسلسل إضافة محل جديد (الاسم والرابط في خطوتين منفصلتين)
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_shop_name_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_shop_name(message):
    shop_handlers.get_new_shop_name(bot, message, user_states)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_shop_url_for_new' and message.from_user.id == ADMIN_ID)
def handle_get_new_shop_url(message):
    shop_handlers.get_new_shop_url(bot, message, user_states, get_admin_markup)


# ==============================================================================
# معالجات تفاعل المجهز (المستخدم العادي)
# ==============================================================================

@bot.message_handler(func=lambda message: message.text in ['المحلات', 'المحفظة', 'الطلبات'] and message.chat.id in logged_in_suppliers)
def handle_supplier_buttons(message):
    supplier_data = logged_in_suppliers[message.chat.id]
    logging.info(f"المجهز '{supplier_data['name']}' (ID: {message.from_user.id}) ضغط على زر: {message.text}")
    
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
                markup = types.ReplyKeyboardMarkup(
                    [[types.KeyboardButton(text="فتح المحفظة", web_app=types.WebAppInfo(url=wallet_url))]], 
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
                markup = types.ReplyKeyboardMarkup(
                    [[types.KeyboardButton(text="عرض الطلبات", web_app=types.WebAppInfo(url=orders_url))]], 
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

# هذا المعالج العام يلتقط أي رسائل أخرى غير معالجة للمدير
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID)
def handle_admin_fallback(message):
    logging.warning(f"المدير (ID: {message.from_user.id}) أرسل رسالة غير معالجة: '{message.text}' في الحالة: {user_states.get(message.chat.id,{}).get('state')}")
    bot.send_message(message.chat.id, "آسف، لم أفهم طلبك. يرجى اختيار من الأزرار أو بدء الأمر من جديد.", reply_markup=get_admin_markup())
    user_states[message.chat.id] = {'state': 'admin_main_menu'}

# هذا المعالج العام يلتقط أي رسائل أخرى غير معالجة لغير المديرين
@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID)
def handle_general_fallback(message):
    logging.warning(f"مستخدم غير مدير (ID: {message.from_user.id}) أرسل رسالة غير معالجة: '{message.text}' في الحالة: {user_states.get(message.chat.id,{}).get('state')}")
    if message.chat.id in logged_in_suppliers:
        bot.send_message(message.chat.id, "آسف، لم أفهم طلبك. يرجى اختيار من الأزرار.", reply_markup=get_supplier_markup())
    else:
        bot.send_message(message.chat.id, "آسف، لم أفهم طلبك. يرجى إدخال الرمز الخاص بك أو بدء الأمر من جديد.")
        user_states[message.chat.id] = {'state': 'awaiting_supplier_code'}


# ==============================================================================
# نقطة بدء تشغيل البوت (Polling)
# ==============================================================================
# تم نقل هذا الجزء هنا مع try-except لضمان التقاط أي خطأ عند بدء الـ polling
if __name__ == '__main__': # هذا يضمن تشغيل الكود فقط عندما يتم تشغيل الملف مباشرة
    try:
        logging.info("بدء تشغيل البوت والبدء بالاستماع للرسائل...")
        # استخدام thread_safe=True قد يساعد في بيئات مثل Railway إذا كانت الـ concurrency مشكلة
        # timeout=20 يحدد كم يبقى البوت ينتظر التحديثات، none_stop يخليه ما يتوقف
        bot.polling(none_stop=True, interval=0, timeout=20) 
    except Exception as e:
        logging.exception(f"خطأ حرج في تشغيل البوت: {e}")
        # يمكن هنا إضافة محاولة إعادة تشغيل البوت بعد فترة، أو إرسال إشعار للمدير
        # For now, we just log and exit critically
        time.sleep(10) # انتظار 10 ثواني قبل الانتهاء (حتى لو Railway يحاول إعادة التشغيل)
        exit(1) # الخروج من العملية لمنع استهلاك موارد إذا البوت ما جاي يشتغل

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

# --- تسلسل إضافة محل جديد ---
def handle_add_shop_start(bot, message, user_states):
    bot.send_message(message.chat.id, "لطفاً، ادخل اسم المحل ورابطه بالشكل التالي:\nمثال: اسم:محل علي رابط:https://example.com/ali")
    user_states[message.chat.id] = {'state': 'awaiting_shop_info'}
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بإضافة محل جديد.")

def get_shop_info(bot, message, user_states, get_admin_markup_func):
    shop_info = message.text
    logging.debug(f"DEBUG: Entering get_shop_info. Input: '{shop_info}' from Admin ID: {message.from_user.id}")

    try:
        name_start = shop_info.find('اسم:')
        url_start = shop_info.find('رابط:')

        logging.debug(f"DEBUG: name_start={name_start}, url_start={url_start}")

        if name_start == -1 or url_start == -1:
            logging.warning(f"صيغة معلومات المحل خاطئة: تفتقد 'اسم:' أو 'رابط:'. الإدخال: '{shop_info}'")
            bot.send_message(message.chat.id, "صيغة الإدخال غلط. يرجى إدخالها بالشكل الصحيح:\nمثال: اسم:محل علي رابط:https://example.com/ali")
            return # لا نغير الحالة، ننتظر إدخال صحيح

        name = ""
        url = ""

        try:
            if name_start < url_start: 
                name_raw = shop_info[name_start + len('اسم:'):url_start]
                url_raw = shop_info[url_start + len('رابط:'):]
            else: 
                url_raw = shop_info[url_start + len('رابط:'):name_start]
                name_raw = shop_info[name_start + len('اسم:'):]

            name = name_raw.strip()
            url = url_raw.strip()

            if "رابط:" in name:
                name = name.split("رابط:")[0].strip()
            if "اسم:" in url:
                url = url.split("اسم:")[0].strip()

        except Exception as parse_error:
            logging.error(f"خطأ في تحليل اسم/رابط المحل. الإدخال: '{shop_info}'. الخطأ: {parse_error}", exc_info=True)
            bot.send_message(message.chat.id, "حدث خطأ أثناء معالجة الاسم أو الرابط. يرجى التأكد من الصيغة.")
            return

        if not name or not url:
            logging.warning(f"تحليل معلومات المحل نتج عنه اسم/رابط فارغ. الاسم: '{name}', الرابط: '{url}'")
            bot.send_message(message.chat.id, "لم يتم استخلاص الاسم أو الرابط بنجاح. يرجى التأكد من الصيغة.")
            return

        if not (url.startswith('http://') or url.startswith('https://')):
            logging.warning(f"رابط محل غير صالح (يفتقد http(s)): '{url}'")
            bot.send_message(message.chat.id, "الرابط لازم يبدأ بـ 'http://' أو 'https://'. يرجى المحاولة مرة ثانية.")
            return 

        if any(s['name'] == name for s in data_manager.shops_data):
            logging.warning(f"المدير حاول إضافة اسم محل موجود مسبقاً: '{name}'")
            bot.send_message(message.chat.id, f"هذا الاسم ({name}) موجود لمحل ثاني. يرجى استخدام اسم آخر.")
        else:
            data_manager.shops_data.append({'name': name, 'url': url})
            data_manager.save_data() # حفظ البيانات بعد إضافة محل جديد
            logging.info(f"تمت إضافة محل جديد: الاسم='{name}', الرابط='{url}'")
            bot.send_message(message.chat.id, f"تم حفظ المحل:\nالاسم: {name}\nالرابط: {url}")

    except Exception as e:
        logging.exception(f"خطأ حرج في get_shop_info للمدير (ID: {message.from_user.id}). الإدخال: '{shop_info}'.")
        bot.send_message(message.chat.id, f"صار عندي خطأ غير متوقع في إضافة المحل. يرجى المحاولة مرة ثانية أو التواصل مع الدعم. الخطأ: {e}")
    finally:
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
        logging.debug(f"DEBUG: Exiting get_shop_info. State reset for chat ID: {message.chat.id}")

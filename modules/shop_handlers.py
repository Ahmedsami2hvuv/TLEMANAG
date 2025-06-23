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
    markup.add(types.KeyboardButton('إضافة محل'), types.KeyboardButton('عرض المحلات'), 
               types.KeyboardButton('تعديل محل'), # زر جديد لتعديل المحل
               types.KeyboardButton('مسح محل'), # زر جديد لمسح المحل
               types.KeyboardButton('الرجوع للقائمة الرئيسية'))
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
    bot.send_message(message.chat.id, "لطفاً، ادخل اسم المحل:")
    user_states[message.chat.id] = {'state': 'awaiting_shop_name_for_new', 'data': {}} 
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بإضافة محل جديد (تسلسل جديد).")

def get_new_shop_name(bot, message, user_states):
    shop_name = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل اسم المحل: {shop_name}")
    user_states[message.chat.id]['data']['name'] = shop_name
    user_states[message.chat.id]['state'] = 'awaiting_shop_url_for_new' 
    bot.send_message(message.chat.id, "لطفاً، ادخل رابط المحل (يجب أن يبدأ بـ http:// أو https://):")

def get_new_shop_url(bot, message, user_states, get_admin_markup_func):
    shop_url = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل رابط المحل: {shop_url}")

    if not (shop_url.startswith('http://') or shop_url.startswith('https://')):
        logging.warning(f"رابط محل غير صالح (يفتقد http(s)): '{shop_url}'")
        bot.send_message(message.chat.id, "الرابط لازم يبدأ بـ 'http://' أو 'https://'. يرجى المحاولة مرة ثانية.")
        return 

    shop_name = user_states[message.chat.id]['data']['name']

    if any(s['name'] == shop_name for s in data_manager.shops_data):
        logging.warning(f"المدير حاول إضافة اسم محل موجود مسبقاً: '{shop_name}'")
        bot.send_message(message.chat.id, f"هذا الاسم ({shop_name}) موجود لمحل ثاني. يرجى استخدام اسم آخر.")
    else:
        data_manager.shops_data.append({'name': shop_name, 'url': shop_url})
        data_manager.save_data() # حفظ البيانات بعد إضافة محل جديد
        logging.info(f"تمت إضافة محل جديد: الاسم='{shop_name}', الرابط='{shop_url}'")
        bot.send_message(message.chat.id, f"تم حفظ المحل:\nالاسم: {shop_name}\nالرابط: {shop_url}")
        
    user_states[message.chat.id] = {'state': 'admin_main_menu'} 
    bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    logging.debug(f"DEBUG: Exiting get_new_shop_url. State reset for chat ID: {message.chat.id}")

# --- تسلسل تعديل محل ---
def handle_edit_shop_start(bot, message, user_states):
    if not data_manager.shops_data:
        bot.send_message(message.chat.id, "لا يوجد محلات للتعديل. يرجى إضافة محل أولاً.")
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, s in enumerate(data_manager.shops_data):
        markup.add(types.InlineKeyboardButton(text=f"{s['name']}", callback_data=f"edit_shop_select_{i}"))
    bot.send_message(message.chat.id, "اختر المحل الذي تريد تعديله:", reply_markup=markup)
    user_states[message.chat.id] = {'state': 'awaiting_shop_edit_selection'}
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بتعديل محل.")

def select_shop_to_edit_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID: return

    shop_index = int(call.data.split('_')[3])
    if 0 <= shop_index < len(data_manager.shops_data):
        selected_shop = data_manager.shops_data[shop_index]
        user_states[call.message.chat.id] = {
            'state': 'awaiting_shop_edit_info',
            'shop_index': shop_index,
            'data': selected_shop.copy() # نسخة من بيانات المحل
        }
        bot.send_message(call.message.chat.id, 
                         f"لطفاً، ادخل المعلومات الجديدة للمحل {selected_shop['name']}:\n"
                         "اسم جديد: [الاسم الجديد]\n"
                         "رابط جديد: [الرابط الجديد]\n"
                         "اترك فارغاً للحفاظ على القيمة الحالية.\n"
                         "مثال:\n"
                         "اسم جديد: مطعم النخيل\n"
                         "رابط جديد: https://newrestaurant.com")
        logging.info(f"المدير (ID: {call.from_user.id}) اختار المحل رقم {shop_index} للتعديل.")
    else:
        bot.send_message(call.message.chat.id, "المحل غير موجود.", reply_markup=get_admin_markup_func())
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}

def process_edited_shop_info(bot, message, user_states, get_admin_markup_func):
    user_chat_id = message.chat.id
    current_state = user_states.get(user_chat_id, {})
    if current_state.get('state') != 'awaiting_shop_edit_info': return 

    shop_index = current_state.get('shop_index')
    if not isinstance(shop_index, int) or not (0 <= shop_index < len(data_manager.shops_data)):
        bot.send_message(user_chat_id, "حدث خطأ في تحديد المحل. يرجى المحاولة مرة أخرى.", reply_markup=get_admin_markup_func())
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        return

    edited_shop = data_manager.shops_data[shop_index]
    input_lines = message.text.split('\n')
    changes_made = False

    try:
        for line in input_lines:
            line = line.strip()
            if line.startswith('اسم جديد:'):
                new_name = line.replace('اسم جديد:', '').strip()
                if new_name:
                    # التحقق من عدم تكرار الاسم الجديد
                    if any(s['name'] == new_name and s != edited_shop for s in data_manager.shops_data):
                        bot.send_message(user_chat_id, f"الاسم '{new_name}' موجود بالفعل لمحل آخر. لم يتم حفظ الاسم الجديد.")
                    else:
                        edited_shop['name'] = new_name
                        changes_made = True
            elif line.startswith('رابط جديد:'):
                new_url = line.replace('رابط جديد:', '').strip()
                if new_url:
                    if not (new_url.startswith('http://') or new_url.startswith('https://')):
                        bot.send_message(user_chat_id, "الرابط الجديد يجب أن يبدأ بـ 'http://' أو 'https://'. لم يتم حفظ الرابط الجديد.")
                    else:
                        edited_shop['url'] = new_url
                        changes_made = True
        
        if changes_made:
            data_manager.save_data()
            bot.send_message(user_chat_id, f"تم تعديل المحل {edited_shop['name']} بنجاح.")
            logging.info(f"المدير (ID: {message.from_user.id}) عدل المحل {edited_shop['name']}.")
        else:
            bot.send_message(user_chat_id, "لم يتم إدخال أي تغييرات صالحة.")

    except Exception as e:
        logging.exception(f"خطأ في معالجة معلومات تعديل المحل للمدير (ID: {message.from_user.id}).")
        bot.send_message(user_chat_id, f"صار عندي خطأ غير متوقع أثناء التعديل. الخطأ: {e}")
    finally:
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        bot.send_message(user_chat_id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())

# --- تسلسل مسح محل ---
def handle_delete_shop_start(bot, message, user_states):
    if not data_manager.shops_data:
        bot.send_message(message.chat.id, "لا يوجد محلات للمسح.")
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, s in enumerate(data_manager.shops_data):
        markup.add(types.InlineKeyboardButton(text=f"{s['name']}", callback_data=f"delete_shop_select_{i}"))
    bot.send_message(message.chat.id, "اختر المحل الذي تريد مسحه:", reply_markup=markup)
    user_states[message.chat.id] = {'state': 'awaiting_shop_delete_selection'}
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بمسح محل.")

def confirm_delete_shop_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID: return

    shop_index = int(call.data.split('_')[3])
    if 0 <= shop_index < len(data_manager.shops_data):
        shop_to_delete = data_manager.shops_data[shop_index]
        
        # مهم: إزالة المحل من أي مجهز كان مخصصاً له
        for supplier in data_manager.suppliers_data:
            supplier['assigned_shops'] = [s for s in supplier['assigned_shops'] if s != shop_to_delete]

        # إزالة المحل من القائمة الرئيسية للمحلات
        del data_manager.shops_data[shop_index]
        data_manager.save_data() # حفظ البيانات بعد المسح
        bot.send_message(call.message.chat.id, f"تم مسح المحل {shop_to_delete['name']} بنجاح.")
        logging.info(f"المدير (ID: {call.from_user.id}) مسح المحل {shop_to_delete['name']}.")
    else:
        bot.send_message(call.message.chat.id, "المحل غير موجود.", reply_markup=get_admin_markup_func())
        logging.warning(f"المدير (ID: {call.from_user.id}) حاول مسح محل غير موجود.")

    user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
    bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())

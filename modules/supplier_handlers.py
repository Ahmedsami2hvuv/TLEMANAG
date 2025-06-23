from telebot import types
import logging
from . import data_manager # استيراد data_manager من نفس المجلد (النقطة كلش مهمة)

# هذا راح يكون الـ ID مال المدير، راح يتم تعيينه من الملف الرئيسي
ADMIN_ID = None 

def set_admin_id(admin_id):
    global ADMIN_ID
    ADMIN_ID = admin_id

# دالة لإنشاء أزرار قائمة المجهزين الفرعية
def get_supplier_menu_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('إضافة مجهز'), types.KeyboardButton('عرض المجهزين'), 
               types.KeyboardButton('تخصيص محلات لمجهز'), 
               types.KeyboardButton('الرجوع للقائمة الرئيسية')) 
    return markup

# دالة لإنشاء نص قائمة المجهزين
def get_suppliers_list_str():
    if not data_manager.suppliers_data:
        return "ماكو مجهزين حالياً. ضيف مجهز جديد."

    list_str = "قائمة المجهزين:\n"
    for i, s in enumerate(data_manager.suppliers_data):
        shops_assigned = ", ".join([shop['name'] for shop in s['assigned_shops']]) if s['assigned_shops'] else "لا يوجد"
        wallet_link_status = s.get('wallet_url', "غير محدد")
        list_str += f"{i+1}. الرمز: {s['code']}, الاسم: {s['name']}\n   المحلات المخصصة: {shops_assigned}\n   رابط المحفظة: {wallet_link_status}\n"
    return list_str

# --- تسلسل إضافة مجهز جديد ---
def handle_add_supplier_start(bot, message, user_states):
    bot.send_message(message.chat.id, "لطفاً، ادخل اسم المجهز:")
    user_states[message.chat.id] = {'state': 'awaiting_supplier_name_for_new', 'data': {}}
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بإضافة مجهز جديد.")

def get_new_supplier_name(bot, message, user_states):
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل اسم المجهز: {message.text}")
    user_states[message.chat.id]['data']['name'] = message.text.strip()
    user_states[message.chat.id]['state'] = 'awaiting_supplier_code_for_new'
    bot.send_message(message.chat.id, "لطفاً، ادخل رقم (رمز) المجهز:")

def get_new_supplier_code(bot, message, user_states): # شلنا get_admin_markup_func لان ما نحتاجها مباشرة هنا
    code = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل رمز المجهز: {code}")
    if any(s['code'] == code for s in data_manager.suppliers_data):
        logging.warning(f"المدير (ID: {message.from_user.id}) حاول إضافة مجهز برمز موجود مسبقاً: {code}")
        bot.send_message(message.chat.id, f"هذا الرمز ({code}) موجود لمجهز آخر. يرجى استخدام رمز آخر.")
        bot.send_message(message.chat.id, "لطفاً، ادخل رقم (رمز) المجهز:")
        return False # للدلالة على أن العملية لم تكتمل بنجاح (يحتاج إعادة إدخال)
    user_states[message.chat.id]['data']['code'] = code
    user_states[message.chat.id]['state'] = 'awaiting_supplier_wallet_url_for_new'
    bot.send_message(message.chat.id, "لطفاً، ادخل رابط محفظة المجهز (يجب أن يبدأ بـ http:// أو https://):")
    return True # للدلالة على أن العملية مستمرة بنجاح

def get_new_supplier_wallet_url(bot, message, user_states, get_admin_markup_func):
    wallet_url = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل رابط محفظة المجهز: {wallet_url}")
    if not (wallet_url.startswith('http://') or wallet_url.startswith('https://')):
        logging.warning(f"المدير (ID: {message.from_user.id}) أدخل رابط محفظة غير صالح (يفتقد http(s)): {wallet_url}")
        bot.send_message(message.chat.id, "الرابط لازم يبدأ بـ 'http://' أو 'https://'. يرجى المحاولة مرة ثانية.")
        return False # للدلالة على أن العملية لم تكتمل بنجاح

    supplier_name = user_states[message.chat.id]['data']['name']
    supplier_code = user_states[message.chat.id]['data']['code']

    data_manager.suppliers_data.append({
        'code': supplier_code, 
        'name': supplier_name, 
        'telegram_id': None, 
        'assigned_shops': [],
        'wallet_url': wallet_url, 
        'orders_url': None
    })

    data_manager.save_data() # حفظ البيانات بعد إضافة مجهز جديد
    logging.info(f"تمت إضافة مجهز جديد: الاسم={supplier_name}, الرمز={supplier_code}, رابط المحفظة={wallet_url}")
    bot.send_message(message.chat.id, f"تم حفظ المجهز:\nالاسم: {supplier_name}\nالرمز: {supplier_code}\nرابط المحفظة: {wallet_url}")
    user_states[message.chat.id] = {'state': 'admin_main_menu'}
    bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    return True # للدلالة على أن العملية اكتملت بنجاح

# --- تسلسل تخصيص المحلات للمجهز ---
def handle_assign_shops_start(bot, message, user_states, get_admin_markup_func):
    if not data_manager.suppliers_data:
        logging.warning(f"المدير (ID: {message.from_user.id}) حاول تخصيص محلات ولكن لا يوجد مجهزين.")
        bot.send_message(message.chat.id, "ماكو مجهزين حتى تخصصلهم محلات. يرجى إضافة مجهز أولاً.", reply_markup=get_admin_markup_func())
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, s in enumerate(data_manager.suppliers_data):
        markup.add(types.InlineKeyboardButton(text=f"{s['name']} ({s['code']})", callback_data=f"select_supplier_for_shops_{i}"))
    bot.send_message(message.chat.id, "اختر المجهز اللي تريد تخصص اله محلات:", reply_markup=markup)
    user_states[message.chat.id] = {'state': 'awaiting_supplier_selection_for_shops'}
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بتخصيص محلات للمجهز.")

def select_supplier_for_shops_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id)
    logging.info(f"المدير (ID: {call.from_user.id}) اختار مجهز لتخصيص المحلات: {call.data}")

    if call.from_user.id != ADMIN_ID: 
        bot.send_message(call.message.chat.id, "انت لست مدير النظام.")
        logging.warning(f"مستخدم غير مدير (ID: {call.from_user.id}) حاول اختيار مجهز لتخصيص المحلات.")
        return

    supplier_index = int(call.data.split('_')[4])

    if 0 <= supplier_index < len(data_manager.suppliers_data):
        selected_supplier = data_manager.suppliers_data[supplier_index]
        user_states[call.message.chat.id] = {'state': 'assigning_shops_to_supplier', 'supplier_index': supplier_index}

        markup = types.InlineKeyboardMarkup(row_width=1)
        available_shops = [shop for shop in data_manager.shops_data if shop not in selected_supplier['assigned_shops']]

        if not available_shops:
            logging.info(f"لا توجد محلات متاحة للتخصيص للمجهز {selected_supplier['name']} (ID: {call.from_user.id}).")
            bot.send_message(call.message.chat.id, "لا توجد محلات متاحة للتخصيص لهذا المجهز.", reply_markup=get_admin_markup_func())
            user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
            return

        for i, shop in enumerate(available_shops):
            markup.add(types.InlineKeyboardButton(text=f"{shop['name']}", callback_data=f"assign_shop_{data_manager.shops_data.index(shop)}"))

        markup.add(types.InlineKeyboardButton(text="إنهاء التخصيص والرجوع", callback_data="finish_assigning_shops"))

        bot.send_message(call.message.chat.id, f"اختر المحلات اللي تريد تخصصها للمجهز: {selected_supplier['name']}", reply_markup=markup)
    else:
        logging.error(f"المدير (ID: {call.from_user.id}) اختار فهرس مجهز غير صالح لتخصيص المحلات: {supplier_index}")
        bot.send_message(call.message.chat.id, "المجهز غير موجود.")
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())

def assign_shop_to_supplier_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id, text="تم التخصيص!")
    logging.info(f"المدير (ID: {call.from_user.id}) يحاول تخصيص المحل: {call.data}")

    if call.from_user.id != ADMIN_ID: 
        bot.send_message(call.message.chat.id, "انت لست مدير النظام.")
        logging.warning(f"مستخدم غير مدير (ID: {call.from_user.id}) حاول تخصيص محل.")
        return

    user_chat_id = call.message.chat.id
    if user_states.get(user_chat_id, {}).get('state') == 'assigning_shops_to_supplier':
        supplier_index = user_states[user_chat_id]['supplier_index']
        shop_index = int(call.data.split('_')[2])

        if 0 <= supplier_index < len(data_manager.suppliers_data) and 0 <= shop_index < len(data_manager.shops_data):
            selected_supplier = data_manager.suppliers_data[supplier_index]
            selected_shop = data_manager.shops_data[shop_index]

            if selected_shop not in selected_supplier['assigned_shops']:
                selected_supplier['assigned_shops'].append(selected_shop)
                data_manager.save_data() # حفظ البيانات بعد تخصيص محل
                logging.info(f"تم تخصيص محل '{selected_shop['name']}' للمجهز '{selected_supplier['name']}' بواسطة المدير (ID: {call.from_user.id}).")
                bot.send_message(call.message.chat.id, f"تم تخصيص محل '{selected_shop['name']}' للمجهز '{selected_supplier['name']}'.")
            else:
                logging.info(f"محل '{selected_shop['name']}' مخصص أصلاً لهذا المجهز (المدير ID: {call.from_user.id}).")
                bot.send_message(call.message.chat.id, f"محل '{selected_shop['name']}' مخصص أصلاً لهذا المجهز.")

            markup = types.InlineKeyboardMarkup(row_width=1)
            available_shops = [shop for shop in data_manager.shops_data if shop not in selected_supplier['assigned_shops']]

            if not available_shops:
                logging.info(f"لا توجد محلات إضافية متاحة للتخصيص للمجهز {selected_supplier['name']}.")
                bot.send_message(call.message.chat.id, "لا توجد محلات إضافية متاحة للتخصيص لهذا المجهز.", reply_markup=get_admin_markup_func())
                user_states[user_chat_id] = {'state': 'admin_main_menu'}
                return

            for i, shop in enumerate(available_shops):
                markup.add(types.InlineKeyboardButton(text=f"{shop['name']}", callback_data=f"assign_shop_{data_manager.shops_data.index(shop)}"))

            markup.add(types.InlineKeyboardButton(text="إنهاء التخصيص والرجوع", callback_data="finish_assigning_shops"))
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            logging.error(f"صار خطأ في تخصيص المحل (فهرس مجهز/محل غير صالح) للمدير (ID: {call.from_user.id}). فهرس المجهز: {supplier_index}, فهرس المحل: {shop_index}", exc_info=True)
            bot.send_message(call.message.chat.id, "حدث خطأ في تحديد المجهز أو المحل.")
            user_states[user_chat_id] = {'state': 'admin_main_menu'}
            bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    else:
        logging.warning(f"المدير (ID: {call.from_user.id}) حاول تخصيص محل دون اختيار مجهز أولاً.")
        bot.send_message(call.message.chat.id, "يرجى اختيار المجهز أولاً لتخصيص المحلات.")
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())

def finish_assigning_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id, text="تم إنهاء التخصيص.")
    logging.info(f"المدير (ID: {call.from_user.id}) أنهى تخصيص المحلات.")
    if call.from_user.id == ADMIN_ID:
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    else:
        logging.warning(f"مستخدم غير مدير (ID: {call.from_user.id}) حاول إنهاء تخصيص المحلات.")
        bot.send_message(call.message.chat.id, "انت لست مدير النظام.")

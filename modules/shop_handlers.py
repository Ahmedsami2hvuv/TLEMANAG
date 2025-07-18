from telebot import types
import logging
from . import data_manager 

ADMIN_ID = None 

def set_admin_id(admin_id):
    global ADMIN_ID
    ADMIN_ID = admin_id

def get_shop_menu_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('إضافة محل'), types.KeyboardButton('عرض المحلات'), 
               types.KeyboardButton('تعديل محل'), 
               types.KeyboardButton('مسح محل'), 
               types.KeyboardButton('الرجوع للقائمة الرئيسية'))
    return markup

def get_shops_list_str():
    if not data_manager.shops_data:
        return "ماكو محلات حالياً. ضيف محل جديد."
    
    list_str = "قائمة المحلات:\n"
    for i, s in enumerate(data_manager.shops_data):
        list_str += f"{i+1}. الاسم: {s['name']}, الرابط: {s['url']}\n"
    return list_str

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
        data_manager.save_data() 
        logging.info(f"تمت إضافة محل جديد: الاسم='{shop_name}', الرابط='{shop_url}'")
        bot.send_message(message.chat.id, f"تم حفظ المحل:\nالاسم: {shop_name}\nالرابط: {shop_url}")
        
    user_states[message.chat.id] = {'state': 'admin_main_menu'} 
    bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    logging.debug(f"DEBUG: Exiting get_new_shop_url. State reset for chat ID: {message.chat.id}")

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
            'state': 'awaiting_shop_edit_field_selection', # حالة جديدة
            'shop_index': shop_index
        }
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="تعديل الاسم", callback_data="edit_shop_field_name"))
        markup.add(types.InlineKeyboardButton(text="تعديل الرابط", callback_data="edit_shop_field_url"))
        markup.add(types.InlineKeyboardButton(text="العودة", callback_data="cancel_shop_edit")) 
        bot.send_message(call.message.chat.id, 
                         f"ماذا تريد أن تعدل في المحل {selected_shop['name']}؟",
                         reply_markup=markup)
        logging.info(f"المدير (ID: {call.from_user.id}) اختار المحل رقم {shop_index} للتعديل (طلب حقل التعديل).")
    else:
        bot.send_message(call.message.chat.id, "المحل غير موجود.", reply_markup=get_admin_markup_func())
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}

def handle_shop_edit_field_selection(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID: return

    user_chat_id = call.message.chat.id
    current_state = user_states.get(user_chat_id, {})
    if current_state.get('state') != 'awaiting_shop_edit_field_selection':
        bot.send_message(user_chat_id, "يرجى اختيار المحل أولاً.", reply_markup=get_admin_markup_func())
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        return

    shop_index = current_state['shop_index']
    selected_field = call.data.replace('edit_shop_field_', '')
    selected_shop = data_manager.shops_data[shop_index]

    user_states[user_chat_id]['state'] = f'awaiting_shop_new_value_{selected_field}_for_edit' 
    user_states[user_chat_id]['field_to_edit'] = selected_field 
    user_states[user_chat_id]['shop_index'] = shop_index 
    
    prompt = ""
    if selected_field == 'name':
        prompt = f"ادخل الاسم الجديد للمحل {selected_shop['name']}:"
    elif selected_field == 'url':
        prompt = f"ادخل الرابط الجديد للمحل {selected_shop['name']} (يجب أن يبدأ بـ http:// أو https://):"
    
    bot.send_message(user_chat_id, prompt)
    logging.info(f"المدير (ID: {call.from_user.id}) اختار تعديل حقل {selected_field} للمحل رقم {shop_index}.")

def process_edited_shop_field(bot, message, user_states, get_admin_markup_func):
    user_chat_id = message.chat.id
    current_state = user_states.get(user_chat_id, {})
    
    if not current_state.get('state', '').startswith('awaiting_shop_new_value_') or not current_state.get('field_to_edit'):
        return 

    field_to_edit = current_state.get('field_to_edit')
    shop_index = current_state.get('shop_index')

    if not isinstance(shop_index, int) or not (0 <= shop_index < len(data_manager.shops_data)):
        bot.send_message(user_chat_id, "حدث خطأ في تحديد المحل. يرجى المحاولة مرة أخرى.", reply_markup=get_admin_markup_func())
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        return

    edited_shop = data_manager.shops_data[shop_index]
    new_value = message.text.strip()
    
    success = False
    
    if field_to_edit == 'name':
        if any(s['name'] == new_value and s != edited_shop for s in data_manager.shops_data):
            bot.send_message(user_chat_id, f"الاسم '{new_value}' موجود بالفعل لمحل آخر. يرجى إدخال اسم آخر.")
        elif new_value: 
            edited_shop['name'] = new_value
            success = True
        else: 
            bot.send_message(user_chat_id, "لم يتم إدخال اسم جديد. لم يتم التعديل.")
    elif field_to_edit == 'url':
        if new_value and not (new_value.startswith('http://') or new_value.startswith('https://')):
            bot.send_message(user_chat_id, "الرابط يجب أن يبدأ بـ 'http://' أو 'https://'. يرجى إدخال رابط صالح.")
        elif new_value: 
            edited_shop['url'] = new_value
            success = True
        else: 
            bot.send_message(user_chat_id, "لم يتم إدخال رابط جديد. لم يتم التعديل.")
    
    if success:
        data_manager.save_data()
        bot.send_message(user_chat_id, f"تم تعديل حقل {field_to_edit} للمحل {edited_shop['name']} بنجاح.")
        logging.info(f"المدير (ID: {message.from_user.id}) عدل حقل {field_to_edit} للمحل {edited_shop['name']}.")
    
    user_states[user_chat_id] = {'state': 'admin_main_menu'}
    bot.send_message(user_chat_id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    logging.info(f"المدير (ID: {message.from_user.id}) أكمل تعديل حقل المحل. العودة للقائمة الرئيسية.")

def cancel_shop_edit_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id, text="تم إلغاء التعديل.")
    if call.from_user.id == ADMIN_ID:
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    else:
        bot.send_message(call.message.chat.id, "انت لست مدير النظام.")

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
        
        for supplier in data_manager.suppliers_data:
            supplier['assigned_shops'] = [s for s in supplier['assigned_shops'] if s['name'] != shop_to_delete['name']]

        del data_manager.shops_data[shop_index]
        data_manager.save_data() 
        bot.send_message(call.message.chat.id, f"تم مسح المحل {shop_to_delete['name']} بنجاح.")
        logging.info(f"المدير (ID: {call.from_user.id}) مسح المحل {shop_to_delete['name']}.")
    else:
        bot.send_message(call.message.chat.id, "المحل غير موجود.", reply_markup=get_admin_markup_func())
        logging.warning(f"المدير (ID: {call.from_user.id}) حاول مسح محل غير موجود.")

    user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
    bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())

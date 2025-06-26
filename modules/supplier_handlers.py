from telebot import types
import logging
from . import data_manager

ADMIN_ID = None 

def set_admin_id(admin_id):
    global ADMIN_ID
    ADMIN_ID = admin_id

def get_supplier_menu_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('إضافة مجهز'), types.KeyboardButton('عرض المجهزين'), 
               types.KeyboardButton('تخصيص محلات لمجهز'), 
               types.KeyboardButton('تعديل مجهز'), 
               types.KeyboardButton('مسح مجهز'), 
               types.KeyboardButton('الرجوع للقائمة الرئيسية')) 
    return markup

def get_suppliers_list_str():
    if not data_manager.suppliers_data:
        return "ماكو مجهزين حالياً. ضيف مجهز جديد."
    
    list_str = "قائمة المجهزين:\n"
    for i, s in enumerate(data_manager.suppliers_data):
        shops_assigned = ", ".join([shop['name'] for shop in s['assigned_shops']]) if s['assigned_shops'] else "لا يوجد"
        wallet_link_status = s.get('wallet_url', "غير محدد")
        list_str += f"{i+1}. الرمز: {s['code']}, الاسم: {s['name']}\n   المحلات المخصصة: {shops_assigned}\n   رابط المحفظة: {wallet_link_status}\n"
    return list_str

def handle_add_supplier_start(bot, message, user_states):
    bot.send_message(message.chat.id, "لطفاً، ادخل اسم المجهز:")
    user_states[message.chat.id] = {'state': 'awaiting_supplier_name_for_new', 'data': {}} 
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بإضافة مجهز جديد.")

def get_new_supplier_name(bot, message, user_states):
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل اسم المجهز: {message.text}")
    user_states[message.chat.id]['data']['name'] = message.text.strip()
    user_states[message.chat.id]['state'] = 'awaiting_supplier_code_for_new'
    bot.send_message(message.chat.id, "لطفاً، ادخل رقم (رمز) المجهز:")

def get_new_supplier_code(bot, message, user_states):
    code = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل رمز المجهز: {code}")
    if any(s['code'] == code for s in data_manager.suppliers_data):
        logging.warning(f"المدير (ID: {message.from_user.id}) حاول إضافة مجهز برمز موجود مسبقاً: {code}")
        bot.send_message(message.chat.id, f"هذا الرمز ({code}) موجود لمجهز آخر. يرجى استخدام رمز آخر.")
        bot.send_message(message.chat.id, "لطفاً، ادخل رقم (رمز) المجهز:")
        return False 
    user_states[message.chat.id]['data']['code'] = code
    user_states[message.chat.id]['state'] = 'awaiting_supplier_wallet_url_for_new'
    bot.send_message(message.chat.id, "لطفاً، ادخل رابط محفظة المجهز (يجب أن يبدأ بـ http:// أو https://):")
    return True 

def get_new_supplier_wallet_url(bot, message, user_states, get_admin_markup_func):
    wallet_url = message.text.strip()
    logging.info(f"المدير (ID: {message.from_user.id}) أدخل رابط محفظة المجهز: {wallet_url}")
    if not (wallet_url.startswith('http://') or wallet_url.startswith('https://')):
        logging.warning(f"المدير (ID: {message.from_user.id}) أدخل رابط محفظة غير صالح (يفتقد http(s)): {wallet_url}")
        bot.send_message(message.chat.id, "الرابط لازم يبدأ بـ 'http://' أو 'https://'. يرجى المحاولة مرة ثانية.")
        return False 

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
    
    data_manager.save_data() 
    logging.info(f"تمت إضافة مجهز جديد: الاسم={supplier_name}, الرمز={supplier_code}, رابط المحفظة={wallet_url}")
    bot.send_message(message.chat.id, f"تم حفظ المجهز:\nالاسم: {supplier_name}\nالرمز: {supplier_code}\nرابط المحفظة: {wallet_url}")
    user_states[message.chat.id] = {'state': 'admin_main_menu'}
    bot.send_message(message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    return True 

def handle_edit_supplier_start(bot, message, user_states):
    if not data_manager.suppliers_data:
        bot.send_message(message.chat.id, "لا يوجد مجهزين للتعديل. يرجى إضافة مجهز أولاً.")
        user_states[message.chat.id] = {'state': 'admin_main_menu'}
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, s in enumerate(data_manager.suppliers_data):
        markup.add(types.InlineKeyboardButton(text=f"{s['name']} ({s['code']})", callback_data=f"edit_supplier_select_{i}"))
    bot.send_message(message.chat.id, "اختر المجهز الذي تريد تعديله:", reply_markup=markup)
    user_states[message.chat.id] = {'state': 'awaiting_supplier_edit_selection'}
    logging.info(f"المدير (ID: {message.from_user.id}) بدأ بتعديل مجهز.")

def select_supplier_to_edit_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID: return

    supplier_index = int(call.data.split('_')[3])
    if 0 <= supplier_index < len(data_manager.suppliers_data):
        selected_supplier = data_manager.suppliers_data[supplier_index]
        user_states[call.message.chat.id] = {
            'state': 'awaiting_supplier_edit_field_selection', 
            'supplier_index': supplier_index
        }
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="تعديل الاسم", callback_data="edit_supplier_field_name"))
        markup.add(types.InlineKeyboardButton(text="تعديل الرمز", callback_data="edit_supplier_field_code"))
        markup.add(types.InlineKeyboardButton(text="تعديل رابط المحفظة", callback_data="edit_supplier_field_wallet_url"))
        markup.add(types.InlineKeyboardButton(text="العودة", callback_data="cancel_supplier_edit")) 
        bot.send_message(call.message.chat.id, 
                         f"ماذا تريد أن تعدل في المجهز {selected_supplier['name']} ({selected_supplier['code']})؟",
                         reply_markup=markup)
        logging.info(f"المدير (ID: {call.from_user.id}) اختار المجهز رقم {supplier_index} للتعديل (طلب حقل التعديل).")
    else:
        bot.send_message(call.message.chat.id, "المجهز غير موجود.", reply_markup=get_admin_markup_func())
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}

def handle_supplier_edit_field_selection(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID: return

    user_chat_id = call.message.chat.id
    current_state = user_states.get(user_chat_id, {})
    if current_state.get('state') != 'awaiting_supplier_edit_field_selection':
        bot.send_message(user_chat_id, "يرجى اختيار المجهز أولاً.", reply_markup=get_admin_markup_func())
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        return

    supplier_index = current_state['supplier_index']
    selected_field = call.data.replace('edit_supplier_field_', '')
    selected_supplier = data_manager.suppliers_data[supplier_index]

    user_states[user_chat_id]['state'] = f'awaiting_supplier_new_value_{selected_field}_for_edit' 
    user_states[user_chat_id]['field_to_edit'] = selected_field 
    user_states[user_chat_id]['supplier_index'] = supplier_index 

    prompt = ""
    if selected_field == 'name':
        prompt = f"ادخل الاسم الجديد للمجهز {selected_supplier['name']}:"
    elif selected_field == 'code':
        prompt = f"ادخل الرمز الجديد للمجهز {selected_supplier['code']}:"
    elif selected_field == 'wallet_url':
        prompt = f"ادخل رابط المحفظة الجديد للمجهز {selected_supplier['name']} (يجب أن يبدأ بـ http:// أو https://):"
    
    bot.send_message(user_chat_id, prompt)
    logging.info(f"المدير (ID: {call.from_user.id}) اختار تعديل حقل {selected_field} للمجهز رقم {supplier_index}.")

def process_edited_supplier_field(bot, message, user_states, get_admin_markup_func):
    user_chat_id = message.chat.id
    current_state = user_states.get(user_chat_id, {})
    
    if not current_state.get('state', '').startswith('awaiting_supplier_new_value_') or not current_state.get('field_to_edit'):
        return 

    field_to_edit = current_state.get('field_to_edit')
    supplier_index = current_state.get('supplier_index')

    if not isinstance(supplier_index, int) or not (0 <= supplier_index < len(data_manager.suppliers_data)):
        bot.send_message(user_chat_id, "حدث خطأ في تحديد المجهز. يرجى المحاولة مرة أخرى.", reply_markup=get_admin_markup_func())
        user_states[user_chat_id] = {'state': 'admin_main_menu'}
        return

    edited_supplier = data_manager.suppliers_data[supplier_index]
    new_value = message.text.strip()
    
    success = False
    
    if field_to_edit == 'name':
        if any(s['name'] == new_value and s != edited_supplier for s in data_manager.suppliers_data):
            bot.send_message(user_chat_id, f"الاسم '{new_value}' موجود بالفعل لمجهز آخر. يرجى إدخال اسم آخر.")
        elif new_value: 
            edited_supplier['name'] = new_value
            success = True
        else: 
            bot.send_message(user_chat_id, "لم يتم إدخال اسم جديد. لم يتم التعديل.")
    elif field_to_edit == 'code':
        if any(s['code'] == new_value and s != edited_supplier for s in data_manager.suppliers_data):
            bot.send_message(user_chat_id, f"الرمز '{new_value}' موجود بالفعل لمجهز آخر. يرجى إدخال رمز آخر.")
        elif new_value: 
            edited_supplier['code'] = new_value
            success = True
        else: 
            bot.send_message(user_chat_id, "لم يتم إدخال رمز جديد. لم يتم التعديل.")
    elif field_to_edit == 'wallet_url':
        if new_value and not (new_value.startswith('http://') or new_value.startswith('https://')):
            bot.send_message(user_chat_id, "الرابط يجب أن يبدأ بـ 'http://' أو 'https://'. يرجى إدخال رابط صالح.")
        elif new_value: 
            edited_supplier['wallet_url'] = new_value
            success = True
        else: 
            bot.send_message(user_chat_id, "لم يتم إدخال رابط جديد. لم يتم التعديل.")
    
    if success:
        data_manager.save_data()
        bot.send_message(user_chat_id, f"تم تعديل حقل {field_to_edit} للمجهز {edited_supplier['name']} بنجاح.")
        logging.info(f"المدير (ID: {message.from_user.id}) عدل حقل {field_to_edit} للمجهز {edited_supplier['name']}.")
    
    user_states[user_chat_id] = {'state': 'admin_main_menu'}
    bot.send_message(user_chat_id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    logging.info(f"المدير (ID: {message.from_user.id}) أكمل تعديل حقل المجهز. العودة للقائمة الرئيسية.")


def cancel_supplier_edit_callback(bot, call, user_states, get_admin_markup_func):
    bot.answer_callback_query(call.id, text="تم إلغاء التعديل.")
    if call.from_user.id == ADMIN_ID:
        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
    else:
        bot.send_message(call.message.chat.id, "انت لست مدير النظام.")

    def handle_delete_supplier_start(bot, message, user_states):
        if not data_manager.suppliers_data:
            bot.send_message(message.chat.id, "لا يوجد مجهزين للمسح.")
            user_states[message.chat.id] = {'state': 'admin_main_menu'}
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, s in enumerate(data_manager.suppliers_data):
            markup.add(types.InlineKeyboardButton(text=f"{s['name']} ({s['code']})", callback_data=f"delete_supplier_select_{i}"))
        bot.send_message(message.chat.id, "اختر المجهز الذي تريد مسحه:", reply_markup=markup)
        user_states[message.chat.id] = {'state': 'awaiting_supplier_delete_selection'}
        logging.info(f"المدير (ID: {message.from_user.id}) بدأ بمسح مجهز.")

    def confirm_delete_supplier_callback(bot, call, user_states, get_admin_markup_func):
        bot.answer_callback_query(call.id)
        if call.from_user.id != ADMIN_ID: return

        supplier_index = int(call.data.split('_')[3])
        if 0 <= supplier_index < len(data_manager.suppliers_data):
            supplier_to_delete = data_manager.suppliers_data[supplier_index]
            
            del data_manager.suppliers_data[supplier_index]
            data_manager.save_data() 
            bot.send_message(call.message.chat.id, f"تم مسح المجهز {supplier_to_delete['name']} بنجاح.")
            logging.info(f"المدير (ID: {call.from_user.id}) مسح المجهز {supplier_to_delete['name']}.")
        else:
            bot.send_message(call.message.chat.id, "المجهز غير موجود.", reply_markup=get_admin_markup_func())
            logging.warning(f"المدير (ID: {call.from_user.id}) حاول مسح مجهز غير موجود.")

        user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
        bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())

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
            bot.send_message(call.message.chat.id, "المجهز غير موجود.", reply_markup=get_admin_markup_func())
            user_states[call.message.chat.id] = {'state': 'admin_main_menu'}

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
                    data_manager.save_data() 
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
                bot.send_message(call.message.chat.id, "حدث خطأ في تحديد المجهز أو المحل.", reply_markup=get_admin_markup_func())
                user_states[user_chat_id] = {'state': 'admin_main_menu'}
            
        else: 
            logging.warning(f"المدير (ID: {call.from_user.id}) حاول تخصيص محل دون اختيار مجهز أولاً.")
            bot.send_message(call.message.chat.id, "يرجى اختيار المجهز أولاً لتخصيص المحلات.", reply_markup=get_admin_markup_func())
            user_states[call.message.chat.id] = {'state': 'admin_main_menu'}

    def finish_assigning_callback(bot, call, user_states, get_admin_markup_func):
        bot.answer_callback_query(call.id, text="تم إنهاء التخصيص.")
        logging.info(f"المدير (ID: {call.from_user.id}) أنهى تخصيص المحلات.")
        if call.from_user.id == ADMIN_ID:
            user_states[call.message.chat.id] = {'state': 'admin_main_menu'}
            bot.send_message(call.message.chat.id, "اختر من لوحة التحكم:", reply_markup=get_admin_markup_func())
        else:
            bot.send_message(call.message.chat.id, "انت لست مدير النظام.")
    ```
* اضغط على زر **`Commit changes`**.

---

**ثالثاً: تحديث ملف `modules/shop_handlers.py` (مسح التعليقات):**

**أرجوك، انسخ هذا الكود كله، والصقه بملف `modules/shop_handlers.py` على GitHub. تأكد إنك تمسح كل المحتويات القديمة للملف قبل اللصق:**

```python
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
        logging.info(f"المدير (ID: {message.from_user.id}) عدل حقل {field_to_user.id}) ضغط على 'الطلبات' (الرابط غير محدد أو الميزة قيد الإنشاء).")

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

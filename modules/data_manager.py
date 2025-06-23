import jsonpickle
import os
import logging

# مكان ملف البيانات اللي راح نخزن بيه
DATA_FILE = 'data.json'

# متغيرات عالمية (Global) راح نخزن بيها بيانات المجهزين والمحلات
# IMPORTANT: Initialize these with empty lists if module is directly imported and used.
# main.py will also get a reference to these.
suppliers_data = []
shops_data = []

# دالة لتحميل البيانات من الملف
def load_data(): # تم تغيير الاسم هنا من load_data_from_file
    global suppliers_data, shops_data # نعلن إننا سنعدل على المتغيرات العالمية
    
    logging.info(f"محاولة تحميل البيانات من {DATA_FILE}...")
    if os.path.exists(DATA_FILE): # إذا الملف موجود
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: # نفتح الملف للقراءة مع دعم اللغة العربية
                data_str = f.read()
                if not data_str.strip(): # إذا الملف فارغ أو يحتوي على مسافات فقط
                    logging.warning(f"الملف {DATA_FILE} فارغ أو يحتوي على مسافات فقط. تهيئة بيانات فارغة.")
                    suppliers_data = []
                    shops_data = []
                    return # ننهي الدالة هنا
                
                # إعدادات المكتبة jsonpickle حتى تشتغل صح
                jsonpickle.set_preferred_backend('json')
                jsonpickle.set_encoder_options('json', indent=4, sort_keys=True, ensure_ascii=False)
                
                data = jsonpickle.decode(data_str) # نقرا البيانات من الملف
                # تصحيح: نضمن أن القيم هي قوائم (lists) حتى لو كانت في الملف شيء آخر
                suppliers_data[:] = data.get('suppliers', []) # استخدام slice assignment لتحديث القائمة بنفس المرجع
                shops_data[:] = data.get('shops', []) # استخدام slice assignment لتحديث القائمة بنفس المرجع
                
                logging.info(f"تم تحميل البيانات بنجاح من {DATA_FILE}.")
                logging.debug(f"بيانات المجهزين المحملة: {suppliers_data}")
                logging.debug(f"بيانات المحلات المحملة: {shops_data}")

        except jsonpickle.json.JSONDecodeError as jde: # خطأ في فك تشفير JSON
            logging.error(f"خطأ في فك تشفير JSON عند تحميل البيانات من {DATA_FILE}: {jde}. الملف قد يكون تالفاً.", exc_info=True)
            suppliers_data = [] 
            shops_data = []
        except Exception as e: # أي خطأ آخر بالتحميل
            logging.error(f"صار خطأ عام بتحميل البيانات من {DATA_FILE}: {e}", exc_info=True)
            suppliers_data = [] 
            shops_data = []
    else: # إذا الملف ما موجود
        logging.info(f"الملف {DATA_FILE} ما موجود. تهيئة بيانات فارغة.")
        suppliers_data = []
        shops_data = []

# دالة لحفظ البيانات بالملف
def save_data(): # تم تغيير الاسم هنا من save_data_to_file
    data = {
        'suppliers': suppliers_data,
        'shops': shops_data
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f: # نفتح الملف للكتابة مع دعم اللغة العربية
            # إعدادات المكتبة jsonpickle للحفظ
            jsonpickle.set_preferred_backend('json')
            jsonpickle.set_encoder_options('json', indent=4, sort_keys=True, ensure_ascii=False)
            f.write(jsonpickle.encode(data)) # نحفظ البيانات
            logging.info(f"تم حفظ البيانات بنجاح في {DATA_FILE}.")
    except Exception as e: # إذا صار خطأ بالحفظ
        logging.error(f"صار خطأ بحفظ البيانات في {DATA_FILE}: {e}", exc_info=True)

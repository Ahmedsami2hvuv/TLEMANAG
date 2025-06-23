import jsonpickle
import os
import logging

# مكان ملف البيانات اللي راح نخزن بيه
DATA_FILE = 'data.json'

# متغيرات عالمية (Global) راح نخزن بيها بيانات المجهزين والمحلات
suppliers_data = []
shops_data = []

# دالة لتحميل البيانات من الملف
def load_data():
    global suppliers_data, shops_data
    if os.path.exists(DATA_FILE): # إذا الملف موجود
        try:
            with open(DATA_FILE, 'r') as f: # نفتح الملف للقراءة
                # إعدادات المكتبة jsonpickle حتى تشتغل صح ويا الملفات
                jsonpickle.set_preferred_backend('json')
                jsonpickle.set_decoder_options('json', object_hook=jsonpickle.object_hook)
                jsonpickle.set_encoder_options('json', indent=4, sort_keys=True, ensure_ascii=False)

                data = jsonpickle.decode(f.read()) # نقرا البيانات من الملف
                suppliers_data = data.get('suppliers', []) # ناخذ المجهزين، إذا ماكو نخلي قائمة فارغة
                shops_data = data.get('shops', []) # ناخذ المحلات، إذا ماكو نخلي قائمة فارغة
                logging.info("تم تحميل البيانات بنجاح من data.json")
        except Exception as e: # إذا صار خطأ بالتحميل
            logging.error(f"صار خطأ بتحميل البيانات من {DATA_FILE}: {e}", exc_info=True)
            suppliers_data = [] # نخلي القوائم فارغة إذا صار خطأ
            shops_data = []
    else: # إذا الملف ما موجود
        logging.info("الملف data.json ما موجود. تهيئة بيانات فارغة.")
        suppliers_data = []
        shops_data = []

# دالة لحفظ البيانات بالملف
def save_data():
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
            logging.info("تم حفظ البيانات بنجاح في data.json")
    except Exception as e: # إذا صار خطأ بالحفظ
        logging.error(f"صار خطأ بحفظ البيانات في {DATA_FILE}: {e}", exc_info=True)

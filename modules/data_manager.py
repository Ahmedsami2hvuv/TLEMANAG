import jsonpickle
import os
import logging

DATA_FILE = 'data.json' # الملف راح ينحفظ مباشرة في /app/data.json

suppliers_data = []
shops_data = []

def load_data():
    global suppliers_data, shops_data 
    logging.info(f"محاولة تحميل البيانات من {DATA_FILE} (من جذر التطبيق)..")
    if os.path.exists(DATA_FILE):
        logging.debug(f"الملف {DATA_FILE} موجود. حجمه: {os.path.getsize(DATA_FILE)} بايت.")
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data_str = f.read()
                if not data_str.strip():
                    logging.warning(f"الملف {DATA_FILE} فارغ أو يحتوي على مسافات فقط. تهيئة بيانات فارغة.")
                    suppliers_data[:] = []
                    shops_data[:] = []
                    return
                
                jsonpickle.set_preferred_backend('json')
                jsonpickle.set_encoder_options('json', indent=4, sort_keys=True, ensure_ascii=False)
                
                data = jsonpickle.decode(data_str)
                suppliers_data[:] = data.get('suppliers', [])
                shops_data[:] = data.get('shops', [])
                
                logging.info(f"تم تحميل البيانات بنجاح من {DATA_FILE}.")
                logging.debug(f"بيانات المجهزين المحملة: {suppliers_data}")
                logging.debug(f"بيانات المحلات المحملة: {shops_data}")

        except jsonpickle.json.JSONDecodeError as jde:
            logging.error(f"خطأ في فك تشفير JSON عند تحميل البيانات من {DATA_FILE}: {jde}. الملف قد يكون تالفاً.", exc_info=True)
            suppliers_data[:] = []
            shops_data[:] = []
        except Exception as e:
            logging.error(f"صار خطأ عام بتحميل البيانات من {DATA_FILE}: {e}", exc_info=True)
            suppliers_data[:] = []
            shops_data[:] = []
    else:
        logging.info(f"الملف {DATA_FILE} ما موجود. تهيئة بيانات فارغة.")
        suppliers_data[:] = []
        shops_data[:] = []

def save_data():
    data = {
        'suppliers': suppliers_data,
        'shops': shops_data
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            jsonpickle.set_preferred_backend('json')
            jsonpickle.set_encoder_options('json', indent=4, sort_keys=True, ensure_ascii=False)
            f.write(jsonpickle.encode(data))
            logging.info(f"تم حفظ البيانات بنجاح في {DATA_FILE}.")
            logging.debug(f"حجم ملف {DATA_FILE} بعد الحفظ: {os.path.getsize(DATA_FILE)} بايت.")
    except Exception as e:
        logging.error(f"صار خطأ بحفظ البيانات في {DATA_FILE}: {e}", exc_info=True)

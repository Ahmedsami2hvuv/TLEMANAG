import jsonpickle # هذا السطر هو اللي كان بي المشكلة، تم حذف حرف 'ر' الزائد
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
    logging.info(f"محاولة تحميل البيانات من {DATA_FILE}...")
    if os.path.exists(DATA_FILE):
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

# دالة لحفظ البيانات بالملف
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
    except Exception as e:
        logging.error(f"صار خطأ بحفظ البيانات في {DATA_FILE}: {e}", exc_info=True)

import os
import json # استخدام مكتبة json العادية
import logging

# أسماء المتغيرات البيئية اللي راح نخزن بيها البيانات
SUPPLIERS_ENV_VAR = 'SUPPLIERS_DATA_JSON'
SHOPS_ENV_VAR = 'SHOPS_DATA_JSON'

# تهيئة القوائم العالمية في هذا الملف
suppliers_data = []
shops_data = []

def load_data():
    global suppliers_data, shops_data 
    logging.info(f"محاولة تحميل البيانات من المتغيرات البيئية...")
    
    try:
        # تحميل بيانات المجهزين
        suppliers_json_str = os.environ.get(SUPPLIERS_ENV_VAR, '[]')
        suppliers_data_loaded = json.loads(suppliers_json_str)
        suppliers_data.extend(suppliers_data_loaded) # استخدام extend لملء القائمة العالمية

        # تحميل بيانات المحلات
        shops_json_str = os.environ.get(SHOPS_ENV_VAR, '[]')
        shops_data_loaded = json.loads(shops_json_str)
        shops_data.extend(shops_data_loaded) # استخدام extend لملء القائمة العالمية
        
        logging.info(f"تم تحميل البيانات بنجاح من المتغيرات البيئية.")
        logging.debug(f"بيانات المجهزين المحملة: {suppliers_data}")
        logging.debug(f"بيانات المحلات المحملة: {shops_data}")

    except json.JSONDecodeError as jde:
        logging.error(f"خطأ في فك تشفير JSON عند تحميل البيانات من المتغيرات البيئية: {jde}. البيانات قد تكون تالفة.", exc_info=True)
        suppliers_data.clear() # مسح القوائم في حالة وجود خطأ
        shops_data.clear()
    except Exception as e:
        logging.error(f"صار خطأ عام بتحميل البيانات من المتغيرات البيئية: {e}", exc_info=True)
        suppliers_data.clear()
        shops_data.clear()

def save_data():
    logging.info(f"محاولة حفظ البيانات في المتغيرات البيئية...")
    try:
        # حفظ بيانات المجهزين
        os.environ[SUPPLIERS_ENV_VAR] = json.dumps(suppliers_data, ensure_ascii=False)
        
        # حفظ بيانات المحلات
        os.environ[SHOPS_ENV_VAR] = json.dumps(shops_data, ensure_ascii=False)
        
        logging.info(f"تم حفظ البيانات بنجاح في المتغيرات البيئية.")
    except Exception as e:
        logging.error(f"صار خطأ بحفظ البيانات في المتغيرات البيئية: {e}", exc_info=True)

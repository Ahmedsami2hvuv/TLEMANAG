import os
import json # استخدام مكتبة json العادية

# أسماء المتغيرات البيئية اللي راح نخزن بيها البيانات
SUPPLIERS_ENV_VAR = 'SUPPLIERS_DATA_JSON'
SHOPS_ENV_VAR = 'SHOPS_DATA_JSON'

# تهيئة القوائم العالمية في هذا الملف
suppliers_data = []
shops_data = []

def load_data():
    global suppliers_data, shops_data 
    # مسح القوائم الحالية لضمان تحميل جديد ونظيف في كل مرة
    suppliers_data.clear()
    shops_data.clear()

    try:
        # تحميل بيانات المجهزين
        suppliers_json_str = os.environ.get(SUPPLIERS_ENV_VAR, '[]')
        suppliers_data_loaded = json.loads(suppliers_json_str)
        suppliers_data.extend(suppliers_data_loaded) 

        # تحميل بيانات المحلات
        shops_json_str = os.environ.get(SHOPS_ENV_VAR, '[]')
        shops_data_loaded = json.loads(shops_json_str)
        shops_data.extend(shops_data_loaded) 

    except json.JSONDecodeError as jde:
        # في حالة وجود خطأ في JSON، نبدأ بقوائم فارغة
        suppliers_data.clear() 
        shops_data.clear()
    except Exception as e:
        # لأي خطأ آخر، نبدأ بقوائم فارغة
        suppliers_data.clear()
        shops_data.clear()

def save_data():
    try:
        # حفظ بيانات المجهزين
        os.environ[SUPPLIERS_ENV_VAR] = json.dumps(suppliers_data, ensure_ascii=False)

        # حفظ بيانات المحلات
        os.environ[SHOPS_ENV_VAR] = json.dumps(shops_data, ensure_ascii=False)

    except Exception as e:
        # هنا لا يمكننا إرسال رسائل للبوت إذا فشل الحفظ
        # ولكن Railway سيلتقط أي أخطاء في الـ logs
        pass # لا تفعل شيئاً سوى السماح بالخطأ بالمرور وتسجيله بواسطة نظام Logging العام

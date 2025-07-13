import os
import json
import logging
from datetime import datetime, timezone # ✅ ضفنا هذا الاستيراد إذا راح تستخدم timestamp

DATA_FILE = 'data.json' # هذا حالياً ما مستخدم لأن دتستخدم os.environ

suppliers_data = []
shops_data = []
# ✅ متغيرات إضافية تم تعريفها هنا لضمان أنها global ويسهل الوصول إليها وتصفيرها
orders_data = {} # ✅ تم تغييرها إلى قاموس لأن الطلبيات تكون على شكل قواميس
pricing_data = {}
invoice_counter = 1
daily_profit_data = 0.0
supplier_report_timestamps = {}

def load_data():
    global suppliers_data, shops_data, orders_data, pricing_data, invoice_counter, daily_profit_data, supplier_report_timestamps 

    suppliers_data.clear()
    shops_data.clear()
    orders_data.clear()
    pricing_data.clear()
    # invoice_counter, daily_profit_data, supplier_report_timestamps will be reloaded from env or default
    
    try:
        # Load from environment variables
        suppliers_json_str = os.environ.get('SUPPLIERS_DATA_JSON', '[]')
        suppliers_data_loaded = json.loads(suppliers_json_str)
        suppliers_data.extend(suppliers_data_loaded) 

        shops_json_str = os.environ.get('SHOPS_DATA_JSON', '[]')
        shops_data_loaded = json.loads(shops_json_str)
        shops_data.extend(shops_data_loaded) 
        
        # ✅ تحميل البيانات الإضافية من المتغيرات البيئية
        orders_json_str = os.environ.get('ORDERS_DATA_JSON', '{}')
        orders_data.update(json.loads(orders_json_str)) # نستخدم update لأنها قاموس

        pricing_json_str = os.environ.get('PRICING_DATA_JSON', '{}')
        pricing_data.update(json.loads(pricing_json_str)) # نستخدم update لأنها قاموس
        
        invoice_counter = int(os.environ.get('INVOICE_COUNTER', '1'))
        daily_profit_data = float(os.environ.get('DAILY_PROFIT_DATA', '0.0'))
        
        supplier_report_timestamps_json_str = os.environ.get('SUPPLIER_REPORT_TIMESTAMPS_JSON', '{}')
        supplier_report_timestamps.update(json.loads(supplier_report_timestamps_json_str)) # نستخدم update لأنها قاموس

        logging.info("Data loaded successfully from environment variables.")
    except json.JSONDecodeError as jde:
        logging.error(f"JSON Decode Error loading data: {jde}. Reinitializing data.")
        suppliers_data.clear() 
        shops_data.clear()
        orders_data.clear()
        pricing_data.clear()
        invoice_counter = 1
        daily_profit_data = 0.0
        supplier_report_timestamps.clear()
    except Exception as e:
        logging.error(f"Error loading data: {e}. Reinitializing data.")
        suppliers_data.clear()
        shops_data.clear()
        orders_data.clear()
        pricing_data.clear()
        invoice_counter = 1
        daily_profit_data = 0.0
        supplier_report_timestamps.clear()

def save_data():
    try:
        # Save to environment variables
        os.environ['SUPPLIERS_DATA_JSON'] = json.dumps(suppliers_data, ensure_ascii=False)
        os.environ['SHOPS_DATA_JSON'] = json.dumps(shops_data, ensure_ascii=False)
        
        # ✅ حفظ المتغيرات الإضافية هنا
        os.environ['ORDERS_DATA_JSON'] = json.dumps(orders_data, ensure_ascii=False)
        os.environ['PRICING_DATA_JSON'] = json.dumps(pricing_data, ensure_ascii=False)
        os.environ['INVOICE_COUNTER'] = str(invoice_counter)
        os.environ['DAILY_PROFIT_DATA'] = str(daily_profit_data)
        os.environ['SUPPLIER_REPORT_TIMESTAMPS_JSON'] = json.dumps(supplier_report_timestamps, ensure_ascii=False)
        
        logging.info("Data saved successfully to environment variables.")
    except Exception as e:
        logging.exception("Error saving data to environment variables.")
        pass

# ✅ دالة تصفير كل البيانات (الجديدة)
def reset_all_data():
    global suppliers_data, shops_data, orders_data, pricing_data, invoice_counter, daily_profit_data, supplier_report_timestamps
    
    suppliers_data.clear()
    shops_data.clear()
    orders_data.clear()
    pricing_data.clear()
    invoice_counter = 1 # إعادة تعيين العداد
    daily_profit_data = 0.0 # إعادة تعيين الربح اليومي
    supplier_report_timestamps.clear() # إعادة تعيين أوقات تصفير المجهزين

    # بعد التصفير، نحفظ البيانات الفارغة لـ os.environ
    save_data()
    logging.info("All data (suppliers, shops, orders, pricing, etc.) reset and saved.")

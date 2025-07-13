import os
import json
import logging

DATA_FILE = 'data.json' # هذا حالياً ما مستخدم لأن دتستخدم os.environ

suppliers_data = []
shops_data = []
# ✅ متغيرات إضافية ممكن تحتاج تصفيرها لاحقاً
# orders_data = []
# pricing_data = {}
# invoice_counter = 1
# daily_profit_data = 0.0
# supplier_report_timestamps = {}

def load_data():
    global suppliers_data, shops_data 
    suppliers_data.clear()
    shops_data.clear()
    
    try:
        # Load from environment variables
        suppliers_json_str = os.environ.get('SUPPLIERS_DATA_JSON', '[]')
        suppliers_data_loaded = json.loads(suppliers_json_str)
        suppliers_data.extend(suppliers_data_loaded) 

        shops_json_str = os.environ.get('SHOPS_DATA_JSON', '[]')
        shops_data_loaded = json.loads(shops_json_str)
        shops_data.extend(shops_data_loaded) 
        
        logging.info("Data loaded successfully from environment variables.")
    except json.JSONDecodeError as jde:
        logging.error(f"JSON Decode Error loading data: {jde}. Reinitializing data.")
        suppliers_data.clear() 
        shops_data.clear()
    except Exception as e:
        logging.error(f"Error loading data: {e}. Reinitializing data.")
        suppliers_data.clear()
        shops_data.clear()

def save_data():
    try:
        # Save to environment variables
        os.environ['SUPPLIERS_DATA_JSON'] = json.dumps(suppliers_data, ensure_ascii=False)
        os.environ['SHOPS_DATA_JSON'] = json.dumps(shops_data, ensure_ascii=False)
        # ✅ ممكن تحتاج تحفظ متغيرات أخرى هنا لو كانت موجودة عالمياً بـ data_manager
        # os.environ['ORDERS_DATA_JSON'] = json.dumps(orders_data, ensure_ascii=False)
        # os.environ['PRICING_DATA_JSON'] = json.dumps(pricing_data, ensure_ascii=False)
        # os.environ['INVOICE_COUNTER'] = str(invoice_counter)
        # os.environ['DAILY_PROFIT_DATA'] = str(daily_profit_data)
        # os.environ['SUPPLIER_REPORT_TIMESTAMPS_JSON'] = json.dumps(supplier_report_timestamps, ensure_ascii=False)
        
        logging.info("Data saved successfully to environment variables.")
    except Exception as e:
        logging.exception("Error saving data to environment variables.")
        # Consider re-raising or handling more gracefully depending on impact
        pass

# ✅ دالة تصفير كل البيانات (الجديدة)
def reset_all_data():
    global suppliers_data, shops_data
    # ✅ هنا لازم نصفر كل البيانات اللي تريدها تتصفر
    suppliers_data.clear()
    shops_data.clear()
    # ✅ هنا لازم تضيف أي متغيرات بيانات عالمية أخرى تريد تصفيرها
    # orders_data.clear()
    # pricing_data.clear()
    # invoice_counter = 1
    # daily_profit_data = 0.0
    # supplier_report_timestamps.clear()

    # بعد التصفير، نحفظ البيانات الفارغة لـ os.environ
    save_data()
    logging.info("All data (suppliers, shops) reset and saved.")

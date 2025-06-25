import os
import json
import logging

DATA_FILE = 'data.json'

suppliers_data = []
shops_data = []

def load_data():
    global suppliers_data, shops_data 
    suppliers_data.clear()
    shops_data.clear()

    try:
        suppliers_json_str = os.environ.get('SUPPLIERS_DATA_JSON', '[]')
        suppliers_data_loaded = json.loads(suppliers_json_str)
        suppliers_data.extend(suppliers_data_loaded) 

        shops_json_str = os.environ.get('SHOPS_DATA_JSON', '[]')
        shops_data_loaded = json.loads(shops_json_str)
        shops_data.extend(shops_data_loaded) 

    except json.JSONDecodeError as jde:
        suppliers_data.clear() 
        shops_data.clear()
    except Exception as e:
        suppliers_data.clear()
        shops_data.clear()

def save_data():
    try:
        os.environ['SUPPLIERS_DATA_JSON'] = json.dumps(suppliers_data, ensure_ascii=False)
        os.environ['SHOPS_DATA_JSON'] = json.dumps(shops_data, ensure_ascii=False)

    except Exception as e:
        pass

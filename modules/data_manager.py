import os
import json
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Initialize Firebase outside functions to avoid repeated initialization
try:
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': os.environ.get('FIREBASE_PROJECT_ID')
        })
    db = firestore.client()
    logging.info("Firebase initialized successfully.")
except Exception as e:
    logging.critical(f"Critical error initializing Firebase: {e}", exc_info=True)
    db = None # Set db to None if initialization fails

# Firebase collection references
SUPPLIERS_COLLECTION = 'suppliers'
SHOPS_COLLECTION = 'shops'

# Global lists to hold data (synced with Firestore)
suppliers_data = []
shops_data = []

def load_data():
    global suppliers_data, shops_data
    suppliers_data.clear()
    shops_data.clear()
    
    if db is None:
        logging.error("Database not initialized. Cannot load data.")
        return

    try:
        logging.info("Attempting to load supplier data from Firestore...")
        suppliers_docs = db.collection(SUPPLIERS_COLLECTION).stream()
        for doc in suppliers_docs:
            supplier_dict = doc.to_dict()
            supplier_dict['id'] = doc.id
            suppliers_data.append(supplier_dict)
        logging.info(f"Loaded {len(suppliers_data)} suppliers from Firestore.")

        logging.info("Attempting to load shop data from Firestore...")
        shops_docs = db.collection(SHOPS_COLLECTION).stream()
        for doc in shops_docs:
            shop_dict = doc.to_dict()
            shop_dict['id'] = doc.id
            shops_data.append(shop_dict)
        logging.info(f"Loaded {len(shops_data)} shops from Firestore.")

    except Exception as e:
        logging.exception(f"Error loading data from Firestore: {e}")
        suppliers_data.clear()
        shops_data.clear()

def save_data():
    if db is None:
        logging.error("Database not initialized. Cannot save data.")
        return

    try:
        logging.info("Attempting to save data to Firestore...")
        
        # Save Suppliers
        current_suppliers_ids = [doc.id for doc in db.collection(SUPPLIERS_COLLECTION).stream()]
        for doc_id in current_suppliers_ids:
            db.collection(SUPPLIERS_COLLECTION).document(doc_id).delete()
        
        for supplier in suppliers_data:
            doc_id_to_use = supplier.get('id') if supplier.get('id') else supplier['code']
            db.collection(SUPPLIERS_COLLECTION).document(doc_id_to_use).set(supplier)
        
        # Save Shops
        current_shops_ids = [doc.id for doc in db.collection(SHOPS_COLLECTION).stream()]
        for doc_id in current_shops_ids:
            db.collection(SHOPS_COLLECTION).document(doc_id).delete()

        for shop in shops_data:
            doc_id_to_use = shop.get('id') if shop.get('id') else shop['name']
            db.collection(SHOPS_COLLECTION).document(doc_id_to_use).set(shop)

        logging.info("Data saved successfully to Firestore.")

    except Exception as e:
        logging.exception(f"Error saving data to Firestore: {e}")

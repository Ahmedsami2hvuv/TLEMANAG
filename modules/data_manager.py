import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import logging
import os

# تهيئة Firebase
# المفروض ملف الصلاحيات يتم تحميله تلقائيا من GOOGLE_APPLICATION_CREDENTIALS
# إذا لم يعمل هذا، قد نحتاج إلى استخدام مسار الملف مباشرة
try:
    if not firebase_admin._apps: # لمنع التهيئة المتكررة
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': os.environ.get('FIREBASE_PROJECT_ID') # يجب إضافة هذا كمتغير بيئي في Railway
        })
    db = firestore.client()
    logging.info("تم تهيئة Firebase بنجاح.")
except Exception as e:
    logging.critical(f"خطأ حرج في تهيئة Firebase: {e}", exc_info=True)
    # إذا فشلت التهيئة، لا يمكننا الاستمرار.
    # يجب التأكد من أن GOOGLE_APPLICATION_CREDENTIALS مضبوطة وصحيحة.
    db = None # لضمان عدم وجود db object
    # نستخدم exit(1) في main.py إذا فشل الاستيراد

# المراجع الرئيسية للمجموعات في Firestore
SUPPLIERS_COLLECTION = 'suppliers'
SHOPS_COLLECTION = 'shops'

# القوائم العالمية التي ستعكس بيانات Firestore
suppliers_data = []
shops_data = []

def load_data():
    global suppliers_data, shops_data

    # مسح القوائم الحالية لضمان تحميل جديد ونظيف في كل مرة
    suppliers_data.clear()
    shops_data.clear()

    if db is None:
        logging.error("قاعدة البيانات غير مهيأة. لا يمكن تحميل البيانات.")
        return

    try:
        logging.info("محاولة تحميل بيانات المجهزين من Firestore...")
        suppliers_docs = db.collection(SUPPLIERS_COLLECTION).stream()
        for doc in suppliers_docs:
            supplier_dict = doc.to_dict()
            supplier_dict['id'] = doc.id # إضافة الـ ID الخاص بـ Firestore
            suppliers_data.append(supplier_dict)
        logging.info(f"تم تحميل {len(suppliers_data)} مجهز من Firestore.")

        logging.info("محاولة تحميل بيانات المحلات من Firestore...")
        shops_docs = db.collection(SHOPS_COLLECTION).stream()
        for doc in shops_docs:
            shop_dict = doc.to_dict()
            shop_dict['id'] = doc.id # إضافة الـ ID الخاص بـ Firestore
            shops_data.append(shop_dict)
        logging.info(f"تم تحميل {len(shops_data)} محل من Firestore.")

    except Exception as e:
        logging.exception(f"خطأ في تحميل البيانات من Firestore: {e}")
        suppliers_data.clear()
        shops_data.clear()

def save_data():
    if db is None:
        logging.error("قاعدة البيانات غير مهيأة. لا يمكن حفظ البيانات.")
        return

    try:
        logging.info("محاولة حفظ البيانات إلى Firestore...")
        # حذف جميع المجهزين الحاليين وإعادة إضافتهم
        # (هذه الطريقة ليست مثالية للأداء في المشاريع الكبيرة جداً، ولكنها بسيطة ومناسبة هنا)
        current_suppliers_ids = [doc.id for doc in db.collection(SUPPLIERS_COLLECTION).stream()]
        for doc_id in current_suppliers_ids:
            db.collection(SUPPLIERS_COLLECTION).document(doc_id).delete()

        for supplier in suppliers_data:
            # نستخدم الرمز كـ ID للمستند لسهولة الوصول (أو ID Firestore إن وجد)
            doc_id_to_use = supplier.get('id') if supplier.get('id') else supplier['code']
            db.collection(SUPPLIERS_COLLECTION).document(doc_id_to_use).set(supplier)

        # حذف جميع المحلات الحالية وإعادة إضافتها
        current_shops_ids = [doc.id for doc in db.collection(SHOPS_COLLECTION).stream()]
        for doc_id in current_shops_ids:
            db.collection(SHOPS_COLLECTION).document(doc_id).delete()

        for shop in shops_data:
            # نستخدم الاسم كـ ID للمستند لسهولة الوصول (أو ID Firestore إن وجد)
            doc_id_to_use = shop.get('id') if shop.get('id') else shop['name']
            db.collection(SHOPS_COLLECTION).document(doc_id_to_use).set(shop)

        logging.info("تم حفظ البيانات بنجاح إلى Firestore.")

    except Exception as e:
        logging.exception(f"خطأ في حفظ البيانات إلى Firestore: {e}")

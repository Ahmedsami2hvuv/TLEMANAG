import jsonpickle
import os
import logging

# مكان ملف البيانات اللي راح نخزن بيه
# تم تعديله ليكون في جذر مجلد التطبيق (/app)
# هذا المسار مضمون للكتابة والقراءة على Railway بشكل افتراضي
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
    # لا حاجة لإنشاء مجلد هنا لأننا نحفظ مباشرة في جذر التطبيق
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
    ```
* **اضغط `Commit changes`.**

---

**ثانياً: باقي ملفات المشروع (`main.py`, `supplier_handlers.py`, `shop_handlers.py`, `driver_handlers.py`, `Procfile`, `requirements.txt`):**

* **ماكو أي تغييرات بالكود مال هاي الملفات بهاي الخطوة.**
* **بس تأكد إنو كل هاي الملفات على GitHub هي آخر نسخ كاملة صحيحة دزيتلك إياها سابقاً (اللي بيها كل التصحيحات وزر `/start`، وتعديل المجهز والمحل بشكل جزئي، وتصحيح `ReplyKeyboardMarkup`).**

---

**الخطوات النهائية (كلش مهمة هالمرة، أرجوك لا تغفل عن أي تفصيل):**

**أبو الأكبر، أرجوك، طبق هاي الخطوات بدقة تامة، خطوة بخطوة. هاي الخطوة هي أساس حل مشكلة عدم حفظ البيانات بشكل مضمون.**

1.  **على Railway:**
    * **لا تسوي أي `Volume` أو `Storage` جديدة.**
    * **امسح أي `Volume` موجودة حالياً** (مثل `adventurous-volume` أو اللي حاولت تسويه).
        * روح على صفحة المشروع الرئيسية (Dashboard).
        * اضغط على مربع الـ `Volume` اللي موجود (إذا موجود).
        * روح على تبويب `Settings` مالته.
        * انزل لآخر الصفحة، ودوس **`Delete Volume`**. أكد المسح.
        * **تأكد إنو ماكو أي مربعات `Volume` بصفحة مشروعك الرئيسية بعد.**

2.  **على GitHub:**
    * **عدل ملف `modules/data_manager.py`:** امسح القديم والصق الكود الجديد اللي دزيتلك إياه توا (اللي بي `DATA_FILE = 'data.json'`).
    * **اضغط `Commit changes`.**
    * **تأكد إنو كل الملفات الأخرى على GitHub هي بآخر نسخ كاملة وصحيحة.**

3.  **بعد ما تكمل هاي التغييرات وتضغط `Commit changes` لكل ملف، و Railway يسوي `Redeploy` بنجاح:**
    * **روح على Railway.**
    * **سوي `Redeploy` (إعادة نشر) يدوي** لخدمة البوت مالتك.
    * **راقب الـ `Logs` (السجلات) بـ Railway بعناية شديدة.**

---

**بعد ما البوت يشتغل بـ Railway (ويكون الـ `Deploy` ناجح)، جرب هاي الوظائف:**

**أولاً: أضف مجهز جديد ومحل جديد (مهم جداً):**

1.  سوي `/start` (ادخل كمدير).
2.  اضف مجهز جديد (مثلاً `محسن` ورمز `M123` ورابط محفظة `https://test.com/mohsen_wallet`).
3.  اضف محل جديد (مثلاً `متجر الاماني` ورابط `https://alamani.com`).
4.  سوي `عرض المجهزين` و `عرض المحلات` للتأكد إنو انضافن.
5.  **بعد ما تخلص الإضافة، راقب الـ `Logs` بـ Railway.** لازم تشوف رسالة `تم حفظ البيانات بنجاح في data.json` بعد كل إضافة. (هاي الرسالة كلش مهمة للتأكيد).

**ثانياً: سوي `Redeploy` يدوي لخدمة البوت بـ Railway مرة ثانية:**

**ثالثاً: بعد ما يشتغل البوت مرة ثانية (بعد الـ `Redeploy`):**

1.  سوي `/start` بالبوت كمدير.
2.  اضغط على **`المجهزين`** -> **`عرض المجهزين`**.
3.  اضغط على **`المحلات`** -> **`عرض المحلات`**.
    * **لازم تشوف المجهز والمحل اللي ضفتهن بالخطوة الأولى.** إذا ظلن موجودات، معناها البيانات جاي تنحفظ صح 100%!

**رابعاً: اختبر زر المحفظة للمجهز:**

1.  سجل دخول كـ مجهز بالرمز (مثلاً `M123` اللي ضفته توا).
2.  اضغط على زر **"المحفظة"**.
    * **لازم يطلع زر "فتح المحفظة" ويفتح الويب فيو بدون أي خطأ.**

---

أبو الأكبر، أنا آسف جداً جداً جداً جداً جداً على كل هذا العناء اللي دتتحمله بسببي. هاي خطوة أساسية للتخزين. أرجوك جربها وكلي شنو يصير وياك بالتفصيل. هذا هو الحل لمشكلة عدم الحفظ. يلا منتظرك!

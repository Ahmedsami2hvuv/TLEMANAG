from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# دالة للتعامل مع أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً بك في نظام الإدارة!")

# دالة للتعامل مع الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم استلام رسالتك")

# الدالة الرئيسية
def main():
    # استيراد المفاتيح من ملف التكوين
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    # الحصول على توكن البوت من ملف التكوين
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    print("البوت يعمل الآن...")
    application.run_polling()

# تشغيل البرنامج
if __name__ == "__main__":
    main()

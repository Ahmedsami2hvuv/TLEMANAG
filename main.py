import telebot
from telebot import types

# هذا التوكن اللي انطاك اياه BotFather
# تم تعديل التوكن بناءً على طلبك
BOT_TOKEN = '7773688435:AAHHWMc5VDYqMAYKIkU0SyCopeNBXgqJfbQ'

# هذا الـ ID مالتك حتى البوت يعرف انت المدير
# لازم تغير هذا الرقم بالـ ID الحقيقي مالتك!
# حتى تعرف الـ ID مالتك، ادخل لاي بوت يسويلك هاي الخدمة مثل @userinfobot
ADMIN_ID = 123456789 # غير هذا الرقم بالـ ID الحقيقي مالتك

bot = telebot.TeleBot(BOT_TOKEN)

# هاي الدالة راح تشتغل من تدوس /start بالبوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id == ADMIN_ID:
        # إذا انت المدير، راح تظهرلك لوحة التحكم
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn1 = types.KeyboardButton('المجهزين')
        itembtn2 = types.KeyboardButton('المحلات')
        itembtn3 = types.KeyboardButton('الطلبيات')
        markup.add(itembtn1, itembtn2, itembtn3)
        bot.send_message(message.chat.id, "أهلاً بك يا مدير، هاي لوحة التحكم:", reply_markup=markup)
    else:
        # إذا مو انت المدير، راح نطلب منه الرمز مالته
        bot.send_message(message.chat.id, "أهلاً بك، يرجى إدخال الرمز الخاص بك:")

# هاي الدالة راح تشغل البوت وتخليه يستمع للرسائل
bot.polling()

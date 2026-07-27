import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================================================================
# ОФИЦИАЛЬНАЯ КОНФИГУРАЦИЯ СТУДИИ SLEEPKIDD (ДАННЫЕ ЗАФИКСИРОВАНЫ)
BOT_TOKEN = "8932382255:AAEPLwGGXS771_Iyc_qBIT-3ZyzSWoih_qs"
ADMIN_ID = 532052338
# =====================================================================

bot = telebot.TeleBot(BOT_TOKEN)

# Внутреннее хранилище состояний модерации (0 - покой, 1 - ожидание отзыва)
user_states = {}

# --- СБОРКА ИНТЕРФЕЙСА: ХАЙ-ТЕК ИНЛАЙН КНОПКИ ---

def get_main_keyboard():
    """Сборка главного меню бота"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    
    # Кнопки со ссылками ведут на твои официальные страницы
    btn_site = InlineKeyboardButton("🌐 ПЕРЕЙТИ НА САЙТ", url="https://sleepkidd.su")
    btn_order = InlineKeyboardButton("⚡ ОБСУДИТЬ ПРОЕКТ (ЛИЧКА)", url="https://t.me")
    btn_review = InlineKeyboardButton("📝 ОСТАВИТЬ ОТЗЫВ", callback_data="trigger_review_flow")
    
    markup.add(btn_site, btn_order, btn_review)
    return markup

def get_cancel_keyboard():
    """Кнопка отмены в режиме ввода текста"""
    markup = InlineKeyboardMarkup()
    btn_cancel = InlineKeyboardButton("❌ ОТМЕНИТЬ ОТПРАВКУ", callback_data="cancel_review_flow")
    markup.add(btn_cancel)
    return markup
# --- ОБРАБОТКА МАРШРУТИЗАЦИИ С САЙТА И ПРИВЕТСТВИЙ ---

@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    text_args = message.text.split()
    
    # Стилизованный под консоль студии радар-приветствие
    tech_header = (
        "┌──────────────────────────────────┐\n"
        "   ■ SLEEPKIDD STUDIO SYSTEMS v2.6   \n"
        "   ■ СТАТУС: СОЕДИНЕНИЕ УСТАНОВЛЕНО  \n"
        "└──────────────────────────────────┘\n\n"
    )
    
    # Если клиент кликнул на кнопку на сайте (передан параметр ?start=review)
    if len(text_args) > 1 and text_args[1] == 'review':
        user_states[chat_id] = 1 # Включаем режим ожидания отзыва
        
        welcome_text = (
            f"{tech_header}"
            "👋 **Приветствуем в панели обратной связи!**\n\n"
            "Вы перешли со страницы отзывов нашего сайта.\n"
            "Пожалуйста, отправьте ваш фидбек **одним сообщением** (текст).\n\n"
            "🤖 _Я мгновенно перешлю его разработчику на модерацию._"
        )
        bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=get_cancel_keyboard())
    else:
        # Обычный старт бота через поиск в ТГ
        user_states[chat_id] = 0
        default_text = (
            f"{tech_header}"
            "🤖 **Добро пожаловать в официальный хаб!**\n\n"
            "Здесь вы можете запустить разработку проекта, перейти на наш сайт или поделиться своим мнением о сотрудничестве.\n\n"
            "Выбирайте нужную команду на панели управления ниже 👇"
        )
        bot.send_message(chat_id, default_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


# --- ОБРАБОТКА НАЖАТИЙ НА ИНЛАЙН КНОПКИ (CALLBACKS) ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    
    if call.data == "trigger_review_flow":
        user_states[chat_id] = 1 # Включаем режим ожидания отзыва
        review_prompt = (
            "📝 **РЕЖИМ НАПИСАНИЯ ОТЗЫВА АКТИВИРОВАН**\n\n"
            "Напишите ваш честный отзыв в ответном сообщении.\n"
            "Укажите, что вам понравилось, скорость работы или ваши впечатления."
        )
        # Плавно редактируем сообщение, добавляя кнопку отмены
        bot.edit_message_text(review_prompt, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_cancel_keyboard())
        
    elif call.data == "cancel_review_flow":
        user_states[chat_id] = 0 # Сбрасываем режим
        abort_text = (
            "❌ **Отправка отзыва отменена.**\n\n"
            "Вы вернулись в главное меню управления студии."
        )
        bot.edit_message_text(abort_text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard())


# --- ПРИЕМ ТЕКСТА И СИСТЕМНОЕ УВЕДОМЛЕНИЕ ДЛЯ АДМИНИСТРАТОРА ---

@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    current_state = user_states.get(chat_id, 0)
    
    if current_state == 1:
        # Сразу сбрасываем состояние в 0, чтобы бот не хватал следующие сообщения
        user_states[chat_id] = 0
        
        # Собираем данные клиента
        username = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
        first_name = message.from_user.first_name or "Пользователь"
        review_text = message.text
        
        # Формируем сочное системное сообщение для тебя (Админа)
        admin_notification = (
            "📥 **ПОЛУЧЕН НОВЫЙ ОТЗЫВ С САЙТА!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **От:** {first_name} ({username})\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 **ТЕКСТ ФИДБЕКА:**\n"
            f"« {review_text} »\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 _Если отзыв устраивает, просто скопируй его и вставь в reviews.html_"
        )
        
        try:
            # Пересылаем отзыв тебе на ID 532052338
            bot.send_message(ADMIN_ID, admin_notification, parse_mode="Markdown")
            
            # Радуем клиента красивым успехом и возвращаем главное меню
            success_text = "✅ **Отзыв успешно зафиксирован!**\n\nСпасибо за ваш вклад. Он передан разработчику на модерацию и скоро появится на панели сайта."
            bot.send_message(chat_id, success_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
            
        except Exception as e:
            bot.send_message(chat_id, "❌ Произошла ошибка отправки. Попробуйте еще раз.", parse_mode="Markdown", reply_markup=get_main_keyboard())
            print(f"Ошибка отправки администратору: {e}")
            
    else:
        # Если юзер пишет обычный текст вне режима отзыва
        fallback_text = "🤖 **Система работает в штатном режиме.**\n\nПожалуйста, используйте интерактивные кнопки меню для навигации."
        bot.send_message(chat_id, fallback_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


# Запуск постоянного сканирования сервера
if __name__ == '__main__':
    print("🤖 Бот SLEEPKIDD STUDIO успешно запущен и слушает сеть...")
    bot.infinity_polling()

import telebot
import os
import logging
import threading
from dotenv import load_dotenv
from config import FILE_NAME
from agent.analyst_agent import AnalystAgent

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(FILE_NAME)

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")

bot = telebot.TeleBot(BOT_TOKEN)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Хранилище для инструкций пользователей
user_instructions = {}


@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.send_message(
        message.chat.id,
        (
            "Бот для анализа данных помощью ИИ-агента\n\n"
            "Отправьте CSV или Excel файл для анализа.\n\n"
            "Вы можете добавить конкретную инструкцию:\n"
            "1. Сначала отправьте файл\n"
            "2. Затем отправьте инструкцию для анализа\n\n"
            "Примеры инструкций:\n"
            "- 'Найди аномалии продаж'\n"
            "- 'Проанализируй паттерны оттока клиентов'\n"
            "- 'Найди корреляции между ценой и продажами'\n\n"
            "Или просто отправьте файл, и я проведу комплексный анализ."
        )
    )


@bot.message_handler(content_types=["document"])
def handle_file(message):
    chat_id = message.chat.id

    try:
        # Проверка расширения файла
        file_name = message.document.file_name
        if not (file_name.endswith('.csv') or file_name.endswith('.xlsx')):
            bot.send_message(
                chat_id,
                "Пожалуйста, отправьте CSV или Excel файл."
            )
            return

        # Загрузка файла
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        save_path = os.path.join(UPLOAD_DIR, file_name)

        with open(save_path, "wb") as new_file:
            new_file.write(downloaded_file)

        # Сохранение пути к файлу
        user_instructions[chat_id] = {
            'file_path': save_path,
            'instruction': None,
            'processing': False
        }

        bot.send_message(
            chat_id,
            f"Файл сохранен: {file_name}\n\n"
            "Теперь отправьте инструкцию для анализа, или напишите:\n"
            "/analyze - для комплексного анализа\n"
            "/cancel - для отмены"
        )

    except Exception as e:
        logger.error(f"Error handling file: {e}")
        bot.send_message(chat_id, f"Ошибка: {str(e)}")


@bot.message_handler(commands=["analyze"])
def analyze(message):
    chat_id = message.chat.id

    if chat_id not in user_instructions:
        bot.send_message(
            chat_id,
            "Пожалуйста, сначала отправьте датасет."
        )
        return

    if user_instructions[chat_id].get('processing', False):
        bot.send_message(
            chat_id,
            "Анализ уже запущен. Пожалуйста, подождите."
        )
        return

    # Инструкция от пользователя
    instruction = user_instructions[chat_id].get('instruction')
    file_path = user_instructions[chat_id]['file_path']

    if not os.path.exists(file_path):
        bot.send_message(
            chat_id,
            "Файл не найден. Пожалуйста, загрузите его снова."
        )
        return

    # Флаг обработки
    user_instructions[chat_id]['processing'] = True

    bot.send_message(
        chat_id,
        "Начинаю анализ... Это может занять несколько минут."
    )

    # Запуск анализа в отдельном потоке
    thread = threading.Thread(
        target=run_analysis,
        args=(chat_id, file_path, instruction)
    )
    thread.daemon = True
    thread.start()


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id

    # Инструкция пользователя
    if chat_id in user_instructions and not user_instructions[chat_id]['processing']:
        instruction = message.text
        user_instructions[chat_id]['instruction'] = instruction

        bot.send_message(
            chat_id,
            f"Инструкция сохранена. Напишите /analyze для начала анализа."
        )
    else:
        bot.send_message(
            chat_id,
            "Пожалуйста, сначала отправьте датасет или используйте /start для помощи."
        )


@bot.message_handler(commands=["cancel"])
def cancel(message):
    chat_id = message.chat.id

    if chat_id in user_instructions:
        # Очистка состояния пользователя
        file_path = user_instructions[chat_id].get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        del user_instructions[chat_id]

    bot.send_message(
        chat_id,
        "Отменено. Используйте /start для начала."
    )


def run_analysis(chat_id, file_path, instruction):
    """Запуск анализа"""
    try:
        logger.info(f"Starting analysis for chat {chat_id}")
        logger.info(f"File: {file_path}")
        logger.info(f"Instruction: {instruction}")

        # Создание агента
        agent = AnalystAgent()

        # Запуск анализ
        pdf_path = agent.analyze(file_path, instruction)

        # Отправка результата
        with open(pdf_path, 'rb') as pdf_file:
            bot.send_document(
                chat_id,
                pdf_file,
                caption="Анализ завершен!\n\nВот ваш подробный отчет с инсайтами и визуализациями."
            )

        # Очистка состояния
        if chat_id in user_instructions:
            file_path = user_instructions[chat_id].get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            del user_instructions[chat_id]

    except Exception as e:
        logger.error(f"Analysis error for chat {chat_id}: {e}", exc_info=True)
        bot.send_message(
            chat_id,
            f"Анализ не удался: {str(e)}\n\nПожалуйста, попробуйте снова с более конкретной инструкцией."
        )

        if chat_id in user_instructions:
            user_instructions[chat_id]['processing'] = False


def start_bot():
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    bot.infinity_polling()
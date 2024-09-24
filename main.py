import os
import logging
import threading
import time
import uuid
import datetime
from collections import deque
import asyncio
from dotenv import load_dotenv
from collections import defaultdict
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from kak import scan_and_report_file, scan_result

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

file_queue = deque()
processing_lock = asyncio.Lock()
user_last_sent = defaultdict(lambda: 0)
lock = threading.Lock()

messages = {
    'uz': {
        'start': "Assalomu alaykum ushbu bot 'Kiberxavfsizlik markazi' DUK tomonidan tashkil qilingan bo'lib "
                 "zararli fayllarni tekshirish uchun tashkil qilingan. Undan foydalanish uchun shubhali "
                 "faylni botga jo'nating",
        'choose_language': "Iltimos, tilni tanlang:\nПожалуйста, выберите язык:",
        'file_received': "Faylingiz 'Kiberxavfsizlik markazi' DUK hodimlariga analiz uchun yuborildi, "
                         "e'tiboringiz uchun raxmat",
        'unsupported_file': "Iltimos faqat .apk, .exe, yoki .pdf fayl yuboring"
    },
    'ru': {
        'start': "Здравствуйте! Этот телеграм-бот создан для анализа и проверки вредоносных и подозрительных файлов."
                 " Отправьте пожалуйста подозрительный файл в данный телеграм-бот для анализа и проверки.",
        'choose_language': "Пожалуйста, выберите язык:\nPlease choose your language:",
        'file_received': "Ваш файл отправлен сотрудникам 'Кибербезопасности Центра' для анализа, "
                         "спасибо за ваше внимание",
        'unsupported_file': "Пожалуйста, отправьте только .apk, .exe, или .pdf файл"
    }
}

user_language = {}


def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_uzbek = InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data='lang_uz')
    btn_russian = InlineKeyboardButton("Русский 🇷🇺", callback_data='lang_ru')
    keyboard.add(btn_uzbek, btn_russian)
    return keyboard


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(messages['uz']['choose_language'], reply_markup=get_language_keyboard())


@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def process_language_choice(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    choice = callback_query.data
    if choice == 'lang_ru':
        user_language[user_id] = 'ru'
        response_message = messages['ru']['start']
    elif choice == 'lang_uz':
        user_language[user_id] = 'uz'
        response_message = messages['uz']['start']
    else:
        user_language[user_id] = 'uz'
        response_message = messages['uz']['start']
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, response_message)


@dp.message_handler(content_types=['document'])
async def handle_document(message: types.Message):
    try:
        user_id = message.from_user.id
        lang = user_language.get(user_id, 'uz')
        current_time = time.time()
        async with processing_lock:
            last_sent_time = user_last_sent.get(user_id, 0)
            if current_time - last_sent_time < 40:
                await message.reply("Iltimos, keyingi faylni 40 soniyadan keyin jo'nating")
                return
            user_last_sent[user_id] = current_time
        document = message.document
        file_name = document.file_name
        username = message.from_user.username
        if file_name.endswith(('.exe', '.apk', '.pdf')):
            await message.reply(messages[lang]['file_received'])
            file_queue.append({
                'document': document,
                'username': username,
                'chat_id': message.chat.id,
                'user_id': message.from_user.id,
                'file_name': file_name
            })
            if not processing_lock.locked():
                await asyncio.create_task(process_files())  ##########
        else:
            await message.reply(messages[lang]['unsupported_file'])
    except Exception as e:
        await bot.send_message(ADMIN_CHAT_ID, f"Error occurred: {e}")


async def process_files():
    while file_queue:
        file_info = file_queue.popleft()
        document = file_info['document']
        chat_id = file_info['chat_id']
        username = file_info['username']
        user_id = file_info['user_id']
        file_name = document.file_name

        try:
            file_info = await bot.get_file(document.file_id)
            file_path = file_info.file_path
            random_filename = f"{uuid.uuid4().hex}{os.path.splitext(file_name)[-1]}"
            save_dir = 'downloads'
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, random_filename)
            await bot.send_document(
                ADMIN_CHAT_ID, document.file_id,
                caption=f"Dastur nomi: {file_name}\nYuborgan shaxs:@{username}\nSaqlanadi:{random_filename}\n"
                        f"Chat ID: {user_id}\nTime: {datetime.datetime.now()}"
            )
            await bot.send_message(user_id, '⌛️')
            await bot.download_file(file_path, save_path)
            scan_process = scan_and_report_file(save_path)
            finish_result = scan_result(scan_process['scans'])
            await bot.send_message(
                chat_id,
                f"Analiz natijalari {file_name}:\n{finish_result}"
            )

        except Exception as e:
            await bot.send_message(ADMIN_CHAT_ID, f"Error occurred while processing {file_name}: {e}")

        await asyncio.sleep(1)


def polling_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logging.error(f"Polling error: {e}")
    finally:
        loop.close()


polling_thread = threading.Thread(target=polling_worker)
polling_thread.start()

while True:
    time.sleep(10)

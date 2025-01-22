import os
import logging
import threading
import time
import uuid
import datetime
import sqlite3
from collections import deque
import asyncio
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from collections import defaultdict
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from kak import scan_and_report_file, scan_result, get_hash

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
ADMIN_CHAT_ID = '7235437192'

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
        'file_received': "Ваш файл отправлен сотрудникам Центра Кибербезопасности  для анализа, "
                         ",благодарим за ваше внимание",
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
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"#start New user started the bot:\nUsername: @{username}\nUser ID: {user_id}"
    )


def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_help = KeyboardButton("📄 Yordam")
    btn_send_file = KeyboardButton("📁 Fayl tekshirish")
    btn_contact_support = KeyboardButton("📞 Ishonch raqami")
    btn_change_language = KeyboardButton("🌐 Tilni almashtirish")
    keyboard.add(btn_help, btn_send_file, btn_contact_support, btn_change_language)
    return keyboard


@dp.message_handler(lambda message: message.text == "🌐 Tilni almashtirish")
async def change_language(message: types.Message):
    user_id = message.from_user.id
    lang = user_language.get(user_id, 'uz')
    await message.reply(messages[lang]['choose_language'], reply_markup=get_language_keyboard())


@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def process_language_choice(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    choice = callback_query.data
    if choice == 'lang_ru':
        user_language[user_id] = 'ru'
        response_message = messages['ru']['start']
    else:
        user_language[user_id] = 'uz'
        response_message = messages['uz']['start']

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, response_message, reply_markup=get_main_menu())


@dp.message_handler(lambda message: message.text == "📄 Yordam")
async def help_command(message: types.Message):
    user_id = message.from_user.id
    lang = user_language.get(user_id, 'uz')
    help_text = messages[lang]['unsupported_file'] if lang == 'ru' else messages['uz']['unsupported_file']
    await message.reply(help_text)


@dp.message_handler(lambda message: message.text == "📁 Fayl tekshirish")
async def send_file_command(message: types.Message):
    user_id = message.from_user.id
    lang = user_language.get(user_id, 'uz')
    send_file_text = "Пожалуйста, отправьте файл для проверки." if lang == 'ru' else ("Iltimos, tekshirish uchun fayl "
                                                                                      "yuboring.")
    await message.reply(send_file_text)


@dp.message_handler(lambda message: message.text == "📞 Ishonch raqami")
async def contact_support_command(message: types.Message):
    user_id = message.from_user.id
    lang = user_language.get(user_id, 'uz')
    support_text = "Свяжитесь с поддержкой по этому номеру: +998 00 000 00 00" if lang == 'ru' else ("Qo'llab"
                                                                                                     "-quvvatlash "
                                                                                                     "uchun bu "
                                                                                                     "raqamga "
                                                                                                     "murojaat "
                                                                                                     "qiling: +998 00 "
                                                                                                     "000 00 00")
    await message.reply(support_text)


@dp.message_handler(commands=['admin_send'])
async def admin_send(message: types.Message):
    if str(message.from_user.id) != ADMIN_CHAT_ID:
        await message.reply("Sizda bu buyruqni bajarish uchun ruxsat yo'q.")
        return
    command_parts = message.get_args().split(' ', 1)

    if len(command_parts) < 2:
        await message.reply(
            "Iltimos, user_id va xabarni kiriting. Misol: /admin_send user_id Sizning faylingizda virus aniqlandi.")
        return

    user_id = command_parts[0]
    user_message = command_parts[1]

    try:
        user_id = int(user_id)
        await bot.send_message(user_id, user_message)
        await message.reply(f"Xabar {user_id} ga yuborildi.")
    except Exception as e:
        await message.reply(f"Xabar yuborishda xatolik: {e}")


# @dp.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
# async def forward_to_admin(message: types.Message):
#     if message.forward_from or message.forward_from_chat:
#         await bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id,)
#         await message.reply("Admin jo'natmangizni oldi javoblarni kuting")
#     elif message.from_user.id != ADMIN_CHAT_ID:
#         await message.reply("Adminga faqat yo'naltirilgan xabarlar yuboriladi.")


@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_document(message: types.Message):
    try:
        user_id = message.from_user.id
        lang = user_language.get(user_id, 'uz')
        if not message.document:
            await message.reply("Noto'g'ri fayl turi yuborildi. Iltimos, faqat hujjat yuboring.")
            return

        current_time = time.time()
        async with processing_lock:
            last_sent_time = user_last_sent.get(user_id, 0)
            if current_time - last_sent_time < 40:
                await message.reply("Iltimos, keyingi faylni 40 soniyadan keyin jo'nating")
                return
            user_last_sent[user_id] = int(current_time)

        document = message.document
        file_name = document.file_name
        username = message.from_user.username
        if file_name.endswith(('.exe', '.apk')):
            await message.reply(messages[lang]['file_received'])
            file_queue.append({
                'document': document,
                'username': username,
                'chat_id': message.chat.id,
                'user_id': message.from_user.id,
                'file_name': file_name
            })
            file_size = document.file_size
            if file_size > 30 * 1024 * 1024:
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    f"Fayl hajmi {file_name} juda katta (>{file_size / (1024 * 1024):.2f} MB), "
                    "qo'lda tekshirish uchun yuklandi."
                )
                await bot.send_document(
                    ADMIN_CHAT_ID,
                    document.file_id,
                    caption=f"Oversized file: {file_name}\nUploaded by: @{username}\nSize: {file_size / (1024 * 1024):.2f} MB"
                )
                return

            if not processing_lock.locked():
                await asyncio.create_task(process_files())
        else:
            await message.reply(messages[lang]['unsupported_file'])

    except Exception as e:
        await bot.send_message(ADMIN_CHAT_ID, f"Error occurred1: {e}")


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
                caption=f"Dastur nomi: {file_name}\nYuborgan shaxs: @{username}\nSaqlanadi: {random_filename}\n"
                        f"Chat ID: {user_id}\nTime: {datetime.datetime.now()}"
            )
            await bot.send_message(user_id, '⌛️')
            await bot.download_file(file_path, save_path)
            file_hash = get_hash(save_path)
            conn = sqlite3.connect('myallfiles.db')
            cursor = conn.cursor()
            cursor.execute('SELECT results FROM files WHERE hash_id = ?', (file_hash,))
            row = cursor.fetchone()
            if row:
                results = row[0]
                await bot.send_message(
                    chat_id,
                    f"Analiz natijalari {file_name} mavjud edi:\n{results}"
                )
            else:
                try:
                    scan_process = scan_and_report_file(file_hash=file_hash)
                    finish_result = scan_result(scan_process['scans'])
                    cursor.execute(
                        'INSERT INTO files (hash_id, file_name, results, date_time, username) VALUES (?, ?, ?, ?, ?)',
                        (file_hash, file_name, finish_result, datetime.datetime.now().isoformat(), username))
                    conn.commit()

                    await bot.send_message(
                        chat_id,
                        f"Analiz natijalari {file_name}:\n{finish_result}"
                    )

                except Exception as e:
                    await bot.send_message(chat_id, "Fayl bazada aniqlanmadi,tekshiruv vaqt olishi mumkin iltimos "
                                                    "kuting...")
                    await bot.send_message(ADMIN_CHAT_ID, f"VirusTotal bazasida aniqlanmadi qo'lda"
                                                          f" tekshiring {file_name}: {e}")
            conn.close()

        except Exception as e:
            await bot.send_message(ADMIN_CHAT_ID, f"Qandaydir xatolik1  {file_name}: {e}")
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

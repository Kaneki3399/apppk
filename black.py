import logging
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from datetime import datetime
import hashlib
import requests

BOT_TOKEN = "6845327291:AAFaQMOFii44XYjqqjY7PsqapKgp564YQOE"
VIRUSTOTAL_API_KEY = "fc1aaee4b150d80b73f7cc7e4064137486fc5ad690e33002c054a3232eeff039"
ADMIN_ID = 5510162499

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


async def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


async def check_virustotal(file_hash):
    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            positives = data["data"]["attributes"]["last_analysis_stats"]["malicious"]
            return positives > 0, positives
        else:
            return None, None
    elif response.status_code == 404:
        return None, None
    else:
        raise Exception(f"Error from VirusTotal: {response.status_code} {response.text}")


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_info = (f"New user started the bot:\n"
                 f"Username: @{message.from_user.username or 'N/A'}\n"
                 f"User ID: {message.from_user.id}\n"
                 f"Command: #start")
    await bot.send_message(ADMIN_ID, user_info)
    await message.reply("Assalomu alaykum ushbu bot 'Kiberxavfsizlik markazi' DUK tomonidan tashkil qilingan"
                        " bo'lib zararli fayllarni tekshirish uchun tashkil qilingan. Undan foydalanish uchun shubhali"
                        " faylni botga jo'nating\nKanalimiz https://t.me/cyber_csec_uz", reply_markup=user_keyboard)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_file(message: types.Message):
    try:
        document = message.document
        if not (document.file_name.endswith(".apk") or document.file_name.endswith(".exe")):
            await message.reply("Iltimos faqat .apk va .exe fayllarni jo'nating.")
            return
        max_size = 20 * 1024 * 1024
        if document.file_size > max_size:
            await message.reply("❗️ Ushbu fayl juda katta! Iltimos, 20 MB dan kichik fayl jo'nating.")
            return

        file = await bot.get_file(document.file_id)
        file_path = file.file_path
        unique_filename = f"downloads/{uuid.uuid4()}_{document.file_name}"
        await bot.download_file(file_path, unique_filename)
        sha256_hash = await calculate_sha256(unique_filename)
        user_info = (f"Username: @{message.from_user.username or 'N/A'}\n"
                     f"User ID: {message.from_user.id}\n"
                     f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"SHA256: {sha256_hash}\n"
                     f"File Name: {document.file_name}")
        await bot.send_message(ADMIN_ID, f"File received:\n{user_info}")
        await bot.send_document(ADMIN_ID, InputFile(unique_filename))
        is_malicious, positives = await check_virustotal(sha256_hash)
        await message.answer("Fayl tahlil qilinmoqda. Iltimos kuting.")

        if is_malicious is None:
            await bot.send_message(ADMIN_ID, "🛠 VirusTotal faylni aniqlamadi. Qo'lda tahlil qilish kerak.")
        elif is_malicious:
            await message.reply("⛔️ Ogoh bo'ling: Bu fayl zararli!\nIzoh: Ushbu fayl o'ta zararli deb topildi"
                                " va ushbu faylni butunlay o'chirib tashlashni tavsiya qilamiz\nhttps://t."
                                "me/cyber_csec_uz")
        else:
            await message.reply("♻️ Ushbu fayldan foydalanishda ehtiyot bo'ling\nIzoh: Ushbu faylda viruslik "
                                "aniqlanmagan bo'lsa ehtiyot bo'lib foydalanish tavsiya qilinadi, imkon qadar Play "
                                "market platformasidan yuklab olishni tavsiya qilamiz\nhttps://t.me/cyber_csec_uz")

    except Exception as e:
        logging.exception("Xatolik yuz berdi.")
        await bot.send_message(ADMIN_ID, f"Error: {str(e)}")
        await message.reply("Xatolik yuz berdi. Iltimos, yana urinib ko'ring.")


@dp.message_handler(commands=['admin'])
async def admin_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("🚫 Siz ushbu buyruqdan foydalanish huquqiga ega emassiz.")
        return

    try:
        args = message.get_args()
        user_id, user_message = args.split(' ', 1)
        user_id = int(user_id)
        await bot.send_message(user_id, user_message)
        await message.reply("Xabar jo'natildi")
    except Exception as e:
        await message.reply(f"Failed to send message.{e}")


user_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
user_keyboard.add(KeyboardButton("🧾 Yo'riqnoma"), KeyboardButton("☎️ Murojaat uchun bog'lanish"))


@dp.message_handler(lambda message: message.text == "🧾 Yo'riqnoma")
async def help_command(message: types.Message):
    await message.reply("Ushbu botdan foydalanish uchun sizga yetib kelgan shubhali "
                        "fayllarni botga jo'nating. Fayl nomi oxiridagi .apk va .exe yozuvlariga e'tiborli"
                        " bo'ling va ochmang\nhttps://t.me/cyber_csec_uz", reply_markup=user_keyboard)


@dp.message_handler(lambda message: message.text == "☎️ Murojaat uchun bog'lanish")
async def contact_command(message: types.Message):
    await message.reply("Savol va takliflar uchun +998 555 02 1010 raqamiga murojaat "
                        "qilishingiz mumkin\nhttps://t.me/cyber_csec_uz", reply_markup=user_keyboard)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

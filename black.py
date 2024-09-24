
# @dp.message_handler(content_types=['document'])
# async def handle_document(message: types.Message):
#     try:
#         user_id = message.from_user.id
#         lang = user_language.get(user_id, 'uz')
#         current_time = time.time()
#
#         # Lock mechanism to prevent spamming
#         with lock:
#             last_sent_time = user_last_sent.get(user_id, 0)
#             if current_time - last_sent_time < 120:
#                 await message.reply("Iltimos, keyingi faylni 2 daqiqadan keyin jo'nating")
#                 return
#             user_last_sent[user_id] = current_time
#
#         document = message.document
#         file_name = document.file_name.lower()
#
#         # Check for allowed file types
#         if file_name.endswith(('.exe', '.apk', '.pdf')):
#             await message.reply(messages[lang]['file_received'])
#
#             # Get the file info and file path from Telegram
#             file_info = await bot.get_file(document.file_id)
#             file_path = file_info.file_path
#
#             # Send the document to the admin chat
#             await bot.send_document(
#                 ADMIN_CHAT_ID, document.file_id,
#                 caption=f"Dastur nomi: {file_name}\nYuborgan shaxs username: @{message.from_user.username}\n"
#                         f"Chat ID: {message.from_user.id}\nTime: {datetime.datetime.now()}"
#             )
#
#             # Ensure the 'downloads' directory exists
#             save_dir = 'downloads'
#             os.makedirs(save_dir, exist_ok=True)
#
#             # Download the file to the specified directory
#             save_path = os.path.join(save_dir, file_name)
#             await bot.download_file(file_path, save_path)
#
#             # Perform the scan and analyze the results
#             scan_process = scan_and_report_file(save_path)
#             finish_result = scan_result(scan_process['scans'])
#
#             # Send the scan results back to the user
#             await bot.send_message(
#                 message.chat.id,
#                 f"Analiz natijalari {file_name}:\n{finish_result}\nQo'shimcha ma'lumot uchun:"
#             )
#
#             # Remove the file after processing
#             os.remove(save_path)
#
#         else:
#             await message.reply(messages[lang]['unsupported_file'])
#
#     except Exception as e:
#         # Notify the admin if an error occurs
#         await bot.send_message(ADMIN_CHAT_ID, f"Error occurred: {e}")


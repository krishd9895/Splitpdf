import telebot
import os
from PyPDF2 import PdfReader, PdfWriter


TOKEN = os.environ['TELEGRAM_TOKEN']

MAX_FILE_SIZE = 20000000  # 20 MB
ALLOWED_EXTENSIONS = ['.pdf']

bot = telebot.TeleBot(TOKEN)

# Dictionary to track the processing status for each chat
processing_status = {}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Welcome to the PDF Splitter Bot!\nUse the /splitpdf command to split PDF files.")

@bot.message_handler(commands=['splitpdf'])
def split_pdf(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send the PDF file to split. Maximum file size allowed: 20 MB.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    file_id = message.document.file_id
    file_size = message.document.file_size
    file_name = message.document.file_name

    # Check if the file has an allowed extension
    if not has_allowed_extension(file_name):
        bot.send_message(chat_id, "Invalid file format. Please send a PDF file.")
        return

    if file_size > MAX_FILE_SIZE:
        bot.send_message(chat_id, "Sorry, the maximum file size allowed is 20 MB.")
        return

    if chat_id in processing_status and processing_status[chat_id]:
        bot.send_message(chat_id, "Sorry, another PDF file is currently being processed. Please wait for the current process to complete.")
        return

    # Set the processing status for the current chat to True
    processing_status[chat_id] = True

    bot.send_message(chat_id, "PDF file received. Splitting process started...")

    # Download the PDF file
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)

    # Save the PDF file locally
    pdf_path = 'temp.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(downloaded_file)

    # Split the PDF into individual pages
    pages = split_pdf_pages(pdf_path)

    # Send each page as a separate file
    for i, page in enumerate(pages):
        page_name = f'page_{i + 1}.pdf'
        with open(page_name, 'wb') as f:
            page.write(f)
        with open(page_name, 'rb') as f:
            bot.send_document(chat_id, f)

        # Remove the generated page file
        os.remove(page_name)

    # Remove the downloaded PDF file
    os.remove(pdf_path)

    # Set the processing status for the current chat to False
    processing_status[chat_id] = False

    bot.send_message(chat_id, "Splitting process completed.")

def split_pdf_pages(file_path):
    input_pdf = PdfReader(file_path)
    pages = []
    for i in range(len(input_pdf.pages)):
        output = PdfWriter()
        output.add_page(input_pdf.pages[i])
        pages.append(output)
    return pages

def has_allowed_extension(filename):
    ext = os.path.splitext(filename)[1]
    return ext.lower() in ALLOWED_EXTENSIONS


bot.polling()
      
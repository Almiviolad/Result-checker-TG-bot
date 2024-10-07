from typing import Final
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os, requests, logging
from bs4 import BeautifulSoup
from result_checker import get_result, sign_in
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN: Final = os.getenv('TOKEN')
BOT_USERNAME: Final = "@FunResultChecker"
MATRIC, PASSWORD, LEVEL, SEMESTER = range(4)

#Entry point
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Thanks for chatting with me. Please enter your matric number") 
    return MATRIC

# validates matric no and moves to password state if valid
async def matric_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matricNo = update.message.text
    if not (matricNo.isdigit() and len(matricNo) == 8):
        await update.message.reply_text("Inavlid Matric number. Matric number must be 8 digits and numeric") 
        return MATRIC
    # store valid matrc no
    context.user_data['matricNo'] = matricNo
    await update.message.reply_text(f"Alright, {matricNo}. What's your password?")
    return PASSWORD

# stores password and and sign in to the portal
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    await update.message.delete()
    # store password
    context.user_data['password'] = password
    matric_no = context.user_data['matricNo']
    password = context.user_data['password']
    await update.message.reply_text("Password received. Signing in to FUNAAB portal...")
    # sign in backend code here
    try:
        login_response = sign_in(matric_no, password)
        if login_response == None:
            await update.message.reply_text(f'An error occured while signing in: Ensure your matric no and password is correct. Enter your matric number again.')
            return MATRIC
    except Exception as e:
        await update.message.reply_text(f'An error occured: {str(e)}. Try to enter your matric number and password again.')
        return MATRIC
    await update.message.reply_text('Signed in successfully ✅ ')
    await update.message.reply_text("What level result do you want to check?. e.g 200")
    context.user_data['login_resp'] = login_response
    return LEVEL

# validate and store level of reult to be cjecke
async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = update.message.text
    if not (level.isdigit() and 100 <= int(level) <= 800):
        await update.message.reply_text("Invald level. Enter a level betwen 100 - 800")
        return LEVEL
    
    # store level
    context.user_data['level'] = level
    reply_keybd = [['first', 'second']]
    markup = ReplyKeyboardMarkup(reply_keybd, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"Alright, {level} level. What semeter?", reply_markup=markup)
    return SEMESTER

#validates and storee semester of result to be checked
async def semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    semester = update.message.text
    if not semester in ('first', 'second'):
        await update.message.reply_text("Invald semseter. It must be either first or second")
        return SEMESTER
    # store semester
    context.user_data['semester'] = semester
    await update.message.reply_text(f"Retrieving result...")

    # get results code here
    level = context.user_data['level']
    semester = context.user_data['semester']
    login_response = context.user_data['login_resp']
    try:
        response_content = get_result(level, semester, login_response)
        if response_content:
            file_name = f"{level} level {semester} semester result.pdf"
            file = BytesIO(response_content)
            await update.message.reply_document(document=file, filename=file_name)
            await update.message.reply_text(f" Here is your {level} level {semester} semester result. Thanks for chatting with me.")

    except LookupError as e:
        await update.message.reply_text(f"An error occured {str(e)}")
    return ConversationHandler.END

#provides help to the user by listing avaiable commands
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start: To get started")

# log error info
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f'Update {update} caused error {context.error}')

# cancels process
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Process cancelled")
    return ConversationHandler.END
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def main():
    # starts a session
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            MATRIC: [MessageHandler(filters.TEXT & (~filters.COMMAND), matric_no)],
            PASSWORD: [MessageHandler(filters.TEXT & (~filters.COMMAND), password)],
            LEVEL: [MessageHandler(filters.TEXT & (~filters.COMMAND), level)],
            SEMESTER: [MessageHandler(filters.TEXT & (~filters.COMMAND), semester)],
        },

        fallbacks=[CommandHandler('cancel', cancel)],
    )


    # Commands
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', help))
    app.add_handler(CommandHandler('cancel', cancel))
    app.add_handler(MessageHandler(filters.TEXT, echo))
          
    # Error
    app.add_error_handler(error)
    print('polling...')
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
import os
import logging
import threading
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

# --- 1. CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# --- 2. AI SETUP (Flash Model) ---
genai.configure(api_key=API_KEY)
# Ab nayi key hai, to Flash model use karenge (Ye sabse fast hai)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. WEB SERVER (Render Alive Rakhne Ke Liye) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running! 🚀", 200

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- 4. BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='lang_hi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')]
    ]
    await update.message.reply_text("Choose Language / भाषा चुनें:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('lang_'):
        context.user_data['l'] = 'hi' if query.data == 'lang_hi' else 'en'
        btn = [[InlineKeyboardButton("Science Fact 🧪", callback_data='fact')]]
        text = "विषय चुनें:" if context.user_data['l'] == 'hi' else "Select Topic:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == 'fact':
        lang = context.user_data.get('l', 'hi')
        prompt = "Give a rare science fact. WRITE ONLY IN HINDI DEVANAGARI SCRIPT." if lang == 'hi' else "Give a rare science fact in English."
        
        try:
            await query.edit_message_text("Thinking... 🤔")
            response = model.generate_content(prompt)
            await query.edit_message_text(response.text)
        except Exception as e:
            await query.edit_message_text(f"Error: {str(e)}")

# --- 5. MAIN EXECUTION ---
if __name__ == '__main__':
    # Server start
    threading.Thread(target=run_web).start()
    
    # Bot start
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()
    

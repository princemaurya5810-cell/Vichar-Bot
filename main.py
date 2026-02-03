import os
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)

# --- CONFIG ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# Configure AI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='lang_hi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')]
    ]
    await update.message.reply_text("Choose Language / भाषा चुनें:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('lang_'):
        lang = 'hi' if query.data == 'lang_hi' else 'en'
        context.user_data['l'] = lang
        btns = [[InlineKeyboardButton("Science Fact 🧪", callback_data='get_fact')]]
        text = "विषय चुनें:" if lang == 'hi' else "Select Topic:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif query.data == 'get_fact':
        user_lang = context.user_data.get('l', 'hi')
        
        # Explicit Prompt for Devanagari
        if user_lang == 'hi':
            prompt = "Give a rare science fact. WRITE ONLY IN HINDI DEVANAGARI SCRIPT. NO ENGLISH LETTERS."
            waiting = "🤔 AI विचार कर रहा है..."
        else:
            prompt = "Give a rare science fact in English."
            waiting = "🤔 AI is thinking..."

        await query.edit_message_text(waiting)

        try:
            response = model.generate_content(prompt)
            await query.edit_message_text(response.text)
        except Exception as e:
            # Ye line bata degi ki abhi bhi error kyun hai
            await query.edit_message_text(f"❌ ERROR: {str(e)}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
    

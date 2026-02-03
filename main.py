import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import google.generativeai as genai

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Model update: Hum 'gemini-1.5-flash' use karenge jo zyada fast hai
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='lang_hindi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_english')],
        [InlineKeyboardButton("Hinglish ✍️", callback_data='lang_hinglish')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Vichar AI mein aapka swagat hai! Bhasha chunein:", reply_markup=reply_markup)

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('lang_'):
        lang = data.split('_')[1]
        context.user_data['lang'] = lang
        keyboard = [
            [InlineKeyboardButton("Science 🧪", callback_data='topic_science')],
            [InlineKeyboardButton("Politics ⚖️", callback_data='topic_politics')],
            [InlineKeyboardButton("Philosophy 🧘", callback_data='topic_philosophy')]
        ]
        await query.edit_message_text(text=f"Bhasha: {lang.capitalize()}\nTopic chunein:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('topic_'):
        topic = data.split('_')[1]
        user_lang = context.user_data.get('lang', 'hindi')
        
        # Hindi ke liye Devanagari script ka strict instruction
        if user_lang == 'hindi':
            lang_instruction = "Write strictly in Hindi language using Devanagari script (हिंदी लिपि)."
        elif user_lang == 'hinglish':
            lang_instruction = "Write in Hinglish (Hindi words in English script)."
        else:
            lang_instruction = "Write in English."

        prompt = f"{lang_instruction} Give a deep and rare {topic} fact. Keep it engaging."
        await query.edit_message_text(text="🤔 AI Vichar kar raha hai...")

        try:
            response = model.generate_content(prompt)
            # Response ko Markdown mein dikhana
            await query.edit_message_text(text=f"✨ **Vichar** ✨\n\n{response.text}", parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Error: {e}")
            await query.edit_message_text(text="❌ Error: AI se sampark nahi ho paya. API Key ya Model check karein.")

if __name__ == '__main__':
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_interaction))
    application.run_polling()
        

import os
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Initialize Gemini with the correct model string
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initial language selection."""
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='lang_hi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose your language / अपनी भाषा चुनें:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all button interactions."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # Handle Language Selection
    if data.startswith('lang_'):
        user_lang = 'hindi' if data == 'lang_hi' else 'english'
        context.user_data['language'] = user_lang
        
        keyboard = [
            [InlineKeyboardButton("Science 🧪", callback_data='topic_sci')],
            [InlineKeyboardButton("Politics ⚖️", callback_data='topic_pol')],
            [InlineKeyboardButton("Philosophy 🧘", callback_data='topic_phi')]
        ]
        text = "Select a topic:" if user_lang == 'english' else "एक विषय चुनें:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Handle Topic Selection
    elif data.startswith('topic_'):
        topic_map = {'topic_sci': 'Science', 'topic_pol': 'Politics', 'topic_phi': 'Philosophy'}
        topic_name = topic_map.get(data)
        user_lang = context.user_data.get('language', 'hindi')

        # Language-specific prompting
        if user_lang == 'hindi':
            prompt = f"Give a rare fact about {topic_name}. WRITE ONLY IN HINDI USING DEVANAGARI SCRIPT. NO ENGLISH ALPHABETS."
            wait_msg = "🤔 AI विचार कर रहा है..."
        else:
            prompt = f"Give a rare fact about {topic_name}. WRITE ONLY IN ENGLISH."
            wait_msg = "🤔 AI is thinking..."

        await query.edit_message_text(wait_msg)

        try:
            response = model.generate_content(prompt)
            header = "✨ **Vichar (Fact)** ✨" if user_lang == 'english' else "✨ **विचार (तथ्य)** ✨"
            await query.edit_message_text(f"{header}\n\n{response.text}", parse_mode='Markdown')
        except Exception as e:
            # Detailed error reporting
            await query.edit_message_text(f"❌ ASLI ERROR: {str(e)}")

if __name__ == '__main__':
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()


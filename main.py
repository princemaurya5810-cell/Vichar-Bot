import os
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Model initialization
genai.configure(api_key=GEMINI_API_KEY)
# Corrected model string to fix 404 error
model = genai.GenerativeModel('gemini-1.5-flash')

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting and language selection buttons."""
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='lang_hi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "Welcome to Vichar AI! Please select your language.\n\n"
        "Vichar AI में आपका स्वागत है! कृपया अपनी भाषा चुनें:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes button presses for language and topics."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # Language selection logic
    if data.startswith('lang_'):
        selected_lang = 'hindi' if data == 'lang_hi' else 'english'
        context.user_data['language'] = selected_lang
        
        keyboard = [
            [InlineKeyboardButton("Science 🧪", callback_data='topic_sci')],
            [InlineKeyboardButton("Politics ⚖️", callback_data='topic_pol')],
            [InlineKeyboardButton("Philosophy 🧘", callback_data='topic_phi')]
        ]
        
        prompt_text = "Select a topic:" if selected_lang == 'english' else "एक विषय चुनें:"
        await query.edit_message_text(prompt_text, reply_markup=InlineKeyboardMarkup(keyboard))

    # Topic selection logic
    elif data.startswith('topic_'):
        topic_map = {'topic_sci': 'Science', 'topic_pol': 'Politics', 'topic_phi': 'Philosophy'}
        topic_name = topic_map.get(data)
        user_lang = context.user_data.get('language', 'hindi')

        # Constructing the AI Prompt based on language choice
        if user_lang == 'hindi':
            instruction = "Provide a rare and interesting fact. WRITE ONLY IN HINDI USING DEVANAGARI SCRIPT. NO ENGLISH LETTERS."
        else:
            instruction = "Provide a rare and interesting fact. WRITE ONLY IN ENGLISH."

        full_prompt = f"{instruction}\nTopic: {topic_name}\nFact:"
        
        waiting_text = "🤔 AI is thinking..." if user_lang == 'english' else "🤔 AI विचार कर रहा है..."
        await query.edit_message_text(waiting_text)

        try:
            response = model.generate_content(full_prompt)
            result_header = "✨ **Vichar (Fact)** ✨" if user_lang == 'english' else "✨ **विचार (तथ्य)** ✨"
            await query.edit_message_text(f"{result_header}\n\n{response.text}", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"AI Connection Error: {e}")
            await query.edit_message_text(f"❌ ERROR: {str(e)}")

# --- MAIN EXECUTION ---

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logger.critical("Missing Environment Variables! Check Render Settings.")
    else:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Adding Handlers
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        logger.info("Bot is running...")
        application.run_polling()


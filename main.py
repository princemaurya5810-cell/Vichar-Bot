import os
import logging
import threading
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

# --- 1. SETUP LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# --- 2. SMART MODEL SELECTOR ---
genai.configure(api_key=API_KEY)

def get_best_model():
    """Google se puchta hai ki kaunsa model available hai."""
    try:
        logger.info("Finding available models...")
        # Available models ki list nikalo
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        logger.info(f"Found models: {available_models}")

        # Priority 1: Flash (Fastest)
        for m in available_models:
            if 'flash' in m and '1.5' in m:
                logger.info(f"Selected Model: {m}")
                return genai.GenerativeModel(m)
        
        # Priority 2: Pro (Standard)
        for m in available_models:
            if 'pro' in m and '1.5' in m:
                logger.info(f"Selected Model: {m}")
                return genai.GenerativeModel(m)

        # Priority 3: Old Pro
        for m in available_models:
            if 'gemini-pro' in m:
                logger.info(f"Selected Model: {m}")
                return genai.GenerativeModel(m)

        # Fallback: Jo bhi pehla mile
        if available_models:
            logger.info(f"Selected Fallback Model: {available_models[0]}")
            return genai.GenerativeModel(available_models[0])
            
    except Exception as e:
        logger.error(f"Error listing models: {e}")
    
    # Agar sab fail ho jaye, to default try karo
    return genai.GenerativeModel('gemini-1.5-flash-latest')

# Initialize Model
model = get_best_model()

# --- 3. FLASK SERVER ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is Alive! ✅", 200

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    app_flask.run(host='0.0.0.0', port=port)

# --- 4. BOT LOGIC ---

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
        
        if user_lang == 'hi':
            prompt = "Give a rare science fact. WRITE ONLY IN HINDI DEVANAGARI SCRIPT."
            waiting = "🤔 AI विचार कर रहा है..."
        else:
            prompt = "Give a rare science fact in English."
            waiting = "🤔 AI is thinking..."

        try:
            await query.edit_message_text(waiting)
            response = model.generate_content(prompt)
            if response.text:
                await query.edit_message_text(response.text)
            else:
                await query.edit_message_text("❌ Empty Response")
        except Exception as e:
            await query.edit_message_text(f"❌ ERROR: {str(e)}")

# --- 5. RUN ---
if __name__ == '__main__':
    t = threading.Thread(target=run_web_server)
    t.start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
                

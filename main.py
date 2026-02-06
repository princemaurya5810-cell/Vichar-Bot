import os
import logging
import threading
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

# --- 1. SETUP LOGGING & CONFIGURATION ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Get API keys from Environment Variables (Render/System)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# --- 2. GEMINI AI SETUP ---
genai.configure(api_key=API_KEY)

# Setting up the model
# Using try-except block to fallback to 'gemini-pro' if 'flash' fails
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    logging.warning(f"Flash model failed, switching to Pro. Error: {e}")
    model = genai.GenerativeModel('gemini-pro')

# --- 3. FLASK SERVER (Required for Render) ---
# This dummy server keeps the Render service alive by listening on a port.
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is Alive and Running! ✅", 200

def run_web_server():
    # Render automatically assigns a PORT. Default to 5000 if not found.
    port = int(os.environ.get('PORT', 5000))
    app_flask.run(host='0.0.0.0', port=port)

# --- 4. BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message with two buttons: Hindi and English."""
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='lang_hi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')]
    ]
    await update.message.reply_text(
        "Choose Language / भाषा चुनें:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks (Language selection & Fact generation)."""
    query = update.callback_query
    await query.answer()
    
    # CASE 1: User selected a language
    if query.data.startswith('lang_'):
        lang = 'hi' if query.data == 'lang_hi' else 'en'
        
        # Save user preference in context
        context.user_data['l'] = lang
        
        # Show the "Get Fact" button in the selected language
        btns = [[InlineKeyboardButton("Science Fact 🧪", callback_data='get_fact')]]
        text = "विषय चुनें:" if lang == 'hi' else "Select Topic:"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

    # CASE 2: User clicked "Science Fact"
    elif query.data == 'get_fact':
        # Retrieve the saved language (default to Hindi if missing)
        user_lang = context.user_data.get('l', 'hi')
        
        # Set prompt based on language
        if user_lang == 'hi':
            prompt = "Give a rare science fact. WRITE ONLY IN HINDI DEVANAGARI SCRIPT. NO ENGLISH LETTERS."
            waiting_text = "🤔 AI विचार कर रहा है..."
        else:
            prompt = "Give a rare science fact in English."
            waiting_text = "🤔 AI is thinking..."

        # Show waiting text first
        try:
            await query.edit_message_text(waiting_text)
            
            # Call Gemini API
            response = model.generate_content(prompt)
            
            if response.text:
                await query.edit_message_text(response.text)
            else:
                await query.edit_message_text("❌ Received empty response from AI.")
                
        except Exception as e:
            # Display error to user for debugging
            await query.edit_message_text(f"❌ ERROR: {str(e)}")

# --- 5. MAIN EXECUTION ---
if __name__ == '__main__':
    # Step A: Start the Flask Web Server in a separate thread
    # This prevents Render from killing the bot.
    t = threading.Thread(target=run_web_server)
    t.start()

    # Step B: Start the Telegram Bot
    print("Bot is starting polling...")
    app = Application.builder().token(TOKEN).build()
    
    # Add Handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start Polling (Blocking call)
    app.run_polling()

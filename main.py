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

# Get API keys from Environment Variables
TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('GEMINI_API_KEY')

# --- 2. GEMINI AI SETUP ---
genai.configure(api_key=API_KEY)

# ✅ FIX: Humne model badal kar 'gemini-pro' kar diya hai.
# Ye purana model hai lekin ye hamesha chalta hai aur error nahi deta.
model = genai.GenerativeModel('gemini-pro')

# --- 3. FLASK SERVER (Render ke liye zaroori) ---
# Ye dummy server hai taaki Render app ko band na kare.
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is Alive! (Running on gemini-pro) ✅", 200

def run_web_server():
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
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()
    
    # CASE 1: Language Selection
    if query.data.startswith('lang_'):
        lang = 'hi' if query.data == 'lang_hi' else 'en'
        context.user_data['l'] = lang
        
        btns = [[InlineKeyboardButton("Science Fact 🧪", callback_data='get_fact')]]
        text = "विषय चुनें:" if lang == 'hi' else "Select Topic:"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

    # CASE 2: Fact Generation
    elif query.data == 'get_fact':
        user_lang = context.user_data.get('l', 'hi')
        
        # Prompt Logic
        if user_lang == 'hi':
            prompt = "Give a rare science fact. WRITE ONLY IN HINDI DEVANAGARI SCRIPT."
            waiting_text = "🤔 AI विचार कर रहा है..."
        else:
            prompt = "Give a rare science fact in English."
            waiting_text = "🤔 AI is thinking..."

        # Show waiting message
        try:
            await query.edit_message_text(waiting_text)
            
            # Call Gemini API
            response = model.generate_content(prompt)
            
            if response.text:
                await query.edit_message_text(response.text)
            else:
                await query.edit_message_text("❌ Empty response.")
                
        except Exception as e:
            await query.edit_message_text(f"❌ ERROR: {str(e)}")

# --- 5. MAIN EXECUTION ---
if __name__ == '__main__':
    # Step A: Start Flask Server (Background me)
    t = threading.Thread(target=run_web_server)
    t.start()

    # Step B: Start Telegram Bot
    print("Bot is starting polling with gemini-pro...")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    app.run_polling()

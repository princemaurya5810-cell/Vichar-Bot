import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import google.generativeai as genai

# --- CONFIG ---
# Ye values Render ke Environment Variables se aayengi
TOKEN = os.environ.get('TELEGRAM_TOKEN')
AI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini Setup
genai.configure(api_key=AI_KEY)
# Latest aur sabse fast model
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='l_hi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='l_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Vichar AI mein aapka swagat hai! Bhasha chunein:", reply_markup=reply_markup)

async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('l_'):
        context.user_data['lang'] = 'hindi' if query.data == 'l_hi' else 'english'
        btns = [
            [InlineKeyboardButton("Science 🧪", callback_data='t_sci')],
            [InlineKeyboardButton("Politics ⚖️", callback_data='t_pol')],
            [InlineKeyboardButton("Philosophy 🧘", callback_data='t_phi')]
        ]
        await query.edit_message_text("Topic chunein:", reply_markup=InlineKeyboardMarkup(btns))
    
    elif query.data.startswith('t_'):
        topic = query.data.split('_')[1]
        user_lang = context.user_data.get('lang', 'hindi')
        
        # Devanagari Instructions
        if user_lang == 'hindi':
            lang_instruction = "Write strictly in Hindi language using Devanagari script (हिंदी लिपि). Do not use English alphabets."
        else:
            lang_instruction = "Write in English."

        prompt = f"{lang_instruction} Give a deep and rare {topic} fact. Keep it engaging."
        await query.edit_message_text("🤔 AI Vichar kar raha hai...")

        try:
            # AI se response mangna
            response = model.generate_content(prompt)
            await query.edit_message_text(text=f"✨ **Vichar** ✨\n\n{response.text}", parse_mode='Markdown')
        except Exception as e:
            # Bot ab aapko asli error message dikhayega
            await query.edit_message_text(text=f"❌ ASLI ERROR: {str(e)}")

if __name__ == '__main__':
    if not TOKEN or not AI_KEY:
        print("Error: TOKEN ya API_KEY nahi mila! Check Environment Variables.")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CallbackQueryHandler(handle_interaction))
        print("Bot is starting...")
        app.run_polling()


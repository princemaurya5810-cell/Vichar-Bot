import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import google.generativeai as genai

# --- CONFIG ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
AI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini Setup
genai.configure(api_key=AI_KEY)
# Latest model name research ke mutabiq
model = genai.GenerativeModel('gemini-1.5-flash-latest')

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Hindi (देवनागरी) 🇮🇳", callback_data='l_hi')],
                [InlineKeyboardButton("English 🇺🇸", callback_data='l_en')]]
    await update.message.reply_text("Vichar AI: Bhasha chunein:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('l_'):
        context.user_data['l'] = 'hindi' if query.data == 'l_hi' else 'english'
        btns = [[InlineKeyboardButton("Science 🧪", callback_data='t_sci')],
                [InlineKeyboardButton("Philosophy 🧘", callback_data='t_phi')]]
        await query.edit_message_text("Topic chunein:", reply_markup=InlineKeyboardMarkup(btns))
    
    elif query.data.startswith('t_'):
        topic = query.data.split('_')[1]
        lang = context.user_data.get('l', 'hindi')
        
        # Strict Devanagari Instruction
        prompt = f"Give a rare {topic} fact. Language: {lang}. If Hindi, use ONLY Devanagari script."
        await query.edit_message_text("🤔 AI Vichar kar raha hai...")
        
        try:
            res = model.generate_content(prompt)
            await query.edit_message_text(f"✨ **Vichar** ✨\n\n{res.text}", parse_mode='Markdown')
        except Exception as e:
            # Bot ab aapko batayega ki problem kya hai
            await query.edit_message_text(f"❌ Asli Error: {str(e)}")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle))
    app.run_polling()

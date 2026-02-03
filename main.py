import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import google.generativeai as genai

# --- CONFIGURATION (Render se keys uthayega) ---
# Yahan humne os.environ use kiya hai taaki keys safe rahein
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8577400341:AAFbP35eA3ySY8OXrnTyBLDq7TyseceIdGI')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini Setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- FUNCTIONS ---

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data='lang_hindi')],
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_english')],
        [InlineKeyboardButton("Hinglish ✍️", callback_data='lang_hinglish')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✨ Welcome to Vichar AI! ✨\nKripya apni bhasha chunein / Please select your language:",
        reply_markup=reply_markup
    )

# 2. Interaction Handling
async def handle_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('lang_'):
        lang = data.split('_')[1]
        context.user_data['lang'] = lang
        
        keyboard = [
            [InlineKeyboardButton("Science Facts 🧪", callback_data='topic_science')],
            [InlineKeyboardButton("Politics & Myths ⚖️", callback_data='topic_politics')],
            [InlineKeyboardButton("Philosophy / Vichar 🧘", callback_data='topic_philosophy')],
            [InlineKeyboardButton("Daily Poll 📊", callback_data='topic_poll')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"✅ Language: **{lang.capitalize()}**\n\nAb ek topic chunein jispar aap AI se 'Vichar' chahte hain:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data.startswith('topic_'):
        topic = data.split('_')[1]
        user_lang = context.user_data.get('lang', 'hinglish')
        
        if topic == 'poll':
            await context.bot.send_poll(
                chat_id=query.message.chat_id,
                question="Kya aapko lagta hai ki digital media par disinformation ko roka ja sakta hai?",
                options=["Haan, bilkul", "Mushkil hai", "Nahi, impossible hai"],
                is_anonymous=False
            )
            return

        # Prompt Creation (Aapke suggestions ke hisaab se)
        prompt = f"Write a deep, engaging, and rare {topic} fact or thought in {user_lang}. " \
                 f"Ensure it promotes critical thinking and is neutral."

        await query.edit_message_text(text="🤖 Vichar AI soch raha hai... Ek pal rukye.")
        
        try:
            response = model.generate_content(prompt)
            final_text = f"✨ **{topic.capitalize()} Vichar ({user_lang})** ✨\n\n{response.text}"
            await query.edit_message_text(text=final_text, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Error: {e}")
            await query.edit_message_text(text="❌ Maaf kijiye, AI connect nahi ho pa raha. API Key check karein.")

# --- MAIN ---
if __name__ == '__main__':
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY nahi mili! Render settings mein check karein.")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_interaction))
    
    print("🚀 Vichar-Bot is LIVE and running...")
    application.run_polling()


from telegram import Update, ReactionTypeEmoji
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
import random

# ==================== IMPOSTAZIONI DI DEFAULT ====================
DEFAULT_MIN = 1
DEFAULT_MAX = 100

# 🔴 ID DEGLI ADMIN AUTORIZZATI
ADMIN_IDS = [6710922454, 7127377678, 1059198431, 6499718935, 5631411226]

EMOJI_WIN = "🎉"
EMOJI_HOT = "🔥"
EMOJI_COLD = "🐳"
EMOJI_WRONG = "🤔"
EMOJI_OUT = "🚫"

# ================================================================

# Dizionario per i giochi attivi
games = {}

def get_game(chat_id):
    if chat_id not in games:
        games[chat_id] = {
            'target_number': None,
            'starter_id': None,
            'starter_name': None,
            'min_number': DEFAULT_MIN,
            'max_number': DEFAULT_MAX
        }
    return games[chat_id]

def is_admin(user_id: int) -> bool:
    """Verifica se l'utente è un admin autorizzato"""
    return user_id in ADMIN_IDS

async def set_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /set per cambiare il range - SOLO ADMIN"""
    user = update.message.from_user
    
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Solo gli admin possono usare questo comando!")
        return
    
    chat_id = update.message.chat_id
    game = get_game(chat_id)
    
    try:
        if context.args and len(context.args) >= 1:
            new_max = int(context.args[0])
            if new_max < 10:
                await update.message.reply_text("⚠️ Il numero massimo deve essere almeno 10!")
                return
            if new_max > 10000:
                await update.message.reply_text("⚠️ Massimo consentito: 10000!")
                return
            
            game['max_number'] = new_max
            await update.message.reply_text(
                f"✅ Range impostato: *{game['min_number']}-{game['max_number']}*\n"
                f"Usa /start per iniziare!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "📊 *Imposta il range*\n\n"
                f"Attuale: {game['min_number']}-{game['max_number']}\n\n"
                "Uso: `/set [numero]`\n"
                "Esempio: `/set 500`",
                parse_mode="Markdown"
            )
    except ValueError:
        await update.message.reply_text("❌ Inserisci un numero valido!\nEsempio: /set 200")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start per iniziare il gioco - SOLO ADMIN"""
    user = update.message.from_user
    
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Solo gli admin possono avviare il gioco!")
        return
    
    chat_id = update.message.chat_id
    game = get_game(chat_id)
    
    min_num = game['min_number']
    max_num = game['max_number']
    
    game['target_number'] = random.randint(min_num, max_num)
    game['starter_id'] = user.id
    game['starter_name'] = user.first_name
    
    target = game['target_number']
    
    private_sent = False
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"🎯 Numero: *{target}*\n"
                 f"📊 Range: {min_num}-{max_num}",
            parse_mode="Markdown"
        )
        private_sent = True
    except Exception:
        pass
    
    info_text = (
        f"🎮 *NUOVA PARTITA!*\n\n"
        f"👤 Organizzatore: {user.first_name}\n"
        f"📊 Range: *{min_num}-{max_num}*\n\n"
        f"*Reazioni:*\n"
        f"🎉 = Esatto!\n"
        f"🔥 = Vicino (±10)\n"
        f"🐳 = Lontano\n\n"
        f"_Scrivi un numero!_"
    )
    
    if not private_sent:
        info_text += "\n\n⚠️ L'organizzatore deve avviarmi in privato!"
    
    await update.message.reply_text(info_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    game = get_game(chat_id)
    
    if game['target_number'] is None:
        return
    
    if not update.message or not update.message.text:
        return
    
    user_msg = update.message.text.strip()
    min_num = game['min_number']
    max_num = game['max_number']
    
    if not user_msg.isdigit():
        await update.message.set_reaction([ReactionTypeEmoji(EMOJI_WRONG)])
        return
    
    number = int(user_msg)
    target = game['target_number']
    
    if number < min_num or number > max_num:
        await update.message.set_reaction([ReactionTypeEmoji(EMOJI_OUT)])
        return
    
    distance = abs(number - target)
    
    if number == target:
        await update.message.set_reaction([ReactionTypeEmoji(EMOJI_WIN)])
        winner_name = update.message.from_user.first_name
        
        await update.message.reply_text(
            f"🎉 *{winner_name}* ha indovinato! Era *{target}*!",
            parse_mode="Markdown"
        )
        game['target_number'] = None
        
    elif distance <= 10:
        await update.message.set_reaction([ReactionTypeEmoji(EMOJI_HOT)])
    else:
        await update.message.set_reaction([ReactionTypeEmoji(EMOJI_COLD)])

def main():
    TOKEN = "8678862114:AAE_zywPiKH0X2JeJHOjbt7KQKXKen5McDc"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("set", set_range))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot avviato!")
    print("📝 Comandi: /start | /set [numero]")
    print("🔒 Accesso limitato agli admin!")
    application.run_polling()

if __name__ == '__main__':
    main()
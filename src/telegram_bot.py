
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from src.config import env_vars

API_URL = "http://localhost:8000"  # Change if deployed elsewhere

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Clôture la dernière conversation active si elle existe
    resp = requests.get(f"{API_URL}/conversation/active/{user_id}")
    last_cid = resp.json().get("conversation_id")
    if last_cid:
        requests.post(f"{API_URL}/conversation/{last_cid}/close", json={"telegram_id": user_id})
    # Démarre une nouvelle conversation
    resp = requests.post(f"{API_URL}/conversation/start", json={"telegram_id": user_id})
    conversation_id = resp.json().get("conversation_id")
    context.user_data["conversation_id"] = conversation_id
    await update.message.reply_text("Bonjour ! Nouvelle conversation démarrée. Pose-moi une question !")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_message = update.message.text
    # Récupérer la dernière conversation active ou en démarrer une
    resp = requests.get(f"{API_URL}/conversation/active/{user_id}")
    conversation_id = resp.json().get("conversation_id")
    if not conversation_id:
        resp = requests.post(f"{API_URL}/conversation/start", json={"telegram_id": user_id})
        conversation_id = resp.json().get("conversation_id")
    # 1. Envoyer la question à l'API /chat
    try:
        chat_resp = requests.get(f"{API_URL}/chat", params={"question": user_message})
        chat_resp.raise_for_status()
        answer = chat_resp.json().get("answer", {}).get("S", "Je n'ai pas compris.")
    except Exception as e:
        answer = "Erreur lors de la communication avec l'IA."
        logging.error(f"Erreur API chat: {e}")
    # 2. Sauvegarder la conversation
    try:
        requests.post(f"{API_URL}/conversation/message", json={
            "telegram_id": user_id,
            "conversation_id": conversation_id,
            "user_message": user_message,
            "bot_response": answer
        })
    except Exception as e:
        logging.error(f"Erreur sauvegarde conversation: {e}")
    # 3. Répondre à l'utilisateur
    await update.message.reply_text(answer)

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    # Clôture la dernière conversation active
    resp = requests.get(f"{API_URL}/conversation/active/{user_id}")
    conversation_id = resp.json().get("conversation_id")
    if conversation_id:
        requests.post(f"{API_URL}/conversation/{conversation_id}/close", json={"telegram_id": user_id})
        await update.message.reply_text("Conversation clôturée. Tapez /start pour en ouvrir une nouvelle.")
    else:
        await update.message.reply_text("Aucune conversation active à clôturer.")

def main():
    token = env_vars.TELEGRAM_BOT_TOKEN
    if not token or token == "your_telegram_bot_token_here":
        raise RuntimeError("TELEGRAM_BOT_TOKEN manquant dans .env !")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("close", close))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot Telegram démarré. Appuyez sur Ctrl+C pour arrêter.")
    app.run_polling()

if __name__ == "__main__":
    main()

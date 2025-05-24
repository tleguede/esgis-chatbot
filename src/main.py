from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from mangum import Mangum
import json, boto3
from mistralai.client import MistralClient

from .config import env_vars


from .utils import Utils

class ConversationMessageIn(BaseModel):
    telegram_id: str
    conversation_id: str
    user_message: str
    bot_response: str
    timestamp: str = None

class ConversationMessageOut(BaseModel):
    conversation_id: str
    user_message: str
    bot_response: str
    timestamp: str

api_key = env_vars.MISTRAL_API_KEY
if not api_key or api_key.strip() == "":
    raise RuntimeError("MISTRAL_API_KEY is missing or empty. Please set it in your environment variables or .env file.")
model = "mistral-small-latest"
client = MistralClient(api_key=api_key)



@asynccontextmanager
async def app_lifespan(application: FastAPI):
    Utils.log_info("Starting the application")
    yield



app = FastAPI(
    title="ChatBot API",
    description="Chatbot API description",
    version="1.0.0",
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Redirige le root vers la documentation interactive
from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/chat")
async def chat(question: str):
    try:
        chat_response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": question,
                },
            ]
        )
        print("chat_response:", chat_response)
        response = {
            "id": {
                "S": f"{getattr(chat_response, 'id', 'no_id')}",
            },
            "question": {
                "S": f"{question}",
            },
            "answer": {
                "S": f"{getattr(chat_response.choices[0].message, 'content', 'no_content') if hasattr(chat_response, 'choices') and chat_response.choices else 'no_choices'}",
            }
        }
        Utils.insert_data(response)
        return response
    except Exception as e:
        import traceback
        print("Exception in /chat endpoint:", e)
        traceback.print_exc()
        return {"error": str(e)}


# --- Conversation Endpoints (placés après la création de app) ---
@app.post("/conversation/message", response_model=None)
async def save_conversation_message(data: ConversationMessageIn):
    """
    Enregistre un message utilisateur + réponse bot dans DynamoDB.
    """
    try:
        Utils.save_conversation_message(
            telegram_id=data.telegram_id,
            conversation_id=data.conversation_id,
            user_message=data.user_message,
            bot_response=data.bot_response,
            timestamp=data.timestamp
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/history/{telegram_id}")
async def get_conversation_history(telegram_id: str, limit: int = 20):
    """
    Récupère l'historique des messages pour un utilisateur (par son Telegram ID).
    """
    try:
        items = Utils.get_conversation_history(telegram_id, limit)
        # Convert DynamoDB format to plain dict
        history = []
        for item in items:
            history.append({
                "conversation_id": item.get("conversation_id", {}).get("S", ""),
                "user_message": item.get("user_message", {}).get("S", ""),
                "bot_response": item.get("bot_response", {}).get("S", ""),
                "timestamp": item.get("timestamp", {}).get("S", ""),
            })
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



async def chats():
    # Get al chats here
    return {}

handler = Mangum(app)

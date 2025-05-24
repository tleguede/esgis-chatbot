from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from mangum import Mangum
import json, boto3
from mistralai.client import MistralClient

from .config import env_vars


from .utils import Utils

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


@app.get("/")
async def root():
    return {"msg": "Hello World"}


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

async def chats():
    # Get al chats here
    return {}

handler = Mangum(app)

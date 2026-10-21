from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.routes.chat import router as chat_router
from src.backend.routes.predict import router as predict_router

app = FastAPI(title="Health Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(predict_router)

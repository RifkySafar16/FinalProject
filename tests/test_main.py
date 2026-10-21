from fastapi.testclient import TestClient

from src.backend import main
from src.backend.routes import chat


client = TestClient(main.app)


def test_chat_returns_rag_response(monkeypatch):
    def fake_ask(question):
        assert question == "Apa isi panduan?"
        return {
            "answer": "Jawaban. ⚠️ Ini bukan nasihat medis.",
            "sources": [{"page": 84, "snippet": "Informasi dari panduan."}],
        }

    monkeypatch.setattr(chat, "ask", fake_ask)

    response = client.post("/chat", json={"question": "Apa isi panduan?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Jawaban. ⚠️ Ini bukan nasihat medis.",
        "sources": [{"page": 84, "snippet": "Informasi dari panduan."}],
    }


def test_chat_rejects_blank_question():
    response = client.post("/chat", json={"question": "   "})

    assert response.status_code == 422


def test_chat_rejects_question_shorter_than_three_characters():
    response = client.post("/chat", json={"question": " a "})

    assert response.status_code == 422


def test_chat_rejects_question_longer_than_500_characters():
    response = client.post("/chat", json={"question": "a" * 501})

    assert response.status_code == 422


def test_chat_allows_cors_preflight_from_frontend():
    response = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

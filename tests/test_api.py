import pytest
from fastapi.testclient import TestClient
from src.backend.main import app

# Membuat client untuk menguji FastAPI secara lokal tanpa perlu menjalankan server
client = TestClient(app)

# ==========================================
# TES UNTUK ENDPOINT /predict (Machine Learning)
# ==========================================

def test_predict_valid_input():
    """Menguji API prediksi dengan data yang valid (Profil B pada laporan)."""
    payload = {
        "age": 58, "sex": 1, "cp": 4, "trestbps": 150, "chol": 260,
        "fbs": 0, "restecg": 0, "thalach": 153, "exang": 1,
        "oldpeak": 0.8, "slope": 1, "ca": 0, "thal": 3
    }
    response = client.post("/predict", json=payload)
    
    # Harus mengembalikan status 200 (OK)
    assert response.status_code == 200
    data = response.json()
    
    # Memastikan response memiliki field yang diharapkan
    assert "prediction" in data
    assert "probability_presence" in data
    assert isinstance(data["probability_presence"], float)

def test_predict_invalid_input_type():
    """Menguji API prediksi dengan tipe data yang salah (harus 422 Unprocessable Entity)."""
    payload = {
        "age": "lima puluh delapan",  # Sengaja salah tipe data (string, harusnya int)
        "sex": 1, "cp": 4, "trestbps": 150, "chol": 260,
        "fbs": 0, "restecg": 0, "thalach": 153, "exang": 1,
        "oldpeak": 0.8, "slope": 1, "ca": 0, "thal": 3
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_predict_missing_field():
    """Menguji API prediksi jika ada field yang kurang (harus 422)."""
    payload = {
        "age": 58, "sex": 1
        # Field lain sengaja dihilangkan
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


# ==========================================
# TES UNTUK ENDPOINT /chat (RAG System)
# ==========================================

def test_chat_valid_question():
    """Menguji API chat dengan pertanyaan yang valid (3-500 karakter)."""
    payload = {"question": "Apa saja faktor risiko penyakit jantung yang bisa diubah?"}
    
    # Catatan: Jika Groq API key belum diset di environment lokal, 
    # test ini bisa memakan waktu lama atau error 500. 
    # Namun jika .env sudah diset, ini akan mengembalikan 200.
    response = client.post("/chat", json=payload)
    
    # Jika berhasil, harus 200
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "Ini bukan nasihat medis" in data["answer"] # Memastikan disclaimer ada

def test_chat_question_too_short():
    """Menguji API chat dengan pertanyaan kurang dari 3 karakter (harus 422)."""
    payload = {"question": "Hi"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422

def test_chat_question_too_long():
    """Menguji API chat dengan pertanyaan lebih dari 500 karakter (harus 422)."""
    payload = {"question": "A" * 501} # Membuat string 501 karakter
    response = client.post("/chat", json=payload)
    assert response.status_code == 422
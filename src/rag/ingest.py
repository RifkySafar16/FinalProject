import os
import re
import pickle
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

def build_documents():
    pdf_path = os.getenv("PDF_PATH")
    persist_file = "vectorstore/docs.pkl" # Kita simpan sebagai file pickle

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    cleaned_documents = []
    for doc in documents:
        page_num = doc.metadata.get("page", 0) + 1 # Halaman dimulai dari 0
        
        # LEWATI 15 halaman pertama dan 15 halaman terakhir (biasanya kata pengantar & pustaka)
        if page_num < 15 or page_num > (len(documents) - 15):
            continue

        text = doc.page_content
        text = re.sub(r'\s+', ' ', text)
        
        if "References" in text or "Bibliography" in text or len(text.strip()) < 300:
            continue
            
        doc.page_content = text
        cleaned_documents.append(doc)

    print(f"Total halaman bersih: {len(cleaned_documents)}") # Cek apakah jumlahnya masuk akal

    # Potong teks
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(cleaned_documents)
    print(f"Total potongan teks: {len(chunks)}")

    # Simpan ke file
    os.makedirs("vectorstore", exist_ok=True)
    with open(persist_file, "wb") as f:
        pickle.dump(chunks, f)
        
    print(f"Dokumen berhasil disimpan di {persist_file}")

if __name__ == "__main__":
    build_documents()
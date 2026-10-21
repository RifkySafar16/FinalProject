import os
import pickle
from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from src.rag.prompts import RAG_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Prompt khusus untuk menerjemahkan pertanyaan ke bahasa Inggris
TRANSLATE_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="Translate the following Indonesian health question into English keywords. Only output the English translation, nothing else.\nQuestion: {question}\nEnglish:"
)

def get_rag_chain():
    persist_file = "vectorstore/docs.pkl"
    if not os.path.exists(persist_file):
        raise FileNotFoundError("File docs.pkl tidak ditemukan. Jalankan ingest.py dulu!")
        
    with open(persist_file, "rb") as f:
        chunks = pickle.load(f)

    # KITA AMBIL LEBIH BANYAK (k=8) agar peluang dapat teks yang benar lebih besar
    retriever = BM25Retriever.from_documents(chunks)
    retriever.k = 8 

    llm = ChatGroq(
        model="openai/gpt-oss-120b", 
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": RAG_PROMPT}
    )
    return qa_chain, llm

def ask(question: str) -> dict:
    chain, llm = get_rag_chain()
    
    # 1. Terjemahkan pertanyaan ke bahasa Inggris agar cocok dengan PDF
    translate_chain = TRANSLATE_PROMPT | llm | StrOutputParser()
    english_query = translate_chain.invoke({"question": question})
    
    # 2. Cari menggunakan kata kunci bahasa Inggris
    result = chain.invoke(english_query) 
    
    sources = [
        {"page": doc.metadata.get("page", "?"), "snippet": doc.page_content[:200]}
        for doc in result["source_documents"]
    ]
    
    return {
        "answer": result["result"],
        "sources": sources
    }

if __name__ == "__main__":
    res = ask("Apa arti kolesterol tinggi menurut panduan ini?")
    print("\n--- JAWABAN AI ---")
    print(res["answer"])
    print("\n--- SUMBER ---")
    for s in res["sources"]:
        print(f"Hal {s['page']}: {s['snippet']}...")
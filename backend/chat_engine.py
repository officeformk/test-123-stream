# backend/chat_engine.py
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains import RetrievalQA

def load_retriever():
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "resources", "Kent Repertory 1.pdf")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
        
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load_and_split()

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             "resources", "faiss_index_homeo")
                             
    if os.path.exists(index_path):
        db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    else:
        db = FAISS.from_documents(docs, embeddings)
        db.save_local(index_path)
    
    return db.as_retriever()

retriever = load_retriever()
llm = OllamaLLM(model="mistral")
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

def run_query(query, chat_history):
    result = qa_chain.invoke({"query": query})
    return result["result"]
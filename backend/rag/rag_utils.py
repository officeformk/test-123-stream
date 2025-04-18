# RAG logic with FAISS & LangChain
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains import RetrievalQA

PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                       "resources", "Kent Repertory 1.pdf")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index_homeo")

def build_vector_index():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF file not found at {PDF_PATH}")
    
    loader = PyMuPDFLoader(PDF_PATH)
    docs = loader.load_and_split()
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(INDEX_PATH)
    print("✅ FAISS index built and saved.")

def get_retriever():
    if not os.path.exists(INDEX_PATH):
        build_vector_index()
    
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return db.as_retriever()

def initialize_qa_chain():
    retriever = get_retriever()
    llm = OllamaLLM(model="mistral")
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

qa_chain = initialize_qa_chain()

def get_rag_response(query: str) -> str:
    try:
        result = qa_chain.invoke({"query": query})
        return result["result"]
    except Exception as e:
        return f"Error processing query: {str(e)}"

# Ensure the function is available for import
__all__ = ['get_rag_response']
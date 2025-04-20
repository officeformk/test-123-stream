# # RAG logic with FAISS & LangChain
# import os
# from dotenv import load_dotenv
# from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_community.vectorstores import FAISS
# import openai  # Import OpenAI directly
# from langchain.chains import RetrievalQA
# from langchain.chat_models import ChatOpenAI

# # Load environment variables
# load_dotenv()

# PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
#                        "resources", "Kent Repertory 1.pdf")
# INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index_homeo")

# def build_vector_index():
#     if not os.path.exists(PDF_PATH):
#         raise FileNotFoundError(f"PDF file not found at {PDF_PATH}")
    
#     loader = PyMuPDFLoader(PDF_PATH)
#     docs = loader.load_and_split()

#     # Use OpenAI embeddings
#     def get_openai_embeddings(texts):
#         response = openai.Embedding.create(
#             model="text-embedding-ada-002",
#             input=texts
#         )
#         return [embedding['embedding'] for embedding in response['data']]

#     embeddings = get_openai_embeddings([doc.page_content for doc in docs])
#     db = FAISS.from_documents(docs, embeddings)
#     db.save_local(INDEX_PATH)
#     print("✅ FAISS index built and saved.")

# def get_retriever():
#     if not os.path.exists(INDEX_PATH):
#         build_vector_index()
    
#     # Load documents again to generate embeddings
#     loader = PyMuPDFLoader(PDF_PATH)
#     docs = loader.load_and_split()

#     # Use OpenAI embeddings
#     def get_openai_embeddings(texts):
#         response = openai.Embedding.create(
#             model="text-embedding-ada-002",
#             input=texts
#         )
#         return [embedding['embedding'] for embedding in response['data']]

#     embeddings = get_openai_embeddings([doc.page_content for doc in docs])
#     db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
#     return db.as_retriever()

# def initialize_qa_chain():
#     retriever = get_retriever()
#     llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=os.getenv("OPENAI_API_KEY"))
#     return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# qa_chain = initialize_qa_chain()

# def get_rag_response(query: str) -> str:
#     try:
#         result = qa_chain({"query": query})
#         return result.get("result", "No response generated.")
#     except Exception as e:
#         return f"Error processing query: {str(e)}"

# # Ensure the function is available for import
# __all__ = ['get_rag_response']
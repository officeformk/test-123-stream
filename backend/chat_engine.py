import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
import logging
import traceback

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OpenAI API key is not set. Please check your environment variables.")
else:
    logger.debug("✅ OpenAI API key loaded.")

# Embedding function (1536-d OpenAI)
embedding_function = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=api_key
)

def load_retriever():
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "Kent Repertory 1.pdf")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")

    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load_and_split()
    logger.debug(f"Loaded {len(docs)} documents from PDF for embedding.")

    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "faiss_index_homeo")

    if os.path.exists(index_path):
        db = FAISS.load_local(index_path, embedding_function, allow_dangerous_deserialization=True)
        logger.debug("Loaded FAISS index from local storage.")
    else:
        db = FAISS.from_documents(docs, embedding_function)
        db.save_local(index_path)
        logger.debug("Created new FAISS index and saved locally.")

    return db.as_retriever()

retriever = load_retriever()
llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=api_key)

# Use Conversational chain to keep chat history
qa_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever)

def run_query(query, chat_history):
    try:
        logger.debug(f"Running query: {query}")

        # Convert chat_history from [{"role": ..., "content": ...}] to [(question, answer), ...]
        formatted_history = []
        for i in range(0, len(chat_history) - 1, 2):
            if chat_history[i]["role"] == "user" and chat_history[i+1]["role"] == "assistant":
                formatted_history.append((chat_history[i]["content"], chat_history[i+1]["content"]))

        # Run the query with history
        result = qa_chain.invoke({
            "question": query,
            "chat_history": formatted_history
        })

        response_text = result.get("answer", "No response generated.")
        logger.debug(f"LLM response: {response_text}")
        return response_text

    except Exception as e:
        logger.error("❌ Error processing query", exc_info=True)
        return "An error occurred while processing your request. Please try again."
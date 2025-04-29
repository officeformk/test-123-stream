import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
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

# Embedding function
embedding_function = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=api_key
)

# Load Retriever
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

# Define Prompts for Two Modes
clarification_mode_system_prompt = """
You are a highly skilled AI assistant for certified homeopathy doctors, trained in classical homeopathy (Kent's Repertory) {context}.

Rules:
- Ask clarifying questions only if critical information is missing.
- Maximum two clarifications per symptom.
- Build naturally without repeating or re-asking already answered points.
- Suggest 1–3 best remedies once enough information is available.
- Use short, clinical, respectful tone.

When suggesting remedies:
- Use bullet points and explain briefly.
- Trust previous answers fully without reconfirming.

Focus on saving doctor's time by quickly moving to remedies once information is sufficient.
"""

remedies_mode_system_prompt = """
You are a highly skilled AI assistant for certified homeopathy doctors, trained in classical homeopathy (Kent's Repertory) {context}. 

Rules:
- Do not ask any clarifying questions, even if some information is missing.
- Directly suggest 1–3 best remedies based on available information.
- Use short, clinical, respectful tone.
- Use bullet points and briefly explain why each remedy is selected.
- Focus on quickly suggesting the remedies without any further questioning.

Proceed even if information seems incomplete.
"""

# Create Custom Prompt Templates
def create_prompt(mode="clarification"):
    if mode == "clarification":
        system_prompt = clarification_mode_system_prompt
    else:
        system_prompt = remedies_mode_system_prompt

    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template("{question}")
    ])

# Initialize LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=api_key, temperature=0.0)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Main Query Handler
def run_query(query, chat_history, mode="remedies"):
    try:
        logger.debug(f"Running query: {query} | Mode: {mode}")

        # Convert chat_history from [{"role": ..., "content": ...}] to memory
        existing_messages = memory.chat_memory.messages if hasattr(memory.chat_memory, 'messages') else []

        if not existing_messages:
            logger.debug("Memory is empty. Updating memory from passed chat_history...")

            if not isinstance(chat_history, list):
                logger.warning(f"Chat history is not a list. Got: {type(chat_history)}. Defaulting to empty list.")
                chat_history = []

            for msg in chat_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] == "user":
                        memory.chat_memory.add_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        memory.chat_memory.add_ai_message(msg["content"])
                else:
                    logger.warning(f"Unexpected message format: {msg}")
        else:
            logger.debug("Memory already populated. Skipping chat_history injection.")

        # Create QA Chain with correct prompt based on mode
        custom_prompt = create_prompt(mode)
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": custom_prompt}
        )

        # Slightly enhance the query if mode is clarification
        enhanced_query = query
        if mode == "clarification":
            enhanced_query += "\n\n(Note: If enough information is available now, proceed to suggest best remedies without further questions.)"

        result = qa_chain.invoke({
            "question": enhanced_query,
        })

        response_text = result.get("answer", "No response generated.")
        logger.debug(f"LLM response: {response_text}")
        return response_text

    except Exception as e:
        logger.error("❌ Error processing query", exc_info=True)
        return "An error occurred while processing your request. Please try again."
import logging
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.llms.openai import OpenAI

# Enable logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_documents(directory, description="Loading documents"):
    """Load and return documents from a directory, including subdirectories."""
    try:
        reader = SimpleDirectoryReader(
            directory,
            recursive=True,  # Scan all subdirectories
            required_exts=[".md", ".txt", ".json", ".csv"],  # Include chat log formats
        )
        docs = reader.load_data()
        logging.info(f"✅ Successfully loaded {len(docs)} documents from {directory}")
        return docs
    except Exception as e:
        logging.error(f"❌ Error loading {description} from {directory}: {e}")
        return []

# Load documentation and chat logs
logging.info("🔍 Loading documentation and chat logs...")
docs = load_documents("/Users/m/Documents/GitHub/ergodocs/docs", "documentation")
chats = load_documents("/Users/m/Documents/GitHub/discord_summariser_ai/guild/important", "chat logs")

# Ensure data is loaded
if not docs and not chats:
    logging.error("🚨 No data loaded! Exiting...")
    exit(1)

# Use GPT-4-turbo with controlled response behavior
llm = OpenAI(model="gpt-4-turbo", temperature=0.5)
service_context = ServiceContext.from_defaults(llm=llm)

# Create index with chat and documentation combined
logging.info("⚡ Creating VectorStoreIndex...")
index = VectorStoreIndex.from_documents(docs + chats)

# Create query engine with better retrieval strategy
query_engine = index.as_query_engine(service_context=service_context, similarity_top_k=15)

logging.info("✅ Query engine ready! Type your questions below (or type 'exit' to quit).")

while True:
    query = input("\n🔍 Ask a question (or type 'exit' to quit): ")
    if query.lower() == "exit":
        logging.info("👋 Exiting interactive mode.")
        break
    
    # Use a structured prompt to ensure correct formatting
    formatted_query = f"""
    You are an expert in ErgoScript. Analyze the chat logs and documentation to provide insights.
    - If asked for an FAQ, extract the **most common user questions from chat logs** that are **not well answered** in the documentation.
    - If asked to improve the documentation, generate **a well-structured, detailed, Markdown-formatted update**.
    - If asked to write a new page, generate a **fully structured Markdown documentation page** with headings, examples, and explanations.
    - Always ensure responses are **formatted properly in Markdown**.
    
    User Question:
    {query}
    """

    response = query_engine.query(formatted_query)
    print("\n📌 Response:\n", response)

import streamlit as st
from ai_cgi_branding import StreamlitUIService
from loguru import logger

from src.core.config import Config
from src.core.env import get_env_settings
from src.core.logger import configure_logger
from src.llm.ai import do_ai

# Configure logger once to capture logs into files and terminal
if "logger_configured" not in st.session_state:
    st.session_state.logger_configured = True
    configure_logger(log_dir="logs", rotation="10 MB", retention="100 days")

# Load config from config.yaml
ENV = get_env_settings()
config = Config.from_yaml("configs/config.yaml")
logger.debug(f"Loaded configuration: {config.general.name}")

# Set page title and styling
st.set_page_config(page_title=config.general.name)
ui_service = StreamlitUIService()
ui_service.load_css()
logger.debug("UI service initialized and CSS loaded")

# Sidebar branding
logo_bytes = ui_service.get_logo(config.general.logo_type)
st.sidebar.image(logo_bytes, width=200)

# Model selection UI (based on config value)
model_name = st.sidebar.selectbox(
    "Model name",
    [config.llm.model_name, "claude-3-haiku", "llama-3.2-1b"],
)
logger.debug(f"User selected model: {model_name}")


# Chat interface
st.header(config.general.name)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    logger.info("Initialized new chat session")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to ask?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    response = do_ai(prompt=prompt, model_name=model_name)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    logger.debug(f"Chat history now contains {len(st.session_state.messages)} messages")

# RAG Settings Display
st.sidebar.markdown("**RAG Settings**")
with st.sidebar.expander("View RAG Configuration", expanded=False):
    st.write(f"**Embedding Model:** {config.llm.embedding_model_name}")
    st.write(f"**Chunk Size:** {config.llm.chunk_size}")
    st.write(f"**Retrieval K:** {config.llm.retrieval_k}")
    st.write(f"**Rerank:** {'✅' if config.llm.rerank else '❌'}")
    if hasattr(config, "paths") and hasattr(config.paths, "rag_index"):
        st.write(f"**RAG Index Path:** {config.paths.rag_index}")

# Show how to access secrets in the environment variables
st.sidebar.markdown("---")
if st.sidebar.button("Show API Key"):
    logger.warning("Displaying API Key in sidebar for demonstration purposes")
    st.sidebar.write(f"Running in {ENV.general.env} environment")
    st.sidebar.write(f"Azure OpenAI API Key (masked): {ENV.azure.openai_api_key}")
    st.sidebar.write(
        f"Azure OpenAI API Key (raw): {ENV.azure.openai_api_key.get_secret_value()}"
    )

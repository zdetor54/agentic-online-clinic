import datetime
import os

import requests
import streamlit as st
from ai_cgi_branding import StreamlitUIService
from loguru import logger
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout

from ui.patient_page import show_patient_page

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PATIENTS_ENDPOINT = f"{API_BASE_URL}/patients/"
HTTP_STATUS_CREATED = 201

# Set page title and styling
st.set_page_config(page_title="Patient Management")
ui_service = StreamlitUIService()
ui_service.load_css()
logo_bytes = ui_service.get_logo("colour")
st.markdown(
    """
    <style>
    .stButton > button[data-testid="baseButton-primary"] {
        background-color: rgb(227, 25, 55) !important;
        border-color: rgb(227, 25, 55) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.sidebar.image(logo_bytes, width=200)
st.sidebar.markdown("# Patient Management Application")
st.sidebar.write("""
    The application is a production-style system used to manage core domain data and user workflows through a web interface.
    It exposes functionality through structured data models, forms, and APIs (CRUD), while also storing information across multiple related records and unstructured fields.
    Current access patterns rely on manual UI interaction or narrowly scoped endpoints.
""")
st.sidebar.markdown("---")
st.sidebar.markdown("""
    An agentic layer that translates natural language requests into:
    - **write (CRUD)** operations against the existing application stack and
    - **read (query/RAG)** and
    will enhance the patient management experience without altering core business logic
""")

# --- Initialize session state ---
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "agent_response" not in st.session_state:
    st.session_state.agent_response = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = False

# --- Top Navigation ---
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("📋 Manual Mode", use_container_width=True):
        st.session_state.pop("active_patient_id", None)
        st.query_params.clear()
        st.rerun()


with col_nav2:
    if st.button("🤖 Agent Mode", use_container_width=True):
        st.session_state.pop("active_patient_id", None)
        st.query_params.clear()
        st.query_params["agent"] = "1"
        st.rerun()


st.markdown("---")

# --- ROUTING: Check query params and render appropriate page ---

patient_id = st.query_params.get("patient_id")

if isinstance(patient_id, list):
    patient_id = patient_id[0]

# persist patient id across reruns
if patient_id:
    st.session_state["active_patient_id"] = patient_id

agent_mode = st.query_params.get("agent")
edit_mode = st.query_params.get("edit")
create_mode = st.query_params.get("create")

patient_id = st.session_state.get("active_patient_id")

if patient_id:
    editable = edit_mode == "1"
    show_patient_page(int(patient_id), editable=editable)
    st.stop()

elif create_mode == "1":
    # ============= CREATE PATIENT PAGE =============
    st.markdown(
        '<h2 style="text-align: center;">Create New Patient</h2>',
        unsafe_allow_html=True,
    )

    with st.form("patient_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1))
        gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
        phone = st.text_input("Phone Number")
        email = st.text_input("Email")
        address = st.text_area("Address")

        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        with col2:
            submitted = st.form_submit_button(
                "Create Patient", use_container_width=True, type="primary"
            )

        if cancel:
            st.query_params.clear()
            st.rerun()

        if submitted:
            if not first_name or not last_name or not gender:
                st.error("First name, last name, and gender are required.")
            else:
                payload = {
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "date_of_birth": dob.isoformat(),
                    "gender": gender,
                    "phone": phone.strip() if phone else None,
                    "email": email.strip() if email else None,
                    "address": address.strip() if address else None,
                    "created_by": "streamlit_user",
                }
                try:
                    response = requests.post(PATIENTS_ENDPOINT, json=payload, timeout=5)
                    if response.status_code == HTTP_STATUS_CREATED:
                        patient_data = response.json()
                        st.success(
                            f"✅ Patient {first_name} {last_name} created successfully!"
                        )
                        logger.info(
                            f"Created patient ID {patient_data['id']}: {first_name} {last_name}"
                        )
                        st.query_params.clear()
                        st.query_params["patient_id"] = str(patient_data["id"])
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Failed to create patient: {response.json().get('detail', response.text)}"
                        )
                        logger.error(f"API error {response.status_code}")
                except RequestsConnectionError:
                    st.error(
                        "❌ Cannot connect to API server. Please ensure the FastAPI server is running."
                    )
                    logger.error("Failed to connect to API server")
                except Timeout:
                    st.error("❌ Request timed out. Please try again.")
                    logger.error("API request timed out")
                except Exception as e:
                    st.error(f"❌ Error: {e!s}")
                    logger.exception("Unexpected error during patient creation")

elif agent_mode == "1":
    # ============= AGENT MODE PAGE =============
    st.markdown(
        "<h2 style='text-align: center;'>Agentic Assistant</h2>",
        unsafe_allow_html=True,
    )

    # Mode selector
    col_toggle, col_clear = st.columns([3, 1])
    with col_toggle:
        chat_mode = st.toggle(
            "💬 Chat Mode (Conversation Memory)",
            value=st.session_state.chat_mode,
            help="Enable to maintain conversation context across multiple messages",
        )
        st.session_state.chat_mode = chat_mode

    with col_clear:
        if (
            chat_mode
            and st.session_state.chat_history
            and st.button("🗑️ Clear Chat", use_container_width=True)
        ):
            st.session_state.chat_history = []
            st.session_state.agent_response = None
            st.rerun()

    # Model selection
    col_model = st.columns([1])[0]
    with col_model:
        model_choice = st.selectbox(
            "Model",
            ["gpt-5-nano", "gpt-4.1-mini", "gpt-4", "gpt-3.5-turbo"],
            help="Select Azure OpenAI deployment",
        )

    st.markdown("---")

    if chat_mode:
        # ============= CHAT MODE =============
        # Display conversation history
        if st.session_state.chat_history:
            st.markdown("### 💬 Conversation")
            chat_container = st.container(height=400)
            with chat_container:
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(
                            f"<div style='text-align: right; padding: 8px; margin: 5px 0; background-color: #e3f2fd; border-radius: 10px;'>"
                            f"<strong>You:</strong> {msg['content']}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div style='padding: 8px; margin: 5px 0; background-color: #f5f5f5; border-radius: 10px;'>"
                            f"<strong>🤖 Assistant:</strong> {msg['content']}</div>",
                            unsafe_allow_html=True,
                        )

        # Chat input positioned right after conversation container (using st.chat_input)
        user_message = st.chat_input("Message: (Ask a question or make a request...)")
        if user_message:
            if user_message.strip():
                with st.spinner("🔄 Processing..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/agent/process",
                            json={
                                "prompt": user_message,
                                "model_name": model_choice,
                                "message_history": st.session_state.chat_history,
                            },
                            timeout=30,
                        )
                        if response.status_code == 200:
                            result = response.json()
                            # Update chat history from response
                            if result.get("message_history"):
                                st.session_state.chat_history = result[
                                    "message_history"
                                ]
                            st.rerun()
                        else:
                            st.error(f"❌ Agent failed: {response.text}")
                    except RequestsConnectionError:
                        st.error(
                            "❌ Cannot connect to API server. Ensure FastAPI is running."
                        )
                        logger.error("Failed to connect to API server")
                    except Timeout:
                        st.error("❌ Request timed out. Try again.")
                        logger.error("Agent request timed out")
                    except Exception as e:
                        st.error(f"❌ Error: {e!s}")
                        logger.exception("Agent request error")
            else:
                st.warning("Please enter a message.")

        # Show token usage stats if available
        if st.session_state.chat_history:
            total_messages = len(st.session_state.chat_history)
            st.caption(
                f"💬 {total_messages} messages in conversation | "
                f"Context: ~{total_messages * 100} tokens (approximate)"
            )

    else:
        # ============= SINGLE-SHOT MODE (Original) =============

        user_prompt = st.text_area(
            "Enter your request, signle shot, in natural language:",
            height=100,
            placeholder="e.g., Find patient with phone 555-1234\ne.g., Create patient Sarah Johnson, DOB 1985-03-20, Female",
        )

        if st.button("Submit", use_container_width=True, type="primary"):
            if user_prompt.strip():
                with st.spinner("🔄 Agent is processing your request..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/agent/process",
                            json={"prompt": user_prompt, "model_name": model_choice},
                            timeout=30,
                        )
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.agent_response = result
                        else:
                            st.error(f"❌ Agent failed: {response.text}")
                            st.session_state.agent_response = None
                    except RequestsConnectionError:
                        st.error(
                            "❌ Cannot connect to API server. Ensure FastAPI is running."
                        )
                        logger.error("Failed to connect to API server")
                    except Timeout:
                        st.error("❌ Request timed out. Try again.")
                        logger.error("Agent request timed out")
                    except Exception as e:
                        st.error(f"❌ Error: {e!s}")
                        logger.exception("Agent request error")
            else:
                st.warning("Please enter a prompt.")

        if st.session_state.agent_response:
            st.markdown("### 📝 Agent Response")
            response = st.session_state.agent_response
            st.success(response.get("message", "Request processed successfully."))
            if response.get("data"):
                st.json(response["data"])

else:
    # ============= SEARCH PAGE (default) =============
    st.markdown(
        "<h2 style='text-align: center;'>Patient Search</h2>", unsafe_allow_html=True
    )
    search_name = st.text_input("Search by Name")
    search_phone = st.text_input("Search by Phone")

    col1, col2 = st.columns([1, 1])
    with col1:
        search_btn = st.button("Search", use_container_width=True)
    with col2:
        if st.button("Create New Patient", use_container_width=True):
            st.query_params.clear()
            st.query_params["create"] = "1"
            st.rerun()

    if search_btn:
        try:
            params = {}
            if search_name:
                params["name"] = search_name
            if search_phone:
                params["phone"] = search_phone
            resp = requests.get(PATIENTS_ENDPOINT, params=params, timeout=5)
            if resp.status_code == 200:
                st.session_state.search_results = resp.json()
            else:
                st.error(f"Search failed: {resp.text}")
                st.session_state.search_results = []
        except Exception as e:
            st.error(f"Error searching patients: {e!s}")
            st.session_state.search_results = []

    if st.session_state.search_results:
        st.markdown("### Search Results")
        for patient in st.session_state.search_results:
            label = f"{patient['first_name']} {patient['last_name']}"
            url = f"?patient_id={patient['id']}"
            st.markdown(
                f'<a href="{url}">{label} - id:{patient["id"]}</a>',
                unsafe_allow_html=True,
            )
    elif search_btn:
        st.info("No matching patients found.")

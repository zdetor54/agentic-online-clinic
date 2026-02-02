import datetime
import os

import requests
import streamlit as st
from ai_cgi_branding import StreamlitUIService
from loguru import logger
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PATIENTS_ENDPOINT = f"{API_BASE_URL}/patients/"
HTTP_STATUS_CREATED = 201


# Set page title and styling
st.set_page_config(page_title="Patient Management")
ui_service = StreamlitUIService()
ui_service.load_css()
logo_bytes = ui_service.get_logo("colour")  # Use your config if needed
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
if "view" not in st.session_state:
    st.session_state.view = "search"  # 'search', 'create', 'view', 'agent'
if "selected_patient_id" not in st.session_state:
    st.session_state.selected_patient_id = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "agent_response" not in st.session_state:
    st.session_state.agent_response = None

# --- Top Navigation ---
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button(
        "📋 Manual Mode",
        use_container_width=True,
        type="primary"
        if st.session_state.view in ["search", "create", "view", "edit"]
        else "secondary",
    ):
        st.session_state.view = "search"
        st.rerun()
with col_nav2:
    if st.button(
        "🤖 Agent Mode",
        use_container_width=True,
        type="primary" if st.session_state.view == "agent" else "secondary",
    ):
        st.session_state.view = "agent"
        st.rerun()

st.markdown("---")

# --- Agent View ---
if st.session_state.view == "agent":
    st.markdown(
        "<h2 style='text-align: center;'>🤖 Agentic Assistant</h2>",
        unsafe_allow_html=True,
    )
    st.info(
        "💡 Try: 'Show me patient John Doe' or 'Create a new patient named Jane Smith born on 1990-05-15'"
    )

    # Model selection
    col_prompt, col_model = st.columns([3, 1])
    with col_model:
        model_choice = st.selectbox(
            "Model",
            ["gpt-4.1-mini", "gpt-4", "gpt-3.5-turbo"],
            help="Select Azure OpenAI deployment",
        )

    user_prompt = st.text_area(
        "Enter your request in natural language:",
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

    # Display agent response
    if st.session_state.agent_response:
        st.markdown("### 📝 Agent Response")
        response = st.session_state.agent_response
        st.success(response.get("message", "Request processed successfully."))

        if response.get("data"):
            st.json(response["data"])

# --- Search View ---
elif st.session_state.view == "search":
    st.markdown(
        "<h2 style='text-align: center;'>Patient Search</h2>", unsafe_allow_html=True
    )
    search_name = st.text_input("Search by Name")
    search_phone = st.text_input("Search by Phone")

    col1, col2 = st.columns([1, 1])
    with col1:
        search_btn = st.button("Search", use_container_width=True)
    with col2:
        create_btn = st.button("Create New Patient", use_container_width=True)

    if create_btn:
        st.session_state.view = "create"
        st.session_state.selected_patient_id = None
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

    # Display search results (persisted in session state)
    if st.session_state.search_results:
        st.markdown("### Search Results")
        for patient in st.session_state.search_results:
            label = f"{patient['first_name']} {patient['last_name']} ({patient.get('phone', 'No phone')})"
            if st.button(
                label, key=f"patient_{patient['id']}", use_container_width=True
            ):
                st.session_state.view = "view"
                st.session_state.selected_patient_id = patient["id"]
                st.rerun()
    elif search_btn:
        st.info("No matching patients found.")

# --- Create Patient View ---
elif st.session_state.view == "create":
    st.markdown(
        '<h2 style="text-align: center;">Create New Patient</h2>',
        unsafe_allow_html=True,
    )

    if st.button("← Back to Search"):
        st.session_state.view = "search"
        st.rerun()

    with st.form("patient_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1))
        gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
        phone = st.text_input("Phone Number")
        email = st.text_input("Email")
        address = st.text_area("Address")
        submitted = st.form_submit_button("Create Patient")

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
                            f"Created patient ID {patient_data.get('id')}: {first_name} {last_name}"
                        )
                        st.session_state.view = "view"
                        st.session_state.selected_patient_id = patient_data.get("id")
                        st.rerun()
                    else:
                        error_detail = response.json().get("detail", response.text)
                        st.error(f"❌ Failed to create patient: {error_detail}")
                        logger.error(
                            f"API error {response.status_code}: {error_detail}"
                        )
                except RequestsConnectionError:
                    st.error(
                        "❌ Cannot connect to API server. Please ensure the FastAPI server is running."
                    )
                    logger.error("Failed to connect to API server")
                except Timeout:
                    st.error("❌ Request timed out. Please try again.")
                    logger.error("API request timed out")
                except (ValueError, RuntimeError, KeyError) as e:
                    st.error(f"❌ An unexpected error occurred: {e!s}")
                    logger.exception("Unexpected error during patient creation")

# --- View Patient Details ---
elif st.session_state.view == "view" and st.session_state.selected_patient_id:
    col_back, col_edit = st.columns([1, 1])
    with col_back:
        if st.button("← Back to Search", use_container_width=True):
            st.session_state.view = "search"
            st.rerun()

    try:
        resp = requests.get(
            f"{PATIENTS_ENDPOINT}{st.session_state.selected_patient_id}", timeout=5
        )
        if resp.status_code == 200:
            patient = resp.json()
            st.markdown(
                f"<h3>Patient Details: {patient['first_name']} {patient['last_name']}</h3>",
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                st.text_input("First Name", value=patient["first_name"], disabled=True)
                st.text_input("Last Name", value=patient["last_name"], disabled=True)
                st.text_input(
                    "Date of Birth", value=patient["date_of_birth"], disabled=True
                )
                st.text_input("Gender", value=patient["gender"], disabled=True)
            with col2:
                st.text_input("Phone", value=patient.get("phone", ""), disabled=True)
                st.text_input("Email", value=patient.get("email", ""), disabled=True)
                st.text_area(
                    "Address",
                    value=patient.get("address", ""),
                    disabled=True,
                    height=100,
                )
        else:
            st.error(f"Patient not found: {resp.text}")
            if st.button("Return to Search"):
                st.session_state.view = "search"
                st.rerun()
    except Exception as e:
        st.error(f"Error loading patient: {e!s}")
        if st.button("Return to Search"):
            st.session_state.view = "search"
            st.rerun()

    with col_edit:
        if st.button("Edit Patient", use_container_width=True):
            st.session_state.view = "edit"
            st.rerun()

# --- Edit Patient ---
elif st.session_state.view == "edit" and st.session_state.selected_patient_id:
    if st.button("← Back to Patient Details"):
        st.session_state.view = "view"
        st.rerun()

    try:
        resp = requests.get(
            f"{PATIENTS_ENDPOINT}{st.session_state.selected_patient_id}", timeout=5
        )
        if resp.status_code == 200:
            patient = resp.json()
            st.markdown(
                f'<h2 style="text-align: center;">Edit Patient: {patient["first_name"]} {patient["last_name"]}</h2>',
                unsafe_allow_html=True,
            )

            with st.form("edit_patient_form"):
                first_name = st.text_input("First Name", value=patient["first_name"])
                last_name = st.text_input("Last Name", value=patient["last_name"])
                dob = st.date_input(
                    "Date of Birth",
                    value=datetime.datetime.strptime(
                        patient["date_of_birth"], "%Y-%m-%d"
                    ).date(),
                    min_value=datetime.date(1900, 1, 1),
                )
                gender = st.selectbox(
                    "Gender",
                    ["Male", "Female", "Other"],
                    index=["Male", "Female", "Other"].index(patient["gender"]),
                )
                phone = st.text_input("Phone Number", value=patient.get("phone", ""))
                email = st.text_input("Email", value=patient.get("email", ""))
                address = st.text_area("Address", value=patient.get("address", ""))
                submitted = st.form_submit_button("Update Patient")

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
                            "updated_by": "streamlit_user",
                        }
                        try:
                            response = requests.put(
                                f"{PATIENTS_ENDPOINT}{st.session_state.selected_patient_id}",
                                json=payload,
                                timeout=5,
                            )
                            if response.status_code == 200:
                                st.success(
                                    f"✅ Patient {first_name} {last_name} updated successfully!"
                                )
                                logger.info(
                                    f"Updated patient ID {st.session_state.selected_patient_id}: {first_name} {last_name}"
                                )
                                st.session_state.view = "view"
                                st.rerun()
                            else:
                                error_detail = response.json().get(
                                    "detail", response.text
                                )
                                st.error(f"❌ Failed to update patient: {error_detail}")
                                logger.error(
                                    f"API error {response.status_code}: {error_detail}"
                                )
                        except RequestsConnectionError:
                            st.error(
                                "❌ Cannot connect to API server. Please ensure the FastAPI server is running."
                            )
                            logger.error("Failed to connect to API server")
                        except Timeout:
                            st.error("❌ Request timed out. Please try again.")
                            logger.error("API request timed out")
                        except (ValueError, RuntimeError, KeyError) as e:
                            st.error(f"❌ An unexpected error occurred: {e!s}")
                            logger.exception("Unexpected error during patient update")
        else:
            st.error(f"Patient not found: {resp.text}")
            if st.button("Return to Search"):
                st.session_state.view = "search"
                st.rerun()
    except Exception as e:
        st.error(f"Error loading patient: {e!s}")
        if st.button("Return to Search"):
            st.session_state.view = "search"
            st.rerun()

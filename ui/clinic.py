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
                 Current access patterns rely on manual UI interaction or narrowly scoped endpoints.""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
                    An agentic layer that translates natural language requests into:
                    - **write (CRUD)** operations against the existing application stack and
                    - **read (query/RAG)** and

                    will enhance the patient management experience without altering core business logic""")

with st.form("patient_form"):
    st.markdown(
        '<h2 style="text-align: center;">Create New Patient</h2>',
        unsafe_allow_html=True,
    )
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1))
    gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")
    address = st.text_area("Address")
    submitted = st.form_submit_button("Create Patient")

    if submitted:
        # Validate required fields
        if not first_name or not last_name or not gender:
            st.error("First name, last name, and gender are required.")
        else:
            # Prepare payload for API
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
                # Call FastAPI endpoint
                response = requests.post(PATIENTS_ENDPOINT, json=payload, timeout=5)

                if response.status_code == HTTP_STATUS_CREATED:
                    patient_data = response.json()
                    st.success(
                        f"✅ Patient {first_name} {last_name} created successfully!"
                    )
                    logger.info(
                        f"Created patient ID {patient_data.get('id')}: {first_name} {last_name}"
                    )
                else:
                    error_detail = response.json().get("detail", response.text)
                    st.error(f"❌ Failed to create patient: {error_detail}")
                    logger.error(f"API error {response.status_code}: {error_detail}")

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

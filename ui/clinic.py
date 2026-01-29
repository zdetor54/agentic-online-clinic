import streamlit as st
from ai_cgi_branding import StreamlitUIService
from loguru import logger

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
                    - **read (query/RAG)** and
                    - **write (CRUD)** operations against the existing application stack,

                    will enhance the patient management experience without altering core business logic""")

with st.form("patient_form"):
    st.markdown(
        '<h2 style="text-align: center;">Create New Patient</h2>',
        unsafe_allow_html=True,
    )
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    dob = st.date_input("Date of Birth")
    gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")
    address = st.text_area("Address")
    submitted = st.form_submit_button("Create Patient")

    if submitted:
        st.success(f"Patient {first_name} {last_name} created!")
        st.write(
            {
                "First Name": first_name,
                "Last Name": last_name,
                "DOB": dob,
                "Gender": gender,
                "Phone": phone,
                "Email": email,
                "Address": address,
            }
        )
        logger.info(f"Created patient: {first_name} {last_name}")

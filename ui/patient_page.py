import datetime

import requests
import streamlit as st

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000")
PATIENTS_ENDPOINT = f"{API_BASE_URL}/patients/"
HTTP_STATUS_CREATED = 201


# ---------------------------
# Data access
# ---------------------------
def fetch_patient(patient_id: int) -> dict | None:
    try:
        resp = requests.get(f"{PATIENTS_ENDPOINT}{patient_id}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"Patient not found: {resp.text}")
    except Exception as exc:
        st.error(f"Error loading patient: {exc!s}")
    return None


# ---------------------------
# Render helpers
# ---------------------------
def render_readonly_patient(patient: dict, patient_id: int) -> None:
    patient_info_html = f"""
    <div style="font-size:1.1em;line-height:1.7;padding:1em 0;">
        <b>Name:</b> {patient.get("first_name", "")} {patient.get("last_name", "")}<br>
        <b>Date of Birth:</b> {patient.get("date_of_birth", "")}<br>
        <b>Gender:</b> {patient.get("gender", "")}<br>
        <b>Phone:</b> {patient.get("phone", "")}<br>
        <b>Email:</b> {patient.get("email", "")}<br>
        <b>Address:</b> {patient.get("address", "")}
    </div>
    """
    st.markdown(patient_info_html, unsafe_allow_html=True)

    if st.button("Edit Patient", use_container_width=True):
        # use experimental_set_query_params to avoid brittle mutation behavior
        st.query_params.clear()
        st.query_params["patient_id"] = str(patient_id)
        st.query_params["edit"] = "1"
        st.rerun()


def render_edit_patient(patient: dict, patient_id: int) -> None:
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

        if st.form_submit_button("Update Patient"):
            if not first_name or not last_name or not gender:
                st.error("First name, last name, and gender are required.")
                return

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
                resp = requests.put(
                    f"{PATIENTS_ENDPOINT}{patient_id}",
                    json=payload,
                    timeout=5,
                )
                if resp.status_code == 200:
                    st.success("✅ Patient updated successfully!")
                    st.query_params.clear()
                    st.query_params["patient_id"] = str(patient_id)

                    st.rerun()
                else:
                    st.error(resp.json().get("detail", resp.text))
            except Exception as exc:
                st.error(f"❌ Error: {exc!s}")


def render_create_patient() -> None:
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

        if st.form_submit_button("Create Patient"):
            if not first_name or not last_name or not gender:
                st.error("First name, last name, and gender are required.")
                return

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
                resp = requests.post(PATIENTS_ENDPOINT, json=payload, timeout=5)
                if resp.status_code == HTTP_STATUS_CREATED:
                    patient_id = resp.json().get("id")
                    st.success("✅ Patient created successfully!")
                    st.query_params.clear()
                    st.query_params["patient_id"] = str(patient_id)

                    st.rerun()
                else:
                    st.error(resp.json().get("detail", resp.text))
            except Exception as exc:
                st.error(f"❌ Error: {exc!s}")


# ---------------------------
# Public API (lint-clean)
# ---------------------------
def show_patient_page(patient_id: int | None = None, editable: bool = False) -> None:
    if patient_id is None:
        render_create_patient()
        return

    patient = fetch_patient(patient_id)
    if not patient:
        return

    if editable:
        render_edit_patient(patient, patient_id)
    else:
        render_readonly_patient(patient, patient_id)

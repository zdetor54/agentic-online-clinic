import datetime

import requests
import streamlit as st

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000")
PATIENTS_ENDPOINT = f"{API_BASE_URL}/patients/"
APPOINTMENTS_ENDPOINT = f"{API_BASE_URL}/appointments/"
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


def fetch_patient_appointments(patient_id: int) -> list[dict]:
    try:
        resp = requests.get(
            APPOINTMENTS_ENDPOINT,
            params={"patient_id": patient_id},
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        st.error(f"Error loading appointments: {exc!s}")
    return []


# ---------------------------
# Render helpers
# ---------------------------
def render_readonly_patient(patient: dict, patient_id: int) -> None:
    full_name = (
        f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
    )
    st.markdown(
        f"<h2 style='text-align: center;'>{full_name} &ndash; Patient Details</h2>",
        unsafe_allow_html=True,
    )
    patient_info_html = f"""
    <div style="font-size:1.1em;line-height:1.7;padding:1em 0;">
        <b>Date of Birth:</b> {patient.get("date_of_birth", "")}<br>
        <b>Gender:</b> {patient.get("gender", "")}<br>
        <b>Phone:</b> {patient.get("phone", "")}<br>
        <b>Email:</b> {patient.get("email", "")}<br>
        <b>Address:</b> {patient.get("address", "")}
    </div>
    """
    st.markdown(patient_info_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Edit Patient", use_container_width=True):
            st.query_params.clear()
            st.query_params["patient_id"] = str(patient_id)
            st.query_params["edit"] = "1"
            st.rerun()
    with col2:
        if st.button("Create Appointment", use_container_width=True, type="primary"):
            st.query_params.clear()
            st.query_params["page"] = "appointment"
            st.query_params["patient_id"] = str(patient_id)
            st.rerun()
    with col3:
        if st.button("Delete Patient", use_container_width=True, type="secondary"):
            try:
                resp = requests.delete(f"{PATIENTS_ENDPOINT}{patient_id}", timeout=5)
                if resp.status_code == 204:
                    st.success("✅ Patient deleted successfully!")
                    # Redirect to main clinic page
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"Failed to delete: {resp.text}")
            except Exception as exc:
                st.error(f"❌ Error deleting patient: {exc!s}")

    # Display appointments list
    st.markdown("---")
    st.markdown("### Appointments")
    appointments = fetch_patient_appointments(patient_id)

    if not appointments:
        st.info("No appointments found for this patient.")
    else:
        for appt in appointments:
            appt_date = appt.get("appointment_date", "N/A")
            appt_time = appt.get("appointment_start_time", "N/A")
            appt_reason = appt.get("appointment_reason", "No reason provided")
            appt_id = appt.get("id")

            col_appt1, col_appt2 = st.columns([3, 1])
            with col_appt1:
                st.markdown(f"**{appt_date}** at {appt_time}")
                st.markdown(f"*{appt_reason}*")
            with col_appt2:
                if st.button(
                    "View", key=f"view_appt_{appt_id}", use_container_width=True
                ):
                    st.query_params.clear()
                    st.query_params["page"] = "appointment"
                    st.query_params["appointment_id"] = str(appt_id)
                    st.rerun()
            st.markdown("---")


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

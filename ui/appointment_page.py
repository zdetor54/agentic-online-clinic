import datetime

import requests
import streamlit as st

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000")
APPOINTMENTS_ENDPOINT = f"{API_BASE_URL}/appointments/"
PATIENTS_ENDPOINT = f"{API_BASE_URL}/patients/"
HTTP_STATUS_CREATED = 201


# ---------------------------
# Data access
# ---------------------------
def fetch_appointment(appointment_id: int) -> dict | None:
    try:
        resp = requests.get(f"{APPOINTMENTS_ENDPOINT}{appointment_id}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"Appointment not found: {resp.text}")
    except Exception as exc:
        st.error(f"Error loading appointment: {exc!s}")
    return None


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
def render_readonly_appointment(appointment: dict, appointment_id: int) -> None:
    st.markdown(
        "<h2 style='text-align: center;'>Appointment Details</h2>",
        unsafe_allow_html=True,
    )

    # Fetch patient details
    patient_id = appointment.get("patient_id")
    patient = fetch_patient(patient_id) if patient_id else None
    patient_name = (
        f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        if patient
        else "Unknown"
    )

    # Build hyperlink to patient page
    patient_link = f"<a href='?page=patient&patient_id={patient_id}'>{patient_name}</a>"
    appointment_info_html = f"""
    <div style="font-size:1.1em;line-height:1.7;padding:1em 0;">
        <b>Patient:</b> {patient_link} (ID: {patient_id})<br>
        <b>Date:</b> {appointment.get("appointment_date", "")}<br>
        <b>Start Time:</b> {appointment.get("appointment_start_time", "N/A")}<br>
        <b>End Time:</b> {appointment.get("appointment_end_time", "N/A")}<br>
        <b>Reason:</b> {appointment.get("appointment_reason", "N/A")}
    </div>
    """
    st.markdown(appointment_info_html, unsafe_allow_html=True)

    if st.button("Edit Appointment", use_container_width=True):
        st.query_params.clear()
        st.query_params["appointment_id"] = str(appointment_id)
        st.query_params["edit"] = "1"
        st.rerun()


def render_edit_appointment(appointment: dict, appointment_id: int) -> None:
    patient_id = appointment["patient_id"]
    patient = fetch_patient(patient_id)
    patient_name = (
        f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        if patient
        else "Unknown"
    )

    patient_link = f"<a href='?page=patient&patient_id={patient_id}'>{patient_name}</a>"
    st.markdown(
        f"**Patient:** {patient_link} (ID: {patient_id})", unsafe_allow_html=True
    )

    def parse_time(tstr: str | None) -> datetime.time | None:
        if not tstr:
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.datetime.strptime(tstr, fmt).time()
            except ValueError:
                continue
        return None

    with st.form("edit_appointment_form"):
        appointment_date = st.date_input(
            "Appointment Date",
            value=datetime.datetime.strptime(
                appointment["appointment_date"], "%Y-%m-%d"
            ).date(),
            min_value=datetime.datetime.now().date(),
        )
        start_time = st.time_input(
            "Start Time",
            value=parse_time(appointment.get("appointment_start_time")),
        )
        end_time = st.time_input(
            "End Time",
            value=parse_time(appointment.get("appointment_end_time")),
        )
        reason = st.text_area(
            "Appointment Reason", value=appointment.get("appointment_reason", "")
        )

        submitted = st.form_submit_button("Update Appointment")
        if submitted:
            payload = {
                "patient_id": patient_id,
                "appointment_date": appointment_date.isoformat(),
                "appointment_start_time": start_time.strftime("%H:%M:%S")
                if start_time
                else None,
                "appointment_end_time": end_time.strftime("%H:%M:%S")
                if end_time
                else None,
                "appointment_reason": reason.strip() if reason else None,
                "updated_by": "streamlit_user",
            }

            try:
                resp = requests.put(
                    f"{APPOINTMENTS_ENDPOINT}{appointment_id}",
                    json=payload,
                    timeout=5,
                )
                if resp.status_code == 200:
                    st.success("✅ Appointment updated successfully!")
                    st.query_params.clear()
                    st.query_params["appointment_id"] = str(appointment_id)
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", resp.text))
            except Exception as exc:
                st.error(f"❌ Error: {exc!s}")


def render_create_appointment(patient_id: int) -> None:
    patient = fetch_patient(patient_id)
    if not patient:
        st.error("Patient not found")
        return

    patient_name = (
        f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
    )

    st.markdown(
        '<h2 style="text-align: center;">Create New Appointment</h2>',
        unsafe_allow_html=True,
    )
    patient_link = f"<a href='?page=patient&patient_id={patient_id}'>{patient_name}</a>"
    st.markdown(
        f"**Patient:** {patient_link} (ID: {patient_id})", unsafe_allow_html=True
    )

    with st.form("appointment_form"):
        appointment_date = st.date_input(
            "Appointment Date", min_value=datetime.datetime.now().date()
        )
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        reason = st.text_area("Appointment Reason")

        if st.form_submit_button("Create Appointment"):
            if not appointment_date:
                st.error("Appointment date is required.")
                return

            payload = {
                "patient_id": patient_id,
                "appointment_date": appointment_date.isoformat(),
                "appointment_start_time": start_time.strftime("%H:%M:%S")
                if start_time
                else None,
                "appointment_end_time": end_time.strftime("%H:%M:%S")
                if end_time
                else None,
                "appointment_reason": reason.strip() if reason else None,
                "created_by": "streamlit_user",
            }

            try:
                resp = requests.post(APPOINTMENTS_ENDPOINT, json=payload, timeout=5)
                if resp.status_code == HTTP_STATUS_CREATED:
                    appointment_id = resp.json().get("id")
                    st.success("✅ Appointment created successfully!")
                    st.query_params.clear()
                    st.query_params["appointment_id"] = str(appointment_id)
                    st.rerun()
                else:
                    st.error(resp.json().get("detail", resp.text))
            except Exception as exc:
                st.error(f"❌ Error: {exc!s}")


# ---------------------------
# Public API
# ---------------------------
def show_appointment_page(
    appointment_id: int | None = None,
    patient_id: int | None = None,
    editable: bool = False,
) -> None:
    if appointment_id is None and patient_id is not None:
        render_create_appointment(patient_id)
        return

    if appointment_id is None:
        st.error("Either appointment_id or patient_id must be provided")
        return

    appointment = fetch_appointment(appointment_id)
    if not appointment:
        return

    if editable:
        render_edit_appointment(appointment, appointment_id)
    else:
        render_readonly_appointment(appointment, appointment_id)

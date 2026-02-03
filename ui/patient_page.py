import datetime

import requests
import streamlit as st

API_BASE_URL = st.session_state.get("API_BASE_URL", "http://localhost:8000")
PATIENTS_ENDPOINT = f"{API_BASE_URL}/patients/"
HTTP_STATUS_CREATED = 201


def show_patient_page(patient_id: int | None = None, editable: bool = False) -> None:
    import streamlit as st

    if patient_id is None:
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
                        response = requests.post(
                            PATIENTS_ENDPOINT, json=payload, timeout=5
                        )
                        if response.status_code == HTTP_STATUS_CREATED:
                            patient_data = response.json()
                            st.success(
                                f"✅ Patient {first_name} {last_name} created successfully!"
                            )
                            st.query_params = {
                                "patient_id": str(patient_data.get("id"))
                            }
                            st.rerun()
                        else:
                            error_detail = response.json().get("detail", response.text)
                            st.error(f"❌ Failed to create patient: {error_detail}")
                    except Exception as e:
                        st.error(f"❌ Error: {e!s}")
    else:
        try:
            resp = requests.get(f"{PATIENTS_ENDPOINT}{patient_id}", timeout=5)
            if resp.status_code == 200:
                patient = resp.json()

                if editable:
                    with st.form("edit_patient_form"):
                        first_name = st.text_input(
                            "First Name", value=patient["first_name"]
                        )
                        last_name = st.text_input(
                            "Last Name", value=patient["last_name"]
                        )
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
                        phone = st.text_input(
                            "Phone Number", value=patient.get("phone", "")
                        )
                        email = st.text_input("Email", value=patient.get("email", ""))
                        address = st.text_area(
                            "Address", value=patient.get("address", "")
                        )
                        submitted = st.form_submit_button("Update Patient")
                        if submitted:
                            if not first_name or not last_name or not gender:
                                st.error(
                                    "First name, last name, and gender are required."
                                )
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
                                        f"{PATIENTS_ENDPOINT}{patient_id}",
                                        json=payload,
                                        timeout=5,
                                    )
                                    if response.status_code == 200:
                                        st.success(
                                            f"✅ Patient {first_name} {last_name} updated successfully!"
                                        )
                                        st.query_params = {
                                            "patient_id": str(patient_id)
                                        }
                                        st.rerun()
                                    else:
                                        error_detail = response.json().get(
                                            "detail", response.text
                                        )
                                        st.error(
                                            f"❌ Failed to update patient: {error_detail}"
                                        )
                                except Exception as e:
                                    st.error(f"❌ Error: {e!s}")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input(
                            "First Name", value=patient["first_name"], disabled=True
                        )
                        st.text_input(
                            "Last Name", value=patient["last_name"], disabled=True
                        )
                        st.text_input(
                            "Date of Birth",
                            value=patient["date_of_birth"],
                            disabled=True,
                        )
                        st.text_input("Gender", value=patient["gender"], disabled=True)
                    with col2:
                        st.text_input(
                            "Phone", value=patient.get("phone", ""), disabled=True
                        )
                        st.text_input(
                            "Email", value=patient.get("email", ""), disabled=True
                        )
                        st.text_area(
                            "Address",
                            value=patient.get("address", ""),
                            disabled=True,
                            height=100,
                        )
                    # Add Edit button
                    if st.button("Edit Patient", use_container_width=True):
                        st.query_params = {"patient_id": str(patient_id), "edit": "1"}
                        st.rerun()
            else:
                st.error(f"Patient not found: {resp.text}")
        except Exception as e:
            st.error(f"Error loading patient: {e!s}")

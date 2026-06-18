from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://localhost:8080/api"
UPLOAD_DIR = Path("streamlit_uploads")

DATASETS = {
    "employees": {
        "endpoint": "users",
        "columns": ["id", "employeeId", "name", "email", "phone", "department", "designation", "role"],
    },
    "attendance": {
        "endpoint": "attendance",
        "columns": ["id", "userId", "attendanceDate", "status"],
    },
    "leaves": {
        "endpoint": "leaves",
        "columns": ["id", "userId", "leaveType", "fromDate", "toDate", "reason", "status"],
    },
    "tasks": {
        "endpoint": "tasks",
        "columns": ["id", "title", "description", "priority", "status", "deadline", "assignedTo"],
    },
    "skills": {
        "endpoint": "skills",
        "columns": ["id", "userId", "skillName", "skillLevel"],
    },
    "notes": {
        "endpoint": "notes",
        "columns": ["id", "title", "description", "createdAt", "attachment"],
    },
}


def page_config() -> None:
    st.set_page_config(
        page_title="TEAM LMS Portal",
        page_icon="TL",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            .main .block-container { padding-top: 1.5rem; max-width: 1180px; }
            section[data-testid="stSidebar"] { background: #f8fafc; }
            h1, h2, h3 { color: #0f172a; }
            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            }
            div[data-testid="stMetric"] label { color: #475569; }
            .hero {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 18px 20px;
                background: #ffffff;
                margin-bottom: 18px;
            }
            .section-panel {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                background: #ffffff;
                margin: 8px 0 16px 0;
            }
            .muted { color: #64748b; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    st.session_state.setdefault("local_data", {name: [] for name in DATASETS})
    st.session_state.setdefault("uploaded_files", [])
    st.session_state.setdefault("backend_online", False)


def clean_filename(name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return safe_name or "uploaded_file"


def save_uploaded_file(uploaded_file: Any, folder: str = "files") -> str:
    UPLOAD_DIR.mkdir(exist_ok=True)
    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}_{clean_filename(uploaded_file.name)}"
    target_path = target_dir / file_name
    target_path.write_bytes(uploaded_file.getbuffer())
    return str(target_path)


def render_avatar(container: Any, image_path: str | None = None, label: str = "User") -> None:
    if image_path and Path(image_path).exists():
        try:
            container.image(image_path, width=140)
            return
        except Exception:
            pass

    initials = "".join(part[:1] for part in label.split()[:2]).upper() or "U"
    container.markdown(
        f"""
        <div style="
            width: 140px;
            height: 140px;
            border-radius: 70px;
            background: #e2e8f0;
            border: 1px solid #cbd5e1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #334155;
            font-size: 36px;
            font-weight: 700;
        ">{initials}</div>
        """,
        unsafe_allow_html=True,
    )


def auth_headers() -> dict[str, str]:
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def get_backend_data(endpoint: str) -> Any | None:
    try:
        response = requests.get(
            f"{API_BASE_URL}/{endpoint}",
            headers=auth_headers(),
            timeout=2,
        )
        response.raise_for_status()
        st.session_state.backend_online = True
        return response.json()
    except requests.RequestException:
        st.session_state.backend_online = False
        return None


def post_backend_data(endpoint: str, payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        response = requests.post(
            f"{API_BASE_URL}/{endpoint}",
            json=payload,
            headers={"Content-Type": "application/json", **auth_headers()},
            timeout=3,
        )
        response.raise_for_status()
        st.session_state.backend_online = True
        return True, "Saved to backend."
    except requests.RequestException:
        st.session_state.backend_online = False
        return False, "Backend is offline, saved in Streamlit session."


def records_for(dataset: str) -> list[dict[str, Any]]:
    config = DATASETS[dataset]
    backend_records = get_backend_data(config["endpoint"])
    if isinstance(backend_records, list):
        return backend_records
    return st.session_state.local_data.get(dataset, [])


def frame_for(dataset: str) -> pd.DataFrame:
    records = records_for(dataset)
    columns = DATASETS[dataset]["columns"]
    frame = pd.DataFrame(records)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame


def next_id(dataset: str) -> int:
    records = st.session_state.local_data.get(dataset, [])
    ids = [int(item.get("id", 0)) for item in records if str(item.get("id", "")).isdigit()]
    return max(ids, default=0) + 1


def add_local_record(dataset: str, payload: dict[str, Any]) -> None:
    record = {"id": next_id(dataset), **payload}
    st.session_state.local_data[dataset].append(record)


def save_record(dataset: str, payload: dict[str, Any]) -> None:
    endpoint = DATASETS[dataset]["endpoint"]
    ok, message = post_backend_data(endpoint, payload)
    if not ok:
        add_local_record(dataset, payload)
    (st.success if ok else st.warning)(message)


def show_table(records: list[dict[str, Any]], columns: list[str]) -> None:
    if not records:
        st.info("No records yet. Add data manually or upload a CSV/JSON file.")
        return

    frame = pd.DataFrame(records)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    st.dataframe(frame[columns], use_container_width=True, hide_index=True)


def load_uploaded_dataset(uploaded_file: Any) -> list[dict[str, Any]]:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(uploaded_file)
        return frame.fillna("").to_dict(orient="records")
    if suffix == ".json":
        data = json.loads(uploaded_file.getvalue().decode("utf-8"))
        if isinstance(data, dict):
            data = data.get("data", [])
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of records.")
        return data
    raise ValueError("Only CSV and JSON data files are supported.")


def data_importer() -> None:
    with st.sidebar.expander("Upload data", expanded=False):
        dataset = st.selectbox("Data type", list(DATASETS.keys()), key="upload_dataset")
        uploaded_file = st.file_uploader(
            "CSV or JSON",
            type=["csv", "json"],
            key="dataset_file",
        )
        if st.button("Import file", use_container_width=True, disabled=uploaded_file is None):
            try:
                records = load_uploaded_dataset(uploaded_file)
                st.session_state.local_data[dataset] = records
                saved_path = save_uploaded_file(uploaded_file, "data")
                st.session_state.uploaded_files.append(
                    {
                        "name": uploaded_file.name,
                        "path": saved_path,
                        "type": dataset,
                        "uploadedAt": dt.datetime.now().isoformat(timespec="seconds"),
                    }
                )
                st.success(f"Imported {len(records)} {dataset} records.")
            except (ValueError, json.JSONDecodeError, pd.errors.ParserError) as exc:
                st.error(f"Upload failed: {exc}")


def status_bar() -> None:
    if st.session_state.backend_online:
        st.sidebar.success("Backend connected")
    else:
        st.sidebar.info("Using Streamlit session data")


def login() -> None:
    left, right = st.columns([1.2, 1])
    with left:
        st.title("TEAM LMS")
        st.caption("Streamlit Learning Management System")
        st.markdown(
            "<div class='hero'><b>Manage employees, attendance, leaves, tasks, skills, notes, reports, and uploads from one app.</b></div>",
            unsafe_allow_html=True,
        )

    with right:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

    if not submitted:
        return

    if not email or not password:
        st.error("Enter email and password.")
        return

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=3,
        )
        response.raise_for_status()
        result = response.json()
        st.session_state.auth_token = result.get("token", "")
        st.session_state.user_email = email
        st.session_state.user_role = result.get("role", "")
        st.session_state.backend_online = True
        st.success("Logged in with backend authentication.")
        st.rerun()
    except requests.RequestException:
        st.session_state.auth_token = "session-token"
        st.session_state.user_email = email
        st.session_state.user_role = "LOCAL"
        st.session_state.backend_online = False
        st.warning("Backend is offline. You are logged into the Streamlit session.")
        st.rerun()


def metric_values() -> dict[str, int]:
    employees = frame_for("employees")
    attendance = frame_for("attendance")
    tasks = frame_for("tasks")

    present = 0
    if not attendance.empty and "status" in attendance.columns:
        present = attendance["status"].astype(str).str.lower().eq("present").sum()
    attendance_percent = round((present / len(attendance)) * 100) if len(attendance) else 0

    completed = 0
    if not tasks.empty and "status" in tasks.columns:
        completed = tasks["status"].astype(str).str.lower().eq("completed").sum()

    return {
        "employees": len(employees),
        "attendance": attendance_percent,
        "completed": completed,
    }


def dashboard() -> None:
    st.title("Dashboard")
    st.caption("Live values are calculated from backend data, uploaded files, or records added in this session.")

    metrics = metric_values()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Employees", metrics["employees"])
    col2.metric("Attendance", f"{metrics['attendance']}%")
    col3.metric("Completed Tasks", metrics["completed"])

    st.subheader("Current Tasks")
    show_table(records_for("tasks"), ["title", "priority", "status", "deadline", "assignedTo"])


def employees() -> None:
    st.title("Employees")
    records = records_for("employees")
    show_table(records, DATASETS["employees"]["columns"])

    with st.expander("Add employee", expanded=False):
        with st.form("employee_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name")
            email = col2.text_input("Email")
            employee_id = col1.text_input("Employee ID")
            phone = col2.text_input("Phone")
            department = col1.text_input("Department")
            designation = col2.text_input("Designation")
            role = st.selectbox("Role", ["EMPLOYEE", "ADMIN"])
            password = st.text_input("Temporary password", type="password")
            submitted = st.form_submit_button("Save employee")

        if submitted:
            save_record(
                "employees",
                {
                    "employeeId": employee_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "department": department,
                    "designation": designation,
                    "role": role,
                    "password": password,
                },
            )


def attendance() -> None:
    st.title("Attendance")
    records = records_for("attendance")
    show_table(records, DATASETS["attendance"]["columns"])

    with st.expander("Mark attendance", expanded=False):
        with st.form("attendance_form", clear_on_submit=True):
            user_id = st.number_input("Employee ID", min_value=1, step=1)
            attendance_date = st.date_input("Date", value=dt.date.today())
            status = st.selectbox("Status", ["Present", "Absent"])
            submitted = st.form_submit_button("Save attendance")

        if submitted:
            save_record(
                "attendance",
                {
                    "userId": user_id,
                    "attendanceDate": attendance_date.isoformat(),
                    "status": status,
                },
            )


def leaves() -> None:
    st.title("Leave Management")
    records = records_for("leaves")
    show_table(records, DATASETS["leaves"]["columns"])

    with st.expander("Apply leave", expanded=False):
        with st.form("leave_form", clear_on_submit=True):
            user_id = st.number_input("Employee ID", min_value=1, step=1)
            leave_type = st.selectbox("Leave type", ["Casual Leave", "Sick Leave", "Earned Leave"])
            col1, col2 = st.columns(2)
            from_date = col1.date_input("From date", value=dt.date.today())
            to_date = col2.date_input("To date", value=dt.date.today())
            reason = st.text_area("Reason")
            submitted = st.form_submit_button("Submit leave")

        if submitted:
            save_record(
                "leaves",
                {
                    "userId": user_id,
                    "leaveType": leave_type,
                    "fromDate": from_date.isoformat(),
                    "toDate": to_date.isoformat(),
                    "reason": reason,
                    "status": "Pending",
                },
            )


def tasks() -> None:
    st.title("Tasks")
    records = records_for("tasks")
    show_table(records, DATASETS["tasks"]["columns"])

    with st.expander("Create task", expanded=False):
        with st.form("task_form", clear_on_submit=True):
            title = st.text_input("Title")
            description = st.text_area("Description")
            col1, col2, col3 = st.columns(3)
            priority = col1.selectbox("Priority", ["Low", "Medium", "High"])
            status = col2.selectbox("Status", ["Not Started", "In Progress", "Completed"])
            deadline = col3.date_input("Deadline", value=dt.date.today())
            assigned_to = st.number_input("Assigned employee ID", min_value=1, step=1)
            submitted = st.form_submit_button("Save task")

        if submitted:
            save_record(
                "tasks",
                {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "status": status,
                    "deadline": deadline.isoformat(),
                    "assignedTo": assigned_to,
                },
            )


def skills() -> None:
    st.title("Skills")
    records = records_for("skills")
    show_table(records, DATASETS["skills"]["columns"])

    with st.expander("Add skill", expanded=False):
        with st.form("skill_form", clear_on_submit=True):
            user_id = st.number_input("Employee ID", min_value=1, step=1)
            skill_name = st.text_input("Skill")
            skill_level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
            submitted = st.form_submit_button("Save skill")

        if submitted:
            save_record("skills", {"userId": user_id, "skillName": skill_name, "skillLevel": skill_level})


def notes() -> None:
    st.title("Notes")
    records = records_for("notes")

    if not records:
        st.info("No notes yet.")

    for note in records:
        with st.container(border=True):
            st.subheader(str(note.get("title", "")))
            st.write(note.get("description", ""))
            if note.get("attachment"):
                st.caption(f"Attachment: {note['attachment']}")
            if note.get("createdAt"):
                st.caption(str(note["createdAt"]))

    with st.expander("Create note", expanded=False):
        with st.form("note_form", clear_on_submit=True):
            title = st.text_input("Title")
            description = st.text_area("Description")
            attachment = st.file_uploader("Attachment")
            submitted = st.form_submit_button("Save note")

        if submitted:
            attachment_path = save_uploaded_file(attachment, "notes") if attachment else ""
            save_record(
                "notes",
                {
                    "title": title,
                    "description": description,
                    "createdAt": dt.datetime.now().isoformat(timespec="seconds"),
                    "attachment": attachment_path,
                },
            )


def uploads() -> None:
    st.title("Uploads")
    st.caption("Uploaded files are saved inside the project folder.")

    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["csv", "json", "pdf", "png", "jpg", "jpeg", "doc", "docx", "txt"],
        )
        description = st.text_input("Description")
        submitted = st.form_submit_button("Upload file")

    if submitted:
        if not uploaded_file:
            st.error("Choose a file first.")
        else:
            saved_path = save_uploaded_file(uploaded_file)
            st.session_state.uploaded_files.append(
                {
                    "name": uploaded_file.name,
                    "description": description,
                    "path": saved_path,
                    "uploadedAt": dt.datetime.now().isoformat(timespec="seconds"),
                }
            )
            st.success(f"Uploaded: {saved_path}")

    show_table(
        st.session_state.uploaded_files,
        ["name", "description", "path", "uploadedAt"],
    )


def reports() -> None:
    st.title("Reports")
    metrics = metric_values()

    col1, col2, col3 = st.columns(3)
    col1.metric("Employees", metrics["employees"])
    col2.metric("Attendance", f"{metrics['attendance']}%")
    col3.metric("Completed Tasks", metrics["completed"])

    st.subheader("Employees")
    show_table(records_for("employees"), DATASETS["employees"]["columns"])

    st.subheader("Tasks")
    show_table(records_for("tasks"), DATASETS["tasks"]["columns"])

    st.subheader("Attendance")
    show_table(records_for("attendance"), DATASETS["attendance"]["columns"])


def profile() -> None:
    st.title("My Profile")
    email = st.session_state.get("user_email", "")
    users = records_for("employees")
    user = next((item for item in users if item.get("email") == email), {})

    profile_image = st.session_state.get("profile_image")
    col1, col2 = st.columns([1, 3])
    render_avatar(col1, profile_image, user.get("name") or email)

    col2.write(f"Name: {user.get('name', '')}")
    col2.write(f"Email: {email}")
    col2.write(f"Department: {user.get('department', '')}")
    col2.write(f"Role: {st.session_state.get('user_role', '')}")

    uploaded_photo = st.file_uploader("Upload profile photo", type=["png", "jpg", "jpeg"])
    if st.button("Save profile photo", disabled=uploaded_photo is None):
        saved_path = save_uploaded_file(uploaded_photo, "profiles")
        st.session_state.profile_image = saved_path
        st.success(f"Profile photo uploaded: {saved_path}")
        st.rerun()


def sidebar() -> str:
    st.sidebar.title("TEAM LMS")
    st.sidebar.caption(st.session_state.get("user_email", "Session user"))
    status_bar()
    data_importer()
    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Employees",
            "Attendance",
            "Leaves",
            "Tasks",
            "Skills",
            "Notes",
            "Uploads",
            "Reports",
            "Profile",
        ],
    )
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    return page


def main() -> None:
    page_config()
    init_state()
    if "auth_token" not in st.session_state:
        login()
        return

    pages = {
        "Dashboard": dashboard,
        "Employees": employees,
        "Attendance": attendance,
        "Leaves": leaves,
        "Tasks": tasks,
        "Skills": skills,
        "Notes": notes,
        "Uploads": uploads,
        "Reports": reports,
        "Profile": profile,
    }
    pages[sidebar()]()


if __name__ == "__main__":
    main()

# TEAM LMS

TEAM LMS is a Streamlit-based Learning Management System for managing employees, interns, attendance, leaves, tasks, skills, notes, reports, and notifications.

## Project Structure

```text
TEAM_LMS/
├── app.py
├── requirements.txt
├── README.md
├── config/
├── database/
├── auth/
├── pages/
├── modules/
├── services/
├── utils/
├── assets/
├── data/
├── exports/
└── tests/
```

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

## Tests

```powershell
pytest
```

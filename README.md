# TEAM LMS - Streamlit Dashboard

## Overview

TEAM LMS is a Learning Management System developed using Python and Streamlit. The application helps organizations manage employees, attendance, tasks, leaves, skills, notes, and reports through an interactive dashboard.

---

## Features

### Dashboard

* Employee Statistics
* Attendance Summary
* Task Overview
* Leave Analytics
* Interactive Charts

### Employee Management

* View Employee Details
* Department Information
* Employee Search

### Attendance Management

* Present/Absent Tracking
* Attendance Reports
* Attendance Analytics

### Leave Management

* Leave Requests
* Leave Status Tracking
* Leave Reports

### Task Management

* Assigned Tasks
* Task Progress
* Task Status Monitoring

### Skills Management

* Employee Skills
* Skill Levels
* Skill Analytics

### Reports

* Attendance Reports
* Task Reports
* Employee Performance Reports

---

## Technology Stack

### Frontend

* Streamlit

### Backend

* Python

### Libraries

* Pandas
* Plotly
* NumPy

### Data Storage

* CSV Files

---

## Project Structure

TEAM_LMS/

├── app.py

├── requirements.txt

├── README.md

│

├── data/

│   ├── employees.csv

│   ├── attendance.csv

│   ├── tasks.csv

│   ├── leaves.csv

│   ├── skills.csv

│   ├── notes.csv

│   └── reports.csv

│

├── pages/

│   ├── Dashboard.py

│   ├── Employees.py

│   ├── Attendance.py

│   ├── Leaves.py

│   ├── Tasks.py

│   ├── Skills.py

│   └── Reports.py

│

└── assets/

```
├── logo.png

└── background.png
```

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd TEAM_LMS
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Application

```bash
streamlit run app.py
```

or

```bash
python -m streamlit run app.py
```

Application URL:

```text
http://localhost:8501
```

---

## Sample Login

### Admin

Email:
[karunya@gmail.com](mailto:karunya@gmail.com)

Password:
123456

---

## Data Files

The application uses CSV files stored inside the data folder.

### employees.csv

Employee information

### attendance.csv

Attendance records

### tasks.csv

Task assignments

### leaves.csv

Leave requests

### skills.csv

Employee skills

### notes.csv

Notes and announcements

### reports.csv

Generated reports

---

## Future Enhancements

* MySQL Database Integration
* Authentication System
* Email Notifications
* AI-Based Analytics
* Employee Performance Prediction
* Mobile Application Support

---

## Author

Karunya

Internship Project

TEAM LMS Dashboard

2026

# BIET College Student Scholarship Management System

A professional full-stack DBMS project for managing scholarships, student applications, reviews, eligibility checks, document verification, and payment disbursements.

## Tech Stack

- Backend: Python standard library HTTP server
- Database: SQLite relational DBMS
- Frontend: HTML, CSS, JavaScript
- Architecture: REST API + single-page dashboard

## Run

From this project folder, the easiest command is:

```powershell
.\start.ps1
```

You can also double-click `start.bat` from File Explorer.

## Host Online

See `DEPLOY.md` for Render hosting steps.

Or run the server directly:

```powershell
python server.py
```

If `python` opens the Microsoft Store or fails on Windows, use the bundled Codex runtime:

```powershell
& "C:\Users\kiran\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" server.py
```

Open:

```text
http://127.0.0.1:8000
```

## Demo Accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@sms.edu | admin123 |
| Reviewer | reviewer@sms.edu | review123 |
| Student | sahana@sms.edu | student123 |

## Key DBMS Features

- Normalized relational schema with foreign keys
- User, student profile, scholarship, application, review, document, notification, payment, and audit-log tables
- Eligibility filtering by CGPA, income, deadline, status, and seat availability
- Application review workflow with scoring and status transitions
- Disbursement tracking for approved scholarships
- Dashboard analytics computed from SQL queries

## Project Structure

```text
.
├── database/
│   └── schema.sql
├── static/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── README.md
└── server.py
```

# Host BIET Scholarship Management System Online

Use Render for the simplest public deployment.

## 1. Upload Project To GitHub

Create a new GitHub repository, then upload these project files.

Do not upload:

- `scholarship_management.db`
- `__pycache__/`

The database will be created automatically on the server when the app starts.

## 2. Deploy On Render

1. Go to `https://render.com`
2. Sign in or create an account.
3. Click `New +`.
4. Choose `Web Service`.
5. Connect your GitHub account.
6. Select the repository for this project.
7. Use these settings:

```text
Name: biet-scholarship-management-system
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: python server.py
```

8. Click `Deploy Web Service`.

After deployment, Render gives a public URL like:

```text
https://biet-scholarship-management-system.onrender.com
```

Share that link with others.

## Demo Logins

```text
Admin: admin@sms.edu / admin123
Reviewer: reviewer@sms.edu / review123
Student: sahana@sms.edu / student123
```

## Important

SQLite is acceptable for a college/demo project. For a real production system with many users, move the database to PostgreSQL or MySQL.

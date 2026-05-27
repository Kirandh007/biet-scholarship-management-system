from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import hashlib
import json
import os
import secrets
import sqlite3
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "scholarship_management.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
STATIC_DIR = BASE_DIR / "static"
SESSIONS = {}


def db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def rows(cursor):
    return [dict(row) for row in cursor.fetchall()]


def one(cursor):
    row = cursor.fetchone()
    return dict(row) if row else None


def audit(connection, actor_id, action, entity, entity_id=None):
    connection.execute(
        "INSERT INTO audit_logs (actor_id, action, entity, entity_id) VALUES (?, ?, ?, ?)",
        (actor_id, action, entity, entity_id),
    )


def seed_database():
    with db() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        existing = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if existing:
            return

        users = [
            ("Dr. Meera Kapoor", "admin@sms.edu", "admin123", "admin", "Scholarship Cell", "+91 90000 11111"),
            ("Prof. Arvind Rao", "reviewer@sms.edu", "review123", "reviewer", "Academic Review", "+91 90000 22222"),
            ("Sahana", "sahana@sms.edu", "student123", "student", "Computer Science", "+91 90000 33333"),
            ("Namana", "namana@sms.edu", "student123", "student", "Mechanical", "+91 90000 44444"),
            ("Adithi H", "adithi@sms.edu", "student123", "student", "Electronics", "+91 90000 55555"),
            ("Kiran", "kiran@sms.edu", "student123", "student", "Information Science", "+91 90000 66666"),
            ("Soma", "soma@sms.edu", "student123", "student", "Civil", "+91 90000 77777"),
        ]
        for user in users:
            connection.execute(
                "INSERT INTO users (name, email, password, role, department, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (user[0], user[1], hash_password(user[2]), user[3], user[4], user[5]),
            )

        profiles = [
            (3, "CS-2024-018", "B.Tech CSE", 3, 9.1, 180000, "OBC", "778899001122", "SBIN0000712"),
            (4, "ME-2024-042", "B.Tech Mechanical", 2, 8.4, 250000, "General", "667788990011", "HDFC0000312"),
            (5, "EC-2024-027", "B.Tech ECE", 4, 9.5, 125000, "General", "998877665544", "ICIC0000528"),
            (6, "IS-2024-033", "B.Tech ISE", 3, 8.9, 210000, "OBC", "889900112233", "CNRB0001024"),
            (7, "CV-2024-011", "B.Tech Civil", 2, 8.1, 160000, "SC/ST", "776655443322", "UBIN0000818"),
        ]
        connection.executemany(
            """
            INSERT INTO student_profiles
            (user_id, roll_number, course, year, cgpa, annual_income, category, bank_account, ifsc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            profiles,
        )

        scholarships = [
            ("Merit Excellence Scholarship", "National Education Trust", 75000, "CGPA 8.5+, annual family income below 300000", 8.5, 300000, 35, "2026-07-30", "open"),
            ("Women in Technology Grant", "TechForward Foundation", 95000, "Female students in computing or electronics with strong academics", 8.0, 500000, 20, "2026-08-15", "open"),
            ("Need Based Academic Aid", "University Welfare Board", 50000, "Students with annual income below 200000 and CGPA 7.0+", 7.0, 200000, 60, "2026-06-20", "open"),
            ("Research Innovation Fellowship", "Innovation Council", 120000, "Final year students with research proposal and CGPA 8.8+", 8.8, 650000, 12, "2026-09-01", "open"),
        ]
        connection.executemany(
            """
            INSERT INTO scholarships
            (title, provider, amount, eligibility, min_cgpa, max_income, seats, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            scholarships,
        )

        applications = [
            (3, 1, "I plan to use this award for tuition fees, cloud certifications, and final-year project expenses.", "approved", 92),
            (3, 2, "This grant will help me continue machine learning research and cover lab equipment costs.", "under_review", 81),
            (4, 3, "My family needs support for semester fees and hostel charges.", "submitted", 70),
            (5, 2, "The scholarship will support embedded systems research and professional training.", "approved", 95),
            (6, 1, "This scholarship will support advanced programming courses, project materials, and semester fee payments.", "submitted", 86),
            (7, 3, "I need financial support for tuition, transport, books, and civil engineering survey equipment.", "waitlisted", 76),
        ]
        connection.executemany(
            """
            INSERT INTO applications (student_id, scholarship_id, purpose, status, score)
            VALUES (?, ?, ?, ?, ?)
            """,
            applications,
        )

        docs = [
            (1, "Income Certificate", "sahana_income_certificate.pdf", "verified"),
            (1, "Marksheets", "sahana_marksheets.pdf", "verified"),
            (2, "Project Proposal", "ml_research_proposal.pdf", "pending"),
            (3, "Income Certificate", "namana_income_certificate.pdf", "pending"),
            (4, "Bonafide Certificate", "adithi_bonafide.pdf", "verified"),
        ]
        connection.executemany(
            """
            INSERT INTO documents (application_id, document_type, file_name, verification_status)
            VALUES (?, ?, ?, ?)
            """,
            docs,
        )

        reviews = [
            (1, 2, "approved", 92, "Excellent academic record and clear financial need."),
            (4, 2, "approved", 95, "Strong profile with relevant research direction."),
        ]
        connection.executemany(
            """
            INSERT INTO reviews (application_id, reviewer_id, decision, score, remarks)
            VALUES (?, ?, ?, ?, ?)
            """,
            reviews,
        )

        connection.execute(
            """
            INSERT INTO disbursements (application_id, amount, transaction_ref, status, processed_at)
            VALUES (1, 75000, 'NEFT-SMS-2026-0001', 'processed', CURRENT_TIMESTAMP)
            """
        )


class AppHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path).path
        if parsed == "/":
            return str(STATIC_DIR / "index.html")
        return str(STATIC_DIR / parsed.lstrip("/"))

    def log_message(self, format, *args):
        return

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def current_user(self):
        raw_cookie = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie(raw_cookie)
        token = jar.get("sms_session")
        if not token or token.value not in SESSIONS:
            return None
        with db() as connection:
            return one(connection.execute(
                "SELECT id, name, email, role, department, phone FROM users WHERE id = ?",
                (SESSIONS[token.value],),
            ))

    def require_user(self):
        user = self.current_user()
        if not user:
            self.send_json({"error": "Authentication required"}, 401)
        return user

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return super().do_GET()

        routes = {
            "/api/me": self.api_me,
            "/api/dashboard": self.api_dashboard,
            "/api/scholarships": self.api_scholarships,
            "/api/applications": self.api_applications,
            "/api/students": self.api_students,
            "/api/audit-logs": self.api_audit_logs,
            "/api/notifications": self.api_notifications,
        }
        handler = routes.get(parsed.path)
        if not handler:
            return self.send_json({"error": "Route not found"}, 404)
        handler()

    def do_POST(self):
        parsed = urlparse(self.path)
        routes = {
            "/api/login": self.api_login,
            "/api/logout": self.api_logout,
            "/api/scholarships": self.api_create_scholarship,
            "/api/applications": self.api_create_application,
            "/api/review": self.api_review_application,
            "/api/disburse": self.api_disburse,
        }
        handler = routes.get(parsed.path)
        if not handler:
            return self.send_json({"error": "Route not found"}, 404)
        handler()

    def api_login(self):
        payload = self.read_json()
        with db() as connection:
            user = one(connection.execute(
                """
                SELECT id, name, email, role, department, phone
                FROM users WHERE email = ? AND password = ?
                """,
                (payload.get("email", "").lower(), hash_password(payload.get("password", ""))),
            ))
        if not user:
            return self.send_json({"error": "Invalid email or password"}, 401)

        token = secrets.token_urlsafe(32)
        SESSIONS[token] = user["id"]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", f"sms_session={token}; HttpOnly; SameSite=Lax; Path=/")
        body = json.dumps({"user": user}).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def api_logout(self):
        raw_cookie = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie(raw_cookie)
        token = jar.get("sms_session")
        if token:
            SESSIONS.pop(token.value, None)
        self.send_response(204)
        self.send_header("Set-Cookie", "sms_session=; Max-Age=0; Path=/")
        self.end_headers()

    def api_me(self):
        user = self.current_user()
        self.send_json({"user": user})

    def api_dashboard(self):
        user = self.require_user()
        if not user:
            return
        with db() as connection:
            stats = one(connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM scholarships WHERE status = 'open') AS open_scholarships,
                    (SELECT COUNT(*) FROM applications) AS total_applications,
                    (SELECT COUNT(*) FROM applications WHERE status IN ('approved', 'paid')) AS approved,
                    (SELECT COALESCE(SUM(amount), 0) FROM disbursements WHERE status = 'processed') AS disbursed
                """
            ))
            pipeline = rows(connection.execute(
                "SELECT status, COUNT(*) AS total FROM applications GROUP BY status ORDER BY total DESC"
            ))
            upcoming = rows(connection.execute(
                """
                SELECT title, provider, amount, deadline
                FROM scholarships
                WHERE status = 'open'
                ORDER BY deadline ASC
                LIMIT 5
                """
            ))
        self.send_json({"stats": stats, "pipeline": pipeline, "upcoming": upcoming})

    def api_scholarships(self):
        user = self.require_user()
        if not user:
            return
        with db() as connection:
            data = rows(connection.execute(
                """
                SELECT s.*,
                       (SELECT COUNT(*) FROM applications a WHERE a.scholarship_id = s.id) AS applications,
                       (SELECT COUNT(*) FROM applications a WHERE a.scholarship_id = s.id AND a.status IN ('approved', 'paid')) AS awarded
                FROM scholarships s
                ORDER BY s.deadline ASC
                """
            ))
            profile = None
            if user["role"] == "student":
                profile = one(connection.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user["id"],)))
                for scholarship in data:
                    scholarship["eligible"] = bool(
                        profile
                        and profile["cgpa"] >= scholarship["min_cgpa"]
                        and profile["annual_income"] <= scholarship["max_income"]
                        and scholarship["status"] == "open"
                    )
        self.send_json({"scholarships": data})

    def api_applications(self):
        user = self.require_user()
        if not user:
            return
        with db() as connection:
            where = ""
            params = ()
            if user["role"] == "student":
                where = "WHERE a.student_id = ?"
                params = (user["id"],)
            data = rows(connection.execute(
                f"""
                SELECT a.*, s.title AS scholarship, s.provider, s.amount,
                       u.name AS student_name, p.roll_number, p.course, p.cgpa, p.annual_income,
                       COALESCE(d.status, 'not_scheduled') AS payment_status
                FROM applications a
                JOIN scholarships s ON s.id = a.scholarship_id
                JOIN users u ON u.id = a.student_id
                LEFT JOIN student_profiles p ON p.user_id = u.id
                LEFT JOIN disbursements d ON d.application_id = a.id
                {where}
                ORDER BY a.updated_at DESC
                """,
                params,
            ))
            for application in data:
                application["documents"] = rows(connection.execute(
                    "SELECT document_type, file_name, verification_status FROM documents WHERE application_id = ?",
                    (application["id"],),
                ))
        self.send_json({"applications": data})

    def api_students(self):
        user = self.require_user()
        if not user:
            return
        if user["role"] not in ("admin", "reviewer"):
            return self.send_json({"error": "Admin or reviewer access required"}, 403)
        with db() as connection:
            students = rows(connection.execute(
                """
                SELECT u.id, u.name, u.email, u.department, p.roll_number, p.course, p.year,
                       p.cgpa, p.annual_income, p.category,
                       COUNT(a.id) AS applications
                FROM users u
                JOIN student_profiles p ON p.user_id = u.id
                LEFT JOIN applications a ON a.student_id = u.id
                GROUP BY u.id
                ORDER BY p.cgpa DESC
                """
            ))
        self.send_json({"students": students})

    def api_notifications(self):
        user = self.require_user()
        if not user:
            return
        with db() as connection:
            notes = rows(connection.execute(
                "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 12",
                (user["id"],),
            ))
        self.send_json({"notifications": notes})

    def api_audit_logs(self):
        user = self.require_user()
        if not user:
            return
        if user["role"] != "admin":
            return self.send_json({"error": "Admin access required"}, 403)
        with db() as connection:
            logs = rows(connection.execute(
                """
                SELECT l.*, COALESCE(u.name, 'System') AS actor
                FROM audit_logs l
                LEFT JOIN users u ON u.id = l.actor_id
                ORDER BY l.created_at DESC
                LIMIT 25
                """
            ))
        self.send_json({"logs": logs})

    def api_create_scholarship(self):
        user = self.require_user()
        if not user:
            return
        if user["role"] != "admin":
            return self.send_json({"error": "Admin access required"}, 403)
        payload = self.read_json()
        required = ["title", "provider", "amount", "eligibility", "min_cgpa", "max_income", "seats", "deadline"]
        if any(not str(payload.get(field, "")).strip() for field in required):
            return self.send_json({"error": "All scholarship fields are required"}, 400)
        with db() as connection:
            cursor = connection.execute(
                """
                INSERT INTO scholarships
                (title, provider, amount, eligibility, min_cgpa, max_income, seats, deadline, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
                """,
                (
                    payload["title"], payload["provider"], int(payload["amount"]),
                    payload["eligibility"], float(payload["min_cgpa"]),
                    int(payload["max_income"]), int(payload["seats"]), payload["deadline"],
                ),
            )
            audit(connection, user["id"], "created scholarship", "scholarships", cursor.lastrowid)
        self.send_json({"ok": True}, 201)

    def api_create_application(self):
        user = self.require_user()
        if not user:
            return
        if user["role"] != "student":
            return self.send_json({"error": "Only students can apply"}, 403)
        payload = self.read_json()
        scholarship_id = int(payload.get("scholarship_id", 0))
        purpose = payload.get("purpose", "").strip()
        if len(purpose) < 30:
            return self.send_json({"error": "Purpose must be at least 30 characters"}, 400)
        with db() as connection:
            scholarship = one(connection.execute("SELECT * FROM scholarships WHERE id = ?", (scholarship_id,)))
            profile = one(connection.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user["id"],)))
            if not scholarship or scholarship["status"] != "open":
                return self.send_json({"error": "Scholarship is not open"}, 400)
            if profile["cgpa"] < scholarship["min_cgpa"] or profile["annual_income"] > scholarship["max_income"]:
                return self.send_json({"error": "Profile does not satisfy eligibility rules"}, 400)
            try:
                cursor = connection.execute(
                    "INSERT INTO applications (student_id, scholarship_id, purpose, score) VALUES (?, ?, ?, ?)",
                    (user["id"], scholarship_id, purpose, round(profile["cgpa"] * 10)),
                )
                connection.execute(
                    """
                    INSERT INTO documents (application_id, document_type, file_name)
                    VALUES (?, 'Student Declaration', 'digital_declaration.pdf')
                    """,
                    (cursor.lastrowid,),
                )
                audit(connection, user["id"], "submitted application", "applications", cursor.lastrowid)
            except sqlite3.IntegrityError:
                return self.send_json({"error": "You have already applied for this scholarship"}, 409)
        self.send_json({"ok": True}, 201)

    def api_review_application(self):
        user = self.require_user()
        if not user:
            return
        if user["role"] not in ("admin", "reviewer"):
            return self.send_json({"error": "Reviewer access required"}, 403)
        payload = self.read_json()
        application_id = int(payload.get("application_id", 0))
        decision = payload.get("decision")
        if decision not in ("under_review", "approved", "rejected", "waitlisted"):
            return self.send_json({"error": "Invalid decision"}, 400)
        score = max(0, min(100, int(payload.get("score", 0))))
        remarks = payload.get("remarks", "Reviewed by scholarship committee.").strip()
        with db() as connection:
            connection.execute(
                """
                INSERT INTO reviews (application_id, reviewer_id, decision, score, remarks)
                VALUES (?, ?, ?, ?, ?)
                """,
                (application_id, user["id"], decision, score, remarks),
            )
            connection.execute(
                "UPDATE applications SET status = ?, score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (decision, score, application_id),
            )
            audit(connection, user["id"], f"marked application {decision}", "applications", application_id)
        self.send_json({"ok": True})

    def api_disburse(self):
        user = self.require_user()
        if not user:
            return
        if user["role"] != "admin":
            return self.send_json({"error": "Admin access required"}, 403)
        payload = self.read_json()
        application_id = int(payload.get("application_id", 0))
        with db() as connection:
            application = one(connection.execute(
                """
                SELECT a.id, s.amount
                FROM applications a
                JOIN scholarships s ON s.id = a.scholarship_id
                WHERE a.id = ? AND a.status = 'approved'
                """,
                (application_id,),
            ))
            if not application:
                return self.send_json({"error": "Only approved applications can be disbursed"}, 400)
            ref = f"NEFT-SMS-2026-{secrets.randbelow(999999):06d}"
            try:
                connection.execute(
                    """
                    INSERT INTO disbursements (application_id, amount, transaction_ref, status, processed_at)
                    VALUES (?, ?, ?, 'processed', CURRENT_TIMESTAMP)
                    """,
                    (application_id, application["amount"], ref),
                )
                connection.execute(
                    "UPDATE applications SET status = 'paid', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (application_id,),
                )
                audit(connection, user["id"], "processed disbursement", "applications", application_id)
            except sqlite3.IntegrityError:
                return self.send_json({"error": "Disbursement already exists"}, 409)
        self.send_json({"ok": True, "transaction_ref": ref})


if __name__ == "__main__":
    seed_database()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    print(f"BIET College Student Scholarship Management System running on port {port}", flush=True)
    server.serve_forever()

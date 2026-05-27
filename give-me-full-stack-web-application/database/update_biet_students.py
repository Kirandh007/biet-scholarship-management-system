import hashlib
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "scholarship_management.db"
PASSWORD = hashlib.sha256("student123".encode("utf-8")).hexdigest()


students = [
    (3, "Sahana", "sahana@sms.edu", "Computer Science", "+91 90000 33333"),
    (4, "Namana", "namana@sms.edu", "Mechanical", "+91 90000 44444"),
    (5, "Adithi H", "adithi@sms.edu", "Electronics", "+91 90000 55555"),
    (6, "Kiran", "kiran@sms.edu", "Information Science", "+91 90000 66666"),
    (7, "Soma", "soma@sms.edu", "Civil", "+91 90000 77777"),
]

profiles = [
    (3, "CS-2024-018", "B.Tech CSE", 3, 9.1, 180000, "OBC", "778899001122", "SBIN0000712"),
    (4, "ME-2024-042", "B.Tech Mechanical", 2, 8.4, 250000, "General", "667788990011", "HDFC0000312"),
    (5, "EC-2024-027", "B.Tech ECE", 4, 9.5, 125000, "General", "998877665544", "ICIC0000528"),
    (6, "IS-2024-033", "B.Tech ISE", 3, 8.9, 210000, "OBC", "889900112233", "CNRB0001024"),
    (7, "CV-2024-011", "B.Tech Civil", 2, 8.1, 160000, "SC/ST", "776655443322", "UBIN0000818"),
]


with sqlite3.connect(DB_PATH) as connection:
    connection.execute("PRAGMA foreign_keys = ON")
    for user_id, name, email, department, phone in students:
        connection.execute(
            """
            INSERT INTO users (id, name, email, password, role, department, phone)
            VALUES (?, ?, ?, ?, 'student', ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                email = excluded.email,
                password = excluded.password,
                role = excluded.role,
                department = excluded.department,
                phone = excluded.phone
            """,
            (user_id, name, email, PASSWORD, department, phone),
        )

    for profile in profiles:
        connection.execute(
            """
            INSERT INTO student_profiles
            (user_id, roll_number, course, year, cgpa, annual_income, category, bank_account, ifsc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                roll_number = excluded.roll_number,
                course = excluded.course,
                year = excluded.year,
                cgpa = excluded.cgpa,
                annual_income = excluded.annual_income,
                category = excluded.category,
                bank_account = excluded.bank_account,
                ifsc = excluded.ifsc
            """,
            profile,
        )

    connection.execute(
        """
        UPDATE documents
        SET file_name = 'sahana_income_certificate.pdf'
        WHERE application_id = 1 AND document_type = 'Income Certificate'
        """
    )
    connection.execute(
        """
        UPDATE documents
        SET file_name = 'sahana_marksheets.pdf'
        WHERE application_id = 1 AND document_type = 'Marksheets'
        """
    )
    connection.execute(
        """
        UPDATE documents
        SET file_name = 'namana_income_certificate.pdf'
        WHERE application_id = 3 AND document_type = 'Income Certificate'
        """
    )
    connection.execute(
        """
        UPDATE documents
        SET file_name = 'adithi_bonafide.pdf'
        WHERE application_id = 4 AND document_type = 'Bonafide Certificate'
        """
    )

print("Updated BIET student data.")

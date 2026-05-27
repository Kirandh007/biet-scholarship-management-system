PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'student', 'reviewer')),
    department TEXT,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    roll_number TEXT NOT NULL UNIQUE,
    course TEXT NOT NULL,
    year INTEGER NOT NULL,
    cgpa REAL NOT NULL CHECK (cgpa BETWEEN 0 AND 10),
    annual_income INTEGER NOT NULL CHECK (annual_income >= 0),
    category TEXT NOT NULL,
    bank_account TEXT NOT NULL,
    ifsc TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    provider TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    eligibility TEXT NOT NULL,
    min_cgpa REAL NOT NULL CHECK (min_cgpa BETWEEN 0 AND 10),
    max_income INTEGER NOT NULL CHECK (max_income >= 0),
    seats INTEGER NOT NULL CHECK (seats > 0),
    deadline TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'open', 'closed')) DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    scholarship_id INTEGER NOT NULL,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'waitlisted', 'paid')
    ) DEFAULT 'submitted',
    score INTEGER NOT NULL DEFAULT 0,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, scholarship_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    verification_status TEXT NOT NULL CHECK (
        verification_status IN ('pending', 'verified', 'rejected')
    ) DEFAULT 'pending',
    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('under_review', 'approved', 'rejected', 'waitlisted')),
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    remarks TEXT NOT NULL,
    reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS disbursements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL UNIQUE,
    amount INTEGER NOT NULL CHECK (amount > 0),
    transaction_ref TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'processed', 'failed')) DEFAULT 'scheduled',
    processed_at TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_student ON applications(student_id);
CREATE INDEX IF NOT EXISTS idx_scholarships_status ON scholarships(status);

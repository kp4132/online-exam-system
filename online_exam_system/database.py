"""
Database module for Online Exam and Quiz System
Handles SQLite connection, schema initialization, and sample seed data.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'exam_system.db')

def get_db():
    """Get a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Create tables if they do not exist and seed initial demo data."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table with Single-Session Token Support
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', -- 'admin' or 'student'
        full_name TEXT NOT NULL,
        session_token TEXT, -- Tracks active session for Single-Device Login
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Ensure session_token column exists if database was created previously
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN session_token TEXT;")
    except sqlite3.OperationalError:
        pass # Column already exists

    # 2. Quizzes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'General',
        duration_minutes INTEGER NOT NULL DEFAULT 15,
        passing_percentage INTEGER NOT NULL DEFAULT 50,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 3. Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL, -- 'A', 'B', 'C', or 'D'
        explanation TEXT,
        marks INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """)

    # 4. Exam Attempts / Submissions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        total_marks INTEGER NOT NULL DEFAULT 0,
        percentage REAL NOT NULL DEFAULT 0.0,
        passed INTEGER NOT NULL DEFAULT 0, -- 1 for pass, 0 for fail
        time_spent_seconds INTEGER DEFAULT 0,
        answers_json TEXT, -- JSON record of user answers
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    seed_demo_data(conn)
    conn.close()

def seed_demo_data(conn):
    """Seed single admin, student user, and full subjects quizzes."""
    cursor = conn.cursor()

    # Fixed Admin Credentials: admin@exam.com / Admin@123
    admin_pass = generate_password_hash("Admin@123")
    cursor.execute("SELECT id FROM users WHERE email = 'admin@exam.com'")
    admin = cursor.fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name)
            VALUES (?, ?, ?, 'admin', ?)
        """, ('admin', 'admin@exam.com', admin_pass, 'System Administrator'))
        admin_id = cursor.lastrowid
    else:
        admin_id = admin['id']
        # Update password to ensure it matches Admin@123
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (admin_pass, admin_id))

    # Default Student Account: student@exam.com / student123
    student_pass = generate_password_hash("student123")
    cursor.execute("SELECT id FROM users WHERE email = 'student@exam.com'")
    student = cursor.fetchone()
    if not student:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name)
            VALUES (?, ?, ?, 'student', ?)
        """, ('student', 'student@exam.com', student_pass, 'Alex Student'))
        student_id = cursor.lastrowid
    else:
        student_id = student['id']

    # Helper function to add a quiz with questions if not existing
    def add_quiz_if_missing(title, description, category, duration, passing_pct, questions):
        cursor.execute("SELECT id FROM quizzes WHERE title = ?", (title,))
        existing = cursor.fetchone()
        if existing:
            return existing['id']

        cursor.execute("""
            INSERT INTO quizzes (title, description, category, duration_minutes, passing_percentage, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (title, description, category, duration, passing_pct, admin_id))
        new_quiz_id = cursor.lastrowid

        formatted_questions = [
            (new_quiz_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7])
            for q in questions
        ]
        cursor.executemany("""
            INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, formatted_questions)
        return new_quiz_id

    # ==========================================
    # 1. HTML Quiz
    # ==========================================
    html_questions = [
        (
            "What is the primary purpose of the <!DOCTYPE html> declaration?",
            "Links external CSS stylesheet",
            "Informs the browser to render the page in standard HTML5 mode",
            "Declares the default JavaScript scripting language",
            "Creates the root element of the document",
            "B",
            "<!DOCTYPE html> ensures modern web browsers render pages using HTML5 standards mode rather than quirks mode.",
            2
        ),
        (
            "Which of the following is an HTML5 semantic element representing self-contained, independent content?",
            "<div>",
            "<section>",
            "<article>",
            "<span>",
            "C",
            "<article> represents an independent, self-contained composition (such as a blog entry, forum post, or news article).",
            2
        ),
        (
            "Which HTML attribute specifies that an input field must be filled out before submitting a form?",
            "validate",
            "required",
            "mandatory",
            "important",
            "B",
            "The boolean 'required' attribute prevents form submission if the input field is left empty.",
            2
        ),
        (
            "How do you open a hyperlink in a new browser tab or window in HTML?",
            "<a href='url' target='_blank'>",
            "<a href='url' target='_new'>",
            "<a href='url' window='new'>",
            "<a href='url' newtab>",
            "A",
            "target='_blank' instructs browsers to display the linked resource in a new browsing context/tab.",
            2
        ),
        (
            "Which HTML5 element is used to draw graphics and animations dynamically via JavaScript?",
            "<svg>",
            "<canvas>",
            "<paint>",
            "<graphic>",
            "B",
            "The <canvas> element provides a resolution-dependent bitmap canvas for dynamic, scriptable 2D and 3D rendering.",
            2
        )
    ]
    add_quiz_if_missing(
        "HTML5 & Web Markup Essentials",
        "Comprehensive assessment on HTML5 document structure, semantic tags, form controls, and APIs.",
        "HTML",
        10,
        50,
        html_questions
    )

    # ==========================================
    # 2. CSS Quiz
    # ==========================================
    css_questions = [
        (
            "Which CSS property aligns items along the cross axis in a Flexbox container?",
            "justify-content",
            "align-items",
            "flex-direction",
            "align-content",
            "B",
            "'align-items' controls alignment along the cross axis, while 'justify-content' aligns along the main axis.",
            2
        ),
        (
            "What are the four components of the standard CSS Box Model, from innermost to outermost?",
            "Content, Margin, Border, Padding",
            "Content, Padding, Border, Margin",
            "Padding, Content, Border, Margin",
            "Border, Content, Padding, Margin",
            "B",
            "The standard box model order is: Content (inner), Padding, Border, and Margin (outermost).",
            2
        ),
        (
            "What is the difference between 'display: none' and 'visibility: hidden'?",
            "'display: none' removes the element from document flow, while 'visibility: hidden' reserves its physical space",
            "Both remove the element and its physical space completely",
            "'visibility: hidden' removes the element from the DOM tree",
            "There is no difference between them",
            "A",
            "'display: none' removes the element from layout calculation, whereas 'visibility: hidden' makes it invisible while keeping its dimensions.",
            2
        ),
        (
            "Which CSS selector carries the highest specificity weighting?",
            "Element / Tag selector (e.g. p)",
            "Class selector (e.g. .card)",
            "ID selector (e.g. #header)",
            "Universal selector (e.g. *)",
            "C",
            "ID selectors carry a specificity weight of (1, 0, 0), which overrides class selectors (0, 1, 0) and element selectors (0, 0, 1).",
            2
        ),
        (
            "Which CSS Grid rule creates a 3-column layout where each column takes an equal fraction of available space?",
            "grid-template-columns: 1fr 1fr 1fr;",
            "grid-columns: 3;",
            "columns-count: 3;",
            "grid-layout: 3-col;",
            "A",
            "'grid-template-columns: 1fr 1fr 1fr;' (or repeat(3, 1fr)) creates three equal fractional columns.",
            2
        )
    ]
    add_quiz_if_missing(
        "CSS3 Styling & Modern Layouts",
        "Test your mastery of CSS Box Model, Flexbox, Grid, specificity hierarchy, and responsive styling.",
        "CSS",
        10,
        50,
        css_questions
    )

    # ==========================================
    # 3. C++ Quiz
    # ==========================================
    cpp_questions = [
        (
            "In C++, how is runtime polymorphism implemented under the hood?",
            "Function overloading and name mangling",
            "Virtual functions and virtual method tables (vtables)",
            "Template instantiation at compile time",
            "Operator overloading functions",
            "B",
            "Runtime polymorphism uses the 'virtual' keyword, which utilizes virtual method tables (vtables) to resolve function calls dynamically.",
            2
        ),
        (
            "Which C++11 smart pointer provides exclusive, non-shared ownership of a dynamic object?",
            "std::shared_ptr",
            "std::weak_ptr",
            "std::unique_ptr",
            "std::auto_ptr",
            "C",
            "std::unique_ptr maintains exclusive ownership of a resource; it cannot be copied, only moved via std::move().",
            2
        ),
        (
            "What is the order of destructor execution when a Derived class object is destroyed?",
            "Base destructor first, then Derived destructor",
            "Derived destructor first, then Base destructor",
            "Destructors run in arbitrary random order",
            "Only the Base class destructor runs",
            "B",
            "Destructors execute in reverse order of construction: Derived class destructor runs first, followed by Base class destructor.",
            2
        ),
        (
            "What happens if a Base class destructor is NOT virtual when deleting a derived object via a base pointer?",
            "It produces a compile-time error",
            "Undefined behavior and potential memory leaks because the Derived destructor is not called",
            "The Derived destructor executes automatically",
            "The object remains safely in heap memory",
            "B",
            "Deleting a derived object through a non-virtual base pointer causes undefined behavior; the derived destructor never runs, causing resource leaks.",
            2
        ),
        (
            "Which foundational C++ design idiom ties resource acquisition to object lifetime and ensures deterministic cleanup?",
            "RAII (Resource Acquisition Is Initialization)",
            "DRY (Don't Repeat Yourself)",
            "SOLID principles",
            "Lazy Evaluation",
            "A",
            "RAII binds resource allocation to object construction and release to object destruction, guaranteeing exception-safe cleanup.",
            2
        )
    ]
    add_quiz_if_missing(
        "C++ Programming & OOP Architecture",
        "Deep dive into C++ OOP principles, memory management, virtual destructors, smart pointers, and RAII.",
        "C++",
        12,
        60,
        cpp_questions
    )

    # ==========================================
    # 4. Ethical Hacking Quiz
    # ==========================================
    hacking_questions = [
        (
            "What is the primary industry standard defense against SQL Injection (SQLi) attacks?",
            "Encrypting all database tables",
            "Using Prepared Statements (Parameterized Queries)",
            "Changing the default database network port",
            "Using HTTP GET requests instead of POST",
            "B",
            "Prepared statements treat user input strictly as parameters rather than executable SQL code, preventing SQL injection.",
            2
        ),
        (
            "Which type of Cross-Site Scripting (XSS) occurs when malicious code is permanently stored in a target server's database?",
            "Reflected XSS",
            "Stored (Persistent) XSS",
            "DOM-based XSS",
            "Blind XSS",
            "B",
            "Stored XSS occurs when an attacker's payload is saved on the server (e.g. database or comment section) and served to other users.",
            2
        ),
        (
            "Which network attack involves poisoning ARP tables to intercept traffic between a host and a router?",
            "Man-in-the-Middle (MITM) via ARP Spoofing",
            "Distributed Denial of Service (DDoS)",
            "Buffer Overflow",
            "DNS Amplification",
            "A",
            "ARP spoofing sends fake ARP replies across a local network to associate an attacker's MAC address with a default gateway's IP.",
            2
        ),
        (
            "What do the three letters in the security CIA Triad stand for?",
            "Control, Inspection, Authentication",
            "Confidentiality, Integrity, Availability",
            "Cryptography, Identification, Authorization",
            "Cyber, Information, Assurance",
            "B",
            "The CIA Triad stands for Confidentiality (privacy), Integrity (data accuracy), and Availability (service uptime).",
            2
        ),
        (
            "In network penetration testing, what characterizes a TCP SYN Scan (half-open scan)?",
            "It completes the entire 3-way TCP handshake",
            "It sends a SYN packet and resets (RST) upon receiving SYN-ACK without completing the handshake",
            "It sends high-volume UDP broadcast packets",
            "It automatically downloads the target server's firewall rules",
            "B",
            "A SYN scan (e.g., nmap -sS) checks open ports without completing the full TCP connection, making it faster and less conspicuous.",
            2
        )
    ]
    add_quiz_if_missing(
        "Ethical Hacking & Cybersecurity Essentials",
        "Penetration testing concepts, SQLi, XSS, ARP spoofing, TCP port scans, and the CIA security triad.",
        "Ethical Hacking",
        12,
        60,
        hacking_questions
    )

    # ==========================================
    # 5. Mobile Programming Quiz
    # ==========================================
    mobile_questions = [
        (
            "Which method in the Android Activity lifecycle is called first during component initialization?",
            "onStart()",
            "onResume()",
            "onCreate()",
            "onAttach()",
            "C",
            "onCreate() is the initial lifecycle callback where view binding, layout inflation (setContentView), and data initialization occur.",
            2
        ),
        (
            "What is the main role of the AndroidManifest.xml file in an Android application?",
            "Contains UI theme colors and vector assets",
            "Declares application components, user permissions, and hardware feature requirements",
            "Compiles Java and Kotlin source code into DEX format",
            "Manages local SQLite database schemas",
            "B",
            "AndroidManifest.xml declares essential app components (Activities, Services, Receivers), permissions, and hardware requirements to the Android OS.",
            2
        ),
        (
            "What is the key difference between an Explicit Intent and an Implicit Intent in Android?",
            "Explicit Intent targets a specific component class; Implicit Intent requests an action for any capable app to handle",
            "Explicit Intent is used only for background threads",
            "Implicit Intent requires device root access",
            "There is no difference between them",
            "A",
            "Explicit Intents name a specific class to launch (e.g. DetailActivity), while Implicit Intents declare a general action (e.g. ACTION_VIEW for URLs).",
            2
        ),
        (
            "Which Android Architecture Component survives configuration changes (such as device screen rotation)?",
            "Activity",
            "ViewModel",
            "SharedPreferences",
            "BroadcastReceiver",
            "B",
            "A ViewModel is designed to outlive configuration changes, retaining state and data without re-fetching.",
            2
        ),
        (
            "In modern frameworks like Jetpack Compose and Flutter, what UI development paradigm is utilized?",
            "Declarative UI (UI is a direct function of State)",
            "Imperative manual DOM tree manipulation",
            "Component Object Model (COM) event dispatching",
            "Static HTML pre-rendering",
            "A",
            "Declarative UI frameworks describe the interface based on the current state; when state changes, the framework re-renders the UI automatically.",
            2
        )
    ]
    add_quiz_if_missing(
        "Mobile Programming & App Architecture",
        "Android lifecycle, AndroidManifest, Explicit vs Implicit Intents, ViewModels, and Declarative UI.",
        "Mobile Programming",
        12,
        60,
        mobile_questions
    )

    conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized and seeded successfully at:", DB_PATH)

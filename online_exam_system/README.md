# Online Exam and Quiz System (Mini Project)

A full-featured, secure, and modern web-based **Online Examination & Quiz Management System** built with **Python (Flask)**, **SQLite**, and **Bootstrap 5**.

---

## 🌟 Key Features

### 👨‍🎓 Candidate / Student Portal
- **Timed Exam Engine**: Real-time JavaScript countdown timer that automatically submits the exam when time expires.
- **Interactive Question Palette**:
  - Jump directly to any question.
  - Color-coded question states: Answered (Green), Flagged for Review (Orange), Unvisited (Gray).
  - "Mark for Review" toggle to bookmark questions.
- **Anti-Cheat Proctoring Monitor**: Detects window blurring and tab switching, displaying warning logs if a student navigates away from the test.
- **Instant Grading & Scorecard**: Percentage calculation, pass/fail status, marks obtained, and time spent.
- **Answer Review with Explanations**: Review student's selected answer vs the correct answer with in-depth conceptual explanations.
- **Printable Certificate of Achievement**: Passing candidates can view and print/save a completion certificate with verification ID.

### 👨‍🏫 Instructor / Admin Portal
- **Analytics Dashboard**: Summary metrics (Total quizzes, enrolled candidates, submissions, platform average score).
- **Quiz Management**: Create, edit, activate/deactivate, and delete quizzes with customizable time limits and passing thresholds.
- **Question Bank**: Add multiple-choice questions (MCQs) with options A, B, C, D, designated correct option, custom mark weights, and explanations.
- **Submission Records & Filtering**: Filter and inspect all candidate attempts, review scorecards, and reset/delete attempts.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.x, Flask |
| **Database** | SQLite3 (Zero setup, embedded, relational) |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, FontAwesome 6 |
| **Security** | Werkzeug Password Hashing (`generate_password_hash`, `check_password_hash`), Session Authentication, Role-Based Access Control |

---

## 🚀 Quick Start Guide

### 1. Requirements
Ensure Python 3.8+ is installed on your computer.

### 2. Install Dependencies
Open your terminal inside the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database
Run the database setup script to generate tables and seed sample quizzes:
```bash
python database.py
```

### 4. Run the Web Server
Launch the Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default Credentials

For quick evaluation, sample accounts with pre-loaded exams are seeded out of the box:

| Role | Email / Username | Password | Notes |
|---|---|---|---|
| Role | Email / Username | Password | Notes |
|---|---|---|---|
| **Admin / Teacher** | `admin@exam.com` or `admin` | `Admin@123` *(Initial default; change anytime via dashboard)* | **Strict Single Login Enforced**: Private manual login required. Demo admin is disabled. |
| **Student / Candidate** | `student@exam.com` or `student` | `student123` | Can take exams & view certificates (Quick 1-Click demo available) |

*(Note: Admin demo login has been removed for security. The Admin can change their password at any time via the "Change Password" button in the Admin Dashboard, ensuring the password is known strictly only to himself).*

### 📚 Pre-loaded Subject Quizzes:
1. **HTML5**: *HTML5 & Web Markup Essentials* (Semantic tags, Canvas, DOCTYPE, forms)
2. **CSS3**: *CSS3 Styling & Modern Layouts* (Box Model, Flexbox, Grid, Specificity)
3. **C++**: *C++ Programming & OOP Architecture* (Virtual destructors, Smart pointers, RAII, vtables)
4. **Ethical Hacking**: *Ethical Hacking & Cybersecurity Essentials* (SQLi, XSS, ARP spoofing, SYN scans, CIA Triad)
5. **Mobile Programming**: *Mobile Programming & App Architecture* (Android Lifecycle, Manifest, Intents, ViewModels, Declarative UI)

---

## 📂 Project Directory Structure

```
online_exam_system/
│── app.py                   # Main Flask routes, auth decorators, and application logic
│── database.py              # SQLite schema, table initialization, and seed sample quizzes
│── exam_system.db           # SQLite database file (created automatically)
│── requirements.txt         # Python package dependencies
│── README.md                # Project documentation and guide
│── static/
│   ├── css/
│   │   └── style.css        # Custom styles, badges, responsive layout, certificate theme
│   └── js/
│       └── exam.js          # Countdown timer, palette switcher, anti-cheat detection
└── templates/
    ├── base.html            # Global base template with responsive navbar & alerts
    ├── index.html           # Landing page with feature highlights & quick links
    ├── login.html           # Authentication page with 1-click demo login buttons
    ├── register.html        # Account registration for students & instructors
    ├── student/
    │   ├── dashboard.html   # Student home: available tests, progress, attempt history
    │   ├── start.html       # Exam instructions & guidelines preview
    │   ├── take_exam.html   # Interactive test-taking screen with timer & question palette
    │   ├── result.html      # Scorecard, pass/fail result, and detailed answer review
    │   └── certificate.html # Printable completion certificate with seal & verification ID
    └── admin/
        ├── dashboard.html   # Admin metrics overview & quiz management table
        ├── quiz_form.html   # Create & Edit quiz configuration form
        ├── questions.html   # MCQ question manager (Add, view, delete questions)
        └── results.html     # All candidate submissions table with quiz filter
```

---

## 🎓 College Viva / Project Presentation Q&A

1. **How is the timer managed and how is cheating prevented?**
   - The countdown timer runs on the client-side using JavaScript `setInterval`. Even if the student attempts to modify the client timer, the server tracks start/submission timestamps and checks answer submissions against questions registered in the database.
   - The anti-cheat module monitors window blur and `document.visibilitychange` events to detect when a student leaves the exam window or switches tabs.
2. **How does automatic evaluation work?**
   - When the candidate submits, `app.py` compares the submitted radio button selections against the `correct_option` field in the `questions` database table. Score is calculated by summing the allocated marks for each correct choice, computing percentage, and determining pass/fail status against the quiz threshold.
3. **What database is used and why?**
   - SQLite3 is used because it is lightweight, serverless, ACID-compliant, and built into standard Python. It requires zero configuration on any machine.

import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, session
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "messages.db")
RESUME_DIR = os.path.join(BASE_DIR, "static", "files")
RESUME_FILENAME = "Sejal_Mishra_Resume.pdf"
PROFILE_PHOTO_PATH = os.path.join(BASE_DIR, "static", "images", "profile.jpg")

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()

PROFILE = {
    "name": "Sejal Mishra",
    "title": "BCA Student",
    "tagline": "Final-year BCA student seeking an internship opportunity.",
    "location": "Surat, Gujarat",
    "email": "sejalmishra173@gmail.com",
    "github": "https://github.com/sejall-mishra",
    "linkedin": "https://www.linkedin.com/in/sejal-mishra-84402b447",
    "about": (
        "I'm a TYBCA student passionate about building real-world projects with "
        "Python, PHP and SQL. I love turning ideas into working applications and "
        "I'm always eager to learn from experienced developers. Currently looking "
        "for an internship where I can apply my skills and grow as a developer."
    ),
    "initials": "SM",
}

SKILLS = {
    "Languages & Web": ["Python", "PHP", "HTML", "CSS", "JavaScript"],
    "Database": ["MySQL", "SQLite", "SQL"],
    "Tools": ["Git", "GitHub", "XAMPP"],
}

EDUCATION = [
    {"degree": "BCA (TYBCA)", "institute": "Sutex Bank College of Commerce and Science",
     "score": "Sem 1-4: 8.18, 8.18, 7.55, 8.36"},
    {"degree": "12th Grade (GSEB)", "institute": "E.E. Dawjee Memorial English Medium School",
     "score": "92.08%"},
    {"degree": "10th Grade (GSEB)", "institute": "E.E. Dawjee Memorial English Medium School",
     "score": "96.74%"},
]

PROJECTS = [
    {"title": "Student Management System", "tech": "Python · MySQL",
     "description": "A full CRUD application to manage student records — add, update, delete and search students. Data is stored and queried in a MySQL database, with reports for attendance and grades.",
     "link": PROFILE["github"]},
    {"title": "Exolia Travel Website", "tech": "PHP · MySQL · XAMPP",
     "description": "Dynamic travel website with user registration/login, destination browsing, booking with history, search & filter, an enquiry form, and an admin panel backed by MySQL.",
     "link": PROFILE["github"]},
    {"title": "Expense Tracker", "tech": "Python · SQLite",
     "description": "Console app to add, view and delete expenses with a category-wise spending summary using SQL GROUP BY, and parameterised queries to prevent SQL injection.",
     "link": PROFILE["github"]},
    {"title": "Quiz Game", "tech": "Python · OOP · JSON",
     "description": "Built with Question, Quiz and Leaderboard classes. Questions load from a JSON file with randomised order, input validation and a saved leaderboard.",
     "link": PROFILE["github"]},
    {"title": "Tic-Tac-Toe with AI", "tech": "Python · Minimax",
     "description": "Play against the computer in Easy mode or Unbeatable mode, powered by the Minimax algorithm with recursion.",
     "link": PROFILE["github"]},
    {"title": "Snake Game", "tech": "Python · Turtle",
     "description": "Classic snake game with three difficulty levels, pause/resume, collision detection and a high score saved to file.",
     "link": PROFILE["github"]},
    {"title": "Hangman", "tech": "Python · OOP · JSON",
     "description": "Word categories loaded from JSON, with a hint system, ASCII graphics and a win record tracker.",
     "link": PROFILE["github"]},
]

LANGUAGES = ["English", "Hindi", "Gujarati"]


@app.context_processor
def inject_globals():
    return {
        "profile": PROFILE,
        "has_photo": os.path.exists(PROFILE_PHOTO_PATH),
        "year": datetime.now().year,
    }


def send_email_notification(name, sender_email, message):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("⚠️ Email not configured — skipping email send.")
        return False
    try:
        body = (
            f"New message from your portfolio contact form:\n\n"
            f"Name: {name}\n"
            f"Email: {sender_email}\n"
            f"Message:\n{message}\n"
        )
        msg = MIMEText(body)
        msg["Subject"] = f"Portfolio Contact: {name}"
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg["Reply-To"] = sender_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def home():
    return render_template(
        "index.html",
        skills=SKILLS,
        education=EDUCATION,
        projects=PROJECTS,
        languages=LANGUAGES,
    )


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("home") + "#contact")

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
        (name, email, message, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()

    send_email_notification(name, email, message)

    flash("Thanks for reaching out! I'll get back to you soon.", "success")
    return redirect(url_for("home") + "#contact")


@app.route("/download-resume")
def download_resume():
    return send_from_directory(RESUME_DIR, RESUME_FILENAME, as_attachment=True)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_messages"))
        flash("Incorrect password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/messages")
@login_required
def admin_messages():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_messages.html", messages=rows)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
# app.py — Cloud MySQL Version (Railway-ready)
from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import secrets
import mysql.connector
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
import os
import random
import string

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

app.config['SESSION_TYPE'] = "filesystem"

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

# -------------------- Cloud MySQL Connection --------------------
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT", 3306))
    )




# Create users table on startup
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(10) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    emoji VARCHAR(10)
)
""")
conn.commit()
cursor.close()
conn.close()

# -------------------- Helpers --------------------
otp_store = {}
reset_tokens = {}
login_attempts = {}
emojis = ["😀", "🎉", "🚀", "🔥", "🌟", "💎", "✨"]

def validate_password(password, last_name, phone):
    last3 = last_name[-3:].lower()
    caps = [c.upper() for c in last3]

    if not any(c in password for c in caps):
        return False, f"Password must include uppercase from: {', '.join(caps)}"

    if phone[-2:] not in password:
        return False, "Password must contain last 2 digits of phone."

    return True, "OK"


def auto_generate_password(last_name=None, phone=None):
    # Google-style password: xxxx-xxxx-xxxx (12 characters with hyphens)
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    all_chars = lower + upper + digits
    
    # Ensure at least one lowercase, one uppercase, and one digit
    pwd_chars = [
        random.choice(lower),
        random.choice(upper),
        random.choice(digits)
    ] + random.choices(all_chars, k=9)
    
    random.shuffle(pwd_chars)
    
    # Format as xxxx-xxxx-xxxx
    part1 = "".join(pwd_chars[:4])
    part2 = "".join(pwd_chars[4:8])
    part3 = "".join(pwd_chars[8:])
    return f"{part1}-{part2}-{part3}"



def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_user_by_name(name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE name=%s", (name,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


# -------------------- ROUTES --------------------

@app.route('/')
def home():
    if session.get("username"):
        return redirect('/dashboard')
    return render_template("signup.html")


# -------- SIGNUP --------
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').lower()

    if get_user_by_email(email):
        flash("Email already exists.")
        return redirect('/')

    last_name = name.split()[-1]

    if 'auto_password' in request.form:
        password = auto_generate_password(last_name, phone)
        generated = True
    else:
        password = request.form.get('password', '')
        valid, msg = validate_password(password, last_name, phone)
        if not valid:
            flash(msg)
            return redirect('/')
        generated = False

    hashed = pbkdf2_sha256.hash(password)
    emoji = random.choice(emojis)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, phone, email, password, emoji) VALUES (%s, %s, %s, %s, %s)",
        (name, phone, email, hashed, emoji)
    )
    conn.commit()
    cursor.close()
    conn.close()

    if generated:
        flash(f"Signup successful! Auto-generated password: {password}")
    else:
        flash("Signup successful! You can now log in.")
    return redirect('/login')


# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    name = request.form.get('name')
    password = request.form.get('password')

    user = get_user_by_name(name)
    if not user:
        flash("User not found.")
        return redirect('/login')

    if not pbkdf2_sha256.verify(password, user['password']):
        flash("Wrong password!")
        return redirect('/login')

    session['username'] = user['name']
    session['email'] = user['email']
    return redirect('/dashboard')


# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if not session.get('username'):
        return redirect('/login')

    user = get_user_by_name(session['username'])
    return render_template("dashboard.html", username=user['name'], emoji=user['emoji'])


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# -------- SNAKE GAME --------
@app.route('/snake')
def snake_game():
    if not session.get("username"):
        return redirect('/login')
    return render_template("snake.html", username=session['username'])


# -------- FORGOT PASSWORD (OTP SEND) --------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template("forgot.html")

    email = request.form.get('email').lower()
    user = get_user_by_email(email)

    if not user:
        flash("Email not found.")
        return redirect('/forgot')

    otp = str(secrets.randbelow(900000) + 100000)
    otp_store[email] = (otp, datetime.utcnow() + timedelta(minutes=5))

    msg = Message("CyberAuth OTP", sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f"Your OTP is {otp}. It expires in 5 minutes."
    mail.send(msg)

    flash("OTP sent to email.")
    return redirect(url_for('verify_otp_page', email=email))


# -------- OTP VERIFY PAGE --------
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_page():
    if request.method == 'GET':
        return render_template("verify_otp.html", email=request.args.get('email'))

    email = request.form.get('email')
    entered = request.form.get('otp')

    if email not in otp_store:
        flash("OTP expired or invalid.")
        return redirect('/forgot')

    otp, expiry = otp_store[email]

    if datetime.utcnow() > expiry:
        otp_store.pop(email)
        flash("OTP expired.")
        return redirect('/forgot')

    if entered != otp:
        flash("Incorrect OTP.")
        return redirect(url_for('verify_otp_page', email=email))

    token = secrets.token_urlsafe(24)
    reset_tokens[token] = (email, datetime.utcnow() + timedelta(minutes=10))

    otp_store.pop(email)
    return redirect(url_for('reset_password_page', token=token))


# -------- RESET PASSWORD PAGE --------
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_page(token):
    if token not in reset_tokens:
        flash("Invalid or expired link.")
        return redirect('/forgot')

    email, expiry = reset_tokens[token]
    if datetime.utcnow() > expiry:
        reset_tokens.pop(token)
        flash("Reset link expired.")
        return redirect('/forgot')

    if request.method == 'GET':
        return render_template("reset_password.html", email=email, token=token)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    name = user['name']
    phone = user['phone']
    last_name = name.split()[-1]

    if 'auto_password' in request.form:
        new_pass = auto_generate_password(last_name, phone)
        gen = True
    else:
        new_pass = request.form.get('password')
        valid, msg = validate_password(new_pass, last_name, phone)
        if not valid:
            flash(msg)
            return redirect(url_for('reset_password_page', token=token))
        gen = False

    hashed = pbkdf2_sha256.hash(new_pass)

    cursor2 = conn.cursor()
    cursor2.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))
    conn.commit()
    cursor.close()
    cursor2.close()
    conn.close()

    reset_tokens.pop(token)

    if gen:
        flash(f"Password reset successful! Your new password: {new_pass}")
    else:
        flash("Password reset successful!")

    return redirect('/login')


# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

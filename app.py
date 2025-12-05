from flask import Flask, render_template, request, redirect, flash, url_for
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
app.secret_key = "supersecretkey"

# MySQL connection
db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    port=os.getenv("MYSQL_PORT")
)

cursor = db.cursor()

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT"))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS") == "True"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

# Stores OTP & reset tokens temporarily
otp_store = {}       # email → (otp, expiry)
reset_tokens = {}    # token → (email, expiry)

emojis = ["😀", "🎉", "🚀", "🔥", "🌟", "💎", "✨"]


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------
def validate_password(password, last_name, aadhar, phone):
    last3 = last_name[-3:].lower()
    required_caps = [c.upper() for c in last3]

    contains_cap = any(c.upper() in password for c in last3)

    aadhar_last2 = aadhar[-2:]
    phone_last2 = phone[-2:]

    if not contains_cap:
        return False, f"Password must include one uppercase letter from: {', '.join(required_caps)}"

    if aadhar_last2 not in password:
        return False, f"Password must include last 2 digits of Aadhar: {aadhar_last2}"

    if phone_last2 not in password:
        return False, f"Password must include last 2 digits of Phone: {phone_last2}"

    return True, "OK"


# --------------------------------------------------
# AUTO-GENERATED PASSWORD
# --------------------------------------------------
def auto_generate_password(last_name, aadhar, phone):
    last3 = last_name[-3:].lower()
    cap_letter = random.choice([c.upper() for c in last3])

    aadhar_last2 = aadhar[-2:]
    phone_last2 = phone[-2:]

    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=4))

    base = cap_letter + aadhar_last2 + phone_last2 + random_part
    base = list(base)
    random.shuffle(base)
    return ''.join(base)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
@app.route('/')
def home():
    return render_template("signup.html")


# --------------------------------------------------
# SIGNUP ROUTE
# --------------------------------------------------
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    aadhar = request.form['aadhar']
    phone = request.form['phone']
    email = request.form['email']

    parts = name.split()
    if len(parts) < 2:
        flash("Enter full name: first + last.")
        return redirect('/')

    last_name = parts[-1]

    if len(aadhar) != 12 or not aadhar.isdigit():
        flash("Aadhar must be exactly 12 digits.")
        return redirect('/')

    if len(phone) != 10 or not phone.isdigit():
        flash("Phone must be exactly 10 digits.")
        return redirect('/')

    if 'auto_password' in request.form:
        password = auto_generate_password(last_name, aadhar, phone)
        generated = True
    else:
        password = request.form['password']
        generated = False
        valid, msg = validate_password(password, last_name, aadhar, phone)
        if not valid:
            flash(msg)
            return redirect('/')

    hashed_pass = pbkdf2_sha256.hash(password)
    reward = random.choice(emojis)

    sql = "INSERT INTO users(name, aadhar, phone, email, password, emoji) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, (name, aadhar, phone, email, hashed_pass, reward))
    db.commit()

    if generated:
        flash(f"Signup successful! Your auto-generated password is: {password}")
    else:
        flash("Signup successful! You may login now.")

    return redirect('/login')


# --------------------------------------------------
# LOGIN ROUTE
# --------------------------------------------------
login_attempts = {}

@app.route('/login')
def login_page():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password']

    sql = "SELECT password, emoji FROM users WHERE name=%s"
    cursor.execute(sql, (name,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!")
        return redirect('/login')

    hashed_pass, emoji = user

    if name not in login_attempts:
        login_attempts[name] = 0

    if login_attempts[name] >= 3:
        flash("❌ Too many attempts! Try Forgot Password.")
        return redirect('/forgot')

    if pbkdf2_sha256.verify(password, hashed_pass):
        login_attempts[name] = 0
        return render_template("dashboard.html", username=name, emoji=emoji)
    else:
        login_attempts[name] += 1
        flash(f"Wrong password! Attempts left: {3 - login_attempts[name]}")
        return redirect('/login')
    

# --------------------------------------------------
# SNAKE GAME ROUTE
# --------------------------------------------------
@app.route('/snake')
def snake_game():
    # If you pass username from dashboard: ?username={{ username }}
    username = request.args.get('username', 'Player')
    return render_template("snake.html", username=username)


# --------------------------------------------------
# FORGOT PASSWORD (SEND OTP)
# --------------------------------------------------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Check if email exists
        sql = "SELECT name FROM users WHERE email=%s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()

        if not user:
            flash("Email not found!")
            return redirect('/forgot')

        username = user[0]

        # Generate 6-digit OTP
        otp = str(secrets.randbelow(900000) + 100000)

        # Save OTP + expiry
        expiry = datetime.utcnow() + timedelta(minutes=5)
        otp_store[email] = (otp, expiry)

        # Send Email
        msg = Message("CyberAuth Password Reset OTP",
                      sender=os.getenv("MAIL_USERNAME"),
                      recipients=[email])
        msg.body = f"Hello {username},\n\nYour OTP is: {otp}\nIt expires in 5 minutes.\n\n– CyberAuth"

        mail.send(msg)

        flash("OTP sent to your email.")
        return redirect(url_for('verify_otp_page', email=email))

    return render_template("forgot.html")


# --------------------------------------------------
# VERIFY OTP
# --------------------------------------------------
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_page():
    if request.method == 'GET':
        email = request.args.get('email')
        return render_template("verify_otp.html", email=email)

    email = request.form['email']
    entered = request.form['otp']

    if email not in otp_store:
        flash("OTP expired or invalid. Request again.")
        return redirect('/forgot')

    otp, expiry = otp_store[email]

    if datetime.utcnow() > expiry:
        otp_store.pop(email)
        flash("OTP expired. Request a new one.")
        return redirect('/forgot')

    if entered != otp:
        flash("Incorrect OTP!")
        return redirect(url_for('verify_otp_page', email=email))

    # OTP Valid — create reset token
    token = secrets.token_urlsafe(24)
    reset_tokens[token] = (email, datetime.utcnow() + timedelta(minutes=10))
    otp_store.pop(email)

    return redirect(url_for('reset_password_page', token=token))



# --------------------------------------------------
# RESET PASSWORD
# --------------------------------------------------
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_page(token):
    if token not in reset_tokens:
        flash("Invalid or expired token.")
        return redirect('/forgot')

    email, expiry = reset_tokens[token]

    if datetime.utcnow() > expiry:
        reset_tokens.pop(token)
        flash("Reset token expired!")
        return redirect('/forgot')

    if request.method == 'GET':
        return render_template("reset_password.html", email=email, token=token)

    cursor.execute("SELECT name, aadhar, phone FROM users WHERE email=%s", (email,))
    name, aadhar, phone = cursor.fetchone()
    last_name = name.split()[-1]

    if 'auto_password' in request.form:
        new_password = auto_generate_password(last_name, aadhar, phone)
        generated = True
    else:
        new_password = request.form['password']
        generated = False
        valid, msg = validate_password(new_password, last_name, aadhar, phone)
        if not valid:
            flash(msg)
            return redirect(url_for('reset_password_page', token=token))

    hashed = pbkdf2_sha256.hash(new_password)
    cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, email))
    db.commit()

    reset_tokens.pop(token)

    if generated:
        flash(f"Password reset successful! Your new password: {new_password}")
    else:
        flash("Password reset successful.")

    return redirect('/login')


# --------------------------------------------------
# RUN APP
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

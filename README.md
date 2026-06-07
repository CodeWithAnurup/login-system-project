# CyberAuth — Secure Full-Stack Authentication System

CyberAuth is a modern, responsive full-stack authentication web application built using **Python (Flask)** and integrated with a **cloud-hosted MySQL database (Aiven)**. It features secure user registration, password verification, auto-generated strong passwords (Google-suggested style), dynamic dashboards, secure session management, and a password recovery flow utilizing time-sensitive **SMTP Email OTP (One-Time Password) Verification**.

---

## 🌟 Key Features

* **Secure Authentication:** Robust user registration and login flows.
* **Password Security:** Multi-layered security using **PBKDF2-SHA256 password hashing** (passwords are never stored as plain text).
* **Password Validation:** Enforces custom complexity rules for manual passwords.
* **Smart Password Generator:** Instantly generates strong, Google-suggested format passwords (`xxxx-xxxx-xxxx`) using secure random selection.
* **Cloud Database:** Integrated with a production-ready **Aiven MySQL** cloud instance with SSL mode enabled.
* **Email OTP Verification:** Implements password recovery using secure, 6-digit verification codes sent via **SMTP Gmail integration** (valid for 5 minutes).
* **Interactive Dashboard:** Dynamic user dashboard featuring customizable user profiles and an integrated web game.
* **Nokia Snake Game:** A fully interactive retro Snake game embedded directly inside the user dashboard.

---

## 🛠️ Tech Stack

* **Backend Framework:** Python & Flask
* **Database:** Cloud MySQL (Hosted on Aiven)
* **Frontend:** Responsive HTML5, CSS3, & Jinja2 Templates
* **Production Server:** Gunicorn (Deployment-ready)
* **Environment Configuration:** Python-Dotenv

---

## 📁 Project Structure

```text
login-system-project/
│
├── static/
│   ├── style.css           # Styling for the application
│   └── *.jpg               # Assets & images
│
├── templates/
│   ├── signup.html         # User Registration view
│   ├── login.html          # User Login view
│   ├── dashboard.html      # Dynamic user dashboard
│   ├── snake.html          # Nokia Snake Game page
│   ├── forgot.html         # OTP request view
│   ├── verify_otp.html     # OTP code submission view
│   └── reset_pass.html     # Password reset form
│
├── app.py                  # Main Flask application logic
├── requirements.txt        # Python package dependencies
├── Procfile                # Deployment instruction file for Gunicorn
├── railway.toml            # Deployment configurations
├── .gitignore              # Files to ignore in Git (such as .env)
└── README.md               # Project documentation
```

---

## 🚀 Step-by-Step Setup and Installation

Follow these instructions to run the project locally on your machine:

### 1. Prerequisites
Ensure you have the following installed:
* [Python 3.8+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

### 2. Clone the Repository
Clone this repository to your local computer and navigate into the folder:
```bash
git clone https://github.com/CodeWithAnurup/login-system-project.git
cd login-system-project
```

### 3. Install Dependencies
Install all required Python libraries using pip:
```bash
pip install -r requirements.txt
```

### 4. Create and Configure Environment Variables (`.env`)
Create a file named `.env` in the root directory (next to `app.py`) and fill in your database and email credentials:

```env
# Cloud MySQL database credentials (e.g., Aiven or TiDB Cloud)
MYSQL_HOST=your-mysql-hostname.com
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=defaultdb
MYSQL_PORT=20652

# Secret key for encrypting sessions
SECRET_KEY=yoursecretkeyhere

# SMTP settings for Email OTP recovery (Gmail Example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```
*(Note: For Gmail SMTP, you must generate a 16-character **App Password** from your Google Account settings, rather than using your main account password).*

### 5. Running the Application
Run the main script to start the local Flask development server:
```bash
python app.py
```
After starting the server, open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔒 Security Practices Demonstrated

1. **Environment Separation:** Sensitive secrets (database passwords, API credentials, secret keys) are stored in a `.env` file that is kept out of Git via `.gitignore`.
2. **Password Cryptography:** Employs industry-standard **PBKDF2-SHA256 salt-based hashing** to secure passwords.
3. **Session Management:** Restricts access to dashboard pages. Users must be actively logged in with a valid session cookie to view protected routes.
4. **Time-Limited OTPs:** Generated recovery OTPs expire after 5 minutes and are verified securely from server-side memory to mitigate brute-force attempts.

---

## 🔮 Future Roadmap (AI Integration)

To further elevate the project's security and capabilities, the following advanced AI-powered modules are planned for integration:

### 1. AI-Powered Face Recognition Login (Passwordless Auth)
* **Concept:** Implement webcam-based facial recognition for a secure, passwordless authentication experience.
* **Mechanism:** Utilize Python's `face_recognition` and `OpenCV` libraries on the backend to extract 128-dimensional facial embeddings, comparing them in real-time against stored templates.
* **Liveness Detection:** Integrate blink and motion detection on the client-side to prevent spoofing attacks (e.g. holding a photo up to the camera).

### 2. Smart Anomaly & Risk Detection Engine
* **Concept:** A smart engine to dynamically evaluate the security risk score of every login attempt and prevent unauthorized access.
* **Mechanism:** Maintain a `login_history` dataset to monitor parameters such as user IP, geolocation, device signatures, and login timestamps.
* **Contextual 2FA:** If a login attempt deviates significantly from the user's historical baseline (e.g. logging in from a new device or country at 3 AM), the system automatically triggers the SMTP-based OTP email verification flow to confirm identity.


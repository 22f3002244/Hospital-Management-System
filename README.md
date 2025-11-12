# Hospital Management System

A comprehensive full-stack hospital management system built with Vue.js 3 frontend and Flask backend, featuring role-based dashboards for administrators, doctors, and patients with automated notifications and reporting.

## 🏥 Overview

This Hospital Management System enables:
- **Patients** to register, book appointments, view medical history, and receive records via email
- **Doctors** to manage appointments, set availability schedules, and update patient treatment records
- **Administrators** to oversee all operations, manage doctors and patients, and monitor system statistics
- **Automated notifications** via email for appointment confirmations, reminders, and reports
- **Asynchronous task processing** using Celery for background jobs

## 🚀 Features

### Patient Features
- User registration and authentication
- Browse departments and doctors
- Book appointments with real-time slot availability
- View and manage upcoming appointments
- Access complete medical history
- Receive medical records via email as PDF
- Update personal profile information
- Daily appointment reminders

### Doctor Features
- Dedicated doctor dashboard
- View and manage appointments
- Set weekly availability schedules (7-day rolling window)
- Update patient treatment records with diagnosis and prescriptions
- View patient history and treatment details
- Cancel appointments
- Monthly activity reports via email

### Admin Features
- Comprehensive admin dashboard with system statistics
- Manage doctors (add, edit, remove)
- Manage patients (view, remove)
- View all appointments and their status
- Monitor department-wise operations
- System-wide oversight

### Automated Features
- Email notifications for appointment confirmations and cancellations
- Daily appointment reminders sent at 8:00 AM
- Monthly doctor activity reports (sent on 1st of each month)
- PDF medical record generation and email delivery
- CSV export of patient treatment history
- Background task processing with Celery
- Redis caching for improved performance

## 🛠️ Tech Stack

### Frontend
- **Framework:** Vue.js 3 (Composition API)
- **State Management:** Pinia
- **Routing:** Vue Router 4
- **HTTP Client:** Axios
- **UI Framework:** Bootstrap 5
- **Icons:** Bootstrap Icons
- **Build Tool:** Vite (with Rolldown)

### Backend
- **Framework:** Flask 3.1.2
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** Session-based with Werkzeug security
- **Task Queue:** Celery 5.3.4
- **Message Broker:** Redis
- **Caching:** Flask-Caching with Redis
- **Email:** Flask-Mail (SMTP)
- **PDF Generation:** ReportLab
- **CORS:** Flask-CORS

## 📋 Prerequisites

### Software Requirements
- **Node.js:** ^20.19.0 || >=22.12.0
- **Python:** 3.8+
- **Redis:** Latest stable version
- npm or yarn package manager
- pip: Python package manager

### Services
- Gmail account for SMTP email sending (or other SMTP server)
- Redis server running on localhost:6379

## 🔧 Installation

### Backend Setup

1. **Clone the repository and navigate to backend:**
```bash
git clone https://github.com/22f3002244/Hospital-Management-System
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
Create a `.env` file in the backend directory:
```env
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password

ADMIN_EMAIL=admin@hospital.com
ADMIN_PASSWORD=admin123

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CACHE_REDIS_URL=redis://localhost:6379/1
```

**Note for Gmail:**
- Use App-Specific Password (not your regular Gmail password)
- Enable 2-factor authentication on your Google account
- Generate app password from Google Account Security settings

5. **Start Redis server:**
```bash
# On Windows (using Windows Subsystem for Linux or native Redis)
redis-server

# On macOS
brew services start redis

# On Linux
sudo systemctl start redis
```

6. **Start Celery worker:**
Open a new terminal, activate virtual environment, and run:
```bash
celery -A tasks.celery_tasks.celery worker --loglevel=info
```

7. **Start Celery beat scheduler (for scheduled tasks):**
Open another terminal, activate virtual environment, and run:
```bash
celery -A tasks.celery_tasks.celery beat --loglevel=info
```

8. **Run Flask application:**
```bash
python app.py
```
Backend will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Run development server:**
```bash
npm run dev
```
Frontend will be available at `http://localhost:3000`

## 📁 Project Structure
```
hospital-management-system/
├── backend/
│   ├── models/
│   │   └── database.py          # SQLAlchemy models
│   ├── routes/
│   │   └── routes.py            # API routes
│   ├── tasks/
│   │   └── celery_tasks.py      # Celery tasks
│   ├── app.py                   # Flask application
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables
│   └── hospital.db              # SQLite database (auto-generated)
│
└── frontend/
    ├── src/
    │   ├── assets/              # Static assets
    │   ├── router/              # Vue Router
    │   │   └── index.js
    │   ├── stores/              # Pinia stores
    │   │   └── auth.js
    │   ├── views/               # Page components
    │   │   ├── AdminDashboard.vue
    │   │   ├── DoctorDashboard.vue
    │   │   ├── PatientDashboard.vue
    │   │   ├── PatientHistory.vue
    │   │   ├── DoctorAvailability.vue
    │   │   ├── DepartmentView.vue
    │   │   ├── LoginView.vue
    │   │   └── RegisterView.vue
    │   ├── App.vue
    │   └── main.js
    ├── public/
    ├── index.html
    ├── vite.config.js
    └── package.json
```

## 🗄️ Database Schema
<img width="2715" height="2129" alt="HMS-schema" src="https://github.com/user-attachments/assets/7ff3a8c2-ea52-409e-b1ba-d11636ffbd99" />


## 🔐 Authentication & Authorization

### Session-Based Authentication
- Cookie-based session management
- Role-based access control (Admin, Doctor, Patient)
- Password hashing using Werkzeug security
- CSRF protection via credentials

### Default Admin Account
```
Username: admin
Password: admin123
Email: admin@hospital.com
```

### Route Protection
- `@login_required`: Requires any authenticated user
- `@admin_required`: Requires admin privileges
- `@doctor_required`: Requires doctor authentication

## 🌐 API Endpoints

### Authentication
```
POST   /register              # Register new patient
POST   /login                 # User/Doctor/Admin login
POST   /logout                # Logout current session
```

### Admin Routes
```
GET    /admin/dashboard       # Admin dashboard data
GET    /admin/doctors         # List all doctors
POST   /admin/doctor          # Add new doctor
PUT    /admin/doctor/:id      # Update doctor profile
DELETE /admin/doctor/:id      # Remove doctor
DELETE /admin/patient/:id     # Remove patient
```

### Doctor Routes
```
GET    /doctor/:id/dashboard               # Doctor dashboard
POST   /appointment/:id/treatment          # Add/update treatment
POST   /doctors/:id/availability           # Save availability schedule
GET    /doctors/:id/availability           # Get availability
GET    /doctors/:id/available-slots        # Get available time slots
```

### Patient Routes
```
GET    /patient/:id/dashboard              # Patient dashboard
PUT    /patient/:id                        # Update patient profile
GET    /patient/:id/history                # Patient medical history
```

### Appointment Routes
```
POST   /appointment                        # Book appointment
DELETE /appointment/:id                    # Cancel appointment
GET    /appointment/:id/details            # Get appointment details
POST   /appointment/:id/send-record        # Email medical record PDF
POST   /appointment/:id/notify-confirmed   # Send confirmation email
POST   /appointment/:id/notify-cancelled   # Send cancellation email
```

### Department Routes
```
GET    /departments                        # List all departments
GET    /departments/:id/doctors            # Get doctors by department
```

### Export & Tasks
```
POST   /export-patient/:id                 # Export patient data (CSV)
GET    /task-status/:task_id               # Check Celery task status
```

## 📧 Email Notifications

### Automated Emails
- **Appointment Confirmation:** Triggered when appointment is booked
- **Appointment Cancellation:** Triggered when appointment is cancelled
- **Daily Reminders:** Every day at 8:00 AM (Asia/Kolkata timezone) for patients with appointments
- **Monthly Doctor Reports:** 1st of every month at 9:00 AM with appointment statistics
- **Medical Record PDF:** On patient request with complete appointment and treatment details

## 🔄 Celery Tasks

### Background Tasks
- `send_appointment_confirmed` - Send confirmation email
- `send_appointment_cancelled` - Send cancellation email
- `daily_reminder` - Scheduled daily at 8:00 AM
- `monthly_doctor_report` - Scheduled monthly on 1st at 9:00 AM
- `export_patient_treatments` - Export patient data to CSV
- `send_appointment_record_pdf` - Generate and email PDF record

## ⚡ Caching

**Redis Cache Configuration:**
- Type: RedisCache
- URL: redis://localhost:6379/1
- Default Timeout: 300 seconds (5 minutes)
- Cached Endpoints: `/departments`

## 🛠️ Development Commands

### Backend
```bash
# Run Flask app
python app.py

# Run Celery worker
celery -A tasks.celery_tasks.celery worker --loglevel=info

# Run Celery beat
celery -A tasks.celery_tasks.celery beat --loglevel=info

# Monitor Celery tasks
celery -A tasks.celery_tasks.celery flower
```

### Frontend
```bash
# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## 🔒 Security Features
- Password hashing with Werkzeug
- CSRF protection via credentials
- Session-based authentication
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (Vue.js escaping)
- Role-based access control
- Input validation on both frontend and backend

## 📝 Environment Variables Reference
```env
# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Email
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Admin
ADMIN_EMAIL=admin@hospital.com
ADMIN_PASSWORD=admin123

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CACHE_REDIS_URL=redis://localhost:6379/1
```

---

**Note:** This is a complete full-stack application. Ensure all services (Redis, Celery, Flask, Vite) are running for full functionality.

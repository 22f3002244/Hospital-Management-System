from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import io
import csv
import requests

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = Celery('hospital_tasks')

def send_gchat(webhook_url, text):
    """Send message to Google Chat webhook"""
    try:
        response = requests.post(
            webhook_url, 
            json={"text": text}, 
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"GChat send failed: {e}")
        return False

@celery.task(name='tasks.send_appointment_confirmed', bind=True)
def send_appointment_confirmed(self, appointment_id):
    from app import app, mail
    from backend.models.database import Appointment
    from flask_mail import Message
    
    with app.app_context():
        a = Appointment.query.get(appointment_id)
        if not a:
            return "appointment not found"

        patient = a.patient
        doctor = a.doctor
        body = (
            f"Hello {patient.full_name},\n\n"
            f"Your appointment is CONFIRMED with Dr. {doctor.name} "
            f"on {a.date.isoformat()} at {a.time.strftime('%H:%M')}.\n\n"
            "Please arrive 10 minutes early.\n\n"
            "Regards,\nHospital Management System"
        )

        # Send email
        if patient.email:
            try:
                msg = Message(
                    "Appointment Confirmed", 
                    recipients=[patient.email]
                )
                msg.body = body
                mail.send(msg)
            except Exception as e:
                print(f"Email send failed: {e}")

        webhook = getattr(patient, 'gchat_webhook', None)
        if webhook:
            send_gchat(webhook, body)

        return f"Confirmation sent for appointment {appointment_id}"

@celery.task(name='tasks.send_appointment_cancelled', bind=True)
def send_appointment_cancelled(self, appointment_id, reason=None):
    from app import app, mail
    from backend.models.database import Appointment
    from flask_mail import Message
    
    with app.app_context():
        a = Appointment.query.get(appointment_id)
        if not a:
            return "appointment not found"

        patient = a.patient
        doctor = a.doctor
        
        reason_text = f"\nReason: {reason}" if reason else ""
        body = (
            f"Hello {patient.full_name},\n\n"
            f"Your appointment with Dr. {doctor.name} "
            f"on {a.date.isoformat()} at {a.time.strftime('%H:%M')} "
            f"has been CANCELLED.{reason_text}\n\n"
            "Regards,\nHospital Management System"
        )

        if patient.email:
            try:
                msg = Message(
                    "Appointment Cancelled", 
                    recipients=[patient.email]
                )
                msg.body = body
                mail.send(msg)
            except Exception as e:
                print(f"Email send failed: {e}")

        webhook = getattr(patient, 'gchat_webhook', None)
        if webhook:
            send_gchat(webhook, body)

        return f"Cancellation notification sent for appointment {appointment_id}"

@celery.task(name='tasks.daily_reminder', bind=True)
def daily_reminder(self):
    from app import app, mail
    from backend.models.database import Appointment
    from flask_mail import Message
    
    with app.app_context():
        today = datetime.now().date()
        appts = Appointment.query.filter(
            Appointment.date == today,
            Appointment.status == 'booked'
        ).all()
        
        sent = 0
        for a in appts:
            patient = a.patient
            doctor = a.doctor
            dept_name = doctor.department.name if doctor.department else 'General'
            
            text = (
                f"Reminder: You have an appointment today with Dr. {doctor.name} "
                f"at {a.time.strftime('%H:%M')} in {dept_name} department."
            )
            
            if patient.email:
                try:
                    msg = Message(
                        "Appointment Reminder - Today", 
                        recipients=[patient.email]
                    )
                    msg.body = f"Hello {patient.full_name},\n\n{text}\n\nThanks,\nHospital"
                    mail.send(msg)
                    sent += 1
                except Exception as e:
                    print(f"Email send failed for patient {patient.id}: {e}")
            
            webhook = getattr(patient, 'gchat_webhook', None)
            if webhook:
                send_gchat(webhook, text)
        
        return f"Daily reminders sent: {sent} emails"

@celery.task(name='tasks.monthly_doctor_report', bind=True)
def monthly_doctor_report(self):
    from app import app, mail
    from backend.models.database import Doctor, Appointment
    from flask_mail import Message
    
    with app.app_context():
        # Calculate last month date range
        today = datetime.now().date()
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        doctors = Doctor.query.all()
        reports_sent = 0
        
        for doctor in doctors:
            appts = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.date >= last_month_start,
                Appointment.date <= last_month_end
            ).order_by(Appointment.date).all()

            # Build HTML report
            rows = ""
            total_consultations = len(appts)
            completed = sum(1 for a in appts if a.status == 'completed')
            
            for a in appts:
                treatment = a.treatment
                diagnosis = treatment.diagnosis if treatment else "N/A"
                prescription = treatment.prescription if treatment else "N/A"
                
                rows += f"""
                <tr>
                    <td>{a.patient.full_name}</td>
                    <td>{a.date.strftime('%Y-%m-%d')}</td>
                    <td>{a.time.strftime('%H:%M')}</td>
                    <td>{a.status}</td>
                    <td>{diagnosis}</td>
                    <td>{prescription[:50]}...</td>
                </tr>
                """

            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #4CAF50; color: white; }}
                    .summary {{ background-color: #f2f2f2; padding: 15px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h2>Monthly Activity Report - Dr. {doctor.name}</h2>
                <div class="summary">
                    <p><strong>Period:</strong> {last_month_start.strftime('%B %d, %Y')} to {last_month_end.strftime('%B %d, %Y')}</p>
                    <p><strong>Department:</strong> {doctor.department.name if doctor.department else 'N/A'}</p>
                    <p><strong>Total Appointments:</strong> {total_consultations}</p>
                    <p><strong>Completed:</strong> {completed}</p>
                    <p><strong>Completion Rate:</strong> {(completed/total_consultations*100) if total_consultations > 0 else 0:.1f}%</p>
                </div>
                
                <h3>Appointment Details</h3>
                <table>
                    <tr>
                        <th>Patient</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Diagnosis</th>
                        <th>Treatment</th>
                    </tr>
                    {rows}
                </table>
            </body>
            </html>
            """

            # Send to doctor's email
            recipient = doctor.email if doctor.email else app.config.get('MAIL_USERNAME')
            
            try:
                msg = Message(
                    f"Monthly Activity Report - {last_month_start.strftime('%B %Y')}", 
                    recipients=[recipient]
                )
                msg.html = html
                mail.send(msg)
                reports_sent += 1
            except Exception as e:
                print(f"Failed to send report to doctor {doctor.id}: {e}")

        return f"Monthly reports sent to {reports_sent} doctors"

@celery.task(name='tasks.export_patient_treatments', bind=True)
def export_patient_treatments(self, patient_id):
    from app import app, mail
    from backend.models.database import Patient, Appointment
    from flask_mail import Message
    
    with app.app_context():
        patient = Patient.query.get(patient_id)
        if not patient:
            return "patient not found"

        # Gather appointment data
        appts = Appointment.query.filter_by(
            patient_id=patient_id
        ).order_by(Appointment.date.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'user_id', 'username', 'patient_name', 'consulting_doctor', 
            'appointment_date', 'appointment_time', 'status', 
            'diagnosis', 'treatment', 'next_visit'
        ])
        
        for a in appts:
            doctor_name = a.doctor.name if a.doctor else 'N/A'
            diagnosis = a.treatment.diagnosis if a.treatment else 'N/A'
            prescription = a.treatment.prescription if a.treatment else 'N/A'
            next_visit = (
                a.treatment.follow_up_date.isoformat() 
                if (a.treatment and a.treatment.follow_up_date) 
                else 'N/A'
            )
            
            writer.writerow([
                patient.id,
                patient.username,
                patient.full_name,
                doctor_name,
                a.date.isoformat(),
                a.time.strftime('%H:%M'),
                a.status,
                diagnosis,
                prescription,
                next_visit
            ])

        csv_data = output.getvalue()
        output.close()

        # Email CSV as attachment
        if patient.email:
            try:
                msg = Message(
                    "Your Treatment History Export", 
                    recipients=[patient.email]
                )
                msg.body = (
                    f"Dear {patient.full_name},\n\n"
                    "Please find attached your complete treatment history.\n\n"
                    "Regards,\nHospital Management System"
                )
                msg.attach(
                    f"treatment_history_{patient.id}.csv", 
                    "text/csv", 
                    csv_data
                )
                mail.send(msg)
                return f"Export completed and emailed to {patient.email}"
            except Exception as e:
                return f"Export created but email failed: {e}"
        else:
            return "Export created but patient has no email"

celery.conf.beat_schedule = {
    'daily-reminder-morning': {
        'task': 'tasks.daily_reminder',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM
    },
    'monthly-doctor-report': {
        'task': 'tasks.monthly_doctor_report',
        'schedule': crontab(minute=0, hour=9, day_of_month='1'),  # 1st day at 9:00 AM
    },
}

celery.conf.timezone = 'Asia/Kolkata'
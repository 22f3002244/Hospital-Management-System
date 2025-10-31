from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
from celery.result import AsyncResult
from backend.models.database import db, Patient, Doctor, Appointment, Department

routes = Blueprint('routes', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        if not session.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'doctor_id' not in session:
            return jsonify({'error': 'Doctor authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    if Patient.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    patient = Patient(
        username=data['username'],
        full_name=data.get('full_name'),
        email=data.get('email'),
        phone=data.get('phone'),
        age=data.get('age'),
        gender=data.get('gender'),
        address=data.get('address'),
        created_at=datetime.utcnow()
    )
    patient.set_password(data['password'])
    
    db.session.add(patient)
    db.session.commit()
    
    return jsonify({
        'message': 'Patient registered successfully!',
        'patient_id': patient.id
    }), 201

@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = Patient.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session.clear()
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({
            'message': 'Login successful',
            'role': 'admin' if user.is_admin else 'patient',
            'user_id': user.id,
            'name': user.full_name
        })

    doctor = Doctor.query.filter_by(username=username).first()
    if doctor and doctor.check_password(password):
        session.clear()
        session['doctor_id'] = doctor.id
        return jsonify({
            'message': 'Login successful',
            'role': 'doctor',
            'doctor_id': doctor.id,
            'name': doctor.name
        })

    return jsonify({'error': 'Invalid username or password'}), 401

@routes.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@routes.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    stats = {
        'total_patients': Patient.query.filter_by(is_admin=False).count(),
        'total_doctors': Doctor.query.count(),
        'total_appointments': Appointment.query.count(),
        'pending_appointments': Appointment.query.filter_by(status='booked').count(),
    }

    recent_patients = [
        {
            'id': p.id,
            'name': p.full_name,
            'email': p.email,
            'created_at': p.created_at.isoformat() if p.created_at else None
        }
        for p in Patient.query.filter_by(is_admin=False).order_by(Patient.created_at.desc()).limit(5)
    ]

    recent_appointments = [
        {
            'id': a.id,
            'patient': a.patient.full_name,
            'doctor': a.doctor.name,
            'date': a.date.strftime('%Y-%m-%d'),
            'time': a.time.strftime('%H:%M'),
            'status': a.status
        }
        for a in Appointment.query.order_by(Appointment.date.desc()).limit(10)
    ]

    return jsonify({
        'stats': stats,
        'recent_patients': recent_patients,
        'recent_appointments': recent_appointments
    })

@routes.route('/doctor/<int:doctor_id>/dashboard', methods=['GET'])
@doctor_required
def doctor_dashboard(doctor_id):
    if session.get('doctor_id') != doctor_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    doctor = Doctor.query.get_or_404(doctor_id)

    appointments = [
        {
            'id': a.id,
            'patient': a.patient.full_name,
            'patient_id': a.patient_id,
            'date': a.date.strftime('%Y-%m-%d'),
            'time': a.time.strftime('%H:%M'),
            'status': a.status,
            'reason': a.reason
        }
        for a in doctor.appointments
    ]

    return jsonify({
        'doctor': {
            'id': doctor.id,
            'name': doctor.name,
            'specialization': doctor.specialization,
            'department': doctor.department.name if doctor.department else None,
            'email': doctor.email
        },
        'appointments': appointments
    })

@routes.route('/patient/<int:patient_id>/dashboard', methods=['GET'])
@login_required
def patient_dashboard(patient_id):
    if session.get('user_id') != patient_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get_or_404(patient_id)

    appointments = [
        {
            'id': a.id,
            'doctor': a.doctor.name,
            'doctor_id': a.doctor_id,
            'department': a.doctor.department.name if a.doctor.department else None,
            'date': a.date.strftime('%Y-%m-%d'),
            'time': a.time.strftime('%H:%M'),
            'status': a.status,
            'reason': a.reason
        }
        for a in patient.appointments
    ]

    return jsonify({
        'patient': {
            'id': patient.id,
            'name': patient.full_name,
            'email': patient.email,
            'phone': patient.phone,
            'age': patient.age
        },
        'appointments': appointments
    })

@routes.route('/departments', methods=['GET'])
def get_departments():
    from app import cache
    
    @cache.cached(timeout=300, key_prefix='all_departments')
    def get_all_departments():
        departments = Department.query.all()
        return [
            {
                'id': d.id,
                'name': d.name,
                'description': d.description
            }
            for d in departments
        ]
    
    return jsonify(get_all_departments())

@routes.route('/export-patient/<int:patient_id>', methods=['POST'])
@login_required
def start_export(patient_id):
    if session.get('user_id') != patient_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get_or_404(patient_id)
    
    from app import celery
    task = celery.send_task('tasks.export_patient_treatments', args=[patient_id])
    
    return jsonify({
        'message': 'Export started',
        'task_id': task.id,
        'patient_name': patient.full_name
    }), 202

@routes.route('/task-status/<task_id>', methods=['GET'])
@login_required
def task_status(task_id):
    from app import celery
    
    result = AsyncResult(task_id, app=celery)
    
    response = {
        'task_id': task_id,
        'state': result.state,
        'status': result.status
    }
    
    if result.state == 'SUCCESS':
        response['result'] = str(result.result)
    elif result.state == 'FAILURE':
        response['error'] = str(result.result)
    elif result.state == 'PENDING':
        response['message'] = 'Task is pending'
    else:
        response['message'] = f'Task is {result.state}'
    
    return jsonify(response)

@routes.route('/appointment/<int:appointment_id>/notify-confirmed', methods=['POST'])
@login_required
def notify_appointment_confirmed(appointment_id):
    from app import celery
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if (session.get('user_id') != appointment.patient_id and 
        not session.get('is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    task = celery.send_task('tasks.send_appointment_confirmed', args=[appointment_id])
    
    return jsonify({
        'message': 'Confirmation notification sent',
        'task_id': task.id
    })

@routes.route('/appointment/<int:appointment_id>/notify-cancelled', methods=['POST'])
@login_required
def notify_appointment_cancelled(appointment_id):
    from app import celery
    
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json() or {}
    reason = data.get('reason')
    
    if (session.get('user_id') != appointment.patient_id and 
        not session.get('is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    task = celery.send_task('tasks.send_appointment_cancelled', args=[appointment_id, reason])
    
    return jsonify({
        'message': 'Cancellation notification sent',
        'task_id': task.id
    })
from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime, date
from celery.result import AsyncResult
from sqlalchemy.exc import IntegrityError
from models.database import db, Patient, Doctor, Appointment, Department, Treatment, DoctorAvailability

routes = Blueprint('routes', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not ('user_id' in session or 'doctor_id' in session or session.get('is_admin')):
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
        {'id': p.id, 'name': p.full_name, 'email': p.email, 'phone': p.phone, 'created_at': p.created_at.isoformat() if p.created_at else None}
        for p in Patient.query.filter_by(is_admin=False).order_by(Patient.created_at.desc()).limit(5)
    ]
    recent_doctors = [
        {'id': d.id, 'name': d.name, 'department': d.department.name if d.department else None, 'qualification': d.qualification, 'experience_years': d.experience_years,'email': d.email, 'phone': d.phone}
        for d in Doctor.query.order_by(Doctor.created_at.desc()).limit(5)
    ]
    recent_appointments = [
        {'id': a.id, 'patient_id': a.patient.id, 'patient': a.patient.full_name, 'doctor': a.doctor.name,
        'department': a.doctor.department.name if a.doctor.department else None,'date': a.date.strftime('%Y-%m-%d'),
        'time': a.time.strftime('%H:%M'),'status': a.status
        }
        for a in Appointment.query.order_by(Appointment.date.desc()).limit(10)
    ]
    return jsonify({
        'stats': stats,
        'recent_doctors': recent_doctors,
        'recent_patients': recent_patients,
        'recent_appointments': recent_appointments
    })

@routes.route('/admin/doctors', methods=['GET'])
@admin_required
def get_all_doctors():
    doctors = Doctor.query.all()
    return jsonify([
        {
            'id': d.id,
            'name': d.name,
            'department': d.department.name if d.department else None,
            'qualification': d.qualification,
            'experience_years': d.experience_years,
            'email': d.email
        }
        for d in doctors
    ])

@routes.route('/admin/doctor', methods=['POST'])
@admin_required
def add_doctor():
    data = request.get_json()
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    if not data.get('name'):
        return jsonify({'error': 'Doctor name is required'}), 400
    
    if not data.get('department_id'):
        return jsonify({'error': 'Department is required'}), 400
    
    if Doctor.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    doctor = Doctor(
        name=data['name'],
        username=data['username'],
        email=data.get('email'),
        phone=data.get('phone'),
        qualification=data.get('qualification'),
        experience_years=data.get('experience_years'),
        department_id=data['department_id'],
        created_at=datetime.utcnow()
    )
    doctor.set_password(data['password'])
    db.session.add(doctor)
    db.session.commit()
    return jsonify({
        'message': 'Doctor added successfully!',
        'doctor_id': doctor.id
    }), 201

@routes.route('/admin/doctor/<int:doctor_id>', methods=['PUT'])
@admin_required
def update_doctor(doctor_id):
    data = request.get_json()
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    if data.get('department_id'):
        dept = Department.query.get(data['department_id'])
        if not dept:
            return jsonify({'error': 'Invalid department ID'}), 400
        doctor.department_id = data['department_id']

    doctor.name = data.get('name', doctor.name)
    doctor.email = data.get('email', doctor.email)
    doctor.qualification = data.get('qualification', doctor.qualification)
    doctor.experience_years = data.get('experience_years', doctor.experience_years)
    try:
        db.session.commit()
        return jsonify({'message': 'Doctor profile updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        print("Error updating doctor:", e)
        return jsonify({'error': 'Failed to update doctor profile'}), 500

@routes.route('/doctor/<int:doctor_id>/dashboard', methods=['GET'])
@doctor_required
def doctor_dashboard(doctor_id):
    if session.get('doctor_id') != doctor_id:
        return jsonify({'error': 'Unauthorized'}), 403
    doctor = Doctor.query.get_or_404(doctor_id)
    appointments = [
        {'id': a.id, 'patient': a.patient.full_name,'patient_id': a.patient_id,'date': a.date.strftime('%Y-%m-%d'),'time': a.time.strftime('%H:%M'),'status': a.status,'reason': a.reason}
        for a in sorted(doctor.appointments, key=lambda x: x.date, reverse=True)
    ]
    return jsonify({
        'doctor': {'id': doctor.id,'name': doctor.name,'department': doctor.department.name if doctor.department else None, 'email': doctor.email},
        'appointments': appointments
    })

@routes.route('/appointment/<int:appointment_id>/treatment', methods=['POST'])
@doctor_required
def add_treatment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if session.get('doctor_id') != appointment.doctor_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    treatment = appointment.treatment
    if not treatment:
        treatment = Treatment(appointment_id=appointment_id)
    treatment.diagnosis = data.get('diagnosis')
    treatment.prescription = data.get('prescription')
    treatment.notes = data.get('notes')
    if data.get('follow_up_date'):
        treatment.follow_up_date = datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date()
    
    appointment.status = 'completed'
    db.session.add(treatment)
    db.session.commit()
    return jsonify({
        'message': 'Treatment added successfully',
        'treatment_id': treatment.id
    })

@routes.route('/patient/<int:patient_id>/dashboard', methods=['GET'])
@login_required
def patient_dashboard(patient_id):
    if session.get('user_id') != patient_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    patient = Patient.query.get_or_404(patient_id)
    appointments = [
        {'id': a.id,'doctor': a.doctor.name,'doctor_id': a.doctor_id,
        'department': a.doctor.department.name if a.doctor.department else None,
        'date': a.date.strftime('%Y-%m-%d'),'time': a.time.strftime('%H:%M'),'status': a.status,'reason': a.reason
        }
        for a in sorted(patient.appointments, key=lambda a: a.date, reverse=True)
    ]
    return jsonify({
        'patient': {'id': patient.id, 'name': patient.full_name,'email': patient.email,'phone': patient.phone,'age': patient.age,'gender': patient.gender},
        'appointments': appointments
    })

@routes.route('/patient/<int:patient_id>', methods=['PUT'])
@login_required
def update_patient(patient_id):
    if session.get('user_id') != patient_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    
    patient.full_name = data.get('full_name', patient.full_name)
    patient.email = data.get('email', patient.email)
    patient.phone = data.get('phone', patient.phone)
    patient.age = data.get('age', patient.age)
    patient.gender = data.get('gender', patient.gender)
    patient.address = data.get('address', patient.address)
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})

@routes.route('/patient/<int:patient_id>/history', methods=['GET'])
@login_required
def patient_history(patient_id):
    user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    doctor_id = session.get('doctor_id')
    if not (is_admin or doctor_id or user_id == patient_id):
        return jsonify({'error': 'Unauthorized access'}), 403

    patient = Patient.query.get_or_404(patient_id)
    appointments = (Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.date.desc()).all())
    history = []
    for appointment in appointments:
        treatment = appointment.treatment
        history.append({
            'appointment_id': appointment.id,
            'doctor': appointment.doctor.name if appointment.doctor else None,
            'department': appointment.doctor.department.name if appointment.doctor and appointment.doctor.department else None,
            'date': appointment.date.strftime('%Y-%m-%d') if appointment.date else None,
            'time': appointment.time.strftime('%H:%M') if appointment.time else None,
            'status': appointment.status,
            'reason': appointment.reason,
            'diagnosis': treatment.diagnosis if treatment else None,
            'prescription': treatment.prescription if treatment else None,
            'follow_up_date': (
                treatment.follow_up_date.strftime('%Y-%m-%d')
                if treatment and treatment.follow_up_date else None
            )
        })
    return jsonify({
        'patient': {'id': patient.id,'name': patient.full_name,'email': patient.email,'phone': patient.phone},
        'history': history
    }), 200

@routes.route('/appointment', methods=['POST'])
@login_required
def book_appointment():
    data = request.get_json()
    patient_id = session.get('user_id')
    if not patient_id:
        return jsonify({'error': 'Patient authentication required'}), 401

    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        appointment_time = datetime.strptime(data['time'], '%H:%M').time()        
        today = date.today()
        now = datetime.now().time()
        if appointment_date < today:
            return jsonify({'error': 'Cannot book appointments in the past'}), 400
        if appointment_date == today and appointment_time <= now:
            return jsonify({'error': 'Cannot book appointments for past times'}), 400
        availability = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == data['doctor_id'],
            DoctorAvailability.date == appointment_date,
            DoctorAvailability.is_enabled == True,
            DoctorAvailability.start_time <= appointment_time,
            DoctorAvailability.end_time > appointment_time
        ).first()
    
        if not availability:
            return jsonify({'error': 'Selected time slot is not available'}), 400
        existing = Appointment.query.filter_by(doctor_id=data['doctor_id'],date=appointment_date,time=appointment_time).filter(Appointment.status.in_(['booked', 'confirmed'])).first()
        if existing:
            return jsonify({'error': 'This time slot is already booked'}), 409
        
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=data['doctor_id'],
            date=appointment_date,
            time=appointment_time,
            reason=data.get('reason'),
            status='booked',
            created_at=datetime.utcnow()
        )
        db.session.add(appointment)
        db.session.commit()

        from app import celery
        celery.send_task('tasks.send_appointment_confirmed', args=[appointment.id])
        return jsonify({
            'message': 'Appointment booked successfully',
            'appointment_id': appointment.id
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'This time slot was just booked by another patient. Please select another time.'}), 409
    except ValueError as e:
        return jsonify({'error': f'Invalid date or time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to book appointment. Please try again.'}), 500

@routes.route('/appointment/<int:appointment_id>', methods=['DELETE'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if (session.get('user_id') != appointment.patient_id and 
        session.get('doctor_id') != appointment.doctor_id and
        not session.get('is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json(silent=True) or {}
    reason = data.get('reason')
    appointment.status = 'cancelled'
    db.session.commit()

    from app import celery
    celery.send_task('tasks.send_appointment_cancelled', args=[appointment_id, reason])
    return jsonify({'message': 'Appointment cancelled successfully'})

@routes.route('/appointment/<int:appointment_id>/details', methods=['GET'])
@login_required
def get_appointment_details(appointment_id):
    user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    doctor_id = session.get('doctor_id')
    appointment = Appointment.query.get_or_404(appointment_id)
    if not (is_admin or doctor_id or appointment.patient_id == user_id):
        return jsonify({'error': 'Unauthorized access'}), 403

    treatment = appointment.treatment
    return jsonify({
        'appointment_id': appointment.id,
        'date': appointment.date.strftime('%Y-%m-%d'),
        'time': appointment.time.strftime('%H:%M'),
        'status': appointment.status,
        'reason': appointment.reason,
        'doctor': {
            'name': appointment.doctor.name,
            'department': appointment.doctor.department.name if appointment.doctor.department else None,
            'email': appointment.doctor.email
        },
        'patient': {'name': appointment.patient.full_name,'email': appointment.patient.email,'phone': appointment.patient.phone},
        'treatment': {'diagnosis': treatment.diagnosis if treatment else None,
            'prescription': treatment.prescription if treatment else None,
            'notes': treatment.notes if treatment else None,
            'follow_up_date': treatment.follow_up_date.strftime('%Y-%m-%d') if treatment and treatment.follow_up_date else None
        }
    }), 200

@routes.route('/departments', methods=['GET'])
def get_departments():
    from app import cache
    @cache.cached(timeout=300, key_prefix='all_departments')
    def get_all_departments():
        departments = Department.query.all()
        return [
            {'id': d.id,'name': d.name,'description': d.description}
            for d in departments
        ]
    return jsonify(get_all_departments())

@routes.route('/departments/<int:department_id>/doctors', methods=['GET'])
def get_department_doctors(department_id):
    doctors = Doctor.query.filter_by(department_id=department_id).all()
    return jsonify([
        {'id': d.id,'name': d.name,'qualification': d.qualification,'experience_years': d.experience_years,'email': d.email,'phone': d.phone}
        for d in doctors
    ])

@routes.route('/export-patient/<int:patient_id>', methods=['POST'])
@login_required
def start_export(patient_id):
    if session.get('user_id') != patient_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    patient = Patient.query.get_or_404(patient_id)
    
    from app import celery
    task = celery.send_task('tasks.export_patient_treatments', args=[patient_id])
    return jsonify({'message': 'Export started','task_id': task.id,'patient_name': patient.full_name}), 202

@routes.route('/task-status/<task_id>', methods=['GET'])
@login_required
def task_status(task_id):
    from app import celery
    result = AsyncResult(task_id, app=celery)
    response = {'task_id': task_id,'state': result.state,'status': result.status}
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

    if (session.get('user_id') != appointment.patient_id and not session.get('is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    task = celery.send_task('tasks.send_appointment_confirmed', args=[appointment_id])
    return jsonify({'message': 'Confirmation notification sent','task_id': task.id})

@routes.route('/appointment/<int:appointment_id>/notify-cancelled', methods=['POST'])
@login_required
def notify_appointment_cancelled(appointment_id):
    from app import celery
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json() or {}
    reason = data.get('reason')
    if (session.get('user_id') != appointment.patient_id and not session.get('is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    task = celery.send_task('tasks.send_appointment_cancelled', args=[appointment_id, reason])
    return jsonify({'message': 'Cancellation notification sent','task_id': task.id})

@routes.route('/admin/doctor/<int:doctor_id>', methods=['DELETE'])
@admin_required
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    return jsonify({'message': 'Doctor removed successfully'})

@routes.route('/admin/patient/<int:patient_id>', methods=['DELETE'])
@admin_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    return jsonify({'message': 'Patient removed successfully'})

@routes.route('/doctors/<int:doctor_id>/availability', methods=['POST'])
@doctor_required
def save_doctor_availability(doctor_id):
    if session.get('doctor_id') != doctor_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        doctor = Doctor.query.get_or_404(doctor_id)
        today = date.today()
        for day in data:
            day_date = datetime.strptime(day['date'], '%Y-%m-%d').date()
            if day_date < today:
                return jsonify({'error': f'Cannot set availability for past date: {day["date"]}'}), 400
            
            DoctorAvailability.query.filter(DoctorAvailability.doctor_id == doctor_id,DoctorAvailability.date == day_date).delete(synchronize_session=False)
            if day['enabled']:
                for slot in day['slots']:
                    if not slot['start'] or not slot['end']:
                        continue
                    start_time = datetime.strptime(slot['start'], '%H:%M').time()
                    end_time = datetime.strptime(slot['end'], '%H:%M').time()
                    if start_time >= end_time:
                        return jsonify({'error': f'Invalid time range on {day["date"]}: start time must be before end time'}), 400
                    availability = DoctorAvailability(doctor_id=doctor_id, date=day_date, start_time=start_time, end_time=end_time, is_enabled=True)
                    db.session.add(availability)
                    db.session.commit()
        return jsonify({'message': 'Availability saved successfully'}), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid date or time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@routes.route('/doctors/<int:doctor_id>/availability', methods=['GET'])
def get_doctor_availability(doctor_id):
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        query = DoctorAvailability.query.filter_by(doctor_id=doctor_id, is_enabled=True)
        if start_date:
            query = query.filter(DoctorAvailability.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(DoctorAvailability.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        slots = query.order_by(DoctorAvailability.date, DoctorAvailability.start_time).all()
        availability_by_date = {}
        for slot in slots:
            date_str = slot.date.strftime('%Y-%m-%d')
            if date_str not in availability_by_date:
                availability_by_date[date_str] = {'date': date_str,'enabled': True,'slots': []}
            availability_by_date[date_str]['slots'].append({'start': slot.start_time.strftime('%H:%M'),'end': slot.end_time.strftime('%H:%M')})
        return jsonify(list(availability_by_date.values())), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@routes.route('/doctors/<int:doctor_id>/available-slots', methods=['GET'])
def get_available_slots(doctor_id):
    try:
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({'error': 'Date parameter is required'}), 400
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = date.today()
        if query_date < today:
            return jsonify({'date': date_str,'slots': []}), 200
        slots = DoctorAvailability.query.filter_by(doctor_id=doctor_id, date=query_date, is_enabled=True).order_by(DoctorAvailability.start_time).all()
        booked_appointments = Appointment.query.filter_by(doctor_id=doctor_id,date=query_date).filter(Appointment.status.in_(['booked', 'confirmed'])).all()
        booked_times = [apt.time.strftime('%H:%M') for apt in booked_appointments]
        
        current_time = None
        if query_date == today:
            current_time = datetime.now().time()
        available = []
        for slot in slots:
            if current_time and slot.end_time <= current_time:
                continue
            available.append({'start': slot.start_time.strftime('%H:%M'),'end': slot.end_time.strftime('%H:%M'),'booked_times': booked_times,'current_time': current_time.strftime('%H:%M') if current_time else None})
        return jsonify({'date': date_str,'slots': available}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@routes.route('/appointment/<int:appointment_id>/send-record', methods=['POST'])
@login_required
def send_appointment_record(appointment_id):
    from app import celery
    appointment = Appointment.query.get_or_404(appointment_id)
    if (session.get('user_id') != appointment.patient_id and session.get('doctor_id') != appointment.doctor_id and not session.get('is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    if not appointment.patient.email:
        return jsonify({'error': 'Patient does not have an email address'}), 400

    task = celery.send_task('tasks.send_appointment_record_pdf', args=[appointment_id])
    return jsonify({'message': 'Medical record is being prepared and will be sent to your email shortly.','task_id': task.id}), 202

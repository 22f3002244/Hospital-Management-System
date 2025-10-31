from flask import Flask
from flask_mail import Mail
from flask_caching import Cache
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '').replace(" ", "")
app.config['MAIL_DEFAULT_SENDER'] = ('Hospital', app.config['MAIL_USERNAME'])

app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/1')
app.config['CACHE_DEFAULT_TIMEOUT'] = 300

mail = Mail(app)
cache = Cache(app)

from backend.models.database import db, Patient, Department
db.init_app(app)

from backend.tasks.celery_tasks import make_celery
celery = make_celery(app)

from backend.routes.routes import routes
app.register_blueprint(routes)

with app.app_context():
    db.create_all()

    admin = Patient.query.filter_by(username='admin').first()
    if not admin:
        admin = Patient(
            username='admin',
            is_admin=True,
            full_name='System Administrator',
            email=os.getenv('ADMIN_EMAIL', 'admin@hospital.com')
        )
        admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin'))
        db.session.add(admin)
        db.session.commit()
    
    if Department.query.count() == 0:
        departments = [
            Department(name='Cardiology', description='Heart and cardiovascular system care'),
            Department(name='Neurology', description='Brain and nervous system treatment'),
            Department(name='Orthopedics', description='Bone, joint, and muscle care'),
            Department(name='Pediatrics', description='Medical care for children'),
            Department(name='Dermatology', description='Skin, hair, and nail treatment'),
            Department(name='General Medicine', description='Primary and general healthcare'),
        ]
        db.session.add_all(departments)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

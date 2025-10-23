from flask import Flask
from models.database import db, Patient

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretkey'

db.init_app(app)

with app.app_context():
    db.create_all()

    admin = Patient.query.filter_by(username='admin').first()
    if not admin:
        admin = Patient(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)

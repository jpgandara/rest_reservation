from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'table_number': self.table_number,
            'capacity': self.capacity,
            'is_occupied': self.is_occupied
        }

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    party_size = db.Column(db.Integer, nullable=False)
    reservation_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, seated, cancelled
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True)
    
    table = db.relationship('Table', backref=db.backref('reservations', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'phone_number': self.phone_number,
            'email': self.email,
            'party_size': self.party_size,
            'reservation_time': self.reservation_time.isoformat(),
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'table_id': self.table_id
        }

class Waitlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    party_size = db.Column(db.Integer, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='waiting')  # waiting, notified, seated, left
    estimated_wait_time = db.Column(db.Integer, nullable=True)  # in minutes
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'phone_number': self.phone_number,
            'email': self.email,
            'party_size': self.party_size,
            'joined_at': self.joined_at.isoformat(),
            'status': self.status,
            'estimated_wait_time': self.estimated_wait_time
        }
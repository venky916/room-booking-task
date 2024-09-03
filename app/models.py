from app import db
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('USER', 'ADMIN'), default='USER')  # Updated with role field

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=2)  # Fixed capacity
    date = db.Column(db.Date)  # Add date field
    start_time = db.Column(db.Time)  # Change to db.Time
    end_time = db.Column(db.Time)    # Change to db.Time    
    description = db.Column(db.Text)  # Add description field

    def is_available(self, date, start_time, end_time):
        # Check for conflicting bookings by other users
        conflicting_bookings = Booking.query.filter_by(room_id=self.id).filter(
            (Booking.date == date) &
            ((Booking.start_time < end_time) & (Booking.end_time > start_time))
        ).all()

        # Check if the requested time slot falls within the admin-defined time slot
        if start_time < self.start_time or end_time > self.end_time:
            return False
        if start_time > end_time:
            return False
        # Check for conflicting bookings by other users within the admin-defined time slot
        conflicting_user_bookings = Booking.query.filter_by(room_id=self.id).filter(
            (Booking.date == date) &
            (Booking.user_id.isnot(None)) &
            ((Booking.start_time < end_time) & (Booking.end_time > start_time))
        ).all()

        # Check if the requested time slot overlaps with any conflicting user bookings
        for booking in conflicting_user_bookings:
            conflicting_start = booking.start_time
            conflicting_end = booking.end_time
            if (start_time < conflicting_end and end_time > conflicting_start) or \
               (start_time >= conflicting_start and end_time <= conflicting_end) or \
               (start_time <= conflicting_end and end_time > conflicting_end) or \
               (start_time < conflicting_start and end_time >= conflicting_start):
                return False

        return not conflicting_bookings

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Added date field
    start_time = db.Column(db.Time)  # Change to db.Time
    end_time = db.Column(db.Time)    # Change to db.Time
    # Define relationships
    user = relationship("User", backref="bookings")
    room = relationship("Room", backref="bookings")

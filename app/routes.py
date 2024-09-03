from flask import render_template, redirect, url_for, flash, session
from app import app, db
from app.forms import RegistrationForm, LoginForm,BookingForm,RoomForm
from app.models import Room, Booking, User
from datetime import datetime


@app.route('/index')
def index():
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

@app.route('/',methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
        else:
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)  # Hash the password
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

# Update the routes for admin-only access
@app.route('/admin/add_room', methods=['GET', 'POST'])
def admin_add_room():
    form = RoomForm()
    if form.validate_on_submit():
        name = form.name.data
        date = form.date.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        description = form.description.data
        room = Room(name=name, date=date, start_time=start_time, end_time=end_time, description=description)
        db.session.add(room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('admin_add_room.html', form=form)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session['role'] != 'ADMIN':
        flash('Please log in as admin', 'error')
        return redirect(url_for('login'))

    # 1. View all bookings done by users
    bookings = Booking.query.all()

    # 2. View total rooms, bookings, available rooms, and available bookings
    total_rooms = Room.query.count()
    total_bookings = Booking.query.count()
    available_rooms = total_rooms - total_bookings

    # Calculate available bookings (considering each room has a capacity of 2)
    available_bookings = total_rooms * 2 - total_bookings

    # 3. Show list of users who have signed up
    users = User.query.filter_by(role='USER').all()

    return render_template('admin_dashboard.html', 
                           bookings=bookings, 
                           total_rooms=total_rooms, 
                           total_bookings=total_bookings, 
                           available_rooms=available_rooms, 
                           available_bookings=available_bookings,
                           users=users)


@app.route('/my_bookings')
def my_bookings():
    if 'username' not in session:
        flash('Please log in to view your bookings', 'error')
        return redirect(url_for('login'))
    bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/book_room/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    form = BookingForm()
    room = Room.query.get_or_404(room_id)
    date = room.date
    existing_bookings = Booking.query.filter_by(room_id=room_id).all()
    
    if room.capacity >= 1:
        if form.validate_on_submit():
            start_time = form.start_time.data
            end_time = form.end_time.data
            if room.is_available(date, start_time, end_time):
                booking = Booking(room_id=room_id, user_id=session['user_id'], date=date, start_time=start_time, end_time=end_time)
                db.session.add(booking)
                db.session.commit()
                # Reduce the room capacity after booking
                room.capacity -= 1
                db.session.commit()
                flash('Room booked successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Room is not available for the selected date and time slot or capacity exceeded', 'error')
    else:
        flash("No Slots available capacity exceeded")
    
    return render_template('book_room.html', form=form, room=room, existing_bookings=existing_bookings)

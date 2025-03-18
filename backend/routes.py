from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Table, Reservation, Waitlist
from table_allocation import find_available_table, allocate_table_for_reservation, seat_waitlist_party, calculate_wait_time

api = Blueprint('api', __name__)

# Table routes
@api.route('/tables', methods=['GET'])
def get_tables():
    tables = Table.query.all()
    return jsonify([table.to_dict() for table in tables])

@api.route('/tables', methods=['POST'])
def create_table():
    data = request.json
    new_table = Table(
        table_number=data['table_number'],
        capacity=data['capacity']
    )
    db.session.add(new_table)
    db.session.commit()
    return jsonify(new_table.to_dict()), 201

@api.route('/tables/<int:table_id>', methods=['PUT'])
def update_table(table_id):
    table = Table.query.get_or_404(table_id)
    data = request.json
    
    if 'capacity' in data:
        table.capacity = data['capacity']
    if 'is_occupied' in data:
        table.is_occupied = data['is_occupied']
    
    db.session.commit()
    return jsonify(table.to_dict())

# Reservation routes
@api.route('/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    return jsonify([reservation.to_dict() for reservation in reservations])

@api.route('/reservations', methods=['POST'])
def create_reservation():
    data = request.json
    
    # Parse reservation time
    reservation_time = datetime.fromisoformat(data['reservation_time'].replace('Z', '+00:00'))
    
    new_reservation = Reservation(
        customer_name=data['customer_name'],
        phone_number=data['phone_number'],
        email=data.get('email', ''),
        party_size=data['party_size'],
        reservation_time=reservation_time,
        status='pending'
    )
    
    db.session.add(new_reservation)
    db.session.commit()
    
    # Try to allocate a table immediately
    table = find_available_table(data['party_size'], reservation_time)
    if table:
        new_reservation.table_id = table.id
        new_reservation.status = 'confirmed'
        db.session.commit()
    
    return jsonify(new_reservation.to_dict()), 201

@api.route('/reservations/<int:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    data = request.json
    
    if 'status' in data:
        reservation.status = data['status']
        
        # If confirming a reservation, try to allocate a table
        if data['status'] == 'confirmed' and not reservation.table_id:
            success, message = allocate_table_for_reservation(reservation_id)
            if not success:
                return jsonify({'error': message}), 400
    
    if 'table_id' in data:
        reservation.table_id = data['table_id']
    
    db.session.commit()
    return jsonify(reservation.to_dict())

# Waitlist routes
@api.route('/waitlist', methods=['GET'])
def get_waitlist():
    waitlist = Waitlist.query.filter(Waitlist.status == 'waiting').order_by(Waitlist.joined_at).all()
    return jsonify([entry.to_dict() for entry in waitlist])

@api.route('/waitlist', methods=['POST'])
def add_to_waitlist():
    data = request.json
    
    new_entry = Waitlist(
        customer_name=data['customer_name'],
        phone_number=data['phone_number'],
        email=data.get('email', ''),
        party_size=data['party_size'],
        status='waiting'
    )
    
    # Calculate estimated wait time
    new_entry.estimated_wait_time = calculate_wait_time(data['party_size'])
    
    db.session.add(new_entry)
    db.session.commit()
    
    # Check if we can seat them immediately
    table = find_available_table(data['party_size'])
    if table:
        success, message = seat_waitlist_party(new_entry.id)
        if success:
            return jsonify({'message': message, 'waitlist': new_entry.to_dict()}), 201
    
    return jsonify(new_entry.to_dict()), 201

@api.route('/waitlist/<int:waitlist_id>', methods=['PUT'])
def update_waitlist(waitlist_id):
    waitlist_entry = Waitlist.query.get_or_404(waitlist_id)
    data = request.json
    
    if 'status' in data:
        waitlist_entry.status = data['status']
        
        # If trying to seat a party
        if data['status'] == 'seated':
            success, message = seat_waitlist_party(waitlist_id)
            if not success:
                return jsonify({'error': message}), 400
    
    db.session.commit()
    return jsonify(waitlist_entry.to_dict())

# Dashboard summary route
@api.route('/dashboard', methods=['GET'])
def dashboard_summary():
    current_time = datetime.utcnow()
    
    # Get counts of today's reservations
    today_reservations = Reservation.query.filter(
        Reservation.reservation_time >= current_time.replace(hour=0, minute=0, second=0),
        Reservation.reservation_time < current_time.replace(hour=23, minute=59, second=59)
    ).count()
    
    # Get counts of occupied and available tables
    total_tables = Table.query.count()
    occupied_tables = Table.query.filter_by(is_occupied=True).count()
    
    # Get waitlist count
    waitlist_count = Waitlist.query.filter_by(status='waiting').count()
    
    return jsonify({
        'today_reservations': today_reservations,
        'total_tables': total_tables,
        'occupied_tables': occupied_tables,
        'available_tables': total_tables - occupied_tables,
        'waitlist_count': waitlist_count
    })
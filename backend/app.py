from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from models import db, Table, Reservation, Waitlist
import os
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Seed some tables if none exist
        if Table.query.count() == 0:
            tables = [
                Table(table_number=1, capacity=2),
                Table(table_number=2, capacity=2),
                Table(table_number=3, capacity=4),
                Table(table_number=4, capacity=4),
                Table(table_number=5, capacity=6),
                Table(table_number=6, capacity=8)
            ]
            db.session.add_all(tables)
            db.session.commit()
            print("Tables seeded successfully!")
    
    @app.route('/')
    def index():
        return "Restaurant Reservation API is running!"
    
    # Table routes
    @app.route('/api/tables', methods=['GET'])
    def get_tables():
        tables = Table.query.all()
        return jsonify([table.to_dict() for table in tables])

    @app.route('/api/tables/<int:table_id>', methods=['PUT'])
    def update_table(table_id):
        from flask import request
        table = Table.query.get_or_404(table_id)
        data = request.json
        
        if 'capacity' in data:
            table.capacity = data['capacity']
        if 'is_occupied' in data:
            table.is_occupied = data['is_occupied']
        
        db.session.commit()
        return jsonify(table.to_dict())

    # Reservation routes
    @app.route('/api/reservations', methods=['GET'])
    def get_reservations():
        reservations = Reservation.query.all()
        return jsonify([reservation.to_dict() for reservation in reservations])

    @app.route('/api/reservations', methods=['POST'])
    def create_reservation():
        from flask import request
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
        def find_available_table(party_size, reservation_time=None):
            if reservation_time:
                tables = Table.query.filter(Table.capacity >= party_size).order_by(Table.capacity).all()
                available_tables = []
                
                for table in tables:
                    reservation_start = reservation_time - timedelta(hours=1.5)
                    reservation_end = reservation_time + timedelta(hours=1.5)
                    
                    conflicting_reservation = Reservation.query.filter(
                        Reservation.table_id == table.id,
                        Reservation.status.in_(['confirmed', 'pending']),
                        Reservation.reservation_time.between(reservation_start, reservation_end)
                    ).first()
                    
                    if not conflicting_reservation:
                        available_tables.append(table)
                
                if available_tables:
                    return available_tables[0]
                return None
            else:
                available_table = Table.query.filter(
                    Table.capacity >= party_size,
                    Table.is_occupied == False
                ).order_by(Table.capacity).first()
                
                return available_table
        
        table = find_available_table(data['party_size'], reservation_time)
        if table:
            new_reservation.table_id = table.id
            new_reservation.status = 'confirmed'
            db.session.commit()
        
        return jsonify(new_reservation.to_dict()), 201

    # Waitlist routes
    @app.route('/api/waitlist', methods=['GET'])
    def get_waitlist():
        waitlist = Waitlist.query.filter(Waitlist.status == 'waiting').order_by(Waitlist.joined_at).all()
        return jsonify([entry.to_dict() for entry in waitlist])

    @app.route('/api/waitlist', methods=['POST'])
    def add_to_waitlist():
        from flask import request
        data = request.json
        
        new_entry = Waitlist(
            customer_name=data['customer_name'],
            phone_number=data['phone_number'],
            email=data.get('email', ''),
            party_size=data['party_size'],
            status='waiting'
        )
        
        # Calculate estimated wait time
        def calculate_wait_time(party_size):
            waiting_ahead = Waitlist.query.filter(
                Waitlist.status == 'waiting',
                Waitlist.party_size <= party_size,
                Waitlist.joined_at < datetime.utcnow()
            ).count()
            
            suitable_tables = Table.query.filter(Table.capacity >= party_size).count()
            
            if suitable_tables > 0:
                estimated_wait = max(15, (waiting_ahead * 15) // suitable_tables)
            else:
                estimated_wait = waiting_ahead * 15
            
            return estimated_wait
        
        new_entry.estimated_wait_time = calculate_wait_time(data['party_size'])
        
        db.session.add(new_entry)
        db.session.commit()
        
        # Check if we can seat them immediately
        def find_available_table(party_size):
            available_table = Table.query.filter(
                Table.capacity >= party_size,
                Table.is_occupied == False
            ).order_by(Table.capacity).first()
            
            return available_table
            
        def seat_waitlist_party(waitlist_id):
            waitlist_entry = Waitlist.query.get(waitlist_id)
            if not waitlist_entry:
                return False, "Waitlist entry not found"
            
            if waitlist_entry.status != 'waiting':
                return False, f"Party is already {waitlist_entry.status}"
            
            # Find an available table
            table = find_available_table(waitlist_entry.party_size)
            
            if not table:
                return False, "No suitable table available at this time"
            
            # Mark the table as occupied
            table.is_occupied = True
            
            # Update waitlist status
            waitlist_entry.status = 'seated'
            
            db.session.commit()
            
            return True, f"Party seated at table {table.table_number}"
        
        table = find_available_table(data['party_size'])
        if table:
            success, message = seat_waitlist_party(new_entry.id)
            if success:
                return jsonify({'message': message, 'waitlist': new_entry.to_dict()}), 201
        
        return jsonify(new_entry.to_dict()), 201

    # Dashboard summary route
    @app.route('/api/dashboard', methods=['GET'])
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
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
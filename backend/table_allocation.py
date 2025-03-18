from models import Table, Reservation, Waitlist, db
from datetime import datetime, timedelta

def find_available_table(party_size, reservation_time=None):
    """
    Find an available table that can accommodate the party size
    If reservation_time is provided, check for availability at that time
    Otherwise, check for current availability
    """
    # If checking for a future reservation
    if reservation_time:
        # Get all tables
        tables = Table.query.filter(Table.capacity >= party_size).order_by(Table.capacity).all()
        
        # Check which tables are available at the requested time
        available_tables = []
        
        for table in tables:
            # Check if table has any reservations that would conflict
            # A reservation typically lasts 2 hours
            reservation_start = reservation_time - timedelta(hours=1.5)
            reservation_end = reservation_time + timedelta(hours=1.5)
            
            conflicting_reservation = Reservation.query.filter(
                Reservation.table_id == table.id,
                Reservation.status.in_(['confirmed', 'pending']),
                Reservation.reservation_time.between(reservation_start, reservation_end)
            ).first()
            
            if not conflicting_reservation:
                available_tables.append(table)
        
        # Return the smallest available table that fits the party
        if available_tables:
            return available_tables[0]
        return None
    
    # If checking for immediate seating
    else:
        # Find the smallest unoccupied table that can fit the party
        available_table = Table.query.filter(
            Table.capacity >= party_size,
            Table.is_occupied == False
        ).order_by(Table.capacity).first()
        
        return available_table

def allocate_table_for_reservation(reservation_id):
    """
    Allocate a table for a confirmed reservation
    """
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return False, "Reservation not found"
    
    if reservation.status != 'confirmed':
        return False, "Reservation is not confirmed"
    
    # Find an available table
    table = find_available_table(reservation.party_size, reservation.reservation_time)
    
    if not table:
        return False, "No suitable table available"
    
    # Assign the table to the reservation
    reservation.table_id = table.id
    db.session.commit()
    
    return True, f"Table {table.table_number} assigned to reservation"

def seat_waitlist_party(waitlist_id):
    """
    Find an available table for a party on the waitlist
    """
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

def calculate_wait_time(party_size):
    """
    Estimate the wait time for a party of a given size
    This is a simplified algorithm that could be improved
    """
    # Count how many parties are waiting for tables that could accommodate this party
    waiting_ahead = Waitlist.query.filter(
        Waitlist.status == 'waiting',
        Waitlist.party_size <= party_size,
        Waitlist.joined_at < datetime.utcnow()
    ).count()
    
    # Get count of suitable tables
    suitable_tables = Table.query.filter(Table.capacity >= party_size).count()
    
    # Simplified wait time calculation - 15 minutes per party waiting
    # divided by number of suitable tables (minimum 1)
    if suitable_tables > 0:
        estimated_wait = max(15, (waiting_ahead * 15) // suitable_tables)
    else:
        estimated_wait = waiting_ahead * 15
    
    return estimated_wait
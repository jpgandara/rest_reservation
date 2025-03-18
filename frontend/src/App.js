import React, { useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import axios from 'axios';
import { Container, Row, Col, Card, Button, Form, Table, Tabs, Tab, Badge, Alert } from 'react-bootstrap';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [tables, setTables] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [waitlist, setWaitlist] = useState([]);
  const [stats, setStats] = useState({});
  const [alert, setAlert] = useState({ show: false, message: '', variant: 'success' });
  
  // Form states
  const [reservationForm, setReservationForm] = useState({
    customer_name: '',
    phone_number: '',
    email: '',
    party_size: 2,
    reservation_time: ''
  });
  
  const [waitlistForm, setWaitlistForm] = useState({
    customer_name: '',
    phone_number: '',
    email: '',
    party_size: 2
  });

  // Fetch all data
  const fetchData = async () => {
    try {
      const tablesRes = await axios.get(`${API_BASE_URL}/tables`);
      const reservationsRes = await axios.get(`${API_BASE_URL}/reservations`);
      const waitlistRes = await axios.get(`${API_BASE_URL}/waitlist`);
      const dashboardRes = await axios.get(`${API_BASE_URL}/dashboard`);
      
      setTables(tablesRes.data);
      setReservations(reservationsRes.data);
      setWaitlist(waitlistRes.data);
      setStats(dashboardRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      showAlert("Failed to load data", "danger");
    }
  };

  // Show alert message
  const showAlert = (message, variant = 'success') => {
    setAlert({ show: true, message, variant });
    setTimeout(() => setAlert({ show: false, message: '', variant: 'success' }), 3000);
  };

  // Handle reservation form submission
  const handleReservationSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/reservations`, reservationForm);
      showAlert("Reservation created successfully!");
      setReservationForm({
        customer_name: '',
        phone_number: '',
        email: '',
        party_size: 2,
        reservation_time: ''
      });
      fetchData();
    } catch (error) {
      console.error("Error creating reservation:", error);
      showAlert("Failed to create reservation", "danger");
    }
  };

  // Handle waitlist form submission
  const handleWaitlistSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/waitlist`, waitlistForm);
      showAlert("Added to waitlist successfully!");
      setWaitlistForm({
        customer_name: '',
        phone_number: '',
        email: '',
        party_size: 2
      });
      fetchData();
    } catch (error) {
      console.error("Error adding to waitlist:", error);
      showAlert("Failed to add to waitlist", "danger");
    }
  };

  // Toggle table occupancy
  const toggleTableOccupancy = async (tableId, currentStatus) => {
    try {
      await axios.put(`${API_BASE_URL}/tables/${tableId}`, {
        is_occupied: !currentStatus
      });
      showAlert(`Table ${tableId} ${currentStatus ? 'freed' : 'occupied'} successfully!`);
      fetchData();
    } catch (error) {
      console.error("Error updating table:", error);
      showAlert("Failed to update table status", "danger");
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchData();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Container className="mt-4">
      <h1 className="text-center mb-4">The Krabby Patty</h1>
      
      {alert.show && (
        <Alert variant={alert.variant}>{alert.message}</Alert>
      )}
      
      <Tabs defaultActiveKey="dashboard" className="mb-4">
        <Tab eventKey="dashboard" title="Dashboard">
          <Row>
            <Col md={3}>
              <Card className="text-center mb-3">
                <Card.Body>
                  <Card.Title>Total Tables</Card.Title>
                  <h2>{stats.total_tables || 0}</h2>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center mb-3">
                <Card.Body>
                  <Card.Title>Available Tables</Card.Title>
                  <h2>{stats.available_tables || 0}</h2>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center mb-3">
                <Card.Body>
                  <Card.Title>Today's Reservations</Card.Title>
                  <h2>{stats.today_reservations || 0}</h2>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center mb-3">
                <Card.Body>
                  <Card.Title>Waitlist Count</Card.Title>
                  <h2>{stats.waitlist_count || 0}</h2>
                </Card.Body>
              </Card>
            </Col>
          </Row>
          
          <Row className="mt-4">
            <Col>
              <h3>Tables</h3>
              <div className="d-flex flex-wrap">
                {tables.map(table => (
                  <Card 
                    key={table.id} 
                    className={`m-2 ${table.is_occupied ? 'bg-danger text-white' : 'bg-success text-white'}`}
                    style={{ width: '120px', height: '100px' }}
                  >
                    <Card.Body className="d-flex flex-column align-items-center justify-content-center">
                      <Card.Title>Table {table.table_number}</Card.Title>
                      <Card.Text>Seats: {table.capacity}</Card.Text>
                      <Button 
                        size="sm" 
                        variant={table.is_occupied ? "outline-light" : "outline-light"}
                        onClick={() => toggleTableOccupancy(table.id, table.is_occupied)}
                      >
                        {table.is_occupied ? 'Free Up' : 'Occupy'}
                      </Button>
                    </Card.Body>
                  </Card>
                ))}
              </div>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="reservations" title="Reservations">
          <Row>
            <Col md={4}>
              <Card>
                <Card.Body>
                  <Card.Title>New Reservation</Card.Title>
                  <Form onSubmit={handleReservationSubmit}>
                    <Form.Group className="mb-3">
                      <Form.Label>Customer Name</Form.Label>
                      <Form.Control 
                        type="text" 
                        required 
                        value={reservationForm.customer_name}
                        onChange={(e) => setReservationForm({...reservationForm, customer_name: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Phone Number</Form.Label>
                      <Form.Control 
                        type="text" 
                        required 
                        value={reservationForm.phone_number}
                        onChange={(e) => setReservationForm({...reservationForm, phone_number: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Email</Form.Label>
                      <Form.Control 
                        type="email"
                        value={reservationForm.email}
                        onChange={(e) => setReservationForm({...reservationForm, email: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Party Size</Form.Label>
                      <Form.Control 
                        type="number" 
                        min="1" 
                        required 
                        value={reservationForm.party_size}
                        onChange={(e) => setReservationForm({...reservationForm, party_size: parseInt(e.target.value)})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Reservation Time</Form.Label>
                      <Form.Control 
                        type="datetime-local" 
                        required 
                        value={reservationForm.reservation_time}
                        onChange={(e) => setReservationForm({...reservationForm, reservation_time: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Button variant="primary" type="submit">Create Reservation</Button>
                  </Form>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={8}>
              <Card>
                <Card.Body>
                  <Card.Title>Reservations</Card.Title>
                  <Table striped bordered hover>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Party Size</th>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Table</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reservations.length > 0 ? (
                        reservations.map(res => (
                          <tr key={res.id}>
                            <td>{res.customer_name}</td>
                            <td>{res.party_size}</td>
                            <td>{new Date(res.reservation_time).toLocaleString()}</td>
                            <td>
                              <Badge bg={
                                res.status === 'confirmed' ? 'success' : 
                                res.status === 'seated' ? 'primary' : 
                                res.status === 'cancelled' ? 'danger' : 'warning'
                              }>
                                {res.status}
                              </Badge>
                            </td>
                            <td>{res.table_id || 'Not assigned'}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="text-center">No reservations found</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="waitlist" title="Waitlist">
          <Row>
            <Col md={4}>
              <Card>
                <Card.Body>
                  <Card.Title>Add to Waitlist</Card.Title>
                  <Form onSubmit={handleWaitlistSubmit}>
                    <Form.Group className="mb-3">
                      <Form.Label>Customer Name</Form.Label>
                      <Form.Control 
                        type="text" 
                        required 
                        value={waitlistForm.customer_name}
                        onChange={(e) => setWaitlistForm({...waitlistForm, customer_name: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Phone Number</Form.Label>
                      <Form.Control 
                        type="text" 
                        required 
                        value={waitlistForm.phone_number}
                        onChange={(e) => setWaitlistForm({...waitlistForm, phone_number: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Email</Form.Label>
                      <Form.Control 
                        type="email"
                        value={waitlistForm.email}
                        onChange={(e) => setWaitlistForm({...waitlistForm, email: e.target.value})}
                      />
                    </Form.Group>
                    
                    <Form.Group className="mb-3">
                      <Form.Label>Party Size</Form.Label>
                      <Form.Control 
                        type="number" 
                        min="1" 
                        required 
                        value={waitlistForm.party_size}
                        onChange={(e) => setWaitlistForm({...waitlistForm, party_size: parseInt(e.target.value)})}
                      />
                    </Form.Group>
                    
                    <Button variant="primary" type="submit">Add to Waitlist</Button>
                  </Form>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={8}>
              <Card>
                <Card.Body>
                  <Card.Title>Current Waitlist</Card.Title>
                  <Table striped bordered hover>
                    <thead>
                      <tr>
                        <th>Position</th>
                        <th>Name</th>
                        <th>Party Size</th>
                        <th>Wait Time</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {waitlist.length > 0 ? (
                        waitlist.map((entry, index) => (
                          <tr key={entry.id}>
                            <td>{index + 1}</td>
                            <td>{entry.customer_name}</td>
                            <td>{entry.party_size}</td>
                            <td>{entry.estimated_wait_time} min</td>
                            <td>
                              <Badge bg={
                                entry.status === 'seated' ? 'success' : 
                                entry.status === 'notified' ? 'info' : 
                                entry.status === 'left' ? 'danger' : 'warning'
                              }>
                                {entry.status}
                              </Badge>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="text-center">No parties waiting</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
      </Tabs>
    </Container>
  );
}

export default App;
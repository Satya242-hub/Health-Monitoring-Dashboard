# Health-Monitoring-Dashboard

A real-time patient health monitoring dashboard built using **React**, **FastAPI**, and **WebSockets**. The application simulates live patient vital signs and displays them through an interactive dashboard with real-time updates.

## Features

* Real-time patient monitoring
* Live heart rate, SpO₂, and temperature updates
* WebSocket communication between frontend and backend
* Interactive charts for vital signs
* Responsive dashboard interface
* Backend connection status indicator
* Simulated patient data for demonstration

## Tech Stack

### Frontend

* React
* Vite
* Recharts
* Lucide React

### Backend

* FastAPI
* Uvicorn
* WebSockets

## Project Structure

```text
Health Dashboard/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── vitals_logic.py
│   ├── simulator.py
│   ├── ws_manager.py
│   ├── requirements.txt
│   └── README.md
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── health-dashboard.jsx
```

## Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/providence-health-dashboard.git
cd providence-health-dashboard
```

### Backend Setup

Navigate to the backend folder:

```bash
cd backend
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the backend server:

```bash
uvicorn main:app --reload
```

The backend will be available at:

```
http://127.0.0.1:8000
```

### Frontend Setup

Navigate to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

The frontend will be available at:

```
http://localhost:5173
```

## Dashboard Features

* Live patient monitoring
* Heart rate tracking
* Blood oxygen (SpO₂) monitoring
* Body temperature monitoring
* Interactive real-time charts
* Backend connection status
* WebSocket-based live updates

## API Endpoints

### REST API

```
GET /patients
```

Returns the list of available patients.

### WebSocket

```
ws://127.0.0.1:8000/ws
```

Streams real-time patient vital signs.

## Future Enhancements

* User authentication
* Patient search and filtering
* Historical data storage
* Alert notification system
* Doctor and nurse login
* Database integration
* Dark mode
* Mobile-responsive interface

## Author

**Satya**


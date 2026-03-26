ATM Operations Dashboard
Overview

This project is an operations dashboard designed to monitor ATM systems across multiple data sources, including application logs, hardware sensors, streaming metrics, and infrastructure telemetry.

The dashboard is built to support different user personas (e.g. Admin, ATM Manager, Operations) and provides a structured view of system activity, errors, and operational status.

Features
Role-based access (Admin, Manager, Ops)
Persona-specific dashboards
Flask backend serving dashboard and API endpoints
Integration-ready for live data from SQLite (atm_logs.db)
Health and system status endpoints
Clean, structured UI for operational monitoring
Project Structure
src/
  dashboard/
    server.py        # Flask backend
    index.html       # Dashboard UI
    styles.css       # Styling
    app.js           # Frontend logic

data/
  clean/
    atm_logs.db      # Cleaned database (if available)
Running the Application
1. Start the Flask server
python src/dashboard/server.py
2. Open in browser
http://127.0.0.1:5000

This will take you to the login page.

Authentication Flow
Users can sign up and choose a role:
Admin
ATM Manager
Operations
Users can then sign in using their credentials
After login, users are redirected to their role-specific dashboard
Sessions are managed using Flask
Logout clears the session and returns to the login page
API Endpoints
Health Check
/health

Returns system status and database availability.

API Status
/api/status

Returns:

whether the database is present
available tables (if database exists)
Data Integration

The dashboard is designed to integrate with a cleaned SQLite database:

data/clean/atm_logs.db

If the database is not present:

the system will still run
endpoints will safely return empty/unavailable states
User Personas
Admin
Full system overview
Cross-source visibility
High-level monitoring
ATM Manager
Local ATM status
Immediate operational issues
Action-focused information
Operations (Ops)
Infrastructure health
Error spikes and system failures
Telemetry and backend monitoring
Notes
The authentication system is implemented using Flask sessions
Passwords are securely stored using hashing
The system is designed to be lightweight and extendable
Some features may depend on data availability from the pipeline

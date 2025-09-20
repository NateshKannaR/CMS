#!/usr/bin/env python3
"""
College Management System - Startup Script
Run this file to start the application
"""

from app import app, init_db

if __name__ == '__main__':
    # Initialize database on first run
    init_db()
    
    # Run the application
    print("Starting College Management System...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
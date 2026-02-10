import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'iot-energy-monitor-secret-key-2024'
    
    # Database Configuration
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'iot_energy_monitor'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Theme Configuration
    THEME_COLORS = {
        'primary': '#1a237e',      # Dark Blue
        'secondary': '#0d47a1',    # Medium Blue
        'accent': '#2962ff',       # Light Blue
        'dark': '#000000',         # Black
        'light': '#ffffff',        # White
        'gray': '#2d3748',         # Dark Gray
        'success': '#4caf50',      # Green
        'warning': '#ff9800',      # Orange
        'danger': '#f44336',       # Red
    }
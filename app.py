from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from config import Config
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config.from_object(Config)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    query = "SELECT * FROM `user` WHERE user_id = %s"
    user_data = db.execute_query(query, (user_id,), fetch_one=True)
    if user_data:
        return User(user_data['user_id'], user_data['username'], user_data['role'])
    return None

# ==================== ROUTES ====================

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # For demo purposes - in production, use proper password hashing
        if username == 'admin' and password == 'admin123':
            user = User(1, 'admin', 'admin')
            login_user(user)
            return redirect(url_for('dashboard'))
        elif username == 'budi' and password == 'user123':
            user = User(2, 'budi', 'user')
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's devices
    devices_query = """
        SELECT d.*, 
               COUNT(DISTINCT ms.session_id) as session_count,
               COUNT(ml.log_id) as log_count,
               COALESCE(SUM(ms.total_energy_kwh), 0) as total_energy
        FROM `device` d
        LEFT JOIN `monitoring_session` ms ON d.device_id = ms.device_id
        LEFT JOIN `monitoring_log` ml ON d.device_id = ml.device_id
        WHERE d.user_id = %s
        GROUP BY d.device_id
    """
    devices = db.execute_query(devices_query, (current_user.id,))
    
    # Get recent sessions
    sessions_query = """
        SELECT ms.*, d.device_name 
        FROM `monitoring_session` ms
        JOIN `device` d ON ms.device_id = d.device_id
        WHERE ms.user_id = %s
        ORDER BY ms.start_time DESC
        LIMIT 5
    """
    recent_sessions = db.execute_query(sessions_query, (current_user.id,))
    
    # Get energy summary
    summary_query = """
        SELECT 
            COUNT(DISTINCT ms.session_id) as total_sessions,
            COALESCE(SUM(ms.total_energy_kwh), 0) as total_energy,
            COALESCE(SUM(ms.energy_cost), 0) as total_cost,
            COUNT(DISTINCT d.device_id) as total_devices
        FROM `monitoring_session` ms
        JOIN `device` d ON ms.device_id = d.device_id
        WHERE ms.user_id = %s AND ms.status = 'COMPLETED'
    """
    summary = db.execute_query(summary_query, (current_user.id,), fetch_one=True)
    
    return render_template('dashboard.html', 
                         devices=devices or [],
                         recent_sessions=recent_sessions or [],
                         summary=summary or {})

@app.route('/devices')
@login_required
def devices():
    query = "SELECT * FROM `device` WHERE user_id = %s ORDER BY created_at DESC"
    devices = db.execute_query(query, (current_user.id,))
    return render_template('devices.html', devices=devices or [])

@app.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    query = "SELECT * FROM `user` ORDER BY created_at DESC"
    users = db.execute_query(query)
    return render_template('users.html', users=users or [])

@app.route('/monitoring')
@login_required
def monitoring():
    # Get user's devices for dropdown
    devices_query = "SELECT device_id, device_name FROM `device` WHERE user_id = %s"
    devices = db.execute_query(devices_query, (current_user.id,))
    return render_template('monitoring.html', devices=devices or [])

@app.route('/start_monitoring', methods=['POST'])
@login_required
def start_monitoring():
    data = request.get_json()
    device_id = data.get('device_id')
    session_name = data.get('session_name')
    initial_kwh = float(data.get('initial_kwh', 0))
    
    # Start new monitoring session
    query = """
        INSERT INTO `monitoring_session` 
        (device_id, user_id, session_name, start_time, initial_kwh, status)
        VALUES (%s, %s, %s, NOW(), %s, 'ACTIVE')
    """
    session_id = db.execute_query(query, (device_id, current_user.id, session_name, initial_kwh))
    
    # Simulate ESP32 sending data (in real app, this would be from actual ESP32)
    if session_id:
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'Monitoring session started: {session_name}'
        })
    
    return jsonify({'success': False, 'error': 'Failed to start session'})

@app.route('/stop_monitoring/<int:session_id>', methods=['POST'])
@login_required
def stop_monitoring(session_id):
    final_kwh = float(request.json.get('final_kwh', 0))
    
    # Update session to completed
    query = """
        UPDATE `monitoring_session` 
        SET end_time = NOW(), final_kwh = %s, status = 'COMPLETED'
        WHERE session_id = %s AND user_id = %s
    """
    db.execute_query(query, (final_kwh, session_id, current_user.id))
    
    return jsonify({'success': True, 'message': 'Monitoring session stopped'})

@app.route('/get_session_data/<int:session_id>')
@login_required
def get_session_data(session_id):
    # Get session info
    session_query = """
        SELECT ms.*, d.device_name 
        FROM `monitoring_session` ms
        JOIN `device` d ON ms.device_id = d.device_id
        WHERE ms.session_id = %s AND ms.user_id = %s
    """
    session_info = db.execute_query(session_query, (session_id, current_user.id), fetch_one=True)
    
    # Get logs for this session
    logs_query = """
        SELECT * FROM `monitoring_log` 
        WHERE session_id = %s 
        ORDER BY timestamp
    """
    logs = db.execute_query(logs_query, (session_id,))
    
    return jsonify({
        'session': session_info,
        'logs': logs or []
    })

@app.route('/simulate_data/<int:session_id>')
@login_required
def simulate_data(session_id):
    """Simulate ESP32 sending data (for demo purposes)"""
    # Generate random sensor data
    voltage = round(220 + random.uniform(-5, 5), 2)
    current = round(random.uniform(1.0, 5.0), 3)
    power = round(voltage * current, 2)
    energy = round(power * (5/3600), 6)  # 5 seconds interval
    
    # Insert into monitoring_log
    query = """
        INSERT INTO `monitoring_log` 
        (device_id, session_id, timestamp, voltage_v, current_a, active_power_w, energy_wh)
        SELECT device_id, %s, NOW(), %s, %s, %s, %s
        FROM `monitoring_session` WHERE session_id = %s
    """
    db.execute_query(query, (session_id, voltage, current, power, energy, session_id))
    
    return jsonify({
        'voltage': voltage,
        'current': current,
        'power': power,
        'energy': energy,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/logs')
@login_required
def logs():
    # Get all monitoring sessions for user
    query = """
        SELECT ms.*, d.device_name 
        FROM `monitoring_session` ms
        JOIN `device` d ON ms.device_id = d.device_id
        WHERE ms.user_id = %s
        ORDER BY ms.start_time DESC
    """
    sessions = db.execute_query(query, (current_user.id,))
    return render_template('logs.html', sessions=sessions or [])

@app.route('/reports')
@login_required
def reports():
    # Get energy consumption by device
    energy_query = """
        SELECT 
            d.device_name,
            d.location,
            COUNT(DISTINCT ms.session_id) as session_count,
            COALESCE(SUM(ms.total_energy_kwh), 0) as total_energy,
            COALESCE(SUM(ms.energy_cost), 0) as total_cost,
            AVG(ml.active_power_w) as avg_power,
            MAX(ml.active_power_w) as peak_power
        FROM `device` d
        LEFT JOIN `monitoring_session` ms ON d.device_id = ms.device_id
        LEFT JOIN `monitoring_log` ml ON d.device_id = ml.device_id
        WHERE d.user_id = %s
        GROUP BY d.device_id, d.device_name, d.location
    """
    energy_data = db.execute_query(energy_query, (current_user.id,))
    
    # Get daily energy consumption
    daily_query = """
        SELECT 
            DATE(ms.start_time) as date,
            SUM(ms.total_energy_kwh) as daily_energy,
            SUM(ms.energy_cost) as daily_cost
        FROM `monitoring_session` ms
        WHERE ms.user_id = %s AND ms.status = 'COMPLETED'
        GROUP BY DATE(ms.start_time)
        ORDER BY date DESC
        LIMIT 7
    """
    daily_data = db.execute_query(daily_query, (current_user.id,))
    
    return render_template('reports.html', 
                         energy_data=energy_data or [],
                         daily_data=daily_data or [])

# ==================== API ENDPOINTS ====================

@app.route('/api/devices', methods=['GET'])
@login_required
def api_devices():
    devices = db.execute_query("SELECT * FROM `device` WHERE user_id = %s", (current_user.id,))
    return jsonify(devices or [])

@app.route('/api/add_device', methods=['POST'])
@login_required
def api_add_device():
    data = request.get_json()
    query = """
        INSERT INTO `device` 
        (device_name, device_code, esp32_mac, user_id, location, device_type, power_rating_w)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    device_id = db.execute_query(query, (
        data['device_name'],
        data['device_code'],
        data['esp32_mac'],
        current_user.id,
        data['location'],
        data['device_type'],
        data['power_rating_w']
    ))
    
    if device_id:
        return jsonify({'success': True, 'device_id': device_id})
    return jsonify({'success': False, 'error': 'Failed to add device'})

@app.route('/api/delete_device/<int:device_id>', methods=['DELETE'])
@login_required
def api_delete_device(device_id):
    query = "DELETE FROM `device` WHERE device_id = %s AND user_id = %s"
    db.execute_query(query, (device_id, current_user.id))
    return jsonify({'success': True})

# ==================== INITIALIZATION ====================

with app.app_context():
    print("Initializing database...")
    db.setup_database()
    db.insert_master_data()
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
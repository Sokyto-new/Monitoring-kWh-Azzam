import mysql.connector
from mysql.connector import Error
from config import Config
import json

class Database:
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME
        }
        self.connection = None
    
    def connect(self):
        """Create database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            return self.connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None, fetch_one=False):
        """Execute SQL query"""
        connection = self.connect()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                if fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid
            
            return result
        except Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.disconnect()
    
    def setup_database(self):
        """Create database and tables if not exist"""
        # Create database
        create_db_query = f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}"
        temp_config = self.config.copy()
        temp_config.pop('database')
        
        try:
            conn = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()
            cursor.execute(create_db_query)
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Error creating database: {e}")
            return False
        
        # Connect to the database
        self.connect()
        
        # Create tables
        tables = self.get_table_queries()
        connection = self.connect()
        cursor = connection.cursor()
        
        try:
            for table_name, query in tables.items():
                cursor.execute(query)
                print(f"Table '{table_name}' created successfully")
            
            connection.commit()
            print("Database setup completed successfully!")
            return True
        except Error as e:
            print(f"Error creating tables: {e}")
            return False
        finally:
            cursor.close()
            self.disconnect()
    
    def get_table_queries(self):
        """Return dictionary of table creation queries"""
        return {
            'user': '''
                CREATE TABLE IF NOT EXISTS `user` (
                    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
                    `username` VARCHAR(50) UNIQUE NOT NULL,
                    `password_hash` VARCHAR(255) NOT NULL,
                    `email` VARCHAR(100) UNIQUE NOT NULL,
                    `full_name` VARCHAR(100),
                    `role` ENUM('admin', 'user', 'viewer') DEFAULT 'user',
                    `phone_number` VARCHAR(20),
                    `is_active` BOOLEAN DEFAULT TRUE,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `last_login` TIMESTAMP NULL
                )
            ''',
            'device': '''
                CREATE TABLE IF NOT EXISTS `device` (
                    `device_id` INT AUTO_INCREMENT PRIMARY KEY,
                    `device_name` VARCHAR(100) NOT NULL,
                    `device_code` VARCHAR(50) UNIQUE NOT NULL,
                    `esp32_mac` VARCHAR(17) UNIQUE NOT NULL,
                    `user_id` INT NOT NULL,
                    `location` VARCHAR(100),
                    `device_type` ENUM('lighting', 'appliance', 'ac', 'other') DEFAULT 'lighting',
                    `power_rating_w` DECIMAL(8,2),
                    `is_online` BOOLEAN DEFAULT FALSE,
                    `last_seen` TIMESTAMP NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE
                )
            ''',
            'monitoring_session': '''
                CREATE TABLE IF NOT EXISTS `monitoring_session` (
                    `session_id` INT AUTO_INCREMENT PRIMARY KEY,
                    `device_id` INT NOT NULL,
                    `user_id` INT NOT NULL,
                    `session_name` VARCHAR(100),
                    `start_time` DATETIME NOT NULL,
                    `end_time` DATETIME,
                    `initial_kwh` DECIMAL(12,6) NOT NULL,
                    `final_kwh` DECIMAL(12,6),
                    `total_energy_kwh` DECIMAL(12,6) AS (COALESCE(`final_kwh`, 0) - `initial_kwh`) STORED,
                    `energy_cost` DECIMAL(12,2) AS ((COALESCE(`final_kwh`, 0) - `initial_kwh`) * 1500) STORED,
                    `status` ENUM('ACTIVE', 'COMPLETED', 'PAUSED', 'CANCELLED') DEFAULT 'ACTIVE',
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (`device_id`) REFERENCES `device`(`device_id`) ON DELETE CASCADE,
                    FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE
                )
            ''',
            'monitoring_log': '''
                CREATE TABLE IF NOT EXISTS `monitoring_log` (
                    `log_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                    `device_id` INT NOT NULL,
                    `session_id` INT,
                    `timestamp` DATETIME NOT NULL,
                    `voltage_v` DECIMAL(7,3) NOT NULL,
                    `current_a` DECIMAL(8,4) NOT NULL,
                    `active_power_w` DECIMAL(10,4) NOT NULL,
                    `energy_wh` DECIMAL(12,6) NOT NULL,
                    `device_status` ENUM('ON', 'OFF') DEFAULT 'ON',
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (`device_id`) REFERENCES `device`(`device_id`) ON DELETE CASCADE,
                    FOREIGN KEY (`session_id`) REFERENCES `monitoring_session`(`session_id`) ON DELETE SET NULL
                )
            '''
        }
    
    def insert_master_data(self):
        """Insert initial master data"""
        # Insert admin user (password: admin123)
        admin_query = '''
            INSERT IGNORE INTO `user` (username, password_hash, email, full_name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        admin_data = ('admin', 'pbkdf2:sha256:260000$hash$adminhash', 'admin@iot.com', 'Administrator', 'admin', True)
        
        # Insert test user (password: user123)
        user_query = '''
            INSERT IGNORE INTO `user` (username, password_hash, email, full_name, role, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        user_data = ('budi', 'pbkdf2:sha256:260000$hash$userhash', 'budi@iot.com', 'Budi Santoso', 'user', True)
        
        # Insert test devices
        devices_query = '''
            INSERT IGNORE INTO `device` (device_name, device_code, esp32_mac, user_id, location, device_type, power_rating_w)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        devices_data = [
            ('Kitchen Lights', 'DEV-KITCH-001', 'AA:BB:CC:DD:EE:FF', 2, 'Kitchen', 'lighting', 100.00),
            ('Living Room AC', 'DEV-LIVING-001', '11:22:33:44:55:66', 2, 'Living Room', 'ac', 500.00),
            ('Workspace PC', 'DEV-WORK-001', '77:88:99:AA:BB:CC', 2, 'Workspace', 'appliance', 300.00)
        ]
        
        try:
            # Insert users
            self.execute_query(admin_query, admin_data)
            self.execute_query(user_query, user_data)
            
            # Insert devices
            for device in devices_data:
                self.execute_query(devices_query, device)
            
            print("Master data inserted successfully!")
            return True
        except Error as e:
            print(f"Error inserting master data: {e}")
            return False

# Initialize database
db = Database()
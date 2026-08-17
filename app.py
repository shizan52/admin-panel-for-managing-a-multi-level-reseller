from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_session import Session
import mysql.connector
import bcrypt
from config import MYSQL_CONFIG
import os
import json
from datetime import timedelta, datetime, date
from functools import wraps
import random

app = Flask(__name__)

# Flask Configuration
app.config['SECRET_KEY'] = os.urandom(24)  # Generate random secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)  # Session valid for 12 hours
Session(app)

# Role hierarchy used by inbox and other features (kept simple)
ROLE_HIERARCHY = {
    'super_master': ['master', 'admin', 'super_seller', 'seller'],
    'master': ['admin', 'super_seller', 'seller'],
    'admin': ['super_seller', 'seller'],
    'super_seller': ['seller'],
    'seller': []
}

def get_db_connection():
    """Create database connection"""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    return conn

def get_descendant_user_ids(user_id):
    """
    Recursively get all descendant user IDs for a given user.
    Returns a list of user IDs including the user itself and all descendants.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    descendant_ids = [user_id]
    to_process = [user_id]
    
    while to_process:
        current_id = to_process.pop(0)
        # Find all users created by current_id
        cursor.execute('SELECT id FROM users WHERE created_by = %s', (current_id,))
        children = cursor.fetchall()
        for child in children:
            child_id = child['id']
            if child_id not in descendant_ids:
                descendant_ids.append(child_id)
                to_process.append(child_id)
    
    conn.close()
    return descendant_ids

def init_db():
    """Initialize database with users table and default users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Ensure created_by column exists for hierarchical ownership (nullable)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_by INT")
        conn.commit()
    except Exception:
        # Column probably already exists
        conn.rollback()
        pass
    # Ensure mac_address column exists for users (nullable)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN mac_address VARCHAR(255) DEFAULT NULL")
        conn.commit()
    except Exception:
        # Column probably exists already
        conn.rollback()
        pass
    
    # Create messages/inbox table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INT PRIMARY KEY AUTO_INCREMENT,
            from_user_id INT NOT NULL,
            to_user_id INT NOT NULL,
            subject VARCHAR(500) NOT NULL,
            message TEXT NOT NULL,
            is_read INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Create news table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INT PRIMARY KEY AUTO_INCREMENT,
            author_id INT NOT NULL,
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            target_role VARCHAR(50) NOT NULL,
            is_active INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Create news_read tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_read (
            id INT PRIMARY KEY AUTO_INCREMENT,
            news_id INT NOT NULL,
            user_id INT NOT NULL,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(news_id, user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Create keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `keys` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            key_code VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active_until DATE NULL,
            is_paid INT DEFAULT 0,
            is_active INT DEFAULT 0,
            is_blocked INT DEFAULT 0,
            mac_address VARCHAR(255) DEFAULT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Create index on keys for faster queries
    try:
        cursor.execute('CREATE INDEX idx_keys_created_by ON `keys`(created_by)')
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    try:
        cursor.execute('CREATE INDEX idx_keys_key_code ON `keys`(key_code)')
        conn.commit()
    except Exception:
        conn.rollback()
        pass

    # Ensure mac_address column exists (for older DBs)
    try:
        cursor.execute("ALTER TABLE `keys` ADD COLUMN mac_address VARCHAR(255) DEFAULT NULL")
        conn.commit()
    except Exception:
        # Column probably exists already
        conn.rollback()
        pass
    
    # Ensure is_blocked column exists (for older DBs)
    try:
        cursor.execute("ALTER TABLE `keys` ADD COLUMN is_blocked INT DEFAULT 0")
        conn.commit()
    except Exception:
        # Column probably exists already
        conn.rollback()
        pass
    
    # Create key_access table for device tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_access (
            id INT PRIMARY KEY AUTO_INCREMENT,
            key_id INT NOT NULL,
            ip_address VARCHAR(255),
            last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (key_id) REFERENCES `keys`(id) ON DELETE CASCADE,
            UNIQUE(key_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Create key_access_history table for logging all access attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_access_history (
            id INT PRIMARY KEY AUTO_INCREMENT,
            key_id INT NOT NULL,
            ip_address VARCHAR(255),
            user_agent TEXT,
            access_status VARCHAR(50) NOT NULL,
            access_message TEXT,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (key_id) REFERENCES `keys`(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Create index for faster history queries
    try:
        cursor.execute('CREATE INDEX idx_history_key_id ON key_access_history(key_id)')
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    try:
        cursor.execute('CREATE INDEX idx_history_accessed_at ON key_access_history(accessed_at)')
        conn.commit()
    except Exception:
        conn.rollback()
        pass

    # Create default super_master user if not exists
    try:
        cursor.execute("SELECT id FROM users WHERE username = 'super_master'")
        if not cursor.fetchone():
            hashed_password = bcrypt.hashpw('super_master123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username, password, role, created_by) VALUES (%s, %s, %s, NULL)",
                ('super_master', hashed_password, 'super_master')
            )
            conn.commit()
            print("Default super_master user created (username: super_master, password: super_master123)")
    except Exception as e:
        print(f"Error creating default super_master user: {e}")
        conn.rollback()

    # Create tickets table for storing success tickets submitted by desktop app
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INT PRIMARY KEY AUTO_INCREMENT,
            ticket_date DATE NOT NULL,
            from_location VARCHAR(255),
            to_location VARCHAR(255),
            source VARCHAR(255),
            notes TEXT,
            session_name VARCHAR(255),
            asset_folder_data LONGBLOB,
            asset_files_list JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session_name (session_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Add session_name column to existing tickets table (for migration)
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN session_name VARCHAR(255) DEFAULT NULL")
        conn.commit()
    except Exception:
        # Column probably exists already
        conn.rollback()
        pass
    
    # Add asset_folder_data column to existing tickets table (for migration)
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN asset_folder_data LONGBLOB DEFAULT NULL")
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    # Add asset_files_list column to existing tickets table (for migration)
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN asset_files_list JSON DEFAULT NULL")
        conn.commit()
    except Exception:
        conn.rollback()
        pass
    
    # Create failed_logs table for storing failed booking attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS failed_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            log_file_path VARCHAR(500) NOT NULL,
            log_date DATE NOT NULL,
            from_station VARCHAR(100),
            to_station VARCHAR(100),
            train_number VARCHAR(50),
            error_message TEXT,
            log_content LONGTEXT,
            session_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_log_date (log_date),
            INDEX idx_created_at (created_at),
            INDEX idx_session_name (session_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')
    conn.commit()
    
    # Add session_name column to existing failed_logs table (for migration)
    try:
        cursor.execute("ALTER TABLE failed_logs ADD COLUMN session_name VARCHAR(255) DEFAULT NULL")
        conn.commit()
    except Exception:
        # Column probably exists already
        conn.rollback()
        pass
    
    # Ensure a clean user set: remove any users not in the approved default list
    # and reset related tables so the project only contains the mandated logins.
    # Only 5 masters are hardcoded - all other users (admin, super_seller, seller) 
    # will be created dynamically by masters through the UI
    default_users = [
        ('master', 'master123', 'master'),
        ('master2', 'master456', 'master'),
        ('master3', 'master789', 'master'),
        ('master4', 'master012', 'master'),
        ('master5', 'master345', 'master'),
    ]

    # Clear dependent tables ONLY IF no users exist (first time setup)
    cursor.execute('SELECT COUNT(*) as count FROM users')
    result = cursor.fetchone()
    user_count = result[0] if result else 0
    
    if user_count == 0:
        # First time setup - clear all tables
        tables_to_clear = ['messages', 'news_read', 'news', 'key_access_history', 'key_access', '`keys`']
        for tbl in tables_to_clear:
            try:
                cursor.execute(f'DELETE FROM {tbl}')
            except Exception:
                # ignore if table doesn't exist or delete fails
                pass

        # Remove all users and recreate only the approved default users
        cursor.execute('DELETE FROM users')

        # Get super_master id to link default masters
        cursor.execute("SELECT id FROM users WHERE username = 'super_master'")
        super_master_user = cursor.fetchone()
        super_master_id = super_master_user[0] if super_master_user else None

        users_added = []
        for username, password, role in default_users:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                'INSERT INTO users (username, password, role, created_by) VALUES (%s, %s, %s, %s)',
                (username, hashed_password, role, super_master_id)
            )
            users_added.append(f"{role.title()}: username='{username}', password='{password}'")

        conn.commit()
        
        # All masters are now linked to super_master
        # Users will be created dynamically through the UI by masters
        
        print("✅ Database initialized — 5 master users linked to super_master:")
        for user_info in users_added:
            print(f"   {user_info}")
    else:
        # Database already has users - update existing masters to link with super_master
        cursor.execute("SELECT id FROM users WHERE username = 'super_master'")
        super_master_user = cursor.fetchone()
        
        if super_master_user:
            super_master_id = super_master_user[0]
            # Update all existing masters (master, master2, master3, master4, master5) to be created by super_master
            master_usernames = ['master', 'master2', 'master3', 'master4', 'master5']
            for master_username in master_usernames:
                try:
                    cursor.execute(
                        'UPDATE users SET created_by = %s WHERE username = %s AND role = %s AND (created_by IS NULL OR created_by != %s)',
                        (super_master_id, master_username, 'master', super_master_id)
                    )
                except Exception as e:
                    print(f"Note: Could not update {master_username}: {e}")
            conn.commit()
            print("✅ Existing master users linked to super_master")
        
        print("ℹ️  Database already initialized - skipping data reset")
        conn.commit()

    conn.close()

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to protect routes by user role.

    Accepts a single role string or an iterable of allowed roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user_role = session.get('role')
            # allow passing a single role or a list/tuple/set of roles
            if isinstance(required_role, (list, tuple, set)):
                if user_role not in required_role:
                    return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
            else:
                if user_role != required_role:
                    return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Redirect to login if not authenticated, else to appropriate dashboard"""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'super_master':
            return redirect(url_for('super_master_dashboard'))
        elif role == 'master':
            return redirect(url_for('master_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'super_seller':
            return redirect(url_for('super_seller_dashboard'))
        elif role == 'seller':
            return redirect(url_for('seller_dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Serve login page"""
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login API request"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        login_type = data.get('loginType', '').strip()
        
        if not username or not password or not login_type:
            return jsonify({
                'success': False,
                'message': 'Please fill in all fields'
            }), 400
        
        # Query database for user
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM users WHERE username = %s AND role = %s',
            (username, login_type)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid username or login type'
            }), 401
        
        # Verify password
        # Convert stored password string back to bytes for bcrypt comparison
        stored_password = user['password'].encode('utf-8') if isinstance(user['password'], str) else user['password']
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return jsonify({
                'success': False,
                'message': 'Invalid password'
            }), 401
        
        # Create session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True
        
        # Determine redirect URL
        if user['role'] == 'super_master':
            redirect_url = url_for('super_master_dashboard')
        elif user['role'] == 'master':
            redirect_url = url_for('master_dashboard')
        elif user['role'] == 'admin':
            redirect_url = url_for('admin_dashboard')
        elif user['role'] == 'super_seller':
            redirect_url = url_for('super_seller_dashboard')
        elif user['role'] == 'seller':
            redirect_url = url_for('seller_dashboard')
        else:
            redirect_url = url_for('login')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': redirect_url,
            'user': {
                'username': user['username'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle logout API request"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully',
        'redirect': url_for('login')
    }), 200

@app.route('/super_master_dashboard')
@login_required
@role_required('super_master')
def super_master_dashboard():
    """Serve Super Master Dashboard"""
    return render_template('super_master_dashboard.html')

@app.route('/master_dashboard')
@login_required
@role_required('master')
def master_dashboard():
    """Serve Master Dashboard"""
    return render_template('master_dashboard.html')


@app.route('/api/tickets/submit', methods=['POST'])
def api_tickets_submit():
    """Endpoint for desktop app to submit a success ticket.

    Expected JSON: { 
        ticket_date: 'YYYY-MM-DD', 
        from_location: '', 
        to_location: '', 
        source: '', 
        notes: '', 
        session_name: 'NDLS_BCT_12952',
        asset_folder_base64: '<base64 encoded zip>',
        asset_files: ['booking_script.log', 'irctc_logs/file.json', ...]
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Debug logging
        print(f"[tickets.submit] Received data keys: {list(data.keys())}")
        print(f"[tickets.submit] ticket_date: {data.get('ticket_date')}, from: {data.get('from_location')}, to: {data.get('to_location')}, source: {data.get('source')}")
        print(f"[tickets.submit] asset_folder_base64 length: {len(data.get('asset_folder_base64', ''))}")
        print(f"[tickets.submit] asset_files count: {len(data.get('asset_files', []))}")
        
        ticket_date = data.get('ticket_date') or data.get('date')
        from_location = data.get('from_location') or data.get('from')
        to_location = data.get('to_location') or data.get('to')
        source = data.get('source')
        notes = data.get('notes')
        session_name = data.get('session_name')
        asset_folder_base64 = data.get('asset_folder_base64')
        asset_files = data.get('asset_files', [])

        if not ticket_date:
            print("[tickets.submit] ERROR: Missing ticket_date")
            return jsonify(success=False, message='Missing ticket_date'), 400

        # Decode base64 asset folder data if provided
        asset_blob = None
        if asset_folder_base64:
            import base64
            try:
                asset_blob = base64.b64decode(asset_folder_base64)
                print(f"[tickets.submit] Decoded asset folder: {len(asset_blob)} bytes")
            except Exception as decode_err:
                print(f"[tickets.submit] ERROR decoding base64: {decode_err}")
                return jsonify(success=False, message=f'Base64 decode error: {str(decode_err)}'), 400
        else:
            print("[tickets.submit] WARNING: No asset_folder_base64 provided")

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Convert asset_files list to JSON string
        asset_files_json = json.dumps(asset_files) if asset_files else None
        print(f"[tickets.submit] Inserting: ticket_date={ticket_date}, asset_blob_size={len(asset_blob) if asset_blob else 0}, asset_files_count={len(asset_files)}")
        
        try:
            cur.execute(
                'INSERT INTO tickets (ticket_date, from_location, to_location, source, notes, session_name, asset_folder_data, asset_files_list) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (ticket_date, from_location, to_location, source, notes, session_name, asset_blob, asset_files_json)
            )
            conn.commit()
            ticket_id = cur.lastrowid
            conn.close()
            
            print(f"[tickets.submit] SUCCESS: Ticket ID {ticket_id}, Asset size: {len(asset_blob) if asset_blob else 0} bytes, Files: {len(asset_files)}")
            return jsonify(success=True, ticket_id=ticket_id), 201
        except Exception as insert_error:
            print(f"[tickets.submit] INSERT ERROR: {insert_error}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            conn.close()
            return jsonify(success=False, message=f'Database insert error: {str(insert_error)}'), 500
    except Exception as e:
        print(f"[tickets.submit] GENERAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f'Server error: {str(e)}'), 500


@app.route('/api/tickets/today', methods=['GET'])
def api_tickets_today():
    """Return tickets for today as JSON list"""
    try:
        today = date.today().isoformat()
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id, ticket_date, from_location, to_location, source, notes, created_at FROM tickets WHERE ticket_date = %s ORDER BY created_at DESC', (today,))
        rows = cur.fetchall()
        conn.close()

        tickets = []
        for r in rows:
            tickets.append({
                'id': r['id'],
                'ticket_date': r['ticket_date'],
                'from_location': r['from_location'],
                'to_location': r['to_location'],
                'source': r['source'],
                'notes': r['notes'],
                'created_at': str(r['created_at']) if r['created_at'] else None
            })

        return jsonify(success=True, tickets=tickets), 200
    except Exception as e:
        print(f"[tickets.today] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/tickets/last24h', methods=['GET'])
def api_tickets_last24h():
    """Return tickets from last 24 hours as JSON list"""
    try:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT id, ticket_date, from_location, to_location, source, notes, created_at FROM tickets WHERE created_at >= %s ORDER BY created_at DESC', (cutoff_time,))
        rows = cur.fetchall()
        conn.close()

        tickets = []
        for r in rows:
            tickets.append({
                'id': r['id'],
                'ticket_date': str(r['ticket_date']) if r['ticket_date'] else None,
                'from_location': r['from_location'],
                'to_location': r['to_location'],
                'source': r['source'],
                'notes': r['notes'],
                'created_at': str(r['created_at']) if r['created_at'] else None
            })

        return jsonify(success=True, tickets=tickets), 200
    except Exception as e:
        print(f"[tickets.last24h] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/failed-logs/submit', methods=['POST'])
def api_failed_logs_submit():
    """Endpoint for irctc22.py to submit a failed booking log with asset folder.
    
    Expected JSON: {
        log_file_path: 'path/to/log',
        log_date: 'YYYY-MM-DD',
        from_station: 'XXX',
        to_station: 'YYY',
        train_number: '12345',
        error_message: 'Error description',
        log_content: 'Full log content',
        asset_folder_zip: 'base64_encoded_zip_data',
        asset_files_list: ['file1.log', 'file2.json', ...]
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        log_file_path = data.get('log_file_path')
        log_date = data.get('log_date') or date.today().isoformat()
        from_station = data.get('from_station')
        to_station = data.get('to_station')
        train_number = data.get('train_number')
        error_message = data.get('error_message')
        log_content = data.get('log_content')
        session_name = data.get('session_name')
        asset_folder_zip = data.get('asset_folder_zip')  # Base64 encoded zip
        asset_files_list = data.get('asset_files_list', [])  # List of files

        if not log_file_path:
            return jsonify(success=False, message='Missing log_file_path'), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create table if not exists with asset columns
        cur.execute('''CREATE TABLE IF NOT EXISTS failed_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            log_file_path VARCHAR(255),
            log_date DATE,
            from_station VARCHAR(100),
            to_station VARCHAR(100),
            train_number VARCHAR(20),
            error_message TEXT,
            log_content LONGTEXT,
            session_name VARCHAR(255),
            asset_folder_data LONGBLOB,
            asset_files_list JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        
        # Ensure asset columns exist (for older databases)
        try:
            cur.execute('ALTER TABLE failed_logs ADD COLUMN asset_folder_data LONGBLOB')
            conn.commit()
        except Exception:
            pass
        try:
            cur.execute('ALTER TABLE failed_logs ADD COLUMN asset_files_list JSON')
            conn.commit()
        except Exception:
            pass
        
        # Decode base64 zip if provided
        asset_blob = None
        if asset_folder_zip:
            import base64
            asset_blob = base64.b64decode(asset_folder_zip)
        
        # Convert files list to JSON
        import json
        files_json = json.dumps(asset_files_list) if asset_files_list else None
        
        cur.execute('''INSERT INTO failed_logs 
                       (log_file_path, log_date, from_station, to_station, train_number, error_message, log_content, session_name, asset_folder_data, asset_files_list) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (log_file_path, log_date, from_station, to_station, train_number, error_message, log_content, session_name, asset_blob, files_json))
        conn.commit()
        log_id = cur.lastrowid
        conn.close()
        return jsonify(success=True, log_id=log_id), 201
    except Exception as e:
        print(f"[failed_logs.submit] exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/failed-logs/today', methods=['GET'])
def api_failed_logs_today():
    """Return failed logs for today"""
    try:
        today = date.today().isoformat()
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('''SELECT id, log_file_path, log_date, from_station, to_station, train_number, 
                              error_message, created_at 
                       FROM failed_logs 
                       WHERE log_date = %s 
                       ORDER BY created_at DESC''', (today,))
        rows = cur.fetchall()
        conn.close()

        logs = []
        for r in rows:
            logs.append({
                'id': r['id'],
                'log_file_path': r['log_file_path'],
                'log_date': str(r['log_date']),
                'from_station': r['from_station'],
                'to_station': r['to_station'],
                'train_number': r['train_number'],
                'error_message': r['error_message'],
                'created_at': str(r['created_at']) if r['created_at'] else None
            })

        return jsonify(success=True, logs=logs), 200
    except Exception as e:
        print(f"[failed_logs.today] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/failed-logs/last24h', methods=['GET'])
def api_failed_logs_last24h():
    """Return failed logs from last 24 hours"""
    try:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('''SELECT id, log_file_path, log_date, from_station, to_station, train_number, 
                              error_message, created_at 
                       FROM failed_logs 
                       WHERE created_at >= %s 
                       ORDER BY created_at DESC''', (cutoff_time,))
        rows = cur.fetchall()
        conn.close()

        logs = []
        for r in rows:
            logs.append({
                'id': r['id'],
                'log_file_path': r['log_file_path'],
                'log_date': str(r['log_date']) if r['log_date'] else None,
                'from_station': r['from_station'],
                'to_station': r['to_station'],
                'train_number': r['train_number'],
                'error_message': r['error_message'],
                'created_at': str(r['created_at']) if r['created_at'] else None
            })

        return jsonify(success=True, logs=logs), 200
    except Exception as e:
        print(f"[failed_logs.last24h] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/failed-logs/view/<int:log_id>', methods=['GET'])
def api_failed_logs_view(log_id):
    """View full log content for a specific failed log"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('''SELECT id, log_file_path, log_date, from_station, to_station, train_number, 
                              error_message, log_content, asset_files_list, created_at 
                       FROM failed_logs 
                       WHERE id = %s''', (log_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify(success=False, message='Log not found'), 404
        
        # Parse asset files list from JSON
        import json
        asset_files = []
        if row['asset_files_list']:
            try:
                asset_files = json.loads(row['asset_files_list'])
            except:
                asset_files = []

        log_data = {
            'id': row['id'],
            'log_file_path': row['log_file_path'],
            'log_date': str(row['log_date']),
            'from_station': row['from_station'],
            'to_station': row['to_station'],
            'train_number': row['train_number'],
            'error_message': row['error_message'],
            'log_content': row['log_content'],
            'asset_files': asset_files,
            'created_at': str(row['created_at']) if row['created_at'] else None
        }

        return jsonify(success=True, log=log_data), 200
    except Exception as e:
        print(f"[failed_logs.view] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/failed-logs/download/<int:log_id>', methods=['GET'])
def api_failed_logs_download(log_id):
    """Download asset folder zip for a specific failed log"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT asset_folder_data, from_station, to_station, train_number, log_date FROM failed_logs WHERE id = %s', (log_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify(success=False, message='Log not found'), 404
        
        if not row['asset_folder_data']:
            return jsonify(success=False, message='No asset folder available'), 404

        filename = f"failed_assets_{row['from_station']}_{row['to_station']}_{row['train_number']}_{row['log_date']}.zip"
        
        from flask import Response
        return Response(
            row['asset_folder_data'],
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    except Exception as e:
        print(f"[failed_logs.download] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/failed-logs/asset-file/<int:log_id>/<path:filename>', methods=['GET'])
def api_failed_logs_asset_file(log_id, filename):
    """Get specific file from failed log asset folder"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT asset_folder_data, asset_files_list FROM failed_logs WHERE id = %s', (log_id,))
        row = cur.fetchone()
        conn.close()

        if not row or not row['asset_folder_data']:
            return jsonify(success=False, message='Asset folder not found'), 404

        # Extract specific file from zip
        import zipfile
        import io
        
        zip_data = io.BytesIO(row['asset_folder_data'])
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            # Find the file in zip
            try:
                file_content = zip_ref.read(filename)
                
                # Determine mime type
                if filename.endswith('.log') or filename.endswith('.txt'):
                    mimetype = 'text/plain'
                elif filename.endswith('.json'):
                    mimetype = 'application/json'
                elif filename.endswith('.html'):
                    mimetype = 'text/html'
                elif filename.endswith('.png') or filename.endswith('.jpg'):
                    mimetype = 'image/png'
                else:
                    mimetype = 'application/octet-stream'
                
                from flask import Response
                return Response(file_content, mimetype=mimetype)
            except KeyError:
                return jsonify(success=False, message=f'File {filename} not found in asset folder'), 404
                
    except Exception as e:
        print(f"[failed_logs.asset-file] exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/tickets/view/<int:ticket_id>', methods=['GET'])
def api_tickets_view(ticket_id):
    """View full details for a specific success ticket including asset files list"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('''SELECT id, ticket_date, from_location, to_location, source, notes, created_at, asset_files_list
                       FROM tickets 
                       WHERE id = %s''', (ticket_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify(success=False, message='Ticket not found'), 404

        # Parse asset files list
        asset_files = []
        if row['asset_files_list']:
            try:
                asset_files = json.loads(row['asset_files_list'])
                print(f"[tickets.view] Ticket {ticket_id}: Found {len(asset_files)} asset files")
            except Exception as parse_error:
                print(f"[tickets.view] Ticket {ticket_id}: Error parsing asset_files_list: {parse_error}")
        else:
            print(f"[tickets.view] Ticket {ticket_id}: No asset_files_list in database")

        ticket_data = {
            'id': row['id'],
            'ticket_date': str(row['ticket_date']),
            'from_location': row['from_location'],
            'to_location': row['to_location'],
            'source': row['source'],
            'notes': row['notes'],
            'created_at': str(row['created_at']) if row['created_at'] else None,
            'asset_files': asset_files
        }

        return jsonify(success=True, ticket=ticket_data), 200
    except Exception as e:
        print(f"[tickets.view] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/tickets/download/<int:ticket_id>', methods=['GET'])
def api_tickets_download(ticket_id):
    """Download entire asset folder as zip file for a specific success ticket"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT ticket_date, from_location, to_location, source, asset_folder_data FROM tickets WHERE id = %s', (ticket_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify(success=False, message='Ticket not found'), 404

        if not row['asset_folder_data']:
            return jsonify(success=False, message='No asset folder data available'), 404

        # Return zip file
        filename = f"asset_folder_{row['from_location']}_{row['to_location']}_{row['ticket_date']}.zip"
        
        from flask import Response
        return Response(
            row['asset_folder_data'],
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
    except Exception as e:
        print(f"[tickets.download] exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/tickets/asset-file/<int:ticket_id>/<path:filename>', methods=['GET'])
def api_tickets_asset_file(ticket_id, filename):
    """Get specific file from asset folder"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT asset_folder_data, asset_files_list FROM tickets WHERE id = %s', (ticket_id,))
        row = cur.fetchone()
        conn.close()

        if not row or not row['asset_folder_data']:
            return jsonify(success=False, message='Asset folder not found'), 404

        # Extract specific file from zip
        import zipfile
        import io
        
        zip_data = io.BytesIO(row['asset_folder_data'])
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            # Find the file in zip
            try:
                file_content = zip_ref.read(filename)
                
                # Determine mime type
                if filename.endswith('.log') or filename.endswith('.txt'):
                    mimetype = 'text/plain'
                elif filename.endswith('.json'):
                    mimetype = 'application/json'
                elif filename.endswith('.html'):
                    mimetype = 'text/html'
                elif filename.endswith('.png') or filename.endswith('.jpg'):
                    mimetype = 'image/png'
                else:
                    mimetype = 'application/octet-stream'
                
                from flask import Response
                return Response(file_content, mimetype=mimetype)
            except KeyError:
                return jsonify(success=False, message=f'File {filename} not found in asset folder'), 404
                
    except Exception as e:
        print(f"[tickets.asset-file] exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/booking-sessions/list', methods=['GET'])
def api_booking_sessions_list():
    """Get list of all booking sessions from venom/asset/booking_sessions"""
    try:
        import json
        workspace_root = os.path.dirname(os.path.abspath(__file__))
        booking_sessions_dir = os.path.join(workspace_root, "venom", "asset", "booking_sessions")
        
        if not os.path.exists(booking_sessions_dir):
            return jsonify(success=True, sessions=[]), 200
        
        sessions = []
        for session_folder in os.listdir(booking_sessions_dir):
            session_path = os.path.join(booking_sessions_dir, session_folder)
            if not os.path.isdir(session_path):
                continue
            
            # Try to load session metadata
            metadata_file = os.path.join(session_path, "session_info.json")
            session_info = {
                "folder_name": session_folder,
                "path": session_path,
                "success": None,
                "pnr": None,
                "error_message": None,
                "timestamp": None
            }
            
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        session_info.update(metadata)
                except Exception:
                    pass
            
            # Extract info from folder name (FROM_TO_TRAIN_DATETIME)
            parts = session_folder.split('_')
            if len(parts) >= 4:
                session_info['from_station'] = parts[0]
                session_info['to_station'] = parts[2] if len(parts) > 2 else None
                session_info['train_number'] = parts[3] if len(parts) > 3 else None
            
            # Check for log file
            log_file = os.path.join(session_path, "booking_script.log")
            if os.path.exists(log_file):
                session_info['has_log'] = True
                session_info['log_size'] = os.path.getsize(log_file)
            else:
                session_info['has_log'] = False
            
            sessions.append(session_info)
        
        # Sort by timestamp (newest first)
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify(success=True, sessions=sessions), 200
    except Exception as e:
        print(f"[booking_sessions.list] exception: {e}")
        return jsonify(success=False, message='Server error'), 500


@app.route('/api/booking-sessions/view/<path:session_name>', methods=['GET'])
def api_booking_session_view(session_name):
    """View details of a specific booking session"""
    try:
        import json
        workspace_root = os.path.dirname(os.path.abspath(__file__))
        session_path = os.path.join(workspace_root, "venom", "asset", "booking_sessions", session_name)
        
        if not os.path.exists(session_path):
            return jsonify(success=False, message='Session not found'), 404
        
        # Load metadata
        metadata_file = os.path.join(session_path, "session_info.json")
        session_data = {}
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        
        # Load log content
        log_file = os.path.join(session_path, "booking_script.log")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                session_data['log_content'] = f.read()
        
        # List all files in session
        session_files = []
        for root, dirs, files in os.walk(session_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, session_path)
                session_files.append({
                    'name': file,
                    'path': rel_path,
                    'size': os.path.getsize(file_path)
                })
        
        session_data['files'] = session_files
        
        return jsonify(success=True, session=session_data), 200
    except Exception as e:
        print(f"[booking_session.view] exception: {e}")
        return jsonify(success=False, message='Server error'), 500

@app.route('/admin_dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    """Serve Admin Dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/super_seller_dashboard')
@login_required
@role_required('super_seller')
def super_seller_dashboard():
    """Serve Super Seller Dashboard"""
    return render_template('super_seller_dashboard.html')

@app.route('/seller_dashboard')
@login_required
@role_required('seller')
def seller_dashboard():
    """Serve Seller Dashboard"""
    return render_template('seller_dashboard.html')

@app.route('/api/session-check')
def session_check():
    """Check if user session is valid"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'username': session.get('username'),
                'role': session.get('role')
            }
        }), 200
    return jsonify({'authenticated': False}), 401

# ==================== INBOX/MESSAGES ROUTES ====================

@app.route('/api/inbox/messages', methods=['GET'])
@login_required
def get_inbox_messages():
    """Get all messages for logged-in user"""
    try:
        user_id = session.get('user_id')
        print(f"User {session.get('username')} ({user_id}) fetching inbox messages")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get latest 50 messages sent to this user with sender info
        cursor.execute('''
            SELECT 
                m.id,
                m.subject,
                m.message,
                m.is_read,
                m.created_at,
                u.username as from_username
            FROM messages m
            LEFT JOIN users u ON m.from_user_id = u.id
            WHERE m.to_user_id = %s
            ORDER BY m.created_at DESC
            LIMIT 50
        ''', (user_id,))
        rows = cursor.fetchall()

        messages_list = []
        for r in rows:
            messages_list.append({
                'id': r['id'],
                'subject': r['subject'],
                'message': r['message'],
                'from_username': r['from_username'],
                'is_read': bool(r['is_read']),
                'created_at': str(r['created_at']) if r['created_at'] else None
            })

        print(f"Fetched {len(messages_list)} messages for user_id={user_id}")

        # unread count
        cursor.execute('SELECT COUNT(*) as cnt FROM messages WHERE to_user_id = %s AND is_read = 0', (user_id,))
        unread_row = cursor.fetchone()
        unread_count = unread_row['cnt'] if unread_row else 0

        conn.close()

        # Provide both 'unread_count' and legacy 'unread' key for frontend compatibility
        return jsonify({'success': True, 'messages': messages_list, 'unread_count': unread_count, 'unread': unread_count}), 200
    except Exception as e:
        print(f"Error fetching inbox for {session.get('username')}: {e}")
        return jsonify({'success': False, 'message': 'Error fetching messages'}), 500

@app.route('/api/inbox/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to another user"""
    try:
        data = request.get_json() or {}
        to_username = (data.get('to_username') or '').strip()
        to_user_id_override = data.get('to_user_id')
        subject = (data.get('subject') or '').strip()
        message = (data.get('message') or '').strip()

        if not to_username or not subject or not message:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        from_user_id = session.get('user_id')
        from_role = session.get('role')

        print(f"User {session.get('username')} ({from_user_id}) sending inbox message to {to_username}")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get recipient user: prefer explicit to_user_id if provided (avoids username ambiguity)
        recipient = None
        if to_user_id_override:
            try:
                int_id = int(to_user_id_override)
                cursor.execute('SELECT id, role, username FROM users WHERE id = %s', (int_id,))
                recipient = cursor.fetchone()
            except Exception:
                recipient = None

        if not recipient and to_username:
            cursor.execute('SELECT id, role, username FROM users WHERE username = %s', (to_username,))
            recipient = cursor.fetchone()

        if not recipient:
            conn.close()
            return jsonify({'success': False, 'message': f'User "{to_username}" not found'}), 404

        # Permission check per requirement:
        # - seller can send only to admin or master
        # - others can send to anyone
        recipient_role = recipient['role']
        print(f"Recipient found: id={recipient['id']}, role={recipient_role}")
        if from_role == 'seller' and recipient_role not in ('admin', 'master'):
            conn.close()
            return jsonify({'success': False, 'message': 'Permission denied for recipient'}), 403

        # Insert message
        cursor.execute(
            'INSERT INTO messages (from_user_id, to_user_id, subject, message) VALUES (%s, %s, %s, %s)',
            (from_user_id, recipient['id'], subject, message)
        )
        inserted_id = cursor.lastrowid
        print(f"Inserted message id={inserted_id} from={from_user_id} to={recipient['id']}")
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Sent!'}), 200
    except Exception as e:
        print(f"Error in send_message by {session.get('username')}: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return jsonify({'success': False, 'message': f'Error sending message: {str(e)}'}), 500

@app.route('/api/inbox/mark-read/<int:message_id>', methods=['POST'])
@login_required
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        user_id = session.get('user_id')
        print(f"User {session.get('username')} ({user_id}) marking message {message_id} as read")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if message belongs to this user
        cursor.execute(
            'SELECT id FROM messages WHERE id = %s AND to_user_id = %s',
            (message_id, user_id)
        )
        message = cursor.fetchone()
        
        if not message:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
        
        # Mark as read
        cursor.execute(
            'UPDATE messages SET is_read = 1 WHERE id = %s AND to_user_id = %s',
            (message_id, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error marking message: {str(e)}'
        }), 500

@app.route('/api/inbox/delete/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    try:
        user_id = session.get('user_id')
        print(f"User {session.get('username')} ({user_id}) deleting message {message_id}")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if message belongs to this user
        cursor.execute(
            'SELECT id FROM messages WHERE id = %s AND to_user_id = %s',
            (message_id, user_id)
        )
        message = cursor.fetchone()
        
        if not message:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
        
        # Delete message (ensure only owner can delete)
        cursor.execute('DELETE FROM messages WHERE id = %s AND to_user_id = %s', (message_id, user_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Message deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting message: {str(e)}'
        }), 500

@app.route('/api/users/list', methods=['GET'])
@login_required
def get_users_list():
    """Get list of users that current user can send messages to (hierarchy-based)"""
    try:
        user_role = session.get('role')
        user_id = session.get('user_id')
        print(f"User {session.get('username')} ({session.get('user_id')}) requesting users list for messaging")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all descendant user IDs (subordinates)
        descendant_ids = get_descendant_user_ids(user_id)
        # Remove self from descendants
        subordinate_ids = [uid for uid in descendant_ids if uid != user_id]
        
        # Get ancestors (created_by chain going up)
        ancestor_ids = []
        cursor.execute('SELECT created_by FROM users WHERE id = %s', (user_id,))
        row = cursor.fetchone()
        if row and row['created_by']:
            current_ancestor_id = row['created_by']
            while current_ancestor_id:
                ancestor_ids.append(current_ancestor_id)
                cursor.execute('SELECT created_by FROM users WHERE id = %s', (current_ancestor_id,))
                row = cursor.fetchone()
                if row and row['created_by']:
                    current_ancestor_id = row['created_by']
                else:
                    break
        
        # Combine ancestors and subordinates
        allowed_user_ids = list(set(ancestor_ids + subordinate_ids))
        
        if not allowed_user_ids:
            conn.close()
            return jsonify({'success': True, 'users': []}), 200
        
        # Fetch user details
        placeholders = ','.join(['%s'] * len(allowed_user_ids))
        cursor.execute(
            f'SELECT id, username, role, mac_address FROM users WHERE id IN ({placeholders}) ORDER BY username ASC',
            tuple(allowed_user_ids)
        )
        rows = cursor.fetchall()
        conn.close()

        users_list = []
        for r in rows:
            users_list.append({
                'id': r['id'],
                'username': r['username'],
                'role': r['role'],
                'mac_address': r['mac_address'] if 'mac_address' in r.keys() else None
            })

        return jsonify({'success': True, 'users': users_list}), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching users: {str(e)}'
        }), 500

# Endpoint: Get users by role (used by master dashboard to list super sellers)
@app.route('/api/users/by-role', methods=['GET'])
@login_required
def get_users_by_role():
    """Return list of users for a given role within current user's hierarchy.

    Master can see all admins/super_sellers/sellers in their hierarchy.
    Admin can see all super_sellers/sellers in their hierarchy.
    Super_seller can see all sellers in their hierarchy.
    """
    try:
        requested_role = request.args.get('role', '').strip()
        if not requested_role:
            return jsonify({'success': False, 'message': 'Missing role parameter'}), 400

        current_role = session.get('role')
        current_user_id = session.get('user_id')

        # Permission check
        allowed = False
        if current_role in ('super_master', 'master', 'admin'):
            allowed = True
        elif current_role == 'super_seller' and requested_role == 'seller':
            allowed = True

        if not allowed:
            return jsonify({'success': False, 'message': 'Unauthorized to view requested role'}), 403

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        user_ids = []
        
        if current_role == 'super_master':
            if requested_role == 'master':
                # Masters directly created by super_master
                cursor.execute('SELECT id, username, password, role, created_at FROM users WHERE role = %s AND created_by = %s ORDER BY id ASC', ('master', current_user_id))
            else:
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
                
        elif current_role == 'master':
            if requested_role == 'admin':
                # Admins directly created by master
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE role = %s AND created_by = %s ORDER BY id ASC', ('admin', current_user_id))
            elif requested_role == 'super_seller':
                # Super sellers created by admins (who were created by this master)
                cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('admin', current_user_id))
                admin_ids = [r['id'] for r in cursor.fetchall()]
                if admin_ids:
                    placeholders = ','.join(['%s'] * len(admin_ids))
                    cursor.execute(f'SELECT id, username, role, created_at FROM users WHERE role = %s AND created_by IN ({placeholders}) ORDER BY id ASC', ('super_seller', *admin_ids))
                else:
                    cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
            elif requested_role == 'seller':
                # Sellers created by super_sellers (who were created by admins, who were created by this master)
                cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('admin', current_user_id))
                admin_ids = [r['id'] for r in cursor.fetchall()]
                super_seller_ids = []
                if admin_ids:
                    placeholders = ','.join(['%s'] * len(admin_ids))
                    cursor.execute(f'SELECT id FROM users WHERE role = %s AND created_by IN ({placeholders})', ('super_seller', *admin_ids))
                    super_seller_ids = [r['id'] for r in cursor.fetchall()]
                if super_seller_ids:
                    placeholders = ','.join(['%s'] * len(super_seller_ids))
                    cursor.execute(f'SELECT id, username, role, created_at FROM users WHERE role = %s AND created_by IN ({placeholders}) ORDER BY id ASC', ('seller', *super_seller_ids))
                else:
                    cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
            else:
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
                
        elif current_role == 'admin':
            if requested_role == 'super_seller':
                # Super sellers directly created by this admin
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE role = %s AND created_by = %s ORDER BY id ASC', ('super_seller', current_user_id))
            elif requested_role == 'seller':
                # Sellers created by super_sellers (who were created by this admin)
                cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('super_seller', current_user_id))
                super_seller_ids = [r['id'] for r in cursor.fetchall()]
                if super_seller_ids:
                    placeholders = ','.join(['%s'] * len(super_seller_ids))
                    cursor.execute(f'SELECT id, username, role, created_at FROM users WHERE role = %s AND created_by IN ({placeholders}) ORDER BY id ASC', ('seller', *super_seller_ids))
                else:
                    cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
            else:
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
                
        elif current_role == 'super_seller':
            if requested_role == 'seller':
                # Sellers directly created by this super_seller
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE role = %s AND created_by = %s ORDER BY id ASC', ('seller', current_user_id))
            else:
                cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result
        else:
            cursor.execute('SELECT id, username, role, created_at FROM users WHERE 1=0')  # Empty result

        rows = cursor.fetchall()
        conn.close()

        users = []
        for r in rows:
            users.append({
                'id': r['id'],
                'username': r['username'],
                'password': r.get('password', ''),
                'role': r['role'],
                'created_at': str(r['created_at']) if r['created_at'] else None
            })

        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        # Log the exception server-side if needed and return generic error to client
        print('Error in get_users_by_role:', e)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Server error while fetching users'}), 500

# ==================== NEWS ROUTES ====================

@app.route('/api/news/list', methods=['GET'])
@login_required
def get_news_list():
    """Get all news for logged-in user's role"""
    try:
        user_id = session.get('user_id')
        user_role = session.get('role')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all news targeted to user's role or 'all'
        cursor.execute('''
            SELECT 
                n.id,
                n.title,
                n.content,
                n.target_role,
                n.created_at,
                n.updated_at,
                u.username as author_username,
                u.role as author_role,
                CASE WHEN nr.news_id IS NOT NULL THEN 1 ELSE 0 END as is_read
            FROM news n
            JOIN users u ON n.author_id = u.id
            LEFT JOIN news_read nr ON n.id = nr.news_id AND nr.user_id = %s
            WHERE n.is_active = 1 AND (n.target_role = %s OR n.target_role = 'all')
            ORDER BY n.created_at DESC
        ''', (user_id, user_role))
        news_items = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dicts
        news_list = []
        unread_count = 0
        for item in news_items:
            news_dict = {
                'id': item['id'],
                'title': item['title'],
                'content': item['content'],
                'target_role': item['target_role'],
                'author_username': item['author_username'],
                'author_role': item['author_role'],
                'is_read': bool(item['is_read']),
                'created_at': str(item['created_at']) if item['created_at'] else None,
                'updated_at': str(item['updated_at']) if item['updated_at'] else None
            }
            news_list.append(news_dict)
            if not item['is_read']:
                unread_count += 1
        
        return jsonify({
            'success': True,
            'news': news_list,
            'total': len(news_list),
            'unread': unread_count
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading news: {str(e)}'
        }), 500

@app.route('/api/news/create', methods=['POST'])
@login_required
def create_news():
    """Create a new news item
    
    When a new news is created for a target_role, all previous news for that same target_role are deleted.
    This ensures only the latest news exists for each role.
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        target_role = data.get('target_role', '').strip()
        
        if not title or not content or not target_role:
            return jsonify({
                'success': False,
                'message': 'Title, content, and target role are required'
            }), 400
        
        author_id = session.get('user_id')
        author_role = session.get('role')
        
        # Check if author has permission to post news for target role
        allowed = False
        if author_role == 'master':
            # Master can post for admin, super_seller, seller, or all
            if target_role in ['admin', 'super_seller', 'seller', 'all']:
                allowed = True
        elif author_role == 'admin':
            # Admin can post for super_seller, seller, or all
            if target_role in ['super_seller', 'seller', 'all']:
                allowed = True
        elif author_role == 'super_seller':
            # Super seller can post for seller only
            if target_role == 'seller':
                allowed = True
        
        if not allowed:
            return jsonify({
                'success': False,
                'message': f'You do not have permission to post news for {target_role}'
            }), 403
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # **AUTO-DELETE**: Delete all previous news for this target_role
        # This includes deleting from news_read table first (foreign key constraint)
        cursor.execute('SELECT id FROM news WHERE target_role = %s', (target_role,))
        old_news_ids = [row['id'] for row in cursor.fetchall()]
        
        if old_news_ids:
            placeholders = ','.join(['%s'] * len(old_news_ids))
            # Delete from news_read first
            cursor.execute(f'DELETE FROM news_read WHERE news_id IN ({placeholders})', tuple(old_news_ids))
            # Delete from news
            cursor.execute(f'DELETE FROM news WHERE id IN ({placeholders})', tuple(old_news_ids))
            conn.commit()
        
        # Insert new news
        cursor.execute('''
            INSERT INTO news (author_id, title, content, target_role)
            VALUES (%s, %s, %s, %s)
        ''', (author_id, title, content, target_role))
        
        news_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'News posted successfully (previous news deleted)',
            'news_id': news_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating news: {str(e)}'
        }), 500

@app.route('/api/news/mark-read/<int:news_id>', methods=['POST'])
@login_required
def mark_news_read(news_id):
    """Mark a news item as read for current user"""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if news exists and user can access it
        cursor.execute(
            'SELECT id, target_role FROM news WHERE id = %s AND is_active = 1',
            (news_id,)
        )
        news = cursor.fetchone()
        
        if not news:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'News not found'
            }), 404
        
        user_role = session.get('role')
        if news['target_role'] not in [user_role, 'all']:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Insert or ignore (if already read)
        cursor.execute('''
            INSERT IGNORE INTO news_read (news_id, user_id)
            VALUES (%s, %s)
        ''', (news_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'News marked as read'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error marking news as read: {str(e)}'
        }), 500

@app.route('/api/news/delete/<int:news_id>', methods=['DELETE'])
@login_required
def delete_news(news_id):
    """Delete a news item (soft delete)"""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if news belongs to this user
        cursor.execute(
            'SELECT id FROM news WHERE id = %s AND author_id = %s',
            (news_id, user_id)
        )
        news = cursor.fetchone()
        
        if not news:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'News not found or you do not have permission to delete it'
            }), 404
        
        # Soft delete (set is_active to 0)
        cursor.execute(
            'UPDATE news SET is_active = 0 WHERE id = %s',
            (news_id,)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'News deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting news: {str(e)}'
        }), 500

@app.route('/api/news/update/<int:news_id>', methods=['PUT'])
@login_required
def update_news(news_id):
    """Update a news item"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title or not content:
            return jsonify({
                'success': False,
                'message': 'Title and content are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if news belongs to this user
        cursor.execute(
            'SELECT id FROM news WHERE id = %s AND author_id = %s',
            (news_id, user_id)
        )
        news = cursor.fetchone()
        
        if not news:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'News not found or you do not have permission to edit it'
            }), 404
        
        # Update news
        cursor.execute('''
            UPDATE news 
            SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (title, content, news_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'News updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating news: {str(e)}'
        }), 500

@app.route('/api/news/target-roles', methods=['GET'])
@login_required
def get_target_roles():
    """Get list of roles current user can post news for"""
    try:
        user_role = session.get('role')
        
        roles = []
        if user_role == 'master':
            roles = [
                {'value': 'admin', 'label': 'Admin'},
                {'value': 'super_seller', 'label': 'Super Seller'},
                {'value': 'seller', 'label': 'Seller'},
                {'value': 'all', 'label': 'All Roles'}
            ]
        elif user_role == 'admin':
            roles = [
                {'value': 'super_seller', 'label': 'Super Seller'},
                {'value': 'seller', 'label': 'Seller'},
                {'value': 'all', 'label': 'All Roles'}
            ]
        elif user_role == 'super_seller':
            roles = [
                {'value': 'seller', 'label': 'Seller'}
            ]
        
        return jsonify({
            'success': True,
            'roles': roles
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching target roles: {str(e)}'
        }), 500


# ==================== USER SEARCH FOR INBOX ====================

# Search user by userid, MAC address, or Secret Key
@app.route('/api/inbox/user-search', methods=['GET'])
@login_required
def inbox_user_search():
    """Search for a user by user ID, MAC address, or Secret Key to send inbox message"""
    query = request.args.get('query', '').strip()
    search_type = request.args.get('type', '').strip()  # 'userid', 'mac', 'secret_key'
    
    if not query or not search_type:
        return jsonify({'success': False, 'error': 'Missing search query or type.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user_row = None
    
    try:
        if search_type == 'userid':
            # Search by username (user ID)
            cursor.execute('SELECT id, username, role, mac_address FROM users WHERE username = %s', (query,))
            user_row = cursor.fetchone()
            
        elif search_type == 'mac':
            # Search by MAC address
            cursor.execute('SELECT id, username, role, mac_address FROM users WHERE mac_address = %s', (query,))
            user_row = cursor.fetchone()
            
        elif search_type == 'secret_key':
            # Find the seller who created this key by searching key_code
            cursor.execute('''
                SELECT u.id, u.username, u.role, u.mac_address
                FROM `keys` k
                JOIN users u ON k.created_by = u.id
                WHERE k.key_code = %s
            ''', (query,))
            user_row = cursor.fetchone()
            
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid search type. Use: userid, mac, or secret_key'}), 400

        if not user_row:
            conn.close()
            return jsonify({'success': False, 'error': f'No user found with this {search_type}.'}), 404

        user_info = {
            'id': user_row['id'],
            'username': user_row['username'],
            'role': user_row['role'],
            'mac_address': user_row.get('mac_address') or 'Not set'
        }
        conn.close()
        return jsonify({'success': True, 'user': user_info})
        
    except Exception as e:
        print(f"Error in user search: {e}")
        conn.close()
        return jsonify({'success': False, 'error': 'Server error during search'}), 500

# ==================== USER MANAGEMENT ROUTES ====================

@app.route('/api/users/create', methods=['POST'])
@login_required
def create_user():
    """Create a new user (role-based permissions)"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', '').strip()
        
        # Validate inputs
        if not username or not password or not role:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check permissions based on current user role
        current_role = session.get('role')
        role_permissions = {
            'super_master': ['master', 'admin', 'super_seller', 'seller'],
            'master': ['admin'],
            'admin': ['super_seller'],
            'super_seller': ['seller']
        }
        
        allowed_roles = role_permissions.get(current_role, [])
        if role not in allowed_roles:
            return jsonify({'success': False, 'message': f'You can only create {", ".join(allowed_roles)} accounts'}), 403
        
        # Check username length
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
        
        # Check password length
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if username already exists
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new user and set created_by to current user id (for hierarchical ownership)
        created_by = session.get('user_id')
        cursor.execute(
            'INSERT INTO users (username, password, role, created_by) VALUES (%s, %s, %s, %s)',
            (username, hashed_password, role, created_by)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{role.replace("_", " ").title()} account created successfully',
            'user': {
                'id': user_id,
                'username': username,
                'role': role
            }
        }), 201
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/users/list-managed', methods=['GET'])
@login_required
def get_managed_users():
    """Get list of users that current user can manage (only direct children)"""
    try:
        current_user_id = session.get('user_id')
        current_role = session.get('role')
        
        # Define which roles each role can manage
        role_permissions = {
            'super_master': ['master'],
            'master': ['admin'],
            'admin': ['super_seller'],
            'super_seller': ['seller']
        }
        
        managed_roles = role_permissions.get(current_role, [])
        
        if not managed_roles:
            return jsonify({'success': True, 'users': []}), 200
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get users created by current user only
        placeholders = ','.join(['%s'] * len(managed_roles))
        cursor.execute(
            f'SELECT id, username, role, created_at FROM users WHERE role IN ({placeholders}) AND created_by = %s ORDER BY created_at DESC',
            (*managed_roles, current_user_id)
        )
        
        users = []
        rows = cursor.fetchall()
        for row in rows:
            users.append({
                'id': row['id'],
                'username': row['username'],
                'role': row['role'],
                'created_at': str(row['created_at']) if row['created_at'] else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users,
            'managed_roles': managed_roles
        }), 200
        
    except Exception as e:
        print(f"Error fetching managed users: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete a user (only if current user has permission)"""
    try:
        current_role = session.get('role')
        current_user_id = session.get('user_id')
        
        # Cannot delete yourself
        if user_id == current_user_id:
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and get their role
        cursor.execute('SELECT role, username FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_role = user['role']
        username = user['username']
        
        # Check permissions
        role_permissions = {
            'super_master': ['master', 'admin', 'super_seller', 'seller'],
            'master': ['admin'],
            'admin': ['super_seller'],
            'super_seller': ['seller']
        }
        
        allowed_roles = role_permissions.get(current_role, [])
        if user_role not in allowed_roles:
            conn.close()
            return jsonify({'success': False, 'message': 'You do not have permission to delete this user'}), 403
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/users/update-password/<int:user_id>', methods=['PUT'])
@login_required
def update_user_password(user_id):
    """Update user password (only if current user has permission)"""
    try:
        data = request.get_json()
        new_password = data.get('password', '').strip()
        
        if not new_password:
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        current_role = session.get('role')
        current_user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and get their role
        cursor.execute('SELECT role, username FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_role = user['role']
        username = user['username']
        
        # Allow updating own password or subordinate users
        if user_id != current_user_id:
            role_permissions = {
                'super_master': ['master', 'admin', 'super_seller', 'seller'],
                'master': ['admin'],
                'admin': ['super_seller'],
                'super_seller': ['seller']
            }
            
            allowed_roles = role_permissions.get(current_role, [])
            if user_role not in allowed_roles:
                conn.close()
                return jsonify({'success': False, 'message': 'You do not have permission to update this user'}), 403
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Password for {username} updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error updating password: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/users/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get statistics about managed users"""
    try:
        current_role = session.get('role')
        current_user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # initialize
        stats = {'admin': 0, 'super_seller': 0, 'seller': 0, 'total': 0}

        if current_role == 'master':
            # admins directly under this master
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = %s AND created_by = %s', ('admin', current_user_id))
            stats['admin'] = cursor.fetchone()['count']

            # super_sellers under those admins
            cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('admin', current_user_id))
            admin_rows = [r['id'] for r in cursor.fetchall()]
            if admin_rows:
                placeholders = ','.join(['%s'] * len(admin_rows))
                cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE role = 'super_seller' AND created_by IN ({placeholders})", tuple(admin_rows))
                stats['super_seller'] = cursor.fetchone()['count']
                # sellers under those super_sellers
                # first get super_seller ids under these admins
                cursor.execute(f"SELECT id FROM users WHERE role = 'super_seller' AND created_by IN ({placeholders})", tuple(admin_rows))
                super_rows = [r['id'] for r in cursor.fetchall()]
                if super_rows:
                    placeholders2 = ','.join(['%s'] * len(super_rows))
                    cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE role = 'seller' AND created_by IN ({placeholders2})", tuple(super_rows))
                    stats['seller'] = cursor.fetchone()['count']

        elif current_role == 'admin':
            # super_sellers directly under this admin
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = %s AND created_by = %s', ('super_seller', current_user_id))
            stats['super_seller'] = cursor.fetchone()['count']
            # sellers under those super_sellers
            cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('super_seller', current_user_id))
            super_rows = [r['id'] for r in cursor.fetchall()]
            if super_rows:
                placeholders = ','.join(['%s'] * len(super_rows))
                cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE role = 'seller' AND created_by IN ({placeholders})", tuple(super_rows))
                stats['seller'] = cursor.fetchone()['count']

        elif current_role == 'super_seller':
            # sellers directly under this super_seller
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = %s AND created_by = %s', ('seller', current_user_id))
            stats['seller'] = cursor.fetchone()['count']

        # total = sum of counts
        stats['total'] = (stats.get('admin', 0) or 0) + (stats.get('super_seller', 0) or 0) + (stats.get('seller', 0) or 0)

        # --- Key sales calculations ---
        # today's date in MySQL: CURDATE()
        today_expr = "CURDATE()"

        # helper to count keys by seller ids
        def count_keys_for_sellers(seller_ids):
            if not seller_ids:
                return (0, 0)
            placeholders = ','.join(['%s'] * len(seller_ids))
            # total paid & active
            cursor.execute(f"SELECT COUNT(*) as count FROM `keys` WHERE is_paid = 1 AND is_active = 1 AND created_by IN ({placeholders})", tuple(seller_ids))
            total = cursor.fetchone()['count']
            # today
            cursor.execute(f"SELECT COUNT(*) as count FROM `keys` WHERE is_paid = 1 AND is_active = 1 AND DATE(created_at) = {today_expr} AND created_by IN ({placeholders})", tuple(seller_ids))
            today = cursor.fetchone()['count']
            return (today, total)

        todays_sale = 0
        total_sale = 0

        if current_role == 'master':
            # admin_rows and super_rows were computed above; recompute seller ids under those super_sellers
            seller_ids = []
            if admin_rows:
                # get super_seller ids under these admins
                # admin_rows variable exists earlier; ensure it's in scope
                try:
                    # reuse admin_rows list
                    if admin_rows:
                        placeholders = ','.join(['%s'] * len(admin_rows))
                        cursor.execute(f"SELECT id FROM users WHERE role = 'super_seller' AND created_by IN ({placeholders})", tuple(admin_rows))
                        supers = [r['id'] for r in cursor.fetchall()]
                        if supers:
                            placeholders2 = ','.join(['%s'] * len(supers))
                            cursor.execute(f"SELECT id FROM users WHERE role = 'seller' AND created_by IN ({placeholders2})", tuple(supers))
                            seller_ids = [r['id'] for r in cursor.fetchall()]
                except Exception:
                    seller_ids = []
            (tod, tot) = count_keys_for_sellers(seller_ids)
            todays_sale = tod
            total_sale = tot

        elif current_role == 'admin':
            # get super_seller ids under this admin
            cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('super_seller', current_user_id))
            supers = [r['id'] for r in cursor.fetchall()]
            seller_ids = []
            if supers:
                placeholders = ','.join(['%s'] * len(supers))
                cursor.execute(f"SELECT id FROM users WHERE role = 'seller' AND created_by IN ({placeholders})", tuple(supers))
                seller_ids = [r['id'] for r in cursor.fetchall()]
            (tod, tot) = count_keys_for_sellers(seller_ids)
            todays_sale = tod
            total_sale = tot

        elif current_role == 'super_seller':
            # sellers directly under this super_seller
            cursor.execute('SELECT id FROM users WHERE role = %s AND created_by = %s', ('seller', current_user_id))
            seller_ids = [r['id'] for r in cursor.fetchall()]
            (tod, tot) = count_keys_for_sellers(seller_ids)
            todays_sale = tod
            total_sale = tot

        else:
            # other roles - default 0
            todays_sale = 0
            total_sale = 0

        stats['todays_sale'] = todays_sale
        stats['total_sale'] = total_sale

        conn.close()

        return jsonify({'success': True, 'stats': stats}), 200
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

# ==================== KEY MANAGEMENT ROUTES ====================

@app.route('/api/keys/set-active/<int:key_id>', methods=['PUT'])
@login_required
@role_required(('super_seller', 'admin', 'master'))
def set_key_active_status(key_id):
    """Super Seller: Set key active/inactive (block/unblock)"""
    try:
        data = request.get_json()
        is_active = data.get('is_active')
        if is_active not in [0, 1, True, False]:
            return jsonify({'success': False, 'message': 'Invalid active status'}), 400

        current_user_id = session.get('user_id')
        current_role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Check if key exists and get seller info
        cursor.execute('''
            SELECT k.id, k.created_by, u.created_by as seller_created_by, u.role as creator_role
            FROM `keys` k
            JOIN users u ON k.created_by = u.id
            WHERE k.id = %s
        ''', (key_id,))
        key = cursor.fetchone()
        if not key:
            conn.close()
            return jsonify({'success': False, 'message': 'Key not found'}), 404

        # Permission check:
        # Super_seller can only block/unblock keys from sellers they created
        if current_role == 'super_seller':
            if key['seller_created_by'] != current_user_id:
                conn.close()
                return jsonify({'success': False, 'message': 'You can only manage keys from sellers you created'}), 403
        # Admin/Master can manage any key (already checked by role_required decorator)

        if is_active:
            # Unblock: set is_active=1 and active_until = today+30 days
            from datetime import date, timedelta
            new_active_until = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute('UPDATE `keys` SET is_active = 1, active_until = %s WHERE id = %s', (new_active_until, key_id))
        else:
            # Block: set is_active=0 and active_until = NULL
            cursor.execute('UPDATE `keys` SET is_active = 0, active_until = NULL WHERE id = %s', (key_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Key status updated', 'is_active': bool(is_active)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/keys/create', methods=['POST'])
@login_required
@role_required('seller')
def create_key():
    """Create a new key"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        current_user_id = session.get('user_id')
        current_role = session.get('role')
        
        # Validate input
        if not name:
            return jsonify({'success': False, 'message': 'Key name is required'}), 400
        
        if len(name) < 3:
            return jsonify({'success': False, 'message': 'Key name must be at least 3 characters'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if key_code (name) already exists globally (for any user)
        cursor.execute('SELECT id, created_by FROM `keys` WHERE key_code = %s', (name,))
        existing_key = cursor.fetchone()
        if existing_key:
            conn.close()
            return jsonify({'success': False, 'message': 'This key name is already taken by another user. Please choose a different name.'}), 400
        
        # Use the name as key_code
        key_code = name
        
        # Auto-generate a random password (8 characters) - still needed for password_hash field
        import string
        auto_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        # Hash password
        password_hash = bcrypt.hashpw(auto_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Only sellers may create keys. Newly created keys are unpaid and inactive by default.
        is_paid = 0
        is_active = 0
        active_until = None
        
        # Insert key
        cursor.execute('''
            INSERT INTO `keys` (name, key_code, password_hash, created_by, is_paid, is_active, active_until)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (name, key_code, password_hash, current_user_id, is_paid, is_active, active_until))
        
        key_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Key created successfully. Your Secret Key is: ' + key_code,
            'key': {
                'id': key_id,
                'name': name,
                'key_code': key_code,
                'is_paid': bool(is_paid),
                'is_active': bool(is_active),
                'active_until': active_until,
                'status': 'Inactive',
                'paid': False,
                'mac': 'unknown',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201
        
    except Exception as e:
        print(f"Error creating key: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/list', methods=['GET'])
@login_required
def get_keys_list():
    """Get list of keys based on user role and hierarchy"""
    try:
        current_user_id = session.get('user_id')
        current_role = session.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all descendant user IDs (users created by this user and their descendants)
        descendant_ids = get_descendant_user_ids(current_user_id)
        
        # Seller can only see own keys
        if current_role == 'seller':
            cursor.execute('''
                SELECT k.*, u.username, u.role as creator_role, u.created_by as seller_created_by,
                       ka.ip_address, ka.last_access
                FROM `keys` k
                JOIN users u ON k.created_by = u.id
                LEFT JOIN key_access ka ON k.id = ka.key_id
                WHERE k.created_by = %s
                ORDER BY k.created_at DESC
            ''', (current_user_id,))
        else:
            # Higher roles: show keys from all descendant users (excluding self)
            # Remove current_user_id from the list as we only want subordinates' keys
            subordinate_ids = [uid for uid in descendant_ids if uid != current_user_id]
            
            if not subordinate_ids:
                # No subordinates, return empty list
                conn.close()
                return jsonify({
                    'success': True,
                    'keys': [],
                    'current_user_id': current_user_id,
                    'current_role': current_role,
                    'can_manage_paid': current_role == 'super_seller'
                }), 200
            
            placeholders = ','.join(['%s'] * len(subordinate_ids))
            query = f'''
                SELECT k.*, u.username, u.role as creator_role, u.created_by as seller_created_by,
                       ka.ip_address, ka.last_access
                FROM `keys` k
                JOIN users u ON k.created_by = u.id
                LEFT JOIN key_access ka ON k.id = ka.key_id
                WHERE k.created_by IN ({placeholders})
                ORDER BY k.created_at DESC
            '''
            cursor.execute(query, tuple(subordinate_ids))
        
        keys = []
        current_date = date.today()
        
        rows = cursor.fetchall()
        for row in rows:
            key_data = {
                'id': row['id'],
                'name': row['name'],
                'key_code': row['key_code'],
                'created_by': row['created_by'],
                'seller_created_by': row.get('seller_created_by'),
                'creator_username': row['username'],
                'creator_role': row['creator_role'],
                'created_at': str(row['created_at']) if row.get('created_at') else None,
                'is_paid': bool(row['is_paid']),
                'is_blocked': bool(row.get('is_blocked', 0)),
                'ip_address': row.get('ip_address'),
                'last_access': str(row['last_access']) if row.get('last_access') else None,
                'mac_address': row.get('mac_address'),
                # Backwards-compatible alias for frontend: some UI expects `mac`
                'mac': row.get('mac_address') or 'unknown'
            }
            
            # Calculate active status and days remaining with auto-expiry
            if row.get('active_until'):
                active_until_val = row['active_until']
                if isinstance(active_until_val, str):
                    active_until_date = datetime.strptime(active_until_val, '%Y-%m-%d').date()
                else:
                    active_until_date = active_until_val
                days_remaining = (active_until_date - current_date).days
                key_data['active_until'] = str(active_until_date)
                key_data['days_remaining'] = max(0, days_remaining)
                
                # Auto-expire: If expired, update DB
                if days_remaining <= 0 and row['is_active']:
                    cursor.execute('UPDATE `keys` SET is_active = 0 WHERE id = %s', (row['id'],))
                    key_data['is_active'] = False
                else:
                    key_data['is_active'] = days_remaining > 0
            else:
                key_data['active_until'] = None
                key_data['days_remaining'] = 0
                key_data['is_active'] = False
            
            keys.append(key_data)
        
        # Commit any auto-expiry updates
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'keys': keys,
            'current_user_id': current_user_id,
            'current_role': current_role,
            # Only super_seller may manage (activate/deactivate) paid status per policy
            'can_manage_paid': current_role == 'super_seller'
        }), 200
        
    except Exception as e:
        print(f"Error fetching keys: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/update-paid/<int:key_id>', methods=['PUT'])
@login_required
def update_key_paid_status(key_id):
    """Update paid status and active duration of a key"""
    try:
        data = request.get_json()
        is_paid = data.get('is_paid', False)
        duration_days = data.get('duration_days', 30)  # Default 30 days, can be customized
        extend_mode = data.get('extend', False)  # If True, add days to existing date instead of replacing
        current_role = session.get('role')
        
        # Validate duration
        if duration_days not in [7, 15, 30, 60, 90]:
            duration_days = 30  # Fallback to default
        
        # Only super_seller can activate/deactivate keys
        if current_role != 'super_seller':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        current_user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get key details and seller info
        cursor.execute('''
            SELECT k.*, u.role as creator_role, u.created_by as seller_created_by
            FROM `keys` k
            JOIN users u ON k.created_by = u.id
            WHERE k.id = %s
        ''', (key_id,))
        
        key = cursor.fetchone()
        if not key:
            conn.close()
            return jsonify({'success': False, 'message': 'Key not found'}), 404
        
        # Super_seller can only manage keys from sellers they created
        if key['seller_created_by'] != current_user_id:
            conn.close()
            return jsonify({'success': False, 'message': 'You can only manage keys from sellers you created'}), 403
        
        # Update paid status
        if is_paid:
            # Calculate new active_until date
            if extend_mode and key.get('active_until'):
                # Extend mode: Add days to existing expiry date
                try:
                    existing_val = key['active_until']
                    if isinstance(existing_val, str):
                        existing_date = datetime.strptime(existing_val, '%Y-%m-%d').date()
                    else:
                        existing_date = existing_val
                    # If already expired, start from today
                    if existing_date < date.today():
                        active_until = (date.today() + timedelta(days=duration_days)).isoformat()
                    else:
                        # Add to existing date
                        active_until = (existing_date + timedelta(days=duration_days)).isoformat()
                except:
                    # If parsing fails, start from today
                    active_until = (date.today() + timedelta(days=duration_days)).isoformat()
            else:
                # Replace mode: Set new expiry from today
                active_until = (date.today() + timedelta(days=duration_days)).isoformat()
            
            cursor.execute('''
                UPDATE `keys`
                SET is_paid = 1, active_until = %s, is_active = 1
                WHERE id = %s
            ''', (active_until, key_id))
            
            message = f'Key validity {"extended by" if extend_mode else "activated for"} {duration_days} days successfully'
        else:
            # Remove active status
            cursor.execute('''
                UPDATE `keys`
                SET is_paid = 0, active_until = NULL, is_active = 0
                WHERE id = %s
            ''', (key_id,))
            message = 'Key deactivated successfully'
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        print(f"Error updating paid status: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/reset-device/<int:key_id>', methods=['POST'])
@login_required
def reset_key_device(key_id):
    """Reset IP address for a key to allow new device"""
    try:
        current_user_id = session.get('user_id')
        current_role = session.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get key details and seller info
        cursor.execute('''
            SELECT k.*, u.role as creator_role, u.created_by as seller_created_by
            FROM `keys` k
            JOIN users u ON k.created_by = u.id
            WHERE k.id = %s
        ''', (key_id,))
        
        key = cursor.fetchone()
        if not key:
            conn.close()
            return jsonify({'success': False, 'message': 'Key not found'}), 404
        
        # Permission checks:
        # 1. Seller can reset only their own keys
        # 2. Super_seller cannot reset (only sellers can reset)
        # 3. Admin/Master can reset any key
        
        if current_role == 'seller':
            # Seller can only reset their own keys
            if key['created_by'] != current_user_id:
                conn.close()
                return jsonify({'success': False, 'message': 'You can only reset your own keys'}), 403
        elif current_role == 'super_seller':
            # Super_seller cannot reset keys (only sellers can)
            conn.close()
            return jsonify({'success': False, 'message': 'Only sellers can reset their own keys'}), 403
        elif current_role in ['admin', 'master']:
            # Admin/Master can reset any key
            pass
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
        
        # Delete entire device access record
        cursor.execute('DELETE FROM key_access WHERE key_id = %s', (key_id,))
        # Clear bound MAC address as well so key can be used on new device
        try:
            cursor.execute('UPDATE `keys` SET mac_address = NULL WHERE id = %s', (key_id,))
        except Exception:
            pass
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Device reset successfully. Key can now be used on a new device.'
        }), 200
        
    except Exception as e:
        print(f"Error resetting device: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/delete/<int:key_id>', methods=['DELETE'])
@login_required
def delete_key(key_id):
    """Delete a key"""
    try:
        current_user_id = session.get('user_id')
        current_role = session.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get key details
        cursor.execute('''
            SELECT k.*, u.role as creator_role
            FROM `keys` k
            JOIN users u ON k.created_by = u.id
            WHERE k.id = %s
        ''', (key_id,))
        
        key = cursor.fetchone()
        if not key:
            conn.close()
            return jsonify({'success': False, 'message': 'Key not found'}), 404
        
        # Check if user owns this key or can manage it
        if key['created_by'] == current_user_id:
            # Owner can delete
            pass
        else:
            # Check hierarchy
            role_hierarchy = {
                'master': ['admin', 'super_seller', 'seller'],
                'admin': ['super_seller', 'seller'],
                'super_seller': ['seller']
            }
            manageable_roles = role_hierarchy.get(current_role, [])
            if key['creator_role'] not in manageable_roles:
                conn.close()
                return jsonify({'success': False, 'message': 'Cannot delete this key'}), 403
        
        # Delete key (cascade will delete key_access)
        cursor.execute('DELETE FROM `keys` WHERE id = %s', (key_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Key deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting key: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/toggle-block/<int:key_id>', methods=['PUT'])
@login_required
def toggle_block_key(key_id):
    """Block or unblock a key (sellers can only block their own keys)"""
    try:
        current_user_id = session.get('user_id')
        current_role = session.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get key details
        cursor.execute('''
            SELECT k.*, u.role as creator_role
            FROM `keys` k
            JOIN users u ON k.created_by = u.id
            WHERE k.id = %s
        ''', (key_id,))
        
        key = cursor.fetchone()
        if not key:
            conn.close()
            return jsonify({'success': False, 'message': 'Key not found'}), 404
        
        # Check if user owns this key or can manage it
        if key['created_by'] == current_user_id:
            # Owner can block/unblock
            pass
        else:
            # Check hierarchy
            role_hierarchy = {
                'master': ['admin', 'super_seller', 'seller'],
                'admin': ['super_seller', 'seller'],
                'super_seller': ['seller']
            }
            manageable_roles = role_hierarchy.get(current_role, [])
            if key['creator_role'] not in manageable_roles:
                conn.close()
                return jsonify({'success': False, 'message': 'Cannot manage this key'}), 403
        
        # Toggle blocked status
        current_blocked = bool(key.get('is_blocked', 0))
        new_blocked = 0 if current_blocked else 1
        
        cursor.execute('UPDATE `keys` SET is_blocked = %s WHERE id = %s', (new_blocked, key_id))
        conn.commit()
        conn.close()
        
        action = 'blocked' if new_blocked else 'unblocked'
        return jsonify({
            'success': True,
            'message': f'Key {action} successfully',
            'is_blocked': bool(new_blocked)
        }), 200
        
    except Exception as e:
        print(f"Error toggling block status: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/access', methods=['POST'])
def access_key():
    """
    Validate key access and enforce one device rule
    This endpoint is used when a key is being used/authenticated
    """
    try:
        data = request.get_json()
        key_code = data.get('key_code', '').strip()
        password = data.get('password', '').strip()
        
        if not key_code or not password:
            return jsonify({'success': False, 'message': 'Key code and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get key details
        cursor.execute('SELECT * FROM `keys` WHERE key_code = %s', (key_code,))
        key = cursor.fetchone()
        
        if not key:
            # Log failed attempt - invalid key
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid key code'}), 404
        
        # Get client info
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), key['password_hash'].encode('utf-8')):
            # Log failed attempt - wrong password
            cursor.execute('''
                INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message)
                VALUES (%s, %s, %s, %s, %s)
            ''', (key['id'], client_ip, user_agent, 'FAILED', 'Invalid password'))
            conn.commit()
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid password'}), 401
        
        # Check if key is active (paid and not expired)
        if not key['is_paid']:
            # Log failed attempt - not activated
            cursor.execute('''
                INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message)
                VALUES (%s, %s, %s, %s, %s)
            ''', (key['id'], client_ip, user_agent, 'FAILED', 'Key not activated'))
            conn.commit()
            conn.close()
            return jsonify({'success': False, 'message': 'Key is not activated. Contact administrator.'}), 403
        
        # Check expiry
        if key.get('active_until'):
            active_until_val = key['active_until']
            if isinstance(active_until_val, str):
                active_until_date = datetime.strptime(active_until_val, '%Y-%m-%d').date()
            else:
                active_until_date = active_until_val
            if active_until_date < date.today():
                # Update is_active to false
                cursor.execute('UPDATE `keys` SET is_active = 0 WHERE id = %s', (key['id'],))
                # Log failed attempt - expired
                cursor.execute('''
                    INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (key['id'], client_ip, user_agent, 'FAILED', 'Key expired'))
                conn.commit()
                conn.close()
                return jsonify({'success': False, 'message': 'Key has expired. Contact administrator.'}), 403
        
        # Check existing device access
        cursor.execute('SELECT * FROM key_access WHERE key_id = %s', (key['id'],))
        existing_access = cursor.fetchone()
        
        if existing_access:
            # Device already registered - check IP match
            if existing_access.get('ip_address') and existing_access['ip_address'] != client_ip:
                # Log failed attempt - device mismatch
                cursor.execute('''
                    INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (key['id'], client_ip, user_agent, 'BLOCKED', f'Device mismatch (registered: {existing_access["ip_address"]})'))
                conn.commit()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'Device mismatch! This key is bound to IP {existing_access["ip_address"]}. Use "Reset Device" to allow new device.',
                    'error_code': 'DEVICE_MISMATCH'
                }), 403
            
            # Update last access time
            cursor.execute('''
                UPDATE key_access
                SET last_access = CURRENT_TIMESTAMP
                WHERE key_id = %s
            ''', (key['id'],))
        else:
            # First time access - record device
            cursor.execute('''
                INSERT INTO key_access (key_id, ip_address, last_access)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            ''', (key['id'], client_ip))
        
        # Log successful access
        cursor.execute('''
            INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message)
            VALUES (%s, %s, %s, %s, %s)
        ''', (key['id'], client_ip, user_agent, 'SUCCESS', 'Access granted'))
        
        conn.commit()
        conn.close()
        
        # Calculate days remaining
        days_remaining = 0
        if key.get('active_until'):
            active_until_val = key['active_until']
            if isinstance(active_until_val, str):
                active_until_date = datetime.strptime(active_until_val, '%Y-%m-%d').date()
            else:
                active_until_date = active_until_val
            days_remaining = (active_until_date - date.today()).days
        
        return jsonify({
            'success': True,
            'message': 'Access granted',
            'key': {
                'id': key['id'],
                'name': key['name'],
                'days_remaining': days_remaining,
                'is_active': bool(key['is_active'])
            }
        }), 200
        
    except Exception as e:
        print(f"Error accessing key: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/keys/access-history/<int:key_id>', methods=['GET'])
@login_required
def get_key_access_history(key_id):
    """Get access history for a specific key"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get key to verify ownership/permission
        cursor.execute('''
            SELECT k.*, u.role as creator_role
            FROM `keys` k
            JOIN users u ON k.created_by = u.id
            WHERE k.id = %s
        ''', (key_id,))
        key = cursor.fetchone()
        
        if not key:
            conn.close()
            return jsonify({'success': False, 'message': 'Key not found'}), 404
        
        # Permission check (same as delete/reset)
        current_role = session.get('role')
        current_user_id = session.get('user_id')
        
        role_hierarchy = {
            'master': ['admin', 'super_seller', 'seller'],
            'admin': ['super_seller', 'seller'],
            'super_seller': ['seller'],
            'seller': []
        }
        
        # Check if user can view this key
        if current_role != 'seller':
            manageable_roles = role_hierarchy.get(current_role, [])
            if key['creator_role'] not in manageable_roles:
                conn.close()
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
        else:
            # Seller can only view own keys
            if key['created_by'] != current_user_id:
                conn.close()
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        # Get access history
        cursor.execute('''
            SELECT ip_address, user_agent, access_status, access_message, accessed_at
            FROM key_access_history
            WHERE key_id = %s
            ORDER BY accessed_at DESC
            LIMIT 100
        ''', (key_id,))
        
        history = []
        rows = cursor.fetchall()
        for row in rows:
            history.append({
                'ip_address': row['ip_address'],
                'user_agent': row['user_agent'],
                'status': row['access_status'],
                'message': row['access_message'],
                'accessed_at': str(row['accessed_at']) if row.get('accessed_at') else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'history': history,
            'total': len(history)
        }), 200
        
    except Exception as e:
        print(f"Error getting access history: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@app.route('/api/keys/verify', methods=['POST'])
def api_keys_verify():
    """Verify a key_code from the software (used by app_backend).

    Input JSON: {"key_code": "ABC123"}
    Success: 200 {"success": true, "key": {"id":..., "name":..., "days_remaining": 30, "is_active": true}}
    Error: 403/404 with {"success": false, "message": "..."}
    """
    data = request.get_json(silent=True) or {}
    key_code = data.get('key_code')
    mac_address = data.get('mac_address')

    if not key_code:
        return jsonify(success=False, message='Missing key_code'), 400

    # mac_address is required for device-binding policy
    if not mac_address:
        return jsonify(success=False, message='Missing mac_address'), 400

    # Normalize mac address format to uppercase colon-separated for consistent storage/comparison
    try:
        mac_address = str(mac_address).strip()
        mac_address = mac_address.upper()
        # Replace common separators with ':'
        mac_address = mac_address.replace('-', ':')
    except Exception:
        pass

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM `keys` WHERE key_code = %s', (key_code,))
        row = cur.fetchone()

        if not row:
            print(f"[verify] key not found for key_code={key_code}")
            return jsonify(success=False, message='Key not found'), 404

        row_map = dict(row)
        # Device binding logic:
        # - If mac_address column is NULL => bind this device (first successful login)
        # - If mac_address matches => allow
        # - If mismatch => deny
        existing_mac = row_map.get('mac_address')
        if existing_mac:
            existing_mac = str(existing_mac).strip().upper().replace('-', ':')

        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')

        # Check if key is blocked
        is_blocked = bool(row_map.get('is_blocked', 0))
        if is_blocked:
            print(f"[verify] key is blocked id={row_map.get('id')}")
            return jsonify(success=False, message='Key has been blocked'), 403

        # If key not paid/active/expired we'll reject before binding

        is_active = bool(row_map.get('is_active'))
        if not is_active:
            print(f"[verify] key not active id={row_map.get('id')}")
            return jsonify(success=False, message='Key is not active'), 403

        is_paid = bool(row_map.get('is_paid'))
        if not is_paid:
            print(f"[verify] key not paid id={row_map.get('id')}")
            return jsonify(success=False, message='Key is not paid'), 403

        active_until = row_map.get('active_until')
        days_remaining = None
        if active_until:
            try:
                expiry = None
                if isinstance(active_until, (int, float)):
                    expiry = datetime.fromtimestamp(active_until)
                elif isinstance(active_until, str):
                    expiry = datetime.fromisoformat(active_until)
                else:
                    # assume it's a date object
                    expiry = datetime.combine(active_until, datetime.min.time())
                now = datetime.utcnow()
                if expiry < now:
                    print(f"[verify] key expired id={row_map.get('id')} expiry={active_until}")
                    return jsonify(success=False, message='Key expired'), 403
                days_remaining = (expiry.date() - now.date()).days
            except Exception:
                days_remaining = None

        # Now handle device binding / verification
        key_id = row_map.get('id')
        if not existing_mac:
            # Bind this MAC to the key (first successful login)
            try:
                cur.execute('UPDATE `keys` SET mac_address = %s WHERE id = %s', (mac_address, key_id))
                conn.commit()
                print(f"[verify] bound mac {mac_address} to key id={key_id}")
                # log access
                cur.execute('''INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message) VALUES (%s, %s, %s, %s, %s)''', (key_id, client_ip, user_agent, 'SUCCESS', 'Bound device'))
                conn.commit()
            except Exception as e:
                print(f"[verify] failed to bind mac for key id={key_id}: {e}")
                return jsonify(success=False, message='Server error during device bind'), 500
        else:
            # If provided mac doesn't match the bound mac -> deny
            if existing_mac != mac_address:
                print(f"[verify] device mismatch for key id={key_id}: expected={existing_mac} got={mac_address}")
                try:
                    cur.execute('''INSERT INTO key_access_history (key_id, ip_address, user_agent, access_status, access_message) VALUES (%s, %s, %s, %s, %s)''', (key_id, client_ip, user_agent, 'FAILED', 'Device mismatch'))
                    conn.commit()
                except Exception:
                    pass
                return jsonify(success=False, message='Device mismatch'), 403

        result = {
            'success': True,
            'key': {
                'id': row_map.get('id'),
                'name': row_map.get('name'),
                'days_remaining': days_remaining,
                'is_active': is_active,
                'mac_address': mac_address if existing_mac is None else existing_mac,
                'expires_on': str(active_until) if active_until else None
            }
        }
        print(f"[verify] key verified id={row_map.get('id')} key_code={key_code}")
        return jsonify(result), 200

    except Exception as e:
        print(f"[verify] exception: {e}")
        return jsonify(success=False, message='Server error'), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    print("\n" + "="*50)
    print("🚀 VENOM Dashboard Server Starting...")
    print("="*50)
    print("📍 Server: http://127.0.0.1:5000")
    print("📝 Login Page: http://127.0.0.1:5000/login")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

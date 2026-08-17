# MySQL Database Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'tatkal_user',
    'password': 'tatkal_password_123',
    'database': 'tatkal_db',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': False,
    'raise_on_warnings': False
}

# Flask Configuration
SECRET_KEY_LENGTH = 24
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = True
SESSION_LIFETIME_HOURS = 12

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///settle_space.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings for 2FA and notifications
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Your Gmail address
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Your Gmail App Password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    
    # Twilio settings for SMS OTP (Free tier: $15 credit + free phone number)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')  # Your Twilio phone number
    
    # Alternative SMS providers (all have free tiers)
    # Option 1: TextLocal (Free 100 SMS/day in India)
    TEXTLOCAL_API_KEY = os.environ.get('TEXTLOCAL_API_KEY')
    TEXTLOCAL_SENDER = os.environ.get('TEXTLOCAL_SENDER', 'SETTLE')
    
    # Option 2: MSG91 (Free 100 SMS)
    MSG91_API_KEY = os.environ.get('MSG91_API_KEY')
    MSG91_SENDER_ID = os.environ.get('MSG91_SENDER_ID', 'SETTLE')
    MSG91_ROUTE = os.environ.get('MSG91_ROUTE', '4')  # 4 = Transactional
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join('..', 'frontend', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Payment settings
    LISTING_FEE = 500  # Rs. 500 listing fee
    GPAY_UPI_ID = os.environ.get('GPAY_UPI_ID') or 'settlespace@paytm'
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # 2FA settings
    OTP_EXPIRY_MINUTES = 10
    MAX_OTP_ATTEMPTS = 3
    RATE_LIMIT_PER_MINUTE = 5  # Max OTP requests per minute per user
    
    # Application settings
    SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:5000')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@settlespace.com')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'settle_space.log')

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
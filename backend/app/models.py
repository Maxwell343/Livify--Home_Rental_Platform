from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # customer, seller, admin
    upi_id = db.Column(db.String(100))  # For sellers
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 2FA fields
    two_factor_enabled = db.Column(db.Boolean, default=True)
    two_factor_method = db.Column(db.String(10), default='email')  # email or sms
    
    # Relationships
    properties = db.relationship('Property', backref='seller', lazy=True)
    inquiries_sent = db.relationship('Inquiry', foreign_keys='Inquiry.customer_id', backref='customer', lazy=True)
    inquiries_received = db.relationship('Inquiry', foreign_keys='Inquiry.seller_id', backref='property_seller', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='seller', lazy=True)
    otp_codes = db.relationship('OTPCode', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_otp(self, method='email'):
        """Generate a new OTP code for this user"""
        # Delete any existing OTP codes for this user
        OTPCode.query.filter_by(user_id=self.id, used=False).delete()
        
        # Generate 6-digit OTP
        otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Create new OTP record
        otp = OTPCode(
            user_id=self.id,
            code=otp_code,
            method=method,
            expires_at=datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
        )
        db.session.add(otp)
        db.session.commit()
        
        return otp_code
    
    def verify_otp(self, code):
        """Verify OTP code"""
        otp = OTPCode.query.filter_by(
            user_id=self.id,
            code=code,
            used=False
        ).first()
        
        if not otp:
            return False
        
        if datetime.utcnow() > otp.expires_at:
            return False
        
        # Mark as used
        otp.used = True
        db.session.commit()
        
        return True
    
    def __repr__(self):
        return f'<User {self.email}>'

class OTPCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    method = db.Column(db.String(10), nullable=False)  # email or sms
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<OTPCode {self.code} for User {self.user_id}>'

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), nullable=False)  # buy, rent, pg
    property_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    area = db.Column(db.Integer, nullable=False)  # in sq ft
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text)  # JSON string
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Category specific fields
    sale_price = db.Column(db.Integer)  # For buy properties
    property_age = db.Column(db.Integer)  # For buy properties
    monthly_rent = db.Column(db.Integer)  # For rent properties
    security_deposit = db.Column(db.Integer)  # For rent properties
    furnishing_status = db.Column(db.String(20))  # fully, semi, unfurnished
    per_bed_price = db.Column(db.Integer)  # For PG properties
    gender_preference = db.Column(db.String(10))  # male, female, coed
    meal_included = db.Column(db.Boolean, default=False)  # For PG properties
    
    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade='all, delete-orphan')
    inquiries = db.relationship('Inquiry', backref='property', lazy=True)
    favorites = db.relationship('Favorite', backref='property', lazy=True)
    
    def __repr__(self):
        return f'<Property {self.title}>'

class PropertyImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PropertyImage {self.filename}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)
    screenshot_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relationship
    property = db.relationship('Property', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    status = db.Column(db.String(20), default='open')  # open, responded, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Inquiry {self.id}>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'property_id', name='unique_user_property_favorite'),)
    
    def __repr__(self):
        return f'<Favorite {self.user_id}-{self.property_id}>'
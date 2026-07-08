from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, PasswordField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, Optional, ValidationError, Regexp
from wtforms.widgets import TextArea
from app.models import User
import re

class StrongPasswordValidator:
    """Custom validator for strong password requirements"""
    def __init__(self, message=None):
        if not message:
            message = 'Password must contain at least 8 characters, including uppercase, lowercase, number, and special character'
        self.message = message

    def __call__(self, form, field):
        password = field.data
        if not password:
            return
            
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
            
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
            
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number')
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character')

class PhoneNumberValidator:
    """Custom validator for Indian phone numbers"""
    def __init__(self, message=None):
        if not message:
            message = 'Please enter a valid 10-digit Indian phone number'
        self.message = message

    def __call__(self, form, field):
        phone = field.data
        if not phone:
            return
            
        # Remove any spaces, hyphens, or parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check for Indian mobile number pattern
        if not re.match(r'^(\+91)?[6-9]\d{9}$', cleaned_phone):
            raise ValidationError(self.message)

class UPIValidator:
    """Custom validator for UPI IDs"""
    def __init__(self, message=None):
        if not message:
            message = 'Please enter a valid UPI ID (e.g., yourname@paytm, yourname@gpay)'
        self.message = message

    def __call__(self, form, field):
        upi_id = field.data
        if not upi_id:
            return
            
        # UPI ID pattern: something@provider
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$', upi_id):
            raise ValidationError(self.message)
            
        # Common UPI providers
        valid_providers = ['paytm', 'gpay', 'phonepe', 'ybl', 'okhdfcbank', 'okaxis', 'oksbi', 'okicici']
        provider = upi_id.split('@')[1].lower()
        
        # Allow any provider but warn about common ones
        if len(provider) < 2:
            raise ValidationError('UPI provider seems too short')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class TwoFactorForm(FlaskForm):
    otp_code = StringField('Verification Code', validators=[
        DataRequired(message="Please enter the verification code"),
        Length(min=6, max=6, message="Code must be 6 digits"),
        Regexp(r'^\d{6}$', message="Code must contain only numbers")
    ])
    submit = SubmitField('Verify')

class CustomerRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters"),
        Regexp(r'^[a-zA-Z\s]+$', message="Name can only contain letters and spaces")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email is too long")
    ])
    
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required"),
        PhoneNumberValidator()
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        StrongPasswordValidator()
    ])
    
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    
    # 2FA preference
    two_factor_method = SelectField('2FA Method', choices=[
        ('email', 'Email (Recommended)'),
        ('sms', 'SMS')
    ], default='email', validators=[DataRequired()])
    
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different email or try logging in.')
    
    def validate_phone(self, phone):
        # Clean phone number for database check
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone.data)
        if cleaned_phone.startswith('+91'):
            cleaned_phone = cleaned_phone[3:]
        
        user = User.query.filter_by(phone=cleaned_phone).first()
        if user:
            raise ValidationError('This phone number is already registered.')

class SellerRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters"),
        Regexp(r'^[a-zA-Z\s]+$', message="Name can only contain letters and spaces")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email is too long")
    ])
    
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required"),
        PhoneNumberValidator()
    ])
    
    upi_id = StringField('UPI ID', validators=[
        DataRequired(message="UPI ID is required for receiving payments"),
        UPIValidator(),
        Length(min=5, max=100, message="UPI ID must be between 5 and 100 characters")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        StrongPasswordValidator()
    ])
    
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    
    # 2FA preference
    two_factor_method = SelectField('2FA Method', choices=[
        ('email', 'Email (Recommended)'),
        ('sms', 'SMS')
    ], default='email', validators=[DataRequired()])
    
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different email or try logging in.')
    
    def validate_phone(self, phone):
        # Clean phone number for database check
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone.data)
        if cleaned_phone.startswith('+91'):
            cleaned_phone = cleaned_phone[3:]
            
        user = User.query.filter_by(phone=cleaned_phone).first()
        if user:
            raise ValidationError('This phone number is already registered.')
    
    def validate_upi_id(self, upi_id):
        user = User.query.filter_by(upi_id=upi_id.data.lower()).first()
        if user:
            raise ValidationError('This UPI ID is already registered by another seller.')

class PropertyForm(FlaskForm):
    title = StringField('Property Title', validators=[DataRequired(), Length(min=10, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=100, max=2000)], widget=TextArea())
    category = SelectField('Category', choices=[('buy', 'Buy'), ('rent', 'Rent'), ('pg', 'PG/Hostel')], validators=[DataRequired()])
    property_type = SelectField('Property Type', choices=[
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('plot', 'Plot'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('warehouse', 'Warehouse'),
        ('pg', 'PG'),
        ('hostel', 'Hostel')
    ], validators=[DataRequired()])
    price = IntegerField('Price (₹)', validators=[DataRequired(), NumberRange(min=1000)])
    location = StringField('Location', validators=[DataRequired(), Length(min=5, max=200)])
    area = IntegerField('Area (sq ft)', validators=[DataRequired(), NumberRange(min=100)])
    bedrooms = IntegerField('Bedrooms', validators=[DataRequired(), NumberRange(min=0, max=10)])
    bathrooms = IntegerField('Bathrooms', validators=[DataRequired(), NumberRange(min=1, max=10)])
    amenities = TextAreaField('Amenities (comma separated)')
    
    # Category specific fields
    property_age = IntegerField('Property Age (years)', validators=[Optional(), NumberRange(min=0, max=100)])
    security_deposit = IntegerField('Security Deposit (₹)', validators=[Optional(), NumberRange(min=0)])
    furnishing_status = SelectField('Furnishing Status', choices=[
        ('', 'Select Status'),
        ('fully', 'Fully Furnished'),
        ('semi', 'Semi Furnished'),
        ('unfurnished', 'Unfurnished')
    ], validators=[Optional()])
    gender_preference = SelectField('Gender Preference', choices=[
        ('', 'Select Preference'),
        ('male', 'Male Only'),
        ('female', 'Female Only'),
        ('coed', 'Co-ed')
    ], validators=[Optional()])
    meal_included = BooleanField('Meals Included')
    
    # File uploads
    images = MultipleFileField('Property Images (3-4 images)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    submit = SubmitField('Submit Property')

class PaymentForm(FlaskForm):
    transaction_id = StringField('UPI Transaction ID', validators=[DataRequired(), Length(min=5, max=100)])
    screenshot = FileField('Payment Screenshot', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Submit Payment Proof')

class InquiryForm(FlaskForm):
    message = TextAreaField('Your Message', validators=[DataRequired(), Length(min=10, max=500)], widget=TextArea())
    submit = SubmitField('Send Inquiry')

class SearchForm(FlaskForm):
    search = StringField('Search Properties')
    category = SelectField('Category', choices=[('', 'All Categories'), ('buy', 'Buy'), ('rent', 'Rent'), ('pg', 'PG/Hostel')])
    location = StringField('Location')
    min_price = IntegerField('Min Price (₹)', validators=[Optional(), NumberRange(min=0)])
    max_price = IntegerField('Max Price (₹)', validators=[Optional(), NumberRange(min=0)])
    property_type = SelectField('Property Type', choices=[
        ('', 'Any Type'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('plot', 'Plot'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('warehouse', 'Warehouse'),
        ('pg', 'PG'),
        ('hostel', 'Hostel')
    ])
    bedrooms = SelectField('Min Bedrooms', choices=[('', 'Any'), ('1', '1+'), ('2', '2+'), ('3', '3+'), ('4', '4+'), ('5', '5+')])
    submit = SubmitField('Search')
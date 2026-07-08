from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app.models import User, db
from app.forms import LoginForm, CustomerRegistrationForm, SellerRegistrationForm, TwoFactorForm
from app.services.two_factor import TwoFactorService
import re

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                # Store user ID in session for 2FA verification
                session['pending_user_id'] = user.id
                session['remember_me'] = form.remember_me.data
                
                # Send OTP
                if TwoFactorService.send_otp(user, user.two_factor_method):
                    return redirect(url_for('auth.verify_2fa'))
                else:
                    flash('Failed to send verification code. Please try again.', 'error')
            else:
                # Login directly if 2FA is disabled
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    if user.role == 'admin':
                        next_page = url_for('admin.dashboard')
                    elif user.role == 'seller':
                        next_page = url_for('seller.dashboard')
                    else:
                        next_page = url_for('main.index')
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(next_page)
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if 'pending_user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['pending_user_id'])
    if not user:
        session.pop('pending_user_id', None)
        flash('Invalid session. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    form = TwoFactorForm()
    
    # Use temporary method if set, otherwise use user's default method
    current_method = session.get('temp_2fa_method', user.two_factor_method)
    
    if form.validate_on_submit():
        if user.verify_otp(form.otp_code.data):
            # OTP verified successfully
            login_user(user, remember=session.get('remember_me', False))
            
            # Clean up session
            session.pop('pending_user_id', None)
            session.pop('remember_me', None)
            session.pop('temp_2fa_method', None)  # Clean up temp method
            
            # Redirect to appropriate dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user.role == 'admin':
                    next_page = url_for('admin.dashboard')
                elif user.role == 'seller':
                    next_page = url_for('seller.dashboard')
                else:
                    next_page = url_for('main.index')
            
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid or expired verification code. Please try again.', 'error')
    
    # Pass the current method to template
    return render_template('auth/verify_2fa.html', form=form, user=user, current_method=current_method)

@bp.route('/resend-otp')
def resend_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if 'pending_user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['pending_user_id'])
    if not user:
        session.pop('pending_user_id', None)
        flash('Invalid session. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Use temporary method if set, otherwise use user's default method
    method = session.get('temp_2fa_method', user.two_factor_method)
    
    # Send new OTP
    if TwoFactorService.send_otp(user, method):
        flash('New verification code sent successfully!', 'success')
    else:
        flash('Failed to send verification code. Please try again.', 'error')
    
    return redirect(url_for('auth.verify_2fa'))

@bp.route('/switch-2fa-method', methods=['POST'])
def switch_2fa_method():
    """Switch 2FA method during verification process"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if 'pending_user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['pending_user_id'])
    if not user:
        session.pop('pending_user_id', None)
        flash('Invalid session. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    new_method = request.form.get('method')
    if new_method not in ['email', 'sms']:
        flash('Invalid verification method.', 'error')
        return redirect(url_for('auth.verify_2fa'))
    
    # Store the temporary method preference in session
    session['temp_2fa_method'] = new_method
    
    # Send OTP using the new method
    if TwoFactorService.send_otp(user, new_method):
        flash(f'Verification code sent via {new_method.upper()}!', 'success')
    else:
        flash(f'Failed to send verification via {new_method.upper()}. Please try again.', 'error')
        # Remove the temp method if sending failed
        session.pop('temp_2fa_method', None)
    
    return redirect(url_for('auth.verify_2fa'))

@bp.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('auth/register_choice.html')

@bp.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = CustomerRegistrationForm()
    
    # DEBUG: Print what's happening
    print("=== REGISTRATION DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"Form submitted: {form.is_submitted()}")
    print(f"Form valid: {form.validate()}")
    
    if request.method == 'POST':
        print(f"Form data received: {request.form}")
        print(f"Form errors: {form.errors}")
    
    if form.validate_on_submit():
        print("[INFO] Form validation PASSED - Creating user...")
        try:
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', form.phone.data)
            if cleaned_phone.startswith('+91'):
                cleaned_phone = cleaned_phone[3:]
            elif not cleaned_phone.startswith('91') and len(cleaned_phone) == 10:
                pass
            
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.lower().strip(),
                phone=cleaned_phone,
                role='customer',
                two_factor_method=form.two_factor_method.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            print("[INFO] User created successfully!")
            
            TwoFactorService.send_welcome_email(user)
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            print(f"[ERROR] Database error: {str(e)}")
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
    else:
        if request.method == 'POST':
            print("[ERROR] Form validation FAILED")
            for field, errors in form.errors.items():
                print(f"Field '{field}' errors: {errors}")
    
    return render_template('auth/register_customer.html', form=form)

@bp.route('/register/seller', methods=['GET', 'POST'])
def register_seller():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = SellerRegistrationForm()
    
    # DEBUG: Print what's happening (same as customer registration)
    print("=== SELLER REGISTRATION DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"Form submitted: {form.is_submitted()}")
    print(f"Form valid: {form.validate()}")
    
    if request.method == 'POST':
        print(f"Form data received: {request.form}")
        print(f"Form errors: {form.errors}")
    
    if form.validate_on_submit():
        print("[INFO] Form validation PASSED - Creating seller...")
        try:
            # Clean phone number
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', form.phone.data)
            if cleaned_phone.startswith('+91'):
                cleaned_phone = cleaned_phone[3:]
            elif not cleaned_phone.startswith('91') and len(cleaned_phone) == 10:
                pass  # Keep as is for 10-digit numbers
            
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.lower().strip(),
                phone=cleaned_phone,
                upi_id=form.upi_id.data.lower().strip(),
                role='seller',
                two_factor_method=form.two_factor_method.data
            )
            user.set_password(form.password.data)
            
            print(f"Creating user: {user.name}, {user.email}, {user.phone}, {user.upi_id}")
            
            db.session.add(user)
            db.session.commit()
            print("[INFO] Seller created successfully!")
            
            # Send welcome email
            TwoFactorService.send_welcome_email(user)
            
            flash('Registration successful! You can now log in and start listing properties. 2FA is enabled for security.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            print(f"[ERROR] Database error: {str(e)}")
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    else:
        if request.method == 'POST':
            print("[ERROR] Form validation FAILED")
            for field, errors in form.errors.items():
                print(f"Field '{field}' errors: {errors}")
    
    return render_template('auth/register_seller.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    # Clear any pending 2FA sessions
    session.pop('pending_user_id', None)
    session.pop('remember_me', None)
    session.pop('temp_2fa_method', None)
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('main.index'))

# Additional security routes

@bp.route('/change-2fa-method', methods=['POST'])
def change_2fa_method():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    new_method = request.form.get('method')
    if new_method in ['email', 'sms']:
        current_user.two_factor_method = new_method
        db.session.commit()
        flash(f'2FA method changed to {new_method.upper()} successfully!', 'success')
    else:
        flash('Invalid 2FA method selected.', 'error')
    
    return redirect(url_for('customer.profile'))  # or seller.profile based on role

@bp.route('/disable-2fa', methods=['POST'])
def disable_2fa():
    """Allow users to disable 2FA (not recommended)"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Require password confirmation for security
    password = request.form.get('current_password')
    if not password or not current_user.check_password(password):
        flash('Please enter your current password to disable 2FA.', 'error')
        return redirect(url_for('customer.profile'))
    
    current_user.two_factor_enabled = False
    db.session.commit()
    
    flash('⚠️ Two-factor authentication has been disabled. Your account is less secure now.', 'warning')
    return redirect(url_for('customer.profile'))

@bp.route('/enable-2fa', methods=['POST'])
def enable_2fa():
    """Allow users to enable 2FA"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    method = request.form.get('method', 'email')
    if method not in ['email', 'sms']:
        method = 'email'
    
    current_user.two_factor_enabled = True
    current_user.two_factor_method = method
    db.session.commit()
    
    flash(f'Two-factor authentication enabled with {method.upper()}! Your account is now more secure.', 'success')
    return redirect(url_for('customer.profile'))
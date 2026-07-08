from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Property, Payment, PropertyImage
from app import db
from sqlalchemy import desc, asc, func, or_
from functools import wraps

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_properties': Property.query.count(),
        'pending_properties': Property.query.filter_by(status='pending').count(),
        'total_users': User.query.filter(User.role != 'admin').count(),
        'total_revenue': db.session.query(func.sum(Payment.amount)).filter_by(status='verified').scalar() or 0
    }
    
    # Get recent properties (last 5)
    recent_properties = Property.query.order_by(desc(Property.created_at)).limit(5).all()
    
    # Get recent payments (last 5)
    recent_payments = Payment.query.order_by(desc(Payment.created_at)).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_properties=recent_properties,
                         recent_payments=recent_payments)

@bp.route('/pending-properties')
@login_required
@admin_required
def pending_properties():
    # Get filters from request
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    seller = request.args.get('seller', '')
    
    # Base query
    query = Property.query.filter_by(status='pending')
    
    # Apply filters
    if category:
        query = query.filter_by(category=category)
    if location:
        query = query.filter(Property.location.ilike(f'%{location}%'))
    if seller:
        query = query.join(User).filter(User.name.ilike(f'%{seller}%'))
    
    properties = query.order_by(desc(Property.created_at)).all()
    
    return render_template('admin/pending_properties.html', properties=properties)

@bp.route('/pending-payments')
@login_required
@admin_required
def pending_payments():
    payments = Payment.query.filter_by(status='pending').order_by(desc(Payment.created_at)).all()
    return render_template('admin/pending_payments.html', payments=payments)

@bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    # Get filters from request
    role = request.args.get('role', '')
    verified = request.args.get('verified', '')
    search = request.args.get('search', '')
    
    # Base query (exclude admin users from management)
    query = User.query.filter(User.role != 'admin')
    
    # Apply filters
    if role:
        query = query.filter_by(role=role)
    if verified:
        is_verified = verified == '1'
        query = query.filter_by(is_verified=is_verified)
    if search:
        query = query.filter(or_(
            User.name.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%')
        ))
    
    users = query.order_by(desc(User.created_at)).all()
    
    # Get user statistics
    stats = {
        'total_users': User.query.filter(User.role != 'admin').count(),
        'sellers': User.query.filter_by(role='seller').count(),
        'customers': User.query.filter_by(role='customer').count()
    }
    
    return render_template('admin/manage_users.html', users=users, stats=stats)

@bp.route('/all-properties')
@login_required
@admin_required
def all_properties():
    # Get filters from request
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    
    # Base query
    query = Property.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if location:
        query = query.filter(Property.location.ilike(f'%{location}%'))
    if search:
        query = query.filter(or_(
            Property.title.ilike(f'%{search}%'),
            Property.description.ilike(f'%{search}%')
        ))
    
    # Apply sorting
    if sort == 'oldest':
        query = query.order_by(asc(Property.created_at))
    elif sort == 'price_high':
        query = query.order_by(desc(Property.price))
    elif sort == 'price_low':
        query = query.order_by(asc(Property.price))
    else:  # newest
        query = query.order_by(desc(Property.created_at))
    
    properties = query.all()
    
    return render_template('admin/all_properties.html', properties=properties)

# API Routes for AJAX updates
@bp.route('/property/<int:property_id>/status', methods=['POST'])
@login_required
@admin_required
def update_property_status(property_id):
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['pending', 'approved', 'rejected']:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        property = Property.query.get_or_404(property_id)
        property.status = status
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Property {status} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating property status'})

@bp.route('/payment/<int:payment_id>/status', methods=['POST'])
@login_required
@admin_required
def update_payment_status(payment_id):
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['pending', 'verified', 'rejected']:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        payment = Payment.query.get_or_404(payment_id)
        payment.status = status
        
        # If payment is verified, also approve the property
        if status == 'verified':
            payment.property.status = 'approved'
        elif status == 'rejected':
            payment.property.status = 'rejected'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Payment {status} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating payment status'})

@bp.route('/user/<int:user_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        user.is_verified = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User verified successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error verifying user'})

@bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    try:
        user = User.query.get_or_404(user_id)
        # Toggle some status (you might want to add an 'active' field to User model)
        # For now, we'll toggle the verified status as an example
        user.is_verified = not user.is_verified
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User status updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating user status'})
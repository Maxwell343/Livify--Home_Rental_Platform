from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Property, PropertyImage, Payment
from app.forms import PropertyForm, PaymentForm
from app import db
import os
import json
from PIL import Image

bp = Blueprint('seller', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'seller':
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('main.index'))
    
    # Get seller's properties
    properties = Property.query.filter_by(seller_id=current_user.id).order_by(Property.created_at.desc()).all()
    
    # Get statistics
    total_properties = len(properties)
    approved_properties = len([p for p in properties if p.status == 'approved'])
    pending_properties = len([p for p in properties if p.status == 'pending'])
    rejected_properties = len([p for p in properties if p.status == 'rejected'])
    
    stats = {
        'total': total_properties,
        'approved': approved_properties,
        'pending': pending_properties,
        'rejected': rejected_properties
    }
    
    return render_template('seller/dashboard.html', properties=properties, stats=stats)

@bp.route('/add-property', methods=['GET', 'POST'])
@login_required
def add_property():
    if current_user.role != 'seller':
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('main.index'))
    
    form = PropertyForm()
    if form.validate_on_submit():
        # Create property
        property = Property(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            property_type=form.property_type.data,
            price=form.price.data,
            location=form.location.data,
            area=form.area.data,
            bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data,
            amenities=form.amenities.data,
            seller_id=current_user.id
        )
        
        # Set category-specific fields
        if form.category.data == 'buy':
            property.sale_price = form.price.data
            property.property_age = form.property_age.data
        elif form.category.data == 'rent':
            property.monthly_rent = form.price.data
            property.security_deposit = form.security_deposit.data
            property.furnishing_status = form.furnishing_status.data
        elif form.category.data == 'pg':
            property.per_bed_price = form.price.data
            property.gender_preference = form.gender_preference.data
            property.meal_included = form.meal_included.data
        
        db.session.add(property)
        db.session.flush()  # Get the property ID
        
        # Handle image uploads
        if form.images.data:
            upload_folder = os.path.join(current_app.instance_path, 'uploads', 'properties')
            os.makedirs(upload_folder, exist_ok=True)
            
            for i, file in enumerate(form.images.data):
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"property_{property.id}_{i}_{file.filename}")
                    filepath = os.path.join(upload_folder, filename)
                    
                    # Resize and save image
                    image = Image.open(file)
                    image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                    image.save(filepath, optimize=True, quality=85)
                    
                    # Create PropertyImage record
                    property_image = PropertyImage(
                        property_id=property.id,
                        filename=filename,
                        is_primary=(i == 0)
                    )
                    db.session.add(property_image)
        
        db.session.commit()
        flash('Property submitted successfully! Please proceed with payment to complete the listing.', 'success')
        return redirect(url_for('seller.payment', property_id=property.id))
    
    return render_template('seller/add_property.html', form=form)

@bp.route('/payment/<int:property_id>', methods=['GET', 'POST'])
@login_required
def payment(property_id):
    if current_user.role != 'seller':
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('main.index'))
    
    property = Property.query.filter_by(id=property_id, seller_id=current_user.id).first_or_404()
    
    # Check if payment already exists
    existing_payment = Payment.query.filter_by(property_id=property_id).first()
    if existing_payment:
        flash('Payment already submitted for this property.', 'info')
        return redirect(url_for('seller.dashboard'))
    
    form = PaymentForm()
    if form.validate_on_submit():
        # Handle screenshot upload
        upload_folder = os.path.join(current_app.instance_path, 'uploads', 'payments')
        os.makedirs(upload_folder, exist_ok=True)
        
        file = form.screenshot.data
        filename = secure_filename(f"payment_{property_id}_{form.transaction_id.data}_{file.filename}")
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Create payment record
        payment = Payment(
            seller_id=current_user.id,
            property_id=property_id,
            amount=current_app.config['LISTING_FEE'],
            transaction_id=form.transaction_id.data,
            screenshot_filename=filename
        )
        db.session.add(payment)
        db.session.commit()
        
        flash('Payment proof submitted successfully! Your property will be reviewed by admin.', 'success')
        return redirect(url_for('seller.dashboard'))
    
    return render_template('seller/payment.html', form=form, property=property, 
                         listing_fee=current_app.config['LISTING_FEE'],
                         gpay_upi=current_app.config['GPAY_UPI_ID'])

@bp.route('/property/<int:id>')
@login_required
def property_detail(id):
    if current_user.role != 'seller':
        flash('Access denied. Seller account required.', 'error')
        return redirect(url_for('main.index'))
    
    property = Property.query.filter_by(id=id, seller_id=current_user.id).first_or_404()
    payment = Payment.query.filter_by(property_id=id).first()
    
    return render_template('seller/property_detail.html', property=property, payment=payment)
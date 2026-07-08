from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Favorite, Property, Inquiry
from app.forms import InquiryForm
from app import db

bp = Blueprint('customer', __name__)

@bp.route('/favorites')
@login_required
def favorites():
    if current_user.role != 'customer':
        flash('Access denied. Customer account required.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    favorites = db.session.query(Favorite, Property).join(Property).filter(
        Favorite.user_id == current_user.id,
        Property.status == 'approved'
    ).order_by(Favorite.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('customer/favorites.html', favorites=favorites)

@bp.route('/toggle-favorite/<int:property_id>', methods=['POST'])
@login_required
def toggle_favorite(property_id):
    if current_user.role != 'customer':
        return jsonify({'error': 'Access denied'}), 403
    
    property = Property.query.filter_by(id=property_id, status='approved').first_or_404()
    
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        property_id=property_id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        is_favorite = False
        message = 'Removed from favorites'
    else:
        favorite = Favorite(user_id=current_user.id, property_id=property_id)
        db.session.add(favorite)
        is_favorite = True
        message = 'Added to favorites'
    
    db.session.commit()
    
    return jsonify({
        'is_favorite': is_favorite,
        'message': message
    })

@bp.route('/inquire/<int:property_id>', methods=['GET', 'POST'])
@login_required
def inquire(property_id):
    if current_user.role != 'customer':
        flash('Access denied. Customer account required.', 'error')
        return redirect(url_for('main.index'))
    
    property = Property.query.filter_by(id=property_id, status='approved').first_or_404()
    
    form = InquiryForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            property_id=property_id,
            customer_id=current_user.id,
            seller_id=property.seller_id,
            message=form.message.data,
            customer_name=current_user.name,
            customer_phone=current_user.phone
        )
        db.session.add(inquiry)
        db.session.commit()
        
        flash('Your inquiry has been sent to the seller!', 'success')
        return redirect(url_for('main.property_detail', id=property_id))
    
    return render_template('customer/inquire.html', form=form, property=property)

@bp.route('/inquiries')
@login_required
def inquiries():
    if current_user.role != 'customer':
        flash('Access denied. Customer account required.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    inquiries = Inquiry.query.filter_by(customer_id=current_user.id).order_by(
        Inquiry.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('customer/inquiries.html', inquiries=inquiries)
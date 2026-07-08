import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort, current_app
from flask_login import current_user
from app.models import Property, User
from app.forms import SearchForm
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Homepage - shows no properties initially as admin hasn't approved any"""
    search_form = SearchForm()
    
    # Get featured properties (only approved ones, but there are none initially)
    featured_properties = Property.query.filter_by(status='approved', is_featured=True).limit(6).all()
    
    # Stats (will be 0 initially)
    total_properties = Property.query.filter_by(status='approved').count()
    total_customers = User.query.filter_by(role='customer').count()
    total_sellers = User.query.filter_by(role='seller').count()
    
    stats = {
        'properties': total_properties,
        'customers': total_customers,
        'sellers': total_sellers
    }
    
    return render_template('index.html', 
                         featured_properties=featured_properties,
                         stats=stats,
                         search_form=search_form)

@bp.route('/properties')
def properties():
    """Properties listing page with search and filters"""
    search_form = SearchForm()
    
    # Start with approved properties only (none initially)
    query = Property.query.filter_by(status='approved')
    
    # Apply filters if form is submitted
    if search_form.validate_on_submit() or request.args:
        if search_form.search.data or request.args.get('search'):
            search_term = search_form.search.data or request.args.get('search')
            query = query.filter(
                Property.title.contains(search_term) |
                Property.description.contains(search_term) |
                Property.location.contains(search_term)
            )
        
        if search_form.category.data or request.args.get('category'):
            category = search_form.category.data or request.args.get('category')
            query = query.filter_by(category=category)
        
        if search_form.location.data or request.args.get('location'):
            location = search_form.location.data or request.args.get('location')
            query = query.filter(Property.location.contains(location))
        
        if search_form.min_price.data or request.args.get('min_price'):
            min_price = search_form.min_price.data or int(request.args.get('min_price'))
            query = query.filter(Property.price >= min_price)
        
        if search_form.max_price.data or request.args.get('max_price'):
            max_price = search_form.max_price.data or int(request.args.get('max_price'))
            query = query.filter(Property.price <= max_price)
        
        if search_form.property_type.data or request.args.get('property_type'):
            prop_type = search_form.property_type.data or request.args.get('property_type')
            query = query.filter_by(property_type=prop_type)
        
        if search_form.bedrooms.data or request.args.get('bedrooms'):
            bedrooms = int(search_form.bedrooms.data or request.args.get('bedrooms'))
            query = query.filter(Property.bedrooms >= bedrooms)
    
    # Get category from URL parameter
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
        search_form.category.data = category
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    properties = query.order_by(Property.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('properties/list.html', 
                         properties=properties,
                         search_form=search_form,
                         category=category)

@bp.route('/property/<int:id>')
def property_detail(id):
    """Property detail page - requires login"""
    if not current_user.is_authenticated:
        flash('Please log in to view property details.', 'info')
        return redirect(url_for('auth.login', next=request.url))
    
    property = Property.query.filter_by(id=id, status='approved').first_or_404()
    
    # Check if property is in user's favorites
    is_favorite = False
    if current_user.is_authenticated:
        from app.models import Favorite
        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id, 
            property_id=property.id
        ).first() is not None
    
    return render_template('properties/detail.html', 
                         property=property,
                         is_favorite=is_favorite)

@bp.route('/uploads/properties/<filename>')
def uploaded_file(filename):
    """Serve uploaded property images from instance folder"""
    upload_folder = os.path.join(current_app.instance_path, 'uploads', 'properties')
    
    # Security check - make sure file exists and is in the right folder
    file_path = os.path.join(upload_folder, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    return send_from_directory(upload_folder, filename)

@bp.route('/debug/images')
def debug_images():
    """Debug route to check image issues"""
    debug_info = {
        'instance_path': current_app.instance_path,
        'upload_path': os.path.join(current_app.instance_path, 'uploads', 'properties'),
        'path_exists': False,
        'files_in_folder': [],
        'sample_properties': []
    }
    
    upload_path = debug_info['upload_path']
    
    # Check if upload folder exists
    if os.path.exists(upload_path):
        debug_info['path_exists'] = True
        try:
            debug_info['files_in_folder'] = os.listdir(upload_path)
        except Exception as e:
            debug_info['files_in_folder'] = f"Error reading folder: {e}"
    else:
        debug_info['files_in_folder'] = "Upload folder does not exist"
    
    # Get sample properties with images
    try:
        properties_with_images = Property.query.filter(Property.images.any()).limit(5).all()
        for prop in properties_with_images:
            prop_info = {
                'id': prop.id,
                'title': prop.title,
                'images': []
            }
            for img in prop.images:
                img_path = os.path.join(upload_path, img.filename)
                prop_info['images'].append({
                    'filename': img.filename,
                    'exists_on_disk': os.path.exists(img_path) if debug_info['path_exists'] else False,
                    'full_path': img_path
                })
            debug_info['sample_properties'].append(prop_info)
    except Exception as e:
        debug_info['sample_properties'] = f"Error querying properties: {e}"
    
    # Return formatted debug info
    import json
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')
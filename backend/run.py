from flask import send_from_directory
from app import create_app, db
from app.models import User, Property, PropertyImage, Payment, Inquiry, Favorite
import os

app = create_app()

# Add route to serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the instance/uploads directory"""
    return send_from_directory(
        os.path.join(app.instance_path, 'uploads'), 
        filename
    )

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Property': Property,
        'PropertyImage': PropertyImage,
        'Payment': Payment,
        'Inquiry': Inquiry,
        'Favorite': Favorite
    }

def create_tables():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email='admin@settlespace.com').first()
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@settlespace.com',
            phone='+91 9876543210',
            role='admin',
            is_verified=True,
            two_factor_enabled=False
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@settlespace.com / admin123")
        
    # Create customer demo user if it doesn't exist
    customer = User.query.filter_by(email='customer@demo.com').first()
    if not customer:
        customer = User(
            name='Demo Customer',
            email='customer@demo.com',
            phone='9876543211',
            role='customer',
            is_verified=True,
            two_factor_enabled=False
        )
        customer.set_password('password123')
        db.session.add(customer)
        db.session.commit()
        print("Customer demo user created: customer@demo.com / password123")
        
    # Create seller demo user if it doesn't exist
    seller = User.query.filter_by(email='seller@demo.com').first()
    if not seller:
        seller = User(
            name='Demo Seller',
            email='seller@demo.com',
            phone='9876543212',
            role='seller',
            is_verified=True,
            two_factor_enabled=False,
            upi_id='demo.seller@okaxis'
        )
        seller.set_password('password123')
        db.session.add(seller)
        db.session.commit()
        print("Seller demo user created: seller@demo.com / password123")

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)
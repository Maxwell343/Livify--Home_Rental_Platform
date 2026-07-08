from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(upi_id='amey@gpay').first()
    if user:
        db.session.delete(user)
        db.session.commit()
        print("User deleted successfully")
    else:
        print("User not found")

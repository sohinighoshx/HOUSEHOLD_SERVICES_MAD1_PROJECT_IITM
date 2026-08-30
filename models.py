from flask_sqlalchemy import SQLAlchemy
from app import app
from app import app
from datetime import datetime
db=SQLAlchemy(app)
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Store password as plain text
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    blocked = db.Column(db.Boolean, default=False, nullable=False) 
class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    service_name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)  # Add time_required field

    customer = db.relationship("Customer", backref="cart_items", lazy=True)
    service = db.relationship("Service", backref="cart_items", lazy=True)
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    timerequired = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    allowed = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=False)
class Professional(db.Model):
    __tablename__ = 'professionals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    service_type = db.Column(db.String(32), db.ForeignKey('services.name'), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    document = db.Column(db.String(200), nullable=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    blocked = db.Column(db.Boolean, default=False, nullable=False)
    service = db.relationship("Service", backref="professionals", lazy=True)
    date_created = db.Column(db.DateTime, nullable=True)  # Initially nullable

    def approve(self):
        """Approve the professional and set the date_created."""
        self.is_approved = True
        self.date_created = datetime.utcnow()

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    date_requested = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_completed = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="Pending", nullable=False)
    notes = db.Column(db.Text, nullable=True)
    work_completed = db.Column(db.Boolean, nullable=False, default=False)
    provider_notes = db.Column(db.Text, nullable=True)
    customer_approval = db.Column(db.Boolean, nullable=False, default=False)  # Approval by customer
    professional_approval = db.Column(db.Boolean, nullable=False, default=False)  
    feedback_given=db.Column(db.Boolean,db.ForeignKey('feedbacks.feedback_given'), nullable=False, default=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    cart = db.relationship('Cart', backref='orders', lazy=True)

    customer = db.relationship("Customer", backref="customer_orders", lazy=True)
    provider = db.relationship("Professional", backref="provider_orders", lazy=True)
    service = db.relationship("Service", backref="orders", lazy=True)
    feedback=db.relationship("Feedback",backref="orders",lazy=True)
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Use service_id
    pincode = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, etc.
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime, nullable=True)  # New field for completion date
    work_completed = db.Column(db.Boolean, nullable=False, default=False)  # New field for work status
    customer_approval = db.Column(db.Boolean, nullable=False, default=False)  # Approval by customer
    professional_approval = db.Column(db.Boolean, nullable=False, default=False)
    
    service = db.relationship("Service", backref="service_requests", lazy=True)
    customer = db.relationship("Customer", backref="service_requests", lazy=True)
    professional = db.relationship("Professional", backref="assigned_requests", lazy=True)

    def update_status(self):
            """
            Updates the status to 'Completed' if both approvals are True.
            """
            if self.customer_approval and self.professional_approval:
                self.status = 'Completed'
                self.date_completed = datetime.utcnow()

class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)  # Assuming you have a Customer model
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Assuming a Service model
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)  # Ensure 'professionals.id' matches your Professional model table name
    rating = db.Column(db.Integer, nullable=False)  # Rating scale (1-5)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_given=db.Column(db.Boolean, nullable=False, default=False) 
    # Relationships
    customer = db.relationship('Customer', backref='feedbacks')
    service = db.relationship('Service', backref='feedbacks')
    professional = db.relationship('Professional', backref='feedbacks')

    def __repr__(self):
        return f'<Feedback {self.id}>'

# Initialize database
with app.app_context():
    db.create_all()

    # Create admin if not exists
    admin = Customer.query.filter_by(username='admin').first()
    if not admin:
        admin = Customer(
            name="Admin User",
            username="admin",
            password="admin123",  # Use hashed passwords in production
            email="admin@example.com",
            address="Admin Headquarters",
            pincode="000000",
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

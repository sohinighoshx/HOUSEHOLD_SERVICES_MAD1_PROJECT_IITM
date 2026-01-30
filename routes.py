from flask import Flask, render_template, request, redirect, url_for,flash,session
from models import db,Customer,Professional,Order,Service,Cart,ServiceRequest,Feedback
from app import app
import os
import logging
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
logging.basicConfig(level=logging.INFO)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads/'  
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Dummy data storage
customers = [
    {'id': 1, 'username': 'john_doe', 'password': 'password123'}
]

professionals = [
    {'id': 1, 'username': 'jane_smith', 'password': 'password123', 'service_type': 'Plumbing'}
]
@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/admin_dashboard')
def admin():
    return render_template('admin_dashboard.html')
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check for empty username or password
        if not username or not password:
            flash("Username and password are required.", "warning")
            return render_template('error.html')

        try:
            # Check if the username exists in the Professional table
            professional = Professional.query.filter_by(username=username).first()

            if professional:
                # Check if the professional account is approved
                if professional.is_approved == False :
                    flash("Your professional account is not yet approved. Please wait for admin approval.", "warning")
                    return redirect(url_for('login'))
                if professional.blocked==False:
                    if professional.password == password:  # Compare plain text password for professional
                        session['professional_id'] = professional.id  # Save professional ID in session
                        return redirect(url_for('professional_dashboard'))
                    else:
                        flash("Incorrect password for professional account.", "danger")
                        return render_template('error.html')
                else:
                    return "YOU are blocked!!!!!"
                # If professional is not found, check the Customer table
            customer = Customer.query.filter_by(username=username).first()

            if customer:
                if customer.blocked==False:
                    if customer.password == password:  # Compare plain text password for customer
                        session['customer_id'] = customer.id  # Save customer ID in session
                        if customer.is_admin:
                            return redirect(url_for('admin_dashboard'))
                        else:
                            return redirect(url_for('customer_dashboard'))
                    else:
                        flash("Incorrect password for customer account.", "danger")
                        return render_template('error.html')
                else:
                    return "you are blocked now"

                # If username is not found in either table
            flash("Username not found in our system. Please check and try again.", "danger")
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')
@app.route('/c_register', methods=['GET', 'POST'])
def c_register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        address = request.form['address']
        pincode = request.form['pincode']

        new_customer = Customer(
            name=name,
            username=username,
            password=password,
            email=email,
            address=address,
            pincode=pincode
        )

        try:
            db.session.add(new_customer)
            db.session.commit()

            return redirect(url_for('login'))  # Redirect after successful registration
        except IntegrityError:
            db.session.rollback()
            return "Username or Email already exists. Please choose a different one."
        except Exception as e:
            db.session.rollback()
            # Display the exact error message in the browser
            return f"There was an issue saving your information: {str(e)}"
    
    return render_template('customer_register.html')

@app.route('/p_register', methods=['GET', 'POST'])
def p_register():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        service_type = request.form.get('service_type')
        experience = request.form.get('experience')
        description = request.form.get('description')
        document = request.files.get('document')

        # Validate required fields
        if not name or not password or not email:
            return redirect(url_for('p_register'))

        # Check if email already exists
        existing_professional = Professional.query.filter_by(email=email).first()
        if existing_professional:
            flash('Email is already registered.', 'danger')
            return redirect(url_for('p_register'))

        # Save uploaded document if provided
        document_filename = None
        if document:
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            if document.filename.split('.')[-1].lower() not in allowed_extensions:
                flash('Invalid file type. Only PDF, JPG, PNG files are allowed.', 'danger')
                return redirect(url_for('p_register'))

            document_filename = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
            document.save(document_filename)

        # Create a new Professional instance
        new_professional = Professional(
            name=name,
            username=username,
            password=password,  # Store the password as plain text
            email=email,
            address=address,
            pincode=pincode,
            service_type=service_type,
            experience=int(experience),
            description=description,
            document=document_filename,
            is_approved=False 
        )

        # Add  the professional to the database
        try:
            db.session.add(new_professional)
            db.session.commit()
            flash("Your registration is pending admin approval.", "info")
            return redirect(url_for('waiting'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {e}', 'danger')

    return render_template('p_register.html')
@app.route('/waiting')
def waiting():
    return "WAIT FOR APPROVAL "
@app.route('/success')
def success():
    return "Registration successful!"
@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    # Assuming session-based customer ID management
    customer_id = session.get('customer_id')

    if not customer_id:
        flash("You need to log in to access the dashboard.", "danger")
        return redirect(url_for('login'))

    customer = Customer.query.get(customer_id)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for('login'))
    if customer.blocked:
        return "Your page has been blocked. Please contact authorities for an explanation.", 403

    search_query = request.form.get('search', '').strip()
    selected_category = request.form.get('category', '').strip()

    # Start by querying only confirmed services
    query = Service.query.filter(Service.status == 'Confrimed')

    if search_query:
        query = query.filter(
            (Service.name.ilike(f"%{search_query}%")) | 
            (Service.description.ilike(f"%{search_query}%"))
        )

    if selected_category:
        # Filter by selected category (if any)
        query = query.filter(Service.name == selected_category)
    # Fetch the filtered services
    filtered_services = query.all()
    # Distinct categories for dropdown 
    categories = [row.name for row in Service.query.filter(Service.status == 'Confrimed').distinct(Service.name).all()]

    username = customer.username
    return render_template(
        'customer_dashboard.html',
        services=categories,
        filtered_services=filtered_services,
        search_query=search_query,
        selected_category=selected_category,
        customer_id=customer_id,
        username=username
    )

@app.route('/increase_quantity/<int:item_id>', methods=['POST', 'GET'])
def increase_quantity(item_id):
    # Fetch the cart item by ID
    cart_item = Cart.query.filter_by(id=item_id).first()

    if cart_item:
        # Increase the quantity
        cart_item.quantity += 1
        cart_item.total = cart_item.quantity * cart_item.price
        db.session.commit()

    # Redirect to the cart page after the operation
    return redirect(url_for('view_cart'))

@app.route('/decrease_quantity/<int:item_id>', methods=['POST', 'GET'])
def decrease_quantity(item_id):
    # Fetch the cart item by ID
    cart_item = Cart.query.filter_by(id=item_id).first()

    if cart_item:
        # Decrease quantity, ensuring it doesn't drop below 1
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.total = cart_item.quantity * cart_item.price
            db.session.commit()
        else:
            # remove the item if quantity drops to 0
            db.session.delete(cart_item)
            db.session.commit()

    # Redirect to the cart page after the operation
    return redirect(url_for('view_cart'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Get the form data (service ID, customer ID, quantity)
    service_id = request.form.get('service_id')
    customer_id = request.form.get('user_id')
    quantity = int(request.form.get('quantity', 1))  # Default to 1 if no quantity is provided

    # Fetch the customer and service from the database
    customer = Customer.query.get(customer_id)
    service = Service.query.get(service_id)

    # Check if the customer and service exist
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for('customer_dashboard'))  # Redirect to customer dashboard
    if not service:
        flash("Service not found.", "danger")
        return redirect(url_for('customer_dashboard'))  # Redirect to customer dashboard

    # Calculate the total price (quantity * price)
    total_price = quantity * service.price
    time_required = service.timerequired  # Fetch the time required for the service

    # Fetch the cart for the customer (if exists)
    cart = Cart.query.filter_by(customer_id=customer_id).first()

    if not cart:
        # Create a new cart if none exists
        cart = Cart(
            customer_id=customer_id,
            service_id=service.id,
            service_name=service.name,
            quantity=quantity,
            price=service.price,
            total=total_price,
            time_required=time_required  # Add time required to the cart
        )
        db.session.add(cart)
        db.session.commit()
        flash("Service added to cart.", "success")
    else:
        # If cart exists, check if the service is already in the cart
        existing_item = Cart.query.filter_by(customer_id=customer_id, service_id=service.id).first()
        
        if existing_item:
            # Update quantity and total for the existing cart item
            existing_item.quantity += quantity
            existing_item.total = existing_item.quantity * existing_item.price
            db.session.commit()
            flash("Cart updated.", "success")
        else:
            # Add new service to the existing cart
            new_item = Cart(
                customer_id=customer_id,
                service_id=service.id,
                service_name=service.name,
                quantity=quantity,
                price=service.price,
                total=total_price,
                time_required=time_required  # Add time required to the cart
            )
            db.session.add(new_item)
            db.session.commit()
            flash("Service added to cart.", "success")
    
    return redirect(url_for('customer_dashboard'))
@app.route('/view_cart', methods=['GET'])
def view_cart():
    # Assuming customer_id is available in session or passed from the frontend
    customer_id = session.get('customer_id')

    if not customer_id:
        flash("You need to log in to view your cart.", "danger")
        return redirect(url_for('login'))

    # Fetch the customer's cart items
    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    
    # Calculate total time
    total_time = sum(item.time_required * item.quantity for item in cart_items)
    total_price = sum(item.price * item.quantity for item in cart_items)
    # Fetch the customer's username
    customer = Customer.query.get(customer_id)
    username = customer.username if customer else "Guest"

    # Check if the cart is empty
    if not cart_items:
        flash("Your cart is empty.", "info")

    return render_template('cart.html', cart_items=cart_items, username=username, total_time=total_time,total_price=total_price)
@app.route('/remove_item/<int:item_id>', methods=['GET', 'POST'])
def remove_item(item_id):
    # Logic to remove the item from the cart
    cart_item = Cart.query.get(item_id)
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed successfully!', 'success')
    else:
        flash('Item not found!', 'danger')
    return redirect(url_for('view_cart'))
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    customer_id = session.get('customer_id')  # Replace with actual session handling
    if not customer_id:
        flash('Please log in to checkout', 'warning')
        return redirect(url_for('login'))  # Assuming there's a login route

    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    total = sum(item.price * item.quantity for item in cart_items)  # Assuming price and quantity exist
    time = sum(item.service.timerequired * item.quantity for item in cart_items if item.service)

    if request.method == 'POST':
        flash('Checkout successful!', 'success')
        # You might want to clear the cart or process the order here
        return redirect(url_for('view_cart'))  # Redirect to a relevant page

    return render_template('checkout.html', cart_items=cart_items, total=total, time=time)

@app.route('/error')
def error():
    return render_template('error.html')
if __name__ == '__main__':
    app.run(debug=True)
# # Route for Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')
@app.route('/add_service', methods=['POST'])
def add_service():
    # Get data from the form
    service_name = request.form.get('service_name')
    description = request.form.get('description')
    price = request.form.get('price')
    time_required = request.form.get('time_required')

    # Validate input (optional but recommended)
    if not (service_name and description and price and time_required):
        flash('All fields are required!', 'error')
        return redirect(url_for('admin_dashboard'))  
    # Create a new Service instance
    new_service = Service(
        name=service_name,
        description=description,
        price=int(price),
        timerequired=int(time_required),
        allowed=True,
        status='Confrimed'
    )

    # Add to the database
    db.session.add(new_service)
    db.session.commit()

    # Redirect to the admin dashboard with a success message
    flash('Service added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))  

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    # Ensure the customer is logged in
    customer_id = session.get('customer_id')

    if not customer_id:
        flash("Please log in to confirm the order.", "warning")
        return redirect(url_for('login'))

    # Fetch customer and cart items
    customer = Customer.query.get(customer_id)
    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('view_cart'))

    orders = []
    total_price = 0  # Initialize total_price variable

    try:
        # Calculate total price for the service request and create ServiceRequest for each item
        for item in cart_items:
            total_price += item.quantity * item.price  
            professionals = Professional.query.filter_by(service_type=item.service_name)
            professional = professionals.first()  # Get the first matching professional
            quantity=item.quantity
        
            # Create a ServiceRequest summarizing the customer's request
            service_request = ServiceRequest(
                customer_id=customer_id,
                professional_id=professional.id if professional else None,  # Assign professional ID if available
                service_id=item.service_id,
                pincode=customer.pincode,  
                status="Pending",
                work_completed=False,
                date_of_request=datetime.utcnow().replace(microsecond=0),
                customer_approval=False,
                professional_approval=False
            )
            db.session.add(service_request)
            db.session.commit()  
            # Save each cart item as an Order
            order = Order(
                customer_id=customer_id,
                service_id=item.service_id,
                provider_id=professional.id if professional else None,  # Assign provider ID if available
                date_requested=datetime.utcnow().replace(microsecond=0),
                status="Pending",
                work_completed=False,  # Professional decision pending
                notes=f"Order for {item.service_name}",
                provider_notes=None,
                quantity=quantity
            )
            db.session.add(order)
            orders.append(order)

        db.session.commit()  # Commit all orders
        flash("Order confirmed successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error during order confirmation: {str(e)}", "danger")
        return redirect(url_for('view_cart'))  # Redirect if there's an error

    # Clear the cart after confirming the order
    try:
        Cart.query.filter_by(customer_id=customer_id).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error clearing cart: {str(e)}", "danger")

    # Render the order transcript for the customer
    return render_template('confirm_order.html', orders=orders, total_price=total_price)


@app.route('/booking_history')
def booking_history():
    # Ensure the customer is logged in by checking the session
    customer_id = session.get('customer_id')  # Retrieve customer ID from session

    if not customer_id:
        flash("Please log in to view your booking history.", "warning")
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    # Fetch all orders for the logged-in customer
    orders = Order.query.filter_by(customer_id=customer_id).all()

    if not orders:
        flash("You have no previous orders.", "info")

    # Render the booking history template with the orders
    return render_template('booking_history.html', orders=orders)

@app.route('/services', methods=['GET', 'POST'])
def services():
    search_query = request.form.get('search', '').strip()  # Get the search query

    # Fetch only confirmed services
    services_query = Service.query.filter(Service.status == 'Confrimed')

    if search_query:
        # Apply the search filter if there is a search query
        services_query = services_query.filter(Service.name.ilike(f'%{search_query}%'))

    # Execute the query and get the list of services
    services = services_query.all()

    return render_template(
        'services.html', 
        services=services, 
        search_query=search_query
    )

    
@app.route('/professional_dashboard', methods=['GET'])
def professional_dashboard():
    # Check for professional ID in session or request args
    professional_id = session.get('professional_id') or request.args.get('professional_id')

    if not professional_id:  # Redirect to login if no ID is found
        return redirect(url_for('login'))

    # Fetch the professional details
    professional = Professional.query.filter_by(id=professional_id).first()
    username=professional.username
    if not professional:
        return "Professional not found", 404  # Handle non-existent professional
    
    if professional.blocked:
        return "Your account is blocked. Please contact support.", 403  # Handle blocked professionals

    # Fetch pending service requests assigned to this professional
    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id, status='Pending').all()

    # Render the dashboard template
    return render_template('professional_dashboard.html', service_requests=service_requests,username=username)

# Ensure session setup (if using sessions)
app.secret_key = 'your_secret_key'  

@app.route('/update_request/<action>/<int:request_id>', methods=['POST'])
def update_request(action, request_id):
    request = ServiceRequest.query.get_or_404(request_id)
    if action == 'confirm':
        request.status = 'Confirmed'
        # Update the customer's booking history
        order = Order.query.filter_by(customer_id=request.customer_id,provider_id=request.professional_id, status='Pending').first()
        if order:
            order.status = 'Confirmed'
            db.session.commit()
        flash(f"Request confirmed by {request.professional.name}.", 'success')
    elif action == 'cancel':
        order = Order.query.filter_by(customer_id=request.customer_id,provider_id=request.professional_id, status='Pending').first()
        request.status = 'Cancelled'
        order.status='Rejected'
        flash(f"Request cancelled.", 'success')
    db.session.commit()
    return redirect(url_for('professional_dashboard'))  # Redirect back to the professional dashboard


@app.route('/service_history', methods=['GET'])
def service_history():
    professional_id = session.get('professional_id')  # Replace with actual session handling
    
    if not professional_id:
        flash("Please log in to view your service history.", "warning")
        return redirect(url_for('login'))

    # Query all service requests assigned to this professional
    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id).all()

    # Fetch feedback for each service request (if any)
    for request in service_requests:
        feedback = Feedback.query.filter_by(service_id=request.service_id).first()
        request.feedback = feedback  # Attach the feedback object to the request

    return render_template(
        'service_history.html',
        service_requests=service_requests
    )



@app.route('/mark_complete_customer/<int:request_id>', methods=['POST'])
def mark_complete_customer(request_id):
    service_request = ServiceRequest.query.get(request_id)
    orders=Order.query.get(request_id)
    if service_request:
        if service_request.status=='Confirmed':
            service_request.customer_approval = True
            if service_request.customer_approval and service_request.professional_approval:
                service_request.status = 'Completed'
                service_request.date_completed =datetime.utcnow().replace(microsecond=0)
                service_request.work_completed=True
                orders.status='Completed'
                orders.work_completed=True
                orders.date_completed = datetime.utcnow().replace(microsecond=0)
            db.session.commit()
    return redirect(url_for('booking_history'))

@app.route('/mark_complete_professional/<int:request_id>', methods=['POST'])
def mark_complete_professional(request_id):
    service_request = ServiceRequest.query.get(request_id)
    orders=Order.query.get(request_id)
    if service_request:
        if service_request.status=='Confirmed':
            service_request.professional_approval = True
            if service_request.customer_approval and service_request.professional_approval:
                service_request.status = 'Completed'
                service_request.work_completed=True
                service_request.date_completed = datetime.utcnow()
                orders.status='Completed'
                orders.work_completed=True
                orders.date_completed = datetime.utcnow()
            db.session.commit()
    return redirect(url_for('service_history'))
@app.route('/joining_requests', methods=['GET'])
def joining_requests():
    pending_requests = Professional.query.filter_by(is_approved=False).all()
    return render_template('joining_requests.html', pending_requests=pending_requests)
@app.route('/approve_request/<int:professional_id>', methods=['POST'])
def approve_request(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.is_approved = True
    professional.date_created = datetime.utcnow().replace(microsecond=0)
    db.session.commit()
    flash(f"Professional '{professional.name}' approved successfully!", "success")
    return redirect(url_for('joining_requests'))

@app.route('/reject_request/<int:professional_id>', methods=['POST'])
def reject_request(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    db.session.delete(professional)
    db.session.commit()
    flash(f"Professional '{professional.name}' rejected and removed.", "danger")
    return redirect(url_for('joining_requests'))
@app.route('/list_of_professionals', methods=['GET'])
def list_of_professionals():
    professionals = Professional.query.filter_by(is_approved=True).all()
    return render_template('list_of_professionals.html', professionals=professionals)
@app.route('/lservices', methods=['GET'])
def lservices():
    services = Service.query.all()  
    return render_template('lservices.html', services=services)
@app.route('/bookings', methods=['GET'])
def bookings():
    bookings = Order.query.all()  
    return render_template('bookings.html', bookings=bookings)
@app.route('/create_service_request', methods=['GET', 'POST'])
def create_service_request():
    if request.method == 'POST':
        # Get form data
        service_name = request.form.get('service_name')
        description = request.form.get('description')
        
        # Get the customer ID from session (assuming customer is logged in)
        customer_id = session.get('customer_id')  # Ensure that the customer is logged in

        if not customer_id:
            flash('You must be logged in to submit a service request!', 'error')
            return redirect(url_for('login'))  # Redirect to login if no customer_id in session
        
        # Validate customer existence
        customer = Customer.query.get(customer_id)
        if not customer:
            flash('Invalid customer ID!', 'error')
            return redirect(url_for('customer_dashboard'))
        
        # Validate service name and description (optional but good practice)
        if not service_name or not description:
            flash('Service name and description are required!', 'error')
            return redirect(url_for('create_service_request'))
        
        # Create new service request (status = Pending initially)
        new_request = Service(
            name=service_name,
            description=description,  
            price=0,  # Price to be filled by admin
            timerequired=0,  # Time required to be filled by admin
            allowed=False,  # Pending approval
            status='Pending'  # Pending status
        )

        # Add the request to the database
        try:
            db.session.add(new_request)
            db.session.commit()
            flash('Your service request has been submitted and is pending approval!', 'success')
            return redirect(url_for('customer_dashboard'))  # Redirect to customer dashboard after submission
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('customer_dashboard'))
    
    # If GET request, render the form
    return render_template('create_service_request.html')

@app.route('/admin/service_requests')
def admin_service_requests():
    # Admin view to review all service requests
    requests = Service.query.filter_by(allowed=False).all()

    return render_template('admin_service_requests.html', requests=requests)
@app.route('/admin/review_request/<int:request_id>', methods=['GET', 'POST'])
def admin_review_request(request_id):
    service_request = Service.query.get(request_id)

    if not service_request:
        flash("Service request not found", "error")
        return redirect(url_for('admin_service_requests'))

    # Handle POST request to accept or deny
    if request.method == 'POST':
        price = request.form.get('price')
        timerequired = request.form.get('timerequired')
        description = request.form.get('description')
        action = request.form.get('action')  # Get the action (accept/deny)

        # Ensure all required fields are filled before processing
        if price and timerequired and description:
            service_request.price = float(price)
            service_request.timerequired = int(timerequired)
            service_request.description = description

            if action == 'accept':
                service_request.status = 'Confirmed'
                service_request.allowed = True
                flash(f"Request for {service_request.name} has been accepted.", "success")
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f"An error occurred while accepting: {str(e)}", "error")
            elif action == 'deny':
                # If 'deny' is clicked, delete the service request from the database
                try:
                    db.session.delete(service_request)
                    db.session.commit()
                    flash(f"Request for {service_request.name} has been denied and removed.", "error")
                    return redirect(url_for('admin_service_requests'))  # Redirect after deletion
                except Exception as e:
                    db.session.rollback()
                    flash(f"An error occurred while deleting: {str(e)}", "error")

            return redirect(url_for('admin_service_requests'))
        else:
            flash("Please fill in all required fields.", "error")

    return render_template('admin_review_request.html', service_request=service_request)

@app.route('/admin/delete_service/<int:service_id>', methods=['GET', 'POST'])
def delete_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        flash("Service not found", "error")
        return redirect(url_for('lservices'))

    try:
        db.session.delete(service)
        db.session.commit()
        flash("Service deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")

    return redirect(url_for('lservices'))
@app.route('/admin/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        flash("Service not found", "error")
        return redirect(url_for('lservices'))  
    if request.method == 'POST':
        # Update service data
        service.name = request.form['name']
        service.description = request.form['description']
        service.price = request.form['price']
        service.timerequired = request.form['timerequired']
        db.session.commit()
        flash("Service updated successfully.", "success")
        return redirect(url_for('lservices'))

    return render_template('edit_service.html', service=service)
@app.route('/feedback/<int:order_id>', methods=['GET', 'POST'])
def feedback(order_id):
    if 'customer_id' not in session:
        flash("Please log in to submit feedback.", "error")
        return redirect(url_for('login'))

    customer_id = session['customer_id']  # Retrieve logged-in customer's ID

    # Retrieve the specific order
    order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
    if not order:
        flash("Order not found or unauthorized access.", "error")
        return redirect(url_for('booking_history'))

    # Check if feedback has already been submitted
    if order.feedback_given:
        flash("Feedback has already been submitted for this order.", "info")
        return redirect(url_for('booking_history'))

    service_id = order.service_id
    provider_id = order.provider_id

    # Ensure service and provider information are valid
    if not service_id or not provider_id:
        flash("Service or provider information is missing for this order.", "error")
        return redirect(url_for('services'))

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment', '')

        # Validate the rating
        if not rating or int(rating) not in range(1, 6):
            flash("Please provide a valid rating between 1 and 5.", "error")
            return render_template('feedback.html', order=order)

        feedback = Feedback(
            customer_id=customer_id,
            service_id=service_id,
            professional_id=provider_id,
            rating=int(rating),
            comment=comment,
            feedback_given=True
        )

        try:
            # Add feedback and update order feedback status
            db.session.add(feedback)
            order.feedback_given = True  # Update the feedback status for the order
            db.session.commit()
            flash("Your feedback has been submitted successfully!", "success")
            return redirect(url_for('booking_history'))  # Redirect to booking history
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while submitting feedback: {str(e)}", "error")

    return render_template('feedback.html', order=order)


@app.route('/feedbacks')
def feedbacks():
    # Fetch all feedbacks along with related customer, service, and professional details
    feedbacks = db.session.query(Feedback, Customer, Service, Professional) \
        .join(Customer, Customer.id == Feedback.customer_id) \
        .join(Service, Service.id == Feedback.service_id) \
        .join(Professional, Professional.id == Feedback.professional_id) \
        .all()

    return render_template('view_feedback.html', feedbacks=feedbacks)
@app.route('/block_customer/<int:customer_id>')
def block_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if customer.is_admin:
        flash("You cannot block an admin.", "error")
        return redirect(url_for('feedbacks'))

    customer.blocked = True
    try:
        db.session.commit()
        flash(f"Customer {customer.name} has been blocked.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while blocking the customer: {str(e)}", "error")
    return redirect(url_for('feedbacks'))
@app.route('/unblock_customer/<int:customer_id>')
def unblock_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if customer.is_admin:
        flash("You cannot unblock an admin.", "error")
        return redirect(url_for('feedbacks'))

    customer.blocked = False
    try:
        db.session.commit()
        flash(f"Customer {customer.name} has been unblocked.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while unblocking the customer: {str(e)}", "error")
    
    return redirect(url_for('feedbacks'))

# Route to block a professional
@app.route('/block_professional/<int:professional_id>')
def block_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    if not professional.blocked:  # Ensure professional is not already blocked
        professional.blocked = True
        db.session.commit()
    return redirect(url_for('list_of_professionals'))

# Route to unblock a professional
@app.route('/unblock_professional/<int:professional_id>')
def unblock_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    if professional.blocked:  # Ensure professional is blocked
        professional.blocked = False
        db.session.commit()
    return redirect(url_for('list_of_professionals'))

# Route to list all professionals
@app.route('/list_of_professionals')
def list_professionals():
    professionals = Professional.query.all()
    return render_template('list__of_professionals.html', professionals=professionals)

@app.route('/request_summary')
def request_summary():
    customer_id=session.get('customer_id')
    # Count total, completed, and pending requests
    total_requests = Order.query.filter_by(customer_id=customer_id).count()
    completed_requests = Order.query.filter_by(customer_id=customer_id,status='Completed').count()
    pending_requests = Order.query.filter_by(customer_id=customer_id,status='Pending').count()
    rejected_requests = Order.query.filter_by(customer_id=customer_id,status='Rejected').count()

    # Pass data to the template
    return render_template('request_summary.html', 
                           total_requests=total_requests, 
                           completed_requests=completed_requests, 
                           pending_requests=pending_requests,
                           rejected_requests=rejected_requests)
@app.route('/professional_summary')
def professional_summary():
    # Ensure professional is logged in
    professional_id = session.get('professional_id')  
    if not professional_id:
        flash("Please log in to view your summary.", "warning")
        return redirect(url_for('login'))

    # Count total, completed, pending, and cancelled requests for the logged-in professional
    total_requests = ServiceRequest.query.filter_by(professional_id=professional_id).count()
    completed_requests = ServiceRequest.query.filter_by(professional_id=professional_id, status='Completed').count()
    pending_requests = ServiceRequest.query.filter_by(professional_id=professional_id, status='Pending').count()
    cancelled_requests = ServiceRequest.query.filter_by(professional_id=professional_id, status='Cancelled').count()

    # Pass data to the template
    return render_template('professional_summary.html', 
                           total_requests=total_requests, 
                           completed_requests=completed_requests, 
                           pending_requests=pending_requests,
                           cancelled_requests=cancelled_requests)
@app.route('/customer/profile', methods=['GET', 'POST'])
def customer_profile():
    # Ensure customer is logged in
    customer_id = session.get('customer_id')  # Fetch logged-in customer ID
    if not customer_id:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('login'))

    # Fetch the customer details
    customer = Customer.query.get(customer_id)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Update customer details
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        customer.pincode = request.form.get('pincode')
        password = request.form.get('password')

        if password:  # Update password only if provided
            customer.password = password

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating profile. Please try again.", "danger")

    return render_template('customer_profile.html', customer=customer)
@app.route('/professional/profile', methods=['GET', 'POST'])
def professional_profile():
    # Ensure professional is logged in
    professional_id = session.get('professional_id')  # Fetch logged-in professional ID
    if not professional_id:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('login'))

    # professional details
    professional = Professional.query.get(professional_id)
    if not professional:
        flash("Professional not found.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Update professional details
        professional.name = request.form.get('name')
        professional.email = request.form.get('email')
        professional.address = request.form.get('address')
        professional.pincode = request.form.get('pincode')
        professional.experience = request.form.get('experience')
        professional.description = request.form.get('description')
        password = request.form.get('password')

        if password:  # Update password only if provided
            professional.password = password

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating profile. Please try again.", "danger")

    return render_template('professional_profile.html', professional=professional)
@app.route('/service_request/view/<int:request_id>', methods=['GET'])
def view_service_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    customer = service_request.customer
    return render_template('view_service_request.html', service_request=service_request, customer=customer)

@app.route('/admin_summary', methods=['GET'])
def admin_summary():
    # Data for User Statistics
    total_customers = Customer.query.filter_by(is_admin=False).count()
    total_professionals = Professional.query.count()
    total_users = total_customers+total_professionals
    # Data for Order Statistics
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(status='Completed').count()
    rejected_orders = Order.query.filter_by(status='Rejected').count()
    pending_orders=Order.query.filter_by(status='Pending').count()
    return render_template(
        'admin_summary.html',
        total_users=total_users,
        total_customers=total_customers,
        total_professionals=total_professionals,
        total_orders=total_orders,
        completed_orders=completed_orders,
        rejected_orders=rejected_orders,
        pending_orders=pending_orders
    )
@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('index'))  

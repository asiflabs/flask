from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # Import datetime to handle timestamps

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)

# Set a strong secret key for session management
app.config['SECRET_KEY'] = 'asif007'  # Replace this with a strong secret key

# Configure the SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)  # Initialize the db object

# Create the EditHistory model
class EditHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)  # Link to Item
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to User
    change_time = db.Column(db.DateTime, default=datetime.utcnow)  # Track the time of change
    action = db.Column(db.String(100), nullable=False)  # Store action: 'Added' or 'Edited'
    
    item = db.relationship('Item', backref='edit_history', lazy=True)  # Link to the Item model
    user = db.relationship('User', backref='edit_history', lazy=True)  # Link to the User model

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Item Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Use PBKDF2 with SHA256 for hashing the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose another one.", "danger")
            return redirect(url_for('register'))
        
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Login failed. Please check your credentials.", "danger")
    
    return render_template('login.html')

# Home Page - Show all items
@app.route('/')
@login_required
def index():
    items = Item.query.all()  # Get all items from the database
    return render_template('index.html', items=items)

# Add Item Route
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        
        # Create the new item
        new_item = Item(name=name, quantity=quantity)
        db.session.add(new_item)
        db.session.commit()

        # Create a new EditHistory record for this item
        edit_history = EditHistory(item_id=new_item.id, user_id=session['user_id'], action='Added')
        db.session.add(edit_history)
        db.session.commit()

        flash("Item added successfully!", "success")
        return redirect(url_for('index'))
    
    return render_template('add.html')


# Edit Item Route
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        # Update the item's name and quantity
        item.name = request.form['name']
        item.quantity = request.form['quantity']
        db.session.commit()

        # Create a new EditHistory record for this item edit
        edit_history = EditHistory(item_id=item.id, user_id=session['user_id'], action='Edited')
        db.session.add(edit_history)
        db.session.commit()

        flash("Item updated successfully!", "success")
        return redirect(url_for('index'))
    
    return render_template('edit.html', item=item)


# Delete Item Route
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted successfully!", "success")
    return redirect(url_for('index'))

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    flash("You have been logged out.")
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    with app.app_context():  # Start the application context
        db.create_all()  # Create all the tables
    app.run(debug=True)

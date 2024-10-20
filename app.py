# Import necessary libraries and modules
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, NumberRange
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
import random
import threading
import time

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your actual secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/stockappdatabase'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for performance
db = SQLAlchemy(app)  # Initialize the SQLAlchemy object

# Database model for users
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)  # Unique identifier for the user
    user_name = db.Column(db.String(100), unique=True, nullable=False)  # Username
    full_name = db.Column(db.String(100), nullable=False)  # Full name
    email = db.Column(db.String(100), unique=True, nullable=False)  # Email
    passwrd = db.Column(db.String(100), nullable=False)  # Password
    acc_type = db.Column(db.String(10), nullable=False)  # Account type (e.g., 'user', 'admin')
    balance = db.Column(db.Numeric(10, 2), default=0)  # User's balance

# Database model for stocks
class Stock(db.Model):
    stock_id = db.Column(db.Integer, primary_key=True)  # Unique identifier for the stock
    company_name = db.Column(db.String(100), nullable=False)  # Name of the company
    ticker = db.Column(db.String(10), nullable=False)  # Stock ticker symbol
    stock_quantity = db.Column(db.Integer, nullable=False)  # Number of stocks owned
    initial_price = db.Column(db.Numeric(10, 2), nullable=False)  # Initial purchase price
    current_price = db.Column(db.Numeric(10, 2), nullable=False)  # Current market price

# Database model for contact messages
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for the message
    name = db.Column(db.String(100), nullable=False)  # Sender's name
    email = db.Column(db.String(100), nullable=False)  # Sender's email
    message = db.Column(db.Text, nullable=False)  # Content of the message


# Form for adding stocks
class StockForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])  # Company name input
    ticker = StringField('Ticker', validators=[DataRequired()])  # Ticker symbol input
    current_price = DecimalField('Current Price', validators=[DataRequired()], places=2)  # Current price input
    submit = SubmitField('Add Stock')  # Submit button for the form

class DepositForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired()])  # User ID input


    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])  # Deposit amount input
    submit = SubmitField('Deposit')  # Submit button for the form
class WithdrawForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired()])  # User ID input
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])  # Withdrawal amount input
    submit = SubmitField('Withdraw')  # Submit button for the form
# Form for contact messages
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])  # Name input
    email = StringField('Email', validators=[DataRequired(), Email()])  # Email input
    message = TextAreaField('Message', validators=[DataRequired()])  # Message content input
    submit = SubmitField('Send Message')  # Submit button for the form


# Route for the portfolio page (home page)
@app.route('/')
def portfolio():
    page = request.args.get('page', 1, type=int)  # Get the page number for pagination
    stocks_per_page = 10  # Number of stocks to display per page
    stocks = Stock.query.paginate(page=page, per_page=stocks_per_page, error_out=False)  # Paginate stock records
    return render_template('portfolio.html', stocks=stocks)  # Pass paginated stocks to the template



# Route for the stock management page
@app.route('/stock', methods=['GET', 'POST'])
def stock():
    form = StockForm()  # Initialize the stock form
    if form.validate_on_submit():  # Check if the form is submitted and valid
        new_stock = Stock(
            company_name=form.company_name.data,
            ticker=form.ticker.data,
            stock_quantity=0,  # Set to zero for new stocks
            initial_price=form.current_price.data,
            current_price=form.current_price.data
        )
        db.session.add(new_stock)  # Add the new stock to the session
        db.session.commit()  # Commit the session to save changes
        flash('Stock added successfully!', 'success')  # Show success message
        return redirect(url_for('stock'))  # Redirect to the stock page

    page = request.args.get('page', 1, type=int)  # Get the page number for pagination
    stocks_per_page = 10  # Number of stocks to display per page
    stocks = Stock.query.paginate(page=page, per_page=stocks_per_page, error_out=False)  # Paginate stock records
    return render_template('stock.html', form=form, stocks=stocks)  # Render the stock management template

# Route for the contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()  # Initialize the contact form
    if form.validate_on_submit():  # Check if the form is submitted and valid
        new_message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            message=form.message.data
        )
        db.session.add(new_message)  # Add the new message to the session
        db.session.commit()  # Commit the session to save changes
        flash('Message sent successfully!', 'success')  # Show success message
        return redirect(url_for('contact'))  # Redirect to the contact page
    return render_template('contact.html', form=form)  # Render the contact template

# Route for the trade page
@app.route('/trade')
def trade():
    return render_template('trade.html')  # Render the trade template

# Route for deleting a stock
@app.route('/delete_stock/<int:stock_id>')
def delete_stock(stock_id):
    stock_to_delete = Stock.query.get_or_404(stock_id)  # Retrieve the stock or return a 404 error
    db.session.delete(stock_to_delete)  # Delete the stock from the session
    db.session.commit()  # Commit the session to save changes
    flash('Stock deleted successfully!', 'success')  # Show success message
    return redirect(url_for('stock'))  # Redirect to the stock page

# Function to randomly update stock prices
def update_stock_prices():
    with app.app_context():  # Ensure we are in the app context
        while True:
            stocks = Stock.query.all()  # Get all stocks
            for stock in stocks:
                # Change current price randomly by -10 to 10
                change = Decimal(random.uniform(-10, 10))  # Convert change to Decimal
                new_price = max(stock.current_price + change, 0)  # Ensure price doesn't go negative
                stock.current_price = round(new_price, 2)  # Update current price
            db.session.commit()  # Commit changes to the database
            time.sleep(10)  # Wait for 10 seconds before the next update

# Start the price update thread
threading.Thread(target=update_stock_prices, daemon=True).start()

# Application entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)  # Run the application in debug mode

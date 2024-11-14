from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, NumberRange
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
import MySQLdb.cursors
from sqlalchemy import text
from decimal import Decimal
import re
import random
import threading
import time
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash  # Importing for password hashing

# Define a constant for the repeated message
FILL_FORM_MSG = 'Please fill out the form!'

# Set up Flask application and configuration
app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24).hex()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'geeklogin'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:password@localhost/geeklogin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up MySQL and SQLAlchemy
mysql = MySQL(app)
db = SQLAlchemy(app)

# FlaskForm for stock management
class StockForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    ticker = StringField('Ticker Symbol', validators=[DataRequired()])
    initial_price = DecimalField('Initial Price', validators=[DataRequired(), NumberRange(min=0)])
    current_price = DecimalField('Current Price', validators=[DataRequired(), NumberRange(min=0)]) 
    submit = SubmitField('Add Stock')

# Database model for stocks
class Stock(db.Model):
    __tablename__ = 'stocks'
    stock_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    initial_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_price = db.Column(db.Numeric(10, 2), nullable=False)

# FlaskForm for contact messages
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

# Database model for contact messages
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# User login route
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account and check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)


# Admin login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account and check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['is_admin'] = True  # Add this line
            return redirect(url_for('admin_dashboard'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('admin_login.html', msg=msg)

@app.route('/admin/dashboard')
def admin_dashboard():

    users = db.session.execute(text('SELECT * FROM accounts')).fetchall()

    stocks = db.session.execute(text('SELECT * FROM stocks')).fetchall()

    return render_template('admin_dashboard.html', users=users, stocks=stocks)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and all(field in request.form for field in ['username', 'password', 'email']):
        username, password, email = request.form['username'], request.form['password'], request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = FILL_FORM_MSG
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO accounts (username, password, email, balance) VALUES (%s, %s, %s, 0)', (username, hashed_password, email))
            mysql.connection.commit()
            flash('You have successfully registered!')
            return redirect(url_for('login'))
    elif request.method == 'POST':
        msg = FILL_FORM_MSG
    return render_template('register.html', msg=msg)


# Admin registration route
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    msg = ''
    if request.method == 'POST' and all(field in request.form for field in ['username', 'password', 'email']):
        username, password, email = request.form['username'], request.form['password'], request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Admin account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO admins (username, password, email) VALUES (%s, %s, %s)', (username, hashed_password, email))
            mysql.connection.commit()
            flash('Admin registration successful!')
            return redirect(url_for('admin_login'))
    else:
        msg = FILL_FORM_MSG
    return render_template('admin_register.html', msg=msg)


# Stock management route for adding/removing stocks
@app.route('/admin/add_stock', methods=['GET', 'POST'])
def add_stock():
    form = StockForm()  # Initialize the form

    # Handle form submission
    if form.validate_on_submit():
        company_name = form.company_name.data
        ticker = form.ticker.data
        initial_price = form.initial_price.data
        current_price = form.current_price.data

        # Check if the stock already exists
        existing_stock = Stock.query.filter_by(ticker=ticker).first()

        if existing_stock:
            flash('Stock with this ticker already exists!', 'danger')
            return redirect(url_for('add_stock'))

        # Add the new stock to the database
        new_stock = Stock(
            company_name=company_name,
            ticker=ticker,
            initial_price=initial_price,
            current_price=current_price
        )
        db.session.add(new_stock)
        db.session.commit()

        flash('Stock added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))  # Redirect to the dashboard or another page

    # Render the template and pass the form
    return render_template('add_stock.html', form=form)


@app.route('/admin/remove_stock/<int:stock_id>', methods=['POST'])
def remove_stock(stock_id):
    stock_to_remove = Stock.query.get_or_404(stock_id)
    
    # Remove associated user stocks before removing the stock itself
    user_stocks = UserStock.query.filter_by(stock_id=stock_id).all()
    for user_stock in user_stocks:
        db.session.delete(user_stock)
    
    try:
        db.session.delete(stock_to_remove)
        db.session.commit()
        flash(f'Successfully removed stock: {stock_to_remove.company_name} ({stock_to_remove.ticker})', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing stock: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/index', methods=['GET'])
def index():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch user balance
        cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
        result = cursor.fetchone()
        user_balance = result['balance'] if result else 0

        # Fetch user stocks
        cursor.execute('''
            SELECT s.stock_id, s.company_name, s.ticker, s.current_price, COALESCE(us.stock_quantity, 0) AS stock_quantity
            FROM stocks s
            LEFT JOIN user_stocks us ON s.stock_id = us.stock_id AND us.user_id = %s
        ''', (user_id,))
        user_stocks = cursor.fetchall()
        return render_template('index.html', balance=user_balance, stocks=user_stocks)
    return redirect(url_for('login'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'loggedin' in session:
        user_id = session['id']
        amount = float(request.form['amount'])

        if amount > 0:
            cursor = mysql.connection.cursor()
            cursor.execute('UPDATE accounts SET balance = balance + %s WHERE id = %s', (amount, user_id))
            mysql.connection.commit()
            return redirect(url_for('index'))
        else:
            msg = 'Please enter a positive amount!'
            return render_template('index.html', msg=msg)

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'loggedin' in session:
        user_id = session['id']
        amount = request.form['amount']

        # Fetch the current balance
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
        result = cursor.fetchone()

        if result:
            current_balance = result['balance']
            amount = Decimal(amount)

            if amount > current_balance:
                return render_template('index.html', msg='Not enough funds!', balance=current_balance)

            # Update the balance
            new_balance = current_balance - amount
            cursor.execute('UPDATE accounts SET balance = %s WHERE id = %s', (new_balance, user_id))
            mysql.connection.commit()

            return render_template('index.html', msg='Withdrawal successful!', balance=new_balance)

    return redirect(url_for('login'))
                                                                                            
@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
    form = StockForm()

    if 'loggedin' in session:
        user_id = session['id']

        # Check if the form is submitted and valid to add a new stock
        if form.validate_on_submit():
            new_stock = Stock(
                company_name=form.company_name.data,
                ticker=form.ticker.data,
                initial_price=form.initial_price.data,
                current_price=form.current_price.data,
            )
            db.session.add(new_stock)
            db.session.commit()
            flash('Stock added successfully!', 'success')
            return redirect(url_for('stocks'))

        # Get the current page number for pagination
        page = request.args.get('page', 1, type=int)
        stocks_per_page = 10

        # Fetch paginated stocks
        paginated_stocks = Stock.query.paginate(page=page, per_page=stocks_per_page, error_out=False)
        all_stocks = paginated_stocks.items

        # Get user's owned stock quantities from the `user_stocks` table using raw SQL query
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT stock_id, stock_quantity FROM user_stocks WHERE user_id = %s', (user_id,))
        user_stocks = cursor.fetchall()

        # Create a dictionary for user's stock quantities
        user_stock_dict = {stock['stock_id']: stock['stock_quantity'] for stock in user_stocks}

        # Add the user's quantity for each stock
        for stock in all_stocks:
            stock.user_quantity = user_stock_dict.get(stock.stock_id, 0)  # Set to 0 if not owned

        return render_template(
            'stocks.html',
            form=form,
            stocks=all_stocks,
            page=page,
            total=paginated_stocks.total,
            per_page=stocks_per_page
        )

    # Redirect to login if not logged in
    flash('You must be logged in to view this page.', 'warning')
    return redirect(url_for('login'))

@app.route('/transactions')
def transactions():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Query to fetch transaction history
            cursor.execute('''
                SELECT s.company_name, t.transaction_type, t.shares, t.date, t.price
                FROM transactions t
                JOIN stocks s ON t.stock_id = s.stock_id
                WHERE t.user_id = %s
                ORDER BY t.date DESC
            ''', (user_id,))
            
            transactions = cursor.fetchall()
            
            # Check if there are any transactions to display
            if not transactions:
                flash('No transactions found.', 'info')
            
            return render_template('transactions.html', transactions=transactions)

        except Exception as e:
            flash(f'An error occurred while fetching transactions: {str(e)}', 'danger')
            return redirect(url_for('stocks')) 

    flash('You must be logged in to view transactions.', 'warning')
    return redirect(url_for('login'))


# Buy stock route
@app.route('/buy_stock/<int:stock_id>', methods=['POST'])
def buy_stock(stock_id):
    if 'loggedin' in session:
        user_id = session['id']
        quantity = int(request.form['quantity'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Fetch stock details
            cursor.execute('SELECT current_price, company_name FROM stocks WHERE stock_id = %s', (stock_id,))
            stock = cursor.fetchone()
            
            if stock:
                current_price = Decimal(stock['current_price'])
                company_name = stock['company_name'] 
                total_cost = current_price * quantity

                # Check user's current balance
                cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
                result = cursor.fetchone()
                current_balance = result['balance']
                if total_cost > current_balance:
                    flash('Not enough funds!', 'danger')
                    return redirect(url_for('stocks'))

                # Update user's balance
                new_balance = current_balance - total_cost
                cursor.execute('UPDATE accounts SET balance = %s WHERE id = %s', (new_balance, user_id))

                # Update user_stocks or insert if it doesn't exist
                cursor.execute('INSERT INTO user_stocks (user_id, stock_id, stock_quantity) '
                               'VALUES (%s, %s, %s) '
                               'ON DUPLICATE KEY UPDATE stock_quantity = stock_quantity + %s', 
                               (user_id, stock_id, quantity, quantity))

                # Log the transaction
                cursor.execute(
                    'INSERT INTO transactions (user_id, stock_id, company_name, transaction_type, shares, price, date) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (user_id, stock_id, company_name, 'buy', quantity, current_price, datetime.now())
                )

                mysql.connection.commit()
                flash('Purchase successful!', 'success')
                return redirect(url_for('stocks'))

        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of error
            flash(f'An error occurred: {str(e)}', 'danger')

    flash('You must be logged in to perform this action.', 'warning')
    return redirect(url_for('login'))

# Sell stock route
@app.route('/sell_stock/<int:stock_id>', methods=['POST'])
def sell_stock(stock_id):
    if 'loggedin' in session:
        user_id = session['id']
        quantity = int(request.form['quantity'])

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Fetch shares owned and stock details
            cursor.execute(
                'SELECT us.stock_quantity, s.current_price, s.company_name FROM stocks s '
                'JOIN user_stocks us ON s.stock_id = us.stock_id '
                'WHERE s.stock_id = %s AND us.user_id = %s', (stock_id, user_id)
            )
            stock = cursor.fetchone()

            if stock:
                shares_owned = stock['stock_quantity']
                current_price = Decimal(stock['current_price'])
                company_name = stock['company_name']
                total_revenue = current_price * quantity

                # Check if user has enough shares to sell
                if quantity > shares_owned:
                    flash('Not enough shares to sell!', 'danger')
                    return redirect(url_for('stocks'))

                # Update user balance
                cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
                balance_result = cursor.fetchone()
                if balance_result:
                    user_balance = Decimal(balance_result['balance'])
                    new_balance = user_balance + total_revenue

                    # Update balance in the accounts table
                    cursor.execute('UPDATE accounts SET balance = %s WHERE id = %s', (new_balance, user_id))

                    # Update shares owned or remove entry if all shares sold
                    new_shares_owned = shares_owned - quantity
                    if new_shares_owned > 0:
                        cursor.execute(
                            'UPDATE user_stocks SET stock_quantity = %s WHERE stock_id = %s AND user_id = %s', 
                            (new_shares_owned, stock_id, user_id)
                        )
                    else:
                        cursor.execute(
                            'DELETE FROM user_stocks WHERE stock_id = %s AND user_id = %s', 
                            (stock_id, user_id)
                        )

                    # Log the transaction
                    cursor.execute(
                        'INSERT INTO transactions (user_id, stock_id, company_name, transaction_type, shares, price, date) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (user_id, stock_id, company_name, 'sell', quantity, current_price, datetime.now())
                    )

                    mysql.connection.commit()
                    flash('Sale successful!', 'success')
                    return redirect(url_for('stocks'))
                else:
                    flash("User balance not found.", "danger")

        except Exception as e:
            # Rollback if there is an error
            mysql.connection.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
        finally:
            cursor.close()

    flash('You must be logged in to perform this action.', 'warning')
    return redirect(url_for('login'))

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor()
        
        # Delete stock from user_stocks table
        cursor.execute('DELETE FROM user_stocks WHERE stock_id = %s AND user_id = %s', (stock_id, user_id))
        
        mysql.connection.commit()
        flash('Stock deleted successfully!')
        return redirect(url_for('stocks'))

    return redirect(url_for('login'))

# Route for the contact page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        contact_message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            message=form.message.data
        )
        db.session.add(contact_message)
        db.session.commit()
        flash('Message sent successfully!')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)


# Function to update stock prices in the background
def update_stock_prices():
    with app.app_context():
        while True:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT stock_id, current_price FROM stocks')
                stocks = cursor.fetchall()

                for stock in stocks:
                    stock_id = stock['stock_id']
                    current_price = stock['current_price']
                    price_change = Decimal(random.uniform(-10, 10))
                    new_price = max(current_price + price_change, 0)

                    cursor.execute('UPDATE stocks SET current_price = %s WHERE stock_id = %s', (new_price, stock_id))
                
                mysql.connection.commit()
                cursor.close()
            except Exception as e:
                print(f"Error updating stock prices: {e}")
                flash('Error updating stock prices. Please try again later.', 'error')
            time.sleep(300)

# New route to fetch current stock prices
@app.route('/update_prices', methods=['GET'])
def fetch_stock_prices():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT stock_id, current_price FROM stocks')
        cursor.fetchall()

        flash('Stock prices updated successfully!', 'success')
    except Exception as e:
        print(f"Error fetching stock prices: {e}")
        flash('Failed to fetch stock prices. Please try again later.', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('stocks'))

# Start the background thread for price updates
threading.Thread(target=update_stock_prices, daemon=True).start()

# Application entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist

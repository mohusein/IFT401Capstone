from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from decimal import Decimal
import re
import random
import threading
import time

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'geeklogin'

mysql = MySQL(app)

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully!'
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
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
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, 0)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)

@app.route('/index', methods=['GET'])
def index():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch user's balance
        cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
        user_balance = cursor.fetchone()['balance']

        # Fetch user's stocks
        cursor.execute('SELECT * FROM stock WHERE user_id = %s', (user_id,))
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
            current_balance = result['balance']  # This is a Decimal
            amount = Decimal(amount)  # Convert amount to Decimal

            if amount > current_balance:
                return render_template('index.html', msg='Not enough funds!', balance=current_balance)

            # Update the balance
            new_balance = current_balance - amount
            cursor.execute('UPDATE accounts SET balance = %s WHERE id = %s', (new_balance, user_id))
            mysql.connection.commit()

            return render_template('index.html', msg='Withdrawal successful!', balance=new_balance)

    return redirect(url_for('login'))

@app.route('/stocks', methods=['GET'])
def stocks():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch user's balance
        cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
        user_balance = cursor.fetchone()['balance']

        # Pagination logic
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page

        # Fetch stocks and the quantity owned by the user
        cursor.execute('''
            SELECT s.stock_id, s.company_name, s.ticker, s.current_price, a.shares_owned
            FROM stock s
            LEFT JOIN accounts a ON a.id = %s
            LIMIT %s OFFSET %s
        ''', (user_id, per_page, offset))
        stocks = cursor.fetchall()

        # Count total stocks
        cursor.execute('SELECT COUNT(*) as count FROM stock')
        total_stocks = cursor.fetchone()['count']

        cursor.close()
        return render_template('stocks.html', stocks=stocks, page=page, per_page=per_page, total=total_stocks, balance=user_balance)

    return redirect(url_for('login'))


from decimal import Decimal

def update_stock_prices():
    with app.app_context():  # Set the application context for the thread
        while True:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
                cursor.execute('SELECT stock_id, current_price FROM stock')  # Fetch current prices
                stocks = cursor.fetchall()

                if not stocks:
                    print("No stocks found.")
                    time.sleep(10)
                    continue  # Wait and try again if no stocks

                for stock in stocks:
                    stock_id = stock['stock_id']
                    current_price = stock['current_price']
                    price_change = Decimal(random.uniform(-10, 10))  # Convert to Decimal
                    new_price = current_price + price_change

                    print(f"Updating stock_id {stock_id}: {current_price} -> {new_price}")  # Debug print

                    cursor.execute('UPDATE stock SET current_price = %s WHERE stock_id = %s', (new_price, stock_id))
                
                mysql.connection.commit()
                cursor.close()
            except Exception as e:
                print(f"Error updating stock prices: {e}")  # Log any errors
            time.sleep(300)

# Start the background thread for price updates
threading.Thread(target=update_stock_prices, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)

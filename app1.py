from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_mysqldb import MySQL
import MySQLdb.cursors
from decimal import Decimal
import re
import random
import threading
import time
import os


# Define a constant for the repeated message
FILL_FORM_MSG = 'Please fill out the form!'


secret_key = os.urandom(24).hex()

app = Flask(__name__, template_folder='templates')

app.secret_key = secret_key

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

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']


        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully!'
            return redirect(url_for('admin_dashboard'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('admin_login.html', msg=msg)

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
    #C:\Users\mulki\Documents\capstone\capstone\templates\register.html

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if username and password and email:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Admin account already exists!'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Admin account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', (username, password))
            mysql.connection.commit()
            msg = 'Admin registration successful!'
            return redirect(url_for('addmin_login'))
    else:
        msg = 'Please fill out the form!'
    return render_template('admin_register.html', msg=msg)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # if 'loggedin' in session and session.get('is_admin'):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM stocks')
        stocks = cursor.fetchall()

        cursor.execute('SELECT * FROM admins')
        accounts = cursor.fetchall()

        return render_template('admin_dashboard.html', username=session['username'], stocks=stocks, accounts=accounts)
    # return redirect(url_for('admin_login'))

@app.route('/admin_login', methods=['GET', 'POST'])
@app.route('/home', methods=['GET'])
def user_index():
    if 'loggedin' in session:

    
        return render_template('admin_dashboard.html', username=session['username'])
    return redirect(url_for('login'))


#admin add stock page
@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    msg = ''
    if 'loggedin' in session and session.get('is_admin'):
        if request.method == 'POST':
            company_name = request.form['company_name']
            ticker = request.form['ticker']
            initial_price = request.form['initial_price']
            current_price = request.form['current_price']

            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO stocks (company_name, ticker, initial_price, current_price) VALUES (%s, %s, %s, %s)', 
                           (company_name, ticker, initial_price, current_price))
            mysql.connection.commit()
            msg = 'Stock added successfully!'
            return redirect(url_for('admin_portfolio'))

        return render_template('add_stock.html', msg=msg)
    return redirect(url_for('admin_login'))

#admin remove stock page
@app.route('/remove_stock/<int:stock_id>', methods=['POST'])
def remove_stock(stock_id):
    if 'loggedin' in session and session.get('is_admin'):
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM stocks WHERE stock_id = %s', (stock_id,))
        mysql.connection.commit()
        flash('Stock removed successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))


@app.route('/index', methods=['GET'])
def index():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

       

       # Fetch user's balance
        cursor.execute('SELECT balance FROM accounts WHERE id = %s', (id,))
        result = cursor.fetchone()

        if result:  # Check if result is not None
            user_balance = result['balance']
        else:
            user_balance = 0  # Or handle the case as appropriate
        print('No balance found for the user.')


        # Fetch user's stocks
        cursor.execute('''
            SELECT s.stock_id, s.company_name, s.ticker, s.current_price, COALESCE(us.stock_quantity, 0) AS stock_quantity
            FROM stock s
            LEFT JOIN user_stocks us ON s.stock_id = us.stock_id AND us.user_id = %s
        ''', (user_id,))
        user_stocks = cursor.fetchall()
        print(f"User Stocks: {user_stocks}")

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


#@app.route('/get_transaction', methods=['GET'])
#def get_transaction():
   # if 'loggedin' in session:
    #    user_id = session['id']
       # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch user's balance
        #cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
       # get_transaction = cursor.fetchone()

       # return render_template('index.html', get_transaction=get_transaction)

@app.route('/transactions')
def transactions():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('SELECT company_name, transaction_type, shares, date, price FROM transactions')
        transactions = cursor.fetchall()
    except Exception as e:
        return f"Error fetching transactions: {str(e)}"
    finally:
        cursor.close()

        
    #cursor.execute('SELECT company_name, transaction_type, shares, date, price FROM transactions')
    #transactions = cursor.fetchall()
    #cursor.close()
    
    return render_template('transactions.html', transactions=transactions)



#def stocks():
 #   if 'loggedin' in session:
 #       id = session['id']
  #      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch user's balance
  #      cursor.execute('SELECT balance FROM accounts WHERE id = %s', (id,))
  #      stocks = cursor.fetchone()
#
        # Pagination logic
  #      page = request.args.get('page', 1, type=int)
  #      per_page = 10
  #      offset = (page - 1) * per_page

        # Fetch stocks and the quantity owned by the user
   #     cursor.execute('''
   #         SELECT s.stock_id, s.company_name, s.ticker, s.current_price, COALESCE(us.stock_quantity, 0) AS shares_owned
    #        FROM stock s
     #       LEFT JOIN user_stocks us ON us.stock_id = s.stock_id AND us.user_id = %s
      #      LIMIT %s OFFSET %s
     #   ''', (id, per_page, offset))
     #   stocks = cursor.fetchall()

        # Count total stocks
      #  cursor.execute('SELECT COUNT(*) as count FROM stock')
     #   total_stocks = cursor.fetchone()['count']

    #    cursor.close()
     #   return render_template('stocks.html', stocks=stocks, page=page, per_page=per_page, total=total_stocks)

   # return redirect(url_for('login'))

@app.route('/stocks')
def stocks():
    cursor = mysql.connection.cursor()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of stocks to display per page

    try:
        # Fetch the total number of stocks
        cursor.execute('SELECT COUNT(*) FROM stocks')
        total_stocks = cursor.fetchone()[0]

        # Calculate the offset for pagination
        offset = (page - 1) * per_page

        # Fetch the stocks for the current page
        cursor.execute('SELECT * FROM stocks LIMIT %s OFFSET %s', (per_page, offset))
        stocks= cursor.fetchall()
    except Exception as e:
        return f"An error occurred: {e}"
    finally:
        cursor.close()

    return render_template('stocks.html')


@app.route('/buy_stock/<int:stock_id>', methods=['POST'])
def buy_stock(stock_id):
    if 'loggedin' in session:
        user_id = session['id']
        quantity = int(request.form['quantity'])

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch stock details
        cursor.execute('SELECT current_price FROM stock WHERE stock_id = %s', (stock_id,))
        stock = cursor.fetchone()

        if stock:
            current_price = Decimal(stock['current_price'])
            total_cost = current_price * quantity

            # Fetch user's balance
            cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
            result = cursor.fetchone()

            if total_cost > new_balance:
                return redirect(url_for('stocks', msg='Not enough funds!'))

            # Update user balance
            new_balance = new_balance - total_cost
            cursor.execute('UPDATE accounts SET balance = %s WHERE id = %s', (new_balance, user_id))

            # Check if the user already owns this stock
            cursor.execute('SELECT stock_quantity FROM user_stocks WHERE user_id = %s AND stock_id = %s', (user_id, stock_id))
            user_shares = cursor.fetchone()

            if user_shares:
                # Update existing stock quantity
                new_shares_owned = user_shares['stock_quantity'] + quantity
                cursor.execute('UPDATE user_stocks SET stock_quantity = %s WHERE user_id = %s AND stock_id = %s', 
                               (new_shares_owned, user_id, stock_id))
            else:
                # Insert new stock entry
                cursor.execute('INSERT INTO user_stocks (user_id, stock_id, stock_quantity) VALUES (%s, %s, %s)', 
                               (user_id, stock_id, quantity))

            mysql.connection.commit()

            return redirect(url_for('stocks', msg=f'Successfully bought {quantity} shares of stock ID {stock_id}!'))

    return redirect(url_for('login'))

@app.route('/sell_stock/<int:stock_id>', methods=['POST'])
def sell_stock(stock_id):
    if 'loggedin' in session:
        user_id = session['id']
        quantity = int(request.form['quantity'])

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch shares owned
        cursor.execute('SELECT stock_quantity, current_price FROM stock s LEFT JOIN user_stocks us ON s.stock_id = us.stock_id WHERE s.stock_id = %s AND us.user_id = %s', (stock_id, user_id))
        stock = cursor.fetchone()

        if stock:
            shares_owned = stock['stock_quantity']
            current_price = Decimal(stock['current_price'])
            total_revenue = current_price * quantity

            if quantity > shares_owned:
                return redirect(url_for('stocks', msg='Not enough shares to sell!'))

            # Update user balance
            cursor.execute('SELECT balance FROM accounts WHERE id = %s', (user_id,))
            user_balance = cursor.fetchone()['balance']
            new_balance = user_balance + total_revenue
            cursor.execute('UPDATE accounts SET balance = %s WHERE id = %s', (new_balance, user_id))

            # Update shares owned
            new_shares_owned = shares_owned - quantity
            if new_shares_owned > 0:
                cursor.execute('UPDATE user_stocks SET stock_quantity = %s WHERE stock_id = %s AND user_id = %s', (new_shares_owned, stock_id, user_id))
            else:
                cursor.execute('DELETE FROM user_stocks WHERE stock_id = %s AND user_id = %s', (stock_id, user_id))

            mysql.connection.commit()

            return redirect(url_for('stocks', msg=f'Successfully sold {quantity} shares of stock ID {stock_id}!'))

    return redirect(url_for('login'))

def update_stock_prices():
    with app.app_context():  # Set the application context for the thread
        while True:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT stock_id, current_price FROM stock')
                stocks = cursor.fetchall()

                if not stocks:
                    print("No stocks found.")
                    time.sleep(10)
                    continue  # Wait and try again if no stocks

                for stock in stocks:
                    stock_id = stock['stock_id']
                    current_price = stock['current_price']
                    price_change = Decimal(random.uniform(-10, 10))
                    new_price = max(current_price + price_change, 0)  # Ensure price does not go negative

                    print(f"Updating stock_id {stock_id}: {current_price} -> {new_price}")

                    # Update the current price in the stock table
                    cursor.execute('UPDATE stock SET current_price = %s WHERE stock_id = %s', (new_price, stock_id))
                
                mysql.connection.commit()  # Commit the updates
                cursor.close()  # Close the cursor
            except Exception as e:
                print(f"Error updating stock prices: {e}")
            time.sleep(300)  # Sleep for 5 minutes

# Start the background thread for price updates
threading.Thread(target=update_stock_prices, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)
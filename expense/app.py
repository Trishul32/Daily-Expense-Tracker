# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Expense, User
from datetime import datetime, timedelta
from dateutil import parser
import os

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',  # change in production
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'expenses.sqlite'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# ensure instance folder exists
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ---------------- Authentication Routes ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash(f'Account created successfully! Welcome, {username}!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

# ---------------- Main Routes ----------------

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # add new expense
        try:
            amount = float(request.form.get('amount', '0'))
            category = request.form.get('category', 'Other').strip() or 'Other'
            note = request.form.get('note', '').strip()
            date_str = request.form.get('date', '')
            if date_str:
                created_at = parser.parse(date_str)
            else:
                created_at = datetime.utcnow()

            if amount <= 0:
                flash('Amount must be > 0', 'error')
            else:
                e = Expense(amount=amount, category=category, note=note, created_at=created_at, user_id=current_user.id)
                db.session.add(e)
                db.session.commit()
                flash('Expense added', 'success')
                return redirect(url_for('index'))
        except ValueError:
            flash('Invalid amount', 'error')

    # show recent expenses
    recent = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).limit(20).all()
    categories = sorted({e.category for e in Expense.query.filter_by(user_id=current_user.id).all()})
    return render_template('index.html', expenses=recent, categories=categories)

@app.route('/expenses')
@login_required
def expenses_table():
    all_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).all()
    return render_template('expenses_table.html', expenses=all_expenses)

@app.route('/api/summary')
@login_required
def api_summary():
    """
    Returns JSON with:
    - category totals for the last N days
    - daily totals for the last N days
    Query param days= (default 30)
    """
    days = int(request.args.get('days', 30))
    end = datetime.utcnow()
    start = end - timedelta(days=days-1)

    # category aggregation
    from sqlalchemy import func
    cat_rows = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.created_at >= start, Expense.created_at <= end, Expense.user_id == current_user.id)
        .group_by(Expense.category)
        .all()
    )
    categories = [{'category': r[0], 'total': float(r[1] or 0)} for r in cat_rows]

    # daily aggregation (for trend)
    daily = {}
    for i in range(days):
        day = (start + timedelta(days=i)).date()
        daily[day.isoformat()] = 0.0

    daily_rows = (
        db.session.query(func.date(Expense.created_at), func.sum(Expense.amount))
        .filter(Expense.created_at >= start, Expense.created_at <= end, Expense.user_id == current_user.id)
        .group_by(func.date(Expense.created_at))
        .all()
    )
    for row in daily_rows:
        date_str = row[0]
        total = float(row[1] or 0)
        daily[date_str] = total

    daily_list = [{'date': d, 'total': daily[d]} for d in sorted(daily.keys())]

    total_spent = sum([c['total'] for c in categories])

    return jsonify({
        'categories': categories,
        'daily': daily_list,
        'total_spent': total_spent,
        'days': days
    })

if __name__ == '__main__':
    # Get port from environment variable (for Railway deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

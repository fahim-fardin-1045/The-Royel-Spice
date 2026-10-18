"""The Royal Spice: Flask + MySQL (XAMPP) restaurant management starter.

Development only by default. Run commands described in README.md.
"""
import os
import secrets
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from urllib.parse import urlparse

import click
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from sqlalchemy.engine import make_url
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

# The local XAMPP MySQL server listens on port 3307. Adapt an existing
# DATABASE_URL pointing to 127.0.0.1:3306 without changing the MySQL server
# configuration, existing username, password, or database name.
database_url = make_url(os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:@127.0.0.1:3307/royal_spice?charset=utf8mb4',
))
if (database_url.get_backend_name() == 'mysql'
        and database_url.host in ('127.0.0.1', 'localhost')
        and database_url.port in (None, 3306)):
    database_url = database_url.set(port=3307)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', '0') == '1',
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)
if os.environ.get('APP_ENV') == 'production' and not os.environ.get('SECRET_KEY'):
    raise RuntimeError('A permanent SECRET_KEY is required in production.')
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please sign in as an administrator.'

ORDER_STATES = ['new', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']
RESERVATION_STATES = ['pending', 'confirmed', 'cancelled', 'completed']
PAYMENT_METHODS = ['Cash', 'Card', 'bKash', 'Nagad']
SERVICE_TYPES = ['delivery', 'takeaway', 'dine-in']
RESERVED_STATES = ['pending', 'confirmed']


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.String(20), nullable=False, default='REST-001')
    name = db.Column(db.String(120), nullable=False, default='The Royal Spice')
    subtitle = db.Column(db.String(120), default='Restaurant & Café')
    owner_name = db.Column(db.String(100), default='Ahmed Rahman')
    address = db.Column(db.String(255), default='Dhanmondi, Dhaka-1209, Bangladesh')
    phone = db.Column(db.String(40), default='+880 1XXX-XXXXXX')
    email = db.Column(db.String(120), default='contact@theroyalspice.example.com')
    opening_time = db.Column(db.Time, nullable=False, default=time(10, 0))
    closing_time = db.Column(db.Time, nullable=False, default=time(23, 0))
    seating_capacity = db.Column(db.Integer, nullable=False, default=80)


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), default='')
    available = db.Column(db.Boolean, default=True, nullable=False)


class Offer(db.Model):
    """Admin-controlled promo codes; only active, eligible codes are redeemable."""
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), nullable=False, unique=True, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), default='')
    discount_type = db.Column(db.String(12), nullable=False, default='percent')
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    min_order = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    max_discount = db.Column(db.Numeric(10, 2), nullable=True)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)
    used_count = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    featured = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def display_amount(self):
        if self.discount_type == 'percent':
            return f'{self.discount_value.normalize():f}% OFF'
        return f'৳{self.discount_value:,.0f} OFF'


class OrderDiscount(db.Model):
    """Immutable discount snapshot. Separate table keeps old order schema intact."""
    __tablename__ = 'order_discounts'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True, nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=True)
    code = db.Column(db.String(30), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    discount = db.Column(db.Numeric(12, 2), nullable=False)
    order = db.relationship('Order', backref=db.backref('discount_record', uselist=False))



class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), default='')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    public_token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(24))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer', backref='orders')
    service_type = db.Column(db.String(20), nullable=False)
    table_number = db.Column(db.String(20), default='')
    address = db.Column(db.String(255), default='')
    notes = db.Column(db.String(500), default='')
    payment_method = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(db.String(20), nullable=False, default='unpaid')
    status = db.Column(db.String(20), nullable=False, default='new')
    total = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    items = db.relationship('OrderItem', backref='order', cascade='all,delete-orphan', lazy='selectin')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    @property
    def line_total(self):
        return self.unit_price * self.quantity


class RestaurantTable(db.Model):
    __tablename__ = 'restaurant_tables'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    seats = db.Column(db.Integer, nullable=False, default=4)
    active = db.Column(db.Boolean, nullable=False, default=True)


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(120), default='')
    party_size = db.Column(db.Integer, nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    notes = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Numeric(12, 2), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False, default='kg')
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    reorder_level = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    supplier = db.Column(db.String(120), default='')


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)


@login_manager.user_loader
def load_user(identifier):
    return db.session.get(Admin, int(identifier)) if identifier.isdigit() else None


def setting():
    return db.session.get(Setting, 1) or Setting()


@app.context_processor
def inject_shared():
    return dict(restaurant=setting(), cart_count=sum(session.get('cart', {}).values()),
                payment_methods=PAYMENT_METHODS, order_states=ORDER_STATES,
                reservation_states=RESERVATION_STATES, today=date.today())


@app.template_filter('bdt')
def format_bdt(value):
    return f'৳{Decimal(value or 0):,.2f}'


def require_value(field, maxlen=120):
    value = request.form.get(field, '').strip()
    if not value or len(value) > maxlen:
        raise ValueError(f'{field.replace("_", " ").title()} must contain 1–{maxlen} characters.')
    return value


def optional(field, maxlen=255):
    v = request.form.get(field, '').strip()
    if len(v) > maxlen:
        raise ValueError(f'{field.replace("_", " ")} is too long.')
    return v


def positive_int(field, maximum=100000):
    try:
        n = int(request.form.get(field, ''))
        if not 1 <= n <= maximum:
            raise ValueError()
        return n
    except (ValueError, TypeError):
        raise ValueError(f'{field.replace("_", " ").title()} must be between 1 and {maximum}.')


def money(field, allow_zero=False):
    try:
        val = Decimal(request.form.get(field, '').strip())
        if not val.is_finite() or val > Decimal('99999999') or (val < 0 if allow_zero else val <= 0):
            raise ValueError()
        return val.quantize(Decimal('0.01'))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f'Enter a valid {field} amount.')


def redirect_back(endpoint):
    return redirect(url_for(endpoint))


def offer_usage(offer):
    return offer.used_count or 0


def is_offer_live(offer, now=None):
    now = now or datetime.now()
    return (offer.active and (offer.starts_at is None or offer.starts_at <= now)
            and (offer.ends_at is None or offer.ends_at >= now)
            and (offer.max_uses is None or offer_usage(offer) < offer.max_uses))


def active_offers(featured_only=False):
    query = Offer.query.filter_by(active=True)
    if featured_only:
        query = query.filter_by(featured=True)
    return [x for x in query.order_by(Offer.created_at.desc()).all() if is_offer_live(x)]


def discount_quote(code, subtotal, lock=False):
    """Calculate discount against server-trusted subtotal; no client totals accepted.

    On MySQL the selected offer row is locked during checkout to serialize
    discount redemptions when max_uses is configured.
    """
    code = str(code or '').strip().upper()
    if not code:
        return None, Decimal('0.00'), None
    query = Offer.query.filter_by(code=code)
    offer = query.with_for_update().first() if lock else query.first()
    if offer is None or not is_offer_live(offer):
        return None, Decimal('0.00'), 'This offer code is not valid or has expired.'
    if subtotal < offer.min_order:
        return None, Decimal('0.00'), f'Order at least {format_bdt(offer.min_order)} to use {code}.'
    if offer.discount_type == 'percent':
        amount = (subtotal * offer.discount_value / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if offer.max_discount is not None:
            amount = min(amount, offer.max_discount)
    else:
        amount = offer.discount_value
    return offer, min(amount, subtotal), None



@app.get('/')
def home():
    featured = MenuItem.query.filter_by(available=True).limit(4).all()
    return render_template('home.html', featured=featured, offers=active_offers(featured_only=True)[:3])


@app.get('/menu')
def menu():
    items = MenuItem.query.filter_by(available=True).order_by(MenuItem.category, MenuItem.name).all()
    groups = defaultdict(list)
    for item in items:
        groups[item.category].append(item)
    return render_template('menu.html', groups=groups)


@app.get('/offers')
def offers():
    return render_template('offers.html', offers=active_offers())


@app.post('/offers/apply')
def offer_apply():
    code = request.form.get('code', '').strip().upper()
    if len(code) > 30 or not code:
        flash('Enter a valid offer code.', 'error')
    else:
        _, subtotal = get_cart_lines()
        if subtotal <= 0:
            flash('Add something to your cart before applying an offer.', 'error')
        else:
            offer, amount, error = discount_quote(code, subtotal)
            if error:
                flash(error, 'error')
            else:
                session['offer_code'] = offer.code
                flash(f'{offer.code} applied. You save {format_bdt(amount)}.', 'success')
    return redirect(url_for('cart'))


@app.post('/offers/remove')
def offer_remove():
    session.pop('offer_code', None)
    flash('Offer removed.', 'success')
    return redirect(url_for('cart'))


@app.get('/about')
def about():
    return render_template('about.html')


def valid_reservation_start(value):
    try:
        start = datetime.strptime(value, '%Y-%m-%dT%H:%M')
    except (TypeError, ValueError):
        raise ValueError('Choose a valid reservation date and time.')
    info = setting()
    if start < datetime.now() + timedelta(minutes=10):
        raise ValueError('Bookings must be at least 10 minutes in the future.')
    if start > datetime.now() + timedelta(days=90):
        raise ValueError('Bookings may be made up to 90 days in advance.')
    if start.time() < info.opening_time or (datetime.combine(start.date(), info.closing_time) - start < timedelta(hours=2)):
        raise ValueError('Reservations need a two-hour slot within opening hours.')
    return start


@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        try:
            name = require_value('guest_name', 100)
            phone = require_value('phone', 40)
            size = positive_int('party_size', 10)
            start = valid_reservation_start(request.form.get('starts_at'))
            email = optional('email', 120)
            notes = optional('notes', 500)
            # Lock singleton settings row in MySQL to serialize concurrent capacity checks.
            info = Setting.query.filter_by(id=1).with_for_update().first()
            if info is None:
                raise ValueError('Please initialise the database first.')
            left = start - timedelta(hours=2)
            right = start + timedelta(hours=2)
            overlapping = db.session.query(func.coalesce(func.sum(Reservation.party_size), 0)).filter(
                Reservation.status.in_(RESERVED_STATES),
                Reservation.starts_at > left,
                Reservation.starts_at < right,
            ).scalar() or 0
            capacity = min(info.seating_capacity,
                sum(t.seats for t in RestaurantTable.query.filter_by(active=True).all()))
            if int(overlapping) + size > capacity:
                raise ValueError('There is insufficient seating for this time. Choose another slot.')
            booking = Reservation(guest_name=name, phone=phone, email=email,
                                  party_size=size, starts_at=start, notes=notes)
            db.session.add(booking)
            db.session.commit()
            flash(f'Reservation request #{booking.id} submitted. Our team will confirm it.', 'success')
            return redirect(url_for('reserve'))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    return render_template('reserve.html')


@app.post('/cart/add/<int:item_id>')
def cart_add(item_id):
    item = db.session.get(MenuItem, item_id)
    if not item or not item.available:
        abort(404)
    try:
        qty = positive_int('quantity', 20)
        cart = dict(session.get('cart', {}))
        total = int(cart.get(str(item_id), 0)) + qty
        if total > 20:
            raise ValueError('Maximum 20 portions per menu item.')
        cart[str(item_id)] = total
        session['cart'] = cart
        flash(f'{item.name} added to your cart.', 'success')
    except ValueError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('menu'))


def get_cart_lines():
    ids = [int(k) for k in session.get('cart', {}) if k.isdigit()]
    products = {x.id: x for x in MenuItem.query.filter(MenuItem.id.in_(ids)).all()} if ids else {}
    lines, total = [], Decimal('0')
    for key, qty in session.get('cart', {}).items():
        item = products.get(int(key)) if key.isdigit() else None
        if not item or not item.available or not isinstance(qty, int) or qty < 1 or qty > 20:
            continue
        amount = item.price * qty
        lines.append({'item': item, 'quantity': qty, 'subtotal': amount})
        total += amount
    return lines, total


@app.get('/cart')
def cart():
    lines, total = get_cart_lines()
    offer, savings, offer_error = discount_quote(session.get('offer_code'), total)
    return render_template('cart.html', lines=lines, total=total, offer=offer, savings=savings, final_total=total-savings, offer_error=offer_error)


@app.post('/cart/update')
def cart_update():
    new_cart = {}
    for key in session.get('cart', {}):
        try:
            qty = int(request.form.get('qty_' + key, '0'))
            if qty < 0 or qty > 20:
                raise ValueError()
            if qty:
                new_cart[key] = qty
        except ValueError:
            flash('Quantities must be between 0 and 20.', 'error')
            return redirect_back('cart')
    session['cart'] = new_cart
    flash('Cart updated.', 'success')
    return redirect_back('cart')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    lines, total = get_cart_lines()
    if not lines:
        flash('Add food to your cart first.', 'error')
        return redirect_back('menu')
    offer, savings, offer_error = discount_quote(session.get('offer_code'), total)
    if request.method == 'POST':
        try:
            name = require_value('name', 100)
            phone = require_value('phone', 40)
            email = optional('email', 120)
            service = request.form.get('service_type')
            payment = request.form.get('payment_method')
            if service not in SERVICE_TYPES or payment not in PAYMENT_METHODS:
                raise ValueError('Choose valid service and payment options.')
            address = optional('address', 255)
            table_number = optional('table_number', 20)
            notes = optional('notes', 500)
            if service == 'delivery' and not address:
                raise ValueError('Enter a delivery address.')
            if service == 'dine-in':
                if not table_number or not RestaurantTable.query.filter_by(number=table_number, active=True).first():
                    raise ValueError('Choose a valid dine-in table.')
            # Lock and revalidate offer at submission: no stale/forged discounts.
            if session.get('offer_code'):
                offer, savings, offer_error = discount_quote(session['offer_code'], total, lock=True)
                if offer_error:
                    raise ValueError(offer_error)
            # Always recompute prices from database, not submitted form fields.
            customer = Customer.query.filter_by(phone=phone).first()
            if customer is None:
                customer = Customer(name=name, phone=phone, email=email)
                db.session.add(customer)
                db.session.flush()
            else:
                customer.name, customer.email = name, email
            order = Order(customer_id=customer.id, service_type=service,
                          payment_method=payment, total=total-savings, notes=notes,
                          address=address if service == 'delivery' else '',
                          table_number=table_number if service == 'dine-in' else '')
            db.session.add(order)
            db.session.flush()
            if offer:
                offer.used_count = (offer.used_count or 0) + 1
                db.session.add(OrderDiscount(order_id=order.id, offer_id=offer.id,
                                             code=offer.code, subtotal=total, discount=savings))
            for line in lines:
                item = line['item']
                db.session.add(OrderItem(order_id=order.id, menu_item_id=item.id,
                                         name=item.name, unit_price=item.price,
                                         quantity=line['quantity']))
            db.session.commit()
            session.pop('cart', None)
            session.pop('offer_code', None)
            flash('Order submitted successfully. Payment is not collected online.', 'success')
            return redirect(url_for('order_receipt', token=order.public_token))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    tables = RestaurantTable.query.filter_by(active=True).order_by(RestaurantTable.number).all()
    return render_template('checkout.html', lines=lines, total=total, offer=offer, savings=savings, offer_error=offer_error, final_total=total-savings, tables=tables)


@app.get('/receipt/<token>')
def order_receipt(token):
    order = Order.query.filter_by(public_token=token).first_or_404()
    return render_template('receipt.html', order=order)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect_back('admin_dashboard')
    if request.method == 'POST':
        name = request.form.get('username', '').strip()
        user = Admin.query.filter_by(username=name).first()
        if user and check_password_hash(user.password_hash, request.form.get('password', '')):
            login_user(user)
            return redirect_back('admin_dashboard')
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')


@app.post('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Signed out.', 'success')
    return redirect_back('admin_login')


def admin_template(template, **params):
    return render_template('admin/' + template, **params)


@app.get('/admin')
@login_required
def admin_dashboard():
    start = datetime.combine(date.today(), time.min)
    end = start + timedelta(days=1)
    daily_orders = Order.query.filter(Order.created_at >= start, Order.created_at < end,
                                      Order.status != 'cancelled').all()
    sales = sum((o.total for o in daily_orders if o.status == 'completed'), Decimal('0'))
    expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date == date.today()).scalar()
    recent = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    open_bookings = Reservation.query.filter_by(status='pending').count()
    low_stock = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.reorder_level).count()
    return admin_template('dashboard.html', daily_orders=len(daily_orders), sales=sales,
                          expenses=expenses, open_bookings=open_bookings,
                          low_stock=low_stock, recent=recent)


@app.route('/admin/menu', methods=['GET', 'POST'])
@login_required
def admin_menu():
    if request.method == 'POST':
        try:
            item_id = request.form.get('item_id')
            item = db.session.get(MenuItem, int(item_id)) if item_id else MenuItem()
            if item is None:
                abort(404)
            item.code = require_value('code', 20)
            item.name = require_value('name', 120)
            item.category = require_value('category', 80)
            item.price = money('price')
            item.description = optional('description', 255)
            item.available = request.form.get('available') == 'on'
            db.session.add(item)
            db.session.commit()
            flash('Menu item saved.', 'success')
            return redirect_back('admin_menu')
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), 'error')
        except Exception as exc:
            db.session.rollback()
            # Do not expose internal DB details in the UI.
            flash('Could not save item. The item code may already exist.', 'error')
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    return admin_template('menu.html', items=items)


@app.post('/admin/menu/<int:item_id>/delete')
@login_required
def admin_menu_delete(item_id):
    item = db.get_or_404(MenuItem, item_id)
    if OrderItem.query.filter_by(menu_item_id=item.id).first():
        item.available = False
        db.session.commit()
        flash('Item has order history, so it was marked unavailable instead.', 'success')
    else:
        db.session.delete(item)
        db.session.commit()
        flash('Menu item deleted.', 'success')
    return redirect_back('admin_menu')


@app.route('/admin/offers', methods=['GET', 'POST'])
@login_required
def admin_offers():
    if request.method == 'POST':
        try:
            offer_id = request.form.get('offer_id', '').strip()
            offer = db.session.get(Offer, int(offer_id)) if offer_id else Offer()
            if offer is None:
                abort(404)
            code = require_value('code', 30).upper()
            if not all(x.isalnum() or x in '-_' for x in code) or not code.isascii():
                raise ValueError('Offer code: only A-Z, numbers, - and _ are allowed.')
            existing = Offer.query.filter_by(code=code).first()
            if existing and existing.id != offer.id:
                raise ValueError('This offer code already exists.')
            offer.code = code
            offer.title = require_value('title', 120)
            offer.description = optional('description', 255)
            offer.discount_type = request.form.get('discount_type')
            if offer.discount_type not in ('percent', 'fixed'):
                raise ValueError('Choose percentage or fixed amount.')
            offer.discount_value = money('discount_value')
            if offer.discount_type == 'percent' and offer.discount_value > 100:
                raise ValueError('Percentage discount must be 100 or less.')
            offer.min_order = money('min_order', allow_zero=True)
            offer.max_discount = (money('max_discount') if request.form.get('max_discount', '').strip() and offer.discount_type == 'percent' else None)
            max_uses = request.form.get('max_uses', '').strip()
            offer.max_uses = int(max_uses) if max_uses else None
            if offer.max_uses is not None and not 1 <= offer.max_uses <= 1000000:
                raise ValueError('Usage limit must be between 1 and 1,000,000.')
            def read_dt(field):
                raw = request.form.get(field, '').strip()
                return datetime.strptime(raw, '%Y-%m-%dT%H:%M') if raw else None
            offer.starts_at = read_dt('starts_at')
            offer.ends_at = read_dt('ends_at')
            if offer.starts_at and offer.ends_at and offer.starts_at >= offer.ends_at:
                raise ValueError('End date must be after start date.')
            offer.active = request.form.get('active') == 'on'
            offer.featured = request.form.get('featured') == 'on'
            db.session.add(offer)
            db.session.commit()
            flash(f'Offer {code} saved.', 'success')
            return redirect_back('admin_offers')
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(f'Could not save offer: {exc}', 'error')
        except Exception:
            db.session.rollback()
            flash('Could not save offer. Check the code and form values.', 'error')
    entries = Offer.query.order_by(Offer.created_at.desc()).all()
    counts = {o.id: offer_usage(o) for o in entries}
    return admin_template('offers.html', entries=entries, counts=counts)


@app.post('/admin/offers/<int:offer_id>/toggle')
@login_required
def admin_offer_toggle(offer_id):
    offer = db.get_or_404(Offer, offer_id)
    offer.active = not offer.active
    db.session.commit()
    flash(f'Offer {offer.code} {"enabled" if offer.active else "disabled"}.', 'success')
    return redirect_back('admin_offers')


@app.route('/admin/pos', methods=['GET', 'POST'])
@login_required
def admin_pos():
    """Staff-entered point of sale; payment is recorded, not processed."""
    if request.method == 'POST':
        try:
            name = require_value('name', 100)
            phone = require_value('phone', 40)
            service = request.form.get('service_type')
            payment = request.form.get('payment_method')
            if service not in ['dine-in', 'takeaway'] or payment not in PAYMENT_METHODS:
                raise ValueError('POS currently supports dine-in and takeaway only.')
            table_number = optional('table_number', 20)
            if service == 'dine-in' and not RestaurantTable.query.filter_by(number=table_number, active=True).first():
                raise ValueError('Select an active dining table.')
            ids = request.form.getlist('menu_item_id')
            quantities = request.form.getlist('quantity')
            if not ids or len(ids) != len(quantities) or len(ids) > 20:
                raise ValueError('Add at least one product (maximum 20 lines).')
            lines = []
            for menu_id, raw_qty in zip(ids, quantities):
                try:
                    qty = int(raw_qty)
                    if not 1 <= qty <= 20:
                        raise ValueError()
                    item = db.session.get(MenuItem, int(menu_id))
                except (TypeError, ValueError):
                    raise ValueError('Invalid POS item or quantity.')
                if not item or not item.available:
                    raise ValueError('One of the selected products is not available.')
                lines.append((item, qty))
            total = sum((item.price * qty for item, qty in lines), Decimal('0'))
            pos_code = request.form.get('offer_code', '').strip().upper()
            offer, savings, offer_error = discount_quote(pos_code, total, lock=True)
            if offer_error:
                raise ValueError(offer_error)
            customer = Customer.query.filter_by(phone=phone).first()
            if customer is None:
                customer = Customer(name=name, phone=phone)
                db.session.add(customer)
                db.session.flush()
            else:
                customer.name = name
            order = Order(customer_id=customer.id, service_type=service,
                          table_number=table_number if service == 'dine-in' else '',
                          payment_method=payment,
                          payment_status='paid' if request.form.get('paid') == 'on' else 'unpaid',
                          status='completed' if request.form.get('completed') == 'on' else 'new',
                          total=total-savings)
            db.session.add(order)
            db.session.flush()
            if offer:
                offer.used_count = (offer.used_count or 0) + 1
                db.session.add(OrderDiscount(order_id=order.id, offer_id=offer.id,
                                             code=offer.code, subtotal=total, discount=savings))
            for item, qty in lines:
                db.session.add(OrderItem(order_id=order.id, menu_item_id=item.id,
                                         name=item.name, unit_price=item.price, quantity=qty))
            db.session.commit()
            flash(f'POS order #{order.id} created.', 'success')
            return redirect(url_for('order_receipt', token=order.public_token))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    menu_items = MenuItem.query.filter_by(available=True).order_by(MenuItem.name).all()
    tables = RestaurantTable.query.filter_by(active=True).order_by(RestaurantTable.number).all()
    return admin_template('pos.html', menu_items=menu_items, tables=tables)


@app.get('/admin/orders')
@login_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).limit(200).all()
    return admin_template('orders.html', orders=orders)


@app.post('/admin/orders/<int:order_id>/status')
@login_required
def admin_order_status(order_id):
    order = db.get_or_404(Order, order_id)
    state = request.form.get('status')
    if state not in ORDER_STATES:
        abort(400)
    order.status = state
    db.session.commit()
    flash(f'Order #{order.id} updated.', 'success')
    return redirect_back('admin_orders')


@app.post('/admin/orders/<int:order_id>/paid')
@login_required
def admin_order_paid(order_id):
    order = db.get_or_404(Order, order_id)
    order.payment_status = 'paid' if request.form.get('paid') == 'yes' else 'unpaid'
    db.session.commit()
    flash('Payment record updated by staff.', 'success')
    return redirect_back('admin_orders')


@app.route('/admin/reservations', methods=['GET', 'POST'])
@login_required
def admin_reservations():
    if request.method == 'POST':
        booking = db.get_or_404(Reservation, request.form.get('id', type=int))
        new_state = request.form.get('status')
        if new_state not in RESERVATION_STATES:
            abort(400)
        booking.status = new_state
        db.session.commit()
        flash('Reservation updated.', 'success')
        return redirect_back('admin_reservations')
    bookings = Reservation.query.order_by(Reservation.starts_at.desc()).limit(200).all()
    return admin_template('reservations.html', bookings=bookings)


@app.route('/admin/tables', methods=['GET', 'POST'])
@login_required
def admin_tables():
    if request.method == 'POST':
        try:
            table_id = request.form.get('item_id')
            table = db.session.get(RestaurantTable, int(table_id)) if table_id else RestaurantTable()
            if table is None:
                abort(404)
            table.number = require_value('number', 20)
            table.seats = positive_int('seats', 30)
            table.active = request.form.get('active') == 'on'
            db.session.add(table)
            db.session.commit()
            flash('Table saved.', 'success')
            return redirect_back('admin_tables')
        except (ValueError, TypeError):
            db.session.rollback()
            flash('Check table number and seats (number must be unique).', 'error')
        except Exception:
            db.session.rollback()
            flash('Table number is already in use.', 'error')
    return admin_template('tables.html', tables=RestaurantTable.query.order_by(RestaurantTable.id).all())


@app.route('/admin/employees', methods=['GET', 'POST'])
@login_required
def admin_employees():
    if request.method == 'POST':
        try:
            identifier = request.form.get('item_id')
            row = db.session.get(Employee, int(identifier)) if identifier else Employee()
            if row is None:
                abort(404)
            row.code = require_value('code', 20)
            row.name = require_value('name', 100)
            row.position = require_value('position', 100)
            row.salary = money('salary', allow_zero=True)
            row.active = request.form.get('active') == 'on'
            db.session.add(row)
            db.session.commit()
            flash('Employee saved.', 'success')
            return redirect_back('admin_employees')
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
        except Exception:
            db.session.rollback()
            flash('Could not save employee. Check whether ID already exists.', 'error')
    return admin_template('employees.html', employees=Employee.query.order_by(Employee.id).all())


@app.route('/admin/inventory', methods=['GET', 'POST'])
@login_required
def admin_inventory():
    if request.method == 'POST':
        try:
            identifier = request.form.get('item_id')
            row = db.session.get(InventoryItem, int(identifier)) if identifier else InventoryItem()
            if row is None:
                abort(404)
            row.name = require_value('name', 100)
            row.unit = require_value('unit', 20)
            row.quantity = money('quantity', allow_zero=True)
            row.reorder_level = money('reorder_level', allow_zero=True)
            row.supplier = optional('supplier', 120)
            db.session.add(row)
            db.session.commit()
            flash('Inventory record saved.', 'success')
            return redirect_back('admin_inventory')
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    return admin_template('inventory.html', stocks=InventoryItem.query.order_by(InventoryItem.id).all())


@app.get('/admin/customers')
@login_required
def admin_customers():
    customers = Customer.query.order_by(Customer.created_at.desc()).limit(200).all()
    return admin_template('customers.html', customers=customers)


@app.route('/admin/expenses', methods=['GET', 'POST'])
@login_required
def admin_expenses():
    if request.method == 'POST':
        try:
            description = require_value('description', 160)
            amount = money('amount')
            expense_date = date.fromisoformat(require_value('expense_date', 10))
            db.session.add(Expense(description=description, amount=amount, expense_date=expense_date))
            db.session.commit()
            flash('Expense added.', 'success')
            return redirect_back('admin_expenses')
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    return admin_template('expenses.html', expenses=Expense.query.order_by(Expense.expense_date.desc()).limit(200).all())


@app.get('/admin/reports')
@login_required
def admin_reports():
    all_sales = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.status == 'completed').scalar()
    all_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    completed = Order.query.filter_by(status='completed').count()
    breakdown = db.session.query(Order.service_type, func.count(Order.id),
                                 func.coalesce(func.sum(Order.total), 0)).filter(
        Order.status == 'completed').group_by(Order.service_type).all()
    return admin_template('reports.html', all_sales=all_sales, all_expenses=all_expenses,
                          completed=completed, breakdown=breakdown)


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        try:
            info = db.get_or_404(Setting, 1)
            info.name = require_value('name', 120)
            info.subtitle = require_value('subtitle', 120)
            info.owner_name = require_value('owner_name', 100)
            info.address = require_value('address', 255)
            info.phone = require_value('phone', 40)
            info.email = require_value('email', 120)
            opened = time.fromisoformat(require_value('opening_time', 8))
            closed = time.fromisoformat(require_value('closing_time', 8))
            if opened >= closed:
                raise ValueError('Closing time must be later than opening time on the same day.')
            info.opening_time, info.closing_time = opened, closed
            info.seating_capacity = positive_int('seating_capacity', 1000)
            db.session.commit()
            flash('Restaurant profile updated.', 'success')
            return redirect_back('admin_settings')
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    return admin_template('settings.html')


@app.cli.command('init-db')
def init_db_command():
    """Create tables in a pre-created XAMPP MySQL database."""
    db.create_all()
    click.echo('Database tables created. Next: flask --app app seed')


@app.cli.command('seed')
def seed_command():
    """Insert fictional example restaurant, menu, staff and 20 tables (idempotent)."""
    db.create_all()
    if db.session.get(Setting, 1) is None:
        db.session.add(Setting(id=1))
    menu_data = [
        ('F001', 'Chicken Biryani', 'Main Course', 280),
        ('F002', 'Beef Tehari', 'Main Course', 320),
        ('F003', 'Chicken Fried Rice', 'Chinese', 250),
        ('F004', 'Chicken Burger', 'Fast Food', 220),
        ('F005', 'BBQ Chicken Pizza', 'Pizza', 550),
        ('F006', 'French Fries', 'Snacks', 120),
        ('F007', 'Chicken Soup', 'Starter', 180),
        ('F008', 'Fresh Lemonade', 'Drinks', 100),
        ('F009', 'Chocolate Milkshake', 'Drinks', 180),
        ('F010', 'Chocolate Brownie', 'Dessert', 150),
    ]
    for code, name, category, price in menu_data:
        if not MenuItem.query.filter_by(code=code).first():
            db.session.add(MenuItem(code=code, name=name, category=category, price=price))
    staff = [('EMP001', 'Rahim Uddin', 'Manager', 35000),
             ('EMP002', 'Karim Ahmed', 'Head Chef', 30000),
             ('EMP003', 'Hasan Ali', 'Waiter', 15000),
             ('EMP004', 'Sumaiya Akter', 'Cashier', 18000),
             ('EMP005', 'Imran Hossain', 'Delivery Rider', 16000)]
    for code, name, position, salary in staff:
        if not Employee.query.filter_by(code=code).first():
            db.session.add(Employee(code=code, name=name, position=position, salary=salary))
    for num in range(1, 21):
        table_no = f'T{num:02}'
        if not RestaurantTable.query.filter_by(number=table_no).first():
            db.session.add(RestaurantTable(number=table_no, seats=4))
    # Demo offers. Remove or edit these in Admin > Offers before public launch.
    for code, title, description, kind, amount, minimum in [
        ('WELCOME10', 'A spicy welcome treat', 'Take 10% off your food order.', 'percent', 10, 0),
        ('SPICE50', 'A little extra on us', 'Save ৳50 when you spend ৳500 or more.', 'fixed', 50, 500),
    ]:
        if not Offer.query.filter_by(code=code).first():
            db.session.add(Offer(code=code, title=title, description=description,
                                 discount_type=kind, discount_value=amount, min_order=minimum,
                                 active=True, featured=True))
    db.session.commit()
    click.echo('Sample data seeded (10 foods, 5 employees, 20 tables, 2 demo offers).')


@app.cli.command('create-admin')
@click.option('--username', prompt='Admin username')
@click.password_option('--password', confirmation_prompt=True)
def create_admin_command(username, password):
    """Create or update the administrator account. Password typed securely."""
    if len(password) < 10:
        raise click.ClickException('Admin password must have at least 10 characters.')
    user = Admin.query.filter_by(username=username).first()
    if user is None:
        user = Admin(username=username)
        db.session.add(user)
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    click.echo('Admin account saved.')


if __name__ == '__main__':
    app.run(debug=os.environ.get('APP_ENV') == 'development')

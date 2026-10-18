"""Integration tests on temporary SQLite (independent of XAMPP)."""
import os
from datetime import datetime, timedelta

os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'test-only-secret-key-never-use-in-production'
os.environ['APP_ENV'] = 'test'

import pytest
from werkzeug.security import generate_password_hash
from app import app, db, Admin, MenuItem, Order, Reservation, Setting


@pytest.fixture()
def client():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
        runner = app.test_cli_runner()
        result = runner.invoke(args=['seed'])
        assert result.exit_code == 0, result.output
        db.session.add(Admin(username='operator', password_hash=generate_password_hash('test-password-123')))
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def sign_in(client):
    return client.post('/admin/login', data={'username':'operator','password':'test-password-123'}, follow_redirects=True)


def test_public_and_protected_pages(client):
    assert client.get('/').status_code == 200
    page = client.get('/menu')
    assert page.status_code == 200
    assert b'Chicken Biryani' in page.data
    assert b'280.00' in page.data
    assert client.get('/admin').status_code == 302
    assert b'Restaurant Overview' in sign_in(client).data


def test_order_cart_and_admin_updates(client):
    with app.app_context():
        food = MenuItem.query.filter_by(code='F001').one()
        item_id = food.id
    assert client.post(f'/cart/add/{item_id}', data={'quantity':'2'}).status_code == 302
    page = client.get('/cart')
    assert b'560.00' in page.data
    response = client.post('/checkout', data={
        'name':'Example Customer','phone':'01700000000','service_type':'delivery',
        'address':'House 1, Dhanmondi', 'payment_method':'Cash'
    }, follow_redirects=True)
    assert b'Order #' in response.data
    with app.app_context():
        order = Order.query.one()
        assert float(order.total) == 560
        assert order.status == 'new' and order.payment_status == 'unpaid'
        oid = order.id
    sign_in(client)
    assert client.post(f'/admin/orders/{oid}/status', data={'status':'completed'}).status_code == 302
    assert client.post(f'/admin/orders/{oid}/paid', data={'paid':'yes'}).status_code == 302
    with app.app_context():
        order = db.session.get(Order, oid)
        assert order.status == 'completed' and order.payment_status == 'paid'


def test_reservations_obey_capacity(client):
    with app.app_context():
        db.session.get(Setting, 1).seating_capacity = 2
        db.session.commit()
    tomorrow = datetime.now() + timedelta(days=1)
    when = tomorrow.replace(hour=13, minute=0).strftime('%Y-%m-%dT%H:%M')
    payload={'guest_name':'A','phone':'01711111111','party_size':'2','starts_at':when}
    assert client.post('/reserve',data=payload).status_code == 302
    second = dict(payload, guest_name='B', phone='01722222222', party_size='1')
    response = client.post('/reserve',data=second,follow_redirects=True)
    assert b'insufficient seating' in response.data
    with app.app_context():
        assert Reservation.query.count() == 1


def test_pos_creation(client):
    sign_in(client)
    with app.app_context():
        food = MenuItem.query.filter_by(code='F008').one()
        fid = food.id
    response=client.post('/admin/pos', data={
        'name':'Walk-in Guest','phone':'pos-ref-1', 'service_type':'takeaway',
        'payment_method':'Cash', 'menu_item_id':str(fid), 'quantity':'2',
        'paid':'on', 'completed':'on'
    },follow_redirects=True)
    assert b'200.00' in response.data
    with app.app_context():
        order=Order.query.one()
        assert order.status=='completed' and order.payment_status=='paid'


def test_offer_discount_saved_with_order(client):
    from app import Offer, OrderDiscount
    with app.app_context():
        food_id = MenuItem.query.filter_by(code='F001').one().id
    assert b'WELCOME10' in client.get('/offers').data
    client.post(f'/cart/add/{food_id}', data={'quantity': '2'})
    applied = client.post('/offers/apply', data={'code': 'welcome10'}, follow_redirects=True)
    assert b'WELCOME10' in applied.data
    assert b'56.00' in applied.data
    response = client.post('/checkout', data={
        'name': 'Coupon Guest', 'phone': '01799900001', 'service_type': 'takeaway',
        'payment_method': 'Cash'
    }, follow_redirects=True)
    assert b'504.00' in response.data
    assert b'56.00' in response.data
    with app.app_context():
        order = Order.query.one()
        snap = OrderDiscount.query.one()
        assert order.total == 504
        assert snap.code == 'WELCOME10' and snap.subtotal == 560
        assert snap.discount == 56
        assert Offer.query.filter_by(code='WELCOME10').one().used_count == 1


def test_minimum_spend_and_redemption_limit(client):
    from app import Offer
    with app.app_context():
        item_id = MenuItem.query.filter_by(code='F001').one().id
        offer = Offer.query.filter_by(code='WELCOME10').one()
        offer.max_uses = 1
        db.session.commit()
    client.post(f'/cart/add/{item_id}', data={'quantity': '1'})
    too_small = client.post('/offers/apply', data={'code': 'SPICE50'}, follow_redirects=True)
    assert b'Order at least' in too_small.data
    client.post('/offers/apply', data={'code': 'WELCOME10'})
    client.post('/checkout', data={
        'name': 'First Guest', 'phone': '01799900002', 'service_type': 'takeaway',
        'payment_method': 'Cash'
    })
    client.post(f'/cart/add/{item_id}', data={'quantity': '1'})
    exhausted = client.post('/offers/apply', data={'code': 'WELCOME10'}, follow_redirects=True)
    assert b'not valid or has expired' in exhausted.data


def test_admin_can_manage_offers(client):
    from app import Offer
    sign_in(client)
    response = client.post('/admin/offers', data={
        'code': 'HAPPY25', 'title': 'Autumn offer', 'description': 'Enjoy a tasty discount',
        'discount_type': 'percent', 'discount_value': '25', 'min_order': '200',
        'max_discount': '60', 'max_uses': '5', 'active': 'on', 'featured': 'on'
    }, follow_redirects=True)
    assert b'HAPPY25' in response.data
    with app.app_context():
        offer = Offer.query.filter_by(code='HAPPY25').one()
        oid = offer.id
        assert float(offer.max_discount) == 60
    assert client.post(f'/admin/offers/{oid}/toggle', follow_redirects=True).status_code == 200
    assert b'HAPPY25' not in client.get('/offers').data
    with app.app_context():
        assert not db.session.get(Offer, oid).active


def test_pos_offer_reduces_staff_bill(client):
    from app import OrderDiscount
    sign_in(client)
    with app.app_context():
        item_id = MenuItem.query.filter_by(code='F001').one().id
    response = client.post('/admin/pos', data={
        'name': 'Promo Walk-in', 'phone': 'pos-promo-test', 'service_type': 'takeaway',
        'payment_method': 'Cash', 'menu_item_id': str(item_id), 'quantity': '2',
        'offer_code': 'SPICE50', 'paid': 'on'
    }, follow_redirects=True)
    assert b'510.00' in response.data
    with app.app_context():
        assert float(Order.query.one().total) == 510
        assert OrderDiscount.query.one().code == 'SPICE50'

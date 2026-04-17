"""Park City Trips — Luxury Transportation in Park City, Utah."""
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash, session
import config, json, os, uuid, requests as req, smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from blog_data import POSTS


def _send_quick_email(booking):
    """Send email via Resend.com HTTP API (Railway blocks SMTP ports)."""
    if not config.RESEND_API_KEY:
        print("[Email] No RESEND_API_KEY configured")
        return
    vehicle_names = {'small':'Small SUV','midsize':'Midsize SUV','premier':'Premier SUV','luxury':'Luxury SUV'}
    c = booking['customer']
    t = booking['trip']
    bid = booking['id'].upper()
    v = vehicle_names.get(booking['vehicle'], booking['vehicle'])

    html = f"""<div style="font-family:Arial,sans-serif;max-width:550px;margin:0 auto;background:#0a0c10;border-radius:12px;overflow:hidden;">
<div style="background:linear-gradient(135deg,#c9a84c,#e8c65a);padding:20px 28px;text-align:center;">
<h1 style="margin:0;color:#000;font-size:20px;">🚗 New Trip Request</h1></div>
<div style="padding:24px 28px;color:#fff;">
<div style="background:#111318;border:1px solid #1e2130;border-radius:10px;padding:16px;margin-bottom:16px;">
<div style="font-size:11px;color:#c9a84c;letter-spacing:2px;margin-bottom:8px;">ORDER #{bid}</div>
<table style="width:100%;font-size:13px;color:#fff;border-collapse:collapse;">
<tr><td style="padding:5px 0;color:#666;">Customer</td><td style="padding:5px 0;text-align:right;font-weight:700;">{c['name']}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Phone</td><td style="padding:5px 0;text-align:right;"><a href="tel:{c['phone']}" style="color:#c9a84c;">{c['phone']}</a></td></tr>
<tr><td style="padding:5px 0;color:#666;">Email</td><td style="padding:5px 0;text-align:right;">{c.get('email','—')}</td></tr>
<tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:6px 0;"></td></tr>
<tr><td style="padding:5px 0;color:#666;">Vehicle</td><td style="padding:5px 0;text-align:right;font-weight:700;">{v}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Date</td><td style="padding:5px 0;text-align:right;">{t.get('date','—')}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Pickup</td><td style="padding:5px 0;text-align:right;color:#22c55e;">{t.get('pickup','—')}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Dropoff</td><td style="padding:5px 0;text-align:right;color:#ef4444;">{t.get('dropoff','—')}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Flight</td><td style="padding:5px 0;text-align:right;">{t.get('flight_number','—')}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Arrival</td><td style="padding:5px 0;text-align:right;">{t.get('arrival_time','—')}</td></tr>
<tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:6px 0;"></td></tr>
<tr><td style="padding:5px 0;color:#666;">Passengers</td><td style="padding:5px 0;text-align:right;">{t.get('adults','0')} adults, {t.get('children','0')} kids</td></tr>
<tr><td style="padding:5px 0;color:#666;">Bags</td><td style="padding:5px 0;text-align:right;">{t.get('bags','0')} + {t.get('ski_bags','0')} ski</td></tr>
<tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:6px 0;"></td></tr>
<tr><td style="padding:5px 0;color:#666;">Total</td><td style="padding:5px 0;text-align:right;font-size:18px;font-weight:800;color:#c9a84c;">${booking['total']}</td></tr>
</table></div>
{'<div style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);border-radius:8px;padding:10px;font-size:12px;color:#22c55e;margin-bottom:12px;">💳 '+booking.get('card_brand','')+' ****'+booking.get('card_last4','')+'</div>' if booking.get('card_last4') else ''}
<div style="text-align:center;"><a href="https://web-production-d69bf.up.railway.app/admin/bookings?pin=6939" style="display:inline-block;padding:12px 24px;background:#c9a84c;color:#000;border-radius:50px;text-decoration:none;font-weight:700;font-size:13px;">Review & Approve</a></div>
</div></div>"""

    # 1. Email to Hudson (admin notification)
    resp = req.post('https://api.resend.com/emails', json={
        'from': 'Rio Transportation <booking@parkcitytrips.com>',
        'to': [config.NOTIFY_EMAIL],
        'subject': f"🚗 Trip #{bid} — {c['name']} — {v} — ${booking['total']}",
        'html': html,
    }, headers={'Authorization': f'Bearer {config.RESEND_API_KEY}'}, timeout=10)
    print(f"[Email] Admin notification: {resp.status_code} — {resp.text[:200]}")

    # 2. Email to customer (confirmation)
    if c.get('email') and c['email'].strip():
        customer_html = f"""<div style="font-family:Arial,sans-serif;max-width:550px;margin:0 auto;background:#0a0c10;border-radius:12px;overflow:hidden;">
<div style="background:linear-gradient(135deg,#c9a84c,#e8c65a);padding:20px 28px;text-align:center;">
<h1 style="margin:0;color:#000;font-size:20px;">Trip Request Received!</h1>
<p style="margin:4px 0 0;color:rgba(0,0,0,.6);font-size:12px;">Rio Transportation LLC</p></div>
<div style="padding:24px 28px;color:#fff;">
<p style="font-size:15px;margin-bottom:16px;">Hi {c['name'].split()[0]},</p>
<p style="font-size:14px;color:#999;line-height:1.7;margin-bottom:20px;">Thank you for your trip request! This is <strong style="color:#fff;">not a confirmed booking yet</strong> — our team will review and contact you within <strong style="color:#c9a84c;">30 minutes</strong> to confirm your ride.</p>
<div style="background:#111318;border:1px solid #1e2130;border-radius:10px;padding:16px;margin-bottom:16px;">
<div style="font-size:11px;color:#c9a84c;letter-spacing:2px;margin-bottom:8px;">ORDER #{bid}</div>
<table style="width:100%;font-size:13px;color:#fff;border-collapse:collapse;">
<tr><td style="padding:5px 0;color:#666;">Vehicle</td><td style="padding:5px 0;text-align:right;font-weight:700;">{v}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Date</td><td style="padding:5px 0;text-align:right;">{t.get('date','—')}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Pickup</td><td style="padding:5px 0;text-align:right;color:#22c55e;">{t.get('pickup','—')}</td></tr>
<tr><td style="padding:5px 0;color:#666;">Dropoff</td><td style="padding:5px 0;text-align:right;color:#ef4444;">{t.get('dropoff','—')}</td></tr>
<tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:6px 0;"></td></tr>
<tr><td style="padding:5px 0;color:#666;">Estimated Total</td><td style="padding:5px 0;text-align:right;font-size:18px;font-weight:800;color:#c9a84c;">${booking['total']}</td></tr>
</table></div>
<div style="background:rgba(59,130,246,.06);border:1px solid rgba(59,130,246,.15);border-radius:8px;padding:12px;font-size:12px;color:rgba(255,255,255,.6);margin-bottom:16px;">
<strong>💳 Your card will NOT be charged</strong> until we confirm your ride.</div>
<p style="font-size:13px;color:#666;margin-bottom:16px;">Questions? Call or text us anytime:</p>
<div style="text-align:center;margin-bottom:8px;"><a href="tel:+14352146939" style="color:#c9a84c;text-decoration:none;font-weight:700;font-size:15px;">📞 (435) 214-6939</a></div>
<div style="text-align:center;"><a href="https://wa.me/14352146939" style="color:#25d366;text-decoration:none;font-weight:600;font-size:13px;">💬 WhatsApp</a></div>
</div>
<div style="padding:12px 28px;border-top:1px solid #1e2130;font-size:10px;color:#444;text-align:center;">Rio Transportation LLC · Park City, Utah · parkcitytrips.com</div>
</div>"""
        resp2 = req.post('https://api.resend.com/emails', json={
            'from': 'Rio Transportation <booking@parkcitytrips.com>',
            'to': [c['email']],
            'subject': f"Your Trip Request #{bid} — Rio Transportation",
            'html': customer_html,
        }, headers={'Authorization': f'Bearer {config.RESEND_API_KEY}'}, timeout=10)
        print(f"[Email] Customer confirmation to {c['email']}: {resp2.status_code}")


def send_booking_email(booking):
    """Send styled email notification for new trip request."""
    if not config.SMTP_USER:
        print("[Email] SMTP not configured, skipping")
        return
    vehicle_names = {'small':'Small SUV (Eclipse Cross)','midsize':'Midsize SUV (Pathfinder)',
                     'premier':'Premier SUV (GMC Yukon)','luxury':'Luxury SUV (Lincoln Navigator)'}
    v = vehicle_names.get(booking['vehicle'], booking['vehicle'])
    c = booking['customer']
    t = booking['trip']
    bid = booking['id'].upper()

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0c10;color:#fff;border-radius:12px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#c9a84c,#e8c65a);padding:24px 32px;text-align:center;">
            <h1 style="margin:0;color:#000;font-size:22px;">🚗 New Trip Request</h1>
            <p style="margin:4px 0 0;color:rgba(0,0,0,.6);font-size:13px;">Rio Transportation LLC</p>
        </div>
        <div style="padding:28px 32px;">
            <div style="background:#111318;border:1px solid #1e2130;border-radius:10px;padding:18px;margin-bottom:20px;">
                <div style="font-size:11px;color:#c9a84c;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">ORDER #{bid}</div>
                <table style="width:100%;border-collapse:collapse;font-size:14px;color:#fff;">
                    <tr><td style="padding:6px 0;color:#666;">Customer</td><td style="padding:6px 0;text-align:right;font-weight:700;">{c['name']}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Phone</td><td style="padding:6px 0;text-align:right;"><a href="tel:{c['phone']}" style="color:#c9a84c;text-decoration:none;">{c['phone']}</a></td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Email</td><td style="padding:6px 0;text-align:right;">{c.get('email','—')}</td></tr>
                    <tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:8px 0;"></td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Vehicle</td><td style="padding:6px 0;text-align:right;font-weight:700;">{v}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Date</td><td style="padding:6px 0;text-align:right;">{t.get('date','—')}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Pickup</td><td style="padding:6px 0;text-align:right;color:#22c55e;">{t.get('pickup','—')}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Dropoff</td><td style="padding:6px 0;text-align:right;color:#ef4444;">{t.get('dropoff','—')}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Flight</td><td style="padding:6px 0;text-align:right;">{t.get('flight_number','—')}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Arrival</td><td style="padding:6px 0;text-align:right;">{t.get('arrival_time','—')}</td></tr>
                    <tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:8px 0;"></td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Passengers</td><td style="padding:6px 0;text-align:right;">{t.get('adults','0')} adults, {t.get('children','0')} children, {t.get('infants','0')} infants</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Car Seats</td><td style="padding:6px 0;text-align:right;">{t.get('car_seats','0')}</td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Bags</td><td style="padding:6px 0;text-align:right;">{t.get('bags','0')} regular, {t.get('ski_bags','0')} ski</td></tr>
                    {'<tr><td style="padding:6px 0;color:#666;">Notes</td><td style="padding:6px 0;text-align:right;">'+t.get('notes','')+'</td></tr>' if t.get('notes') else ''}
                    <tr><td colspan="2" style="border-bottom:1px solid #1e2130;padding:8px 0;"></td></tr>
                    <tr><td style="padding:6px 0;color:#666;">Base Price</td><td style="padding:6px 0;text-align:right;">${booking['base_price']}</td></tr>
                    {'<tr><td style="padding:6px 0;color:#666;">Premium Stop</td><td style="padding:6px 0;text-align:right;">+$'+str(booking['premium_stop'])+'</td></tr>' if booking.get('premium_stop') else ''}
                    <tr><td style="padding:6px 0;color:#666;">Tip ({booking.get('tip_percent',0)}%)</td><td style="padding:6px 0;text-align:right;">${booking.get('tip_amount',0)}</td></tr>
                    <tr><td style="padding:10px 0;font-size:18px;font-weight:800;">TOTAL</td><td style="padding:10px 0;text-align:right;font-size:18px;font-weight:800;color:#c9a84c;">${booking['total']}</td></tr>
                </table>
            </div>
            {'<div style="background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.15);border-radius:8px;padding:12px;font-size:12px;color:#22c55e;margin-bottom:16px;">💳 Card saved: '+booking.get('card_brand','')+'  ****'+booking.get('card_last4','')+'</div>' if booking.get('card_last4') else ''}
            <div style="text-align:center;margin-top:16px;">
                <a href="https://web-production-d69bf.up.railway.app/admin/bookings?pin=6939" style="display:inline-block;padding:14px 28px;background:#c9a84c;color:#000;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;">Review & Approve Booking</a>
            </div>
        </div>
        <div style="padding:16px 32px;border-top:1px solid #1e2130;font-size:11px;color:#444;text-align:center;">
            Rio Transportation LLC · 1776 Kearns Blvd, Park City, UT 84060 · (435) 214-6939
        </div>
    </div>"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚗 Trip Request #{bid} — {c['name']} — {v}"
        msg['From'] = config.SMTP_USER
        msg['To'] = config.NOTIFY_EMAIL
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(msg)
        print(f"[Email] Trip request #{bid} sent to {config.NOTIFY_EMAIL}")
    except Exception as e:
        print(f"[Email] Error: {e}")
        import traceback
        traceback.print_exc()

# Use /tmp for Railway (persists within a deploy, not across deploys)
# Or use RAILWAY_VOLUME_MOUNT_PATH if a volume is attached
_data_dir = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', os.path.join(os.path.dirname(__file__), 'data'))
BOOKINGS_FILE = os.path.join(_data_dir, 'bookings.json')
os.makedirs(os.path.dirname(BOOKINGS_FILE), exist_ok=True)

def load_bookings():
    try:
        with open(BOOKINGS_FILE) as f: return json.load(f)
    except: return []

def save_bookings(bookings):
    with open(BOOKINGS_FILE, 'w') as f: json.dump(bookings, f, indent=2)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route('/')
def home():
    return render_template('home_v2.html', config=config)


@app.route('/v1')
def home_v1():
    """Old design preserved at /v1 for comparison."""
    return render_template('home.html', config=config)


@app.route('/weather')
def weather():
    return render_template('weather.html', config=config)


@app.route('/about')
def about():
    return render_template('about.html', config=config)


@app.route('/fleet')
def fleet():
    return render_template('fleet.html', config=config)


@app.route('/book')
def book():
    return render_template('book.html', config=config)


@app.route('/book/submit', methods=['POST'])
def book_submit():
    """Save booking and redirect to payment page."""
    data = request.form.to_dict()
    booking_id = str(uuid.uuid4())[:8]
    vehicle = data.get('vehicle', 'premier')
    base_price = config.VEHICLE_PRICES.get(vehicle, 189)
    premium_stop = config.PREMIUM_STOP_PRICE if data.get('premium_stop') else 0

    booking = {
        'id': booking_id,
        'vehicle': vehicle,
        'base_price': base_price,
        'premium_stop': premium_stop,
        'subtotal': base_price + premium_stop,
        'tip_percent': 0,
        'tip_amount': 0,
        'total': base_price + premium_stop,
        'card_id': None,
        'status': 'pending_payment',
        'customer': {
            'name': data.get('name', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
        },
        'trip': {
            'direction': data.get('direction', ''),
            'date': data.get('date', ''),
            'flight_number': data.get('flight_number', ''),
            'arrival_time': data.get('arrival_time', ''),
            'pickup': data.get('pickup', ''),
            'dropoff': data.get('dropoff', ''),
            'destination': data.get('destination', ''),
            'adults': data.get('adults', '2'),
            'children': data.get('children', '0'),
            'infants': data.get('infants', '0'),
            'car_seats': data.get('car_seats', '0'),
            'bags': data.get('bags', '2'),
            'ski_bags': data.get('ski_bags', '0'),
            'notes': data.get('notes', ''),
        },
        'created_at': datetime.now().isoformat(),
        'charged_at': None,
    }

    bookings = load_bookings()
    bookings.append(booking)
    save_bookings(bookings)
    # Also store in session as backup (survives redeploys)
    session[f'booking_{booking_id}'] = booking
    print(f"[Booking] New booking {booking_id}: {data.get('name','')} — {vehicle} ${base_price}")
    return redirect(f'/book/payment/{booking_id}')


@app.route('/book/payment/<booking_id>')
def book_payment(booking_id):
    """Show Square payment form to save card."""
    bookings = load_bookings()
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    if not booking:
        booking = session.get(f'booking_{booking_id}')
    if not booking:
        abort(404)
    return render_template('book_payment.html', booking=booking, config=config,
                           square_app_id=config.SQUARE_APP_ID,
                           square_js_url=config.SQUARE_JS_URL)


@app.route('/book/save-card', methods=['POST'])
def book_save_card():
    """Save card on file via Square (no charge yet)."""
    data = request.get_json()
    booking_id = data.get('booking_id')
    nonce = data.get('nonce')
    tip_percent = int(data.get('tip_percent', 0))

    bookings = load_bookings()
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    # Fallback: check session if file was lost during redeploy
    if not booking:
        booking = session.get(f'booking_{booking_id}')
        if booking:
            bookings.append(booking)
    if not booking or not nonce:
        return jsonify({'error': 'Invalid booking or nonce'}), 400

    # Calculate tip
    subtotal = booking['subtotal']
    tip_amount = round(subtotal * tip_percent / 100)
    total = subtotal + tip_amount

    # Save card on file via Square API
    square_url = 'https://connect.squareup.com' if config.SQUARE_ENVIRONMENT == 'production' else 'https://connect.squareupsandbox.com'
    try:
        # First create a customer
        cust_resp = req.post(f'{square_url}/v2/customers', json={
            'given_name': booking['customer']['name'].split()[0] if booking['customer']['name'] else 'Guest',
            'family_name': ' '.join(booking['customer']['name'].split()[1:]) if len(booking['customer']['name'].split()) > 1 else '',
            'phone_number': booking['customer']['phone'],
            'email_address': booking['customer']['email'],
        }, headers={'Authorization': f'Bearer {config.SQUARE_ACCESS_TOKEN}', 'Content-Type': 'application/json'})
        customer_id = cust_resp.json().get('customer', {}).get('id', '')

        # Save card on file
        print(f"[Square] Customer created: {customer_id}")
        print(f"[Square] Saving card with nonce: {nonce[:30]}...")
        card_resp = req.post(f'{square_url}/v2/cards', json={
            'idempotency_key': str(uuid.uuid4()),
            'source_id': nonce,
            'card': {
                'customer_id': customer_id,
            }
        }, headers={'Authorization': f'Bearer {config.SQUARE_ACCESS_TOKEN}', 'Content-Type': 'application/json'})
        print(f"[Square] Card API response {card_resp.status_code}: {card_resp.text[:500]}")

        card_data = card_resp.json()
        if 'card' in card_data:
            card_id = card_data['card']['id']
            last4 = card_data['card'].get('last_4', '****')
            brand = card_data['card'].get('card_brand', '')

            booking['card_id'] = card_id
            booking['card_last4'] = last4
            booking['card_brand'] = brand
            booking['customer_id'] = customer_id
            booking['tip_percent'] = tip_percent
            booking['tip_amount'] = tip_amount
            booking['total'] = total
            booking['status'] = 'pending_approval'
            save_bookings(bookings)

            print(f"[Square] Card saved for booking {booking_id}: {brand} ****{last4}")
            # Send email — save booking first so it persists even if email fails
            save_bookings(bookings)
            try:
                _send_quick_email(booking)
                print(f"[Email] Sent OK for #{booking_id}")
            except Exception as email_err:
                print(f"[Email] FAILED: {email_err}")
                import traceback
                traceback.print_exc()
            return jsonify({'success': True, 'booking_id': booking_id})
        else:
            errors = card_data.get('errors', [{}])
            msg = errors[0].get('detail', 'Unknown error') if errors else 'Card save failed'
            print(f"[Square] Card error: {msg}")
            return jsonify({'error': msg}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/book/confirm/<booking_id>')
def book_confirm(booking_id):
    bookings = load_bookings()
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    name = booking['customer']['name'] if booking else 'there'
    return render_template('book_confirm.html', name=name, booking=booking)


@app.route('/admin/bookings')
def admin_bookings():
    """Hudson's booking management panel."""
    pin = request.args.get('pin', '')
    if pin != '6939':  # last 4 digits of phone
        return 'Access denied. Use ?pin=XXXX', 403
    bookings = sorted(load_bookings(), key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('admin_bookings.html', bookings=bookings, config=config)


@app.route('/admin/bookings/<booking_id>/charge', methods=['POST'])
def admin_charge_booking(booking_id):
    """Charge a saved card for an approved booking."""
    pin = request.form.get('pin', '')
    if pin != '6939':
        return jsonify({'error': 'Unauthorized'}), 403

    bookings = load_bookings()
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    if not booking or not booking.get('card_id'):
        return jsonify({'error': 'Booking not found or no card'}), 404

    square_url = 'https://connect.squareup.com' if config.SQUARE_ENVIRONMENT == 'production' else 'https://connect.squareupsandbox.com'
    total_cents = int(booking['total'] * 100)

    try:
        resp = req.post(f'{square_url}/v2/payments', json={
            'idempotency_key': str(uuid.uuid4()),
            'source_id': booking['card_id'],
            'customer_id': booking.get('customer_id', ''),
            'amount_money': {
                'amount': total_cents,
                'currency': 'USD',
            },
            'note': f"Rio Transportation — {booking['vehicle']} — {booking['trip']['date']}",
        }, headers={'Authorization': f'Bearer {config.SQUARE_ACCESS_TOKEN}', 'Content-Type': 'application/json'})

        pay_data = resp.json()
        if 'payment' in pay_data:
            booking['status'] = 'charged'
            booking['charged_at'] = datetime.now().isoformat()
            booking['payment_id'] = pay_data['payment']['id']
            save_bookings(bookings)
            print(f"[Square] Charged ${booking['total']} for booking {booking_id}")
            return redirect(f'/admin/bookings?pin=6939&msg=Charged+${booking["total"]}+successfully')
        else:
            errors = pay_data.get('errors', [{}])
            msg = errors[0].get('detail', 'Payment failed')
            return redirect(f'/admin/bookings?pin=6939&msg=Error:+{msg}')

    except Exception as e:
        return redirect(f'/admin/bookings?pin=6939&msg=Error:+{str(e)}')


@app.route('/blog')
def blog():
    return render_template('blog.html', posts=POSTS, config=config)


@app.route('/blog/<slug>')
def blog_post(slug):
    post = next((p for p in POSTS if p['slug'] == slug), None)
    if not post:
        abort(404)
    return render_template('blog_post.html', post=post, config=config)


# SEO Landing Pages
SEO_PAGES = {
    'slc-airport-to-park-city': {
        'title': 'SLC Airport to Park City Shuttle | Private SUV from $129',
        'h1': 'Salt Lake City Airport to Park City',
        'desc': 'Private luxury SUV shuttle from Salt Lake City International Airport (SLC) to Park City, Utah. Door-to-door service, flight tracking, from $129. Book now!',
        'keywords': 'SLC airport to Park City, Salt Lake City airport shuttle, SLC to Park City shuttle, airport transfer Park City',
        'content': 'Looking for a reliable ride from Salt Lake City Airport to Park City? Rio Transportation offers private luxury SUV service with professional drivers who monitor your flight and text you before landing. The drive takes approximately 40-50 minutes along scenic I-80 through Parley\'s Canyon.',
    },
    'park-city-taxi': {
        'title': 'Park City Taxi | 24/7 Private Car Service | (435) 214-6939',
        'h1': 'Park City Taxi & Car Service',
        'desc': 'Need a taxi in Park City, Utah? Rio Transportation offers 24/7 private luxury SUV service. Airport transfers, local rides, ski resorts. Call (435) 214-6939.',
        'keywords': 'Park City taxi, taxi near me Park City, Park City cab, Park City car service, taxi Park City Utah',
        'content': 'Skip the wait for a traditional taxi. Rio Transportation provides private luxury SUV service throughout Park City, Utah. Whether you need a ride to the airport, a restaurant on Main Street, or a ski resort, our professional drivers are available 24/7.',
    },
    'park-city-airport-shuttle': {
        'title': 'Park City Airport Shuttle | Private SUV Transfer | From $129',
        'h1': 'Park City Airport Shuttle Service',
        'desc': 'Private airport shuttle between Park City and Salt Lake City Airport. Luxury SUVs, professional drivers, all-inclusive pricing from $129. No shared rides.',
        'keywords': 'Park City airport shuttle, Park City shuttle, airport shuttle Park City Utah, private shuttle Park City',
        'content': 'Unlike shared shuttle services that make multiple stops, Rio Transportation provides direct, private door-to-door service between Salt Lake City Airport and your Park City destination. Our fleet includes GMC Yukon, Nissan Pathfinder, and Cadillac Escalade vehicles.',
    },
    'deer-valley-transportation': {
        'title': 'Deer Valley Transportation | Luxury Shuttle from SLC Airport',
        'h1': 'Deer Valley Resort Transportation',
        'desc': 'Luxury transportation to Deer Valley Resort from Salt Lake City Airport. Private SUVs, ski equipment welcome, from $129. Book your Deer Valley shuttle.',
        'keywords': 'Deer Valley transportation, Deer Valley shuttle, Deer Valley airport shuttle, Deer Valley car service',
        'content': 'Getting to Deer Valley Resort has never been easier. Rio Transportation offers premium private SUV service from Salt Lake City Airport directly to your Deer Valley hotel, condo, or lodge. Our vehicles accommodate ski and snowboard equipment with ease.',
    },
    'park-city-wedding-transportation': {
        'title': 'Park City Wedding Transportation | Luxury SUV & Event Service',
        'h1': 'Wedding Transportation in Park City',
        'desc': 'Elegant luxury transportation for Park City weddings and events. Cadillac Escalade, GMC Yukon. Guest shuttles, bridal party transfers. Book now!',
        'keywords': 'Park City wedding transportation, wedding shuttle Park City, event transportation Park City, luxury car wedding Utah',
        'content': 'Make your special day perfect with elegant luxury transportation. Rio Transportation provides wedding party transfers, guest shuttles between venues, and airport pickups for out-of-town guests. Our Cadillac Escalade and GMC Yukon fleet adds sophistication to any celebration.',
    },
    'park-city-ski-shuttle': {
        'title': 'Park City Ski Shuttle | Resort Transfers | From $129',
        'h1': 'Park City Ski Resort Shuttle',
        'desc': 'Private ski shuttle to Park City Mountain and Deer Valley resorts from SLC Airport. Luxury SUVs, ski equipment welcome, professional drivers.',
        'keywords': 'Park City ski shuttle, ski resort shuttle Park City, Park City Mountain shuttle, ski taxi Park City',
        'content': 'Hit the slopes faster with Rio Transportation\'s private ski shuttle service. We provide direct transfers from Salt Lake City Airport to Park City Mountain Resort, Deer Valley, and surrounding ski areas. Our luxury SUVs have plenty of room for skis, snowboards, and luggage.',
    },
    'park-city-corporate-transportation': {
        'title': 'Park City Corporate Transportation | Group Shuttle Service',
        'h1': 'Corporate Transportation in Park City',
        'desc': 'Professional corporate transportation in Park City, Utah. Group shuttles, conference transfers, team events. Luxury SUVs. Book for your next retreat.',
        'keywords': 'Park City corporate transportation, corporate shuttle Park City, group transportation Park City, conference shuttle Utah',
        'content': 'Impress your team and clients with professional luxury transportation. Rio Transportation handles corporate retreats, conference shuttles, and team-building event transfers throughout Park City and the Wasatch Back region.',
    },
}


@app.route('/s/<slug>')
def seo_page(slug):
    page = SEO_PAGES.get(slug)
    if not page:
        abort(404)
    return render_template('seo_page.html', page=page, config=config, vehicles=config.VEHICLES)


@app.route('/sitemap.xml')
def sitemap():
    from flask import Response
    pages = ['/'] + [f'/s/{s}' for s in SEO_PAGES] + ['/blog'] + [f'/blog/{p["slug"]}' for p in POSTS]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        xml += f'  <url><loc>https://www.parkcitytrips.com{p}</loc><changefreq>weekly</changefreq><priority>{"1.0" if p=="/" else "0.8"}</priority></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')


@app.route('/robots.txt')
def robots():
    from flask import Response
    txt = "User-agent: *\nAllow: /\nSitemap: https://www.parkcitytrips.com/sitemap.xml\n"
    return Response(txt, mimetype='text/plain')


@app.route('/api/quote', methods=['POST'])
def api_quote():
    """Calculate price quote."""
    data = request.json or {}
    vehicle_id = data.get('vehicle', '')
    route = data.get('route', 'slc-pc')
    passengers = int(data.get('passengers', 1))

    vehicle = next((v for v in config.VEHICLES if v['id'] == vehicle_id), None)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 400

    route_info = config.ROUTES.get(route, config.ROUTES['slc-pc'])
    price = round(vehicle['price'] * route_info['multiplier'])

    return jsonify({
        'price': price,
        'vehicle': vehicle['name'],
        'route': route_info['name'],
        'passengers': passengers,
    })


@app.route('/api/contact', methods=['POST'])
def api_contact():
    """Handle contact form."""
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()

    if not name or not message:
        return jsonify({'error': 'Name and message required'}), 400

    # For now just log — later integrate email/WhatsApp
    print(f"[Contact] {name} | {email} | {phone} | {message}")
    return jsonify({'success': True, 'message': 'Message sent!'})


if __name__ == '__main__':
    print(f"  Park City Trips")
    print(f"  http://localhost:{config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=True)

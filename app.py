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
    vehicle_names = {'small':'Comfort Electric','midsize':'Midsize SUV','premier':'Premier SUV','luxury':'Luxury SUV'}
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
        'to': [e.strip() for e in config.NOTIFY_EMAIL.split(',')],
        'subject': f"🚗 Trip #{bid} — {c['name']} — {v} — ${booking['total']}",
        'html': html,
    }, headers={'Authorization': f'Bearer {config.RESEND_API_KEY}'}, timeout=10)
    print(f"[Email] Admin notification: {resp.status_code} — {resp.text[:200]}")

    # 2. Email to customer (confirmation)
    if c.get('email') and c['email'].strip():
        customer_html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;background:#ffffff;">
<div style="padding:32px 32px 24px;border-bottom:3px solid #000;">
<h1 style="margin:0;color:#000;font-size:22px;font-weight:800;">Rio Transportation</h1>
</div>
<div style="padding:28px 32px;">
<p style="font-size:15px;color:#333;margin-bottom:6px;">Hi {c['name'].split()[0]},</p>
<p style="font-size:14px;color:#666;line-height:1.7;margin-bottom:24px;">Thank you for your trip request. This is <strong style="color:#000;">not a confirmed booking yet</strong> — our team will contact you within <strong style="color:#000;">30 minutes</strong> to confirm.</p>
<div style="background:#f8f8f6;border:1px solid #e8e8e4;border-radius:8px;padding:20px;margin-bottom:20px;">
<div style="font-size:10px;color:#999;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">ORDER #{bid}</div>
<table style="width:100%;font-size:14px;color:#333;border-collapse:collapse;">
<tr><td style="padding:6px 0;color:#999;">Vehicle</td><td style="padding:6px 0;text-align:right;font-weight:700;">{v}</td></tr>
<tr><td style="padding:6px 0;color:#999;">Date</td><td style="padding:6px 0;text-align:right;">{t.get('date','—')}</td></tr>
<tr><td style="padding:6px 0;color:#999;">Pickup</td><td style="padding:6px 0;text-align:right;">{t.get('pickup','—')}</td></tr>
<tr><td style="padding:6px 0;color:#999;">Dropoff</td><td style="padding:6px 0;text-align:right;">{t.get('dropoff','—')}</td></tr>
<tr><td colspan="2" style="border-bottom:1px solid #e8e8e4;padding:8px 0;"></td></tr>
<tr><td style="padding:8px 0;font-weight:700;color:#000;">Estimated Total</td><td style="padding:8px 0;text-align:right;font-size:20px;font-weight:800;color:#000;">${booking['total']}</td></tr>
</table></div>
<div style="background:#f0f7ff;border:1px solid #d4e5f7;border-radius:6px;padding:12px 16px;font-size:13px;color:#555;margin-bottom:24px;">
💳 Your card will <strong>not be charged</strong> until we confirm your ride.</div>
<div style="text-align:center;margin-bottom:24px;">
<p style="font-size:13px;color:#999;margin-bottom:12px;">Questions? Contact us anytime</p>
<a href="tel:+14352146939" style="display:inline-block;padding:10px 24px;background:#000;color:#fff;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;margin-right:8px;">📞 (435) 214-6939</a>
<a href="https://wa.me/14352146939" style="display:inline-block;padding:10px 24px;background:#25d366;color:#fff;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;">💬 WhatsApp</a>
</div>
</div>
<div style="padding:16px 32px;border-top:1px solid #eee;font-size:11px;color:#bbb;text-align:center;">Rio Transportation LLC · Park City, Utah · parkcitytrips.com</div>
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
    vehicle_names = {'small':'Comfort Electric (Tesla Model Y)','midsize':'Midsize SUV (Pathfinder)',
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
# Visitor tracking
_recent_visitors = {}
VISITORS_FILE = os.path.join(_data_dir, 'visitors.json')

def load_visitors():
    try:
        with open(VISITORS_FILE) as f: return json.load(f)
    except: return []

def save_visitor(entry):
    visitors = load_visitors()
    visitors.append(entry)
    # Keep last 1000 entries
    if len(visitors) > 1000:
        visitors = visitors[-1000:]
    with open(VISITORS_FILE, 'w') as f: json.dump(visitors, f)

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


@app.before_request
def canonicalize_host():
    """301 redirect www.parkcitytrips.com → parkcitytrips.com so Google
    treats the site as a single canonical host. Matches sitemap.xml."""
    host = (request.host or '').lower()
    if host.startswith('www.parkcitytrips.com'):
        new_url = request.url.replace('://www.parkcitytrips.com', '://parkcitytrips.com', 1)
        return redirect(new_url, code=301)


@app.after_request
def add_seo_headers(response):
    """Add cache + security headers for SEO performance."""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=2592000'  # 30 days
    elif not request.path.startswith('/admin') and not request.path.startswith('/signin'):
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 min for pages
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@app.route('/')
def home():
    return render_template('home_v2.html', config=config)


@app.route('/v1')
def home_v1():
    """Old design preserved at /v1 for comparison."""
    return render_template('home.html', config=config)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        email = request.form.get('email', '')
        if pin == config.ADMIN_PIN:
            session['admin'] = True
            session['admin_email'] = email
            session['admin_pin'] = pin
            return redirect('/admin')
        return render_template('signin.html', error='Invalid PIN')
    return render_template('signin.html', error=None)


@app.route('/signout')
def signout():
    session.clear()
    return redirect('/')


@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect('/signin')
    # Load visitors
    visitors = load_visitors()
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    week_ago = (now - __import__('datetime').timedelta(days=7)).isoformat()

    visitors_today = sum(1 for v in visitors if v.get('timestamp', '')[:10] == today_str)
    visitors_7d = sum(1 for v in visitors if v.get('timestamp', '') >= week_ago)

    # Source breakdown (last 7 days)
    sources = {}
    recent = [v for v in visitors if v.get('timestamp', '') >= week_ago]
    for v in recent:
        src = v.get('source', 'Direct')
        sources[src] = sources.get(src, 0) + 1
    total_visits = max(len(recent), 1)
    src_colors = {'Google': '#22c55e', 'Direct': '#6366f1', 'Facebook': '#3b82f6', 'Instagram': '#ec4899', 'Bing': '#f59e0b', 'Yelp': '#ef4444', 'TripAdvisor': '#06b6d4'}
    top_sources = sorted([{'name': k, 'count': v, 'pct': round(v / total_visits * 100), 'color': src_colors.get(k, '#666')} for k, v in sources.items()], key=lambda x: -x['count'])[:8]

    # Load bookings
    bookings = sorted(load_bookings(), key=lambda b: b.get('created_at', ''), reverse=True)
    revenue = sum(b.get('total', 0) for b in bookings if b.get('status') == 'charged')

    return render_template('admin_dashboard.html',
        visitors_today=visitors_today, visitors_7d=visitors_7d,
        bookings_total=len(bookings), revenue=revenue,
        bookings=bookings, top_sources=top_sources,
        recent_visitors=list(reversed(visitors[-20:])))


@app.route('/admin/visitors')
def admin_visitors():
    if not session.get('admin'):
        return redirect('/signin')
    visitors = list(reversed(load_visitors()))
    return render_template('admin_dashboard.html',
        visitors_today=len([v for v in visitors if v.get('timestamp','')[:10]==datetime.now().strftime('%Y-%m-%d')]),
        visitors_7d=len(visitors), bookings_total=0, revenue=0,
        bookings=[], top_sources=[], recent_visitors=visitors[:100])


@app.route('/admin/seo')
def admin_seo():
    if not session.get('admin'):
        return redirect('/signin')
    visitors = load_visitors()
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    week_ago = (now - __import__('datetime').timedelta(days=7)).isoformat()
    month_ago = (now - __import__('datetime').timedelta(days=30)).isoformat()

    visitors_today = sum(1 for v in visitors if v.get('timestamp', '')[:10] == today_str)
    visitors_7d = sum(1 for v in visitors if v.get('timestamp', '') >= week_ago)
    visitors_30d = sum(1 for v in visitors if v.get('timestamp', '') >= month_ago)
    mobile_count = sum(1 for v in visitors if v.get('device') == 'Mobile')
    pct_mobile = round(mobile_count / max(len(visitors), 1) * 100)
    countries = set(v.get('country', '') for v in visitors if v.get('country'))

    # Top pages
    pages = {}
    for v in visitors:
        p = v.get('page', '/')
        name = {'/' : 'Home', '/book': 'Booking', '/fleet': 'Fleet', '/about': 'About', '/weather': 'Weather', '/blog': 'Blog'}.get(p, p)
        pages[name] = pages.get(name, 0) + 1
    max_page = max(pages.values()) if pages else 1
    top_pages = sorted([{'name': k, 'count': v, 'pct': round(v / max_page * 100)} for k, v in pages.items()], key=lambda x: -x['count'])[:10]

    # Top sources
    sources = {}
    for v in visitors:
        s = v.get('source', 'Direct')
        sources[s] = sources.get(s, 0) + 1
    max_src = max(sources.values()) if sources else 1
    src_colors = {'Google': '#22c55e', 'Direct': '#6366f1', 'Facebook': '#3b82f6', 'Instagram': '#ec4899', 'Bing': '#f59e0b', 'Yelp': '#ef4444'}
    top_sources = sorted([{'name': k, 'count': v, 'pct': round(v / max_src * 100), 'color': src_colors.get(k, '#666')} for k, v in sources.items()], key=lambda x: -x['count'])[:8]

    # Top countries
    country_data = {}
    for v in visitors:
        c = v.get('country', '')
        if c:
            flag = v.get('flag', '🌐')
            country_data[c] = {'name': c, 'flag': flag, 'count': country_data.get(c, {}).get('count', 0) + 1}
    top_countries = sorted(country_data.values(), key=lambda x: -x['count'])[:10]

    # Site pages
    site_pages = [
        {'url': '/', 'title': 'Home'},
        {'url': '/fleet', 'title': 'Fleet'},
        {'url': '/about', 'title': 'About'},
        {'url': '/weather', 'title': 'Weather & Conditions'},
        {'url': '/book', 'title': 'Booking'},
        {'url': '/blog', 'title': 'Blog'},
    ]

    return render_template('admin_seo.html',
        visitors_today=visitors_today, visitors_7d=visitors_7d, visitors_30d=visitors_30d,
        pct_mobile=pct_mobile, unique_countries=len(countries),
        top_pages=top_pages, top_sources=top_sources, top_countries=top_countries,
        site_pages=site_pages)


@app.route('/admin/new-booking', methods=['GET', 'POST'])
def admin_new_booking():
    if not session.get('admin'):
        return redirect('/signin')
    if request.method == 'POST':
        data = request.form.to_dict()
        booking_id = str(uuid.uuid4())[:8]
        vehicle = data.get('vehicle', 'premier')
        base_price = config.VEHICLE_PRICES.get(vehicle, 189)
        premium_stop = config.PREMIUM_STOP_PRICE if data.get('premium_stop') else 0
        total = base_price + premium_stop

        booking = {
            'id': booking_id, 'vehicle': vehicle, 'base_price': base_price,
            'premium_stop': premium_stop, 'subtotal': total, 'tip_percent': 0,
            'tip_amount': 0, 'total': total, 'card_id': None, 'card_last4': '',
            'card_brand': '', 'status': 'confirmed_manual',
            'customer': {'name': data.get('name',''), 'phone': data.get('phone',''), 'email': data.get('email','')},
            'trip': {'date': data.get('date',''), 'pickup': data.get('pickup',''), 'dropoff': data.get('dropoff',''),
                     'flight_number': data.get('flight_number',''), 'arrival_time': data.get('arrival_time',''),
                     'adults': data.get('adults','1'), 'children': data.get('children','0'),
                     'infants': data.get('infants','0'), 'car_seats': data.get('car_seats','0'),
                     'bags': data.get('bags','0'), 'ski_bags': data.get('ski_bags','0'),
                     'notes': data.get('notes','')},
            'created_at': datetime.now().isoformat(), 'charged_at': None,
        }
        bookings = load_bookings()
        bookings.append(booking)
        save_bookings(bookings)

        # Send confirmation email to client
        if data.get('email') and config.RESEND_API_KEY:
            vehicle_names = {'small':'Comfort Electric','midsize':'Midsize SUV','premier':'Premier SUV','luxury':'Luxury SUV'}
            v = vehicle_names.get(vehicle, vehicle)
            bid = booking_id.upper()
            c = booking['customer']
            t = booking['trip']
            customer_html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;background:#ffffff;">
<div style="padding:32px 32px 24px;border-bottom:3px solid #000;">
<h1 style="margin:0;color:#000;font-size:22px;font-weight:800;">Rio Transportation</h1>
</div>
<div style="padding:28px 32px;">
<p style="font-size:15px;color:#333;margin-bottom:6px;">Hi {c['name'].split()[0] if c['name'] else 'there'},</p>
<p style="font-size:14px;color:#666;line-height:1.7;margin-bottom:24px;">Your ride has been <strong style="color:#000;">confirmed</strong>! Here are your trip details:</p>
<div style="background:#f8f8f6;border:1px solid #e8e8e4;border-radius:8px;padding:20px;margin-bottom:20px;">
<div style="font-size:10px;color:#999;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">BOOKING #{bid}</div>
<table style="width:100%;font-size:14px;color:#333;border-collapse:collapse;">
<tr><td style="padding:6px 0;color:#999;">Vehicle</td><td style="padding:6px 0;text-align:right;font-weight:700;">{v}</td></tr>
<tr><td style="padding:6px 0;color:#999;">Date</td><td style="padding:6px 0;text-align:right;font-weight:700;">{t.get('date','—')}</td></tr>
<tr><td style="padding:6px 0;color:#999;">Pickup</td><td style="padding:6px 0;text-align:right;">{t.get('pickup','—')}</td></tr>
<tr><td style="padding:6px 0;color:#999;">Dropoff</td><td style="padding:6px 0;text-align:right;">{t.get('dropoff','—')}</td></tr>
{f'<tr><td style="padding:6px 0;color:#999;">Flight</td><td style="padding:6px 0;text-align:right;">{t["flight_number"]}</td></tr>' if t.get('flight_number') else ''}
{f'<tr><td style="padding:6px 0;color:#999;">Arrival</td><td style="padding:6px 0;text-align:right;">{t["arrival_time"]}</td></tr>' if t.get('arrival_time') else ''}
<tr><td colspan="2" style="border-bottom:1px solid #e8e8e4;padding:8px 0;"></td></tr>
<tr><td style="padding:8px 0;font-weight:700;color:#000;">Total</td><td style="padding:8px 0;text-align:right;font-size:20px;font-weight:800;color:#000;">${total}</td></tr>
</table></div>
<div style="background:#f0f7ff;border:1px solid #d4e5f7;border-radius:6px;padding:12px 16px;font-size:13px;color:#555;margin-bottom:24px;">
✅ Your ride is <strong>confirmed</strong>. Our driver will track your flight and contact you before arrival.</div>
<div style="text-align:center;margin-bottom:24px;">
<p style="font-size:13px;color:#999;margin-bottom:12px;">Questions? Contact us anytime</p>
<a href="tel:+14352146939" style="display:inline-block;padding:10px 24px;background:#000;color:#fff;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;margin-right:8px;">📞 (435) 214-6939</a>
<a href="https://wa.me/14352146939" style="display:inline-block;padding:10px 24px;background:#25d366;color:#fff;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;">💬 WhatsApp</a>
</div></div>
<div style="padding:16px 32px;border-top:1px solid #eee;font-size:11px;color:#bbb;text-align:center;">Rio Transportation LLC · Park City, Utah · parkcitytrips.com</div>
</div>"""
            try:
                req.post('https://api.resend.com/emails', json={
                    'from': 'Rio Transportation <booking@parkcitytrips.com>',
                    'to': [data['email']],
                    'subject': f'Booking Confirmed #{bid} — Rio Transportation',
                    'html': customer_html,
                }, headers={'Authorization': f'Bearer {config.RESEND_API_KEY}'}, timeout=10)
                print(f"[Email] Manual booking confirmation sent to {data['email']}")
            except Exception as e:
                print(f"[Email] Error: {e}")

        return redirect(f'/admin/bookings?pin={config.ADMIN_PIN}&msg=Booking+{booking_id}+created+and+email+sent')
    return render_template('admin_new_booking.html')


@app.route('/admin/email-preview')
def admin_email_preview():
    """Preview the booking confirmation email template."""
    if not session.get('admin'):
        return redirect('/signin')
    html = """<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;background:#ffffff;">
<div style="padding:32px 32px 24px;border-bottom:3px solid #000;">
<h1 style="margin:0;color:#000;font-size:22px;font-weight:800;">Rio Transportation</h1>
</div>
<div style="padding:28px 32px;">
<p style="font-size:15px;color:#333;margin-bottom:6px;">Hi John,</p>
<p style="font-size:14px;color:#666;line-height:1.7;margin-bottom:24px;">Your ride has been <strong style="color:#000;">confirmed</strong>! Here are your trip details:</p>
<div style="background:#f8f8f6;border:1px solid #e8e8e4;border-radius:8px;padding:20px;margin-bottom:20px;">
<div style="font-size:10px;color:#999;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">BOOKING #A1B2C3D4</div>
<table style="width:100%;font-size:14px;color:#333;border-collapse:collapse;">
<tr><td style="padding:6px 0;color:#999;">Vehicle</td><td style="padding:6px 0;text-align:right;font-weight:700;">Premier SUV (GMC Yukon)</td></tr>
<tr><td style="padding:6px 0;color:#999;">Date</td><td style="padding:6px 0;text-align:right;font-weight:700;">April 25, 2026</td></tr>
<tr><td style="padding:6px 0;color:#999;">Pickup</td><td style="padding:6px 0;text-align:right;">SLC Airport, Terminal 1</td></tr>
<tr><td style="padding:6px 0;color:#999;">Dropoff</td><td style="padding:6px 0;text-align:right;">Montage Deer Valley</td></tr>
<tr><td style="padding:6px 0;color:#999;">Flight</td><td style="padding:6px 0;text-align:right;">DL1234</td></tr>
<tr><td style="padding:6px 0;color:#999;">Arrival</td><td style="padding:6px 0;text-align:right;">2:30 PM</td></tr>
<tr><td colspan="2" style="border-bottom:1px solid #e8e8e4;padding:8px 0;"></td></tr>
<tr><td style="padding:8px 0;font-weight:700;color:#000;">Total</td><td style="padding:8px 0;text-align:right;font-size:20px;font-weight:800;color:#000;">$189</td></tr>
</table></div>
<div style="background:#f0f7ff;border:1px solid #d4e5f7;border-radius:6px;padding:12px 16px;font-size:13px;color:#555;margin-bottom:24px;">
✅ Your ride is <strong>confirmed</strong>. Our driver will track your flight and contact you before arrival.</div>
<div style="text-align:center;margin-bottom:24px;">
<p style="font-size:13px;color:#999;margin-bottom:12px;">Questions? Contact us anytime</p>
<a href="tel:+14352146939" style="display:inline-block;padding:10px 24px;background:#000;color:#fff;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;margin-right:8px;">📞 (435) 214-6939</a>
<a href="https://wa.me/14352146939" style="display:inline-block;padding:10px 24px;background:#25d366;color:#fff;border-radius:50px;text-decoration:none;font-weight:700;font-size:14px;">💬 WhatsApp</a>
</div></div>
<div style="padding:16px 32px;border-top:1px solid #eee;font-size:11px;color:#bbb;text-align:center;">Rio Transportation LLC · Park City, Utah · parkcitytrips.com</div>
</div>"""
    return f"""<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Email Preview</title><style>body{{background:#f5f5f5;padding:40px 20px;margin:0;}}</style></head>
<body><div style="text-align:center;margin-bottom:20px;font-family:Arial;font-size:13px;color:#999;">EMAIL TEMPLATE PREVIEW — <a href="/admin">Back to Admin</a></div>{html}</body></html>"""


@app.route('/admin/crm')
def admin_crm():
    if not session.get('admin'):
        return redirect('/signin')
    # Fetch clients + quotes + finance from TravelForza API
    headers = {'X-API-Key': config.TRANSP_API_KEY}
    try:
        clients = req.get(f'{config.TRAVELFORZA_API}/api/transp/clients', headers=headers, timeout=10).json().get('clients', [])
    except: clients = []
    try:
        quotes = req.get(f'{config.TRAVELFORZA_API}/api/transp/quotes', headers=headers, timeout=10).json().get('quotes', [])
    except: quotes = []
    try:
        finance = req.get(f'{config.TRAVELFORZA_API}/api/transp/finance', headers=headers, timeout=10).json()
    except: finance = {'summary': {}, 'expenses': []}
    return render_template('admin_crm.html', clients=clients, quotes=quotes, finance=finance)


@app.route('/experiences')
def experiences():
    return render_template('experiences.html', config=config)


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


@app.route('/api/visitor', methods=['POST'])
def track_visitor():
    """Track visitor and notify Hudson via email."""
    import threading
    ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or request.remote_addr
    now = datetime.now().timestamp()

    # Skip if same IP visited in last 2 hours
    if ip in _recent_visitors and (now - _recent_visitors[ip]) < 7200:
        return jsonify({'ok': True, 'cached': True})

    # Skip bots and local
    if not ip or ip.startswith('127.') or ip.startswith('10.'):
        return jsonify({'ok': True})

    _recent_visitors[ip] = now

    # Get visitor data from JS beacon
    data = request.get_json() or {}
    page = data.get('page', '/')
    title = data.get('title', '')
    referrer = data.get('referrer', '')
    utm_source = data.get('utm_source', '')
    screen_size = data.get('screen', '')
    lang = data.get('lang', '')
    ua = request.headers.get('User-Agent', '')[:150]
    device = 'Mobile' if any(x in ua for x in ['Mobile','iPhone','Android','iPad']) else 'Desktop'
    browser = 'Chrome' if 'Chrome' in ua else 'Safari' if 'Safari' in ua else 'Firefox' if 'Firefox' in ua else 'Other'

    # Determine traffic source
    source = 'Direct'
    if utm_source:
        source = utm_source.capitalize()
    elif referrer:
        ref = referrer.lower()
        if 'google' in ref: source = 'Google'
        elif 'facebook' in ref or 'fb.' in ref: source = 'Facebook'
        elif 'instagram' in ref: source = 'Instagram'
        elif 'bing' in ref: source = 'Bing'
        elif 'yahoo' in ref: source = 'Yahoo'
        elif 'tiktok' in ref: source = 'TikTok'
        elif 'twitter' in ref or 'x.com' in ref: source = 'Twitter/X'
        elif 'yelp' in ref: source = 'Yelp'
        elif 'tripadvisor' in ref: source = 'TripAdvisor'
        else: source = referrer.split('/')[2][:30] if '//' in referrer else referrer[:30]

    def notify():
        try:
            geo = req.get(f'https://ipapi.co/{ip}/json/', timeout=5, headers={'User-Agent': 'RioTransportation/1.0'}).json()
            city = geo.get('city', '?')
            region = geo.get('region', '')
            country = geo.get('country_name', '?')
            cc = geo.get('country_code', '')
            flag = chr(127397 + ord(cc[0])) + chr(127397 + ord(cc[1])) if len(cc) == 2 else '🌐'

            # Save to log
            save_visitor({
                'ip': ip[:20], 'city': city, 'region': region, 'country': country, 'flag': flag,
                'device': device, 'browser': browser, 'page': page, 'source': source,
                'referrer': referrer[:100], 'screen': screen_size, 'lang': lang,
                'timestamp': datetime.now().isoformat()
            })

            # Send email notification
            if config.RESEND_API_KEY:
                page_name = {'/' : 'Home', '/book': 'Booking', '/fleet': 'Fleet', '/about': 'About', '/weather': 'Weather', '/blog': 'Blog'}.get(page, page)
                req.post('https://api.resend.com/emails', json={
                    'from': 'Rio Transportation <booking@parkcitytrips.com>',
                    'to': ['agendahudsonbarros@gmail.com'],
                    'subject': f'{flag} {city} — {source} — {page_name}',
                    'html': f"""<div style="font-family:Arial,sans-serif;max-width:420px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;">
<div style="background:#000;padding:14px 20px;color:#fff;font-size:13px;font-weight:700;">🌐 New Visitor — parkcitytrips.com</div>
<div style="padding:16px 20px;">
<table style="width:100%;font-size:13px;color:#333;border-collapse:collapse;">
<tr><td style="padding:5px 0;color:#999;">📍 Location</td><td style="padding:5px 0;text-align:right;font-weight:700;">{flag} {city}, {region}</td></tr>
<tr><td style="padding:5px 0;color:#999;">🌍 Country</td><td style="padding:5px 0;text-align:right;">{country}</td></tr>
<tr><td style="padding:5px 0;color:#999;">📱 Device</td><td style="padding:5px 0;text-align:right;">{device} · {browser}</td></tr>
<tr><td style="padding:5px 0;color:#999;">📄 Page</td><td style="padding:5px 0;text-align:right;font-weight:700;">{page_name}</td></tr>
<tr><td style="padding:5px 0;color:#999;">🔗 Source</td><td style="padding:5px 0;text-align:right;font-weight:700;color:{'#22c55e' if source=='Google' else '#3b82f6' if source in ('Facebook','Instagram') else '#000'};">{source}</td></tr>
{f'<tr><td style="padding:5px 0;color:#999;">↩ Referrer</td><td style="padding:5px 0;text-align:right;font-size:11px;color:#999;">{referrer[:60]}</td></tr>' if referrer and source=='Direct' else ''}
<tr><td style="padding:5px 0;color:#999;">🗣 Language</td><td style="padding:5px 0;text-align:right;">{lang}</td></tr>
</table>
</div></div>""",
                }, headers={'Authorization': f'Bearer {config.RESEND_API_KEY}'}, timeout=10)
                print(f"[Visitor] {flag} {city} — {source} — {page_name} — {device}")
        except Exception as e:
            print(f"[Visitor] Error: {e}")

    threading.Thread(target=notify, daemon=True).start()
    return jsonify({'ok': True})


@app.route('/blog')
def blog():
    return render_template('blog.html', posts=POSTS, config=config)


@app.route('/blog/<slug>')
def blog_post(slug):
    post = next((p for p in POSTS if p['slug'] == slug), None)
    if not post:
        abort(404)
    return render_template('blog_post.html', post=post, config=config)


# SEO Landing Pages — loaded from seo_pages_data.py (enriched content
# to avoid Google's "Duplicate without user-selected canonical" issue)
from seo_pages_data import SEO_PAGES


@app.route('/s/<slug>')
def seo_page(slug):
    page = SEO_PAGES.get(slug)
    if not page:
        abort(404)
    # Inject slug (referenced by the template's canonical + related links)
    page_with_slug = {**page, 'slug': slug}
    # Related services — pick up to 5 other SEO pages, round-robin across the dict
    all_slugs = list(SEO_PAGES.keys())
    if slug in all_slugs:
        start = (all_slugs.index(slug) + 1) % len(all_slugs)
        related_slugs = (all_slugs[start:] + all_slugs[:start])
        related_slugs = [s for s in related_slugs if s != slug][:5]
    else:
        related_slugs = [s for s in all_slugs if s != slug][:5]
    related = [{'slug': s, 'title': SEO_PAGES[s]['h1']} for s in related_slugs]
    return render_template(
        'seo_page.html',
        page=page_with_slug, config=config, vehicles=config.VEHICLES,
        related=related,
    )


@app.route('/sitemap.xml')
def sitemap():
    from flask import Response
    today = datetime.now().strftime('%Y-%m-%d')
    pages = [
        ('/', '1.0', 'daily'),
        ('/book', '0.9', 'weekly'),
        ('/fleet', '0.8', 'weekly'),
        ('/about', '0.7', 'monthly'),
        ('/weather', '0.8', 'daily'),
    ] + [(f'/s/{s}', '0.8', 'weekly') for s in SEO_PAGES] + [
        ('/blog', '0.7', 'weekly'),
    ] + [(f'/blog/{p["slug"]}', '0.6', 'monthly') for p in POSTS]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, priority, freq in pages:
        xml += f'  <url><loc>https://parkcitytrips.com{url}</loc><lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{priority}</priority></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')


@app.route('/robots.txt')
def robots():
    from flask import Response
    txt = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /signin\n"
        "Disallow: /signout\n"
        "Disallow: /admin\n"
        "Disallow: /admin/\n"
        "Disallow: /book/payment/\n"
        "Disallow: /book/confirm/\n"
        "Disallow: /v1\n"
        "Disallow: /api/\n"
        "Sitemap: https://parkcitytrips.com/sitemap.xml\n"
    )
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

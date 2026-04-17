"""Park City Trips — Luxury Transportation in Park City, Utah."""
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash
import config
from blog_data import POSTS

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route('/')
def home():
    return render_template('home_v2.html', config=config)


@app.route('/v1')
def home_v1():
    """Old design preserved at /v1 for comparison."""
    return render_template('home.html', config=config)


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
    """Process booking form — send notification to Hudson via SMS/email."""
    data = request.form.to_dict()
    # Build summary message
    vehicle_names = {'small': 'Small SUV (Eclipse Cross)', 'midsize': 'Midsize SUV (Pathfinder)',
                     'premier': 'Premier SUV (Yukon)', 'luxury': 'Luxury SUV (Navigator)'}
    msg = f"""🚗 NEW BOOKING REQUEST

Vehicle: {vehicle_names.get(data.get('vehicle',''), data.get('vehicle',''))}
Direction: {data.get('direction','')}
Date: {data.get('date','')}
Flight: {data.get('flight_number','')}
Arrival: {data.get('arrival_time','')}

Passengers: {data.get('adults','0')} adults, {data.get('children','0')} children, {data.get('infants','0')} infants
Car Seats: {data.get('car_seats','0')}
Bags: {data.get('bags','0')} regular, {data.get('ski_bags','0')} ski

Name: {data.get('name','')}
Phone: {data.get('phone','')}
Email: {data.get('email','')}
Hotel: {data.get('destination','')}
Notes: {data.get('notes','')}"""

    print(f"[Booking] {msg}")
    # TODO: Send SMS/email to Hudson
    flash('Booking request received! We\'ll confirm within 30 minutes.', 'success')
    return redirect(url_for('book_confirm', name=data.get('name','')))


@app.route('/book/confirm')
def book_confirm():
    name = request.args.get('name', 'there')
    return f"""<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
    <title>Booking Confirmed — Rio Transportation</title>
    <link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;700;800&display=swap" rel="stylesheet">
    <style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{background:#080a0f;color:#fff;font-family:Onest,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:20px;}}
    .check{{width:80px;height:80px;border-radius:50%;background:rgba(201,168,76,.1);border:2px solid #c9a84c;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;font-size:36px;color:#c9a84c;}}
    h1{{font-size:32px;margin-bottom:12px;}}p{{color:#666;font-size:16px;margin-bottom:24px;line-height:1.6;}}
    a{{color:#c9a84c;text-decoration:none;font-weight:700;}}</style></head>
    <body><div><div class="check">✓</div><h1>Thank you, {name}!</h1>
    <p>Your booking request has been received.<br>We'll confirm within 30 minutes via phone or text.</p>
    <a href="/">← Back to Rio Transportation</a></div></body></html>"""


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

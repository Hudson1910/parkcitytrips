"""Configuration for Park City Trips."""
import os

# SECRET_KEY: never fall back to a guessable string. If the env var is
# missing on prod, fail loudly at boot rather than serving sessions with
# a forge-able cookie. Generate one with: python -c "import secrets;
# print(secrets.token_urlsafe(64))" — set as Railway env SECRET_KEY.
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if os.getenv('RAILWAY_ENVIRONMENT'):
        raise RuntimeError(
            'SECRET_KEY env var is required on Railway. Generate with: '
            'python -c "import secrets; print(secrets.token_urlsafe(64))" '
            'and set as a Railway variable.'
        )
    # Local dev fallback — random per-process so cookies don't leak between
    # devs sharing the codebase but Hudson can still hit localhost.
    import secrets as _secrets
    SECRET_KEY = _secrets.token_urlsafe(64)
    print('[config] SECRET_KEY env var unset — using random per-process key for local dev.')

PORT = int(os.getenv('PORT', 5000))

# Company
COMPANY_NAME = 'Rio Transportation LLC'
BRAND_NAME = 'Park City Trips'
PHONE = '+14352146939'
WHATSAPP = '+14352146939'
EMAIL = 'contactus@riotravelpc.com'
ADDRESS = '1776 Kearns Blvd, Park City, UT 84060'
INSTAGRAM = 'https://instagram.com/riotravelllc'

# Vehicles & Pricing (SLC <-> Park City, per vehicle each way)
VEHICLES = [
    {
        'id': 'mid-suv',
        'name': 'Mid Size SUV',
        'model': 'Nissan Pathfinder 2023 or similar',
        'price': 129,
        'passengers': 6,
        'bags': 6,
        'features': ['Leather seats', 'Climate control', 'USB charging', 'Bottled water', 'Free car seats', 'Flight tracking'],
        'image': 'mid-suv.jpg',
        'tag': 'Best Value',
    },
    {
        'id': 'premier-suv',
        'name': 'Premier SUV',
        'model': 'GMC Yukon 2023 or similar',
        'price': 189,
        'passengers': 7,
        'bags': 7,
        'features': ['Leather seats', 'Captain chairs', 'WiFi', 'USB charging', 'Bottled water', 'Free car seats', 'Flight tracking'],
        'image': 'premier-suv.jpg',
        'tag': 'Most Popular',
    },
    {
        'id': 'luxury-suv',
        'name': 'Luxury SUV',
        'model': 'Cadillac Escalade 2023 or similar',
        'price': 220,
        'passengers': 6,
        'bags': 6,
        'features': ['Premium leather', 'Heated seats', 'WiFi', 'USB charging', 'Bottled water', 'Privacy glass', 'Free car seats', 'Flight tracking', 'Beverages & snacks'],
        'image': 'luxury-suv.jpg',
        'tag': 'Premium',
    },
]

# Routes & pricing multipliers
ROUTES = {
    'slc-pc': {'name': 'SLC Airport → Park City', 'multiplier': 1.0},
    'pc-slc': {'name': 'Park City → SLC Airport', 'multiplier': 1.0},
    'local': {'name': 'Local Park City (hourly)', 'multiplier': 0.75},
    'event': {'name': 'Special Event / Wedding', 'multiplier': 1.5},
}

# Square Payment
SQUARE_APP_ID = os.getenv('SQUARE_APP_ID', '')
SQUARE_ACCESS_TOKEN = os.getenv('SQUARE_ACCESS_TOKEN', '')
SQUARE_ENVIRONMENT = os.getenv('SQUARE_ENVIRONMENT', 'sandbox')
SQUARE_JS_URL = 'https://web.squarecdn.com/v1/square.js' if SQUARE_ENVIRONMENT == 'production' else 'https://sandbox.web.squarecdn.com/v1/square.js'

# Mapbox (address autocomplete)
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN', '')

# Pricing
VEHICLE_PRICES = {'small': 100, 'midsize': 129, 'premier': 189, 'luxury': 220, 'hourly': 120, 'group': 0}
PREMIUM_STOP_PRICE = 60

# Email notifications
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL', 'agendahudsonbarros@gmail.com,contactus@riotravelpc.com')
# Legacy SMTP (Railway blocks ports, keeping for local dev)
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')

# Admin login PIN — set ADMIN_PIN env var on Railway with something
# stronger than 4 digits (you should pick 6+ chars or move to a real
# password). Falls back to a random per-boot value on local dev so the
# old guessable '6939' default can't accidentally leak via the source.
ADMIN_PIN = os.getenv('ADMIN_PIN')
if not ADMIN_PIN:
    if os.getenv('RAILWAY_ENVIRONMENT'):
        raise RuntimeError(
            'ADMIN_PIN env var is required on Railway. Pick a strong value '
            '(8+ chars, mix letters+numbers) and set as a Railway variable.'
        )
    import secrets as _secrets_pin
    ADMIN_PIN = _secrets_pin.token_urlsafe(8)
    print(f'[config] ADMIN_PIN env unset — using random dev PIN: {ADMIN_PIN}')
TRAVELFORZA_API = os.getenv('TRAVELFORZA_API', 'https://web-production-1378b.up.railway.app')
TRANSP_API_KEY = os.getenv('TRANSP_API_KEY', 'rio-transp-2026')

# Stats
TOTAL_RIDES = '9,000+'

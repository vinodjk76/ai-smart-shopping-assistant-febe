"""Seed the database with DEMO/SAMPLE data. Safe to rerun (idempotent by SKU).

All products, prices, ratings and reviews below are fictional sample data and
are NOT verified current market information.

Usage:  python seed.py
"""
from datetime import datetime, timezone

from extensions import db
from models import Product, ProductPrice, Review

SAMPLE_SOURCES = ("Demo Store A", "Demo Store B")

# (sku, name, brand, category, description, specs, features, rating, rating_count,
#  [price_a, price_b], in_stock, [(review rating, title, body), ...])
PRODUCTS = [
    ("SM-001", "Nova X1 5G", "Novatech", "Smartphones",
     "Mid-range 5G phone with a large battery and a smooth 120 Hz display.",
     {"Battery": "5000 mAh", "Display": "6.6 in AMOLED 120 Hz", "RAM": "8 GB",
      "Storage": "128 GB", "Camera": "64 MP main"},
     ["5G", "Long battery life", "Fast charging", "AMOLED display"], 4.3, 1840,
     [19999, 20499], True,
     [(5, "Battery lasts two days", "Battery easily lasts two days of normal use and charging is quick."),
      (4, "Great display", "The screen is bright and smooth. Camera is good in daylight."),
      (3, "Low light camera so-so", "Photos at night are average and the phone gets warm while gaming.")]),
    ("SM-002", "Pixora Lite", "Pixora", "Smartphones",
     "Budget smartphone for everyday calls, messaging and light browsing.",
     {"Battery": "4500 mAh", "Display": "6.5 in LCD 90 Hz", "RAM": "4 GB",
      "Storage": "64 GB", "Camera": "50 MP main"},
     ["Budget friendly", "Good battery life", "Expandable storage"], 3.9, 960,
     [9499, 9799], True,
     [(4, "Value for money", "Does everything I need at a low price and the battery is solid."),
      (3, "Slow at times", "Apps open slowly when many are running. Storage fills up fast."),
      (4, "Good for parents", "Simple, reliable and easy to use.")]),
    ("SM-003", "Aether Pro Max", "Aether", "Smartphones",
     "Flagship phone with a top-tier processor and a versatile triple camera.",
     {"Battery": "4800 mAh", "Display": "6.8 in LTPO AMOLED 120 Hz", "RAM": "12 GB",
      "Storage": "256 GB", "Camera": "108 MP main + telephoto"},
     ["5G", "Flagship performance", "Excellent camera", "Wireless charging"], 4.6, 2210,
     [74999, 75999], True,
     [(5, "Superb camera", "The camera quality is outstanding in all lighting."),
      (5, "Very fast", "Handles heavy games without any lag."),
      (3, "Expensive", "Great phone but very pricey and the charger is not included.")]),
    ("LP-001", "CodeBook 14", "Lumina", "Laptops",
     "Lightweight laptop suited to programming and everyday productivity.",
     {"Processor": "Ryzen 5 7530U", "RAM": "16 GB", "Storage": "512 GB SSD",
      "Display": "14 in FHD IPS", "Battery": "Up to 10 hours", "Weight": "1.4 kg"},
     ["Good for programming", "16 GB RAM", "Lightweight", "Backlit keyboard"], 4.4, 1320,
     [54990, 56490], True,
     [(5, "Perfect for coding", "Compiles fast, keyboard is comfortable and RAM is plentiful."),
      (4, "Light and portable", "Easy to carry all day, battery lasts a full workday."),
      (3, "Average speakers", "Speakers are weak but everything else is good.")]),
    ("LP-002", "StudyMate 15", "Zenit", "Laptops",
     "Affordable laptop for students and office work.",
     {"Processor": "Core i3 12th Gen", "RAM": "8 GB", "Storage": "256 GB SSD",
      "Display": "15.6 in FHD", "Battery": "Up to 7 hours", "Weight": "1.7 kg"},
     ["Budget friendly", "Large display", "Numeric keypad"], 3.8, 870,
     [34990, 35990], True,
     [(4, "Good for students", "Handles documents, video calls and browsing well."),
      (3, "Heavy build", "Feels a little heavy and the battery is average."),
      (3, "Struggles with many tabs", "Slows down with a lot of browser tabs open.")]),
    ("LP-003", "Titan Creator 16", "Titanix", "Laptops",
     "High-performance laptop with a dedicated GPU for creative work and gaming.",
     {"Processor": "Core i7 13th Gen", "RAM": "32 GB", "GPU": "RTX 4060 8 GB",
      "Storage": "1 TB SSD", "Display": "16 in QHD+ 165 Hz", "Battery": "Up to 6 hours"},
     ["Dedicated GPU", "High refresh display", "32 GB RAM"], 4.5, 640,
     [124990, 127990], False,
     [(5, "Powerhouse", "Video editing and gaming are both smooth."),
      (4, "Great screen", "Colour accurate and fast display."),
      (2, "Loud fans and short battery", "Fans get loud under load and the battery drains quickly.")]),
    ("HP-001", "BassBuds Neo", "Sonara", "Headphones",
     "Wireless in-ear earbuds with deep bass and a compact charging case.",
     {"Type": "True wireless earbuds", "Battery": "28 hours with case",
      "Bluetooth": "5.3", "Water resistance": "IPX4"},
     ["Deep bass", "Long battery life", "Budget friendly", "Low latency mode"], 4.1, 3050,
     [1799, 1899], True,
     [(4, "Great for the price", "Strong bass and the battery lasts long."),
      (4, "Comfortable fit", "Stays in my ears during workouts."),
      (2, "Mic is average", "Callers say my voice sounds muffled outdoors.")]),
    ("HP-002", "QuietWave ANC", "Sonara", "Headphones",
     "Over-ear wireless headphones with active noise cancellation.",
     {"Type": "Over-ear wireless", "Battery": "40 hours", "ANC": "Hybrid active noise cancellation",
      "Bluetooth": "5.2"},
     ["Noise cancellation", "Long battery life", "Comfortable", "Foldable"], 4.4, 1580,
     [2799, 2999], True,
     [(5, "ANC is impressive", "Blocks most of the noise on my commute at this price."),
      (4, "Very comfortable", "Soft ear cushions, I can wear them for hours."),
      (3, "Treble is a bit harsh", "Sound is good but the highs can be sharp at high volume.")]),
    ("HP-003", "StudioPro 700", "Auralis", "Headphones",
     "Premium wireless headphones with balanced sound and top-tier noise cancellation.",
     {"Type": "Over-ear wireless", "Battery": "30 hours", "ANC": "Adaptive noise cancellation",
      "Bluetooth": "5.3"},
     ["Noise cancellation", "Premium sound", "Multipoint connection"], 4.7, 2400,
     [24990, 25990], True,
     [(5, "Best sound I've owned", "Rich, balanced sound and excellent noise cancellation."),
      (5, "Great for travel", "Comfortable on long flights."),
      (3, "Pricey", "Excellent but costs a lot.")]),
    ("HA-001", "AirSwift 1.5T Inverter AC", "Coolora", "Home Appliances",
     "1.5 ton 5-star inverter split air conditioner.",
     {"Capacity": "1.5 ton", "Energy rating": "5 star", "Type": "Inverter split",
      "Warranty": "1 year product, 10 years compressor"},
     ["Energy efficient", "Inverter compressor", "Low noise"], 4.2, 780,
     [38990, 39990], True,
     [(5, "Cools quickly", "Cools the bedroom fast and the electricity bill dropped."),
      (4, "Quiet", "Indoor unit is very quiet."),
      (3, "Installation delay", "Installation took a week to schedule.")]),
    ("HA-002", "CleanSweep R5 Robot Vacuum", "Dustio", "Home Appliances",
     "Robot vacuum with smart mapping and app control.",
     {"Suction": "3000 Pa", "Battery": "150 minutes", "Navigation": "LiDAR mapping",
      "Dustbin": "450 ml"},
     ["Smart mapping", "App control", "Auto recharge"], 4.0, 520,
     [18999, 19499], True,
     [(4, "Saves time", "Maps the house well and cleans on a schedule."),
      (3, "Struggles with rugs", "Sometimes gets stuck on thick rugs."),
      (4, "App is easy", "Setup took five minutes.")]),
    ("HA-003", "BrewMaster Mixer Grinder 750W", "Kitchenly", "Home Appliances",
     "750W mixer grinder with three stainless steel jars.",
     {"Power": "750 W", "Jars": "3 stainless steel", "Warranty": "2 years"},
     ["Powerful motor", "Budget friendly", "Durable jars"], 4.1, 1900,
     [3299, 3499], True,
     [(4, "Strong motor", "Grinds spices and chutney quickly."),
      (4, "Good value", "Solid build for the price."),
      (3, "A bit noisy", "Louder than my previous mixer.")]),
    ("AC-001", "PowerPulse 20000mAh Power Bank", "Voltix", "Accessories",
     "20000 mAh power bank with 22.5W fast charging and dual outputs.",
     {"Capacity": "20000 mAh", "Output": "22.5 W", "Ports": "USB-C + 2x USB-A"},
     ["Fast charging", "Large capacity", "Dual output"], 4.3, 2750,
     [1799, 1899], True,
     [(5, "Charges my phone 4 times", "Large capacity and charges quickly."),
      (4, "Solid build", "Feels sturdy but a bit heavy."),
      (3, "Slow to recharge itself", "Takes a long time to recharge the power bank.")]),
    ("AC-002", "FlexCharge 65W GaN Charger", "Voltix", "Accessories",
     "Compact 65W GaN wall charger that can power a phone and a laptop.",
     {"Output": "65 W", "Ports": "2x USB-C + 1x USB-A", "Technology": "GaN"},
     ["Fast charging", "Compact", "Multi-device"], 4.5, 1210,
     [2299, 2399], True,
     [(5, "Charges laptop and phone", "Small yet powerful, replaced three chargers."),
      (5, "Compact", "Very travel friendly."),
      (4, "Gets warm", "Gets warm under full load but nothing alarming.")]),
    ("AC-003", "ClickType Wireless Keyboard & Mouse", "Typix", "Accessories",
     "Quiet wireless keyboard and mouse combo for home and office.",
     {"Connectivity": "2.4 GHz wireless", "Battery": "Up to 12 months", "Layout": "Full size"},
     ["Quiet keys", "Long battery life", "Budget friendly"], 3.9, 890,
     [1299, 1399], True,
     [(4, "Quiet and comfortable", "Good for long typing sessions."),
      (3, "Mouse is basic", "Mouse tracking is fine but not for gaming."),
      (4, "Easy setup", "Plug the dongle and it works.")]),
]


def seed(commit=True):
    """Insert sample data; skip anything that already exists. Returns count of new products."""
    created = 0
    now = datetime.now(timezone.utc)
    for (sku, name, brand, category, desc, specs, features, rating, rcount,
         prices, in_stock, reviews) in PRODUCTS:
        if Product.query.filter_by(sku=sku).first():
            continue
        product = Product(
            sku=sku, name=name, brand=brand, category=category, description=desc,
            specs=specs, features=features, rating=rating, rating_count=rcount,
            image_url="", source_url=None, data_source="demo_seed", is_sample=True,
            in_stock=in_stock,
            stock_note="Sample availability (demo data)",
        )
        for source, amount in zip(SAMPLE_SOURCES, prices):
            product.prices.append(ProductPrice(
                amount=amount, currency="INR", source=source, source_url=None,
                is_verified=False, is_sample=True, retrieved_at=now,
            ))
        for r_rating, title, body in reviews:
            product.reviews.append(Review(
                author="Sample reviewer", rating=r_rating, title=title,
                body=body, is_sample=True,
            ))
        db.session.add(product)
        created += 1
    if commit:
        db.session.commit()
    return created


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        n = seed()
        total = Product.query.count()
        print(f"Seed complete: {n} new sample products added ({total} total).")

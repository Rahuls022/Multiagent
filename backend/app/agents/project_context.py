"""Intelligent project interpreter and business domain context generator.

Synthesizes rich, domain-aware business models, product catalogs, API specifications,
database schemas, and UI configurations for any mission request.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def extract_business_name(request: str) -> str:
    """Extract a clean, professional business name from natural language request."""
    req = request.strip()
    if re.search(r"\bfreshsip\b", req, re.IGNORECASE):
        return "FreshSip Juice Centre"
    if re.search(r"\btestflow\b", req, re.IGNORECASE):
        return "TestFlow"

    # Strip leading action verbs and determiners
    clean = re.sub(
        r"^(build|create|develop|design|make|setup|generate)\s+(?:(?:a|an|the|professional|modern|full-stack)\s+)*",
        "",
        req,
        flags=re.IGNORECASE,
    ).strip()

    # Pattern: "website for a Juice Centre to accept online orders" -> "Juice Centre"
    match = re.search(
        r"(?:website|portal|web\s+app|app|platform|system)?\s*(?:for|of)?\s*(?:a|an|the)?\s*([a-zA-Z0-9\s&'-]+?)(?:\s+(?:to|where|with|featuring|including|that|which|for\s+accepting)\b|$)",
        clean,
        re.IGNORECASE,
    )
    if match and match.group(1):
        candidate = match.group(1).strip()
        # Exclude generic words
        tokens = [w for w in candidate.split() if w.lower() not in ("website", "portal", "web", "app", "application", "a", "an", "the", "for", "of")]
        if tokens:
            name = " ".join(t.capitalize() for t in tokens)
            return name

    # Fallback to text before 'with' / 'featuring'
    m_with = re.search(r"^(.*?)(?:\s+(?:with|featuring|including|having|to)\s+.*)?$", clean, flags=re.IGNORECASE)
    if m_with and m_with.group(1):
        clean = m_with.group(1).strip()

    clean = " ".join(word.capitalize() for word in clean.split() if word.lower() not in ("website", "web", "portal", "a", "an", "the", "for", "of"))
    return clean or "Business Portal"


def get_juice_profile(business_name: str) -> Dict[str, Any]:
    name = business_name if "juice" in business_name.lower() else f"{business_name} Juice Centre"
    return {
        "domain": "juice",
        "name": name,
        "kind": "Fresh Juice Centre & Smoothie Bar",
        "actor": "Juice Enthusiast & Barista",
        "entity": "order",
        "plural": "orders",
        "item_entity": "juice",
        "item_plural": "juices",
        "primary_action": "explore natural cold-pressed juices, customize smoothies, manage cart, and place orders",
        "brand_icon": "🥤",
        "brand_tag": "100% Pure & Cold-Pressed",
        "hero_tag": "✨ Pure Nature in Every Sip",
        "hero_title": "Refresh Your Day With Freshly Prepared Juices",
        "hero_desc": "Cold-pressed daily from farm-fresh fruits and vegetables. Zero added sugar, zero artificial preservatives, 100% pure vitality.",
        "kpi_labels": {
            "catalog": "Total Fresh Juices",
            "orders": "Today's Juice Orders",
            "revenue": "Live Daily Revenue",
            "health": "In-Stock Juices",
        },
        "categories": ["All", "Fresh Fruit Juices", "Smoothies", "Milkshakes", "Detox & Wellness", "Seasonal Specials"],
        "products": [
            {
                "id": "j1",
                "name": "Fresh Orange Juice",
                "category": "Fresh Fruit Juices",
                "price": 4.50,
                "icon": "🍊",
                "rating": 4.9,
                "reviews": 128,
                "stock": 40,
                "desc": "100% freshly squeezed Valencia oranges bursting with pure Vitamin C.",
            },
            {
                "id": "j2",
                "name": "Watermelon Hydration Cooler",
                "category": "Fresh Fruit Juices",
                "price": 3.99,
                "icon": "🍉",
                "rating": 4.8,
                "reviews": 95,
                "stock": 35,
                "desc": "Crisp chilled watermelon cold-pressed with sweet fresh garden mint and lime.",
            },
            {
                "id": "j3",
                "name": "Alphonso Mango Magic",
                "category": "Seasonal Specials",
                "price": 5.50,
                "icon": "🥭",
                "rating": 5.0,
                "reviews": 210,
                "stock": 25,
                "desc": "Luscious Ratnagiri Alphonso mango puree blended into golden tropical sunshine.",
            },
            {
                "id": "j4",
                "name": "Detox Green Cleanse",
                "category": "Detox & Wellness",
                "price": 6.25,
                "icon": "🥬",
                "rating": 4.7,
                "reviews": 84,
                "stock": 20,
                "desc": "Raw cold-pressed celery, green apple, organic spinach, cucumber, and spicy ginger.",
            },
            {
                "id": "j5",
                "name": "Pineapple Mint Splash",
                "category": "Fresh Fruit Juices",
                "price": 4.75,
                "icon": "🍍",
                "rating": 4.8,
                "reviews": 76,
                "stock": 30,
                "desc": "Sweet golden tropical pineapple crushed with crushed spearmint and Himalayan pink salt.",
            },
            {
                "id": "j6",
                "name": "Strawberry Silk Milkshake",
                "category": "Milkshakes",
                "price": 5.99,
                "icon": "🍓",
                "rating": 4.9,
                "reviews": 164,
                "stock": 28,
                "desc": "Hand-picked alpine strawberries whipped with artisanal vanilla ice cream and whole milk.",
            },
            {
                "id": "j7",
                "name": "Creamy Banana Almond Shake",
                "category": "Milkshakes",
                "price": 5.25,
                "icon": "🍌",
                "rating": 4.8,
                "reviews": 92,
                "stock": 22,
                "desc": "Caramelized ripe bananas, roasted almond butter, and wildflower honey cream.",
            },
            {
                "id": "j8",
                "name": "Tropical Acai Energy Smoothie",
                "category": "Smoothies",
                "price": 6.75,
                "icon": "🫐",
                "rating": 4.9,
                "reviews": 145,
                "stock": 18,
                "desc": "Organic Brazilian acai berries, wild blueberries, chia seeds, and Greek yogurt.",
            },
        ],
        "default_orders": [
            {"id": "ORD-JUICE-701", "customer": "Elena Rostova", "phone": "555-0192", "address": "Suite 4B, Riverfront", "items": "Fresh Orange Juice (x2), Detox Green Cleanse (x1)", "total": 15.25, "status": "Delivered", "date": "2026-11-04 09:15"},
            {"id": "ORD-JUICE-702", "customer": "Marcus Brody", "phone": "555-0144", "address": "742 Evergreen Terrace", "items": "Alphonso Mango Magic (x2)", "total": 11.00, "status": "Out for Delivery", "date": "2026-11-04 10:30"},
            {"id": "ORD-JUICE-703", "customer": "Chloe Zhao", "phone": "555-0188", "address": "120 Innovation Way", "items": "Strawberry Silk Milkshake (x1), Watermelon Cooler (x1)", "total": 9.98, "status": "Preparing", "date": "2026-11-04 11:05"},
        ],
        "features": [
            "Cold-Pressed Fresh Juice & Smoothie Menu",
            "Real-Time Shopping Cart with Quantity Controls",
            "Seamless Online Checkout with Customer & Delivery Details",
            "Live Inventory & Out-of-Stock Protection",
            "Dynamic Real-Time Sales & Order Volume Analytics",
        ],
    }


def get_restaurant_profile(business_name: str) -> Dict[str, Any]:
    name = business_name if any(w in business_name.lower() for w in ("restaurant", "bistro", "cafe", "kitchen", "grill")) else f"{business_name} Restaurant"
    return {
        "domain": "restaurant",
        "name": name,
        "kind": "Gourmet Restaurant & Food Ordering System",
        "actor": "Guest & Executive Chef",
        "entity": "order",
        "plural": "orders",
        "item_entity": "dish",
        "item_plural": "dishes",
        "primary_action": "browse chef specialties, customize meals, place dining or delivery orders, and track preparation",
        "brand_icon": "🍽️",
        "brand_tag": "Chef's Artisanal Kitchen",
        "hero_tag": "🔥 Fresh Flavors Made to Order",
        "hero_title": "Exquisite Culinary Delights Delivered to Your Table",
        "hero_desc": "Handcrafted dishes prepared with ethically sourced ingredients, house-made pastas, and wood-fired mastery.",
        "kpi_labels": {
            "catalog": "Active Menu Dishes",
            "orders": "Kitchen Food Orders",
            "revenue": "Live Daily Revenue",
            "health": "In-Stock Dishes",
        },
        "categories": ["All", "Appetizers", "Chef Mains", "Wood-Fired Pizza", "Pasta & Risotto", "Desserts & Drinks"],
        "products": [
            {
                "id": "r1",
                "name": "Truffle Wild Mushroom Bruschetta",
                "category": "Appetizers",
                "price": 11.50,
                "icon": "🍄",
                "rating": 4.9,
                "reviews": 112,
                "stock": 30,
                "desc": "Toasted sourdough with sautéed portobello, shaved black truffle, and thyme.",
            },
            {
                "id": "r2",
                "name": "Wood-Fired Margherita Pizza",
                "category": "Wood-Fired Pizza",
                "price": 16.99,
                "icon": "🍕",
                "rating": 5.0,
                "reviews": 240,
                "stock": 45,
                "desc": "San Marzano D.O.P. tomato sauce, buffalo mozzarella, fresh basil, and extra virgin olive oil.",
            },
            {
                "id": "r3",
                "name": "Classic Wagyu Gourmet Burger",
                "category": "Chef Mains",
                "price": 18.50,
                "icon": "🍔",
                "rating": 4.8,
                "reviews": 185,
                "stock": 35,
                "desc": "Prime Wagyu beef patty, smoked bacon jam, aged white cheddar on toasted brioche.",
            },
            {
                "id": "r4",
                "name": "Handmade Tagliatelle al Tartufo",
                "category": "Pasta & Risotto",
                "price": 21.00,
                "icon": "🍝",
                "rating": 4.9,
                "reviews": 130,
                "stock": 25,
                "desc": "Handcrafted egg pasta ribbons in creamy Parmigiano-Reggiano sauce with black truffles.",
            },
            {
                "id": "r5",
                "name": "Pan-Seared Atlantic Salmon",
                "category": "Chef Mains",
                "price": 24.50,
                "icon": "🐟",
                "rating": 4.8,
                "reviews": 98,
                "stock": 20,
                "desc": "Crispy skin salmon served over wild asparagus and lemon-herb velouté.",
            },
            {
                "id": "r6",
                "name": "Crispy Calamari Fritti",
                "category": "Appetizers",
                "price": 13.50,
                "icon": "🦑",
                "rating": 4.7,
                "reviews": 88,
                "stock": 28,
                "desc": "Golden tender squid with garlic smoked chili aioli and charred lemon wedges.",
            },
            {
                "id": "r7",
                "name": "Authentic Italian Tiramisu",
                "category": "Desserts & Drinks",
                "price": 8.99,
                "icon": "🍰",
                "rating": 4.9,
                "reviews": 175,
                "stock": 32,
                "desc": "Espresso-soaked savoiardi ladyfingers layered with rich mascarpone and dark Dutch cocoa.",
            },
            {
                "id": "r8",
                "name": "Wild Berry Sparkling Spritz",
                "category": "Desserts & Drinks",
                "price": 6.50,
                "icon": "🍹",
                "rating": 4.7,
                "reviews": 70,
                "stock": 40,
                "desc": "Handcrafted blackberry cordial, fresh mint leaves, and effervescent sparkling soda.",
            },
        ],
        "default_orders": [
            {"id": "ORD-REST-501", "customer": "Liam Gallagher", "phone": "555-0811", "address": "Table 12 (Dine-In)", "items": "Wood-Fired Margherita Pizza (x2), Wild Berry Spritz (x2)", "total": 46.98, "status": "Served", "date": "2026-11-04 12:10"},
            {"id": "ORD-REST-502", "customer": "Sophia Perez", "phone": "555-0922", "address": "Apt 5A, West End", "items": "Tagliatelle al Tartufo (x1), Italian Tiramisu (x1)", "total": 29.99, "status": "In the Kitchen", "date": "2026-11-04 12:45"},
            {"id": "ORD-REST-503", "customer": "Tariq Mansour", "phone": "555-0433", "address": "Table 4 (Dine-In)", "items": "Classic Wagyu Gourmet Burger (x2)", "total": 37.00, "status": "Preparing", "date": "2026-11-04 13:00"},
        ],
        "features": [
            "Interactive Culinary Menu with Category Filtering",
            "Live Food Cart & Table / Delivery Checkout",
            "Order Status Tracking with Estimated Preparation Times",
            "Real-Time Kitchen Inventory Management",
            "Dynamic Revenue & Dining Analytics",
        ],
    }


def get_bakery_profile(business_name: str) -> Dict[str, Any]:
    name = business_name if "bakery" in business_name.lower() else f"{business_name} Bakery"
    return {
        "domain": "bakery",
        "name": name,
        "kind": "Artisan Bakery & Patisserie Online Store",
        "actor": "Patron & Head Baker",
        "entity": "order",
        "plural": "orders",
        "item_entity": "pastry",
        "item_plural": "pastries",
        "primary_action": "order freshly baked artisan sourdough, viennoiserie, celebration cakes, and pastries",
        "brand_icon": "🥐",
        "brand_tag": "Baked Fresh Every Morning",
        "hero_tag": "🥖 Warm Out of the Oven",
        "hero_title": "Handcrafted Breads & Exquisite French Pastries",
        "hero_desc": "Slow-fermented artisan sourdough, layered flaky butter croissants, and bespoke custom celebration cakes baked daily at dawn.",
        "kpi_labels": {
            "catalog": "Bakery Delights",
            "orders": "Daily Bakery Orders",
            "revenue": "Live Daily Revenue",
            "health": "In-Stock Baked Goods",
        },
        "categories": ["All", "Artisan Breads", "Viennoiserie", "Celebration Cakes", "Cookies & Tarts"],
        "products": [
            {"id": "b1", "name": "French Cultured Butter Croissant", "category": "Viennoiserie", "price": 3.95, "icon": "🥐", "rating": 5.0, "reviews": 190, "stock": 45, "desc": "Flaky 81-layer laminated pastry made with cultured French Normandy butter."},
            {"id": "b2", "name": "San Francisco Sourdough Boule", "category": "Artisan Breads", "price": 6.50, "icon": "🍞", "rating": 4.9, "reviews": 142, "stock": 30, "desc": "36-hour slow cold fermentation with crisp blistered crust and tangy tender crumb."},
            {"id": "b3", "name": "Dark Belgian Chocolate Ganache Cake", "category": "Celebration Cakes", "price": 32.00, "icon": "🎂", "rating": 4.9, "reviews": 95, "stock": 15, "desc": "Three layers of moist valrhona chocolate sponge frosted in 70% dark ganache."},
            {"id": "b4", "name": "Classic Pain au Chocolat", "category": "Viennoiserie", "price": 4.50, "icon": "🍫", "rating": 4.8, "reviews": 115, "stock": 40, "desc": "Buttery folded puff pastry filled with two batons of bittersweet Belgian chocolate."},
            {"id": "b5", "name": "Madagascar Vanilla Raspberry Tart", "category": "Cookies & Tarts", "price": 5.99, "icon": "🥧", "rating": 4.9, "reviews": 82, "stock": 25, "desc": "Crisp sweet sablée crust loaded with vanilla bean custard and fresh glazed raspberries."},
            {"id": "b6", "name": "Ceylon Cinnamon Swirl Brioche", "category": "Viennoiserie", "price": 4.75, "icon": "🥨", "rating": 4.8, "reviews": 78, "stock": 28, "desc": "Tender golden brioche rolled with fragrant Sri Lankan cinnamon and brown sugar glaze."},
        ],
        "default_orders": [
            {"id": "ORD-BAKE-301", "customer": "Claire Martin", "phone": "555-0321", "address": "15 Maple Lane", "items": "French Butter Croissant (x4), Pain au Chocolat (x2)", "total": 24.80, "status": "Ready for Pickup", "date": "2026-11-04 08:30"},
            {"id": "ORD-BAKE-302", "customer": "David Thorne", "phone": "555-0988", "address": "404 Pine Crest", "items": "San Francisco Sourdough Boule (x2)", "total": 13.00, "status": "Baking", "date": "2026-11-04 09:45"},
        ],
        "features": [
            "Daily Fresh Baked Catalog with Batch Availability",
            "Interactive Cart & Advance Order Booking",
            "Special Instructions & Dietary Notes Support",
            "Live Oven & Inventory Health Monitoring",
            "Real-Time Daily Sales Analytics",
        ],
    }


def get_clothing_profile(business_name: str) -> Dict[str, Any]:
    name = business_name if any(w in business_name.lower() for w in ("clothing", "apparel", "boutique", "fashion", "wear")) else f"{business_name} Apparel"
    return {
        "domain": "clothing",
        "name": name,
        "kind": "Modern Apparel & Designer Fashion Boutique",
        "actor": "Shopper & Stylist",
        "entity": "order",
        "plural": "orders",
        "item_entity": "garment",
        "item_plural": "garments",
        "primary_action": "browse seasonal collections, select sizes and colors, add to bag, and purchase",
        "brand_icon": "👗",
        "brand_tag": "Curated Designer Wear",
        "hero_tag": "✨ New Season Arrivals",
        "hero_title": "Elevate Your Everyday Style & Expression",
        "hero_desc": "Consciously crafted contemporary fashion, sustainable organic textiles, and timeless silhouettes.",
        "kpi_labels": {
            "catalog": "Curated Items",
            "orders": "Placed Orders",
            "revenue": "Live Sales Volume",
            "health": "In-Stock Sizes",
        },
        "categories": ["All", "Tops & Shirts", "Outerwear", "Bottoms", "Accessories"],
        "products": [
            {"id": "c1", "name": "Organic Heavyweight Crewneck", "category": "Tops & Shirts", "price": 42.00, "icon": "👕", "rating": 4.9, "reviews": 110, "stock": 45, "desc": "400gsm combed organic cotton with relaxed drop-shoulder cut."},
            {"id": "c2", "name": "Italian Tailored Wool Overcoat", "category": "Outerwear", "price": 189.00, "icon": "🧥", "rating": 5.0, "reviews": 64, "stock": 18, "desc": "Luxurious virgin wool blend with structured peak lapels and horn buttons."},
            {"id": "c3", "name": "Japanese Raw Selvedge Denim", "category": "Bottoms", "price": 98.00, "icon": "👖", "rating": 4.8, "reviews": 88, "stock": 30, "desc": "13.5oz shuttle-loomed indigo denim with classic straight taper fit."},
            {"id": "c4", "name": "Mongolian Cashmere Crew Sweater", "category": "Tops & Shirts", "price": 135.00, "icon": "🧶", "rating": 4.9, "reviews": 75, "stock": 20, "desc": "Grade-A 2-ply pure Mongolian cashmere with ribbed hems."},
            {"id": "c5", "name": "Water-Resistant City Parka", "category": "Outerwear", "price": 149.00, "icon": "🌧️", "rating": 4.7, "reviews": 52, "stock": 24, "desc": "Technical breathable shell featuring taped waterproof seams and storm hood."},
            {"id": "c6", "name": "Handmade Full-Grain Chelsea Boots", "category": "Accessories", "price": 165.00, "icon": "👞", "rating": 4.9, "reviews": 92, "stock": 16, "desc": "Vegetable-tanned leather with Goodyear welted Dainite rubber soles."},
        ],
        "default_orders": [
            {"id": "ORD-CLOTH-801", "customer": "Nathan Wu", "phone": "555-0677", "address": "77 Grand Ave, NY", "items": "Organic Heavyweight Crewneck (x2)", "total": 84.00, "status": "Shipped", "date": "2026-11-03 16:20"},
            {"id": "ORD-CLOTH-802", "customer": "Mia Lindqvist", "phone": "555-0899", "address": "12 St. Marks Place", "items": "Italian Wool Overcoat (x1)", "total": 189.00, "status": "Processing", "date": "2026-11-04 11:15"},
        ],
        "features": [
            "Seasonal Lookbook & Category Explorer",
            "Interactive Shopping Bag & Quick Checkout",
            "Size & Color Variant Management",
            "Order Tracking & Shipping Status Updates",
            "Real-Time Boutique Revenue Analytics",
        ],
    }


def get_hospital_profile(business_name: str) -> Dict[str, Any]:
    name = business_name if any(w in business_name.lower() for w in ("hospital", "clinic", "health", "care", "medical")) else f"{business_name} Hospital"
    return {
        "domain": "hospital",
        "name": name,
        "kind": "Healthcare & Patient Appointment Portal",
        "actor": "Patient & Healthcare Provider",
        "entity": "appointment",
        "plural": "appointments",
        "item_entity": "doctor",
        "item_plural": "doctors",
        "primary_action": "schedule medical consultations, view doctor profiles, and manage clinical appointments",
        "brand_icon": "🏥",
        "brand_tag": "Accredited Medical Center",
        "hero_tag": "🩺 Compassionate Expert Care",
        "hero_title": "Modern Healthcare & Rapid Specialist Appointments",
        "hero_desc": "Connect with certified medical specialists, schedule clinic or telehealth appointments, and access health records securely.",
        "kpi_labels": {
            "catalog": "Medical Specialists",
            "orders": "Scheduled Consultations",
            "revenue": "Operating Departments",
            "health": "Available Doctors",
        },
        "categories": ["All Specialties", "Cardiology", "Neurology", "Pediatrics", "Orthopedics", "General Medicine"],
        "doctors": [
            {"id": "d1", "name": "Dr. Sarah Jenkins, MD", "specialty": "Cardiology", "experience": "15 Years", "rating": 4.9, "fee": 150, "status": "Available Today", "icon": "🫀", "desc": "Board-certified cardiologist specializing in preventive heart health and arrhythmias."},
            {"id": "d2", "name": "Dr. Marcus Vance, DO", "specialty": "Neurology", "experience": "12 Years", "rating": 4.8, "fee": 180, "status": "Available Tomorrow", "icon": "🧠", "desc": "Neurologist focused on cognitive diagnostics, migraines, and nerve therapies."},
            {"id": "d3", "name": "Dr. Emily Chen, MD", "specialty": "Pediatrics", "experience": "9 Years", "rating": 5.0, "fee": 120, "status": "Available Today", "icon": "👶", "desc": "Dedicated pediatrician providing gentle child care, vaccinations, and growth wellness."},
            {"id": "d4", "name": "Dr. Robert Patel, MD", "specialty": "Orthopedics", "experience": "18 Years", "rating": 4.9, "fee": 200, "status": "Available Thursday", "icon": "🦴", "desc": "Orthopedic surgeon specializing in sports injuries, joint mobility, and arthroscopy."},
            {"id": "d5", "name": "Dr. Angela Rossi, MD", "specialty": "General Medicine", "experience": "14 Years", "rating": 4.8, "fee": 100, "status": "Available Today", "icon": "⚕️", "desc": "Primary care physician managing chronic conditions, annual checkups, and wellness."},
            {"id": "d6", "name": "Dr. David Kim, MD", "specialty": "Ophthalmology", "experience": "11 Years", "rating": 4.9, "fee": 140, "status": "Available Today", "icon": "👁️", "desc": "Ophthalmologist specializing in corrective vision therapy, cataract care, and retinal health."},
        ],
        "default_appointments": [
            {"id": "APT-2026-101", "patient_name": "Amanda Cruz", "phone": "555-0143", "doctor": "Dr. Sarah Jenkins, MD", "specialty": "Cardiology", "date": "2026-11-05 10:00 AM", "reason": "Routine ECG & Blood Pressure Follow-up", "status": "Confirmed"},
            {"id": "APT-2026-102", "patient_name": "Thomas Thorne", "phone": "555-0822", "doctor": "Dr. Robert Patel, MD", "specialty": "Orthopedics", "date": "2026-11-06 02:30 PM", "reason": "Right knee post-sprain evaluation", "status": "Scheduled"},
            {"id": "APT-2026-103", "patient_name": "Grace Hopper", "phone": "555-0399", "doctor": "Dr. Emily Chen, MD", "specialty": "Pediatrics", "date": "2026-11-04 04:00 PM", "reason": "Annual toddler developmental checkup", "status": "Completed"},
        ],
        "features": [
            "Specialist Doctor Directory with Real-Time Availability",
            "Interactive Patient Appointment Booking Modal",
            "Medical History & Consultation Record Explorer",
            "Department Filter & Schedule Conflict Prevention",
            "Clinical Care Analytics & Timetable Metrics",
        ],
    }


def get_tech_ecommerce_profile(business_name: str) -> Dict[str, Any]:
    name = business_name if any(w in business_name.lower() for w in ("tech", "electronics", "gadget", "store", "gear")) else f"{business_name} Store"
    return {
        "domain": "ecommerce",
        "name": name,
        "kind": "High-Performance Electronics & Tech Gear Store",
        "actor": "Tech Enthusiast & Store Manager",
        "entity": "order",
        "plural": "orders",
        "item_entity": "product",
        "item_plural": "products",
        "primary_action": "browse electronics catalog, configure tech accessories, manage cart, and complete purchase",
        "brand_icon": "⚡",
        "brand_tag": "Flagship Tech & Gadgets",
        "hero_tag": "🚀 Next-Gen Hardware",
        "hero_title": "Discover High-Performance Tech & Smart Gadgets",
        "hero_desc": "Premium wireless audio, ergonomic workstation gear, and tactile accessories engineered for professionals.",
        "kpi_labels": {
            "catalog": "Catalog SKUs",
            "orders": "Placed Orders",
            "revenue": "Live Daily Revenue",
            "health": "In-Stock Items",
        },
        "categories": ["All", "Audio", "Wearables", "Gaming & Input", "Workstation"],
        "products": [
            {"id": "e1", "name": "Aura Pro Wireless Headphones", "category": "Audio", "price": 199.99, "icon": "🎧", "rating": 4.9, "reviews": 142, "stock": 45, "desc": "Active noise cancellation with 40h battery life and spatial audio."},
            {"id": "e2", "name": "PulseFit Ultra Smartwatch", "category": "Wearables", "price": 149.50, "icon": "⌚", "rating": 4.8, "reviews": 98, "stock": 32, "desc": "AMOLED display with continuous heart rate monitoring, ECG, and GPS."},
            {"id": "e3", "name": "Vortex Mechanical Gaming Keyboard", "category": "Gaming & Input", "price": 89.00, "icon": "⌨️", "rating": 4.7, "reviews": 84, "stock": 28, "desc": "Hot-swappable tactile switches with customizable per-key RGB backlighting."},
            {"id": "e4", "name": "ErgoComfort Ergonomic Desk Chair", "category": "Workstation", "price": 249.00, "icon": "🪑", "rating": 4.9, "reviews": 65, "stock": 19, "desc": "Breathable responsive mesh with adjustable 4D armrests and lumbar lock."},
            {"id": "e5", "name": "Precision Ergonomic Optical Mouse", "category": "Gaming & Input", "price": 59.99, "icon": "🖱️", "rating": 4.8, "reviews": 112, "stock": 50, "desc": "Dual-sensor 26,000 DPI tracking with zero-latency wireless connection."},
            {"id": "e6", "name": "Ultra-Wide 4K Studio Monitor Lightbar", "category": "Workstation", "price": 68.00, "icon": "💡", "rating": 4.8, "reviews": 80, "stock": 35, "desc": "Anti-glare asymmetric optical design with wireless rotary touch controller."},
        ],
        "default_orders": [
            {"id": "ORD-TECH-901", "customer": "Jordan Miller", "phone": "555-0129", "address": "88 Cyber Ave, Austin TX", "items": "Aura Pro Wireless Headphones (x1)", "total": 199.99, "status": "Delivered", "date": "2026-11-03 14:10"},
            {"id": "ORD-TECH-902", "customer": "Devon Lee", "phone": "555-0943", "address": "104 Silicon Way, Seattle WA", "items": "PulseFit Ultra Smartwatch (x1), Vortex Keyboard (x1)", "total": 238.50, "status": "Shipped", "date": "2026-11-04 10:20"},
        ],
        "features": [
            "Hardware SKU Catalog with Spec Comparison",
            "Real-Time Shopping Cart with Quantity Controls",
            "Secure Checkout with Shipping Address Validation",
            "Order Fulfillment Tracking & Dispatch Records",
            "Live E-Commerce Sales Volume Analytics",
        ],
    }


def get_generic_commerce_profile(business_name: str, domain_theme: str) -> Dict[str, Any]:
    name = business_name or "Custom Store"
    theme = domain_theme or "Specialty Goods"
    return {
        "domain": "ecommerce",
        "name": name,
        "kind": f"{name} Online Platform",
        "actor": "Customer & Store Manager",
        "entity": "order",
        "plural": "orders",
        "item_entity": "item",
        "item_plural": "items",
        "primary_action": f"browse {name} catalog, add items to cart, and place orders seamlessly",
        "brand_icon": "🛍️",
        "brand_tag": "Live Online Store",
        "hero_tag": "✨ Premium Selection",
        "hero_title": f"Discover Handpicked Products at {name}",
        "hero_desc": f"Explore curated selections, top-rated products, and dedicated customer service from {name}.",
        "kpi_labels": {
            "catalog": "Catalog Items",
            "orders": "Placed Orders",
            "revenue": "Live Daily Revenue",
            "health": "In-Stock Items",
        },
        "categories": ["All", "Featured", "Popular", "Premium", "New Arrivals"],
        "products": [
            {"id": "g1", "name": f"{name} Signature Item", "category": "Featured", "price": 29.99, "icon": "⭐", "rating": 4.9, "reviews": 85, "stock": 40, "desc": f"The flagship premium item from {name} crafted with the highest standards."},
            {"id": "g2", "name": f"{name} Classic Essential", "category": "Popular", "price": 19.50, "icon": "✨", "rating": 4.8, "reviews": 64, "stock": 35, "desc": "Everyday favorite providing unmatched reliability and quality."},
            {"id": "g3", "name": f"{name} Deluxe Edition", "category": "Premium", "price": 49.00, "icon": "💎", "rating": 5.0, "reviews": 42, "stock": 20, "desc": "Exclusive upgraded edition with extended warranty and handcrafted finish."},
            {"id": "g4", "name": f"{name} Seasonal Select", "category": "New Arrivals", "price": 24.00, "icon": "🌟", "rating": 4.7, "reviews": 38, "stock": 30, "desc": "Limited seasonal release designed for modern enthusiasts."},
        ],
        "default_orders": [
            {"id": "ORD-GEN-101", "customer": "Alex Morgan", "phone": "555-0101", "address": "42 Main Street", "items": f"{name} Signature Item (x1)", "total": 29.99, "status": "Delivered", "date": "2026-11-03 15:00"},
            {"id": "ORD-GEN-102", "customer": "Sam Taylor", "phone": "555-0202", "address": "88 Elm Road", "items": f"{name} Deluxe Edition (x1)", "total": 49.00, "status": "Processing", "date": "2026-11-04 09:30"},
        ],
        "features": [
            f"{name} Product Catalog with Category Filtering",
            "Real-Time Shopping Cart with Quantity Controls",
            "Quick Checkout with Customer Details",
            "Live Stock & Order Fulfillment Updates",
            "Dynamic Daily Sales Revenue Analytics",
        ],
    }


def project_context(request: str) -> dict[str, Any]:
    """Analyzes the user mission request and extracts an authentic business profile."""
    text = request.lower().strip()
    business_name = extract_business_name(request)

    # 1. Student / Academic Portal
    if any(k in text for k in ["student", "school", "education", "university", "academic", "course", "college", "campus", "gradebook", "classroom", "curriculum", "transcripts"]):
        return {
            "domain": "student",
            "name": business_name if "student" in business_name.lower() or "portal" in business_name.lower() else f"{business_name} Student Portal",
            "kind": "Student Management & Academic Portal",
            "actor": "Student & Administrator",
            "entity": "student",
            "plural": "students",
            "primary_action": "manage student enrollments, track courses, view grades, and monitor academic progress",
            "features": [
                "Student Directory & Profile Management",
                "Course Registration & Enrollment Tracking",
                "Gradebook & Academic Transcript Generator",
                "Attendance & Performance Analytics Dashboard",
            ],
            "domain_models": [
                {
                    "name": "Student",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Unique student identifier"},
                        {"name": "student_code", "type": "String", "description": "Unique matriculation code"},
                        {"name": "first_name", "type": "String", "description": "Student given name"},
                        {"name": "last_name", "type": "String", "description": "Student family name"},
                        {"name": "email", "type": "String", "description": "Institutional email address"},
                        {"name": "department", "type": "String", "description": "Academic department or major"},
                        {"name": "gpa", "type": "Float", "description": "Cumulative Grade Point Average"},
                        {"name": "status", "type": "Enum", "description": "Active | Graduated | On Leave | Suspended"},
                    ],
                },
            ],
            "routes": [
                {"method": "GET", "path": "/api/students", "description": "List all enrolled students with search & department filters"},
                {"method": "POST", "path": "/api/students", "description": "Register a new student profile in the portal"},
                {"method": "GET", "path": "/api/students/{id}", "description": "Retrieve detailed student profile and transcript"},
                {"method": "PATCH", "path": "/api/students/{id}", "description": "Update student status, contact info, or GPA"},
                {"method": "DELETE", "path": "/api/students/{id}", "description": "Delete a student record"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
            "ui": [
                "Student Directory & Metrics Cards",
                "New Student Registration Form Modal",
                "Student Detail & Academic Transcript View",
                "Course Enrollment & Grade Management Panel",
            ],
            "feature_slug": "students",
            "pascal_entity": "Student",
        }

    # 1.5. Unit & Integration Testing Platform (TestFlow)
    if any(k in text for k in ["test", "testing", "unit test", "integration test", "testflow", "qa", "quality assurance", "test automation", "test suite", "test case"]):
        tf_name = "TestFlow – Unit & Integration Testing Management Platform" if any(w in text for w in ["testflow", "unit", "integration", "platform", "portal"]) else (business_name if "test" in business_name.lower() else f"{business_name} Testing Platform")
        return {
            "domain": "testing",
            "name": tf_name,
            "kind": "Unit & Integration Testing Management Platform",
            "actor": "QA Engineer & Test Architect",
            "entity": "test_suite",
            "plural": "test_suites",
            "primary_action": "manage unit test suites, run integration pipelines, monitor real-time test execution, and analyze coverage metrics",
            "brand_icon": "⚡",
            "brand_tag": "Enterprise QA Platform",
            "hero_tag": "⚡ Continuous Quality Automation",
            "hero_title": "Enterprise Unit & Integration Testing Platform",
            "hero_desc": "Unified testing workbench featuring real-time test execution monitoring, scenario building, code coverage analytics, and admin controls.",
            "kpi_labels": {
                "catalog": "Total Test Suites",
                "orders": "Test Runs Executed",
                "revenue": "Overall Pass Rate",
                "health": "Code Coverage",
            },
            "features": [
                "Executive QA Dashboard & Real-Time KPI Cards",
                "Interactive Units Directory with CRUD & Search",
                "Integration Testing Module with Scenario Configuration",
                "Real-Time Test Execution Console with Progress Streaming",
                "Interactive Visual Analytics (Coverage, Trends, Pass/Fail Ratio)",
                "Protected Admin Settings with Auth & Healing Control",
            ],
            "domain_models": [
                {
                    "name": "TestSuite",
                    "fields": [
                        {"name": "id", "type": "String", "description": "Unique test suite identifier"},
                        {"name": "name", "type": "String", "description": "Test suite name"},
                        {"name": "type", "type": "Enum", "description": "Unit | Integration | E2E | Security | API"},
                        {"name": "module", "type": "String", "description": "Application module under test"},
                        {"name": "cases_count", "type": "Integer", "description": "Total assertions count"},
                        {"name": "status", "type": "Enum", "description": "Passed | Failed | Running | Pending"},
                        {"name": "coverage", "type": "Float", "description": "Code coverage percentage"},
                        {"name": "duration_ms", "type": "Integer", "description": "Execution duration in milliseconds"},
                        {"name": "framework", "type": "String", "description": "PyTest | Jest | Playwright | Vitest"},
                    ],
                },
                {
                    "name": "TestRun",
                    "fields": [
                        {"name": "id", "type": "String", "description": "Run execution reference"},
                        {"name": "suite_name", "type": "String", "description": "Executed suite name"},
                        {"name": "status", "type": "Enum", "description": "Passed | Failed"},
                        {"name": "duration_ms", "type": "Integer", "description": "Execution latency"},
                        {"name": "assertions_passed", "type": "Integer", "description": "Passing assertions"},
                        {"name": "assertions_failed", "type": "Integer", "description": "Failing assertions"},
                        {"name": "log_output", "type": "String", "description": "Console output logs"},
                    ],
                },
            ],
            "routes": [
                {"method": "GET", "path": "/api/test-suites", "description": "List all test suites with status & module filters"},
                {"method": "POST", "path": "/api/test-suites", "description": "Create a new unit or integration test suite"},
                {"method": "POST", "path": "/api/test-runs/execute", "description": "Trigger real-time execution of test suites"},
                {"method": "GET", "path": "/api/analytics/coverage", "description": "Retrieve comprehensive test analytics"},
                {"method": "POST", "path": "/api/auth/admin-login", "description": "Authenticate QA administrator"},
                {"method": "GET", "path": "/api/health", "description": "QA engine health check"},
            ],
            "ui": [
                "Executive QA Dashboard",
                "Units Directory & Search/Filter Grid",
                "Integration Testing Scenario Builder",
                "Real-Time Execution Monitor Console",
                "Visual Analytics Charts",
                "Admin Control Panel",
            ],
            "feature_slug": "testing",
            "pascal_entity": "TestSuite",
        }

    # 2. Hospital / Healthcare Portal
    if any(k in text for k in ["hospital", "patient", "clinic", "health", "medical", "doctor", "appointment", "healthcare", "ehr", "physician", "nurse", "surgery", "telemedicine"]):
        h_profile = get_hospital_profile(business_name)
        return {
            **h_profile,
            "feature_slug": "appointments",
            "pascal_entity": "Appointment",
            "domain_models": [
                {
                    "name": "Doctor",
                    "fields": [
                        {"name": "id", "type": "String", "description": "Doctor ID"},
                        {"name": "name", "type": "String", "description": "Doctor Name"},
                        {"name": "specialty", "type": "String", "description": "Medical Specialty"},
                        {"name": "fee", "type": "Decimal", "description": "Consultation Fee"},
                    ],
                },
                {
                    "name": "Appointment",
                    "fields": [
                        {"name": "id", "type": "String", "description": "Appointment Reference"},
                        {"name": "patient_name", "type": "String", "description": "Patient Name"},
                        {"name": "doctor_name", "type": "String", "description": "Attending Doctor"},
                        {"name": "scheduled_time", "type": "DateTime", "description": "Appointment Time"},
                        {"name": "status", "type": "Enum", "description": "Scheduled | Confirmed | Completed | Cancelled"},
                    ],
                },
            ],
            "routes": [
                {"method": "GET", "path": "/api/doctors", "description": "List specialist doctors"},
                {"method": "GET", "path": "/api/appointments", "description": "List patient appointments"},
                {"method": "POST", "path": "/api/appointments", "description": "Book a new appointment"},
                {"method": "GET", "path": "/api/health", "description": "Healthcare service health check"},
            ],
        }

    # 3. Juice Centre & Smoothie Bar
    if any(k in text for k in ["juice", "juices", "smoothie", "smoothies", "milkshake", "milkshakes", "beverage", "beverages", "cold-pressed", "fruit bar", "refreshment"]):
        j_profile = get_juice_profile(business_name)
        return {
            **j_profile,
            "feature_slug": "orders",
            "pascal_entity": "Order",
            "domain_models": [
                {"name": "Juice", "fields": [{"name": "id", "type": "String"}, {"name": "name", "type": "String"}, {"name": "price", "type": "Decimal"}, {"name": "stock", "type": "Integer"}]},
                {"name": "Order", "fields": [{"name": "id", "type": "String"}, {"name": "customer", "type": "String"}, {"name": "total", "type": "Decimal"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List juice catalog"},
                {"method": "POST", "path": "/api/orders", "description": "Place a fresh juice order"},
                {"method": "GET", "path": "/api/orders", "description": "List juice orders"},
                {"method": "GET", "path": "/api/analytics", "description": "Live daily juice revenue metrics"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
        }

    # 4. Restaurant & Dining
    if any(k in text for k in ["restaurant", "dining", "cafe", "bistro", "food", "dish", "dishes", "cuisine", "menu", "chef", "meal", "meals", "eatery", "diner", "pizza", "burger", "pasta"]):
        r_profile = get_restaurant_profile(business_name)
        return {
            **r_profile,
            "feature_slug": "orders",
            "pascal_entity": "Order",
            "domain_models": [
                {"name": "Dish", "fields": [{"name": "id", "type": "String"}, {"name": "name", "type": "String"}, {"name": "price", "type": "Decimal"}, {"name": "stock", "type": "Integer"}]},
                {"name": "Order", "fields": [{"name": "id", "type": "String"}, {"name": "customer", "type": "String"}, {"name": "total", "type": "Decimal"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List restaurant food menu"},
                {"method": "POST", "path": "/api/orders", "description": "Place a dining/delivery food order"},
                {"method": "GET", "path": "/api/orders", "description": "List active food orders"},
                {"method": "GET", "path": "/api/analytics", "description": "Live restaurant sales analytics"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
        }

    # 5. Bakery & Patisserie
    if any(k in text for k in ["bakery", "baker", "cake", "cakes", "pastry", "pastries", "bread", "breads", "croissant", "cookies", "cupcake", "patisserie", "dessert"]):
        b_profile = get_bakery_profile(business_name)
        return {
            **b_profile,
            "feature_slug": "orders",
            "pascal_entity": "Order",
            "domain_models": [
                {"name": "Pastry", "fields": [{"name": "id", "type": "String"}, {"name": "name", "type": "String"}, {"name": "price", "type": "Decimal"}, {"name": "stock", "type": "Integer"}]},
                {"name": "Order", "fields": [{"name": "id", "type": "String"}, {"name": "customer", "type": "String"}, {"name": "total", "type": "Decimal"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List bakery treats catalog"},
                {"method": "POST", "path": "/api/orders", "description": "Place a bakery order"},
                {"method": "GET", "path": "/api/orders", "description": "List bakery orders"},
                {"method": "GET", "path": "/api/analytics", "description": "Live bakery sales metrics"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
        }

    # 6. Clothing & Fashion Boutique
    if any(k in text for k in ["clothing", "apparel", "fashion", "boutique", "garment", "wear", "dress", "shirt", "jacket", "pants", "jeans", "outfit", "wardrobe"]):
        c_profile = get_clothing_profile(business_name)
        return {
            **c_profile,
            "feature_slug": "orders",
            "pascal_entity": "Order",
            "domain_models": [
                {"name": "Garment", "fields": [{"name": "id", "type": "String"}, {"name": "name", "type": "String"}, {"name": "price", "type": "Decimal"}, {"name": "stock", "type": "Integer"}]},
                {"name": "Order", "fields": [{"name": "id", "type": "String"}, {"name": "customer", "type": "String"}, {"name": "total", "type": "Decimal"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List apparel collection"},
                {"method": "POST", "path": "/api/orders", "description": "Place a boutique order"},
                {"method": "GET", "path": "/api/orders", "description": "List customer orders"},
                {"method": "GET", "path": "/api/analytics", "description": "Live boutique sales metrics"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
        }

    # 7. Tech & Electronics (Explicit request only)
    if any(k in text for k in ["electronics", "gadget", "gadgets", "tech store", "hardware store", "computer store", "headphones"]):
        e_profile = get_tech_ecommerce_profile(business_name)
        return {
            **e_profile,
            "feature_slug": "orders",
            "pascal_entity": "Order",
            "domain_models": [
                {"name": "Product", "fields": [{"name": "id", "type": "String"}, {"name": "name", "type": "String"}, {"name": "price", "type": "Decimal"}, {"name": "stock", "type": "Integer"}]},
                {"name": "Order", "fields": [{"name": "id", "type": "String"}, {"name": "customer", "type": "String"}, {"name": "total", "type": "Decimal"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List electronics catalog"},
                {"method": "POST", "path": "/api/orders", "description": "Place a hardware order"},
                {"method": "GET", "path": "/api/orders", "description": "List store orders"},
                {"method": "GET", "path": "/api/analytics", "description": "Live sales analytics"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
        }

    # 8. Library & Catalog Management
    if any(k in text for k in ["library", "book", "books", "borrow", "reading", "book catalog", "librarian"]):
        return {
            "domain": "library",
            "name": business_name if "library" in business_name.lower() else f"{business_name} Library",
            "kind": "Digital Library & Catalog Management System",
            "actor": "Member & Head Librarian",
            "entity": "book",
            "plural": "books",
            "primary_action": "browse book catalog, issue books, return volumes, and monitor circulation records",
            "brand_icon": "📚",
            "brand_tag": "Library Catalog & Circulation",
            "hero_tag": "📖 Digital Reading Resource",
            "hero_title": "Explore Our Curated Library Catalog & Knowledge Base",
            "hero_desc": "Search thousands of volumes, manage borrowing history, issue loans, and track return schedules.",
            "kpi_labels": {
                "catalog": "Total Catalog Books",
                "orders": "Active Book Loans",
                "revenue": "Reserved Titles",
                "health": "Available on Shelf",
            },
            "features": [
                "Catalog Search with Author, Genre, and ISBN Filters",
                "Automated Borrow & Return Circulation Desk",
                "Overdue Loan Monitoring with Fine Calculations",
                "Digital Member Card & Loan History Explorer",
                "Live Shelf Inventory & Collection Health Metrics",
            ],
            "feature_slug": "books",
            "pascal_entity": "Book",
            "domain_models": [
                {"name": "Book", "fields": [{"name": "id", "type": "String"}, {"name": "title", "type": "String"}, {"name": "author", "type": "String"}, {"name": "isbn", "type": "String"}, {"name": "status", "type": "Enum"}]},
                {"name": "Loan", "fields": [{"name": "id", "type": "String"}, {"name": "book_id", "type": "String"}, {"name": "borrower", "type": "String"}, {"name": "due_date", "type": "DateTime"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/books", "description": "Search and list catalog books"},
                {"method": "POST", "path": "/api/loans", "description": "Issue a book loan to a borrower"},
                {"method": "GET", "path": "/api/loans", "description": "List current active loans"},
                {"method": "POST", "path": "/api/returns", "description": "Process a book return"},
                {"method": "GET", "path": "/api/health", "description": "Circulation desk health check"},
            ],
        }

    # 9. Employee & HR Portal
    if any(k in text for k in ["employee", "staff", "human resources", "hr portal", "payroll", "personnel", "workforce"]):
        return {
            "domain": "employee",
            "name": business_name if "hr" in business_name.lower() or "employee" in business_name.lower() else f"{business_name} HR Portal",
            "kind": "Enterprise HR & Personnel Management System",
            "actor": "Staff Member & HR Lead",
            "entity": "employee",
            "plural": "employees",
            "primary_action": "manage employee directory, record onboardings, process leaves, and view payroll metrics",
            "brand_icon": "👥",
            "brand_tag": "Workforce Directory & HR",
            "hero_tag": "💼 People Operations Hub",
            "hero_title": "Modern Team Collaboration & Staff Management",
            "hero_desc": "Unified directory of team members, departments, compensation tiers, and leave requests.",
            "kpi_labels": {
                "catalog": "Active Employees",
                "orders": "Pending Leave Requests",
                "revenue": "Monthly Payroll",
                "health": "Department Coverage",
            },
            "features": [
                "Staff Directory with Department and Role Badges",
                "Employee Onboarding & Registration Form",
                "Paid Time Off (PTO) & Leave Approval Workflow",
                "Performance Review & Appraisal Tracking",
                "Headcount & Compensation Distribution Analytics",
            ],
            "feature_slug": "employees",
            "pascal_entity": "Employee",
            "domain_models": [
                {"name": "Employee", "fields": [{"name": "id", "type": "String"}, {"name": "full_name", "type": "String"}, {"name": "department", "type": "String"}, {"name": "role", "type": "String"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/employees", "description": "List all active team employees"},
                {"method": "POST", "path": "/api/employees", "description": "Register a new employee record"},
                {"method": "GET", "path": "/api/departments", "description": "List department rosters"},
                {"method": "GET", "path": "/api/health", "description": "HR service health check"},
            ],
        }

    # 10. Warehouse & Inventory Management
    if any(k in text for k in ["inventory", "warehouse", "stock", "supply chain", "logistics", "depot"]):
        return {
            "domain": "inventory",
            "name": business_name if "inventory" in business_name.lower() or "warehouse" in business_name.lower() else f"{business_name} Inventory",
            "kind": "Real-Time Warehouse & Inventory Operations",
            "actor": "Warehouse Manager & Logistics Lead",
            "entity": "item",
            "plural": "items",
            "primary_action": "audit warehouse stock, track SKU bin locations, replenish supplies, and manage dispatch",
            "brand_icon": "📦",
            "brand_tag": "SKU Inventory Control",
            "hero_tag": "🏭 Warehouse Supply Chain",
            "hero_title": "Real-Time Inventory Control & Warehouse Tracking",
            "hero_desc": "Monitor stock levels across aisles, track inbound shipments, manage restock thresholds, and prevent shortages.",
            "kpi_labels": {
                "catalog": "Monitored SKUs",
                "orders": "Pending Inbound Shipments",
                "revenue": "Total Inventory Value",
                "health": "Low Stock Alerts",
            },
            "features": [
                "SKU Catalog with Bin Location & Barcode Tracking",
                "Inbound Stock Receipt & Quality Inspection",
                "Automated Low Stock Replenishment Triggers",
                "Stock Movement & Transfer Audit Logs",
                "Storage Capacity & Turnover Rate Dashboards",
            ],
            "feature_slug": "inventory",
            "pascal_entity": "InventoryItem",
            "domain_models": [
                {"name": "Item", "fields": [{"name": "sku", "type": "String"}, {"name": "name", "type": "String"}, {"name": "quantity", "type": "Integer"}, {"name": "location", "type": "String"}, {"name": "reorder_level", "type": "Integer"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/inventory", "description": "List SKU inventory records"},
                {"method": "POST", "path": "/api/inventory/adjust", "description": "Adjust stock counts"},
                {"method": "GET", "path": "/api/inventory/alerts", "description": "List low-stock warnings"},
                {"method": "GET", "path": "/api/health", "description": "Warehouse engine health check"},
            ],
        }

    # 11. General Store / E-Commerce fallback
    if any(k in text for k in ["store", "shop", "e-commerce", "ecommerce", "e commerce", "commerce", "order", "product", "cart", "checkout", "retail", "marketplace", "merchandise", "shopping", "catalog"]):
        g_profile = get_generic_commerce_profile(business_name, "Retail Products")
        return {
            **g_profile,
            "feature_slug": "orders",
            "pascal_entity": "Order",
            "domain_models": [
                {"name": "Item", "fields": [{"name": "id", "type": "String"}, {"name": "name", "type": "String"}, {"name": "price", "type": "Decimal"}, {"name": "stock", "type": "Integer"}]},
                {"name": "Order", "fields": [{"name": "id", "type": "String"}, {"name": "customer", "type": "String"}, {"name": "total", "type": "Decimal"}, {"name": "status", "type": "Enum"}]},
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List products"},
                {"method": "POST", "path": "/api/orders", "description": "Place an order"},
                {"method": "GET", "path": "/api/orders", "description": "List orders"},
                {"method": "GET", "path": "/api/analytics", "description": "Live store metrics"},
                {"method": "GET", "path": "/api/health", "description": "Service health check"},
            ],
        }

    # 9. Generic Custom Operations System
    words = [w for w in business_name.split() if w.lower() not in ["app", "portal", "system", "platform", "manager", "tracker"]]
    main_word = words[0] if words else "Record"
    entity = main_word.lower()
    plural = f"{entity}s"
    pascal_entity = main_word.capitalize()

    return {
        "domain": "generic",
        "name": business_name,
        "kind": f"{business_name} Operations System",
        "actor": "Operator & End User",
        "entity": entity,
        "plural": plural,
        "primary_action": f"manage, create, update, and inspect {plural} efficiently",
        "features": [
            f"{business_name} Interactive Dashboard & Analytics",
            f"Validated {pascal_entity} Creation & Form Management",
            f"Search, Filtering, and Batch Operations for {plural.capitalize()}",
            "Audit Trail, Activity Logs, and System Status Metrics",
        ],
        "domain_models": [
            {
                "name": pascal_entity,
                "fields": [
                    {"name": "id", "type": "UUID", "description": f"Unique {entity} identifier"},
                    {"name": "title", "type": "String", "description": f"Name or label of the {entity}"},
                    {"name": "status", "type": "Enum", "description": "Draft | Active | Archived | Completed"},
                    {"name": "created_at", "type": "DateTime", "description": "Creation timestamp"},
                    {"name": "updated_at", "type": "DateTime", "description": "Last modified timestamp"},
                ],
            },
        ],
        "routes": [
            {"method": "GET", "path": f"/api/{plural}", "description": f"Retrieve list of {plural} with pagination"},
            {"method": "POST", "path": f"/api/{plural}", "description": f"Create a new {entity} record"},
            {"method": "GET", "path": f"/api/{plural}/{{id}}", "description": f"Fetch details for a specific {entity}"},
            {"method": "PATCH", "path": f"/api/{plural}/{{id}}", "description": f"Update properties of a {entity}"},
            {"method": "DELETE", "path": f"/api/{plural}/{{id}}", "description": f"Delete a {entity}"},
            {"method": "GET", "path": "/api/health", "description": "Service health check"},
        ],
        "ui": [
            f"{pascal_entity} Overview Dashboard",
            f"Create {pascal_entity} Modal Form",
            f"{pascal_entity} Details & History Timeline",
            "System Health & Metric Cards",
        ],
        "feature_slug": plural,
        "pascal_entity": pascal_entity,
    }

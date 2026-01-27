import json
import random

# --- 1. CONFIGURATION & IMAGES (Color-Coded) ---
# We use Placehold.co because it NEVER fails.
IMG_CEMENT = "https://placehold.co/600x400/808080/FFFFFF/png?text=CEMENT+(Water+Retaining)"
IMG_SAND = "https://placehold.co/600x400/eda00b/FFFFFF/png?text=SHARP+SAND+(20T)"
IMG_GRANITE = "https://placehold.co/600x400/4a4a4a/FFFFFF/png?text=GRANITE+(3/4+inch)"
IMG_BLOCKS = "https://placehold.co/600x400/8b4513/FFFFFF/png?text=BLOCKS+(Vibrated)"
IMG_STEEL = "https://placehold.co/600x400/2c3e50/FFFFFF/png?text=STEEL+ROD+(TMT)"
IMG_ROOF = "https://placehold.co/600x400/c0392b/FFFFFF/png?text=ROOFING+SHEET"
IMG_FINISH = "https://placehold.co/600x400/e67e22/FFFFFF/png?text=TILES+/+POP"
IMG_PLUMB = "https://placehold.co/600x400/3498db/FFFFFF/png?text=PLUMBING+PIPE"
IMG_ELEC = "https://placehold.co/600x400/f1c40f/000000/png?text=ELECTRICAL+CABLE"

# --- 2. REAL GEOLOCATED SUPPLIERS ---
# These coordinates map to real markets in Ibadan.
suppliers = [
    {
        "name": "AdMub Sands (Iwo Road)", 
        "location": "Iwo Road, Ibadan", 
        "_geoloc": {"lat": 7.4019, "lng": 3.9173}
    },
    {
        "name": "Bodija Builders Mart", 
        "location": "Bodija, Ibadan", 
        "_geoloc": {"lat": 7.4228, "lng": 3.8960}
    },
    {
        "name": "Oyo Concrete Works", 
        "location": "Challenge, Ibadan", 
        "_geoloc": {"lat": 7.3468, "lng": 3.8789}
    },
    {
        "name": "Titanium Steel Depot", 
        "location": "Ring Road, Ibadan", 
        "_geoloc": {"lat": 7.3585, "lng": 3.8596}
    }
]

materials = []

# Helper function to create items easily
def add_item(category, name, price, unit, image, description):
    # Pick a random supplier for variety
    sup = random.choice(suppliers)
    materials.append({
        "objectID": f"{category[:3]}_{random.randint(10000, 99999)}",
        "name": name,
        "category": category,
        "price": price,
        "unit": unit,
        "supplier": sup["name"],
        "location": sup["location"],
        "_geoloc": sup["_geoloc"],  # Crucial for "Nearest Location" feature
        "image_url": image,
        "description": description
    })

# --- 3. POPULATE DATA (Merging all your requests) ---

# === A. BASICS (Concrete & Shell) ===
# Cement
brands = ["Dangote 3X 42.5R", "Elephant Supaset", "Lafarge 42.5N"]
for brand in brands:
    add_item("Cement", f"Cement - {brand} (50kg)", random.randint(9500, 10500), "Bag", IMG_CEMENT, "Portland limestone cement.")

# Aggregates
add_item("Aggregates", "Sharp Sand (20 tons)", random.randint(120000, 140000), "Truck", IMG_SAND, "River sharp sand for concreting.")
add_item("Aggregates", "Granite 3/4 inch (30 tons)", random.randint(600000, 680000), "Truck", IMG_GRANITE, "Clean granite stone.")
add_item("Aggregates", "Plaster Sand (20 tons)", random.randint(100000, 120000), "Truck", IMG_SAND, "Soft sand for plastering.")

# Blocks
add_item("Blocks", "9-inch Vibrated Block", 650, "Block", IMG_BLOCKS, "Load bearing hollow block.")
add_item("Blocks", "6-inch Vibrated Block", 500, "Block", IMG_BLOCKS, "Partition wall block.")

# === B. STRUCTURAL STEEL ===
sizes = [8, 10, 12, 16, 20, 25]
for s in sizes:
    add_item("Steel", f"{s}mm Iron Rod (TMT)", 4500 + (s*600), "Length (12m)", IMG_STEEL, f"High Yield TMT Reinforcement Bar Y{s}.")

# === C. ROOFING & CEILING ===
add_item("Roofing", "Stone Coated Tiles (Bond)", 4200, "sqm", IMG_ROOF, "Premium stone coated roofing tile.")
add_item("Roofing", "Long Span Aluminium (0.55mm)", 3800, "Meter", IMG_ROOF, "Standard aluminium roofing sheet.")
add_item("Roofing", "POP Cement (40kg)", 8500, "Bag", IMG_FINISH, "Plaster of Paris for ceiling casting.")
add_item("Roofing", "PVC Ceiling Strip", 1500, "Bundle", IMG_ROOF, "PVC Ceiling panels.")

# === D. FINISHING (Tiles) ===
add_item("Finishing", "Vitrified Floor Tile (60x60)", 4500, "sqm", IMG_FINISH, "Polished vitrified tiles.")
add_item("Finishing", "Ceramic Wall Tile (30x60)", 3500, "sqm", IMG_FINISH, "Glazed wall tiles.")
add_item("Finishing", "Royal Marble Tile", 15000, "sqm", IMG_FINISH, "High-end marble finish.")

# === E. PLUMBING (PVC, PPR, CPVC) ===
add_item("Plumbing", "4-inch PVC Waste Pipe", 4500, "Length (4m)", IMG_PLUMB, "Drainage/Sewage pipe.")
add_item("Plumbing", "20mm PPR Pipe (Supply)", 3500, "Length (4m)", IMG_PLUMB, "Hot/Cold water supply.")
add_item("Plumbing", "3/4 inch CPVC Pipe", 2800, "Length", IMG_PLUMB, "Hot water supply pipe.")
add_item("Plumbing", "PVC Elbow 4-inch", 500, "Piece", IMG_PLUMB, "Fittings.")
add_item("Plumbing", "Pressure Pump (1.5HP)", 85000, "Piece", IMG_PLUMB, "Water pump.")

# === F. ELECTRICAL ===
add_item("Electrical", "2.5mm Single Core Cable", 18500, "Coil (100m)", IMG_ELEC, "Socket circuit wire (Pure Copper).")
add_item("Electrical", "1.5mm Single Core Cable", 12500, "Coil (100m)", IMG_ELEC, "Lighting circuit wire.")
add_item("Electrical", "4.0mm Single Core Cable", 29000, "Coil (100m)", IMG_ELEC, "A/C circuit wire.")
add_item("Electrical", "20mm PVC Conduit", 900, "Length", IMG_ELEC, "Wiring protection pipe.")
add_item("Electrical", "13A Double Socket", 2800, "Piece", IMG_ELEC, "Wall outlet.")

# --- 4. EXPORT ---
filename = 'unified_construction_database.json'
with open(filename, 'w') as f:
    json.dump(materials, f, indent=2)

print(f"SUCCESS: Generated {len(materials)} records in '{filename}'.")
print("INSTRUCTION: Go to Algolia -> Manage Index -> CLEAR INDEX -> Then UPLOAD this file.")
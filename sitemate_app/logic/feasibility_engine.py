import math

def check_feasibility(location, building_type, floors, land_size_sqm):
    """
    Provides a rough 'Ballpark Estimate' based on location, building type, AND Land Size.
    """
    
    # 1. Base Construction Cost per Square Meter (NGN) - 2026 Estimates
    # Lekki is premium (swampy foundation cost), Ibadan is cheaper.
    BASE_RATES = {
        "Lekki, Lagos": 450000, 
        "Ibadan, Oyo": 250000, 
        "Abuja, FCT": 380000
    }
    
    # 2. Structure Standard Sizes (Floor Area in SQM)
    SIZES = {
        "3-Bedroom Bungalow": 150, 
        "4-Bedroom Duplex": 280,   
        "BQ / Boys Quarters": 50,
        "Perimeter Fence (Plot)": 0 # Calculated dynamically below
    }
    
    rate = BASE_RATES.get(location, 300000)
    build_area = SIZES.get(building_type, 100)
    
    # 3. Dynamic Calculation Logic
    if building_type == "Perimeter Fence (Plot)":
        # Calculate Perimeter based on Land Area (assuming 1:2 rectangular plot ratio, common in NG)
        # Area = L * W. Let W = x, L = 2x. Area = 2x^2. x = sqrt(Area/2).
        width = math.sqrt(land_size_sqm / 2)
        length = 2 * width
        perimeter = 2 * (length + width) # Linear Meters
        
        fence_rate_per_m = 40000 # Block + Foundation + Plaster per meter
        if "Lekki" in location: fence_rate_per_m *= 1.5 # Raft foundation factor
        
        est_cost = perimeter * fence_rate_per_m
        details = f"Est. {perimeter:.0f}m Fence on {land_size_sqm}sqm land."

    else:
        # Standard Building
        # Check if land is too small
        if land_size_sqm < build_area:
            return {"low": "N/A", "high": "N/A", "details": "⚠️ Land too small for this building!"}
            
        est_cost = rate * build_area
        if floors > 1 and "Duplex" not in building_type:
            est_cost *= (1 + (floors * 0.2)) # 20% extra per floor

        # Add Site Prep Cost (Clearing/filling based on land size)
        prep_rate = 2000 if "Lekki" not in location else 8000 # Sandfilling in Lekki
        site_prep = land_size_sqm * prep_rate
        est_cost += site_prep
        
        details = f"Building: {build_area}sqm | Site Prep: ₦{site_prep:,.0f} (for {land_size_sqm}sqm)"

    # 4. Ranges
    low_est = est_cost * 0.90
    high_est = est_cost * 1.15

    return {
        "low": f"₦{low_est:,.0f}",
        "high": f"₦{high_est:,.0f}",
        "details": details
    }
def check_feasibility(location, building_type, floors):
    """
    Provides a rough 'Ballpark Estimate' based on location and building type.
    Rates are based on current Nigerian Construction costs per sqm (Approx).
    """
    
    # 1. Base Construction Cost per Square Meter (NGN) - 2026 Estimates
    # Lekki is premium (swampy foundation cost), Ibadan is cheaper, Abuja is high.
    BASE_RATES = {
        "Lekki, Lagos": 450000, 
        "Ibadan, Oyo": 250000, 
        "Abuja, FCT": 380000
    }
    
    # 2. Building Size Multipliers (Approx SQM)
    SIZES = {
        "3-Bedroom Bungalow": 150, # sqm
        "4-Bedroom Duplex": 300,   # sqm (roughly 150 per floor)
        "BQ / Boys Quarters": 60,
        "Perimeter Fence (Plot)": 1 # Special handling
    }
    
    rate = BASE_RATES.get(location, 300000)
    size = SIZES.get(building_type, 100)
    
    # 3. Fence Logic (Linear Meters, not SQM)
    if building_type == "Perimeter Fence (Plot)":
        # Standard 600sqm plot = ~120 linear meters
        linear_meters = 120 
        fence_rate_per_m = 35000 # Cost per meter (Block + Foundation + Plaster)
        if "Lekki" in location: fence_rate_per_m *= 1.4 # Raft foundation
        
        low_est = linear_meters * fence_rate_per_m * 0.9
        high_est = linear_meters * fence_rate_per_m * 1.1
        
    else:
        # Standard Building Logic
        est_cost = rate * size
        if floors > 1 and "Duplex" not in building_type:
            est_cost *= (1 + (floors * 0.2)) # Add 20% per extra floor for decking/reinforcement

        low_est = est_cost * 0.85  # Best case
        high_est = est_cost * 1.15 # Inflation case

    # 4. Format Output
    return {
        "low": f"₦{low_est:,.0f}",
        "high": f"₦{high_est:,.0f}",
        "details": f"Based on avg cost of **₦{rate:,.0f}/sqm** in {location}."
    }
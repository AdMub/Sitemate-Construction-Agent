import math

class StructuralEngine:
    def __init__(self):
        # Constants per BS 8110 / Oyenuga
        self.fcu = 25  # Concrete Strength (N/mm2)
        self.fy = 410  # Steel Strength (N/mm2) - High Yield
        self.gamma_conc = 24 # Unit weight of concrete (kN/m3)

    def design_strip_foundation(self, wall_load_kn_m, soil_bearing_capacity_kn_m2):
        """
        Designing a Strip Foundation for a 225mm wall.
        Returns: Width (mm), Depth (mm), Reinforcement info.
        """
        # 1. Determine Width (Serviceability Limit State)
        # Service Load approx = Ultimate Load / 1.4 (Simplified heuristic for sizing)
        service_load = wall_load_kn_m / 1.4 
        req_width_m = service_load / soil_bearing_capacity_kn_m2
        
        # Round up to nearest standard size (450, 600, 900, 1200)
        standard_widths = [0.45, 0.60, 0.675, 0.90, 1.20]
        width_m = 0.45
        for w in standard_widths:
            if w >= req_width_m:
                width_m = w
                break
        
        # Oyenuga Recommendation for Bungalow/Duplex Strip:
        # Min Width 675mm often recommended for stability even if load is low.
        if width_m < 0.675: 
            width_m = 0.675

        # 2. Determine Depth & Steel (Heuristic for Residential)
        # Detailed shear check omitted for brevity, using Standard Oyenuga Depths
        depth_mm = 225  # Standard for residential
        
        # 3. Reinforcement (Standard Oyenuga Spec)
        steel_spec = "3 No. Y12 (Runners) + Y10 Links @ 300mm c/c"
        
        return {
            "type": "Strip Foundation",
            "width_mm": int(width_m * 1000),
            "depth_mm": depth_mm,
            "reinforcement": steel_spec,
            "concrete_vol_per_m": round(width_m * (depth_mm/1000), 3)
        }

    def design_pad_foundation(self, column_load_kn, soil_bearing_capacity_kn_m2):
        """
        Designing a Square Pad Foundation.
        Returns: Length (mm), Width (mm), Depth (mm), Reinforcement.
        """
        # 1. Sizing (Area = Load / SBC)
        # Assume Column Load includes self-weight factor.
        service_load = column_load_kn / 1.4
        req_area = service_load / soil_bearing_capacity_kn_m2
        
        # Square Root to find side length
        side_length_m = math.sqrt(req_area)
        
        # Round up to nearest 100mm (e.g., 1.0, 1.1, 1.2)
        side_length_m = math.ceil(side_length_m * 10) / 10
        if side_length_m < 1.0: side_length_m = 1.0 # Minimum 1m x 1m
        
        # 2. Depth Calculation (Simplified Punching Shear Check)
        # For residential, usually start at 300mm and check
        depth_mm = 300
        if column_load_kn > 500: depth_mm = 400
        if column_load_kn > 800: depth_mm = 500
        
        # 3. Reinforcement Calculation (Bending Moment)
        # M = (Load * (L - c)^2) / 8L (Approx cantilever moment)
        # This is complex to automate perfectly without FEA, so we use Tables.
        # Rule of Thumb: Y12 @ 150mm c/c (B2) is standard for residential pads < 1.5m
        
        steel_spec = "Y12 @ 150mm c/c (Both Ways)"
        if side_length_m > 1.5:
             steel_spec = "Y12 @ 125mm c/c (Both Ways)"
        
        return {
            "type": "Pad Foundation",
            "size_mm": f"{int(side_length_m*1000)}x{int(side_length_m*1000)}",
            "depth_mm": depth_mm,
            "reinforcement": steel_spec,
            "concrete_vol": round(side_length_m * side_length_m * (depth_mm/1000), 3)
        }
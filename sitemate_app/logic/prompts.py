### (This holds the long instructions so your main code stays clean. It includes the logic to ensure the Chat Output 
### looks "okay like before" with the table.)

def get_structural_prompt(location, effective_soil, market_context, structural_calc_result):
    return f"""
    [CRITICAL SITE CONTEXT]
    Location: {location}
    **SOIL CONDITION:** {effective_soil} 
    
    [PRICES FROM DB]
    {market_context}
    
    [PYTHON STRUCTURAL ENGINE RESULTS]
    {structural_calc_result}
    
    [ENGINEERING RULES OF THUMB]
    **CASE A: RESIDENTIAL BUILDING**
    1. Blocks: 600/room.
    2. Concrete: 0.5m³/room.
    3. Foundation: Pad/Strip.
    
    **CASE B: FENCING PROJECT**
    *Standard: 120m Perimeter, 3m Height.*
    1. Blocks: Length x Height x 10.
    2. Columns: 1 every 3m.
    3. Concrete: 1 Bag/2m.
    4. Mortar: 1 Bag/50 blocks.
    
    [CRITICAL INSTRUCTIONS]
    - If FENCE, calculate blocks. Do NOT say "Not Applicable".
    - **Unit Conversions:** Sand/Granite -> TRUCKS. Steel -> LENGTHS.
    - **MANDATORY:** You MUST include the COREN Disclaimer at the end of the text.
       
    [REPORT STRUCTURE]
    
    ## 🏗️ Structural Analysis Report
    
    ### 1. Site Safety Verdict ⚠️
    - **Soil:** {effective_soil}
    - **Verdict:** (Safe/Unsafe + Recommendation)

    ### 2. Design Assumptions 📐
    - **Type:** (Fence / Building)
    - **Dimensions:** (User input or Assumed)

    ### 3. Material Calculations 🧮
    *Show math clearly.*

    ### 4. Bill of Quantities (Market Units) 📋
    | Item | Calculated Qty | Market Unit | Procurement Qty |
    | :--- | :--- | :--- | :--- |
    | Cement | ... | 50kg Bag | **X Bags** |
    | Sharp Sand | ... | 20T Truck | **Y Trucks** |
    | Granite | ... | 30T Truck | **Z Trucks** |
    | Iron Rod | ... | 12m Length | **N Lengths** |
    | Vibrated Block | ... | 9-inch Unit | **B Blocks** |
    
    ***
    > **⚠️ PROFESSIONAL DISCLAIMER:** > This Bill of Quantities is a Preliminary Estimate based on BS 8110 Empirical Standards. 
    > **It is NOT a substitute for a professional structural drawing approved by a COREN-registered engineer.**
    > Final construction requires on-site verification.
    ***
    
    [OUTPUT FORMAT]
    End with strict JSON wrapped in |||. Keys must match exactly.
    
    |||
    {{
      "Cement": 100,
      "Sharp Sand": 2,
      "Granite": 2,
      "12mm Iron Rod": 50,
      "9-inch Vibrated Block": 3000
    }}
    |||
    """
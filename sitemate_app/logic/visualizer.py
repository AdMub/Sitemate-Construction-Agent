import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

def render_strip_foundation(width_mm, depth_mm):
    """
    Draws a cross-section of a Strip Foundation.
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(6, 3))
    
    # 1. Draw Concrete Rect (Grey)
    rect = patches.Rectangle((0, 0), width_mm, depth_mm, linewidth=2, edgecolor='#2C3E50', facecolor='#BDC3C7')
    ax.add_patch(rect)
    
    # 2. Draw Blinding (Thin layer below)
    blinding = patches.Rectangle((-50, -50), width_mm + 100, 50, linewidth=1, edgecolor='#7F8C8D', facecolor='#ECF0F1', linestyle='--')
    ax.add_patch(blinding)
    
    # 3. Draw Reinforcement (Red Dots for bars)
    # 3 Bottom Bars (Runners)
    margin = 50
    spacing = (width_mm - 2*margin) / 2
    for i in range(3):
        x_pos = margin + (i * spacing)
        circle = patches.Circle((x_pos, 50), radius=12, color='#E74C3C', label='Y12 Main Bars')
        ax.add_patch(circle)
        
    # 4. Labels & Dimensions
    ax.text(width_mm/2, depth_mm + 30, f"Width: {width_mm}mm", ha='center', fontsize=10, color='black', weight='bold')
    ax.text(-80, depth_mm/2, f"Depth:\n{depth_mm}mm", ha='right', va='center', fontsize=9, color='black')
    
    # 5. Styling
    ax.set_xlim(-150, width_mm + 150)
    ax.set_ylim(-100, depth_mm + 150)
    ax.set_aspect('equal')
    ax.axis('off') # Hide axis numbers
    ax.set_title("SECTION A-A: STRIP FOUNDATION", fontsize=12, weight='bold', pad=10)
    
    return fig

def render_pad_foundation(size_str, depth_mm):
    """
    Draws a Plan View (Top View) of a Pad Foundation.
    Expects size_str like "1000x1000"
    """
    try:
        L = int(size_str.split('x')[0])
        W = int(size_str.split('x')[1])
    except:
        L, W = 1000, 1000

    fig, ax = plt.subplots(figsize=(5, 5))
    
    # 1. Draw Pad Plan (Square)
    rect = patches.Rectangle((0, 0), L, W, linewidth=2, edgecolor='#2C3E50', facecolor='#BDC3C7')
    ax.add_patch(rect)
    
    # 2. Draw Column in Center
    col_w = 225
    col_x = (L - col_w)/2
    col_y = (W - col_w)/2
    col = patches.Rectangle((col_x, col_y), col_w, col_w, linewidth=0, facecolor='#2C3E50')
    ax.add_patch(col)
    
    # 3. Draw Grid Lines (Reinforcement Indication)
    for i in range(1, 5):
        # Vertical lines
        ax.plot([i*(L/5), i*(L/5)], [50, W-50], color='#E74C3C', linestyle='-', linewidth=1)
        # Horizontal lines
        ax.plot([50, L-50], [i*(W/5), i*(W/5)], color='#E74C3C', linestyle='-', linewidth=1)

    # 4. Labels
    ax.text(L/2, -100, f"Length: {L}mm", ha='center', fontsize=10, weight='bold')
    ax.text(-100, W/2, f"Width:\n{W}mm", ha='right', va='center', fontsize=10, weight='bold')
    
    ax.set_xlim(-200, L + 200)
    ax.set_ylim(-200, W + 200)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"PLAN VIEW: PAD FOUNDATION ({size_str})", fontsize=12, weight='bold', pad=10)
    
    return fig
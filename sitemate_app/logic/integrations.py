### (This now handles both WhatsApp and Email generation)

import urllib.parse

def generate_order_message(location, boq_dataframe, supplier_name):
    """
    Creates a professional order message text.
    """
    if boq_dataframe is None or boq_dataframe.empty:
        return "No items to order."

    # Calculate Grand Total safely
    grand_total = boq_dataframe['Total Cost'].sum()
    
    message = f"Hello {supplier_name},\n\n"
    message += f"I would like to place an order for a project in *{location}*.\n\n"
    message += "*REQUESTED MATERIALS:*\n"
    
    for _, row in boq_dataframe.iterrows():
        # Handle formatting (e.g. 10.0 -> 10)
        qty_val = row['Qty']
        qty_str = f"{qty_val:.0f}" if qty_val % 1 == 0 else f"{qty_val:.1f}"
        
        message += f"- {row['Item']}: {qty_str} units\n"
        
    message += f"\n💰 *Target Budget:* ₦{grand_total:,.0f}\n"
    message += "Please send your official invoice and bank details.\n\nRegards,\nSiteMate User"
    return message

def get_whatsapp_link(phone_number, message):
    """Generates a direct WhatsApp Click-to-Chat link."""
    if not phone_number:
        return None
    
    # Sanitize phone number (Remove + if present to fix invalid link error)
    clean_number = str(phone_number).replace("+", "").strip()
    
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_number}?text={encoded_msg}"

def get_email_link(email_address, location, message):
    """Generates a mailto link with subject and body."""
    if not email_address:
        return None
    
    subject = f"Order Request - {location} Project"
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(message)
    
    return f"mailto:{email_address}?subject={encoded_subject}&body={encoded_body}"